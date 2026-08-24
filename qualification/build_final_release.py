from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
RELEASE_ID = f"prefix-python-{VERSION}"
FINAL_ROOT = ROOT / "release" / f"{RELEASE_ID}-final"
FINAL_BUNDLE = ROOT / "release" / f"{RELEASE_ID}-windows-linux.zip"
FIXED_ZIP_TIME = (2024, 1, 1, 0, 0, 0)
FIXED_UNIX_TIME = 1704067200
WINDOWS_PYTHON_ARCHIVE = "python-3.12.10-embed-amd64.zip"
WINDOWS_PYTHON_URL = f"https://www.python.org/ftp/python/3.12.10/{WINDOWS_PYTHON_ARCHIVE}"
WINDOWS_PYTHON_SHA256 = "4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the final cross-platform PREFIX for Python 0.1.0 release.")
    parser.add_argument("--allow-dirty", action="store_true", help="Development-only override; final release must not use it.")
    args = parser.parse_args()
    source_identity = _source_identity(allow_dirty=args.allow_dirty)

    cache = ROOT / "qualification" / "_cache"
    cache.mkdir(parents=True, exist_ok=True)
    python_archive = cache / WINDOWS_PYTHON_ARCHIVE
    if not python_archive.is_file():
        raise SystemExit(f"Missing pinned Windows runtime cache: {python_archive}\nDownload: {WINDOWS_PYTHON_URL}")
    _require_hash(python_archive, WINDOWS_PYTHON_SHA256)

    with tempfile.TemporaryDirectory(prefix="prefix-final-build-") as temp_name:
        temp = Path(temp_name)
        wheel = _build_wheel(temp)
        vsix = _build_vsix(temp)
        parity = _verify_source_parity(wheel, vsix)

        if FINAL_ROOT.exists():
            shutil.rmtree(FINAL_ROOT)
        FINAL_ROOT.mkdir(parents=True)
        final_wheel = FINAL_ROOT / wheel.name
        final_vsix = FINAL_ROOT / vsix.name
        _canonicalize_zip(wheel, final_wheel)
        _canonicalize_zip(vsix, final_vsix)

        windows_package = _build_windows_package(temp, final_wheel, final_vsix, python_archive)
        linux_package = _build_linux_package(temp, final_wheel, final_vsix)
        shutil.copy2(windows_package, FINAL_ROOT / windows_package.name)
        shutil.copy2(linux_package, FINAL_ROOT / linux_package.name)
        shutil.copy2(ROOT / "FINAL_RELEASE_NOTES.md", FINAL_ROOT / "RELEASE_NOTES.md")
        shutil.copy2(ROOT / "LICENSE.txt", FINAL_ROOT / "LICENSE.txt")
        shutil.copy2(ROOT / "qualification" / "verify_final_release.py", FINAL_ROOT / "VERIFY_RELEASE.py")

        manifest = _write_release_manifest(source_identity, parity)
        _write_sha256sums(FINAL_ROOT)
        _write_deterministic_zip(FINAL_ROOT, FINAL_BUNDLE)

    print(json.dumps({
        "bundle": str(FINAL_BUNDLE),
        "bundle_sha256": _sha256(FINAL_BUNDLE),
        "manifest": manifest,
    }, indent=2, sort_keys=True))
    return 0


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, encoding="utf-8", errors="replace", capture_output=True)
    if result.returncode:
        raise RuntimeError(f"Command failed: {command}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


def _source_identity(*, allow_dirty: bool) -> dict[str, object]:
    status = _run(["git", "status", "--porcelain"], ROOT).stdout.strip()
    if status and not allow_dirty:
        raise SystemExit("Final release build refused because the source worktree is dirty.")
    return {
        "branch": _run(["git", "branch", "--show-current"], ROOT).stdout.strip(),
        "commit": _run(["git", "rev-parse", "HEAD"], ROOT).stdout.strip(),
        "tree": _run(["git", "rev-parse", "HEAD^{tree}"], ROOT).stdout.strip(),
        "worktree_clean": not bool(status),
    }


def _build_wheel(temp: Path) -> Path:
    out = temp / "wheel"
    out.mkdir()
    source = temp / "python-source"
    source.mkdir()
    shutil.copytree(ROOT / "prefix_python", source / "prefix_python", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ["pyproject.toml", "README.md", "LICENSE.txt"]:
        shutil.copy2(ROOT / name, source / name)
    _run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "--no-build-isolation", "--disable-pip-version-check", "-w", str(out)], source)
    wheels = list(out.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"Expected one wheel, found {wheels}")
    return wheels[0]


def _build_vsix(temp: Path) -> Path:
    editor_source = ROOT / "editor" / "vscode"
    editor = temp / "editor"
    shutil.copytree(
        editor_source,
        editor,
        ignore=shutil.ignore_patterns("node_modules", "out", "*.vsix", "__pycache__"),
    )
    npm = "npm.cmd" if os.name == "nt" else "npm"
    _run([npm, "ci", "--offline", "--ignore-scripts"], editor)
    _run([npm, "audit", "--offline"], editor)
    _run([npm, "run", "build"], editor)
    _run([npm, "run", "test:behavior"], editor)
    _run([sys.executable, "package_vsix.py"], editor)
    source = editor / f"prefix-python-{VERSION}.vsix"
    if not source.is_file():
        raise RuntimeError(f"VSIX was not produced: {source}")
    destination = temp / source.name
    shutil.copy2(source, destination)
    return destination


def _verify_source_parity(wheel: Path, vsix: Path) -> dict[str, object]:
    wheel_checks: list[dict[str, object]] = []
    with zipfile.ZipFile(wheel) as archive:
        for source in sorted((ROOT / "prefix_python").glob("*.py")):
            member = f"prefix_python/{source.name}"
            match = hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(archive.read(member)).digest()
            wheel_checks.append({"path": member, "match": match})

    vsix_checks: list[dict[str, object]] = []
    with zipfile.ZipFile(vsix) as archive:
        for relative in ["out/enter.js", "out/extension.js", "out/response.js", "out/runtime.js", "package.json"]:
            source = ROOT / "editor" / "vscode" / relative
            member = f"extension/{relative}"
            match = hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(archive.read(member)).digest()
            vsix_checks.append({"path": member, "match": match})

    if not all(item["match"] for item in wheel_checks + vsix_checks):
        raise RuntimeError("Source-to-package parity failed.")
    return {"wheel": wheel_checks, "vsix": vsix_checks, "all_match": True}


def _payload_manifest(platform_name: str, wheel: Path, vsix: Path, extra: list[Path] = []) -> dict[str, object]:
    artifacts = [wheel, vsix, ROOT / "examples" / "broken_missing_colon.txt", ROOT / "examples" / "broken_return_outside_function.txt", *extra]
    payload: dict[str, object] = {
        "schema": "prefix-platform-payload.v1",
        "product": "PREFIX for Python",
        "version": VERSION,
        "platform": platform_name,
        "wheel": wheel.name,
        "vsix": vsix.name,
        "artifacts": [{"name": path.name, "sha256": _sha256(path), "size": path.stat().st_size} for path in artifacts],
    }
    return payload


def _build_windows_package(temp: Path, wheel: Path, vsix: Path, python_archive: Path) -> Path:
    package = temp / "windows" / f"{RELEASE_ID}-windows-x64"
    payload = package / "payload"
    payload.mkdir(parents=True)
    for name in ["Install-PREFIX-for-Python.cmd", "Install-PREFIX-for-Python.ps1", "Uninstall-PREFIX-for-Python.cmd", "Uninstall-PREFIX-for-Python.ps1"]:
        shutil.copy2(ROOT / "installer" / "windows" / name, package / name)
    for source in [wheel, vsix, python_archive, ROOT / "examples" / "broken_missing_colon.txt", ROOT / "examples" / "broken_return_outside_function.txt"]:
        shutil.copy2(source, payload / source.name)
    manifest = _payload_manifest("windows-x64", payload / wheel.name, payload / vsix.name, [payload / python_archive.name])
    manifest["runtime"] = {
        "implementation": "CPython",
        "version": "3.12.10",
        "architecture": "x64",
        "archive": python_archive.name,
        "source_url": WINDOWS_PYTHON_URL,
        "sha256": WINDOWS_PYTHON_SHA256,
    }
    _write_json(payload / "payload-manifest.json", manifest)
    (package / "README-WINDOWS.txt").write_text(
        "PREFIX for Python 0.1.0 - Windows x64\n\n"
        "Double-click Install-PREFIX-for-Python.cmd. The package installs its private CPython 3.12 runtime, the local engine, and the VS Code extension.\n"
        "No Python or pip setup is required. VS Code must already be installed.\n",
        encoding="utf-8",
    )
    destination = temp / f"{RELEASE_ID}-windows-x64.zip"
    _write_deterministic_zip(package, destination)
    return destination


def _build_linux_package(temp: Path, wheel: Path, vsix: Path) -> Path:
    package = temp / "linux" / f"{RELEASE_ID}-linux-amd64"
    payload = package / "payload"
    payload.mkdir(parents=True)
    for name in ["install-prefix-python.sh", "uninstall-prefix-python.sh"]:
        destination = package / name
        shutil.copy2(ROOT / "installer" / "linux" / name, destination)
        destination.chmod(0o755)
    for source in [wheel, vsix, ROOT / "examples" / "broken_missing_colon.txt", ROOT / "examples" / "broken_return_outside_function.txt"]:
        shutil.copy2(source, payload / source.name)
    _write_json(payload / "payload-manifest.json", _payload_manifest("linux-amd64", payload / wheel.name, payload / vsix.name))
    (package / "README-LINUX.txt").write_text(
        "PREFIX for Python 0.1.0 - Linux amd64\n\n"
        "Run: ./install-prefix-python.sh\n"
        "The installer requires a local CPython 3.12 and installs the engine per-user without pip or root access. If VS Code is present, the extension is installed and connected automatically.\n"
        "Run the demo after installation with: ~/.local/bin/prefix-python-demo\n",
        encoding="utf-8",
    )
    destination = temp / f"{RELEASE_ID}-linux-amd64.tar.gz"
    _write_deterministic_tar_gz(package, destination)
    return destination


def _write_release_manifest(source_identity: dict[str, object], parity: dict[str, object]) -> dict[str, object]:
    files = []
    for path in sorted(FINAL_ROOT.iterdir(), key=lambda item: item.name.lower()):
        if path.is_file() and path.name not in {"RELEASE_MANIFEST.json", "SHA256SUMS.txt"}:
            files.append({"name": path.name, "sha256": _sha256(path), "size": path.stat().st_size})
    payload = {
        "schema": "prefix-final-release.v1",
        "product": "PREFIX for Python",
        "version": VERSION,
        "platforms": ["windows-x64", "linux-amd64"],
        "source": source_identity,
        "source_to_package_parity": parity,
        "files": files,
    }
    _write_json(FINAL_ROOT / "RELEASE_MANIFEST.json", payload)
    return payload


def _canonicalize_zip(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        for name in sorted(zin.namelist()):
            original = zin.getinfo(name)
            info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = original.external_attr
            info.create_system = original.create_system
            zout.writestr(info, zin.read(name))


def _write_deterministic_zip(source_dir: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source_dir.rglob("*"), key=lambda item: item.relative_to(source_dir).as_posix().lower()):
            if not path.is_file():
                continue
            relative = f"{source_dir.name}/{path.relative_to(source_dir).as_posix()}"
            info = zipfile.ZipInfo(relative, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if path.suffix in {".sh", ".cmd", ".ps1"} else 0o644) << 16
            archive.writestr(info, path.read_bytes())


def _write_deterministic_tar_gz(source_dir: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz, tarfile.open(fileobj=gz, mode="w") as archive:
        for path in sorted(source_dir.rglob("*"), key=lambda item: item.relative_to(source_dir).as_posix().lower()):
            relative = Path(source_dir.name) / path.relative_to(source_dir)
            info = archive.gettarinfo(str(path), arcname=relative.as_posix())
            info.mtime = FIXED_UNIX_TIME
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            if path.is_dir():
                info.mode = 0o755
            elif path.suffix == ".sh":
                info.mode = 0o755
            else:
                info.mode = 0o644
            if path.is_file():
                with path.open("rb") as handle:
                    archive.addfile(info, handle)
            else:
                archive.addfile(info)


def _write_sha256sums(root: Path) -> None:
    lines = []
    for path in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(f"{_sha256(path)} *{path.name}")
    (root / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_hash(path: Path, expected: str) -> None:
    actual = _sha256(path)
    if actual != expected:
        raise SystemExit(f"SHA-256 mismatch for {path}: expected {expected}, got {actual}")


if __name__ == "__main__":
    raise SystemExit(main())
