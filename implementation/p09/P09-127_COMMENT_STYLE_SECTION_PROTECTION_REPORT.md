# P09-127 — 댓글 스타일의 실제 anchor 섹션 보호 누락 수정

## 조사 및 실제 결함

기존 CommentBuilder, caller full-IR preparation, stored preparation, rich body 및 원본
source review/catalog/assembly는 이미 존재한다. 원본 metaTag는 정확히 보존하지만
작성자/시간/visibility/resolution 의미는 UnverifiedNativeMapping이다. 이 값을 추측해
qualified 모델로 만들거나 기존 partial import admission을 우회하지 않았다.

기존 apply_style은 잠긴 스타일, 그 스타일을 기본 memoShape로 쓰는 잠긴 섹션,
그리고 잠긴 댓글은 검사했다. 그러나 댓글의 style_id가 해당 anchor 섹션의 기본
memoShapeIDRef와 다를 때, 잠긴 섹션 안의 그 댓글이 사용하는 스타일 변경을 허용했다.
typed 모델은 이 두 style 참조가 서로 다른 유효 상태를 허용하므로 실제 보호 누락이다.

## 재현 및 수정

새 synthetic typed 모델 테스트4개를 원래 CommentRequest/CommentBuilder에 연결했다.
수정 전 build PASS145.31초; test3PASS/1FAILED/exit101, 실패는 locked-anchor style 거부 반례다.
전체 원래 parent55408 bytes/SHAaa332c72…와 실패 executable1177600 bytes/SHAdf758458…를
별도 보존했다. 실패 receipt를 수정 후 성공으로 덮어쓰지 않았다.

production 변경은 apply_style의 잠긴 섹션 ID 집합 생성과 실제 댓글 anchor 섹션 검사뿐이다.
집합을 한 번 만들고 조회하여 댓글마다 전체 섹션을 재검색하지 않는다.
추가 collection과 predicate를 역으로 제거하면 원래 parent와 바이트 단위로 정확히 같다.
원래 스타일 잠금/기본 섹션 참조 잠금 검사와 모든 다른 모델 동작을 유지했다.

수정 후 build PASS119.79초; 실제 test4PASS/0failed/0ignored/0filtered/exit0이다.
잠긴 anchor 섹션의 비기본 댓글 스타일 변경 거부, unlocked anchor의 변경 허용,
무관한 locked 섹션이 있는 정상 변경 허용, 기존 locked default style 거부를 검증했다.
이는 native/HWPX 의미 승인이나 제품 Gate가 아니라 원래 typed 모델의 실제 보호 수정이다.

## 자원·보존 검증

기존 P121 target build cache 재사용/jobs1/CPU affinity1/BelowNormal/2초 샘플,
CPU85%3연속/여유 RAM4GiB/root working set2GiB/상한600초를 사용했다.
빌드 root RAM은 전체 빌드 RAM이 아니다. rustc 자식 약3.85GiB와 CPU1 적용을 별도로 관측했다.
빌드 자식 제한 관측은 초기159회/수정132회다. root RAM을 빌드 전체 사용량으로 보고하지 않는다.
빠른 test0.07초는 양수 test RAM 관측이 없어 실제 최대 RAM을 알 수 없다.
원본/운영 DB/SQL/키/설정/한글/Hwp/COM/UI/접근허용/설치/삭제·이동/stage·commit·push 없음.

새 byte-inverse unit6 PASS. 기존 P126/P125와 모든 ancestry 검증기를 변경하지 않고
선언한 한 parent의 전체 preimage 읽기 view에서 역사적 source1131/scoped228 증거를 전수 확인했다.
이것은 수정 후 현재 전체228 회귀 PASS가 아니다. 현재 전체 회귀는 미수용 상태를 유지한다.
첫 preimage audit는 cwd 형식 TypeError였다. 그 새 checker 전체 소스를 보존한 뒤
실제 cwd를 유지하는 __fspath__만 보완했으며 기존 검사를 교체하거나 약화하지 않았다.

## 현재 경계

current source1136 = 이전1131에서 parent1 교체 + 신규5개, inherited raw pins2592다.
현재 checkpoint는 source delta6/whole source archive 및 초기 checker2/이전 checkpoint1/
수정·실패 executable2/build·test receipts4를 고정한다.
목표 active/P09 Gate OPEN/product false/P10 새 구현 없음/PLANS 삭제 유지.
다음은 수정된 모델의 기존 comment_model 및 caller/stored comment 경로 회귀를 CPU/RAM 제한으로
검증한다. 작성자/시간/native lowerer/qualified source admission/원자적 publication/Gate는 계속 남는다.
