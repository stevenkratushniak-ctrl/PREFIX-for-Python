from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a PREFIX for Python final release directory.")
    parser.add_argument("release_root", nargs="?", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = args.release_root.resolve()
    manifest_path = root / "RELEASE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures = []
    for record in manifest["files"]:
        path = root / record["name"]
        if not path.is_file():
            failures.append({"name": record["name"], "reason": "missing"})
        elif path.stat().st_size != record["size"]:
            failures.append({"name": record["name"], "reason": "size"})
        elif sha256(path) != record["sha256"]:
            failures.append({"name": record["name"], "reason": "sha256"})
    result = {
        "product": manifest.get("product"),
        "version": manifest.get("version"),
        "checked": len(manifest["files"]),
        "failures": failures,
        "verified": not failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
