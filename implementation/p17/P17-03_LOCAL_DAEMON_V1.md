# P17-03 local companion daemon v1

Date: 2026-09-06
Scope: current PC, local-only, Hangul 2020 target profile
Decision: **PASS for the bounded current-PC local daemon; Codex installation and Hangul remain open**

## First bounded increment

`local-companion-daemon` is the private Rust child process behind the future Codex stdio bridge. It
does not add a public MCP tool, launch Hangul, connect to a network, mutate a document or install a
plugin in this increment.

- Configuration is a bounded regular JSON file with one to eight canonical workspace roots.
- The only admitted profile is `hancom-2020-x86-11.0.0.9136`; automation and networking must both
  remain `disabled`.
- Every private request carries a process-scoped 32-byte base64url session token. Authentication and
  exact JSON shape validation precede filesystem inspection.
- `health` returns only a target profile, booleans, workspace count and configuration digest.
- `authorize_path` accepts only a workspace ID plus a safe relative path. Existing reads require a
  regular bounded file. New names must be absent under an existing `output/` parent.
- Absolute paths, traversal, links/reparse points, NTFS alternate data streams, reserved device
  names, oversized files, unknown fields and overwrite attempts fail closed.
- Responses never contain configured roots, the supplied path, token or document content.

The machine-readable boundary is `protocol/private/p17-local-daemon-v1.json`. P17-04 will add the
stdio MCP bridge, process startup/authentication, personal plugin composition and fresh-install
smoke. Credential persistence, PostgreSQL lifecycle, plan-review E2E and Hangul automation remain
open and must not be inferred from this increment.

## Actual evidence

The first clean run `23cfab98b711491aacb2940ca7cf32a8` passed all 11 behavioral checks but is
not promoted: Windows newline translation wrote its receipt with a CRLF terminator, while the
qualification contract requires canonical UTF-8 JSON with one LF terminator. That original receipt
remains untouched as failed qualification history.

Clean repair commit `ca1a332505c07454b517fd780b369fae184e2975` produced qualifying run
`4b1c023ca40c4a02b6dc25ac77ca656b`. It passed all 11 checks and emitted a canonical LF receipt with
SHA-256 `d290e57a81d2b912b1902baf6b85073192fdc1582475112f0c957a133cb53a92`.
The harness built the locked binary offline and exercised authenticated health, wrong-session
rejection, bounded existing-file admission, traversal rejection, output-name admission, overwrite
rejection, unknown-field rejection, redaction, graceful EOF shutdown and exact temporary cleanup in
one real child process.

The crate has 10 Rust tests, including an actual binary smoke and a real Windows junction escape.
Target and full-workspace tests plus Clippy `-D warnings` pass. The acceptance harness has three
Python contract tests. No new external dependency version was added.

## Explicit non-claims

- No plugin or marketplace was installed and no actual Codex MCP session was opened.
- No persistent credential store, PostgreSQL lifecycle, renderer connection or remote sync exists in
  P17-03.
- No Hangul process, access prompt, COM call, user document or network connection was used.
- P17-04 and the P17 phase Gate remain open.
