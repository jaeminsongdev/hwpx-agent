# P09-28 native-form public export and exact source successor report

Updated: 2026-10-02. State: `public_export_source_qualified_non_gate`.

## Result

The actual P09-27 production reader/builder/lowerer is now connected through
the `hwpx-package` public library. Only one private module declaration and
one explicit public export block were added to the shared lib. No existing
P08/P09 exports or implementation were rewritten. Subtracting both exact
literal spans reproduces the archived P09-23/v2 lib byte for byte; its unchanged
v2/v1 projection functions reproduce their exact predecessors and the P08 lib.

- Current lib SHA:
  `d39fd55db3e98dc3130ca8aca8f35d1dd67557b4bb2f127b9e7ee2c439daa987`.
- Preserved v2 lib SHA:
  `1eae8f6896cb5bb70762ac41e00d0fa017af794cb6dfaec8463879eb1f366d09`.
- Final r02 public source capsule:
  `evidence/p09-28-native-form-public-export-source.current-2020.r02.v3.json`,
  SHA `cc9318ba2f75d16dad15f59ee5a6d704fcca14e6e772b4740d5b6d94a14026bc`.
  Exclusive publication and independent `--verify` reproduce exact bytes.

All 18 preceding real/synthetic integration cases execute through public
library imports in `crates/hwpx-package/tests/native_form_hwpx_public.rs`.
Their complete helper/assertion/test body is byte exact to the frozen
pending-export target. The new harness cannot include the production source
file or change a case and still qualify public execution. The original
production module and pending-export Rust tests remain unchanged and execute
as before. Public component linkage is not public action/product routing.

## Historical preservation and actual failures

Before any mutation, preserve four exact predecessor files in
`source-archive/p09-28-pre-public-export/`: shared lib, P09-23 bridge tests,
P09-27 observation tests and P09-22 target tests. The new source verifier
requires all original receipt/source pins; only those four named pins may
resolve to corresponding byte-exact archives. Unknown edits, missing or
duplicate spans, wrong archive/receipt/source identities are not admitted.
The old verifiers were actually invoked, not mocked or digest-patched:

- P09-21 current: FAIL `current_shared_lib_identity_changed`.
- P09-23/v2 current: FAIL `current_successor_lib_identity_changed`.
- P09-27 pending-export current: FAIL
  `native_form_observation_pending_export_boundary_changed`.

Original P09-23/v2, P09-27 and both P09-22 native capsules remain unchanged.
Archived source proof is explicitly not a current full old verifier PASS,
renewed native evidence or green/Gate qualification. P09-22's original mutation
tests still run against explicitly archived v2 lib and original test-source
inputs in disposable historical fixture roots, with every original rejection
case retained. Current exports receive independent source/public-library tests.

The original P09-25 compatibility-failure receipt genuinely reproduces SHA
`a5f86b629ef65d31f3eb49e9cbfacb081aec2165910ed033300b32a80c81e307`.
The original P09-26 note-failure receipt genuinely reproduces SHA
`a03e6461d94010d7b1ccfbf9eecdb8e1d06389f3a690363e7b414d4cda9f2347`.
P09-12 genuinely passes its four implementation and four source locks; its
actual/native/render/differential claims remain NOT_RUN. The old native
missing-ID/anchor/shape failures, note raw binding/body-numbering failures,
CLICK_HERE 920-pixel style mismatch and caption visual gaps remain visible.

## First quality failure and explicit r02 repair

The first capsule SHA
`41a9f4d1fc27d6d1cf3257d7584582c5e022511258ecaa8081a43755575b2280`
is retained at `evidence/p09-28-native-form-public-export-source.current-2020.v3.json`.
Its source/public-case checks passed, but full strict Clippy subsequently failed
on `item in documentation is missing backticks`. The exact first public-test
source, SHA `e515e25d42ebab465546967189206223c0c67df92488df9f6d17a3cc939b6fbd`,
was archived before repair. r02 changes only Markdown backticks in the header
comment; the other eight of nine capsule source entries and every test body
remain exact. The first capsule is historical, not byte-reproduced current
source after this change. No failed result or original evidence was deleted.
See `P09-28_PUBLIC_R02_CLIPPY_REPAIR.md` for the explicit revision boundary.

## Final verification

- Public-library Rust target: 18/18 PASS, no ignored/skipped cases.
- Seven new source/export Python tests PASS, including body/direct-source
  inclusion tamper, archive/receipt tamper and actual predecessor failures.
- Full P09 Python suite: 206/206 PASS, no skips.
- Workspace Rust, all targets/features, locked/offline: 1,801 PASS across
  271 suites, zero failures. Three pre-existing ignored native/external cases
  remain ignored and are not claimed qualified by this command.
- Workspace Clippy, all targets/features, locked/offline, `-D warnings`: PASS
  after the explicitly recorded header repair.
- All 25 real legacy source validators audited: nine original full-lib-lock
  failures retained with unchanged non-lib implementation locks; 16 genuine PASS.
- `cargo fmt --all -- --check` and `git diff --check`: PASS.
- Read-only process inventory: zero Hwp processes. No new native/COM/UI session,
  permission action, registry/trust setting/network change, original edit,
  deletion/move, staging, commit or push occurred in this source step.

## Remaining product work

Public component linkage is complete, but package-part style/border/resource/
reference/protection bindings are still caller inputs, not independently read
by this section component. Build the full production package binding layer,
complete actual-source property/tab cases and independent saved/reopened oracle.
Prepare all dependency-ready native cases together and execute one continuous
batch; only the user handles any sequential permission dialogs. Do not rerun
unchanged or unimplemented cases just to increase the permission queue.

Production routing/fallback, native targets, render/comparator, mixed-document
and other P09-family closure remain incomplete. The conformance authority still
has 46 owned + 7 P11-deferred rows, 35 unit/11 static integration, zero oracle/
green. The full P09-P20 objective remains active. No P10 implementation starts
before an authoritative P09 Gate; this source checkpoint is not that Gate.
