"""Content identities for reproducible, isolated benchmark runs."""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import sys
from pathlib import Path


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def source_hash(root: Path) -> str:
    return canonical_hash([(p.relative_to(root).as_posix(), file_hash(p))
                           for p in sorted(root.rglob('*.py')) if p.is_file()])


def executable(name: str) -> dict | None:
    found = shutil.which(name)
    if not found:
        return None
    path = Path(found).resolve()
    return {'path': str(path), 'sha256': file_hash(path)}


def environment(cli: str, layer: str, metrics: list[str], timeout: int) -> dict:
    spec = importlib.util.find_spec('decbench')
    if spec is None or not spec.origin:
        raise RuntimeError('DecBench is not installed in this Python environment')
    package = Path(spec.origin).resolve().parent
    cli_path = Path(cli).resolve()
    # Tools are included even if a particular metric abstains on this host.
    tool_names = ('llvm-nm', 'nm', 'llvm-strip', 'strip', 'x86_64-linux-gnu-gcc',
                  'aarch64-linux-gnu-gcc', 'gcc', 'clang')
    distributions = sorted((d.metadata.get('Name', ''), d.version)
                           for d in importlib.metadata.distributions())
    return {
        'runner_sha256': source_hash(Path(__file__).resolve().parent),
        'decbench_sha256': source_hash(package),
        'decbench_path': str(package),
        'python': {'executable': str(Path(sys.executable).resolve()), 'version': sys.version,
                   'distributions_sha256': canonical_hash(distributions)},
        'host': {'system': platform.system(), 'machine': platform.machine()},
        'tools': {name: executable(name) for name in tool_names},
        'fission': {'path': str(cli_path), 'sha256': file_hash(cli_path),
                    'resource_root': os.environ.get('FISSION_RESOURCE_ROOT')},
        'layer': layer, 'metrics': sorted(set(metrics)),
        'binary_timeout_s': timeout, 'function_timeout_ms': 45000,
    }


def make_manifest(items: list, env: dict) -> dict:
    entries = []
    for opt, project, name, binary, cfg in items:
        entries.append({'opt': opt, 'project': project, 'binary': name,
                        'binary_path': str(binary.resolve()), 'binary_sha256': file_hash(binary),
                        'cfg_path': str(cfg.resolve()), 'cfg_sha256': file_hash(cfg)})
    contract = {'schema': 1, 'environment': env, 'inputs': entries}
    return {'run_id': canonical_hash(contract), **contract}


def result_matches(rec: object, manifest: dict, item: dict, *, success: bool = True) -> bool:
    if not isinstance(rec, dict):
        return False
    identity = {'run_id': manifest['run_id'], 'binary_sha256': item['binary_sha256'],
                'cfg_sha256': item['cfg_sha256']}
    return (rec.get('provenance') == identity
            and rec.get('opt') == item['opt'] and rec.get('project') == item['project']
            and rec.get('binary') == item['binary']
            and (not success or rec.get('status') == 'ok'))
