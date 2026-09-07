# P06-03 Table Merge/Split Completion Report

- Generated: 2026-09-07
- Final implementation base commit: `0bd152dd85fa42632f8f7213e96e445af44524be`
- Source qualification and audited FULL commit: `5cfa20e54566652f0d3cd17d26996bc45379ea33`
- Audit mode: `STRICT`; reasoning recommendation: `high`
- Overall state: `pass_scoped_current_pc_local_pure_ir`
- Next task: `P06-04 Cell formatting`

P06-03은 P06-01의 검증된 `TableGrid`와 P06-02의 identity 원칙 위에, 완전한 직사각형
병합과 기존 master cell의 균등 분할을 구현했다. 셀 내용은 호출자가 명시한 preservation
policy로만 이동하며, 손실 허용 정책의 폐기 내용도 receipt에 기록한다. 이 작업은 순수 논리
모델이다. HWPX 표 XML lift/lower, Flow bytes, 셀 스타일, 실제 한글 2020 save/reopen/readback/
render 또는 다른 PC/버전은 증명하지 않는다.

## Completion criteria

| Criterion | State | Evidence | Remaining boundary |
|---|---|---|---|
| Rectangular merge | `pass` | 선택 slot을 정렬·중복 제거한 뒤 완전한 직사각형이며 교차 master를 전부 포함하는지 확인 | HWPX physical merge는 주장하지 않음 |
| Merge identity | `pass` | canonical top-left master ID만 생존하고 나머지는 row-major 순서로 retirement receipt에 기록 | backend cell ID 대응은 미검증 |
| Deterministic split | `pass` | 기존 master span을 정확히 나누는 row/column subdivision만 허용하고 grid 크기는 유지 | 한글 split action과의 동치는 미검증 |
| Split identity | `pass` | top-left는 기존 ID를 유지하고 나머지 ID는 호출자가 정확한 row-major 개수로 제공 | 임의 backend ID 생성은 금지 |
| Content preservation | `pass` | `concatenate`, `first`, `distribute`, `reject_if_multiple` 정책과 transfer/discard receipt가 deterministic | rich text/style/formula semantics는 후속 task |
| Atomic bounded failure | `pass` | 원본 grid/content는 immutable이며 전 범위·ID·크기·digest 재검증 후에만 결과 반환 | durable transaction/HWPX publication은 미통합 |
| Property and negative tests | `pass` | rectangular/conflict/partial-span/cardinality/limit/digest/redaction/determinism 회귀 12/12 | arbitrary document corpus는 미검증 |

## Merge, split and content contract

- Contract version: `hwpx-agent.table-merge-split/v1`; private record:
  `protocol/private/p06-table-merge-split-v1.json`.
- `TableContentState`는 grid digest와 정확히 결합하며 master마다 정확히 한 entry를 요구한다.
  content block ID는 전체 table에서 유일하고 bounded이며, private sorted index로 lookup을
  `O(log n)`에 제한한다.
- `TableGrid::merge_cells`는 두 개 이상의 master를 포함하는 완전한 직사각형만 허용한다.
  선택 영역이 기존 span을 부분 교차하거나 hole/nonrectangular selection이면 typed error로
  원자적으로 실패한다.
- `TableGrid::split_cell`은 양의 subdivision과 product 2 이상을 요구하며, 기존 row/column
  span을 각각 나머지 없이 나눌 수 있어야 한다. 새 cell ID의 개수·순서·유일성은 정확하다.
- `concatenate`는 canonical cell/intra-cell 순서를 보존하고, `distribute`는 stable contiguous
  balanced chunk를 사용한다. merge의 단일 출력에서는 `distribute`가 lossless concatenate로
  귀결된다. `reject_if_multiple`은 nonempty source가 둘 이상이면 실패한다.
- `first`만 의도적인 손실을 허용하며 top-left 이후의 모든 block을 `discarded` receipt에
  명시한다. 다른 정책은 content block ID를 손실하거나 중복할 수 없다.
- Receipt는 before/after grid digest, policy, region, surviving/retired/created ID, transfer와
  discard를 bounded canonical JSON으로 결합한다. 공개 accessor는 read-only이고 `Debug`는
  논리 ID와 content를 노출하지 않는다.

## Source qualification

- Source successor v23 `p17.current-workspace-source.v23.20260907`은 immutable v22 contract
  SHA-256 `2d52898b8d232ea819f4f875a3760ba676dc7d67899f78687987014cead3e176`을 인증하고
  source view를 implementation commit `0bd152dd85fa42632f8f7213e96e445af44524be`로 전진시킨다.
- Clean source acceptance run `d39fd169945141d5ae2f968cb0b10b08`은 11/11을 통과했고 기존
  25-member Cargo successor projection을 유지했다. Receipt SHA-256은
  `e6ba2648c19874056a22646db9fde8948d89864227d260546ecd40768fb043bf`다.
- v23 contract는 P06-03 구현·테스트·정책·migration·private contract·validator의 정확한 8개
  파일을 결합하며 SHA-256은
  `62ed365ab62c367f4c25483a53333c185d34bfcbca09aa60d695da5780184aff`다.
- Qualification verifier와 negative suite는 4/4를 통과했다. ignored source receipt는 hash를
  확인한 정확한 bytes만 독립 감사 공간에 복사했다.

## Validation evidence

- Windows와 offline Linux에서 `domain-ir` all-targets 95/95가 통과했다. 그중 merge/split은
  12/12이며 기존 grid/operations 회귀도 모두 포함된다. Clippy `-D warnings`도 통과했다.
- P06 grid/operations/merge-split Python suite는 17/17, 세 contract validator는 모두 PASS,
  v23 qualification negative suite는 4/4다.
- Offline Linux는 Rust 1.96.0 image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`를 사용했다.
  network disabled, source와 Cargo package registry read-only, capabilities dropped,
  no-new-privileges, 4 GiB/2 CPU/256 PID 및 executable disposable tmpfs 조건에서 통과했다.
- Exact audited commit `5cfa20e54566652f0d3cd17d26996bc45379ea33`의 현재 작업공간 FULL은
  linux-core 35.731 s, windows-worker 61.079 s, widget 6.244 s, docs 846.016 s,
  security 21.123 s로 5/5를 통과했다. P14 135/135, P15 85/85, widget 144/144다.
- Current security run `67c9ad9dc71745ce827418d6b51444d2`는 failed checks와 forbidden
  licenses 0, 모든 vulnerability check exit 0을 기록했다. Report SHA-256은
  `5115141178c5ce87931abacd68ecc680d29301695f1b30b2181f74d2c1cf4053`, SBOM SHA-256은
  `b866655c20ca1a12453e0c2e24e0d0afc4532204a61ffeb5dcd5015999e37968`다.
- 동일 커밋의 disposable independent worktree FULL도 linux-core 70.306 s,
  windows-worker 62.745 s, widget 7.652 s, docs 918.024 s, security 12.687 s로 5/5를
  통과했다. P14 135/135, P15 85/85, widget 144/144다.
- Independent security run `03f269bd9a9c4fed81afe549d6bfa16d`도 zero findings이며 report
  SHA-256은 `5fc19133ccefaf4c882442547b678c26f1bc04749465d72acdb72c1cefb1cd25`, SBOM
  SHA-256은 `694e56f37da2598fb3629180db5fd3601d8d9dfc42080d71223fd709eed798d4`다.
  독립 공간에서 v23 4/4, P06 17/17과 세 validator를 다시 통과한 뒤 tracked-clean 상태를
  확인하고 정확한 disposable worktree만 제거했다.
- Final report/ledger working tree의 docs lane도 829.644 s에 PASS했다. Design validation은
  1,566 files/errors 0, P14 135/135, P15 85/85, local-link errors 0을 기록했다.

## Strict review and remediation

- Change risk: `high`; 이후 style, sizing, formula와 HWPX lowering이 이 identity/content
  transfer 경계를 소비한다.
- Verdict: `approve_scoped_current_pc_local_pure_ir`.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- 초기 자체검토에서 content lookup이 linear scan인 DoS 가능성을 발견해 bounded sorted
  private index와 binary lookup으로 교정했다.
- Clippy가 보고한 장문 함수와 excessive-argument API는 suppress하지 않고 request type과
  checked helper로 분해했다.
- 새 Rust/Python source에 `unsafe`, `unwrap`, `expect`, `panic!`, `TODO`, `FIXME` site는 0이고
  `git diff --check`가 통과했다.
- Source grid/content는 borrow-only이며 어떠한 validation failure도 partial result를 공개하지
  않는다. Canonical serialization과 repeated receipt bytes는 deterministic하다.

## Preserved failures and scope boundary

- 첫 offline Linux 시도는 read-only Cargo package cache가 mount되지 않아 offline resolution
  중 `base64` package를 찾지 못하고 compile 전에 실패했다. 이는 PASS가 아니다. 두 번째 시도는
  동일 network/source 경계를 유지한 채 host Cargo `registry`와 `git`을 read-only로 mount하고
  writable bounded Cargo home/target tmpfs를 분리해 95/95와 Clippy를 통과했다.
- 독립 v23 테스트 파일을 직접 실행한 첫 명령은 repository root가 Python module path에
  들어가지 않아 `ModuleNotFoundError: tools`로 실패했다. 제품 검증 PASS로 세지 않았고,
  정식 `python -m unittest` 실행이 4/4를 통과했다.
- Current SBOM은 기존 local install inventory 1,057 components, fresh independent frozen install은
  822 components를 기록했다. 두 환경 모두 content 검사와 vulnerability/license Gate를 통과했지만
  이는 local dependency inventory 차이이며 byte-identical SBOM을 주장하지 않는다.
- 사용자 문서와 원본 설계 ZIP은 열거나 수정·이동·삭제하지 않았다. P06-03은 한글을 실행하거나
  접근 허용 창을 띄우지 않았고 HWPX 표를 생성하지 않았다.
- 한글 2022/2024와 다른 PC, production, server/VM, 배포는 계속 deferred/unqualified다.

## Task decision and next exact task

P06-03은 scoped pure-IR merge/split와 content/identity transfer semantics에 한해 완료다. P06
phase는 계속 진행 중이며 P06-04~09의 완료를 의미하지 않는다.

다음 exact task는 `P06-04 Cell formatting`이며 권장 추론 수준은 `max`다. Bounded margin,
border/fill, horizontal/vertical alignment, text direction과 protection model을 정의하고,
validated style lowerer와 exact current-PC Hangul 2020 readback/render fixture를 구현·검증한다.
먼저 순수 모델·fixture·검증 harness를 준비한 후 실제 runtime 단계 직전에만 한글 2020을
실행하고 사용자에게 접근 허용을 요청한다.
