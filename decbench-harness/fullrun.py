"""Score fission on the *whole* unoptimized config, not the 250-row sample.

The published row covers 100 of 34,406 functions, so fission's rank against
ida/angr/ghidra is not a same-denominator comparison. This runs every row.

Shape follows kitfast.py -- decompile, batch joern, score -- but adds what a
multi-hour sweep needs: one checkpoint file per binary, so an interrupted run
resumes instead of restarting, and stripped copies, because the dataset's
binaries carry symbols and scoring types against those hands the decompiler
the answer key.

Never executes a binary: strip, nm and decompile only.
"""
import concurrent.futures as cf
import hashlib
import itertools
import threading
import json, os, re, shutil, statistics, subprocess, sys, tempfile, time
from pathlib import Path

B = Path("/Users/sjkim1127/fission-benchmark")
D = B / "decbench-data"
sys.path.insert(0, str(B))
sys.path.insert(0, str(B / "runner"))
sys.path.insert(0, "/Users/sjkim1127/Fission/vendor/decbench")
from ged import compute_ged, extract_decompiled_cfgs, load_published_source_cfgs
from decbench.decompilers.raw.fission_raw import _variables
from decbench.metrics.type_match import TypeMatchMetric, extract_ground_truth_types
from decbench.models.decompilation import FunctionDecompilation

CLI = "/Users/sjkim1127/Fission/target/release/fission_cli"
CONFIG = os.environ.get("CONFIG", "unoptimized")
STAGE = Path(os.environ.get("STAGE", "/tmp/decbench-stripped"))
CKPT = Path(os.environ.get("CKPT", "/tmp/decbench-full-ckpt"))
LAYER = os.environ.get("LAYER", "hir")
# Functions per Joern invocation. Measured by parsing real output at several
# sizes: `time = 5.2 s + 0.045 s x functions`, so at 60 two thirds of the cost
# is the JVM starting rather than anything being parsed. Raising it cuts JVM
# starts across the corpus from 1,043 to 348.
JOERN_CHUNK = int(os.environ.get("JOERN_CHUNK", "300"))
# Concurrent Joern JVMs. Measured on `betaflight` (4,018 functions, 67
# chunks), same rows and identical scores each time:
#   serial 530 s | 3 workers 318 s | 6 workers 283 s | 10 workers 281 s
# It saturates at 6 because joern-cli is itself multi-threaded, so more JVMs
# only contend for the same cores. Binaries smaller than one chunk see no
# gain -- the parallelism is across a binary's chunks, not across binaries.
# Measured on `betaflight` (4,018 functions, 67 chunks), same rows and
# identical scores each time:
#   serial 530 s | 3 workers 318 s | 6 workers 283 s | 10 workers 281 s
# The gain flattens past 6 because joern-cli is itself multi-threaded. With
# binaries now running in a pool as well, this is per-binary and the real
# limit is the product -- see JVM_CAP.
JOERN_WORKERS = int(os.environ.get("JOERN_WORKERS", "1"))
# Total Joern JVMs alive at once, across every binary worker. Each wants
# ~1.5 GB and the box has ~10.6 GB free, so six is what fits.
JVM_CAP = int(os.environ.get("JVM_CAP", "16"))
# Joern is about half a sweep (the other half is Fission itself -- the
# "~90%" this comment used to claim was measured while `openssh-portable/ssh`
# was spending 95 minutes in a decompile fallback). Most of it is repeated
# work: between two
# sweeps that differ by one change, 17,717 of 21,290 rows (83%) had byte
# identical output and were re-parsed and re-scored for nothing. Keyed by the
# emitted code itself, so a hit is only possible when the text is unchanged.
GEDCACHE = Path(os.environ.get("GEDCACHE", "/tmp/decbench-gedcache"))
GEDCACHE.mkdir(parents=True, exist_ok=True)
# Decompilation is independent of GED and type scoring, but is currently the
# largest repeated cost when the same local Fission build is re-evaluated.
# Keep this cache outside GEDCACHE so a fresh metric cache does not force a
# fresh Fission run. The key includes the CLI bytes, input binary bytes, layer,
# and exact address set, so a rebuilt CLI or changed input cannot reuse stale
# output accidentally.
DECOMP_CACHE = Path(os.environ.get("DECOMP_CACHE", "/tmp/decbench-decompcache"))
DECOMP_CACHE.mkdir(parents=True, exist_ok=True)
TYPECACHE = Path(os.environ.get("TYPECACHE", "/tmp/decbench-typecache"))
TYPECACHE.mkdir(parents=True, exist_ok=True)
DECOMP_CACHE_VERSION = "fission-decomp-v1"
TYPE_CACHE_VERSION = "type-match-v2"


def _cache_disabled() -> bool:
    return os.environ.get("FISSION_BENCHMARK_NO_CACHE", "").lower() in {
        "1", "true", "yes", "on"
    }
# A single pathological body -- a materialised condition printed as one
# 17,000-character ternary chain -- makes Joern's ReachingDefPass run for
# minutes and then exhaust the heap, taking every function batched beside
# it down with it. Batch those alone so they cost one JVM, not sixty.
HARD_LINE = int(os.environ.get("HARD_LINE", "4000"))
LIMIT = int(os.environ.get("LIMIT", "0"))          # binaries, 0 = all
# Comma-separated substrings; when set, only groups whose "project/binary"
# contains one of them are run. Lets a targeted fix be re-scored on the
# binaries it touches without re-running the whole config.
ONLY = [s for s in os.environ.get("ONLY", "").split(",") if s]
# `openssh-portable/ssh` (1,431 functions) needed ~40 min in one call and hit
# the old 1800 s ceiling, which sent it down the fallback for 95 minutes.
TIMEOUT = int(os.environ.get("TIMEOUT", "3600"))
# Per-function ceiling for the fallback path, so one hung function
# costs that much and not the binary.
PER_FN_TIMEOUT = int(os.environ.get("PER_FN_TIMEOUT", "90"))
STAGE.mkdir(parents=True, exist_ok=True)
CKPT.mkdir(parents=True, exist_ok=True)

manifest = json.load(open(D / "configs" / CONFIG / "manifest.json"))
# The unoptimized config ships a top-level `scores_*.json`; the others keep
# the same structure under their own directory. Prefer whichever exists so a
# sweep can be pointed at any config with `CONFIG=`.
def _load_field_scores(root, config):
    import os
    flat = os.path.join(str(root), f"scores_{config}.json")
    nested = os.path.join(str(root), "configs", config, "function_results.json")
    return json.load(open(flat if os.path.exists(flat) else nested))


scores = _load_field_scores(D, CONFIG)
path_of = {(b["opt"], b["project"], b["binary"]): b for b in manifest["binaries"]}

groups = scores["groups"]
if ONLY:
    groups = [g for g in groups
              if any(o in f'{g["project"]}/{g["binary"]}' for o in ONLY)]
if LIMIT:
    groups = groups[:LIMIT]

_DECLARATOR = re.compile(r"^[^\n;{}]*?\b([A-Za-z_]\w*)\s*\(", re.M)


def declared_name(text, addr):
    for line in text.splitlines():
        if "(" not in line or line.lstrip().startswith(("//", "#", "typedef")):
            continue
        m = _DECLARATOR.match(line)
        if m and (line.rstrip().endswith(")") or line.rstrip().endswith("{")):
            return m.group(1)
    return f"sub_{addr:x}"


def source_cfg_name(fn, src):
    if fn in src:
        return fn
    stripped = fn.split("@", 1)[0]
    for candidate in (stripped, stripped.lstrip("_"), fn.lstrip("_")):
        if candidate in src:
            return candidate
    return None


def stripped_copy(original: Path, key) -> Path:
    """A symbol-free copy, so the decompiler cannot read the answer key."""
    dst = STAGE / ("_".join(key) + "__" + original.name)
    if not dst.exists():
        shutil.copy2(original, dst)
        subprocess.run(["llvm-strip", "--strip-all", str(dst)],
                       capture_output=True, check=False)
    return dst


def addr_by_name(original: Path) -> dict:
    nm = subprocess.run(["llvm-nm", "--defined-only", str(original)],
                        capture_output=True, text=True).stdout
    out = {}
    for line in nm.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[1] in "tT":
            out.setdefault(parts[2], int(parts[0], 16))
    return out


_addr_file_seq = itertools.count()


def _decomp_call(binary, chunk, records, timeout, binary_key, binary_digest,
                 cache_stats):
    """Decompile `chunk` in one call. True if it produced records."""
    addresses = [address for _, address in chunk]
    cached = _decomp_cache_get(binary_key, binary_digest, addresses)
    if cached is not None:
        records.update(cached)
        cache_stats["hits"] += 1
        return True
    cache_stats["misses"] += 1
    # Named per *call*, not per process: binaries run in a thread pool, so
    # `os.getpid()` is the same for every worker and they were overwriting one
    # another's address list -- `bzip2recover` asked for its 13 functions and
    # got whatever the neighbouring thread had just written, so it scored 0 of
    # 13 while reporting success.
    af = STAGE / f"addrs_{threading.get_ident()}_{next(_addr_file_seq)}.txt"
    af.write_text("".join(f"0x{a:x}\n" for _, a in chunk))
    try:
        run = subprocess.run(
            [CLI, "decomp", str(binary), "--layer", LAYER, "--json",
             "--no-header", "--no-warnings", "--addresses-file", str(af)],
            capture_output=True, text=True, timeout=timeout)
        for e in json.loads(run.stdout[run.stdout.index("["):]):
            if e.get("code"):
                records[int(e["address"], 16)] = e
        _decomp_cache_put(binary_key, binary_digest, addresses, records)
        return True
    except Exception:
        return False
    finally:
        af.unlink(missing_ok=True)


def decompile_batch(binary, todo, records, binary_key, binary_digest, cache_stats):
    """Decompile every address, bisecting around whatever breaks.

    The previous fallback retried one function at a time, which re-pays load,
    discovery and FID per function: measured at 4 s/function against 0.13 s in
    batch, and `openssh-portable/ssh` alone cost 95 of a 260-minute sweep that
    way. Halving instead isolates the bad function in log2(n) extra calls and
    keeps everything else at batch speed.

    Returns None when the first call succeeded, else the list of functions
    that failed even alone.
    """
    if _decomp_call(binary, todo, records, TIMEOUT, binary_key, binary_digest,
                    cache_stats):
        return None
    bad = []
    work = [todo]
    while work:
        chunk = work.pop()
        if len(chunk) == 1:
            if not _decomp_call(binary, chunk, records, PER_FN_TIMEOUT, binary_key,
                                binary_digest, cache_stats):
                bad.append(chunk[0])
            continue
        # A whole half that succeeds costs one call, not len(half) calls.
        mid = len(chunk) // 2
        for half in (chunk[:mid], chunk[mid:]):
            if not _decomp_call(binary, half, records, TIMEOUT, binary_key,
                                binary_digest, cache_stats):
                work.append(half)
    return bad


def _ged_cache_path(binary_key, fn, code):
    h = hashlib.sha256(
        f"{binary_key}\0{fn}\0".encode() + code.encode("utf8", "replace")
    ).hexdigest()
    return GEDCACHE / h[:2] / f"{h}.json"


def ged_cache_get(binary_key, fn, code):
    if _cache_disabled():
        return None
    p = _ged_cache_path(binary_key, fn, code)
    if not p.is_file():
        return None
    try:
        return json.load(open(p))
    except Exception:
        return None


def ged_cache_put(binary_key, fn, code, value):
    if _cache_disabled():
        return
    p = _ged_cache_path(binary_key, fn, code)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        json.dump(value, open(p, "w"))
    except Exception:
        pass


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


CLI_FINGERPRINT = _file_sha256(Path(CLI)) if Path(CLI).is_file() else "missing"


def _content_cache_path(root: Path, version: str, key) -> Path:
    encoded = json.dumps(
        {"version": version, "key": key},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return root / digest[:2] / f"{digest}.json"


def _cache_load(root: Path, version: str, key):
    if _cache_disabled():
        return None
    path = _content_cache_path(root, version, key)
    try:
        envelope = json.load(path.open())
    except (OSError, json.JSONDecodeError):
        return None
    if envelope.get("version") != version or envelope.get("key") != key:
        return None
    return envelope.get("value")


def _cache_store(root: Path, version: str, key, value) -> None:
    if _cache_disabled():
        return
    path = _content_cache_path(root, version, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    envelope = {"version": version, "key": key, "value": value}
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(envelope, stream, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def _decomp_cache_key(binary_key, binary_digest, addresses):
    return {
        "binary_key": binary_key,
        "binary_sha256": binary_digest,
        "cli_sha256": CLI_FINGERPRINT,
        "layer": LAYER,
        "addresses": sorted(f"0x{address:x}" for address in addresses),
    }


def _decomp_cache_get(binary_key, binary_digest, addresses):
    key = _decomp_cache_key(binary_key, binary_digest, addresses)
    value = _cache_load(DECOMP_CACHE, DECOMP_CACHE_VERSION, key)
    if not isinstance(value, list):
        return None
    records = {}
    try:
        for record in value:
            if record.get("code") and record.get("address") is not None:
                records[int(record["address"], 16)] = record
    except (AttributeError, TypeError, ValueError):
        return None
    return records


def _decomp_cache_put(binary_key, binary_digest, addresses, records):
    address_set = set(addresses)
    selected = [records[address] for address in sorted(records)
                if address in address_set]
    if selected:
        _cache_store(
            DECOMP_CACHE,
            DECOMP_CACHE_VERSION,
            _decomp_cache_key(binary_key, binary_digest, addresses),
            selected,
        )


def _type_cache_key(binary_key, fn, code, record):
    variables = []
    for entry in record.get("variables") or ():
        if isinstance(entry, dict):
            variables.append({
                field: entry.get(field)
                for field in ("name", "type", "stack_offset", "size", "kind", "arg_index")
            })
    return {
        "config": CONFIG,
        "binary_key": binary_key,
        "function": fn,
        "code": code,
        "variables": variables,
    }


def type_cache_get(binary_key, fn, code, record):
    value = _cache_load(
        TYPECACHE, TYPE_CACHE_VERSION, _type_cache_key(binary_key, fn, code, record)
    )
    return value if isinstance(value, dict) else None


def type_cache_put(binary_key, fn, code, record, value):
    if value:
        _cache_store(
            TYPECACHE,
            TYPE_CACHE_VERSION, _type_cache_key(binary_key, fn, code, record),
            value,
        )


def _extract_cfgs_safe(part):
    """One chunk, in its own process. `extract_decompiled_cfgs` already
    bisects a failing batch internally, so a raise here means the whole
    chunk is unusable rather than one function in it."""
    try:
        return extract_decompiled_cfgs(part)
    except Exception:
        return {}


tm = TypeMatchMetric()
t_start = time.time()
done_bins = 0

# ── One binary, start to finish ──────────────────────────────────────────────
# Pulled out of the loop so binaries can run concurrently. A sweep spends its
# time roughly half in Fission and half in Joern (measured: 58 s and 58 s over
# four binaries), and those two halves used to be strictly sequential per
# binary -- so one binary's Joern ran while nothing decompiled, and vice
# versa. Running binaries in a pool overlaps them.
#
# It also removes a floor that no chunk size could: every binary pays at least
# one JVM start (~5.2 s), and 267 of them in series is 23 minutes of startup
# on its own. In a pool those starts overlap instead of adding up.
#
# Threads, not processes: every expensive call here shells out (fission_cli,
# joern, llvm-nm, llvm-strip), so Python only waits, and a process pool would
# re-import this module -- which re-runs the whole sweep in each child, since
# there is no __main__ guard.
def process_group(gi, grp):
    """Score one binary and return its log line, or None if it was skipped."""
    key = (grp["opt_level"], grp["project"], grp["binary"])
    ck = CKPT / (("_".join(key)).replace("/", "_") + ".json")
    if ck.exists():
        return None

    meta = path_of.get(key)
    wanted = [f["function"] for f in grp["functions"]]
    if not meta:
        json.dump({"key": key, "rows": [], "skip": "manifest"}, open(ck, "w"))
        return None
    original = D / meta["binary_path"]
    if not original.is_file():
        json.dump({"key": key, "rows": [], "skip": "missing"}, open(ck, "w"))
        return None

    t_bin = time.time()
    binary = stripped_copy(original, key)
    binary_digest = _file_sha256(original)
    names = addr_by_name(original)
    todo = [(fn, names[fn]) for fn in wanted if fn in names]

    # ---- decompile every wanted address in one call ----
    records = {}
    decomp_cache_stats = {"hits": 0, "misses": 0}
    if todo:
        bad = decompile_batch(
            binary, todo, records, "/".join(key), binary_digest, decomp_cache_stats
        )
        if bad is not None:
            print(f"  [{gi}/{len(groups)}] {key[1]}/{key[2]} 배치 분할: "
                  f"회수 {len(records)}/{len(todo)}"
                  + (f"  실패: {', '.join(f'{n}@0x{a:x}' for n, a in bad[:5])}"
                     if bad else ""),
                  flush=True)

    t_decomp = time.time() - t_bin

    # ---- reference data ----
    try:
        src = load_published_source_cfgs(D / meta["source_cfg_path"])
    except Exception:
        src = {}
    try:
        gt = extract_ground_truth_types(original)
    except Exception:
        gt = {}

    # ---- CFGs, batched ----
    # A cached row means this exact text was parsed and scored before, so it
    # never reaches Joern at all. On a re-sweep after one change that is most
    # of the corpus.
    bkey = "/".join(key)
    batch, unique_of, cached = {}, {}, {}
    type_cache_stats = {"hits": 0, "misses": 0}
    for i, (fn, a) in enumerate(todo):
        rec = records.get(a)
        if not rec:
            continue
        text = rec.get(f"code_{LAYER}") or rec["code"]
        hit = ged_cache_get(bkey, fn, text)
        if hit is not None:
            cached[a] = hit
            continue
        unique = f"{fn}_u{i}"
        batch[unique] = text.replace(declared_name(text, a), unique)
        unique_of[a] = unique
    cfgs = {}
    t_joern0 = time.time()
    hard = {n for n, t in batch.items()
            if max((len(l) for l in t.splitlines()), default=0) > HARD_LINE}
    keys = [n for n in batch if n not in hard]
    parts = [{n: batch[n] for n in keys[i:i + JOERN_CHUNK]}
             for i in range(0, len(keys), JOERN_CHUNK)]
    # Joern is ~90% of a sweep's wall time (Fission is ~8%), and every chunk
    # is an independent JVM, so this loop was the whole reason a full sweep
    # took four hours on a 14-core machine. Each JVM wants ~1.5 GB, so the
    # default stays well under what the box can hold.
    if parts:
        if JOERN_WORKERS > 1 and len(parts) > 1:
            # Threads, not processes: `extract_decompiled_cfgs` shells out to
            # joern-cli, so the Python side only waits, and a process pool
            # would re-import this module (macOS spawns) -- which re-runs the
            # whole sweep in every child, since this script has no __main__
            # guard. That is exactly how the first attempt died.
            with cf.ThreadPoolExecutor(max_workers=JOERN_WORKERS) as pool:
                for res in pool.map(_extract_cfgs_safe, parts):
                    cfgs.update(res)
        else:
            for part in parts:
                cfgs.update(_extract_cfgs_safe(part))
    # `extract_decompiled_cfgs` already bisects a failing batch internally, so
    # retrying its misses one-by-one here just launched another JVM per
    # function. Only the pathological bodies, held out above, still need their
    # own single attempt.
    for n in sorted(hard):
        try:
            cfgs.update(extract_decompiled_cfgs({n: batch[n]}))
        except Exception:
            pass

    t_joern = time.time() - t_joern0

    # ---- score ----
    t_score0 = time.time()
    rows = []
    for fn, a in todo:
        rec = records.get(a)
        row = {"opt": key[0], "project": key[1], "binary": key[2], "fn": fn,
               "addr": f"0x{a:x}", "decompiled": rec is not None}
        if rec:
            if a in cached:
                row.update(cached[a])
            else:
                unique = unique_of.get(a)
                src_name = source_cfg_name(fn, src) if src else None
                out = {}
                if not src_name:
                    out["no_ged"] = "no_source_cfg"
                elif unique not in cfgs:
                    out["no_ged"] = "joern_failed_on_our_output"
                if unique and src_name and unique in cfgs:
                    try:
                        res = compute_ged(src[src_name], cfgs[unique])
                        if "ged" in res:
                            out.pop("no_ged", None)
                            out["ged"] = res["ged"]
                            out["src_nodes"] = src[src_name].number_of_nodes()
                            out["our_nodes"] = cfgs[unique].number_of_nodes()
                        else:
                            # Previously this fell through leaving no reason at
                            # all: 855 rows of the last sweep, 2.5%, vanished
                            # with nothing recorded about why.
                            out.setdefault("no_ged", "ged_returned_nothing")
                    except Exception as exc:
                        out.setdefault("no_ged", f"ged_failed:{type(exc).__name__}")
                row.update(out)
                ged_cache_put(bkey, fn, rec.get(f"code_{LAYER}") or rec["code"], out)
            if gt.get(fn):
                code = rec.get(f"code_{LAYER}") or rec["code"]
                type_hit = type_cache_get(bkey, fn, code, rec)
                if type_hit is not None:
                    row.update(type_hit)
                    type_cache_stats["hits"] += 1
                else:
                    type_cache_stats["misses"] += 1
                    computed_types = {}
                    for suffix, variables in (("", _variables(rec)), ("_text", None)):
                        fd = FunctionDecompilation(
                            name=fn, address=a, decompiled_code=code,
                            line_count=code.count("\n") + 1,
                            **({"variables": variables} if variables is not None else {}))
                        try:
                            computed_types["type" + suffix] = _tm().compute_for_function(
                                fd, ground_truth_vars=gt[fn]).value
                        except Exception:
                            pass
                    row.update(computed_types)
                    type_cache_put(bkey, fn, code, rec, computed_types)
        rows.append(row)

    json.dump({"key": key, "rows": rows}, open(ck, "w"))
    elapsed = time.time() - t_start
    return (f"[{gi}/{len(groups)}] {key[1]}/{key[2]}  함수 {len(rows)}  "
          f"디컴파일 {sum(1 for r in rows if r['decompiled'])}  "
          f"GED {sum(1 for r in rows if 'ged' in r)}  "
          f"{time.time()-t_bin:.0f}초"
          f" [디컴파일 {t_decomp:.0f} joern {t_joern:.0f} 채점 {time.time()-t_score0:.0f}"
          f" 조각 {len(parts)} 캐시 {len(cached)}/{len(todo)}"
          f" 디컴프캐시 {decomp_cache_stats['hits']}/"
          f"{sum(decomp_cache_stats.values())} 타입캐시 {type_cache_stats['hits']}/"
          f"{sum(type_cache_stats.values())}]"
          f"  (누적 {elapsed/60:.1f}분)")


# `TypeMatchMetric` is not documented as thread-safe and is called from every
# worker, so each thread gets its own rather than sharing one.
_tls = threading.local()


def _tm():
    metric = getattr(_tls, "metric", None)
    if metric is None:
        metric = _tls.metric = TypeMatchMetric()
    return metric


# Concurrent JVMs are what the box can actually hold: each wants ~1.5 GB, and
# BINARY_WORKERS x JOERN_WORKERS of them exist at once. The product is capped
# rather than either factor, because which way to split it depends on the
# corpus -- many small binaries want more binary workers, a few huge ones want
# more chunk workers.
# Binaries in flight. The default is eight binary workers and one Joern worker
# per binary: it keeps the JVM count at eight instead of sixteen, while still
# overlapping independent binaries. On a representative eight-binary slice
# this cut wall time from 62.4 s to 23.4 s with byte-identical rows.
#
# Eleven binaries, 1,190 rows, identical scores at every
# setting (1,104 scored, GED 18,492, 444 perfect):
#   1 x 6 joern 263 s | 2 x 3 152 s | 3 x 2 136 s | 4 x 1 128 s
#   6 x 1 118 s | 8 x 1 113 s | 10 x 1 111 s | 12 x 1 109 s
# Flat past 8, so 8 takes 96% of the best time with the most memory headroom
# (7.3 GB free against 6.8 at twelve) -- and that sample is light on large
# binaries, which is where the headroom gets spent.
BINARY_WORKERS = int(os.environ.get("BINARY_WORKERS", "8"))
if BINARY_WORKERS * JOERN_WORKERS > JVM_CAP:
    JOERN_WORKERS = max(1, JVM_CAP // BINARY_WORKERS)
    print(f"JVM 상한 {JVM_CAP}에 맞춰 JOERN_WORKERS를 {JOERN_WORKERS}로 조정",
          flush=True)

print(f"바이너리 {len(groups)}개  바이너리워커 {BINARY_WORKERS}  "
      f"joern워커 {JOERN_WORKERS}  조각 {JOERN_CHUNK}", flush=True)

if BINARY_WORKERS > 1:
    with cf.ThreadPoolExecutor(max_workers=BINARY_WORKERS) as pool:
        futures = [pool.submit(process_group, gi, grp)
                   for gi, grp in enumerate(groups, 1)]
        for fut in cf.as_completed(futures):
            line = fut.result()
            done_bins += 1
            if line:
                print(line, flush=True)
else:
    for gi, grp in enumerate(groups, 1):
        line = process_group(gi, grp)
        done_bins += 1
        if line:
            print(line, flush=True)

print(f"\n완료: 바이너리 {done_bins}  총 {time.time()-t_start:.0f}초")
