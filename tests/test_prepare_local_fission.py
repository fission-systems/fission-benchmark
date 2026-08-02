import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PREPARE_SCRIPT = REPO_ROOT / "scripts" / "prepare_local_fission.sh"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


def test_failed_host_build_does_not_relabel_stale_linux_artifact(tmp_path: Path) -> None:
    fission_root = tmp_path / "Fission"
    (fission_root / "utils" / "sleigh-specs").mkdir(parents=True)
    (fission_root / "utils" / "ghidra-data").mkdir()
    (fission_root / "utils" / "signatures").mkdir()
    (fission_root / "Cargo.toml").write_text("[workspace]\nmembers = []\n")

    subprocess.run(["git", "init", "-q", str(fission_root)], check=True)
    subprocess.run(
        ["git", "-C", str(fission_root), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(fission_root), "config", "user.name", "Test"],
        check=True,
    )
    subprocess.run(["git", "-C", str(fission_root), "add", "Cargo.toml"], check=True)
    subprocess.run(
        ["git", "-C", str(fission_root), "commit", "-qm", "fixture"],
        check=True,
    )

    target_dir = fission_root / "target" / "x86_64-unknown-linux-gnu" / "release"
    target_dir.mkdir(parents=True)
    stale_cli = target_dir / "fission_cli"
    stale_cli.write_bytes(b"stale-linux-cli")
    stale_cli.chmod(0o755)
    stale_stamp = target_dir / "fission_cli.fission-source-sha256"
    stale_stamp.write_text("old-fingerprint\n")

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_executable(
        fake_bin / "cargo",
        "#!/bin/sh\n"
        'if [ "$1" = "zigbuild" ] && [ "$2" = "-h" ]; then exit 0; fi\n'
        "exit 42\n",
    )
    _write_executable(
        fake_bin / "file",
        "#!/bin/sh\n"
        'echo "ELF 64-bit LSB pie executable, x86-64"\n',
    )
    _write_executable(fake_bin / "rustup", "#!/bin/sh\nexit 0\n")
    _write_executable(fake_bin / "docker", "#!/bin/sh\nexit 43\n")

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
            "FISSION_ROOT": str(fission_root),
            "FISSION_LOCAL_BUNDLE": str(tmp_path / "bundle"),
            "FISSION_CARGO_LOCKED": "0",
            "FISSION_AUTO_INSTALL_ZIGBUILD": "0",
        }
    )
    completed = subprocess.run(
        ["bash", str(PREPARE_SCRIPT)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode != 0
    assert "host cross-build failed; falling back to Docker" in completed.stderr
    assert stale_stamp.read_text() == "old-fingerprint\n"
    assert not (tmp_path / "bundle" / "GIT_SHA").exists()
    assert not (tmp_path / "bundle" / "SOURCE_FINGERPRINT").exists()
