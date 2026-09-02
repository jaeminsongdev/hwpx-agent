# Round-trip repair v0 to v1

- Capability: `hwpx-agent.roundtrip-repair`
- From: absent
- To: `v1`
- Compatibility: additive internal core capability; no existing serialized schema is changed

## Added contract

`v1` adds `RoundTripVerifier`, private `RoundTripEvidence`, typed `RoundTripError` and non-mutating `RepairDiagnostic`. The verifier composes the bounded package, graph, preservation, typed-ID, no-op patch and both P03-08 writer contracts. Success requires repeatable same-mode output, truthful metadata and zero untouched-part violations.

The current rule profile is pinned to the exact local 한글 2020 capability. Runtime validation opens only four fixed disposable outputs in fresh x86 STA processes and compares content hashes without saving or recording text.

## Fail-closed changes from no capability

- no evidence is returned after a partial validation failure;
- preserving and normalized outputs cannot be conflated;
- evidence disagreement and writer nondeterminism stop processing;
- diagnostics do not mutate, auto-repair, overwrite, delete or relax a limit;
- stable error metadata contains no document values or absolute private paths;
- the exact 한글 2020 oracle pins input identity, executable identity and process architecture;
- timeout, repair/conversion prompt, residual process or semantic mismatch prevents Gate passage.

## Future migration triggers

A new contract version is required before changing canonical text comparison, changing the synthetic corpus digest, exposing raw bytes or text, applying repair mutations, auto-adjusting finite limits, weakening no-overwrite or fresh-process requirements, accepting a different Hancom executable identity, sharing the 2020 ID profile with another version, or claiming render/save fidelity and 2022/2024 compatibility.
