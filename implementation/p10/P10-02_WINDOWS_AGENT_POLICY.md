# P10-02 Windows Agent policy

- Component: `HwpxAgent.WindowsAgent`
- Scope: outbound control-plane client, lease/fencing, local staging/sandbox/upload and recovery journal
- Current target: licensed local Hangul 2020 `11.0.0.9136` x86 profile
- Reasoning effort: `max`

## Process boundary

The Windows Agent never exposes a public listener. `GrpcWindowsAgentControlClient` makes the four
`WindowsAgentControl` unary calls declared in P10-01 through a .NET gRPC `CallInvoker`. A production
channel accepts only an absolute HTTPS endpoint without user-info, query or fragment. Every request
uses a bounded deadline, a size limit and an in-memory bearer credential supplied by the host. The
credential is not written to the workspace, journal, artifact store, receipt or diagnostic.

Client-certificate TLS can be supplied through the standard `HttpMessageHandler`; certificate
selection and host credential provisioning belong to deployment configuration. Disabling TLS
certificate validation is not an Agent feature.

## Lease and fencing

Before any staging or execution the Agent validates:

- canonical lowercase Agent, lease, request, job, trace and execution UUIDs;
- exact protocol 1.0 request shape and a fresh random nonce digest;
- a nonzero fencing token and unexpired lease;
- exact current target-profile ID;
- three required, checksum-addressed, read-only and handle-distinct input artifacts;
- finite command/job/memory/output/event limits; and
- current-scope network/clipboard/macro/OLE deny policy plus semantic policy IDs.

An append-only file journal atomically claims the complete assignment binding before work. A held
exclusive lock prevents concurrent duplicate execution. A terminal protobuf receipt is flushed and
atomically published before its commit RPC. The same terminal assignment replays the byte-identical
receipt without calling the executor. A released claim without a terminal receipt is never retried as
if nothing happened; it becomes `UNKNOWN_OUTCOME`. Reusing an execution ID with any assignment or
fencing drift fails before executor or commit.

## Artifact and sandbox boundary

The public protocol supplies no path. Each `sandbox_handle` is a validated lowercase opaque token and
is resolved only below a configured Agent workspace. Workspace, journal, sandbox and artifact-store
roots have immutable markers; filesystem roots and reparse-point roots are rejected. A job sandbox is
created with no-overwrite semantics from the canonical execution ID.

All three inputs are copied through a bounded stream, and their exact length and SHA-256 are checked
before atomic publication as read-only staged files. The executor receives an `AgentJobContext`, not
an absolute path or artifact-store capability. It can open declared staged handles read-only and
create a new output handle once.

Outputs are closed, bounded by the lease, rehashed and uploaded through a content-addressed artifact
store. The lease's aggregate output-byte quota is enforced by the write streams, rechecked across the
complete result before any upload, and checked again while each artifact is published. Every upload
stream is validated even when its object already exists; an identical retry is accepted, while
mismatched bytes fail without replacing the existing object. Sandboxes are removed only when they
are a marked child of the configured sandbox root. Cleanup does not traverse reparse points.

## Receipt boundary

Successful receipts require `ValidationState.PASSED`, exact input identity, source-preserving status,
no diagnostic and no execution-side external network or Registry/system-setting mutation. Failure,
cancellation and unknown-outcome receipts require a typed error and a SHA-256 safe-detail category.
Exception messages, filesystem paths, bearer credentials and document text are never copied into a
receipt. The control-plane response must return the exact local receipt digest before a commit is
accepted.

## Compatibility and negative evidence

The bounded smoke suite drives the real Agent service through the real authenticated gRPC client
surface with a scripted in-process `CallInvoker`. It proves successful lease/stage/execute/upload/
commit, terminal replay, exclusive concurrent ownership, stale heartbeat rejection, abandoned-claim
unknown reconciliation, fencing drift rejection, checksum failure before execution, commit-digest
recovery, idempotent validated upload, no-work behavior, profile mismatch rejection and HTTPS/token/
root boundary rejection. Probe reports also require their declared evidence object to exist and match
its digest before the outbound report call.

This is an in-process E2E of the P10-02 component contract. It does not claim a live remote TLS
endpoint, cloud object store, Windows Service installation, named-pipe transport, STA message pump,
COM/HwpObject execution, sandbox ACL/encryption, secure deletion, interactive desktop isolation,
actual Hangul behavior, another PC/version or production deployment. The named-pipe/STA process is
P10-03; lifecycle and later isolation/runtime proof are P10-04 through P10-10 and P13.
