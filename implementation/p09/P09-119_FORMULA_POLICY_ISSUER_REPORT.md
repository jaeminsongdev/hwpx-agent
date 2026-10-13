# P09-119 — 실제 수식 정책에 대한 필수 서명 승인 소비 경로

## 구현 범위

P116 strict formula DATA/whole source-target/protection, P117 SQL21과 P118 실제 원본 결합 생성·등록은
변경하지 않았다. 새 서버 전용 typed 승인 입력은 P118의 private validated registration record만
받아 exact binding/policy artifact/digest 및 issuer/key/trust generation/time를 결합한다.
Ed25519 signing bytes는 전용 domain 뒤의 NUL + 정확한 signed_claims UTF-8 bytes다.
envelope 생성은 승인이 아니며, 소비 시 live server-selected key로 실제 ring Ed25519를 검증한다.

새 product wrapper는 원래 `prepare_formula_with_policy`의 math/output/source/protection을 호출하기
전에 mandatory signature repository를 연결한다. signature/approval/issuer/key/clock은 public
request 입력이 아니며, typed 서버 dependencies는 현재 정책/최신 승인/현재 trust/서버 clock 모두를
명시적으로 요구한다. 현재 keys/metadata를 매번 읽고 signature 후 selector들을 다시 읽는다.
old key/proof fallback 또는 default approval은 없다.

ArtifactService의 실제 Evidence descriptor/ACL/AEAD/whole bytes/media/size/검사·격리 상태를 검증한다.
envelope/claims/source binding의 unknown/duplicate/escaped duplicate/positional typed array/trailing
JSON/type coercion을 거부한다. 모든 binding, audience/operation/schema/generation/time를 대조한다.
issuer trust의 전체 keys/issuer/scope/generation/window/lifetime snapshot을 결합하여 counter가 같아도
변경을 놓치지 않는다. 원래 소스/보호/모든 대상 거부는 유효한 서명으로 우회할 수 없다.

prepared 결과의 verify와 byte callback도 supplied CURRENT provider/dependencies로 fresh 검증한다.
외부 product route/native/atomic 자격을 승인하지 않으며 원래 route 거부를 유지한다.
공개 receipt는 digests/generation/component qualification만 포함하고 raw claims/서명/key/actor/
document/idempotency key를 출력하지 않는다. 기존 unsigned API는 trusted 경로로 승격하지 않는다.

## 검증 및 실패 보존

생산 library check edd7b7/session4217 →fe0494/exit0 PASS. 생산 library strict lint
599263/session99316 →0e7b7a/exit0 PASS. initial selected test compile ecc6d0/session5182
→67feb5/exit1은 새 테스트 ArtifactId/Option 타입 불일치 E0308이었다. whole 실패 소스를
cbbcbe에서 보존하고 새 테스트 비교만 수정했다. 원래 guards/fixtures는 변경하지 않았다.

첫 targeted runtime1ad476/session91842 →05b047/exit0은12 PASS/0failed/0ignored/208filtered,
348.09초다. 실제 Ed25519/암호화 artifact/source/compiler가 실행됐지만 production trust 증거는 아니다.
expanded strict lint618bb6/exit1은 새 테스트 semicolon5건이었다. a42888에서 whole test 및
이 targeted PASS executable을 별도로 보존하고 스타일만 수정했다. 승인-only AEAD,
정책 세대 교체/old approval replay/five foreign scope 및 typed positional claims/binding을 보강했다.
추가 strict lint1497ec/exit1은 새 malformed test112/100 line 제한이었다. whole source8bbbf5를
보존하고 입력 생성 helper로 분리했다. suppression 또는 original guard 수정 없이118b2a/exit0 PASS.

생산/module parents/test 전체9개 bytes/SHA를d4554a에서 고정했다. 코드 변경 없이 관련 전체
scoped regression ec0306/session6783을 시작했다. 실행 중8dfafa/exit0에서9개 freeze exact 확인.
관측 JSON 예산이 작아 한 번 truncated parse가 실패했으나(25af72 직후), 소스를 바꾸거나
회귀를 재시작하지 않고 full-budget 재관측으로 exact를 확인했다. 검증 성공으로 실패를 바꾸지 않는다.

첫 scoped 회귀 ec0306/session6783 →1d10b0/exit1은 artifact25/CLI6/product10 PASS 다음
stored221 PASS/1 FAIL/0ignored/0filtered(494.14초)로 종료했다. form/revision suite는 이 실행에서
실행되지 않았다. 새 approval-only AEAD 테스트가 실제 ObjectKey의 `.aes256gcm` suffix를 빼고
digest만 비교하여 변조가 발생하지 않은 것이 원인이다. afac17에서 whole failed test와 당시6개
test executable을 모두 별도로 보존했다(미실행 executable도 실행 PASS로 세지 않는다).
테스트만 실제 `ObjectKey::for_artifact`의 exact key 대조로 고치고 positive tamper hit counter를
추가했다. 원본 및 policy 정상 읽기의 hit0, 승인 변조/consumer 미호출/hit>0를 함께 검사한다.
생산 signature/AEAD/원래 정책 guard는 변경하지 않았다. strict lint17d8fd/exit0 PASS;
정확한 단독 수정 검사2d6e93/session20796 →729dbe/exit0은1 PASS/221filtered/21.86초다.

최종 runtime/evidence 결과는 동일 이름 source-regression/source-progress/final-audit 원장과 함께
아래 final verification에서 기록한다. 테스트 목록37d159는 실행 증거가 아니며 새14개는 stored suite에
포함하므로 전체 합계에 두 번 더하지 않는다. whole workspace/hwpx-package136/actual SQL/native
qualification을 재실행했다고 주장하지 않는다.

current-source conformance8b2707/exit0은15 upstream PASS/green0이며 원래 historical default
matrix_drift를 유지한다. conformance는 actual product/native/SQL/Gate 증거가 아니다.

## 보존과 미완료 경계

전체 parent preimages4개로 정확한 역변환을 확인한다. Cargo.lock의 기존 다른 ring dependencies를
건드리지 않고 CLI dependency 하나만 추가했으며 version/network update/install은 하지 않았다.
원래 P118 checker/receipt/모든 ancestry/원본 native/실패 증거는 변경하지 않는다.

실제 production issuer/config/key custody/승인 registry/trust root 서명·등록 및 실제 SQL21
migration/RLS/membership/ACL/CAS/철회/동시성/rollback은 NOT_RUN/unverified다.
synthetic test issuer/root/keys/metadata repository만 사용했고 실제 운영 키를 읽거나 설정하지 않았다.
실제 Ed25519 및 AEAD 성공은 해당 component 증거이며 배포 issuer 신뢰 증거가 아니다.
새14개 signed 경로 검사는 생성한 bounded HWPX와 synthetic server로 수행한다.
회귀에 포함된 기존36 원본/16 수식 원본 등록 검사는 P118의 DATA 등록 범위다. 이를 원래16개
모두에 대한 새 signed 제품 경로 승인으로 확대하지 않는다. 다음 비접근허용 제품 검증은
이 frozen 실제 원본들에서 새 signed consumer의 전체 후보/원본 보호/실제 bytes 대조를 수행한다.

lease/원자적 실행/idempotency/publication/CLI·HTTP transport, whole import/metadata/coordinates/
comment/rich compiler/field-Date-external-document 의미와 P84 SQL 원인이 남는다.
최소6 coarse groups/closed0 유지, 최소30 세분 완료 조건을 부분 구현만으로 차감하지 않는다.
P09/A12/A13 OPEN, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED, no P10/product false/full goal active.
한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동 없음.
P00~P08/user-owned dirty/private/original/failed evidence 및 PLANS 삭제 상태를 보존한다.

## Final verification

수정 뒤 생산/module/test whole9개 bytes/SHA를d564d3에서 다시 고정했다. 최종 회귀
d79fe9/session21708 →4c2f9d/exit0은 artifact25 + CLI6 + product10 + stored222 + form18 +
revision20 =301 PASS/failed0/ignored0/filtered0다. 새 issuer14개는 stored222에 포함한다.
stored531.01초/product13.59초/form13.14초이며 performance acceptance는 아니다.
실행 중 d96a9c/exit0에서 final source freeze9 exact 확인. final binary 목록15739f/exit0은
301 distinct binary+fully-qualified test pairs를 확인했지만 목록 자체는 실행 증거가 아니다.
CLI binary build8bab5e/exit0은 컴파일 증거이며 CLI 실행/transport qualification이 아니다.

수정 후 unmodified P118 checker를 original parent preimage view로 실행한 f9f0d5/exit0 PASS:
1071 previous source 중1067 unchanged, whole parent preimages4/inverse exact,
inherited raw2232 및 old executable482 보존. 이번 실패 아카이브4개와 부모4개를 각각 보존하며,
최종6개와 CLI2개/초기 targeted PASS1개/초기 full regression6개 실행 파일을 별도 결합한다.
새 current byte validator/negative evidence unit의 실제 결과와 checkpoint 최종 pin은 final-audit에
기록한다. 원래 tests/validators/policy payload/SQL21은 수정하지 않았고 P09 Gate는 OPEN이다.
