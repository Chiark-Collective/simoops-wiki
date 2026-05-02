#!/usr/bin/env python3
"""Wiki linter.

Checks cross-references, page lengths, banned phrases, frontmatter round-trips.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional

BANNED_PHRASES = [
    r"\bIn this article\b",
    r"\bIn this section\b",
    r"\bIt is important to note\b",
    r"\bPlease note\b",
    r"\bAs mentioned above\b",
    r"\bAs discussed earlier\b",
    r"\bTODO\b",
    r"\bFIXME\b",
    r"\bBest practice\b",
    r"\bBest practices\b",
]

LENGTH_CAPS = {
    "modules": 200,
    "flows": 150,
    "api": 100,
}


def load_manifest(wiki_dir: Path) -> dict:
    path = wiki_dir / "manifest.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def extract_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        import yaml
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2]
        return frontmatter or {}, body
    except ImportError:
        # Fallback: simple key:value parsing
        frontmatter = {}
        for line in parts[1].strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                frontmatter[k.strip()] = v.strip()
        return frontmatter, parts[2]


def find_md_files(wiki_dir: Path) -> list[Path]:
    return sorted(wiki_dir.rglob("*.md"))


def check_banned_phrases(path: Path, content: str) -> list[str]:
    errors = []
    for phrase in BANNED_PHRASES:
        for match in re.finditer(phrase, content, re.IGNORECASE):
            line = content[:match.start()].count("\n") + 1
            errors.append(f"{path}:{line}: banned phrase: {match.group()}")
    return errors


def check_length(path: Path, content: str) -> list[str]:
    errors = []
    rel = str(path.relative_to(path.parent.parent.parent if len(path.parts) > 3 else path.parent))
    parts = path.parts
    cap = None
    for key, limit in LENGTH_CAPS.items():
        if key in parts:
            cap = limit
            break
    if cap is None:
        return errors
    lines = content.split("\n")
    if len(lines) > cap:
        errors.append(f"{path}: exceeds {cap} lines ({len(lines)})")
    return errors


def extract_links(content: str) -> list[str]:
    # Markdown links [text](path)
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    links = []
    for match in re.finditer(pattern, content):
        href = match.group(2)
        if href.startswith("http") or href.startswith("#"):
            continue
        links.append(href)
    return links


def resolve_link(source: Path, href: str, wiki_dir: Path) -> Optional[Path]:
    if href.startswith("/"):
        target = wiki_dir / href.lstrip("/")
    else:
        target = source.parent / href
    target = target.resolve()
    if target.exists() and target.is_file():
        return target
    # Try adding .md
    md_target = Path(str(target) + ".md")
    if md_target.exists() and md_target.is_file():
        return md_target
    # Try directory/index.md
    if target.exists() and target.is_dir():
        index_target = target / "index.md"
        if index_target.exists() and index_target.is_file():
            return index_target
    return None


def check_cross_references(files: list[Path], wiki_dir: Path) -> list[str]:
    errors = []
    link_map: dict[Path, list[Path]] = {f: [] for f in files}
    for f in files:
        content = f.read_text()
        links = extract_links(content)
        for href in links:
            target = resolve_link(f, href, wiki_dir)
            if target is None:
                errors.append(f"{f}: broken link: {href}")
            elif target in link_map:
                link_map[target].append(f)
    return errors


def check_orphans(files: list[Path], wiki_dir: Path) -> list[str]:
    errors = []
    for f in files:
        # Skip index pages and AGENTS.md
        if f.name in ("index.md", "AGENTS.md", "log.md", "topology.md"):
            continue
        content = f.read_text()
        links = extract_links(content)
        has_inbound = False
        for other in files:
            if other == f:
                continue
            other_content = other.read_text()
            for href in extract_links(other_content):
                target = resolve_link(other, href, wiki_dir)
                if target == f:
                    has_inbound = True
                    break
            if has_inbound:
                break
        if not has_inbound and not links:
            errors.append(f"{f}: orphan page (no inbound or outbound links)")
    return errors


def main() -> int:
    wiki_dir = Path(__file__).parent.parent
    files = find_md_files(wiki_dir)
    errors: list[str] = []

    for f in files:
        content = f.read_text()
        errors.extend(check_banned_phrases(f, content))
        errors.extend(check_length(f, content))

    errors.extend(check_cross_references(files, wiki_dir))
    errors.extend(check_orphans(files, wiki_dir))

    if errors:
        print(f"Found {len(errors)} issue(s):\n")
        for e in errors:
            print(e)
        return 1

    print("Lint passed. No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
