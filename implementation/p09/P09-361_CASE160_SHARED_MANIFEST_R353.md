# P09 160번 manifest 선언 재사용의 실제 연결 검증

manifest 선언 재사용을 실제160 전체 Binding과 이전159 전체 oracle 경로에 연결했다. 최종 fresh 검사까지 통과했으며 공통 역사 결과16개에서88,240,666byte의 반복 읽기 감소를 확인했다. 공식 승인 수는153/249, 잔여 개별 사례는96개다. 새 controller·제품 실행이나 P09 Gate 완료를 뜻하지 않는다.

## 전체 검사 경로 보존

원래160 Binding, 이전 사례 callback과 독립159 prepare의 코드 객체를 그대로 유지하고 private 의존성만 연결했다. 두 admission이 동일한 private159 그래프와 facade를 사용한다. 최초 전체 manifest admission은1회 수행하며 동일 reader·의존성·검증 원장에서 중복 선언1회를 재사용한다.

기본160 설정과 원래159 graph·checkpoint, 원래 manifest loader는 변경하지 않았다. 관측 결과나 frame을 수정하지 않으며 Native 두 실제 byte 경계와 최종 fresh 확인을 대체하지 않는다.

## 실제 연결과 최종 확인 결과

r775는 `PASS_SHARED159_MANIFEST_ACTUAL160_FULL_BINDING_FINAL_FRESH_NOT_CONTROLLER_PREFLIGHT_OR_GO`다. 전체 scope2,772개, Rust 소스787개,24쌍을 연결했고 fresh와 최종 hash 확인은1,083개 모두 일치했다.

시스템 CPU 최대 관측값은48.94%, 최소 가용 RAM은39.66936%, 검사 프로세스의 machine CPU 최대값은5.45623%, private 메모리 최대값은71.16016MiB다. cleanup은 true이며 Native·제품·큐 승인은 실행하지 않았다. 이 관측으로 프리즈 해결을 단정하지 않는다.

## 반복 읽기 비교와 한계

준비 단계의 진단 요청은1,285회에서1,191회, 읽은 byte 수는459,281,820에서330,902,234로 줄었다. 두 진단의 전체 차이는128,379,586byte,27.95225%다. 두 실행의 진단 입력 구성이 같지 않으므로 이를 동일 workload의 정확한 효과로 해석하지 않는다.

동일한 역사 결과16개만 비교한 읽기 감소는88,240,666byte다.158번 결과는9회에서6회,147번 등 여러 결과는5회에서3회로 줄었다.159번 결과는5회로 유지됐다. 이 공통 파일 비교는 진단 입력 차이와 구분한 감소 관측이다.

최종 확인을 포함한 새 실행은2,274회·502,671,672byte를 읽었다. 모든1,083개 최종 fresh 확인을 유지했다. 이전 r772는 준비 계측 후 metadata CPU 경고로 최종 fresh가 중단된 기록으로 보존하며, 그 실행을 전체 검사 통과로 바꾸지 않는다.

## 다음 실행 조건

새 연결을 실제 controller·DATA와 검토된 별도 physical run에 반영하고, 원160/run001 실패 provenance를 보존해야 한다.600초 Native 비용뿐 아니라 준비 단계부터 마지막 확인까지의720초 공유 metadata 비용도 검토한 후 전체 preflight와 단일 제품 실행, 독립 승인을 수행한다.

원래 입력 범위, 읽기 속도, deadline 및 자원 보호를 약화하지 않았다. P09, A12, A13은 OPEN이며 P10 새 구현은0이다. 기존 권위153·성공159·실패160과 사용자 소유 변경을 보존했다. 접근 허용·UAC·OS 설정 변경·외부 프로세스 종료·원본 삭제와 이동·원격 push는 수행하지 않았다.

근거는 `evidence/p09-361-case160-shared-manifest-full-binding-r775.v1.json` 및 `evidence/p09-361-case160-shared-manifest-read-comparison-r776.v1.json`이다.
