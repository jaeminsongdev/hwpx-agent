# P06 table placement v0 to v1

Before v1, the product catalog named table position, inline/floating mode, text wrap and outer
margin capabilities but had no typed bounded placement state or atomic mutation receipt.

`hwpx-agent.table-placement/v1` adds one complete state bound to a validated logical table ID.
Floating position uses explicit reference frames, alignments, signed micrometer offsets and
flow/anchor flags. Wrap and side-flow are one pair, while four nonnegative outer margins remain a
separate field.

Migration is additive. Existing documents are not rewritten. A backend must first read and
validate every required native field before constructing v1; missing or unknown native values are
not defaulted. Operations produce a new state or no partial state. Inline tables retain inactive
wrap/flow and margins, but position or wrap changes require an explicit floating-mode transition.

Direct HWPX mapping, target-specific normalization and licensed Hangul renderer evidence are
separately versioned future boundaries. V1 component success does not enable routing or release.
