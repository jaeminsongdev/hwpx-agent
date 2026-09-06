# P17-06 durable remote boundary v3

Date: 2026-09-06
Scope: current PC, durable sync orchestration and authenticated-adapter component
Decision: **third bounded increment implemented; P17-06 remains in progress**

The `local-sync` crate now exposes `pull`, `push` and `checkpoint` through its durable store and CLI.
Offline state rejects all three before the injected remote port is called. Pull records a validated
remote advance or a conflict through the immutable journal without overwriting queued local work.
Push and checkpoint use two journal phases: the first exact append records the caller's idempotency
key before remote I/O; a second exact append records a definitive success, rejection or conflict.
Unavailable or malformed responses keep the first key pending, including after process reopen, and
a retry with a different key fails before the port is called. A concurrent writer appearing after a
remote effect prevents the terminal append and leaves the durable replay key intact.

Mirror snapshot v3 adds the pending checkpoint key. v1 and v2 snapshots remain readable under
their previous constraints and are emitted as v3 after validation. Public CLI JSON reveals only
booleans for pending plan, uncertain push and uncertain checkpoint. It never echoes paths, private
IDs, digests, credentials or idempotency keys. The compiled CLI deliberately uses a fail-closed host
port: an online remote command returns `REMOTE_UNAVAILABLE` until a separately qualified host
supplies an authenticated transport; no implicit network route is enabled.

`AuthenticatedRemoteSyncAdapter` is a strict private adapter over injected credential and transport
traits. Each exchange asks for a new bounded canonical JWT bearer header, zeroizes its owned header
on drop, serializes one bounded operation request, and requires the response to bind the SHA-256 of
the exact request bytes. Unknown response fields, malformed identifiers, wrong bindings and
oversized bodies become `InvalidResponse`. Provider implementations remain responsible for actual
issuer, audience, expiry, `mirror.sync` scope and single-use enforcement. No credential provider,
HTTP client or remote service is claimed by this increment.

The current component passed 31 tests: ten state-machine, five durable-store, seven durable-remote,
four adapter and five real-process CLI tests. All-target Clippy also passed with warnings denied.
Contracts are recorded in `protocol/private/p17-local-sync-cli-v3.json` and
`protocol/private/p17-remote-sync-adapter-v1.json`. These results prove the local durability,
offline/online transition and injected-adapter boundaries only. Actual host transport, credential
custody, daemon/MCP wiring and remote-service evidence remain open, so P17-06 is not PASS and no
Hangul execution is claimed.
