# P10-01 Windows bridge protocol report

- Generated: 2026-09-03
- Implementation commit: `9e441901da0393595f5545ef942797a85136d8c4`
- State: `pass_protocol_compatibility_current_pc_local`
- Reasoning/review mode: `max` / STRICT public-contract, compatibility and security audit

P10-01 adds the additive `hwpx_agent.windows_bridge.v1` protobuf contract shared by the Rust control
plane and the Windows Agent/STA boundary. `WindowsAgentControl` declares the outbound Agent lease,
heartbeat, terminal commit and runtime-probe RPCs. A separate closed command union defines start,
open, execute-plan, save, render, close and cancel messages for a length-delimited per-job named pipe.

The generated Rust and C# message/reflection SDKs and the bridge descriptor are produced from the
single `.proto` source by the repository generator. This task defines the gRPC surface; it does not
claim a live authenticated gRPC connection or generated runtime client/server transport. That is the
next task, P10-02. Named-pipe I/O and the STA message pump remain P10-03.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Versioned source contract | pass | package `hwpx_agent.windows_bridge.v1`, protocol exactly 1.0 |
| Rust/C# generated SDK | pass | generated message/reflection sources and locked descriptor |
| Rust-to-Agent RPC definition | pass | exact `WindowsAgentControl` service and four method descriptors |
| Agent-to-STA command definition | pass | closed typed oneof with seven bounded commands |
| Compatibility | pass | shared fixed wire vector parses, validates and re-emits in Rust and C# |
| Foundation preservation | pass | pre-existing foundation descriptor remains byte-identical |
| Unsafe boundary rejection | pass | paths, raw HAction/ParameterSet names, bad versions, missing authority, oversize frames and unsafe success receipts fail closed |

## Locked artifacts

- Foundation descriptor SHA-256:
  `174f4c25fd24bdb323c29658b10939365964acffc8cbf4a7d236d1d6842a666e`
- Windows bridge descriptor SHA-256:
  `d1896dd578fa42e0eb77abb5f6bae6f239141848798498ed289545e43403ce60`
- Generated C# SHA-256:
  `d0924f36b93f85b17e9f67ec7feced1670201ef2ccc712ad60a446c726ac84a0`
- Generated Rust SHA-256:
  `d00ac79aa19c8d0fb358daad1c330b1a899e1f8c9842fe23a26d4087800c76f5`

Incompatible bridge changes require a new protobuf package version and an explicit migration. The
additive migration from the unchanged foundation worker envelope is recorded under
`protocol/migrations/`.

## Validation evidence

- Rust protocol tests passed `7/7`: the pre-existing generated-model test plus six Windows bridge
  compatibility, descriptor, fixed-vector and negative-boundary tests.
- `cargo clippy --locked -p hwpx-agent-protocol --all-targets -- -D warnings` passed.
- `cargo run --locked -p xtask -- generate --check` passed with generated artifacts current.
- C# restore in locked mode, format check and Release build passed with zero warnings/errors. The
  smoke executable passed the cross-language vector and service-descriptor checks.
- The current checkout and a detached exact-commit clean checkout at `9e44190` each passed the full
  five-lane bootstrap: `linux-core`, `windows-worker`, `widget`, `docs`, and `security`.
- The exact-commit clean checkout remained Git-clean after validation. Security checks found zero
  secrets, vulnerabilities and forbidden licenses; its generated SBOM contained 231 components.
- Offline Linux validation passed in image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f` with network disabled,
  repository/Cargo registry read-only and executable tmpfs. Protocol tests passed `7/7` and Clippy
  passed with warnings denied.
- The first Docker invocation failed before product tests because `/target` was mounted non-
  executable. Re-running the identical source/image with an executable tmpfs passed; the failed
  invocation is retained as environment diagnostics and was not counted as product evidence.

## Strict self-review

- Change risk: high; this is a new public cross-process wire contract and generator path.
- Review result: APPROVE for the bounded P10-01 scope.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- The public command union contains no raw XML, arbitrary filesystem path, generic action string,
  ParameterSet map, document body or binary payload.
- UUID authority, fencing, deadlines, artifacts, handles, limits, receipts and event sequences are
  validated with stable privacy-safe error categories in Rust. The C# named-pipe ingress validates
  the same command/version/path/raw-action/frame invariants.
- Tests were not weakened and timed-out, environment-failed, synthetic or descriptor-only evidence
  was not promoted into a live transport, COM, render, production or cross-version claim.

## Unverified boundary

P10-01 does not prove live gRPC authentication, lease/fencing persistence, artifact upload/staging,
sandbox filesystem enforcement, named-pipe ACLs or I/O, STA apartment behavior, HwpObject lifecycle,
modal handling, process recycling, another PC/version, production deployment or distribution. These
remain P10-02 through P10-10 work.

## Next exact task

Implement P10-02 as an outbound authenticated Windows Agent service with bounded lease acquisition,
fencing-aware heartbeat/commit, checksum-verified artifact staging, a private per-job sandbox and
no-overwrite upload receipts. Prove stale-lease/no-duplicate-effect behavior with an end-to-end test
at reasoning effort `max`.
