# P09 case160 메타데이터 중복 검토 최적화

공식 승인은 153/249, 잔여 개별 사례는 96개다. P09, A12, A13 Gate는 OPEN이며 목표는 ACTIVE다. case160 run002는 제품 본문을 실행했지만 최종 source freeze를 완료하지 못해 승인하지 않았다.

## 커밋과 검증

현재 세션의 P09 변경과 실패 증거를 먼저 `886564d`에 커밋했다. capsule의 누락된 검증 경로를 수정한 뒤 기존·신규 계약 검사 17개가 통과했다. 수정된 26쌍 입력의 전체 Binding 검사는 r804에 보존했다. Native 비용 예상은 599.461205초로 원래 600초 이내였고, fresh 및 final 1,119개와 cleanup이 확인됐다.

새 controller의 import 실패 r805와 목적지 비교 실패 r806은 별도 증거로 남겼다. 이를 수정한 r807은 계약 검사 18개, fresh 및 final 59개를 통과했다. DATA038의 전체 preflight는 실제 import 64개, fresh 및 final 1,117개를 통과했다. 시스템 CPU 최고 43.35%, 사용 가능 RAM 최저 52.42144%, cleanup 확인이다. 이 결과를 `38bfd94`에 커밋한 뒤 단일 제품 실행을 진행했다.

r802는 수정 전 capsule 소스의 전달 검증 기록이다. 수정 후 전체 입력의 현재 근거는 r804이며, 이전 성공 기록의 소스 pin을 소급 변경하지 않는다.

## 제품 실행 결과

case160 run002는 `FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE`으로 720.01초에 중단됐다. 단계는 `final_source_freeze`였다. 제품 본문과 실제 자식 실행은 관측됐고 GO부터 전체 capture까지 1.721333초였지만, Native 두 번 읽기 중 한 번만 완료돼 frame은 CLOSED다. 전체 제품 PASS나 공식 승인을 부여하지 않는다.

입력은 2,782개, 실제 표현 바이트는 248,914,958이었다. 핸들 3,154개는 모두 닫혔으며 owned tree empty와 cleanup이 확인됐다. 시스템 CPU 최고 44.34%, 사용 가능 RAM 최저 49.83681%, 부모 CPU 최고 4.65388%, 부모 private memory 최고 77.95703MiB였다. 이번 중단은 CPU 보호가 아니라 시간 제한이었다. 컴퓨터 프리즈 해결이나 Defender와의 인과관계를 입증한 결과는 아니다.

원래 Native 600초 비용 검사와 메타데이터 preflight 통과만으로 공유 720초 실행 완료가 보장되지 않는다. 이번 실행의 bootstrap은 350,504,248바이트를 1,246회 읽었다. 최적화에는 제품 전 bootstrap과 이후 Native 읽기를 함께 고려해야 한다.

## 중복 읽기와 보조 코드

r811은 제품이나 Native를 실행하지 않고, 현재 DATA038 및 preflight038을 승인하는 전체 Binding 읽기를 집계했다. 최종 fresh 1,119개와 cleanup이 확인됐다. 시스템 CPU 최고 47.07%, 사용 가능 RAM 최저 48.35125%였다. 진단용 SELF와 이전 실패 review 입력이 포함되므로 실제 runtime의 bootstrap과 동일한 입력량이라고 해석하지 않는다.

최종 검사 전 1,235회 읽기, 354,229,890바이트 중 반복 읽기는 175,665,951바이트였다. 큰 반복 지점은 다음과 같다.

| 과거 증거 | 호출 횟수 | 반복 읽기 바이트 |
| --- | ---: | ---: |
| case158 run005 | 6 | 22,022,325 |
| case159 run001 | 5 | 18,322,704 |
| 실패한 case160 run001 | 5 | 16,512,096 |

새 `same_reader_failure_review_once_v1.py`는 동일 reader에서 원래 실패 검토를 완전히 수행한 후 작은 선언 메타데이터만 재사용한다. reader, API, checkpoint, 원장, 소유 process/thread가 달라지거나 최종 freshness가 시작되면 원래 검토를 수행한다. 재사용 경로에서도 원래 자원 checkpoint를 호출한다. 원본 파일 바이트, runtime JSON 행, hash 계산은 캐시하지 않는다.

r812에서 계약 검사 14개와 실제 실패 검토 1회 및 선언 재사용 1회를 확인했다. fresh 및 final 8개와 cleanup이 확인됐다. 시스템 CPU 최고 16.5%, 사용 가능 RAM 최저 50.79758%였다. 보조 코드는 아직 제품 controller에 연결하지 않았으며 실제 실행 시간 절감은 미검증이다.

## 다음 실행 경계

큰 과거 증거의 중복 승인 호출을 검토하고, 보조 코드의 독립 연결·전체 source/import inventory·공유 720초 비용을 검증한다. 현재 통과한 검증은 근거로 보존하며 입력이 변한 범위만 재검증한다. Native 두 번 읽기, 최종 freshness, 원래 source scope, 속도·시간 제한과 CPU/RAM 보호 조건은 유지한다. 새 실행 번호와 실패 증거 보존을 확인하기 전에는 제품을 재시도하지 않는다.

기존 권위 153, 성공한 case159, 실패한 case160 run001 및 run002와 사용자 소유 변경은 보존한다. P10 새 구현, 접근 허용, UAC, OS 설정 변경, 외부 프로세스 종료, 삭제·이동 및 원격 push는 수행하지 않았다.
