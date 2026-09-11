# P08 chart automation v0 to v1 migration

There is no stored v0 chart automation profile, state, request, plan, observation or receipt. V1
introduces the private `hwpx-agent.chart-automation/v1` exact target-binding contract.

Earlier raw action names, unchecked parameter bags, screenshots, synthetic chart XML, table-chart
component fixtures and manual Hangul edits are not v1 state or target evidence and MUST NOT be
relabeled. A caller must construct a fresh complete target profile and chart state, including all
nine capability mappings, identities, data, series, axes, presentation, preservation and flow
bindings, then issue a new v1 request.

V1 has no defaultable profile, state, request or observation fields. Missing, duplicate, unknown,
malformed, stale, unsupported, inconsistent or over-limit input fails. A coherent synthetic
observation cannot migrate into actual-target evidence: installed-Hangul provenance, direct HWPX,
save/reopen, full property readback, export/render and differential evidence require a later fresh
campaign.
