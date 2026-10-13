# P09 160번 metadata 중복 작업 분석과 최적화

실제160번 단일 실행은 마지막 전체 입력 확인 중 공유 metadata720초 deadline에서 중단됐다. 제품 출력 캡처는1.69233초 안에 완료됐지만, 두 실제 byte 경계 중 한 개만 완료돼 전체 Native·제품 통과로 인정하지 않는다. 공식 승인 수는153/249, 잔여 개별 사례는96개이며 P09, A12, A13은 OPEN이다.

## 실제 실행과 정리 결과

실패 결과 `evidence/p09-361-case160-current-runtime-run001.v1.json`은4,128,024byte, SHA256 `5e2af60e8961c16661a25301d462ead53445141ef67bb58ef52f33253a001df0`로 보존했다. 중단 단계는 `final_source_freeze`, 원인은 `FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE`이다.

잠금 핸들3,114개는 모두 닫혔고 남은 핸들은0개다. cleanup과 owned tree empty는 true다. 시스템 CPU 최대 관측값은88.57%, 최소 가용 RAM은40.02374%, 검사 프로세스의 machine CPU 최대값은5.64262%, private 메모리 최대값은75.69531MiB였다. 이번 중단은 CPU 보호가 아니라 metadata deadline이며 시스템 CPU peak 원인과 PC 프리즈 해결은 입증하지 않는다.

Native acquisition의 reserve와 checkpoint에는222.71943초가 측정됐고 CreateFileW 자체에는0.75686초가 측정됐다. 준비 metadata 읽기는 이전159의302,772,053byte·1,175회에서160의455,904,666byte·1,297회로 늘었다. 기존600초 Native 기준과720초 공유 metadata 기준을 유지한다.

## 반복 읽기 계측

제품을 재실행하지 않고 원래 Binding 경로의 읽기 호출 metadata만 기록했다. r772에서 Binding 준비 후1,285회 요청으로459,281,820byte를 읽었으며,1,079개 경로 중 반복 읽기가283,404,539byte였다.158번 결과는9회,159번 결과는5회, 여러147~157번 결과는5~7회 읽혔다.

이후 최종 fresh 확인에서는75% metadata CPU 경고가 발동해 계측이 중단됐다. 따라서 준비 단계의 반복 읽기 관측은 보존하지만 전체 fresh 검사 통과나 새 실행 자격으로 사용하지 않는다. 계측은 파일 내용·hash·parsed JSON을 캐시하지 않았으며 원래 읽기와 자원 보호를 유지했다.

최초 r771의 계측 코드는 non-parsing read가 payload를 반환하지 않는 원래 인터페이스를 잘못 처리해 TypeError로 중단됐다. 원래 read가 반환한 pin의 byte 수를 사용하도록 고쳤고 두 실패 기록 모두 보존했다.

## 선언 재사용 helper의 범위

`same_reader_manifest_declaration_once_v1.py`는 첫 호출에서 원래 전체159 manifest loader를 실행한다. 이후 동일 reader, process·thread owner, 모든 의존성 객체, manifest pin 및 검증 원장이 유지되는 경우에만 검증된 선언을 재사용한다. Binding은 원래 constructor로 새로 구성하며 호출자가 결과를 수정해도 보존된 선언이 바뀌지 않는다.

다른 reader나 의존성에는 재사용하지 않고, 원장 변경이나 최종 fresh 단계 이후 호출은 거부한다. 저장하는 것은 검증된 descriptor·scope·proof 선언이며 파일 payload나 parsed JSON의 캐시가 아니다. 원래 Native 두 실제 byte 경계와 최종 fresh 확인은 그대로 필요하다.

r773에서 새 helper12개와 기존 source admission7개를 합한19개 검사가 모두 통과했다. fresh와 최종 hash 확인은7개가 일치했고 cleanup은 true다. 해당 실행의 시스템 CPU 최대 관측값은25.34%, 최소 가용 RAM은41.88699%였다. 아직 실제160 full graph에 연결한 결과나 실제 읽기 감소를 검증한 것은 아니다.

## 다음 전체 검증 조건

두 admission이 동일한 private159 Binding 모듈을 사용하도록 연결한 뒤, 선언 재사용을 원래 전체 Binding·최종 fresh 검사로 확인한다. Native600초 비용뿐 아니라 준비 단계와 실행을 포함한 공유720초 비용도 검토해야 한다. 감소가 확인되고 실패 provenance를 포함한 별도 physical run이 검증되기 전에는 제품을 재실행하지 않는다.

근거는 `evidence/p09-361-case160-run001-shared-metadata-stop-review-r770.v1.json`, `evidence/p09-361-case160-binding-read-trace-failed-r771.v1.json`, `evidence/p09-361-case160-binding-read-trace-stopped-r772.v1.json` 및 `evidence/p09-361-case160-manifest-declaration-code19-r773.v1.json`이다. 기존 성공·실패 증거와 사용자 소유 변경을 보존했으며 접근 허용, UAC, OS 설정 변경, 외부 프로세스 종료, 원본 삭제·이동 및 원격 push는 수행하지 않았다.
