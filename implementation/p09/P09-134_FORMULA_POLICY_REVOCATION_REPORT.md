# P09-134 — 수식 정책 철회 제품 경로와 SQL21 연결

## 결과와 범위

수식 정책의 읽기·등록·서명 소비 경로에 없던 **명시적 철회 호출 경로**를 추가했다.
기존 SQL21 migration/function/RLS/schema admission은 변경하지 않았다. 운영 DB 접속,
SQL 실행, issuer/key/trust 설정, 한글/COM/UI/접근허용은 실행하지 않았다.
실제 SQL/production issuer/native/P09 Gate는 여전히 `NOT_RUN`/unverified/OPEN이다.

최종 source에 대한 실행 결과는 revision-service 전체 library 단위 검사22개,
product-cli 전체 library 단위 검사7개, 새 저장소 제품 철회 통합 검사6개다.
전체 workspace의 기본 feature 엄격 lint는32 packages/358 targets를 확인한다.
전체 저장소 제품234개 runtime을 이번 단계에서 통과했다고 주장하지 않는다.

## 실제 구현

- `StoredFormulaPolicy::revoke`: 쓰기 scope → 원래 current policy/source/ACL/AEAD/target 재검증 →
  private exact-version record → 서버 철회 호출1회. 성공 응답은 전체 version/binding과 대조한다.
- `PostgresFormulaPolicyRevoker`: 기존 current policy reader를 그대로 사용하고, 정확한
  tenant/project/branch/document/source/version/generation을 기존 SQL21 connector에 연결한다.
  현재 editor와 과거 policy creator를 혼동하지 않는다.
- `LocalPostgresSourceFormulaPolicyRepository::revoke_policy`: fixed tenant/subject의 기존
  scoped transaction 안에서 `revoke_source_formula_policy_v1`을 호출한다. 기존 SQL의 editor role,
  branch lock/latest-version CAS/immutable revocation을 사용한다. commit acknowledgement 이후에만 반환한다.
- nil version, generation0/overflow, 잘못된 document ID를 거부한다. commit acknowledgement 유실은
  `CommitOutcomeUnknown` → `OutcomeUnknown`이며 자동 재시도·증거 삭제가 없다.
- 저수준 관리 요청은 source head를 요구하지 않는다. source가 이동한 뒤에도 latest 정책을
  관리자가 철회할 수 있다. 제품 convenience 경로는 fresh source preflight를 요구하며,
  이 preflight를 atomic source lease로 주장하지 않는다.

PostgreSQL 스킬의 최소 권한 원칙을 적용해 direct table write/새 권한/default trust를 추가하지 않고,
기존 admitted named function·tenant/subject transaction 경계를 재사용했다.
현재 RLS/editor 권한·CAS/rollback의 실제 SQL 효과는 오프라인 검사로 대체하지 않는다.

## 검증 조건

새 통합 검사6개는 실제 importer/artifact AEAD/formula product 코드와 명시적 in-memory server를 사용한다.

1. 철회 후 이미 준비된 수식 결과의 callback 및 새 policy binding 거부.
2. 읽기 전용 호출은 철회 write0회.
3. source head 변경/quarantine/AEAD tamper는 write 전에 거부.
4. current policy digest 변경은 write 전에 거부.
5. repository denial, ambiguous acknowledgement, 전체15종 reply binding 불일치에서 자동 재시도 없음.
6. 별도 현재 writer가 과거 다른 creator의 정책을 철회하며 creator/author defaults를 재작성하지 않음.

원본 HWPX 전체 bytes, revision head, 기존 정책 Evidence를 보존하며 철회가 ingest/delete를 만들지 않는다.
최종6개만 선택한 실행은 `6 passed / 228 filtered`이고 전체234개 PASS가 아니다.
revision22/product7은 각각 전체 library inventory와 실행 결과가 일치하며 filtered/ignored/failed0이다.

## 실패·중단·재검증 보존

- 초기 revision build3회는 exit101, 미채택이다. 세 번째에서 Cargo가 중복 `--test`를 지적한 것을
  확인했고, `--profile test --lib`에 자동 적용되는 test flag에 추가 flag를 넣은 runner를 수정했다.
  앞2회는 당시 상세 진단 수집이 없었으므로 새 진단을 과거 로그로 소급하지 않는다.
- 엄격 lint 첫3회는 각각 needless_pass_by_value1, doc_markdown1/semicolon3, manual_string_new1이다.
  참조 전달·문서 표기·세미콜론·빈 String 생성만 수정했다. assertions/error conditions는 그대로다.
- 전체234개 실행은259.57초에서 시스템 CPU100/100/96% 연속 관측으로 owned test만 중단됐다.
 49개의 개별 통과 출력은 있지만 terminal 전체 summary가 없으므로 전체 완료로 채택하지 않는다.
- lint 네 번째도 시스템 CPU 연속 과부하로 중단돼 미채택이다. 다섯 번째 전체 엄격 lint가 통과했다.
- 새 단기 검사/빌드2회는 baseline CPU88/91% 때문에 시작하지 않았다. deferred 원장은 그대로다.
- 수정 전 complete source와 runner 단계별 whole preimage 및 기존/최종 EXE를 별도로 보존했다.
  최종 EXE는 `-p134-final.exe`, 이전 EXE는 `-p134-current.exe`로 분리한다.

## 자원 제한과 증거 경계

CPU affinity1/BelowNormal/cargo jobs1/test worker1, sample2초,
시스템 CPU85% 이상3회 연속/가용 RAM4096MiB 미만/root working set2048MiB 초과/시간 한도에서
이번 runner가 소유한 process tree만 중단한다. 다른 앱/작업의 process를 종료하지 않았다.
Windows native metrics와 CIM의 읽기 전용 대조도 보존했고 PC 전체 압박의 원인은 `NOT_DETERMINED`다.
root working set은 compiler children의 합계나 실제 peak RAM이 아니다.

매 실행781개 declared Rust/protocol/xtask/Cargo/driver/fixture/whole parent-preimage를 전후 고정했다.
이 숫자는 작업 수나 모든 compiler dependency의 전수 개수가 아니다. 기존 SQL migration21개는
별도 지문 그룹으로 결속한다. P133 및 이전 증거는 수정한 parent3개에 대한 exact whole preimage와
새 source4개만 제외한 역사적 inventory에서 원래 검증기로 재확인한다. 과거 검사 결과를 새 실행으로 바꾸지 않는다.

## 실행 명령과 원장

- `python tools/p09/verify_formula_policy_revocation.py`
- `python tools/p09/tests/test_formula_policy_revocation.py`: 증거 guard13개.
- `git diff --check`.
- 현재 원장: `implementation/p09/evidence/p09-134-formula-policy-revocation.source-progress.v1.json`.
- 자원/실패/현재 runtime: `target/p09-121-resource-optimized/p134-*.json`.

## 미완료와 다음 경계

전체 current 저장소234개 회귀는 자원 압박으로 미완료다. 다음에는 자원 상태를 확인하며
exact final EXE의234개 inventory를 짧은 개별 실행으로 재개하고, 같은 이름/EXE/source 결속으로
전체 union을 입증해야 한다. 시작하지 않은 사례를 PASS로 보충하지 않는다.

production issuer/key custody/approval·trust registry/실제 SQL21/원자적 실행·publication·transport,
whole import/native metadata/coordinates/comment/rich compiler/field-Date-external 의미,
P84 SQL 원인과 실제 한글 저장·재열기·렌더링이 남는다.
최소6 coarse groups/closed0 유지. 최소30 완료 조건은 전수 확정 잔여 개수가 아니다.
native34는 별도 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED이며 P10은 착수하지 않았다.
P09/A12/A13 OPEN, product_complete=false, goal_status=active. PLANS.md 삭제 상태 유지.
