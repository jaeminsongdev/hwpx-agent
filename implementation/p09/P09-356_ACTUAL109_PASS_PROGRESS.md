# P09-356 독립 STOP 검토·실제109 PASS

2026-10-10. 목표 ACTIVE. 직전 P355는 현행862 자격과 실제 경로 증거를 얻은 진전이다.
이번 단계는 미실행 제품 사례109를 실제 수용하여 큐를103/249로 진전시켰다.
P09/A12/A13 Gate는 OPEN이며 P10은 시작하지 않았다.

## 전제와 범위

사용자는 외출 중이므로 PC 조작·UAC·한글 접근 허용을 요구하지 않는다.
P355 STOP 뒤 코드 재검토 결과를 유지하고, 새로운 독립 STOP 검토와 신선한 준비 증거를
얻은 뒤 원 자원 보호 아래 한 사례만 실행한다. 같은 명령을 자동 재시도하지 않는다.
현재 code2는 qualified862와 동일하다. 기존 코드/제품 성공107·108/실패059는 보존한다.

## 순서와 실제 결과

1. CPU1.22%, RAMfree20.413148%에서 원 admission 뒤 stop-review060을 시작했다.
   exact056 승인을 유지하며 exact059/root+sidecar+빈 placeholder를 대상으로 검토했다.
   결과는 `PASS_PRESERVED106_PRE_PRODUCT_STOP_REVIEW_NOT_GO`, 계약/Native/제품0,
   원059를 PASS로 재분류하지 않음, 감시 정리 true다. PTY29581 exit0로 종료했다.
2. CPU7.09%, RAMfree20.334069%에서 새 프로세스의 원 admission 뒤 fresh061→actual062를
   순차 실행했다. helper import만 공유하고 각 owner/reader/모든 fresh/감시/정리는 독립이다.
   fresh 실패 시 actual을 실행하지 않는 구조이며 자동 retry loop는 없다.
3. fresh061은 `PASS_PRESERVED106_DISTINCT_FRESH_NOT_NATIVE_OR_PRODUCT`, 계약 재실행0,
   exact light057의862를 재사용, 원056·060 승인을 모두 검토, 감시 정리 true다.
4. actual062는 실제109 한 사례를 실행했다. body `PASS_SCOPED_NOT_GATE`, tests_passed1,
   exit0, 실제 product child true, parent elapsed282.03초, owned_tree_empty/cleanup true다.
   root `PASS_EXACT_PRESERVED106_NEXT_RUNTIME_NOT_WHOLE_OR_GATE`로 수용됐다.
   PTY73860 exit0로 종료했고 그 세션을 관찰 timeout 때문에 다시 시작하지 않았다.

선택된 실제 테스트는 `actual_import::policy_product::all_five_source_cases_registered_policy_uses_original_whole_product_candidate_no_publication`이다.
해당 Rust 함수의 다섯 source 사례 순차 검사도 읽기 전용으로 확인했다. 함수 안의 병렬 실행/
자동 재시도 loop는 없었다. 원본과 정책결합 결과를 독립 비교하는 부분은 변경하지 않았다.
이 CLI 회귀 사례의 PASS를 한글 UI·시각·사용자 수용 또는 전체 P09 Gate PASS로 확대하지 않는다.

## 실제 source 경계와 정리

frame은 `COMMITTED`, registered false다. 입력1658/121216238bytes 전체를 before와 after에서
각각1658회/121216238bytes 읽고 exact byte hash/원 stream identity를 확인했다.

두 실제 경계 각각 fresh held metadata1658, 원 predicate4974, pathname probe0,
reader root 복구 true, adapter inactive다. actual adapter selected/restored true다.
원 Native handle1966(regular1658+ancestor308)/duplicate3316 모두 닫혔다.
잔여 handle/duplicate/reader/stream/close failure0, frame/감시/Job 정리 true다.
Job final active_processes0, owned_processes[]다.

원 전체 읽기·신선한 hash·Native identity·두 경계·Job·CPU/RAM·pacing·deadline은 유지했다.
이번 단계 코드를 변경하거나 계약862/성공 제품107·108을 재실행하지 않았다.

## 자원 관측

| 단계 | preparation fresh / reads / bytes | host max | parent own max | private max | RAMfree min |
|---|---|---:|---:|---:|---:|
| review060 | 230 / 463 / 50702545 | 17.31% | 1.912046% | 79867904bytes | 19.843485% |
| fresh061 | 231 / 465 / 50832245 | 18.98% | 1.761252% | 80261120bytes | 19.818976% |
| actual062 parent observer | 232 / 469 / 50961817 | 38.02% | 1.639344% | 114073600bytes | 18.476545% |

actual body의 별도 sampler host 최고는38.39%, owned Job peak private27.2MiB였다.
부모 observer private 최고는108.79MiB이다. 서로 다른 표본 창의 CPU 최고값을 더하거나
같은 순간의 전체 사용량이라고 해석하지 않는다.
Job CPU hard cap readback6.25%, affinity mask1, BelowNormal(16384), breakaway disabled,
kill-on-close와 membership이 확인됐다. 이번 실행에는 resource STOP이 없다.
이 한 번의 낮은 부하와 성공은 PC 프리즈 해소·Defender 인과를 증명하지 않는다.

## 정확한 evidence pins

- review060:64850bytes/`911f8c79d63540ab61f28c79c95e69647a03b4517070c94aa8990fe811d308e8`
- fresh061:64786bytes/`0f4e7b894f927ee9e41169e5420cd1d64b40f690630891309014d706f2184bc9`
- actual062 root:703412bytes/`5b1f3220d0448673b61aff5ee0db885cf03b7c9261e6e51f06464901da74d0d9`
- actual062 body:198015bytes/`a148d641ea1649c062110331ca35dbdd67d8ce28d1258c9a26d63348a2ae5b71`

원059 FAILED/root/sidecar/0byte placeholder는 삭제·수정·수용 승격하지 않았다.
현재 runtime152778bytes/`9fcf1446bf38e14b67c05f10f25b693e6656a9864227d7d71a21ae9bc27b8473`,
test123113bytes/`c01811db277830995f6fb911cd7f181800f17170cfdf0a8037938d1583c54819`다.
정확한 code2/qualified862 archive는 `evidence/p340-formal862-code/`에 보존된다.

## 수용 상태와 다음 경계

수용103/249, 잔여146(일반140+corpus6), next110이다.
성공 body 마감 pending0, whole재조정100이다. full249/signed16/whole1470 current qualification은
모두 false, product_complete false, P09/A12/A13 OPEN, 문서 final-fresh NOT_RUN이다.
이는 특정 큐의 상태이며 P09 전체 잔여율이 아니다.

다음110은 새 cursor103에 맞는 light/fresh 검토가 필요하다. 코드가 같아도 cursor102의
GO를 새 cursor103의 GO로 자동 승격하지 않는다. 성공 제품109도 재실행하지 않는다.
P09 Gate가 실제 닫히기 전에는 P10 새 구현으로 넘어가지 않는다.

UAC/한글 허용/특권Defender 추적/Git/빌드/Defender·OS·WSL 설정 변경/외부 process 종료/
삭제·이동0. 목표 ACTIVE, 검증 세션들은 terminal 상태다.
