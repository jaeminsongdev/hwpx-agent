# P08-24 object selected-shape canary report

## Result

Result: `5/5 exact-target selected-shape canaries pass / routing disabled / differential not run`.

Promoted attempt `p08-24-object-shape-canary-20260915-05` completed all five candidates in one
licensed Hangul 2020 `11.0.0.9136` x86 session and one unsaved disposable blank document. It took
5.481 seconds, did not time out or stall, opened no Hangul file, saved no document, and left no
owned `Hwp.exe` process.

## Observed runtime results

- Candidate executions: 5/5.
- In-memory semantic effects observed: 5/5.
- Candidate Undo semantic restoration: 5/5.
- Raw-byte Undo restoration: 4/5.
- Z-order setup rollback: 1/1.
- File opens, document saves, external network calls, registry/system-setting changes, Computer Use
  clicks/types, and residual owned Hangul processes: 0 each.

The shadow canary changed its shadow state and Undo restored that state. Its raw post-Undo HWPML was
eight bytes longer solely because an omitted `DRAWTEXT Name` default became an explicit empty value.
The public result therefore records semantic-exact Undo under the narrow
`hwpml2x-drawtext-empty-name-default/v1` rule and preserves `undo_raw_exact=false`; it does not hide
or upgrade the raw mismatch. The other four canaries were raw exact after Undo.

The caption Action returned false on this build but produced a visible structural snapshot change
and exact Undo, so return value is recorded as advisory rather than substituted for the observed
effect. The z-order case used an explicit send-back setup and proved both the candidate Undo and the
setup Undo.

## Preserved predecessors

Attempt 01 established two immediate passes but exposed the shadow serializer difference, an
ineffective initial z-order context, and the caption return-value behavior. Attempt 02 corrected the
z-order context and caption success rule. Attempt 03 captured the exact shadow before/after/Undo
snapshots and proved the only post-Undo difference was the empty serializer-default attribute.
Attempt 04 passed the corrected single shadow canary and is superseded by the complete five-case
attempt 05. None of these predecessor states is relabeled.

## Boundary and next evidence

P08-24 proves a bounded selected-object runtime/Undo slice for five nonmodal Actions only. It does
not qualify all 40 source candidates, execute either known-modal route, enable routing, or establish
any direct-vs-automation differential. The required matrix remains 0/58 green and P08 remains in
progress. The next work is a larger effect-type batch for the remaining safe candidates, followed
by fixture-bound direct-vs-automation comparison for candidates that pass runtime qualification.

