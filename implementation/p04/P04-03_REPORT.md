# P04-03 Selector engine report

- Generated: 2026-09-02
- Audited source commit: `afdcf1abe8c2bc1b20c99cb5cb9fc5d643516444`
- Primary implementation commit: `d27da546ae6d6422414a1d638ceea17818bb1abb`
- State: `pass_current_pc_local_pure_model`
- Reasoning/review mode: `high / stale identity, ambiguity and bounded text resolution`

`domain-ir`에 immutable `DocumentGraph`와 typed `RevisionId`를 입력으로 하는 fail-closed
selector snapshot/index를 구현했다. stable logical ID, named slot/field/bookmark, typed
section/note/table-cell path plus node fingerprint, exact NFC text plus neighboring context hash를
지원한다. backend ID, XML 위치, HAction, cursor/session, 한글 runtime은 이 task에 포함하지 않았다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Immutable snapshot identity | `pass` | revision ID + canonical graph SHA-256 mismatch is rejected before lookup |
| Stable logical ID | `pass` | section and note body nodes resolve through one global validated node index |
| Named selectors | `pass` | exact NFC `slot_name`, `field_name`, `bookmark_name`; collision stays ambiguous |
| Structural selector | `pass` | typed root/steps/node kind plus final canonical node fingerprint |
| Text-context selector | `pass` | no bare offset; exact NFC query plus at least one hashed neighboring anchor |
| Exact-one cardinality | `pass` | zero=`not_found`, multiple=`ambiguous`, stale and limit failures remain distinct |
| No first fallback | `pass` | deterministic BTree/traversal order is never promoted to a target choice |
| Finite bounds | `pass` | path/name/query/context/candidate/node/text bounds and streaming occurrence scan |
| Privacy | `pass` | Debug/errors redact ID, revision, query, name, context, range and fingerprint values |
| Version/migration | `pass` | `P04-03_SELECTOR_POLICY.md`, `selector-v0-to-v1.md` |

## Validation evidence

- Windows Rust 1.96.0: selector `9/9`; combined `domain-ir` `27/27`, doc tests and Clippy
  `-D warnings` passed.
- Linux Rust 1.96.0: derived image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`,
  network off, source/registry read-only, Cargo offline, executable temp mounts; selector `9/9`,
  combined `27/27` and Clippy passed at the audited source commit.
- Test matrix includes zero/multiple/stale, wrong revision/digest, ID and note-body lookup, named
  collision, conflicting field metadata, structural index/kind/fingerprint drift, offset-preserving
  text movement, context drift, candidate limits, NFC equivalence, deterministic serialization and
  Debug redaction.
- Current checkout FULL bootstrap: `5/5` lanes passed.
- Exact audited commit clean clone FULL bootstrap: `5/5` lanes passed; post-run Git changes 0.
- Security: current 528 files and exact-implementation clean clone 527 files scanned;
  secrets/vulnerabilities/forbidden licenses 0; current SBOM 271 and clean-clone SBOM 229
  components.
- P04-01 golden digest remains unchanged through its cross-platform regression test.

The first Linux invocation attempted an online rustup channel check and stopped before compilation
because the lane has no network. The authoritative reruns set the already-installed exact
`RUSTUP_TOOLCHAIN`; source/registry remained read-only and all tests/Clippy then passed.

## Strict self-review and remediations

- Change risk: `high` because every later operation and transaction will trust the selected target.
- Text occurrence discovery initially collected every match position in a temporary vector. It was
  changed to streaming traversal so a large paragraph with a short query cannot amplify memory
  before the candidate limit is applied.
- Named candidates initially materialized before their count check. The index set is now bounded
  before result allocation.
- A bare query could otherwise recreate offset-style behavior; construction and resolution both
  require at least one context anchor.
- Field-local and reference names can create semantic drift; disagreement now fails snapshot build
  and has a dedicated negative assertion.
- Section and note roots are distinct typed structural roots, preventing sentinel-index aliasing.
- Final blocker/major/minor findings after remediation: `0/0/0`.

## Scope and remaining boundary

P04-03 proves pure deterministic selection against synthetic validated graphs. It does not compile
the public OperationPlan schema, mutate a document, perform regex/page-position selection, route a
capability, execute Hancom or prove selectors lifted from a real HWPX save. No user document was
opened or modified. Deferred Hancom releases and other PCs remain outside the current-PC scope.

## Next exact task

Start `P04-04 OperationPlan compiler` with reasoning effort `xhigh`. Compile a versioned bounded
draft through exact selector typing, explicit unit/default normalization, ambiguity admission and a
deterministic dependency DAG. Duplicate/missing dependencies, cycles, unresolved defaults/units and
stale selector expectations must fail without producing a partial compiled plan. P04 final Gate
remains `max`. No user local operation is required for P04-04.
