"""Assemble the distribution candidate with the retained 0.1.0 builders.

No publication, provider activation, signing, or replacement of the keyless offer.
The completed official VSIX is an input, never repackaged here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import build_final_release as retained

ROOT = retained.ROOT
VSIX_SHA = "974c97e8732046147e8474689d4cd21936166b4cb16bac0a435451181b69c039"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parity(wheel: Path, vsix: Path) -> dict:
    checks = []
    with zipfile.ZipFile(wheel) as archive:
        for source in sorted((ROOT / "prefix_python").glob("*.py")):
            member = "prefix_python/" + source.name
            checks.append({"artifact": "wheel", "member": member,
                           "match": archive.read(member) == source.read_bytes()})
        metadata = archive.read("prefix_python-0.1.0.dist-info/METADATA").decode()
        entries = archive.read("prefix_python-0.1.0.dist-info/entry_points.txt").decode()
        assert "Version: 0.1.0\n" in metadata
        assert "Requires-Python: <3.13,>=3.12" in metadata
        assert "prefix-python = prefix_python.cli:main" in entries
        assert "prefix-python-ops = prefix_python.commercial_operator_console:main" in entries
    with zipfile.ZipFile(vsix) as archive:
        for relative in ["out/enter.js", "out/extension.js", "out/response.js", "out/runtime.js"]:
            checks.append({"artifact": "vsix", "member": "extension/" + relative,
                           "match": archive.read("extension/" + relative) ==
                           (ROOT / "editor" / "vscode" / relative).read_bytes()})
        packaged = json.loads(archive.read("extension/package.json"))
        original = json.loads((ROOT / "editor" / "vscode" / "package.json").read_text())
        packaged.pop("__metadata", None)
        original.pop("__metadata", None)
        checks.append({"artifact": "vsix", "member": "extension/package.json",
                       "match": packaged == original, "comparison": "JSON excluding vsce __metadata"})
    assert all(c["match"] for c in checks), checks
    return {"all_match": True, "checks": checks, "entry_points_gated": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vsix", type=Path, default=ROOT / "qualification/distribution-inputs/prefix-python-0.1.0.vsix")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    identity = retained._source_identity(allow_dirty=False)
    retained._require_hash(args.vsix, VSIX_SHA)
    cache = ROOT / "qualification" / "_cache"
    cache.mkdir(exist_ok=True)
    runtime = cache / retained.WINDOWS_PYTHON_ARCHIVE
    if not runtime.exists():
        with urllib.request.urlopen(retained.WINDOWS_PYTHON_URL, timeout=120) as response:
            runtime.write_bytes(response.read())
    retained._require_hash(runtime, retained.WINDOWS_PYTHON_SHA256)
    with tempfile.TemporaryDirectory(prefix="prefix-distribution-build-") as temporary:
        temp = Path(temporary)
        built_wheel = retained._build_wheel(temp)
        wheel = output / built_wheel.name
        retained._canonicalize_zip(built_wheel, wheel)
        vsix = output / "prefix-python-0.1.0.vsix"
        shutil.copy2(args.vsix, vsix)
        source_parity = parity(wheel, vsix)
        windows = retained._build_windows_package(temp, wheel, vsix, runtime)
        linux = retained._build_linux_package(temp, wheel, vsix)
        for path in [windows, linux]:
            shutil.copy2(path, output / path.name)
    shutil.copy2(ROOT / "LICENSE.txt", output / "LICENSE.txt")
    shutil.copy2(ROOT / "DISTRIBUTION_CANDIDATE.md", output / "RELEASE_NOTES.md")
    manifest = {
        "schema": "prefix-distribution-candidate.v1", "campaign": "PREFIX-DISTRIBUTION-001",
        "product": "PREFIX for Python", "version": "0.1.0", "source": identity,
        "qualified_core_predecessor": "77d742f0d764064f8ffac8a9ae2101823a4bb2c8",
        "commercial_replacement_authorized": False,
        "production_license_delivery_verified": False,
        "existing_offer": "29 USD one-time; existing qualified keyless download remains the customer promise",
        "source_parity": source_parity,
        "artifacts": [{"name": p.name, "bytes": p.stat().st_size, "sha256": sha(p)}
                      for p in sorted(output.iterdir()) if p.is_file()],
    }
    (output / "DISTRIBUTION_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    retained._write_sha256sums(output)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
