# P09 160번 실패 표현과25쌍 manifest 검증

실패한160/run001의 원본을 보존하고 실제 lossless 표현 파일을 저장했다. 수정된 실패 역할과manifest026의25쌍 전체 admission·최종 fresh 검사가 통과했다. 공식 승인 수는153/249, 잔여 개별 사례는96개다. run002 제품·Native 실행은 아직 수행하지 않았다.

## 실제 실패 표현 파일

원본4,128,024byte를1,535,747byte의 lossless 표현으로 저장했다. 표현의 SHA256은 `62f252f09fbe751789b0df6d3d13911ea1d6f617b8244d16331e996ea132d32e`이며 저장 경로는 `evidence/p361-lossless-runtime-inputs/case160-runtime-run001.failed.envelope.v1.json`이다.

원래 검증된CODE13 writer의 exclusive 생성, fsync 및2MiB/s 제한을 사용하고 두 번 복원해 원본 byte와 같음을 확인했다. 표현 차이는2,592,277byte이며 원본을 삭제하거나 덮어쓰지 않았다. r784에서fresh·최종 hash71개가 일치했고 cleanup은 true다. 시스템 CPU 최대 관측값은42.72%, 최소 가용 RAM은50.50058%였다.

## 실패 역할의 속성 연결 수정

처음manifest025의 닫힌 형식 검사5개는 통과했지만 실제 연결r785에서 실패 역할의 속성을 찾지 못했다. v1은 코드 상수의 문자열을 변경했으나 Python 속성 이름인co_names에는 이전failed004 이름이 남아 있었다.

v1, 실제 생산 기록과manifest025를 보존하고 v2를 추가했다. v2는 상수와 속성 이름의 metadata를 함께 변경하며 역변환이 원래 전체 코드와 같은지 확인한다. 실제 `failed160_partial_receipt_extension`의 provenance도 검증한다.

r790에서회귀 검사를 포함한7개 검사가 통과했다. 보존된v1 helper·테스트·원 qualifier까지 같은 reader에서 pin과 최종 hash를 확인했으며61개가 모두 일치했다. 시스템 CPU 최대 관측값은28.67%, 최소 가용 RAM은49.55814%였고 cleanup은 true다.

추가 연결 중 dependency alias가 빠진r786, 이전6개 테스트를 선택한r787, JSON 문자열을 dictionary처럼 처리한 보고 오류r789도 보존했다. r789의 최종 출력과 cleanup은 확인되지 않아 unknown으로 남긴다. 이전r788의제한된source pin qualification을 현재 전체 source 확인으로 승격하지 않는다.

## 실제 manifest026의 전체 검증

수정된 구성은 `evidence/p09-361-case160-source-manifest026.v4.json`이다. 기존manifest024의24쌍 전체 admission을 유지하고, 부분 실패1쌍과 해당 검토·생산·역할 증거를 명시적으로 추가했다. 생산 당시CODE6 pin과 현재 역할CODE7 pin은 구분해 검증한다.

r791은 `PASS_ACTUAL160_MANIFEST026_CODE5_FULL_ADMISSION_NOT_RUN002_CAPSULE_CONTROLLER_OR_GO`다. 닫힌 형식 검사5개,25쌍 전체 admission, semantic·physical projection 및 실패 provenance가 통과했다. fresh·최종 hash194개가 모두 일치했고 cleanup은 true다. 시스템 CPU 최대 관측값은42.30%, 최소 가용 RAM은48.47709%였다.

## 다음 제품 실행 조건

run002 capsule과 공통parent·worker·전체 oracle, controller 및DATA에 검증된 선언 재사용과 단일 실행 identity를 연결해야 한다. 원래600초 Native 및 전체720초 metadata 비용과 전체 preflight를 확인한 뒤 단일 제품 실행·독립 승인을 수행한다.

기존24쌍 capsule을25쌍으로 바꾸어 주장하지 않았다. P09, A12, A13은 OPEN이고 P10 새 구현은0이다. 기존 권위153·성공159·실패160과 사용자 변경을 보존했다. 입력 범위·속도·deadline을 약화하지 않았으며 프리즈 해결도 주장하지 않는다. 접근 허용·UAC·OS 설정 변경·외부 프로세스 종료·원본 삭제와 이동·원격 push는 수행하지 않았다.
