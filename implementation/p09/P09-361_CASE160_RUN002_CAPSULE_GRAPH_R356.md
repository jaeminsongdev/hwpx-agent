# P09 160번 run002 전달 파일과 공통 그래프 검증

실제25쌍 manifest026을 run002 worker 전달 데이터와 공통parent·frame·worker·전체 oracle 그래프에 연결했다. 전체 admission과 최종 fresh 검사가 통과했다. 공식 승인 수는153/249, 잔여 개별 사례는96개이며 이번 결과는 제품 실행이나 P09 Gate 완료가 아니다.

## 원래 전달 코드와 run002 metadata

원래 capsule connector와 encoder·decoder의 metadata 역변환, worker dispatch의 전체 코드·기본값·closure를 유지한다. 새 task는 `case160-current-r002-tests`, 새 wire schema는v4이며 별도 환경에 연결한다.16KiB 크기 상한은 늘리지 않는다.

r793에서 기존6개와 추가2개를 합한8개 검사가 모두 통과했다. 실제manifest026의25쌍을 encode/decode해 같은 private Binding 형식과 모든 descriptor·manifest pin으로 돌아오는 것을 확인했다. fresh·최종 hash199개가 일치했고 cleanup은 true다. 시스템 CPU 최대 관측값은44.32%, 최소 가용 RAM은47.96782%였다.

## 실제 파일과 canonical byte 구분

저장 파일은 `evidence/p09-361-case160-worker-policy-capsule002.v4.json`이며13,604byte, SHA256 `3f230f4273530d6536f68ef679dd6afb9ab6401faad077c58d570f263f83a79c`다.

원래 encoder의 canonical 데이터는13,603byte, SHA256 `78d2aafb9cae809a268607b123521a7b80b017b22693eea2bdbd36fa6d6937fb`다. 저장 파일과의 차이는 마지막LF1byte다. r794에서 저장된 실제 byte가 canonical 데이터에LF 하나만 추가한 값과 정확히 같음을 확인했다. 이전capsule001과 실패run001은 보존했다.

## 공통 Binding과 최종 확인

원래16개 core source의 모든 non-import AST를 유지한 private 그래프에 명시적인 부분 실패 역할을 연결했다. parent access·frame·worker와 raw policy·전체 oracle은 같은 Binding 모듈을 사용한다. 실제 capsule에서25쌍을 typed decode한 뒤 manifest026의 전체 admission 결과와 모든 descriptor 및 실제pin이 일치하는지 확인했다.

동일 reader의 context 선언은1회 수행하고 중복1회를 재사용했으며 최종 fresh 확인은 유지했다. r794는 `PASS_ACTUAL160_RUN002_SHARED25_PARENT_WORKER_ORACLE_GRAPH_NOT_ENGINE_PREFLIGHT_NATIVE_OR_GO`다. fresh·최종 hash198개가 일치했고 cleanup은 true다. 시스템 CPU 최대 관측값은50.56%, 최소 가용 RAM은43.59007%였다.

## 남은 실제 실행 조건

다음은 boundedrun002 bootstrap과 실제controller·DATA에 검증된 단일 physical identity와 선언 재사용을 연결하는 것이다.600초 Native 및 전체720초 metadata 비용과 전체 preflight를 확인한 뒤 단일 제품 실행과 독립 승인을 진행한다. 이번 검사에서는 engine·worker·Native·제품을 실행하지 않았다.

기존24쌍 전달 파일을25쌍으로 바꾸어 주장하지 않았다. P09, A12, A13은 OPEN이고 P10 새 구현은0이다. 원래 입력 범위·속도·deadline을 약화하지 않았다. 기존 권위153·성공159·실패160과 사용자 변경을 보존했고 프리즈 해결도 주장하지 않는다. 접근 허용·UAC·OS 설정 변경·외부 프로세스 종료·원본 삭제와 이동·원격 push는 수행하지 않았다.
