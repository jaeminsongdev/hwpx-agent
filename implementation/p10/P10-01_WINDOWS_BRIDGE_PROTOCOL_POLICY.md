# P10-01 Windows bridge protocol policy

- Contract: `hwpx_agent.windows_bridge.v1`
- Scope: protocol and generated SDK only
- Current target: licensed local Hangul 2020 `11.0.0.9136` x86 profile
- Reasoning effort: `max`

## Process and trust boundary

`WindowsAgentControl` defines the Rust control-plane to Windows Agent surface. The Agent is the
outbound gRPC client and exposes no public worker RPC. Its four v1 methods are `AcquireLease`,
`Heartbeat`, `CommitExecution` and `ReportProbe`. Lease assignments bind canonical request/job/trace/
execution IDs, a nonzero fencing token, expiry, exact target profile, checksum-addressed staged
artifacts, finite limits and an explicit security policy.

`StaCommandEnvelope` and `StaCommandReceipt` define length-delimited protobuf frames for a per-job,
authenticated local named pipe. The STA process receives a closed oneof of start, open, execute plan,
save, render, close and cancel commands. There is no generic action string, ParameterSet map, raw
document body or binary payload. `sandbox_handle` is a path-free token resolved only inside the job
sandbox; absolute/relative paths are invalid.

The `.proto` service descriptor and message SDK are generated for Rust and C# from one source. This
task does not connect a network listener, named pipe or COM object. Authenticated gRPC transport is
P10-02 and the STA message pump is P10-03.

## Bounded validation

- Protocol is exactly major 1, minor 0; unsupported versions fail before staging.
- A named-pipe frame is at most 1 MiB.
- UUID authority fields are canonical lowercase D form and fencing/deadline values are nonzero.
- Artifact IDs and lowercase SHA-256 values are typed; artifacts are 1 byte through 1 GiB.
- Sandbox handles use lowercase ASCII letters, digits, `_` and `-`, begin with a letter and are 3--64
  bytes. Dots, slashes, drive separators and traversal are impossible.
- Input, OperationPlan and validation-contract artifacts are read-only. Output slots are handles, not
  paths.
- Resource limits are finite: command 1--900 seconds, job through 3,600 seconds, memory 64 MiB--16
  GiB, output through 1 GiB and events 1--10,000.
- `haction` and `parameterset` identifiers are rejected case-insensitively. Only semantic dotted IDs
  and a signed binding-bundle identity cross the pipe.
- Success receipts cannot claim input mutation, raw document logging, external network use, registry
  or system-setting changes, or carry an error diagnostic.
- Public validation errors contain stable categories only and never echo IDs, paths, document text or
  private diagnostic detail.

## Compatibility evidence

The existing foundation descriptor remains byte-locked at SHA-256
`174f4c25fd24bdb323c29658b10939365964acffc8cbf4a7d236d1d6842a666e`. The new baseline separately
locks the bridge descriptor and generated Rust/C# SDKs. Rust and C# parse, validate and re-emit the
same fixed `StaOpenDocumentCommand` wire vector. Descriptor tests require the exact package, imported
foundation dependency, service and four RPC methods. Negative tests cover version drift, zero
fencing, missing commands, traversal-like handles, raw automation names, oversized frames, excessive
lease slots and unsafe success receipts.

## Unverified boundary

P10-01 proves schema generation, descriptor stability and in-process compatibility only. It does not
prove gRPC authentication, lease/fencing persistence, named-pipe ACLs/framing, STA apartment/message
pump behavior, actual HwpObject lifecycle, modal handling, timeout reconciliation, process isolation,
another PC/version, production or distribution. Those remain explicitly unverified for P10-02--10.
