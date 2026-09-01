# P00-07 Provider License Matrix

- State: `passed_disabled`
- Default provider policy: `disabled`
- Date: 2026-09-01
- Decision approval: `explicit_user_blanket_approval`

| Provider/capability | Documentation state | License/contract state | Release state | Required next evidence |
|---|---|---|---|---|
| WebHWP / 웹한글 기안기 | Public developer guide archived | Purchase/deployment terms not supplied | `disabled` | Product version, server topology, contract, concurrency, font and support terms |
| Hancom integrated document viewer/conversion | Public overview only | Not supplied | `disabled` | API/SDK contract, formats, limits, data handling |
| Hancom OCR | Public overview only | Not supplied | `disabled` | API/SDK contract, data retention, accuracy/SLA |
| Hancom Sign | Public API overview only | Not supplied | `disabled` | API contract, webhook security, legal signature scope |
| External OCR | No provider selected | Not applicable | `disabled` | Provider selection ADR and data-processing agreement |
| External translation | No provider selected | Not applicable | `disabled` | Provider selection ADR, privacy and residency review |
| External digital signing | No provider selected | Not applicable | `disabled` | Trust provider, certificate custody and legal review |
| External font service | No provider selected | Not applicable | `disabled` | Font use/embedding/redistribution grant |
| WebHWP demo/tool page | Public evaluation surface | Not production entitlement | `evaluation_only` | Never use as production backend evidence |

## Policy

- An available API guide or demo is not a license grant.
- No account creation, purchase inquiry, personal-data submission, trial activation, or provider connection has been performed.
- A provider is enabled only in a target-specific signed registry after contract and security review.
- Missing provider evidence yields `disabled` or `unverified`, never fallback PASS.

P00-07 is closed with every production provider intentionally disabled. This is approval of the fail-closed disabled decision, not approval or acquisition of any provider license. A later provider selection reopens P00-07 for contract and security review.
