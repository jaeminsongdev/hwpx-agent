# P17-01 Codex bundle core v1

Date: 2026-09-06
Scope: deterministic unregistered Codex package core
Decision: **package core implemented; P17-01 remains in progress**

The P17 bundle composer combines the immutable P16 universal package base, all nine qualified
workflow skills, the bounded `hancom-document-engineer` agent, and five workflow commands into one
19-entry archive. It does not rewrite the P16 base. Archive generation is deterministic and
no-overwrite: fixed timestamps, stored entries, fixed regular-file permissions, sorted paths and
hard-link publication from a synchronized temporary file.

Validation rejects missing or extra entries, duplicate ZIP paths, POSIX or Windows traversal,
absolute/drive paths, links, oversized source/archive/expanded bytes, noncanonical metadata,
placeholder text, bearer credentials, absolute Windows paths, raw HAction identifiers and raw HWPX
XML markers. Agent frontmatter and every command-to-skill binding are checked. The composed
manifest adds only `skills: "./skills/"`; auto-discovered `agents/` and `commands/` require no
unsupported manifest field.

Seven bundle tests pass, including deterministic rebuild, exact entry set, connection omission,
negative source checks, traversal rejection and no-overwrite publication. The predecessor P16 base
and skills suites pass 17/17 each, and the standard plugin validator accepts the tracked base.

The exact committed source `0c0e3e4c54089baca318fd971c9f44562a052c23` produced ignored run
`81de11bb748649cbbae25972cdbd30df`. Its 19-entry, 20,501-byte archive has SHA-256
`586cf63fc1bf9be608e4ea225c56d8f02457c516d47210e661e8128968783e5a`; extraction and the standard
plugin validator both passed. The archive and extracted tree remain local evidence under
`artifacts/p17/packages/` and are not tracked product source.

This artifact deliberately contains no `.app.json` or `.mcp.json`. A remote app mapping cannot be
created honestly until an actual Developer mode registration receipt supplies the real app ID and
HTTPS MCP endpoint. The current-PC local MCP plugin remains separately qualified; absolute local
runtime paths are not copied into this portable archive. Therefore the package core exists, but
P17-01 is not PASS and P17-02 remote E2E remains unverified.
