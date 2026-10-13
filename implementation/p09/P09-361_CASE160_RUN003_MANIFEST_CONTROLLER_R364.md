# P09 case160 run003 입력과 controller 연결

실제 manifest028에 기존26쌍과 검증된3개 표현을 채택해29쌍으로 구성했고, 별도 run003 capsule004와 controllerV31의 계약 검사를 통과했다. 새 전체 Binding 및 비용 검증은 CPU 보호로 중단돼 DATA039, 전체 preflight와 제품 실행은 미검증이다. 공식153/249와 P09, A12, A13 OPEN을 유지한다.

## 실제 manifest와 전달 검증

manifest028은 physical run3을 명시하고 이전 manifest027의 run2 metadata는 그대로 보존한다. 기존26쌍의 전체 admission을 실행한 뒤 실제 이전159 semantic scope에 있는 case133,138,137만 추가한다. producer source pin, 원본과 실제 표현을 fresh 검사하며 원본을 삭제하거나 소급 변경하지 않는다.

처음 전달 검사 r821은 계약18개와 전달·복원이 통과했지만 테스트 pin을 final 이후에 추가해 fresh214와 final213이 불일치했다. `INCOMPLETE_QUALIFICATION_POST_FINAL_TEST_PIN_NOT_CURRENT_TRANSPORT_PASS`로 보존하고 전체 통과 근거로 사용하지 않는다. pin을 final 전에 고정하고 마지막에 건수 일치를 검사하도록 수정한 r822는 fresh 및 final216개, 계약18개와 cleanup을 통과했다. 시스템 CPU 최고35.62%, 사용 가능 RAM 최저48.70530%였다.

검증된 canonical wire는15,662바이트이며 실제 capsule004는 한 LF를 포함해15,663바이트다. 원래16KiB 제한 이내다. schema v6와 `case160-current-r003-tests`를 사용하며 이전 capsule003 및 실제 run002 결과는 재작성하지 않는다. worker dispatch와 원래 connector code는 보존한다.

## 전체 Binding 보호 중단과 코드 보강

전체29쌍 Binding은 원래 이전 전체 oracle, 두 선언 재사용, 원600초 비용 조건 및 최종 freshness를 함께 검사하도록 구성했다. bounded bootstrap은 core16과 실제 capsule·manifest chain만 허용하며 원64 reads 및262144 bytes 상한을 유지한다.

r823은 메타데이터 CPU 보호에서 중단됐다. 시스템 CPU 최고92.23%, 사용 가능 RAM 최저51.70347%, cleanup 확인이다. 제품 및 Native 실행은 없었다. 중단 지점은 paced fresh read였으며 새 guard는 기존 표본을 O(1)로 검사한다. 새 재사용 코드는4096개 이하 원장과 작은 선언만 보관하며 별도 thread·sampler를 추가하지 않는다.

중단 후 시스템 CPU9%와 MRT 부하6%가 관측됐지만 이전 급등의 원인을 입증하는 자료는 아니다. 부모 CPU 및 private memory와 완료된 읽기 집계를 기존 guard 표본에서 기록하고, private 함수 복원 오류가 있어도 guard 정리를 실행하도록 보강했다. 그 뒤 단일 r824는 CPU75%에서 보호 중단됐다. 부모 CPU 최고4.95320%, private memory 최고48.90234MiB, 사용 가능 RAM 최저36.41125%, cleanup 확인이다. 이후 CPU18% 표본에서는 TiWorker와 별도 Python 부하가 관측됐고 hwpx-agent Python은 없었다. 외부 프로세스 종료나 OS 설정 변경은 하지 않았다.

두 중단은 실패로 보존한다. 전체 Binding,600초 비용, 공유720초 완료와 최종 freshness를 PASS로 승격하지 않는다. 반복적인 대규모 읽기를 더 실행하지 않고 코드 연결 작업을 진행했다.

## controller 계약 검증

controllerV31은 원래 function family의 task·preflight 목적지 metadata만 새 실행으로 연결하고 역변환을 확인한다. 원 engine 및 worker를 유지하며 physical3의 단일 template을 사용한다. 새29쌍 Binding과 capsule004, manifest028, bounded bootstrap을 명시적으로 연결했다. first-run 실패 review와 과거 lineage 선언 재사용은 private namespace dependency에만 연결하며 기존 소스와 기본 모듈을 재작성하지 않는다.

r826의 원래14개 계약과 신규4개, 합계18개가 통과했다. 실제29쌍 bounded graph와 run003 task, 원래 단일 adapter, source namespace 보존을 검사했다. fresh 및 final68개, cleanup 확인이다. 시스템 CPU 최고52.74%, 사용 가능 RAM 최저47.21316%였다. engine, frame 및 worker 실행은0이다. 이 계약 검사는 실제 import inventory와 전체 비용 검증을 대체하지 않는다.

## 다음 실행 경계

보존된 중단의 읽기 집계와 부모 자원 증거를 기준으로 전체 입력 검증 코드를 추가 검토한다. 전체29쌍 Binding과 원래600초 및 공유720초 비용을 먼저 통과시킨 뒤 DATA039의 실제 pin을 고정하고 원래 전체 preflight를 수행한다. 그 전에는 run003 제품 실행을 허용하지 않는다. 두 Native 읽기와 독립 승인 전에 공식 건수를 늘리지 않으며 P10 구현을 시작하지 않는다.

권위153, 성공159, 실패160 두 회, 원본 corpus와 사용자 변경은 보존한다. 목표는 ACTIVE다. 접근 허용, UAC, OS 설정 변경, 외부 프로세스 종료, 삭제·이동과 원격 push는 수행하지 않았다. PC 프리즈 해결과 외부 부하의 인과관계는 미증명이다.
