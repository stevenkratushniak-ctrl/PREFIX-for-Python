"""Retain unique technical build files in an unpublished existing-repo draft.

Release-asset storage has no Actions artifact-storage allowance. This helper
never publishes, edits an existing asset, changes the customer offer or signs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "stevenkratushniak-ctrl/PREFIX-for-Python"
TAG = "prefix-distribution-001-review"
TITLE = "PREFIX-DISTRIBUTION-001 technical build staging"


def gh(*arguments, check=True):
    result = subprocess.run(["gh", *arguments, "--repo", REPOSITORY], text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True)
    parser.add_argument("--paths", nargs="+", required=True)
    args = parser.parse_args()
    assert os.environ.get("GITHUB_REPOSITORY") == REPOSITORY
    assert os.environ.get("GITHUB_REF") == "refs/heads/codex/prefix-distribution-001"
    assert all(c.isalnum() or c in "-_." for c in args.kind)
    assert ".." not in args.kind and not args.kind.startswith(".")
    run, attempt = os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_RUN_ATTEMPT"]
    view = gh("release", "view", TAG, "--json", "isDraft,name,targetCommitish", check=False)
    if view.returncode:
        # Concurrent jobs may reach this once; a racing creation is read back.
        create = gh("release", "create", TAG, "--draft", "--prerelease",
                    "--target", os.environ["GITHUB_SHA"], "--title", TITLE,
                    "--notes-file", str(ROOT / "DISTRIBUTION_CANDIDATE.md"), check=False)
        view = gh("release", "view", TAG, "--json", "isDraft,name,targetCommitish")
    state = json.loads(view.stdout)
    if state.get("isDraft") is not True or state.get("name") != TITLE:
        raise RuntimeError("staging release identity/draft guard refused")
    out = ROOT / "qualification-results/staging"
    out.mkdir(parents=True, exist_ok=True)
    archive = out / f"prefix-distribution-001-{run}-{attempt}-{args.kind}.zip"
    included = []
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for argument in args.paths:
            candidate = (ROOT / argument).resolve()
            assert candidate.is_relative_to(ROOT)
            if not candidate.exists():
                continue
            paths = [candidate] if candidate.is_file() else sorted(candidate.rglob("*"))
            for path in paths:
                if not path.is_file():
                    continue
                relative = path.relative_to(ROOT)
                if any(part in {".git", "node_modules", ".gradle", "test-entitlement", "synthetic-entitlement"}
                       for part in relative.parts):
                    raise RuntimeError("private/cache path refused")
                package.write(path, relative.as_posix())
                included.append(relative.as_posix())
    if not included:
        raise RuntimeError("no technical evidence/artifact files exist")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    gh("release", "upload", TAG, str(archive))
    receipt = {"draft": True, "published": False, "repository": REPOSITORY, "tag": TAG,
               "source_commit": os.environ["GITHUB_SHA"], "run_id": run, "attempt": attempt,
               "asset": archive.name, "bytes": archive.stat().st_size, "sha256": digest,
               "included": included, "commercial_replacement_authorized": False}
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
