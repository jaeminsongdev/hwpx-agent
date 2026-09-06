# P17-08 durable confirmation replay ledger v2

Date: 2026-09-06
Scope: current-PC local reference approval boundary
Decision: **durable replay increment implemented; P17-08 remains in progress**

The `approval-policy` crate now accepts an injected confirmation replay ledger. Its default remains
the bounded process-local implementation for isolated callers, while `DurableReplayLedger` provides
the required restart- and process-aware path for a side-effect host. The durable implementation is
explicitly opt-in so callers cannot silently claim persistence from the default constructor.

The ledger stores only SHA-256 confirmation identities and bounded timestamps. It never stores the
raw token ID, encoded confirmation, signing key, operation ID, document content or target path.
Entries use fixed-width monotonic names, `create_new` staging, file synchronization and atomic hard
link publication into an immutable sequence. The full bounded sequence and checksum chain are
replayed before every consumption. Gaps, unexpected names, links/reparse points, oversized entries,
invalid schema, duplicate identities, checksum changes, write failures and sequence races fail
closed. An existing publication is re-read: the same identity reports replay; a different identity
reports a retryable ledger conflict. Confirmation identities are retained for the lifetime of this
bounded v1 ledger, including after token expiry, so clock rollback cannot make a consumed token
reusable.

Fourteen tests now pass: the original nine default-deny authorization tests plus five durable tests
covering reopen replay, concurrent single-winner consumption, storage/debug redaction, unknown and
gapped entries, checksum tamper, and capacity enforcement after restart. All-target Clippy passes
with warnings denied; formatting and whitespace checks pass.

This evidence does not authorize or execute a Git commit, automation, network request, print job or
security change. P17-08 remains open until the daemon/MCP effect host revalidates the exact current
plan and consumes a trusted-host confirmation through this durable boundary. Production replacement
of the local HMAC authority and operational ledger lifecycle/rotation also remain separate work.
