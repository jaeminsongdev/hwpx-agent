#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def main() -> int:
    errors: list[str] = []
    checked = 0
    for markdown in sorted(ROOT.rglob("*.md")):
        if any(part in {"target", "node_modules", ".git", "evidence", "source-archive"} for part in markdown.parts):
            continue
        text = markdown.read_text(encoding="utf-8")
        for raw in LINK.findall(text):
            destination = raw.strip().split(maxsplit=1)[0].strip("<>")
            if not destination or destination.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_text = unquote(destination.split("#", 1)[0])
            if not path_text:
                continue
            checked += 1
            resolved = (markdown.parent / path_text).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"link escapes repository: {markdown.relative_to(ROOT)} -> {destination}")
                continue
            if not resolved.exists():
                errors.append(f"broken link: {markdown.relative_to(ROOT)} -> {destination}")
    print(json.dumps({"checked_local_links": checked, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
