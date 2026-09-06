# P16-06 registered plan-review host v14

Date: 2026-09-06
Scope: current-PC local MCP host and disposable PostgreSQL, Hangul 2020 target profile
Decision: **PASS for the dedicated local registered host; actual Codex app installation and Hangul execution remain open**

## Delivered result

- A dedicated one-tool HTTPS MCP host registers `render_plan_review_widget` and the immutable
  `ui://hwpx-agent/plan-review/v1.html` resource outside the P15 18-tool catalog.
- The server starts only after three least-privilege PostgreSQL clients pass migration, role, RLS,
  policy and privilege admission.
- Every render reauthenticates `project.read`, reloads the active verified source, decrypts and
  revalidates the exact compiled plan, decrypts the receipt-bound review evidence, and returns only
  the strict public widget snapshot.
- The child protocol is bounded and correlated. Secrets stay in an allow-listed process environment,
  diagnostics are capped, bearer data is zeroized in Rust after parsing, and public failures collapse
  without backend details.

## Actual evidence

Clean implementation commit `6856d5cacad6cfbceff8671b3adac85b74fe0d97` produced qualifying
run `d22e85581cd44d06a016f3460a43de12` with 14/14 checks:

- exact P15 catalog digest preserved;
- all 13 migrations and three separate least-privilege roles admitted;
- product-derived source identity plus encrypted plan and review evidence seeded;
- strict Inspector discovery of exactly one tool and one exact resource;
- authoritative render PASS and foreign-project rejection;
- missing/invalid authentication, wrong path/method, hostile Host/Origin and oversized body rejected;
- database plus host restart restored the identical snapshot digest;
- ciphertext tamper failed through the registered endpoint;
- graceful host shutdown and exact labeled container/volume cleanup.

The widget resource SHA-256 is `c72ba812b6b253162c9fefb50a5f1f953962585bd7426d0faccc7248d361c32b`.
The first and restarted public snapshot SHA-256 are both
`19e193a8040d4879db6b8d2a11b95e5aa43afa49ebc7bec4d9f85e684ec79d07`.

Workspace Rust tests and Clippy, Node formatting/typecheck/build/tests, the targeted Python guards,
and the P01 security lane pass. The security lane covered secret scanning, Cargo deny/audit, pnpm
audit/licenses, NuGet vulnerability checks and a CycloneDX SBOM.

Closure commit `06494a9a3932cf40c87b1749f46210a890fa5c95` was then checked out detached at
`D:\개발\hwpx-agent-audit-p16-host-06494a9`. With no ignored run receipt and no pre-existing
dependencies, frozen offline pnpm restore, formatting, typecheck, build, 135 Node tests, 10 targeted
Python tests, exact qualification verification, Rust workspace all-target/all-feature tests and
Clippy with `-D warnings` all passed. The detached tracked tree remained clean.

## Explicit non-claims

- No Hangul process, COM call, user document, access prompt or UI automation was used.
- This proves registration inside the dedicated local MCP server, not installation into an actual
  Codex/ChatGPT account and not a public deployment.
- The renderer does not execute or authorize a document mutation. Actual Hangul 2020 dry-run/write,
  product registration, P16 phase completion, later Hangul versions and other PCs remain open.
- Immutable predecessor contracts are preserved. Their source-lock failures after successor changes
  are not relabeled as predecessor PASS.
