# P15-02 public MCP tool schema report

- Generated: 2026-09-04
- Audited implementation source commit: `c3839df89a9eaf5e8a4f0b1bae7e4f6edd724ff1`
- Reasoning effort: `max`
- Decision: `pass_scoped_current_pc_hancom_2020_contract_only`

P15-02 freezes the public MCP surface before handler wiring. Exactly 18 user-intent-level tools have
self-contained JSON Schema Draft 2020-12 input and structured-output contracts, least-scope OAuth2
declarations, compatibility metadata and conservative safety annotations. The catalog is a contract;
it is not yet a running MCP server.

## Implemented contract

- The ordered public surface is `capability_check`, `document_plan`, `document_create`,
  `document_inspect`, `document_edit`, `document_transform`, `template_analyze`,
  `document_validate`, `document_render`, `document_export`, `project_create`, `project_open`,
  `project_history`, `project_checkpoint`, `project_publish`, `job_get`, `job_cancel` and
  `artifact_get`.
- Every descriptor has an action-oriented name/title, bounded usage description, closed input and
  output schemas, top-level `securitySchemes`, an exact `_meta.securitySchemes` mirror and truthful
  annotations.
- Objects reject unknown fields; arrays, strings and numbers are bounded; identifiers are typed.
  Public inputs and structured results cannot carry raw HWPX XML, COM/HAction names, arbitrary local
  paths, credentials, bearer tokens, signed URLs, document bytes or large widget payloads.
- The only accepted target profile is the current-PC identifier
  `hancom-hangul-2020-secondary`. Hancom 2022/2024 cannot be selected by these contracts.
- Stateful calls require UUID idempotency keys. Revision mutations carry an expected revision;
  `project_create` requires a null initial revision and the exact current target profile.
- Only five tools are annotated read-only: `capability_check`, `document_plan`, `project_open`,
  `project_history` and `job_get`. Inspection, validation, rendering and artifact delivery are
  conservatively non-read-only because they may create durable service state.
- Only `job_cancel` is destructive. All tools are idempotent and closed-world. Export and publish are
  local artifact/label operations and cannot email, print, publicly upload or mutate an external
  service.
- Descriptor scopes are an exact subset of the eight P15-01 scopes. Authentication annotations do
  not replace handler authorization, tenant/resource ownership, policy or confirmation checks.
- The deterministic builder creates the catalog, per-schema hash snapshot and source-lock contract.
  Drift, schema weakening, auth/annotation changes, unknown tools and invalid representative values
  fail closed in validation.

These choices follow the official [OpenAI MCP server guide](https://developers.openai.com/plugins/build/mcp-server),
[plugin reference](https://developers.openai.com/plugins/reference) and
[tool-definition guidance](https://developers.openai.com/plugins/plan/tools), retrieved 2026-09-04.

## Source identity

| Source | Bytes | SHA-256 |
|---|---:|---|
| `implementation/p15/P15-02_TOOL_SCHEMA_POLICY.md` | 6,248 | `abbb5fbfbd854de7799da9a0b6d1cf9ffc81247fbe5e2a129ff281a5600f9791` |
| `implementation/p15/p15-public-tool-schema-contract-v1.json` | 2,439 | `9e7099535bceced5295ce347afb4b9cc9a6dfa71db1f10d633ed9247d126681e` |
| `implementation/p15/p15-public-tool-schema-snapshot-v1.json` | 10,885 | `9859773f6634067b37384a19cc76548f63331232ab24407785fe3a3dd87c54cb` |
| `protocol/mcp/p15-public-tools-v1.json` | 134,758 | `94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001` |
| `tools/p15/build_public_tool_schemas.py` | 38,703 | `f56108e361657f53ed71127fad5556d38aafd386f4dd004b8848e210960b4168` |
| `tools/p15/validate_public_tool_schemas.py` | 17,964 | `55ba3005fd9ee9412f3b3c53168cff3575dc1a63e16caa8f2d95f6426ba1ec4e` |
| `tools/p15/tests/test_public_tool_schemas.py` | 6,729 | `3cc74aa62b2ecfc0d4cf9838fe174558b6e31bc4297dce800acfa519c9eeb043` |

The generated contract also digest-locks the P15-01 auth contract and P15 CI wiring. The catalog
snapshot records canonical hashes for the complete catalog, every descriptor and all 36 input/output
schemas.

## Validation

| Check | Result |
|---|---|
| Deterministic builder drift check | pass, 18 tools |
| JSON Schema meta-validation and fixtures | pass, 18 descriptors, 18 input and 18 output schemas, errors 0 |
| P15-02 schema/negative tests | pass, 17/17 |
| All P15 Python tests | pass, 30/30 |
| Current exact-commit CI | pass, 5/5 lanes |
| Exact-commit independent checkout bootstrap | pass, 5/5 lanes; tracked changes 0 |
| Current security lane | pass, every check exit 0; secrets/vulnerabilities/forbidden licenses 0; SBOM 681 |
| Independent-checkout security lane | pass, every check exit 0; secrets/vulnerabilities/forbidden licenses 0; SBOM 448 |
| Offline Linux schema validation | pass, builder/18 schemas/30 tests; network disabled and source read-only |
| Residual P15 containers / `Hwp.exe` | pass, 0 / 0 |

The current exact-commit security run is `893a1ce1af054844b547ec155ed01bc3`. Its Git-ignored report is
1,294 bytes with SHA-256 `abb7b4bc81a7ab79908d2701b07f43c1877b088030b6095766816679debb5395`;
the 661,686-byte SBOM SHA-256 is
`6cd440e28ecc788edf64b71dbd36b5776685772e65093441b1be852e2666c1bc`.

The independent checkout produced run `831ad80539bf41fc84da6ffe0c559c1c`; its report and SBOM were
copied without modification to the same Git-ignored run path in the main checkout. The report is
1,294 bytes with SHA-256 `090468e06d73bd5a86706d2c0442b13d1a04bfdad5c86bc606d498fd9db8c113`;
the 476,394-byte SBOM SHA-256 is
`36aa812d73e7a91338177ed2442986925a5544090b8f95056e8498151b647e92`.

Offline validation used local image
`hwpx-agent-python-schema:3.13.13-jsonschema-4.25.1-p15@sha256:aed62ff28fa362cdabecea5a4eae8907de82eda2332b83b1eba7d7bc32140fe3`.
It ran with `--network none`, a read-only root and source mount, all capabilities dropped,
`no-new-privileges` and only a bounded temporary filesystem. The independent checkout received only
the four exact digest-matched, Git-ignored current-PC JSON baseline records; no HWPX, PDF or user
document was copied. The temporary worktree was verified and removed after evidence preservation.

`ruff` and `black` were unavailable on this host and are not repository gates. Python compilation,
the repository validator, negative tests, Windows CI and the separate Linux runtime provide the
recorded Python evidence.

## Strict review and diagnostics

- Change risk: `high`; public handlers and clients will depend on these contracts.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Review corrected a scope-mutation test that initially compared expected rather than declared
  scopes, added required artifact-write permissions, narrowed the profile to exact Hancom 2020 and
  made initial project creation require both that profile and a null revision.
- An independent-checkout setup command was stopped before validation because a manually transcribed
  historical smoke-run ID was wrong. The authoritative target profile supplied the correct ID, all
  four JSON hashes were verified and the subsequent clean validation passed. The stopped setup is
  not represented as product evidence.
- No user document, original design ZIP, Hangul process, COM automation, system setting, production
  identity provider or external service was opened or changed.

This card does not qualify handlers, transport, hosted OAuth, authorization-code/PKCE, an OpenAI
connection, MCP Inspector, long-running job UX, attachment delivery, production deployment or any
Hancom 2022/2024 behavior. Those claims remain unverified.

P15-02 may be checked. P15 remains in progress. Continue with P15-03 handler orchestration at
reasoning effort `max`: authenticate, validate input, enforce policy and tenant ownership, dispatch
one service/job effect, then validate and return a bounded structured result.
