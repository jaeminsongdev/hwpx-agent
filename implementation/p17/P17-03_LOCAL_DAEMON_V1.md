# P17-03 local companion daemon v1

Date: 2026-09-06
Scope: current PC, local-only, Hangul 2020 target profile
Decision: **implementation complete; canonical qualification rerun pending**

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

Clean implementation commit `f3a27a694e770df8dd09523592db5dfbabe223aa` produced run
`23cfab98b711491aacb2940ca7cf32a8`, which passed all 11 behavioral checks. The harness built the locked binary
offline and exercised authenticated health, wrong-session rejection, bounded existing-file
admission, traversal rejection, output-name admission, overwrite rejection, unknown-field
rejection, redaction, graceful EOF shutdown and exact temporary cleanup in one real child process.

That run is not promoted to the immutable qualification: Windows newline translation wrote its
receipt with a CRLF terminator, while the qualification contract requires canonical UTF-8 JSON with
one LF terminator. The original receipt remains untouched. The writer now emits explicit bytes and a
fresh clean-commit run is required before this card can be marked PASS.

The crate has 10 Rust tests, including an actual binary smoke and a real Windows junction escape.
Target and full-workspace tests plus Clippy `-D warnings` pass. The acceptance harness has three
Python contract tests. No new external dependency version was added.

## Explicit non-claims

- No plugin or marketplace was installed and no actual Codex MCP session was opened.
- No persistent credential store, PostgreSQL lifecycle, renderer connection or remote sync exists in
  P17-03.
- No Hangul process, access prompt, COM call, user document or network connection was used.
- P17-04 and the P17 phase Gate remain open.
