# P09-126 — 자원 제한을 유지한 실제 scoped 회귀 228개 대조

## 완료 범위

P125의48개 뒤 cases49~200 추가152개를 실행하여 actual_import200개 전부 개별 terminal PASS로
확인했다. 각 receipt는1PASS/0failed/0ignored/227filtered/exit0 및 정확한 test name을 갖는다.
현재 single-case 회귀의 남은 사례0은 P09 전체 잔여 작업0 또는 제품 완료를 의미하지 않는다.
동일 executable10688512 bytes/SHA04fefdf7…/Rust14 source freeze를 재사용했다.
원본/production Rust/Cargo/기존 검증기/사용자 변경/P00~P08/실패 증거를 수정하지 않았다.

P123의 독립 full_document20 및 최상위 root8 receipt도 같은 binary/source 기준으로 다시 확인한다.
새 audit는 실제 --list의228개와 terminal200+20+8개 이름의 합집합이 정확히 같고
중복/누락/foreign name이 없는지 검사한다. 목록만으로 runtime 성공을 주장하지 않는다.
이는 독립 실행으로 수용한 source cases228개다. single-process actual_import200 및
single-process full228 실행의 terminal PASS는 없으며 기존 interrupted201/50 markers를 승격하지 않는다.

## 실제 corpus 결과

case49 원래36개: P120 frozen 결과와 모든 rows/counts의 정확한 일치를 확인했다.
수식 원본16/no-formula20/targets16/bindings128/원본 Changed0/NoChange16을 유지한다.
case50: 허용된 leaf 밖의 추가 숫자 입력 변경16개 반례 거부 marker가 확인됐다.
case51: 원본 숫자 입력을 변경한16개 및 current16개 결과가 기존 실제 targeted 결과와 정확히 같다.
signed Changed/current NoChange/철회와 rebinding 거부를 확인했으며 실제202.52초 PASS다.
case52: 유효한 서명을 가진 Changed/current 파생32개가 보호된 셀에서 거부됨을 확인했다.
생성한 numeric derivative는 원본 HWPX 파일의 변경이 아니며 원본 파일은 그대로 유지한다.
component AEAD/Ed25519 성공은 실제 운영 issuer/key custody/registry 신뢰 또는 SQL 증거가 아니다.
서로 공유하는 scalar evaluation을 독립 native/math oracle로 승격하지 않는다.

## 자원 및 실행

CPU affinity1/BelowNormal/worker1/2초 감시/CPU85%3연속/여유 RAM4GiB/test RAM2GiB를 유지했다.
각 case 상한600초, batch 최대25개/새 시작 budget120초로 실행했다. 중단 자동 retry 없음.
session38322은49~51,50309는52~68,91347는69~200을 완료했다. 모두terminal이며 재시작하지 않았다.
200개 wrapper elapsed 합751.97초는 전체 wall time이나 동일-workload 성능 benchmark가 아니다.
전체 receipt samples452, 관측 test RAM 최대24.67MiB/여유 RAM 최소14043MiB였다.
빠른 case의 양수 test RAM 관측이 없으면 unknown/null로 두며 baseline0을 실제 사용량0으로 보지 않는다.
실행 종료 후 test process0/Hwp0을 확인했다. 다른 앱을 종료하거나 설정을 바꾸지 않았다.

## 검증과 다음 경계

새 coverage-set unit8 PASS:228 분리 집합, 누락/중복/foreign case/wrong root/inventory drift 거부,
순서 무관성을 검사한다. 생성한 목록 unit은 실제 실행 증거와 별도로 취급한다.
기존 resume14/batch10 unit 및 P124/P125 보존 pin 검증도 유지한다.
새 physical audit는 P12510794 bytes/SHA46321fdc…를 고정하고 이전 source/pins 전부를 대조한다.
새 source3/이전1128/현재1131/inherited raw pins2436 및 신규 runtime152개를 checkpoint에 기록한다.

목표 active/P09 Gate OPEN/product false/P10 새 구현 없음/PLANS 재생성 없음.
한글/Hwp/COM/UI/접근허용/실제 SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동 없음.
single-process 통합, 원래 comment mutation/lowering와 qualified 의미, 미완료 fields/notes/references,
source re-admission/실제 한글 저장·재열기·렌더링/신뢰 발급자/원자적 publication/P09 Gate는 남는다.
다음 안전한 제품 구현은 기존 CommentBuilder/source-bound catalog/assembly 경로를 조사하고,
실제 원본 근거로 가능한 댓글 변경을 연결하는 단계다. unavailable 의미를 추측 기본값으로 채우지 않는다.
