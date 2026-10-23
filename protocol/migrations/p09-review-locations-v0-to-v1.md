# 원래 source review XML/IR 위치 v0 → v1

## 추가

- ImportedDocumentReviewBodies::locate(fresh) → immutable ImportedReviewLocations
- StoredImportedReviewBodies::locate(provider, now) → immutable StoredReviewLocations
- ReviewSourcePoint/ReviewSourceLocation: actual original anchors, root-to-container path,
  sibling paragraph/run/XML-item ordinals, original paragraph/control node bindings
- ReviewLocationReceipt: whole source/review graph/observations/location digests와 scope counts
- whole replay verify_source/verify/with_verified_locations; 항상 거부하는 current product route

원래 simple CommentAnchor는 direct section body item 위치에만 사용한다. nested scope는
optional direct anchor=None이며 전체 source path가 남는다. 단순 anchor를 줬다는 사실은
한글 native character/caret/display 좌표나 완전한 native CommentState라는 뜻이 아니다.

## 호환과 거부

기존 IR schema/CommentOperation/registry/contract/readers/writers와 author/time/state unverified
상태를 변경하지 않는다. caller XML/positions/default author metadata를 입력으로 받지 않는다.
source/order/paragraph/control ref/paired field/receipt/byte budget drift와 stored scope/ACL/AEAD/
head drift는 거부한다. getter는 cached data이고 callback은 fresh verification 이후에만 실행된다.

원래 P98 snapshot/audit는 그대로다. 새 P99 audit는 먼저 whole parent preimage/current inverse를
증명한 다음 read-only prior parent view로 unchanged P98 audit를 실행한다. file write나 validator
조건 변경은 없다. 실제 raw current delta는 별도 current manifest 검사로 결속한다.

P09 Gate OPEN, native34 NOT_RUN/green0, actual SQL 미실행, full comment compiler/보호/실행 권위
미완료, P10 미시작을 유지한다. semantic/display/caret acceptance로 migration하면 안 된다.
