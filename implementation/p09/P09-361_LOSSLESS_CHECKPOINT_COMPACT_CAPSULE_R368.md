# P09 checkpoint 읽기 비용과 worker capsule 크기 최적화

2026-10-14 공식 승인은 153/249, 잔여 96개, 다음 사례 160, generation 48이다. P09/A12/A13은 OPEN이고 P10은 시작하지 않았다. 이번 작업은 전체 입력과 기존 검사를 유지하는 표현 최적화이며, 새 제품 실행이나 승인 증가를 포함하지 않는다.

## 무손실 checkpoint transport

원 checkpoint r834의 2,693,611bytes를 보존하고 별도 envelope 973,539bytes를 생성했다. 감소량은 1,720,072bytes다. 원 codec의 64KiB 작업 단위, guard, 2MiB/s exclusive publisher와 fsync를 사용했고, 원본 바이트와 SHA-256을 두 번 정확히 복원·대조했다. 두 decoder 작업의 합계는 0.034654초로 원 5초 한도 안이었다.

물리 파일은 `implementation/p09/evidence/p361-lossless-runtime-inputs/case160-prepared-r834.envelope.v1.json`, SHA-256은 `499ee01169ea94b7fbb5ddab8ac95f3160cc55215fff26d7bd3093d5c086b394`이다. r839 producer의 최종 재읽기는 26/26, CPU 최대 35.19%, 가용 RAM 최소 59.094759%, cleanup True다.

`prepared_checkpoint_transport_v1.py`는 실제 carrier를 매번 읽고 원본 byte/hash를 복원한 다음 원 scope 검사 함수를 그대로 호출한다. 읽기 원장과 반환 scope에는 실제 carrier가 들어간다. 원본 checkpoint를 새 Native frame에서 직접 읽거나 잠갔다고 주장하지 않으며, 파일·hash·JSON 캐시는 사용하지 않는다.

원본 scope 재구성 검사와 transport 12개를 결합한 CODE58 검사가 통과했다. 실제 r840은 manifest 29쌍·Rust 집합 787개·167회의 inventory 요청을 유지했고 최종 재읽기 49/49, cleanup True였다. CPU 최대 29.98%, 가용 RAM 최소 59.563729%, 부모 CPU 최대 4.539395%와 private RAM 최대 46.765625MiB를 기록했다. 읽기는 98회/4,571,712bytes, 경과 시간은 18.042750초다.

새 qualifier 입력까지 포함한 Native 예상 비용은 decoder 5초와 원 margin을 포함해 **601.811217초**였다. 원 600초 제한은 그대로 이를 거부했다. 이전 603.148728초 검사와 이번 검사는 qualifier 입력이 달라 파일 표현 감소량을 제품 runtime 개선율로 변환하지 않는다. 실제 Native semantic 관계와 독립 제품 oracle의 연결은 여전히 미검증이다.

## Worker capsule compact wire

추가 무손실 alias를 채택할 때 capsule이 16KiB를 넘지 않도록, descriptor의 공통 context와 pin 필드명을 한 번만 기록하는 wire를 구현했다. 모든 값과 descriptor를 복원하고 원 capsule의 의미 schema·현재 권위·manifest·hash 검사를 그대로 수행한다.

기존 encoder와 decoder 함수의 code/defaults/closure는 동일하며, 바뀐 JSON 직렬화 인터페이스는 별도 private namespace에만 연결한다. 원 namespace와 worker 본체는 바꾸지 않았다. 입력과 출력 wire의 16,384bytes 한도도 그대로 유지한다.

실제 29쌍 capsule에서 원 canonical wire 15,662bytes가 10,337bytes로 줄었다. 감소량은 5,325bytes이며, 모든 필드·manifest·29개 descriptor가 복원됐다. 새 파일은 `implementation/p09/evidence/p09-361-case160-worker-policy-capsule005.compact.v1.json`, SHA-256은 `aed845a65bb150399a8e4e2acf04c4f540362793ff25a0f4fa3fb77489f07b54`이다.

r841 CODE14 통과, 최종 재읽기 25/25, CPU 최대 10.95%, 가용 RAM 최소 62.462902%, cleanup True다. 31개 descriptor는 단위 fixture에서만 검사했으며 실제 31쌍 manifest 승인으로 처리하지 않았다. 실제 worker 함수는 호출하지 않았고 새 capsule을 현재 manifest/controller에 아직 채택하지 않았다. 전체 결합 단위검사 72개도 통과했다.

## 남은 연결 조건

다음은 큰 미압축 입력의 무손실 표현을 독립적으로 검토하고 compact capsule을 새 manifest에 연결하는 작업이다. 실패 run003의 보존·독립 검토와 새 run004 identity, 전체 입력 준비·새 controller 비용·preflight, 실제 두 Native 바이트 경계와 독립 case160 oracle이 모두 성립해야 제품 승인이 가능하다. 기존 run003은 다시 실행하지 않는다.

Native600/shared720, 의미 입력 전체, 원 CPU/RAM 보호, worker GO/Job/subprocess 본체 및 독립 승인 조건은 유지한다. 원본·기존 실패·사용자 변경을 보존했으며, 접근 허용·UAC·OS 설정·외부 프로세스 종료·삭제·이동·원격 push는 없었다. 목표는 ACTIVE, PC freeze 해결은 미증명이다.
