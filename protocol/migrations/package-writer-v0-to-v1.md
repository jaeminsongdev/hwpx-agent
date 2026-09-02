# Package writer v0 to v1

- Capability: `hwpx-agent.package-writer`
- From: absent
- To: `v1`
- Compatibility: additive internal core capability; no existing serialized schema is changed

## Added contract

`v1` adds two explicit deterministic writers over the private P03-07 artifact. `PreservingWriter` retains source order, compression method and exact expanded bytes when available. `NormalizedWriter` uses canonical order, fixed timestamp and pinned compression. Both return private verified artifacts and never expose ZIP bytes.

`AtomicPackagePublisher` adds secure create-new staging, file synchronization, staged identity/full reopen, same-volume atomic hard-link publication with no overwrite, and published identity/full reopen. Output paths must be normal relative paths inside an explicit `SecureWorkspace`.

## Fail-closed changes from no capability

- no artifact is returned until package, graph, preservation and typed-ID validation all pass;
- output/archive/entry limits are reapplied before publication;
- unsafe paths, links/reparse points, aliases and existing destinations fail closed;
- pre-publication failure removes only its staged artifact or reports cleanup failure;
- post-publication ambiguity never deletes the complete visible destination;
- preservation metadata distinguishes expanded-byte proof from unavailable raw ZIP metadata;
- normalized output is opt-in and cannot be selected implicitly by preserving mode.

## Future migration triggers

A new contract version is required before exposing raw output bytes, changing compression level/order/timestamp rules, claiming raw compressed-stream preservation, publishing across volumes, allowing overwrite, changing the absent-or-complete failure model, weakening staged or published reopen, broadening accepted ZIP features, or sharing the current 한글 2020 profile with another Hancom build.
