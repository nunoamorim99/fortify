#!/usr/bin/env python3
"""Build the downloadable install bundles from the plugin source of truth.

    source: plugins/fortify/{commands,skills}
    output: dist/fortify-<version>.zip        full drop-in for .claude/
            dist/fortify-skill-<version>.zip  skill only, for Claude.ai web upload

The version is read from plugins/fortify/.claude-plugin/plugin.json, so a bundle
can never disagree with the plugin manifest.

Usage:
    python3 scripts/build_bundles.py            build into dist/
    python3 scripts/build_bundles.py --check    build, then assert the contents are right

Uses only the standard library so it runs identically on Windows and on CI.
"""

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

NAME = "fortify"
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "plugins" / NAME
DIST = ROOT / "dist"
SKIP = {"__pycache__", ".DS_Store"}


def add_tree(zf: zipfile.ZipFile, source: Path, prefix: str) -> None:
    """Write every file under `source` into the archive at `prefix`, sorted for reproducibility."""
    for path in sorted(source.rglob("*")):
        if path.is_file() and not SKIP.intersection(path.parts) and path.suffix != ".pyc":
            zf.write(path, f"{prefix}/{path.relative_to(source).as_posix()}")


def build() -> tuple[Path, Path, str]:
    for required in (SRC / "commands", SRC / "skills" / NAME):
        if not required.is_dir():
            sys.exit(f"build-bundles: missing {required.relative_to(ROOT)}")

    manifest = json.loads((SRC / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    version = manifest["version"]

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    full = DIST / f"{NAME}-{version}.zip"
    skill = DIST / f"{NAME}-skill-{version}.zip"

    # Full bundle — unzips straight into .claude/. Commands sit one level deeper than in
    # the plugin because a manual install namespaces them by directory
    # (commands/fortify/<cmd>.md -> /fortify:<cmd>).
    with zipfile.ZipFile(full, "w", zipfile.ZIP_DEFLATED) as zf:
        add_tree(zf, SRC / "skills", "skills")
        add_tree(zf, SRC / "commands", f"commands/{NAME}")
        zf.write(ROOT / "INSTALL.txt", "INSTALL.txt")
        zf.write(ROOT / "LICENSE", "LICENSE")

    # Skill-only bundle — Claude.ai web/desktop's Customize -> Skills expects the skill
    # folder itself, with no commands alongside it.
    with zipfile.ZipFile(skill, "w", zipfile.ZIP_DEFLATED) as zf:
        add_tree(zf, SRC / "skills" / NAME, NAME)
        zf.write(ROOT / "LICENSE", f"{NAME}/LICENSE")

    print(f"build-bundles: built from plugins/{NAME} at version {version}")
    for archive in (full, skill):
        with zipfile.ZipFile(archive) as zf:
            print(f"  {archive.relative_to(ROOT).as_posix()}  ({len(zf.namelist())} files)")
    return full, skill, version


def check(full: Path, skill: Path) -> int:
    errors = []
    commands = sorted(p.name for p in (SRC / "commands").glob("*.md"))

    with zipfile.ZipFile(full) as zf:
        names = zf.namelist()
    for required in [f"skills/{NAME}/SKILL.md", "INSTALL.txt", "LICENSE"] + [
        f"commands/{NAME}/{c}" for c in commands
    ]:
        if required not in names:
            errors.append(f"full bundle missing {required}")

    with zipfile.ZipFile(skill) as zf:
        skill_names = zf.namelist()
    if f"{NAME}/SKILL.md" not in skill_names:
        errors.append(f"skill bundle missing {NAME}/SKILL.md")
    if any(n.startswith("commands/") for n in skill_names):
        errors.append("skill bundle should not contain commands/")
    # Everything the skill references must travel with it on the web-upload path.
    for sub in sorted(p.name for p in (SRC / "skills" / NAME).iterdir() if p.is_dir() and p.name not in SKIP):
        if not any(n.startswith(f"{NAME}/{sub}/") for n in skill_names):
            errors.append(f"skill bundle missing {NAME}/{sub}/")

    if errors:
        print("\nbuild-bundles: FAILED", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("build-bundles: bundle contents OK")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="assert bundle contents after building")
    args = parser.parse_args()

    full_zip, skill_zip, _ = build()
    sys.exit(check(full_zip, skill_zip) if args.check else 0)
