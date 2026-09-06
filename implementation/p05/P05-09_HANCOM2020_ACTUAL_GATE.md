# P05-09 VS-1 actual Hangul 2020 Gate

- Date: 2026-09-07.
- Scope: fixed synthetic VS-1 fixture on this PC's licensed Hangul 2020 `11.0.0.9136` x86 build.
- Result: current-PC P05-09 actual subgate PASS.
- Reasoning/review mode: MAX / HIGH-STRICT.

## Evidence-backed correction

The first actual fixture used `BALANCED_NEWSPAPER` with an explicit column break and a nonempty
backend `colPr/@id`. Hangul saved that ID as empty, causing the strict product inspector to reject
the result. Its PDF also exposed that one complete anchor sentence cannot be assumed to arrive as
one PDF text callback. The original input, saved HWPX, PDF and failed verification remain unchanged
under `fixtures/target-build/p05-09-current-2020-20260906-v1/`; they are not counted as PASS.

The current-target successor makes two evidence-backed changes:

1. explicit-break flow uses ordinary `NEWSPAPER`, while the separate zero-break automatic profile
   remains `BALANCED_NEWSPAPER`;
2. the fixed fixture uses the exact empty backend column ID emitted by this target. The separate
   P05-07 identity-rebinding Gate remains the proof for nonempty-to-empty backend normalization.

The PDF verifier now locates a unique anchor across a normalized sequence of text fragments. A
Hangul/pypdf page-edge callback at `(x=0, y=page-height)` may contribute anchor text but cannot
contribute a layout coordinate or column population count; a later overlapping positioned fragment
must exist. Missing/duplicate anchors, underfilled columns, wrong sides, excessive bottom deltas and
off-page coordinates still fail closed. The existing two-page P05-07 dense PDF replayed with the
updated verifier and retained its exact PNG hashes.

## Actual lifecycle and identities

The user granted the visible access requests. The bounded Registry32 STA client completed COM
creation, input open/read, HWPX SaveAs, close, saved-output reopen/read, PDF export, close and quit.
All 21 progress events completed, the watchdog did not time out, and zero Hwp processes remained.

| Artifact | SHA-256 |
|---|---|
| deterministic v2 input HWPX | `7274a592905e15a0b4a2d58a38a827e45cc4f7e5717e1c8c6c986a9597e91666` |
| saved HWPX | `35169882bd81981fc516a86de8c2082e596b5448fc64f4a0de5fe3095d5a4ea2` |
| exported PDF | `f2df223831be330e81103f0db3d338a6aae3f45b8160b9f808aafaa6af03484d` |
| lifecycle trace | `0b03367ece3bbd0699b3b2f9b4a34bffc05373c16bf75418987742d20b0ac834` |
| progress journal | `17caee23db59fc53c646385e985fdb5877dde46d8e3e48f3400fa84bbf71abbd` |
| predeclared coordinate expectation | `eec108ed9bcc0cb15c6634db9a340d944cc305cdcfe5b428a0ccf076d8f845a8` |
| preserved page-edge callback failure | `472033ee9a78d606964c1a9e89edaa1979e85347c6d191a8736830ec088c6a85` |
| corrected verifier PASS receipt | `1505a422d67376073cb255a03f2b742d07bb1cf552b24e0b76a14c8c7d89b888` |
| verified page PNG | `f5a06415b36eb66c94a7efd0291f1ca4726611b141cd9bc3326d98d652eec7f2` |

Strict inspection reports 11 package parts, five paragraphs, one explicit column break, 80,220
HWPUNIT body width, two equal columns, 1,700 HWPUNIT total gap, seven character styles, twenty
paragraph styles and visible-text SHA-256
`2d93a6073c0703bdc54ccb4a6f12671604a7cac5207fd20744d264a5f93df33f` for both input and output.

## PDF and visual result

The verifier measured one `309739 x 229658` milli-mm landscape page at rotation zero and rendered it
at `1756 x 1302` pixels. The left and right anchors are at x `14973` and `167960` milli-mm,
respectively. It counted 24 positioned left fragments, 17 positioned right fragments and one
unpositioned page-edge callback. The column bottom-baseline difference is 10,145 milli-mm, below the
predeclared 30,000 milli-mm maximum.

The stored PNG was inspected at original resolution. The blue title, two left paragraphs, two right
paragraphs, blue separator and explicit column transition are visible; no overlap, clipping,
unexpected blank column or portrait rotation was found.

## Validation and boundary

- `cargo fmt --all -- --check`: PASS.
- warnings-denied `hwpx-package` all-target/all-feature Clippy: PASS.
- `hwpx-package` all-target/all-feature tests: 218/218 PASS.
- PDF verifier unit tests: 21/21 PASS.
- six bounded Hangul PowerShell static suites: 164/164 PASS.
- prior P05-07 dense two-page PDF replay: PASS with unchanged page PNG digests.

This closes P05-09 only for this fixed current-PC target. It does not qualify arbitrary documents,
Hangul 2022/2024, another PC, production automation, the broader VS-1 table/equation/worker slices,
or the final P05/source/FULL Gate. Those remain separate ledger work.
