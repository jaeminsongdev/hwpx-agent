# P06 table-layout product target v1 to v2

The immutable v1 contract stops at a deterministic cache-repaired target. It does not contain an
actual layout oracle and none of its historical bytes are promoted in place.

V2 introduces `hwpx-agent.p06-05-table-layout-calibrated-target/v1`. Exact licensed Hangul 2020
saved the v1 target successfully, but its regenerated line cache showed that GDI+ preferred width
alone underestimated cell C by one Hangul line-box bucket. A four-micrometer guard also remained in
the same `14000` HWPUNIT line box. Both runs remain valid lifecycle diagnostics and failed semantic
calibrations, not gate PASS evidence.

The successor binds those exact saved HWPX files and advances the left content box to the next
observed 100-HWPUNIT bucket. The calibrated 350-micrometer guard yields cell widths `15120,4723`
HWPUNIT and actual line boxes `14100,3700`. The builder changes only the verified plan and layout
dimensions, writes create-new, rechecks all inputs, and requires exact package/content readback.

There is no automatic migration. A v2 PASS requires all three byte-identical target publications,
the exact current-PC Hangul 2020 lifecycle trace, unchanged visible text and input, saved HWPX
geometry and regenerated line-cache semantics, a valid exact PDF, zero remaining Hwp processes,
and a recorded visual review. The decision is limited to this exact current-PC fixture. Arbitrary
documents, another PC or Hangul version, P06 phase completion, production, and product completion
remain unclaimed.
