# P09-350 — 관리자 승인 없이 검증 코드의 중복 조회·자료 복사 제거

날짜: 2026-10-10. 상태: **IMPLEMENTED_NOT_RUNTIME_QUALIFIED**.

사용자는 외출 중이므로 PC/UAC를 조작할 수 없다고 명확히 알렸고,
Defender 관리자 추적 대신 검증 코드를 다시 검토·수정하도록 요청했다.
UAC/한글 접근 허용을 다시 요청하지 않았으며 Defender/OS/WSL 설정도 변경하지 않았다.

## 원인 판단의 정정

source035 소유 프로세스의 낮은 CPU는 직접적인 CPU 풀로드가 관측되지 않았다는
근거일 뿐이다. 준비 단계의 파일 열기/읽기가 Defender 등의 후속 작업을 유발하지
않았다는 증거가 아니다. 검증 코드에 문제가 없다고 확정할 수 없다.

source035는 준비209 입력의418 읽기/43,485,170바이트를 완료한 뒤 Native 획득에서
중단됐다. 따라서 Native 중단 지점뿐 아니라 그 앞의 준비 읽기와 테스트 자료 생성도
재검토했다. Defender 추적은 코드 최적화의 선행 조건으로 삼지 않았다.

## 구현한 변경

1. current runtime V18의 direct regular 파일은 요청마다 새로운 `lstat` 한 번으로
   file/symlink/junction의 세 predicate를 판정한다. 기존 일반 파일의 `is_file`+`lstat`
   두 pathname 조회가 한 번으로 줄어든다. 새 Native 잠금, 제품 수용, 원자적 경로
   안전성은 주장하지 않는다. reparse/디렉터리 속성/불완전한 stat/조회 오류는 원
   `is_file`과 별도 fresh link 조회/fallback으로 돌아간다. 요청 간 metadata 재사용은 없다.
2. `StopTests`의 독립 full copy 안에 이미 있는 frame을 사용한다. 각8검사에서
   전체 fixture 한 번과 전체 frame 한 번의 추가 복사를 없앴다. 검사별 독립성은 유지한다.
3. fixture 초기화에서는 사용하지 않을 full copy를 만들지 않는다. frame만 필요한
   closing template은 해당 subtree만 새 deep-copy한다. accepted template은 곧 폐기할
   full frame을 복사하기 전에 제외하고 나머지 문서는 원래처럼 독립 deep-copy한다.
4. 새 순수14검사 추가: single-lstat10/fixture allocation4. 기존 검사 삭제 없이
   COUNT379/current+following758로 맞췄다. 조회 계수 oracle도 새 정책을 검증하며
   역사적 V1 실패 증거의 기존 계수 검증은 유지한다.

수정 파일은 기존 current runtime/test 고정2경로다. 원93 frozen 코드, full1658,
308 ancestor, 두 실제 full-byte 경계, Native identity/borrowed stream, JSON parsing,
final-fresh hash, Job/CPU/RAM/600초/720읽기/cleanup을 제거하거나 완화하지 않았다.

## 확인한 내용과 미확인 내용

- 두 파일 AST parse/compile PASS. 실제 `test_` 정의379와 선언 COUNT379 일치.
- 이전730 자격 코드 archive와 AST 비교: runtime에서 변경된 정의는
  `MetadataPathSource`, `MetadataPathQueries`, `metadata_path_contract`뿐이다.
  Native/Frame/Job/resource/closing runner 정의 변경 없음. SCHEMA/COUNT는 별도 갱신.
- 작은 순수 검사41개 및 구조 수정 후45개 실행 시도는 모두 admission에서
  `DEFERRED_ALREADY_SATURATED_SYSTEM`. 두 번 모두 시스템 CPU100%, 실제 실행 검사0.
  소유자 종료 확인. child/Native/product 시작0. 기존 보호를 우회하지 않았다.
- 두 admission 표본의 RAM 여유 최솟값23.2515%/23.7053%, 관측 own private
  30,605,312/29,835,264바이트. 이 표본은 검증 소유자의 관측 범위이며 import 전체의
  최대 부하나 시스템 프리즈 원인을 증명하지 않는다.
- 동작 검사45개, 정식758계약, 전체 Native/source, 실제 부하 감소 및 프리즈 해소는
  **아직 미검증**이다. 구문 PASS를 제품/전체 source PASS로 승격하지 않는다.
- 이전 review031의730 자격은 V17 code2 전용이며 수정된 V18 자격으로 재사용하지 않는다.

실제 syscall 감소량·RAM/CPU 개선율은 아직 측정하지 않았다. 일반 파일의 조회2→1과
사용하지 않을 copy 제거는 코드상의 예상 감소이며 Defender CPU 개선 보증이 아니다.

## 원본 보존과 다음 경계

`evidence/p340-formal730-code/`의 원132620/93235바이트 코드2 SHA는 각각
341e5a327adeb1e6111c600a19b9b39a71afa85a6e8956b823292c957e57839e /
6b3e68e2e8f32977499b47131a6fd216ad17416224b181c108aa4fa0e8ae6783로 현재 재확인했다.
review031/source035의 exact hash도 변경되지 않았다. 상세 current pin/정적 확인/
admission 결과는 `evidence/p09-350-unprivileged-code-optimization.v1.json`에 있다.

다음 실행 순서는 정상 admission에서 작은45계약 → 정식758계약 → 새 정확한 코드 자격에
바인딩한 독립 source 검증이다. 시스템 포화 상태에서 같은 전체 검증을 반복하지 않는다.
성공 제품107/108은 재실행하지 않는다. 실패 원본/미완료 source/P09 OPEN 상태를 유지한다.

등록 목표는 현재 tool 조회상 paused다. 이번 요청의 코드 최적화는 수행했지만 목표
상태를 임의 active/blocked/complete로 바꾸지 않았다. 관리자 승인 없는 원인 확정이나
검증 완료를 주장하지 않는다. Git/빌드/외부 프로세스 종료/삭제·이동은 하지 않았다.
