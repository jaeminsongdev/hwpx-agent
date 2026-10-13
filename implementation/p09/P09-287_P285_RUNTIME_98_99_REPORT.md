# P287: 같은 불변 P285 경로의 실제98·99 수용

2026-10-09. 목표 ACTIVE. runtime 부분집합 수용93/249, 잔여156(일반150+corpus6), 다음index100, whole 재조정대기90, 독립source 마감대기0. P09·A12·A13 OPEN. 이 수치는 P09 전체 완료율이 아니다. whole1470/historical67/full249/signed16/제품 완료/PC 프리즈 해결은 미확정이다.

## 범위와 실행 조건

직전 P285 actual97 수용91/249와 r115 증거를 길이/SHA로 확인했다. 현재34 추가 source/test/preimage·보고서·수용/원 실패/보류·문서 pin과98 본체 부재를 재확인하고 같은 불변 실행기를 사용했다. 이번 턴에 source/test 변경이나 새 runtime generation은 없었다. 접근허용·한글 UI·빌드·Git·설치·OS/Defender/WSL 설정 변경 없음.

98 actual run003과99 actual run004를 직렬 실행했다. 원 수용97은 저장된 root/body·원 pair/queue 조건만 검토하고 본체를 재실행하지 않았다.98 수용 후99 선택 때도98 본체를 재실행하지 않았다. 원 Native20/획득14/metadata32/byte binary1·other2MiB/s, 원 CPU98%x4·기존90/95 완화, RAM hard8%/soft7%/가용RAM·commit, Native/IO600·공유metadata720, Job6.25%/affinity1/BelowNormal/최대16/kill-on-close/no-breakaway·원 전후byte/identity/정리 조건은 유지됐다.

원97 CPU STOP과 원 P284 admission 보류를 미수용 상태로 유지했다. 무작업 보류 예외는 보호된 reader·계약·사례·Frame·Job·본체 미시작·원 admission/정리 검증에 한정하며 partial IO·실제 STOP·제품 실패를 소비하지 않는다. 이번98/99에는 own namespace admission 보류가 발생하지 않아 실제 같은 namespace 보류 후 재개는 여전히 NOT_RUN이다. 그 경로는 이전18 단위+3 synthetic 검증 범위이며 이번 제품 수용으로 확대 주장하지 않는다.

## 실제98·99: 각각 한 건 수용

| 확인 항목 | 98 run003 | 99 run004 |
| --- | ---: | ---: |
| root | PASS_EXACT_R07_NO_WORK_DEFERRAL_RUNTIME_NOT_WHOLE_OR_GATE | 같은 상태 |
| 원 제품 본체 | PASS_SCOPED_NOT_GATE, tests1 | PASS_SCOPED_NOT_GATE, tests1 |
| 원 현재/다음 포함 계약 | 1278 | 1278 |
| runtime 수용 / 다음 | 92 / 99 | 93 / 100 |
| 전후 각 입력 수/bytes | 1597 / 119944363 | 1597 / 119944363 |
| Frame/registry | COMMITTED / 해제 | COMMITTED / 해제 |
| held regular/directory identity | 1597 / 308 | 1597 / 308 |
| 잠금 opened/closed/remaining | 1905/1905/0 | 1905/1905/0 |
| duplicate opened/closed/remaining | 3194/3194/0 | 3194/3194/0 |
| Native reservations / metadata checks | 5099 / 7004 | 5099 / 7004 |
| 준비 reads / bound=fresh | 614 / 235 | 618 / 237 |
| 준비 bytes | 71680085 | 73360723 |
| 후속 reads / bound=fresh / bytes | 2 / 1 / 378158 | 2 / 1 / 370878 |
| 기존 CPU 표본 수 | 892 | 876 |
| 시스템CPUmax | 86.13% | 88.97% |
| 검증 CPUmax | 6.022183% | 6.015691% |
| 검증 private max | 57987072bytes | 58302464bytes |
| 가용RAMmin | 18.763253% | 16.125408% |
| 원 Job active / CPU total | 0 / 8.938초 | 0 / 2.031초 |
| 원 Job private peak | 29.45MiB | 22.03MiB |
| 원parent elapsed | 267.05초 | 258.51초 |
| Native 획득 완료 elapsed | 137.754634초 | 136.516034초 |
| Native parent 종료 elapsed | 404.839205초 | 395.082389초 |
| STOP / watcher cleanup | null / 확인 | null / 확인 |

각 실제 실행에서 전후1597 입력의 원 두 byte 검증, 동일 held regular1597/directory308 identity, shared offset reset3194, pathname reopen0, 잠금/duplicate/stream/binding 잔여0·원 Job active0와 소유 작업 트리 종료를 확인했다. 원 source 범위를 줄이거나 first pin을 최종fresh로 대신하지 않았다. 준비+후속 reads616/620은 공유720 이내다. 원Guard 첫 오류는 null이며 보호를 완화하거나 시간을 연장하지 않았다.

전체 시스템CPUmax86.13/88.97%는 검증 프로세스 max6.02%와 구별한다. 시스템 부하의 단독 원인·검증 코드의 인과적 개선·PC 프리즈 해결을 증명하지 않는다. 시스템 가용RAMmin16.125408%를 관측했지만 검증 private max58,302,464bytes·원 Job peak22.03MiB는 별도 소유 범위다. 다른 앱·Defender·WSL 상태를 원인으로 단정하거나 종료/설정을 변경하지 않았다. 이번 두 실행에서 CPU STOP은 발생하지 않아 근거 없는 추가 최적화 수정은 하지 않았다.

## 종료 후 재검토

root/body SHA·길이와 고정 compiled inventory249·원P212 legacy plan을 확인하고 **원 전체 record/Native/Job/metadata/queue validator**로 각 결과를 재계산했다. 현재34 추가 source/test/preimage pin과 Python AST를 두 실행에서 재확인했다.98 prior plan은97 final plan,99 prior plan은98 final plan과 일치했다. 각 단계는 이전 runtime accepted name 목록에 선택된 이름 한 개만 추가했다. 저장된 결과/현재 추가코드의 검토이며 전체1597 source/제품을 다시 실행한 것은 아니다.

원97 수용 root: implementation/p09/evidence/locked-r07/p285-case-097-run002.v1.json,651680bytes,SHA c3a30dbab87698fd605a40a18c3926777b1382dc392bc2b8683ad238a11b90a6. r115 문서 원byte suffix/별도archive를 보존하고 r116으로 갱신한다. 문서 검토는 whole/Gate 수용을 대신하지 않는다.

## 불변 증거

repository root 기준이다.

| 경로 | bytes | SHA256 |
| --- | ---: | --- |
| implementation/p09/evidence/locked-r07/p285-case-098-run003.v1.json | 651240 | e020ace1ca52e203c91404548bd383e3f28436e2095c0fe1cdef1da827c51d7d |
| implementation/p09/evidence/locked-r07/cases/p285-case-098-run003.json | 189079 | 59ab660aefdf749359e44d0f8a6c25727008e5095da1b2e17f0397bcbcb84474 |
| implementation/p09/evidence/locked-r07/p285-case-099-run004.v1.json | 650724 | be17c5e0b020ca676ec7ae042de6f2b8ca0f9b62a03ed711a7c820dee141c934 |
| implementation/p09/evidence/locked-r07/cases/p285-case-099-run004.json | 185439 | 89190779de1f3ecd5a367ead5b34f94947446f21c69302871770f9b39a2d248d |
| tools/p09/resume_no_work_deferral_runtime.py | 38204 | e637d4af60423ddbfde7165a1b83caf778fb62b3bbdeb7fc695795cbb5464267 |
| tools/p09/tests/test_no_work_deferral_runtime.py | 14756 | 2084e58009f57dddbababf5dd62ad78f9c6c18c8855849c2e1684bf39d8816ed |

## 다음 경계

목표 ACTIVE. 다음은 같은 불변 P285 actual run005의 미실행100번 한 건이다. 원 수용 pair/queue·현재/다음1278 계약·전체1597/ancestor308·원600/720/CPU/RAM/Job/전후byte/identity/정리를 유지한다. 보호 STOP 시 해당 단계/관측/코드를 검토하고 즉시 반복하지 않는다. 엄격히 확인된 무작업 admission 보류만 원 FAILED 상태와 큐를 보존한 검토 경로를 사용한다. passed body 재실행·guard 완화·접근허용·P09 Gate 미완료 상태의 P10 진입은 하지 않는다.
