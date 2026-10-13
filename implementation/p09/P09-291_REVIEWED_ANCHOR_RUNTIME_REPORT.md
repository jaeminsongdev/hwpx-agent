# P291~P293: 부분 anchor 재개 검증과101 최종source STOP 후보

2026-10-09. 목표 ACTIVE. runtime 수용94/249, 잔여155(일반149+corpus6), 다음index101, whole 재조정대기91. **독립 source 마감 후보1건(101), 아직 미수용**. 원100 수용 plan은 변경하지 않았다. P09·A12·A13 OPEN. 지원 계약/문서/후보 검토는 runtime/full249/whole1470/historical67/signed16/제품/P09 Gate PASS가 아니다. PC 프리즈 해결은 미확정이다.

## 이번 구현과 범위

P285 원 실행 코드·test와 원 FAILED/PASS 증거를 덮어쓰지 않고 P291 재개기와 test2개를 추가했다. P285 부분anchor164reads STOP을 엄격한 admission-only 무작업 예외로 처리하지 않고, 원 실패를 그대로 검토하면서 이전97~100의 원 record/Native/Job/byte/queue를 유지한다. 본체를 재실행하지 않고 저장된 결과를 검토했다. 기존1597 입력에 새2개를 더한1599, ancestor308, 원 추가34에새2를 더한36 범위를 사용한다.

원 CPU98%x4/RAM 비율/가용RAM·commit/Native/IO600·공유metadata720/Job6.25%·affinity1·BelowNormal·최대16·kill-on-close·no-breakaway/원 두 전체byte·identity·정리를 유지했다. Native 획득14·원 global/byte20·metadata32·byte binary1/other2MiB/s도 유지했다. 예상 nominal579.107324초는 원600 내이며 실제 완료 보장이 아니다. 접근허용/한글/빌드/Git/설치/Defender·WSL·OS 변경 없음.

무작업 보류 불변 재사용 예외는 여전히 admission-only이다. own partial IO/제품 STOP 자동 수용·자동 반복은 없다. 이번 후속 actual101 실패는 따로 검토하며 P291을 즉시 재호출하지 않는다.

P291 지원20 거부조건은3입력·6reads·243020bytes·최종fresh3/3·정리/STOPnull로 통과했다. 최초 별도 inline support harness에서 잘못된 module의 finish_watcher를 호출한 AttributeError가 있었다. harness만 정식 sql_runtime_supervision helper로 바로잡았고 runtime 코드·실패/수용 결과는 변경하지 않았다. 이후 source/test는 실행된 pin으로 동결했다.

## P291 light run001: 준비만 통과, 제품/Native 전체실행 아님

| 항목 | 관측 |
| --- | ---: |
| 상태 | PASS_REVIEWED_ANCHOR_SELECTION_NOT_ACTUAL_OR_GATE |
| 원1278+현재104+다음104 계약 | 1486 |
| 기존 수용 / 선택 | 94 / 101 |
| 준비 reads / bound=fresh / bytes | 667 / 244 / 77557959 |
| 기존 CPU 표본 / 시스템CPUmax / ownCPUmax | 110 / 95.5% / 6.133991% |
| own private max / 가용RAMmin | 59203584bytes / 24.837713% |
| STOP / watcher cleanup | null / 확인 |
| 제품 본체 실행 | false |

전체1599 입력 catalog/budget/원 계약에 대한 준비 경로이며1599 Native 두 전체 byte 실행이나 제품 통과로 확대하지 않는다. 별도 sampler/child 없이 원 guard와 모든 원 metadata 읽기를 유지했다.

## P291 actual101 run002: 본체 한 건 성공, 최종 source 미완료

| 항목 | 관측 |
| --- | ---: |
| outer root | FAILED_NOT_ACCEPTED |
| outer error / resource reason | STOP_SUSTAINED_SYSTEM_CPU |
| 계약 / 선택 | 1486 / 101 |
| 준비 reads / bound=fresh / bytes | 669 / 245 / 77663915 |
| 원 parent failure body | STOPPED_NOT_ACCEPTED |
| body operation phase | final_source_freeze |
| 원 terminal summary | passed1,failed0,ignored0,filtered248 |
| 원 exit code / tests_passed | 0 / 필드없음 |
| body actual_product_child_executed | true |
| 전체 첫 byte 읽기 | 1599 / 119993724bytes |
| 중단된 마지막 byte 읽기 | 474 / 56921407bytes |
| Frame | CLOSED, registered=false, 완성 before경계1개 |
| 잠금 opened / closed / remaining | 1907 / 1907 / 0 |
| duplicate opened / closed / remaining | 2073 / 2073 / 0 |
| 실제 Job active / CPUtotal / private peak | 0 / 2.172초 / 27.92MiB |
| 원 parent elapsed | 182.9초 |
| 원 Native 획득 / 첫 guard오류elapsed | 136.629838 / 319.530993초 |
| CPU 표본 / 시스템CPUmax / ownCPUmax | 732 / 100% / 6.165748% |
| own private max / 가용RAMmin | 58032128bytes / 22.856593% |
| watcher / 원Job 정리 | 확인 / 확인 |

outer failure_diagnostic은 owned_parent이며 원 Native guard의 first error.phase는 final_fresh_hash이다. ParentConnection이 반환된 직후 원 mark/check가 STOP을 다시 전파해 after_parent/after_release 이벤트가 기록되지 않았다. 이를 시간0/완료 이벤트로 만들어 넣지 않았다. finally에서 실패 본체를 별도 sidecar로 보존했고 원 case 파일은0byte placeholder 그대로다. 완성된 두 전체읽기·COMMITTED·held identity closing이 없으므로 제품 terminal1을 runtime 수용으로 승격하지 않는다.

outer actual_product_child_executed=false는 정상 결과의 후속 반영 코드에 도달하지 못한 기본값이다. 이 false를 “제품 미실행” 증거로 쓰지 않았다. 보존된 body의 actual_product_child_executed=true·원 selected/passed/testargs·terminal/capture·Job limit/cleanup을 확인해 실제 한 건 실행과 원 성공 후보를 검토했다. failure writer의 product_body_executed=false는 기록 과정에서 재실행하지 않았다는 정책이며 과거 제품 실행 여부를 덮어쓰지 않는다.

마지막4 host CPU 표본은 모두100%였다. 첫 표본의 ownCPU0.107759%/읽기 증가213753bytes 이후 마지막3은 ownCPU0/읽기 증가0이다. 원 early90은 warning2/window5/2.5초 대기했다. 정확한 source_byte/entry/guard/pacer 경로 및 Frame read_boundary/commit·parent bridge·원 InputLocks.check를 검토했다. 원95/early90/byte/Native pacer는 bounded sleep·기존 sampler를 사용하고, full byte/read/identity 확인과 cleanup을 유지한다. 검증 자체의 무한 hot loop·중복 sampler·무제한 allocation/재시도는 확인하지 못했다. 전체 시스템포화나 파일 읽기가 외부 부하를 유발했는지의 인과성·프리즈 해결은 미확정이다. 따라서 새로운 보호완화/근거없는 rate 수정은 하지 않았다.

## P293: 완료 본체/미완료source 후보의 명시적 검토

새 review_completed101_stop.py와 test_completed101_stop.py를 추가했다. 원 root/body/placeholder SHA·길이, 원100 final plan과101 prior plan, compiled inventory249의101 이름, 두 신규review코드를 원 보호 reader에서 fresh로 검토했다. 총7입력·14reads·5026630bytes·최종fresh7/7·기존7표본·STOPnull·정리 확인이다.

30개 거부조건은 root/body PASS 승격·실패 sidecar drift·큐 advance·terminal pass 없는 본체·Job 잔여/limit 변경·input 제외·부분post474를1599로 변경·CLOSED를COMMITTED로 변경·잔여 lock/duplicate·CPU tail 제거·Gate 승격을 거부했다. 실패 구조와 source scope는 그대로 보존하며 제품 본체/Job/Native를 재실행하지 않았다.

검토 PASS는 **독립 source 마감이 필요한101 후보 한 건**을 증명할 뿐 runtime 수용이 아니다. 원 root는FAILED, body는STOPPED, placeholder0byte, 원부분post474 상태를 유지한다. runtime accepted94/next101/remaining155/whole91은 그대로이며 독립 source 마감 추적만0→1이다.

## 최적화와 다음 실행 경계

진행 정책의 실제 개선은 통과한97~100과 완료된101 제품 본체를 다시 실행하지 않고, 원 증거·실패 검토를 재사용 가능한 qualification의 입력으로 보존하는 것이다. 이번 코드 변경이 CPU 포화/프리즈를 해결했다고 주장하지 않는다.

전체 preparation metadata가667/669reads로 늘어난 실제 비용을 기록했다. 기존720을 올리거나 mandatory fresh/identity를 스킵하지 않는다. 다음은101 원 source1599 전부와 closing/review/compound controller를 포함한 **별도 두 전체 byte·Native identity 마감** 구현/거부조건 qualification이다. 기존 P258/P259의 source-only/compound 패턴을 현재 scope와 원 pin에 맞춰 사용할 수 있음을 확인했지만, 현재101 독립 full source closing과 compound 수용은 **NOT_RUN**이다.

새 closing에서 Job/제품을 만들지 않고 원 Job 정리 witness를 사용한다. 독립 source가 원 두 실제byte/전체identity/정리 조건을 완료한 후에만 별도 compound가95번째 수용을 할 수 있다. 원 failed 결과나 partial hash를PASS로 다시 쓰지 않는다. 동일101 제품 본체 재실행·P291 즉시retry·접근허용·P10 진입은 하지 않는다. 목표 ACTIVE.

## 불변 증거

| repository-relative 경로 | bytes | SHA256 |
| --- | ---: | --- |
| implementation/p09/evidence/locked-r07/p291-light-run001.v1.json | 52978 | 6e9131e24aefc275d98adb1932ec3e3b942143de04875f6e0fe03aaec4308037 |
| implementation/p09/evidence/locked-r07/p291-case-101-run002.v1.json | 977979 | 20dbb9c846f3b1f719204b9583c51a71cf578a708ab10b2a81c08d61c35495fa |
| implementation/p09/evidence/locked-r07/cases/p291-failure-101-run002.json | 529451 | aeea72d5940d6e0de7f585716101857733d8955c7678017ed141df81816aafff |
| implementation/p09/evidence/locked-r07/cases/p291-case-101-run002.json | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| tools/p09/resume_reviewed_anchor_runtime.py | 45495 | 1967bcd50c673cb6b48a7e1e3169899a95ac5d792bd7adbd55b94cf80440271e |
| tools/p09/tests/test_reviewed_anchor_runtime.py | 3866 | d8e209bb0b4d81bcfeb6965fb8ff3a5824fa15170d95ace872652e48a963f22d |
| tools/p09/review_completed101_stop.py | 8471 | 0a5b1b898813b582a8a5d3df3052b18fc9e616808666636d42e5be0bf7635c41 |
| tools/p09/tests/test_completed101_stop.py | 4297 | 9727f3de024de20d95a662fd96e712355a0fd79c14511a94dc3546d92813541d |

P293 지원검토: implementation/p09/evidence/locked-r07/p293-case101-completed-body-stop-review-run01.v1.json. 문서r117 preimage를 별도 archive와 전체 byte suffix로 보존해r118로 갱신한다. 문서 pin/review는 실제 source 마감/제품 전체/Gate를 대신하지 않는다.
