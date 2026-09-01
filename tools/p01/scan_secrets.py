#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SKIP_PARTS = {".git", "target", "node_modules", "bin", "obj", "tmp", "evidence", "source-archive", "dist"}
TEXT_SUFFIXES = {".cs", ".json", ".md", ".proto", ".ps1", ".py", ".rs", ".sh", ".toml", ".ts", ".txt", ".yaml", ".yml"}
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "signed_query": re.compile(r"(?i)[?&](?:x-amz-signature|x-goog-signature)=[0-9a-f]{32,}"),
}


def main() -> int:
    findings: list[dict[str, object]] = []
    scanned = 0
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts):
            continue
        if path.stat().st_size > 2_000_000:
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append({
                    "rule": name,
                    "path": path.relative_to(ROOT).as_posix(),
                    "line": text.count("\n", 0, match.start()) + 1,
                })
    report = {"schema_version": "hwpx-agent.secret-scan/v1", "scanned_files": scanned, "findings": findings}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
