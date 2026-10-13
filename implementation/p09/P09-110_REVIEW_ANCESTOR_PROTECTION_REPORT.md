# P09-110 — 댓글 밖 MAIN 표·셀의 보호 우회 수정

## 실제 변경 결과

기존 댓글/MEMO/hiddenComment 출력에서 보호 검사가 review body 경계에 멈추던 문제를
수정했다. 실제 선택의 부모 chain이 MAIN 표·셀까지 이어져도 그 상위 보호를 검사한다.
전체 본문 공통 출력에도 같은 검사를 추가했다. 원본 source·선택 검증 뒤,
NoChange/값 검사/patch/writer 전에 Selection으로 거부하며 부분 출력은 반환하지 않는다.

원래 검사와 target ancestry/ID/style/opaque/finite budget/whole package readback 검사는
바꾸지 않았다. `tc protect`, `tbl lock`, 표의 직접 자식 `sz protect`만 기존 규칙으로
읽는다. 관측되지 않은 의미를 채우거나 작성자·시간·상태·실행 권한을 만들지 않는다.
guard 재귀는 종료점 root인 추가 1회로 제한된다. 공개 API/직렬화/DB schema 변경은 없다.

## 회귀 검증

새 target `target/p09-110-review-ancestor-protection`에서 현재 변경된 core package를
다시 빌드했다. 이전 P106 package 실행 파일은 현재 코드 검증에 재사용하지 않았다.

| 범위 | 최종 실행 결과 |
| --- | --- |
| hwpx-package 관련 17 suite | 190 통과, 실패/ignored 0 |
| comment_operation | 16 통과 |
| form_stored_provider | 167 통과 |
| stored_comment_provider | 24 통과 |
| 합계 | 397 실행 통과, 중복 23회 제외 374개 고유 함수 |
| 신규 회귀 | 8개, 기존 셀 suite 6개와 함께 14 통과 |
| 신규 evidence 검사 | Python 8 통과 |
| package 17 suite strict lint | `-D warnings` 통과 |
| 신규 Rust 파일 단독 fmt / 전체 diff check | 통과 |
| 원래 current-source component 검사 | 15개 검증, green0 |

전체 본문/개별 문단/기존 셀/표 삽입 위치에 대해 MAIN의 3개 보호 flag와 두 종류 review를
검증했다. 여러 단계의 MAIN 표 중 바깥 보호도 검출한다. unknown observed 값은 편집
허용으로 해석하지 않는다. 기존 importer의 더 강한 native boolean/필수 속성 거부도
정확한 오류 종류·code로 별도 확인한다. false/누락 spelling을 강제로 허용하지 않는다.

허용 입력은 actual source anchor에 해당하는 content/paragraph를 바꾼 예상 byte와
실제 출력의 모든 expanded package part를 비교했다. 다른 모든 part와 선택 영역 밖의
원문, 표 구조, 형제 셀, 원본 관측값을 보존하고 다시 import했다. no-op/empty target/
writer 작은 예산보다 보호가 우선하며, whole source 변경은 Source로 먼저 거부한다.
표 삽입 위치 테스트는 보호 검사 우선순위를 검증한다. 유효한 2x2 native template의
성공 경로는 원래 suite를 그대로 재실행하며, 신규 1x2 MAIN fixture를 유효 template으로
승격하지 않는다.

## 수정 전 실패와 강한 검사 보존

최초 신규 test compile에서 private semantic/read method, 미구현 PartialEq 사용 4개 오류;
두 번째 compile에서 private XML byte access 오류가 있었다. 기존 공개 접근 제한은
풀지 않고, test에서 verified source ZIP/raw span 및 기존 fixture를 사용하도록 고쳤다.
두 실패 source는 전체 byte로 별도 보존했다.

수정 전 원래 production code로 새 suite 실행은 6 통과/8 실패였다. 보호 우회 7개
회귀와 기존 native boolean 검사에 걸린 positive fixture 1개를 구분한다. 그 source와
실행 파일을 보존했다. guard 추가 직후 11 통과/3 실패는 기존 표 validator의 강한
boolean 거부였고, 별도 실패 실행 파일을 보존했다. 신규 fixture 검증만 정확한 기존
거부를 반영했으며 production boolean 검사나 원래 assertions를 바꾸지 않았다.
최종 focused 14/전체 397에 실패·반복 focused 실행을 더하지 않는다.

원래 default conformance는 여전히 `matrix_drift`/exit1이다. 별도 current-source-v2
15 component 검사 통과를 그 실패 해소나 native/product/Gate PASS로 대체하지 않는다.

## 원본 보존과 현재 원장

부모 source 3개 전체 사전 원본과 정확한 추가 guard/module 역변환을 검증했다.
이전 962 source 중 959개 unchanged + 3개 whole preimage, 이전 raw pin 1763개,
이전 실행 파일 283개를 보존했다. 원래 이전 audit을 whole preimage view에서 재검증했다.
현재 source 971개/delta12/추가 archive6/predecessor2/current executable23이다.
현재 executable23 = 최종 test20 + 미실행 CLI1 + 실패 diagnostic2이며 모두 PASS가 아니다.
전체 과거 qualification 또는 저장된 모든 실행 파일을 재실행한 주장은 하지 않는다.
각 source/receipt/executable byte·SHA256와 명령·session·terminal chunk/test inventory는
`evidence/p09-110-review-ancestor-protection.*.v1.json`에 분리 기록한다.

## 남은 전체 목표

이 수정은 trusted protection 작업군의 부분 진척이다. 최소 6개 큰 잔여 묶음은 유지한다:
원본 metadata/coordinates, full comment/rich Flow/compiler/source mapping, 실제 durable
integration, field/Date/external/document 의미, trusted issuer/전체 보호/atomic 실행·publication,
actual P84 SQL 원인·회귀. 신규 guard 검증은 full native protection acceptance가 아니다.
Native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED, P26 failed_semantic_non_green,
P62/P84_SQL UNRESOLVED, P09/A12/A13 OPEN/green0/product false/no P10을 유지한다.
전체 P09~P20 목표는 active다. 한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/
stage·commit·push/삭제·이동 없이 진행했다. HEAD와 사용자 dirty/private/원본·실패 증거,
PLANS.md 삭제 상태를 보존했다.
