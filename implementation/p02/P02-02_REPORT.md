# P02-02 Help Extractor Report

- Completed: 2026-09-02
- Audited source commit: `c085f0b72aaddac647bb0785fdec6b1390bd92d9`
- Task state: `pass_current_pc_local`
- Review: `STRICT / xhigh`, blocker/major/minor `0/0/0`

## Delivered

- Read-only HTML help extractor bound to one exact `hwpx-agent.source-lock/v2` entry and source SHA-256.
- Strict UTF-8/CP949 decoding, bounded input/text/record counts, script/style/template/noscript exclusion and title/heading-only metadata extraction.
- Original anchor locators when present; otherwise exact line/column positions in the SHA-locked snapshot.
- Deterministic sorted `SourceRecordV1[]`, stable record IDs and contiguous extraction ordinals.
- Input identity revalidation using lstat/open/fstat/restat, symlink/junction denial and source hash recheck.
- Normal relative output paths only, Windows reserved-path denial, existing normal parent requirement, file fsync and hard-link atomic no-overwrite publication.
- Restricted sources may publish only under Git-ignored `implementation/p02/evidence`; no restricted record is committed.
- Independent output verifier binds every record back to source-lock ID, source ID/SHA, locator, ordinal and schema/semantic validation.

## Validation

- Synthetic suite: 8/8 passed on Windows and official Python 3.13.13 Linux image `sha256:355bfa66770995d7e9a0da4b3473b44d0cb451f6b56f5615ad9c39e3c4eca03f` with read-only repository mount.
- Negative coverage: tampered source, non-help lock entry, traversal, missing heading, overwrite, symlink input, reversed versions, Windows reserved path and restricted-output escape.
- Current repository FULL bootstrap: 5/5 lanes passed; secrets/vulnerabilities/forbidden licenses 0.
- Clean clone at `c085f0b`: FULL bootstrap 5/5 passed, private evidence absent by design, post-run Git status changes 0.
- Actual locked snapshot: `hancom-automation-web-20260901`, restricted/local-only, source SHA-256 `48dbd14b35b40c320cc97836520bbe215f1bb5aab9a035cf6bac2e1fd8dc710f` before and after extraction.
- Actual output: 4 records, 4 source-position locators, verifier errors 0, deterministic output SHA-256 `5ef0e749c04efaf856ee07131ed7ae9cbd7449cbc37756d4cccdbce9d07fd7b8` across repeated final emissions.

The authoritative actual output remains local at [private Help records](evidence/help/hancom-automation-web-20260901.records.v4.json). Its record text is not reproduced in this report.

## Preserved boundaries

- Source archive and installed CHM were not copied, modified or committed.
- 한글/COM/UI and user documents were not opened.
- Restricted source output cannot target a public repository path.
- The extractor emits metadata only; it never executes an action or publishes raw HTML.
- This task proves one exact official help snapshot adapter, not 100% disposition of every help item; full disposition remains P02-06.

## Failed checks retained

- The standalone verifier initially failed when invoked by file path because the repository package root was absent from `sys.path`; direct execution was fixed and rerun.
- All negative fixtures remain in `tools/p02/tests/test_help_extractor.py`.

## Next exact task

Implement `P02-03 Automation extractor` over the SHA-locked ActionTable/ParameterSet/Automation/Event PDFs. Preserve field types, descriptions, source page/section and source hash; publish restricted records only to private evidence; reject parser ambiguity rather than inventing action/parameter identifiers. Recommended reasoning effort: `xhigh`; P02 final Gate: `max`. No user local operation is required at task start.
