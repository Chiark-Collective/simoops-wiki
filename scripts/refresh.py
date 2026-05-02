#!/usr/bin/env python3
"""Refresh planning tool.

Compares manifest tracked commits against source repo HEAD.
Produces a markdown report of clean, modified, new, and stale pages.
Does NOT auto-update wiki pages.
"""

import json
import subprocess
import sys
from pathlib import Path


def get_git_head(repo_path: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_git_log_since(repo_path: str, since_commit: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", repo_path, "log", f"{since_commit}..HEAD", "--oneline"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return [f"error: {result.stderr.strip()}"]
    lines = result.stdout.strip().split("\n")
    return [line for line in lines if line]


def main() -> int:
    wiki_dir = Path(__file__).parent.parent
    manifest_path = wiki_dir / "manifest.json"

    if not manifest_path.exists():
        print("manifest.json not found", file=sys.stderr)
        return 1

    with open(manifest_path) as f:
        manifest = json.load(f)

    source_repo = manifest.get("source_repo", "")
    manifest_head = manifest.get("source_head_commit", "")
    current_head = get_git_head(source_repo)

    print("# Refresh Report\n")
    print(f"Source repo: `{source_repo}`")
    print(f"Manifest HEAD: `{manifest_head}`")
    print(f"Current HEAD: `{current_head}`")
    print()

    if manifest_head == current_head:
        print("Status: **CLEAN** — source repo unchanged since last ingest.")
        return 0

    commits_since = get_git_log_since(source_repo, manifest_head)
    print(f"Commits since manifest: {len(commits_since)}")
    for line in commits_since:
        print(f"- {line}")
    print()

    clean = []
    stale = []
    for page in manifest.get("tracked_pages", []):
        if page.get("last_verified_commit") == current_head:
            clean.append(page["path"])
        else:
            stale.append(page["path"])

    print("## Clean pages (up to date)")
    for path in clean:
        print(f"- `{path}`")
    print()

    print("## Stale pages (need review)")
    for path in stale:
        print(f"- `{path}`")
    print()

    print("## Next steps")
    print("1. Review stale pages against source changes")
    print("2. Update `last_verified_commit` in page frontmatter and manifest")
    print("3. Update `source_head_commit` in manifest to match current HEAD")
    print("4. Record ingest in log.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
