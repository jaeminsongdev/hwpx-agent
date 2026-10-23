# 원본 자동번호와 재시작 제어의 선택 치환

`hwpx-agent.source-selector-number-control-replacement/v1`은 SEARCH-009의 원본 AutoNumber/NewNumber
선택을 기존 complete number-stream compiler에 연결한다. 저장된 i32 번호와 명시적 Preserve/Replace
서식을 바꾸며 category·원본 control identity·선택 밖 값과 참조는 유지한다. components200은 원 기능20개·
새 review 연결10개·기존 strict 거부 진단1개·영향 컨트롤36개를67pass·723fresh/final723으로 검증했다.
기존 필수 review 성공 사례도 원 시험을 유지한 채 통과했다. 초기 MIXED/실패 원본은 아래에 보존한다.
현재 저장/엄격한 제품 요청은 별도 [제품 준비 계약](p09-number-control-product-request-v1.md)에 연결했다.
실제 저장 커밋·번호 재계산·Native 실행과 전체 SEARCH-009 완료는 아니다.

## 원본 선택과 변경

lower_review_selector_number_control_candidate는 원본 Form 또는 같은 원본의 operation-local
VerifiedFormReconstruction, 네 SourceIndexScopeSelector와 명시적 review 정책, AutoNumber/NewNumber,
유한 max_results, 저장 번호와 NativeNumberFormatReplacement를 받는다. caller가 XML·anchor·ID를
제공하거나 임의 category·제어 종류·구조를 바꿀 수 없다. 다른 종류는 원본 재구성 전에 UnsupportedKind다.

Replace 서식의 typed NumberFormat·user_character·prefix·suffix·superscript를 사용한다. 기존 유한
문자/요청 byte 제한을 먼저 검사한다. 서식이 없는 원본에 서식을 만들거나 제어를 삽입·삭제하지 않는다.
0/음수/i32 경계값은 저장 값 그대로이며 표시 번호나 재계산된 값으로 해석하지 않는다.

원 control matcher가 scope를 해석할 때 만든 geometry를 그대로 반환하도록 기계적으로 추출했다.
기존 start-only 발견 의미는 그대로다. 새 편집은 contains_whole로 원 제어의 outer range 전체가 선택에
들어 있는지 확인한다. node 범위 끝이나 half-open 선택 끝을 넘어가는 subtree를 편집하지 않는다.
구조 제어는 검색 block을 나누므로 선택 끝은 실제 inventory의 해당 block/normalized scalar로 지정한다.

## 보호와 원본 스트림

한 원본 proof·field/review/index·scope/matcher를 사용한다. 선택된 제어 subtree마다 의미상 no-op을
제거하기 전에 관측 잠금·상위 추적과 field/cache 교차를 검사한다. 원 guard3N에 part별 prefix count
1N을 더해4N으로 공유하고 각 제어마다 전체 자손이나 상위 경로를 다시 걷지 않는다. 정확한 MEMO
본문 예외는 기존 ReviewWriteContext만 사용하며 다른 field가 덮으면 차단한다.

기존 source caption/number state를 한 번 수입하고 control/section-start ID map을 한 번 만든다.
원 문서 시작값과 모든 원본 event의 순서·종류·지문·category를 유지한 완전한 요청을 구성하며 선택한
제어의 번호/서식만 대체한다. 기존 compiler·ID profile·writer·완전한 출력 번호 readback과 선택 밖
byte 대조를 재사용한다. 출력 Form/field/review의 추가 admission으로 review 보존도 확인한다.
이 출력 admission은 아래 review-aware 경로에서 기존 stream readback과 공유해 추가 재수입을 없앴다.

변경 기록은 원본 검색 순서를 유지하고 실제 attribute 변경이 있는 제어만 기록한다. 전체 no-op은
NoChange이며 성공한 빈 결과가 아니다. 선택 밖 제어에서 attribute 변경이 보고되면 readback 오류다.
receipt/후보는 원본·선택·요청 지문과 결과를 묶지만 현재 서비스 접근·저장 커밋·실행 권한은 아니다.

## 초기 실패와 원인 분리

components197는 신규20+영향기존36=56개를 실행해54pass/2fail이다. 원 실패를 보존했다. 하나는
시험이 구조 제어 전후의 두 block을 한 block 좌표로 지정한 오류였다. 실제 inventory 경계로 그 시험만
수정했다. 다른 하나는 원래 성공 조건을 유지한 review 제외/상한 사례의 실제 번호 수입 Coverage 거부다.

selection-recovery198은 수정1개와 원인 분리 진단1개만2pass·721fresh/final721·cleanupTrue다.
변경 없는54개는 보존했다. 신규 기능 고유19개+영향기존36개+별도 진단1개이지 현재56개 단일 실행이나
기능20개 전부 통과가 아니다. 기존 제품266개·공식249는 재실행하지 않았고 원 필수 review 시험도
삭제·완화·ignore하지 않았다. 198 당시 전체 source 자격은 false였고 이 실패 판정은 변경하지 않는다.

진단은 같은 원본에서 검색기가 숨김 제어를 제외한 뒤 max1로 본문 제어1개를 선택함을 확인했다.
하지만 기존 ImportedCaptionSourceState의 번호 수입기는 main/note/caption에 표현되지 않은 review
문단의 번호 제어를 Coverage로 거부한다. 숨김 안의 번호 제어가 없는 기준 원본은 같은 수입을 통과한다.
이는 당시 실제 입력/출력 연결의 미완료였으며 CPU 보호 중단이나 정책 필터 오류가 아니다.

197 전체82.844초·명령36.297초/시험10.29초·Job CPU34.578초·private최고1773.26MiB/5.5656%·
시스템CPU최고34.86%·가용RAM최저29.3168%다. 198 전체96.688초·명령4.422초/시험1.04초·
Job CPU3초·private최고581.33MiB/1.8246%·시스템CPU최고42.38%·가용RAM최저31.0251%다.
두 소유 Job active0/empty/handle closed이며 한 코어 affinity4·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%·명령300초·guard600초를 유지했다. 다른 앱/OS 설정 변경이나
PC 프리즈 해결·benchmark 주장은 없다. 근거는 implementation/p09/evidence/ 아래
p09-361-number-control-source-components197.v1.json과
p09-361-number-control-source-selection-recovery198.v1.json이다.

## 실제 review 모델과 공유 출력 수입

별도 import_review_bound는 같은 원본의 ImportedDocumentForms와 ImportedDocumentReviewBodies만
받는다. pointer identity와 원본 SHA가 다르면 거부하며 실제 관측 Flow에서만 추가 문단을 수집한다.
caller paragraph allowlist나 visibility 추정은 없다. 기존 main/note 문단 set은 그대로 빌리고 추가
review 문단만 상한을 검사한 뒤 소유한다. 기존 header/nonspine·미표현 제어·잘못된 ancestry/값/서식/
구역 시작 거부는 그대로다. 숨김 안의 다른 미지원 개체를 모두 수입한다는 의미는 아니다.

새 source-review-observations-v2 번호 수입 receipt는 review_body_inventory_sha256을 결속한다.
기존 strict import와 source-observations-v1은 review를 자동 수입하지 않는다. 새 optional 필드는
None일 때 JSON에서 생략되므로 기존 receipt wire 형태와 기존 strict Coverage 거부가 유지된다.
ImportedCaptionSourceState도 원본 Form/review pair에서 이 번호 모델을 조립한다.

기존 stream compiler는 입력 번호 모델이 review-bound일 때만 출력 Form·field·review·번호 모델을
한 원본 수입에서 연결한다. 기존 strict 입력은 이전 Body/번호 수입 분기를 사용한다. 완전한 번호·
frame·서식·exact byte readback은 그대로이며 실제 output_review_import receipt를 함께 보관한다.
새 번호 selector compiler는 그 receipt를 기존 ReviewWriteContext에 대조하므로 출력 ZIP/XML/Form/
field/review를 다시 수입하지 않는다. 이는 코드 경로의 중복 제거이며 실행 시간 개선율 주장은 아니다.

components200 원 기능20+새 연결10+기존 진단1+영향36=67pass·723fresh/final723·진단/경고없음·
cleanupTrue다. 원 실패 성공 시험, 네 review 정책 조합과 제외 후 상한·MEMO payload/cache 경계·
잠긴 no-op/제외 값 보존·foreign model 거부·header Coverage 유지·한도·strict wire/출력 분기 유지·
공유 출력 review의 SHA를 확인했다. 새 연결 외 기존 번호/다른 target importer·보호/요청/순서/참조/
byte readback 본문은 명시적 추가·출력 수입 선택·공유 receipt 전달만 역변환하면 원 파일로 복원된다.
기존 제품266·공식249는 반복하지 않았다. 원197 실패·198 MIXED를 현재 PASS로 덮어쓰지 않는다.

200 전체133.125초·명령40.422초/시험12.88초·Job CPU38.531초·private최고1771.43MiB/5.5599%·
시스템CPU최고49.02%·가용RAM최저28.2862%다. 소유 Job active0/empty/handle closed와 기존 한 코어/
낮은 우선순위/CPU·RAM/commit·시간 보호를 유지했다. 근거는
implementation/p09/evidence/p09-361-number-control-review-components200.v1.json이다.

AutoNumber/NewNumber의 현재 저장 서비스·엄격한 제품 JSON은 components203 신규26pass·727fresh/final727으로
연결했다. 원 compiler/공개 API 본문을 유지하고 불변 값 wrapper와 읽기 전용 검색 metadata getter만 추가했다.
다른 제어·전체 query/replacement/selector/filter·실제 저장/commit/CAS/영속 멱등/dispatcher/게시·
target match_set/semantic_diff/reopen·Native/Gate는 남는다. source API v12 incomplete/미해결4/
report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
