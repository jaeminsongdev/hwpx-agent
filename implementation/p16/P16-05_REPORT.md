# P16-05 Project/revision UI report

- Generated: 2026-09-05
- Audited implementation commit: `118928befaff328c2b5e6c156e11f42d4c1b3a82`
- Reasoning effort: `high`; checkpoint/conflict/evidence-boundary and closure review: `max`
- Decision: `pass_scoped_local_mcp_apps_bridge_component_e2e_actual_host_pending`

P16-05 adds a separate project-continuity resource for project open, bounded revision history,
confirmation-gated checkpoint creation and conflict recovery. It proves the current-PC local React
component and a real MCP Apps `App`/`AppBridge` PostMessage lifecycle inside a local Chrome iframe.
It does not claim actual ChatGPT or Codex host rendering, registered-plugin behavior, Developer
mode, hosted MCP execution, Hangul/COM execution, file transfer, another PC or production readiness.

## Implemented boundary

- Immutable resource `ui://hwpx-agent/project-continuity/v1.html` is exposed only by
  `render_project_continuity_widget`; P16-04 and all eighteen P15 public tools remain unchanged.
- Refresh calls exact `project_open` followed by exact `project_history`, using distinct request IDs.
  Either failure rejects the whole refresh instead of publishing partial state.
- Only `outcome === "succeeded"` is accepted. Project, head and revision identifiers are strict opaque
  values, history is bounded and raw summaries are classified to a local enum before disposal.
- Checkpoint creation requires two separate user actions: enter confirmation, then commit the exact
  current head with a UUID idempotency key and fixed label. A conflict disables the write and leaves
  only Refresh.
- The widget has no network API, browser storage, cookies, arbitrary URL/path input or private
  HAction/COM surface. CSP domains are empty and the server remains responsible for authentication
  and authorization on every tool call.
- Seven inspected Chrome captures cover desktop/narrow, ready/confirm/conflict and dark saved states.

## Exact identity

- Contract: `implementation/p16/p16-continuity-contract-v1.json`
- Resource: `web/plugin-widget/dist/continuity-widget-v1.html`, 655,998 bytes, SHA-256
  `cb79603ec437d83535185e881e488ae481e40e51d7c8181e98e64cc2318249ce`
- E2E harness: 432,754 bytes, SHA-256
  `ffa482e1557f6b6ae6d1e090bd6ef232a7090e1a4ca24a7cf3a1fe6caccb9c07`
- Preview: 209,160 bytes, SHA-256
  `cef1458dd74af2bc56814351b0e184697fbb4acd8f918b321b46094de2d78622`
- Source locks: 34; local E2E exact call order:
  `project_open`, `project_history`, `project_checkpoint`.
- Visual source and capture digests are fixed in `implementation/p16/P16-05_VISUAL_QA.md` and the
  continuity contract.

## Validation

| Check | Result |
|---|---|
| P16-05 target | pass; TypeScript/React 41/41, Python 13/13, 34 source locks, deterministic bundle |
| Local browser MCP Apps bridge E2E | pass; real `App`/`AppBridge` PostMessage iframe, calls 3/3 in exact order |
| P16 cumulative | pass, 77/77 |
| Current exact-commit full CI | pass, 5/5: Linux 9.824s, Windows 57.882s, Widget 4.462s, Docs 1,037.541s, Security 15.468s |
| Independent exact-commit full CI | pass, 5/5: Linux 11.130s, Windows 55.052s, Widget 4.762s, Docs 1,420.930s, Security 13.783s |
| Independent P14/P15 regression | pass, P14 132/132 and P15 84/84 |
| Offline Linux P16 | pass; pinned image, network disabled, source/root read-only, capabilities dropped, 77/77 |
| Independent checkout tracked changes / residual checkout | pass, 0 / removed |

The current exact-commit security run `5c8e52df817740bda09ea6c9705eb063` is retained in the
Git-ignored evidence tree. Its 1,295-byte report SHA-256 is
`868d17ac3b71abad67e83ac001b8a7038915f8790e387d4d9341085c7dd47fe6`; its 1,055,074-byte,
1,015-component SBOM SHA-256 is
`0fb6f0d159312981d68d074c613a6ab854664f16776f36c0bdcd7391d6a1dc89`. All checks passed and
`failed_checks` is zero.

The independent security run `31a18cde524b4304a8675f083e27f4b8` was copied byte-for-byte to
`artifacts/p16/evidence/independent-security-runs/` before checkout removal. Its 1,294-byte report
SHA-256 is `8d5799d7385fd7ab45695c1270810ec3f97b5acbf8620b6036d7bf3ada3ad0d8`; its 869,782-byte,
782-component SBOM SHA-256 is
`9c4f25a8ab7cd22c0de49446f75de03399d0756c1ded9f680437ba77be1065a0`. All checks passed and
`failed_checks` is zero. Component-count differences reflect checkout-local ignored build state.

Offline Linux used local pinned image
`python@sha256:355bfa66770995d7e9a0da4b3473b44d0cb451f6b56f5615ad9c39e3c4eca03f` with networking
disabled, a read-only root/source, all capabilities dropped, `no-new-privileges` and bounded
resources. Browser E2E ran independently on the current PC because the offline container has no
browser.

## Failure, repair and independent-audit record

- The first full-CI run correctly failed formatting in ten new files. The failure was not promoted;
  repository Prettier was applied, the contract was regenerated and all target/regression checks
  were rerun.
- Adding a new ignored P16 evidence directory initially changed the historical P15 `.gitignore`
  digest chain. That change was fully reverted. Generated receipts were preserved under the already
  ignored `artifacts/p16/evidence/` tree; no P15 criterion or historical byte was relaxed.
- The first combined independent-CI session lost its execution handle while the docs lane was still
  running. No residual process or security report existed, so no partial result was promoted. The
  missing docs/security lanes and the exact fast lanes were rerun individually and all five passed.
- Only four exact digest-pinned, Git-ignored P10 current-PC diagnostic JSON records were hydrated in
  the independent checkout. No HWPX, PDF, user document, credential or design source was moved.
- No Hangul process, COM call, UI input, external account, public endpoint or system setting was
  opened or changed by this card.

P16-05's local component scope is complete, but its roadmap checkbox remains open because the named
`Web↔Codex E2E` requires an actual registered host. Continue P16-06 at reasoning effort `high`; use
`max` for high-risk confirmation, malicious or contradictory tool results, capability-route
authorization and any write action. P16-02 registration remains independently pending.
