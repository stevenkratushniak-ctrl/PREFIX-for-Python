from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import zipfile
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ROOT = ROOT / "release"
BUNDLE_DIR = RELEASE_ROOT / "prefix-python-0.1.0-rc2"
BUNDLE_ZIP = RELEASE_ROOT / "prefix-python-0.1.0-rc2.zip"
LOCK_PATH = RELEASE_ROOT / ".prefix-python-0.1.0-rc2.lock"
CANONICAL_TIMESTAMP = (2024, 1, 1, 0, 0, 0)
RELEASE_CANDIDATE_ID = "prefix-python-0.1.0-rc2"

WHEEL_SOURCE = ROOT / "dist" / "prefix_python-0.1.0-py3-none-any.whl"
VSIX_SOURCE = ROOT / "editor" / "vscode" / "prefix-python-0.1.0.vsix"

FILES_TO_COPY = [
    ROOT / "README.md",
    ROOT / "FOUNDING_OPERATOR_DISTRIBUTION_GUIDE.md",
    ROOT / "FINAL_FOUNDING_OPERATOR_HANDOFF.md",
    ROOT / "30_DAY_EVALUATION_TERMS.md",
    ROOT / "PILOT_ONBOARDING_PACKET.md",
    ROOT / "OPERATOR_SUPPORT_GUIDE.md",
    ROOT / "KNOWN_LIMITATIONS.md",
    ROOT / "HARDENING_REPORT.md",
    ROOT / "ADVERSARIAL_TEST_MATRIX.md",
    ROOT / "RELEASE_READINESS_REPORT.md",
    ROOT / "REFUSAL_BEHAVIOR_SPEC.md",
    ROOT / "PREFIX_RULE_LANE_MODEL.md",
    ROOT / "PREFIX_PYTHON_RULE_CATALOG_BY_LANE.md",
    ROOT / "PREFIX_STRUCTURAL_GOVERNANCE_MODEL.md",
    ROOT / "PREFIX_TRANSITION_ADMISSIBILITY_MODEL.md",
    ROOT / "PREFIX_LEGALITY_EVIDENCE_MODEL.md",
    ROOT / "PREFIX_CONTINUATION_GRAPH_MODEL.md",
    ROOT / "PREFIX_CONTINUATION_CARDINALITY_LAW.md",
    ROOT / "PREFIX_AST_DISTANCE_SCORING.md",
    ROOT / "PREFIX_AST_GOVERNANCE_RUNTIME.md",
    ROOT / "PREFIX_CONSTRAINED_TRANSITION_ENGINE.md",
    ROOT / "PREFIX_OPERATOR_TRUST_EVOLUTION.md",
    ROOT / "PREFIX_GOVERNANCE_APPLIANCE_HARDENING_REPORT.md",
    ROOT / "PREFIX_OPERATOR_DEMO_GUIDE.md",
    ROOT / "PYTHON_3_12_AST_RULE_CATALOG.md",
    ROOT / "SECURITY_AND_TRUST_REVIEW.md",
    ROOT / "release" / "RELEASE_NOTES_v0.1.0.md",
    ROOT / "release" / "INSTALL_PREFIX_PYTHON.ps1",
    ROOT / "release" / "DEMO_PREFIX_PYTHON.ps1",
    ROOT / "demo" / "PREFIX_GOVERNANCE_SHOWCASE.ps1",
    ROOT / "examples" / "broken_missing_colon.txt",
    ROOT / "examples" / "broken_return_outside_function.txt",
]


def main() -> int:
    with _bundle_lock():
        if BUNDLE_DIR.exists():
            shutil.rmtree(BUNDLE_DIR, ignore_errors=True)
        if BUNDLE_ZIP.exists():
            BUNDLE_ZIP.unlink()

        BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
        _copy_release_files()
        _canonicalize_zip_artifact(WHEEL_SOURCE, BUNDLE_DIR / WHEEL_SOURCE.name)
        _canonicalize_zip_artifact(VSIX_SOURCE, BUNDLE_DIR / VSIX_SOURCE.name)
        manifest = _write_manifest()
        _write_sha256sums()
        _write_canonical_bundle_zip()
        print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def _copy_release_files() -> None:
    for source in FILES_TO_COPY:
        destination = BUNDLE_DIR / source.name
        shutil.copy2(source, destination)


def _canonicalize_zip_artifact(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name in sorted(zin.namelist()):
            original = zin.getinfo(name)
            info = zipfile.ZipInfo(filename=name, date_time=CANONICAL_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = original.external_attr
            info.create_system = original.create_system
            zout.writestr(info, zin.read(name))


def _write_manifest() -> dict[str, object]:
    payload_files = []
    for path in sorted(BUNDLE_DIR.iterdir(), key=lambda item: item.name.lower()):
        payload_files.append(
            {
                "name": path.name,
                "sha256": _sha256_path(path),
                "size_bytes": path.stat().st_size,
            }
        )
    manifest = {
        "bundle_dir": str(BUNDLE_DIR),
        "bundle_zip": str(BUNDLE_ZIP),
        "canonical_timestamp": "2024-01-01T00:00:00",
        "hash_contract": {
            "manifest_scope": "payload_files only",
            "sha256sums_scope": "all bundle files except SHA256SUMS.txt",
            "self_hash_note": "RELEASE_VERIFICATION_MANIFEST.json is verified via SHA256SUMS.txt and is intentionally excluded from its own payload_files index.",
        },
        "payload_files": payload_files,
        "release_candidate_id": RELEASE_CANDIDATE_ID,
        "vsix_source": str(VSIX_SOURCE),
        "wheel_source": str(WHEEL_SOURCE),
    }
    (BUNDLE_DIR / "RELEASE_VERIFICATION_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _write_sha256sums() -> None:
    lines = []
    for path in sorted(BUNDLE_DIR.iterdir(), key=lambda item: item.name.lower()):
        if path.name == "SHA256SUMS.txt":
            continue
        lines.append(f"{_sha256_path(path)} *{path.name}")
    (BUNDLE_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")


def _write_canonical_bundle_zip() -> None:
    with zipfile.ZipFile(BUNDLE_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for path in sorted(BUNDLE_DIR.iterdir(), key=lambda item: item.name.lower()):
            info = zipfile.ZipInfo(filename=f"{BUNDLE_DIR.name}/{path.name}", date_time=CANONICAL_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zout.writestr(info, path.read_bytes())


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def _bundle_lock():
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock_handle: int | None = None
    try:
        for _ in range(100):
            try:
                lock_handle = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(lock_handle, str(os.getpid()).encode("ascii"))
                break
            except FileExistsError:
                time.sleep(0.1)
        if lock_handle is None:
            raise RuntimeError(f"Could not acquire release bundle lock: {LOCK_PATH}")
        yield
    finally:
        if lock_handle is not None:
            os.close(lock_handle)
        try:
            if LOCK_PATH.exists():
                LOCK_PATH.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
