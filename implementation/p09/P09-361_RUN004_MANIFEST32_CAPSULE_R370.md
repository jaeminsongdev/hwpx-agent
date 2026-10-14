# P09 실제 새 입력 선언과 compact capsule 생성

2026-10-14 공식 승인은 153/249, 잔여 96개, 다음 사례 160, generation 48이다. P09/A12/A13은 OPEN이고 P10은 시작하지 않았다. 실제 manifest와 capsule을 생성·검증했지만 새 controller·전체 preflight·제품 실행·독립 승인은 아직 성립하지 않는다.

## 이전 실제 scope의 case132 무손실 표현

원 checkpoint r834에서 미압축 case132가 전체 scope에 존재함을 확인했다. 원본 2,472,248bytes/SHA-256 `6ebab43e075e1da55674120b9e5883408b6be63d45ab58170d06c27058d42f4d`를 별도 물리 표현 635,895bytes로 저장했다. 감소량은 1,836,353bytes다.

별도 경로는 `implementation/p09/evidence/p361-lossless-runtime-inputs/case132-runtime-run001.envelope.v1.json`, SHA-256은 `aa43301b55e28d0b843a53d4adda0635f9306e0a3ac33594126164187514629a`이다. 원본을 덮어쓰지 않았고 원 codec·64KiB 작업·2MiB/s exclusive publisher·fsync를 유지했다. 복원 2회가 전체 byte/hash 단위로 일치했다.

r848 최종 재읽기 18/18, decoder 합계 0.017703초, CPU 최대 16.82%, 가용 RAM 최소 64.271152%, cleanup True였다. 이미 승인된 case132의 제품 body를 재실행하지 않았다.

## 실제 manifest029와 compact capsule006

`runtime_successor_manifest_v7.py`는 기존 실제 manifest028을 그대로 참조하며 물리 run004를 명시한다. 이전 29쌍, 독립적으로 검토한 실패 run002·run003, 이전 실제 scope에서 선택한 case132의 별도 표현을 합쳐 32쌍을 구성한다. 실패 입력의 accepted=False provenance와 다른 원 descriptor·representation 검사를 유지한다.

manifest는 새 파일을 실제로 읽고 byte pin을 확인하는 loader를 통해 검증했다. 이전 private31의 진단용 생성자와 달리 실제 저장된 선언이며, 과거 manifest의 물리 번호를 다시 쓰지 않았다.

| 실제 파일 | bytes | SHA-256 |
| --- | ---: | --- |
| `p09-361-case160-source-manifest029.v7.json` | 742 | `6e2998cfc5cd7ebb690f1c46f61c6a34bcaa9c211a41d1638521ab23d608fde6` |
| `p09-361-case160-worker-policy-capsule006.compact.v1.json` | 11,346 | `2f17b916d461df129f5a4f7f45913dd472c7c7a56119ebd4000c5d867262bb92` |

두 파일은 `implementation/p09/evidence/`에 별도 생성했다. 원 16,384bytes capsule 제한을 유지하면서 32개 descriptor와 manifest pin을 실제 저장된 wire에서 복원·대조했다.

새 graph는 원 private binding module·parent·frame·full oracle 객체를 공유한다. encoder/decoder와 worker connector code/defaults/closure는 유지하고, private JSON wire 인터페이스와 정확한 run004 task metadata만 연결한다. 실제 engine·worker·Native·GO는 실행하지 않았다.

## 검증 결과와 범위

r849 manifest/graph CODE12 및 최종 재읽기 57/57이 통과했다. qualifier 입력을 포함한 선언 scope는 2,856개, physical scope는 2,824개다. 원 Native 모델의 예상 비용은 decoder 5초 포함 **599.769495초**로 원 600초 제한과 60초 margin 조건을 통과했다. CPU 최대 17.02%, 가용 RAM 최소 64.140616%, cleanup True, 경과 시간 24.312167초였다. 전체 결합 단위검사 134개도 통과했다.

이 비용은 **이번 생성 단계의 scope**에 대한 결과다. 준비 scope는 원 run003 checkpoint를 사용했으며 새 run004 controller의 전체 입력 준비·preflight가 아니다. 새 controller의 추가 코드·증거가 scope에 들어가면 다시 비용을 검증해야 한다. Native 실제 완료나 PC freeze 해결을 증명하지 않는다.

## 다음 실행 경계

새 manifest·capsule을 bounded graph bootstrap과 실제 run004 controller에 연결하고, 원 helper 64 reads/262,144bytes 한도와 전체 import closure를 확인해야 한다. 새 controller의 전체 준비·비용·preflight와 독립 case160 acceptance 경로 검증 후에만 단일 제품 실행, 두 실제 Native 바이트 경계, 독립 제품 oracle 및 공식 승인으로 진행한다.

원 Native600/shared720·의미 입력 전체·원본·실패 증거·CPU/RAM 보호·worker GO/Job 본체 및 사용자 변경을 보존했다. 기존 run003 재실행, 접근 허용·UAC·OS 변경·외부 종료·삭제·이동·원격 push는 없었다. 목표는 ACTIVE다.
