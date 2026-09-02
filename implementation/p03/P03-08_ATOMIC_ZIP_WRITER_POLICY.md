# P03-08 Atomic ZIP writer policy

- State: implemented for current-PC local core and approved disposable 한글 2020 fixtures
- Contract: `hwpx-agent.package-writer/v1`
- Source capability: `hwpx-agent.preserving-patch/v1`
- Product boundary: deterministic private ZIP construction and atomic no-overwrite publication
- Consumer: P03-09 round-trip, repair and actual 한글 2020 reopen Gate

## 1. Writer separation

`PreservingWriter` and `NormalizedWriter` are separate public capabilities. Both accept only a fully validated private `PatchResult`, recheck its path/size/hash identity, construct a private `PackageArtifact`, and reopen it through `BoundedZipReader`, `PackageGraph`, `PreservationReport` and `IdIndex` before returning.

`PreservingWriter` retains every available source part order, compression method and exact expanded bytes. `NormalizedWriter` is opt-in and uses canonical path order, a fixed ZIP timestamp, stored `mimetype`, deflate level 6 for all other parts, and deterministic archive construction. Both writers pin the ZIP creator system to Unix and regular-file permissions to `0644`, rather than inheriting the build host's DOS/Unix default. Preserving mode never silently changes to normalized mode.

## 2. Truthful preservation report

Each output entry records its canonical package path, patch disposition, source/output order, source/output compression method and expanded-byte SHA-256. The report describes only evidence the current reader can prove:

- source order and compression method: `PreservedAvailable` in preserving mode;
- canonical order and pinned compression: `Normalized` in normalized mode;
- raw compressed stream, timestamp and extra fields: `NotPreservedUnavailable` in preserving mode because P03-01 does not retain exact source values;
- normalized metadata: `Normalized`, not source-preserved.

No report upgrades expanded-byte equality into exact compressed-stream equality.

## 3. Private artifact and limits

ZIP bytes stay private inside `PackageArtifact`. Public methods expose only mode, bounded byte count, SHA-256, metadata report and a full integrity recheck. Custom `Debug` prints structural metadata and counts rather than document contents.

Writer output is checked against `WriterLimits::max_output_bytes`, `PackageLimits::max_archive_bytes` and entry count before publication. Reopen reapplies all package, graph, preservation and typed-ID limits. Unsupported ZIP64/data descriptor/encryption/method/link/nested-archive/path forms remain rejected by P03-01.

## 4. Atomic publication protocol

`AtomicPackagePublisher` requires an explicit `SecureWorkspace` and normal relative staging/output paths. It performs:

1. create-new staging write;
2. file `sync_all` and SHA-256 capture;
3. containment-checked staged reopen, size/hash comparison and full bounded package validation;
4. same-volume hard-link publication with destination no-overwrite semantics;
5. published file hash comparison and full bounded reopen.

Absolute/traversal/empty paths, existing links or reparse points, containment escape, destination collision and overwrite are rejected. The public receipt keeps only the requested relative output path and verification booleans.

On non-Windows systems, parent directories are synchronized where supported. On Windows, Rust's portable file API does not provide the same directory `fsync` claim; the contract therefore claims file synchronization plus same-volume atomic hard-link visibility, not directory durability beyond what the platform API proves.

## 5. Failure state model

Before atomic visibility, any injected or validation failure attempts to remove only that unpublished staged artifact. If cleanup itself fails, `writer_staging_cleanup_failed` replaces the original error so abandoned staging is not hidden.

After the hard link succeeds, the destination is never deleted by failure recovery. Parent-sync or staging-cleanup ambiguity is classified as `writer_published_incomplete`; published reopen failures use `writer_published_readback_failed`. The destination is therefore absent before publication or a complete immutable hard-link target after publication. Existing destinations are preserved byte-for-byte.

Fault tests cover checkpoints after stage sync, after staged readback, before atomic publication, after atomic publication and after published readback.

## 6. Validation scope

The committed corpus verifies deterministic same-mode output, explicit mode separation, metadata dispositions, traversal and no-overwrite rejection, small output limits, staged cleanup, atomic publication and every failure checkpoint. Existing patch, ID, preservation, graph and malicious ZIP regressions remain mandatory.

`validate_patch_engine` reads only explicitly supplied approved fixtures, mutates `itemref@linear` in private memory, builds each writer twice and fully verifies both artifacts. It prints only fixture ordinal, profile, counts and determinism booleans. It does not write a document or start 한글/COM/UI.

This v1 policy does not claim source raw-compressed/timestamp/extra-field preservation, crash recovery after OS or hardware failure, actual 한글 reopen/save/render, 100+ fixture coverage, repair behavior, fuzz baseline, user-document completeness, or 2022/2024 compatibility. Those remain P03-09 or later-PC work.
