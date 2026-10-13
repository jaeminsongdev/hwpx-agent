# P09-190 — current r07 개별 완료 재사용 검증기

## 현재 결과와 범위

사용자 요청에 따라 249개 전체의 반복 재시작을 다음 실행 전략으로 사용하지 않는다.
현재 실제 실행 가능한 runner는 아직 연결 전이다. 이번 산출물은 재사용 검증기,
exact-one 출력 검증, 전체 목록을 빠짐없이 분류하는 실행 계획이다.
계약 검사가 통과했다고 제품 runtime 완료로 표현하지 않는다.

- compiled249: 기존 P186 별도 closing standing 유지. 이번 전체 source/EXE 재감사 없음.
- 신규 개별 runtime 완료: 0. 실제 exact-one 실행: NOT_RUN.
- 전체 테스트 큐: 249 = 일반 243 + corpus 묶음 6. P09 전체 작업 개수와 다르다.
- full249/signed16/product: false. P09/A12/A13 OPEN, 목표 active, P10 새 구현 없음.

## P189 최신 실행 상태

P189 preparation은109 contracts 및1461개 입력의 전후 검사를 통과했다.
actual은771.0초에 running 상태에서 STOP_SUSTAINED_SYSTEM_CPU로 중단됐다.
public completed/ok48이 있지만 exit0/전체 terminal summary/final source closing이 없다.
완료된 이름 목록이 저장되지 않았으므로48개를 이름/순서 추정으로 skip하지 않는다.
현재 active는 원본36개를 내부에서 순회하는 all36 signed original 테스트였다.
cleanup=true, owned_tree_empty=true, Job final active0이며 자동 재시작하지 않았다.

## 구현한 재사용 조건

`tools/p09/resumable_current_r07.py`는 다음을 요구한다.

1. 정확히249개 유일한 공개 이름, authoritative compiled inventory/EXE와 입력 manifest identity.
2. `[name, --exact, --test-threads=1, --format=pretty, --color=never]`.
3. 실제 running1, 정확한 이름1개의 ok, terminal1PASS/0failed/0ignored/0measured/248filtered.
4. 원래1200초/CPU/RAM/sampling policy, 정상exit0, actual Job membership/limits/GO/정리.
5. complete streams/원래32768bytes cap, capture error 없음. 원문 로그 저장 없음.
6. 별도 batch closing의 전체 before/after 입력 일치 및 fresh 외부 case receipt pin.
7. 중단/미확인/부분 결과/duplicate/다른 코드·EXE·이름/최종 입력 누락은 완료로 skip하지 않음.

개별 성공 후보가 있어도 batch closing이 없으면 대기 상태다. 후보를 자동으로 재실행하지 않고
별도 closing을 통해 수용 가능한지 확인한다. actual reader가 계산한 외부 receipt pin을 받는
구조이므로 문서 자신의 hash를 자체 포함시키는 순환 참조를 요구하지 않는다.

whole preservation audit는 batch 시작/끝에서 수행할 구조이며 매 case마다 역사적EXE 전체를
재감사하는 scheduling 비용을 줄이려는 것이다. 현재 읽기 생략, stat-only freshness,
hash cache, 기존 보호 기준 완화는 구현하지 않았다. 실제 runner와 closing producer 연결이
필요하며 현재의 pure 계약 fixture만으로 자원 감소량이나 실행시간 개선을 주장하지 않는다.

## 무거운6개 처리 경계

corpus namespace의 원래6개 모두 pending으로 남겨 일반243과 구분했다.
36/16/32개 원본·파생 입력을 내부 순회하는 테스트는 실행 프로세스를 하나로 줄이는 것만으로
부담이 해결되지 않을 수 있다. 원본별 분할 시 기존 assert, 유일한 원본 식별,
no-formula denial, signed changed/noop, live revocation, 보호 거부 및 원래 최종 집계를
빠짐없이 유지해야 한다. 원본을 줄이거나 샘플을 전체 결과로 대체하지 않는다.
Rust/product source/원본 fixture/current EXE는 이번에 수정하지 않았다.

## 수행한 검증

`python -B tools/p09/resumable_current_r07.py --mode light`

- synthetic22 contracts PASS; child/Popen/run/new thread는 계약 검사에서 차단.
- read-only plan: accepted0/remaining249/general243/corpus6.
- 최초 일반 case는 actual_aead_tamper_cannot_be_reclassified_as_an_importer_or_policy_failure.
- bound8/final fresh8/read17/6646285bytes(binary0), stop=null, watcher cleanup=true.
- 이전48 카운트 미승격, whole current runtime source/EXE audit 미실행.

주 증거: implementation/p09/evidence/p09-190-r07-resumable-contracts-and-plan-run01.v1.json.
원 P189 preparation/actual 실패 영수증은 그대로 보존했다.

## 다음 작업

실제 exact-one owned runner와 batch 전후 closing을 연결하고, 작은 일반 case부터 정상 종료
영수증을 누적한다. 그 후6개 corpus 묶음을 원본별로 분할한다. 통과 결과를 재사용하되
개별 runtime 누적 완료, single-process 통합 검증, SQL/native/product/Gate를 구분한다.
한글/접근허용/SQL/Git/Review/다운로드/설치/삭제·이동/전역 설정 변경 없이 진행했다.
