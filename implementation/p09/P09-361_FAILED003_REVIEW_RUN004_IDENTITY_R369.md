# P09 실패 기록 검토와 새 실행 준비

2026-10-14 공식 승인은 153/249, 잔여 96개, 다음 사례 160, generation 48이다. P09/A12/A13은 OPEN이며 P10은 시작하지 않았다. 이번 변경은 실패 증거의 독립 검토와 다음 실행 준비이며 제품 승인이나 실행 허용을 대신하지 않는다.

## 실패 run003 독립 검토

원본 4,242,304bytes/SHA-256 `61b51f2bd10ea9a9a6f4bda94b8863eec90e73550038147c0e8652fb2790feb9`를 읽어 CLOSED frame과 정리를 검토했다. 공유 metadata 720초 만료가 `final_source_freeze`에서 발생했고, 완전한 바이트 경계는 before 1개뿐이었다. Native/runtime qualified는 False로 유지한다.

첫 경계의 입력 2,801개/247,714,063bytes와 `source_freeze`가 일치했다. 핸들 3,173개와 borrowed view 5,589개는 모두 닫혔다. 두 번째 읽기는 부분 진행 상태이며, decoder 44회를 필요한 완전한 두 경계의 58회로 승격하지 않는다.

r843 CODE10 검사와 최종 재읽기 4/4가 통과했다. CPU 최대 8.98%, 가용 RAM 최소 62.948815%, cleanup True였다. 검토 결과는 실패를 보존하며 재시도·GO·승인을 허용하지 않는다.

## 두 실패 기록의 별도 무손실 표현

| 원본 | 원본 bytes | 별도 물리 표현 bytes | 감소 bytes |
| --- | ---: | ---: | ---: |
| run002 | 4,217,213 | 1,560,359 | 2,656,854 |
| run003 | 4,242,304 | 1,572,291 | 2,670,013 |

원본을 덮어쓰지 않고 `p361-lossless-runtime-inputs/case160-runtime-run002.failed.envelope.v1.json`과 `case160-runtime-run003.failed.envelope.v1.json`을 생성했다. 원 codec·64KiB 작업·2MiB/s exclusive publisher·fsync를 유지했다. 원본 복원 4회가 byte/hash 단위로 일치했고 decoder 합계 0.061121초로 5초 한도 안이었다.

r844 최종 재읽기는 24/24, CPU 최대 8.13%, 가용 RAM 최소 64.608641%, cleanup True다. 두 물리 표현은 아직 manifest에 채택하지 않았고, 성공한 제품 증거로 처리하지 않는다.

## Run004 identity와 단일 adapter

새 identity는 정확한 `case160-current-r004-tests`, 물리 실행 번호 4, 새 root run004를 사용하며 이전 번호와 bool 입력을 거부한다. historical identity 및 기본 namespace는 바꾸지 않았다. 기존 template의 metadata만 투영하고 원 engine/worker 함수 본체를 유지한다.

실제 원 window에 연결한 r845 CODE38 검사가 통과했다. adapter는 정확히 하나이고, 그 adapter와 원 engine은 같은 private globals를 공유한다. 실제 engine/worker 호출 수는 0이다. run004 root는 아직 존재하지 않는다. 최종 재읽기 63/63, CPU 최대 33.70%, 가용 RAM 최소 62.804352%, cleanup True다.

## Private graph의 두 실패 역할

새 extension은 독립적으로 검토한 run002·run003만 정확한 byte/hash와 명시적 물리 경로로 받아들인다. 다른 descriptor와 기존 representation은 원 코드로 위임하며, 새 private source graph만 변경한다. 두 실패의 provenance는 accepted=False로 유지하고 수정할 수 없는 선언으로 보존한다.

r846 CODE12 검사와 실제 private 31쌍 구성이 통과했다. 기존 29쌍은 모두 유지됐고 두 실패 역할을 별도로 표시했다. 원 worker codec을 compact wire에 연결한 결과 31개 descriptor가 11,015bytes로 인코딩·복원됐다. 16,384bytes 제한은 그대로다. 최종 재읽기 51/51, CPU 최대 18.89%, 가용 RAM 최소 65.145337%, cleanup True다.

이 구성은 기존 manifest pin을 진단용 생성자 입력으로 사용한 **in-memory 후보**이며 실제 31쌍 manifest를 만들거나 승인한 것이 아니다. qualifier 입력을 포함한 예상 Native 비용은 decoder 5초 포함 601.222810초로 원 600초 조건을 충족하지 못했다. 새 controller/runtime 승인으로 처리하지 않는다. 전체 결합 단위검사 122개도 통과했다.

## 남은 연결 작업

추가 과거 입력의 무손실 표현을 실제 이전 scope에서 확인하고, compact capsule과 실제 새 manifest·graph에 채택해야 한다. 그 다음 run004 controller의 전체 준비·비용·preflight, 실제 두 Native 바이트 경계, 독립 case160 제품 oracle이 모두 필요하다. 기존 run003은 재실행하지 않는다.

원 Native600/shared720·scope·자원 보호·worker GO/Job 본체와 독립 승인 조건은 유지했다. 접근 허용·UAC·OS 설정·외부 종료·삭제·이동·원격 push는 없었다. 목표는 ACTIVE이고 PC freeze 해결은 미증명이다.
