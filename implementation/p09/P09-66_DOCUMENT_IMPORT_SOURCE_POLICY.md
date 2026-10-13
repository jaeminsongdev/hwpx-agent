# P09-66 실제 문서 importer 원본 연결 정책

- 목적: 실제 HWPX 전체에서 typed importer에 필요한 원본 위치와 보존 기반을 만든다. caller graph나 form inventory로 이를 대체하지 않는다.
- API: `hwpx_package::document_import::ImportedSourcePackage::import` / `resolve_anchor` / `verify_source`.
- 원본은 읽기만 한다. 추출·재작성·COM/UI/native dispatcher·접근 허용창·실행/publication 없음.

## 강제 계약

1. admitted whole package SHA를 ZIP admission 전에 확인한다. 문서 ID도 anchor identity에 포함한다.
2. 기존 BoundedZipReader/PackageGraph/PreservationReport/PreservingXmlDocument의 안전·무결성·미지원 계약을 유지한다. preview는 기존 Hangul2020PreviewTextV2 규칙이다.
3. 폐쇄 패키지 모든 non-directory part를 integrity-read한다. original ZIP은 binary/preview/미지원 part까지 private immutable 보존한다. 모든 admitted XML 요소에 exact subtree SHA 및 document/package/part/span-bound handle을 생성한다.
4. 실제 namespace와 parent/child/sibling order를 유지한다. anchor는 이 버전에만 유효하며 native numeric ID나 cross-revision persistent logical ID가 아니다.
5. DTD/entity/PI/CDATA/encoding 등 기존 거부를 opaque fallback으로 숨기지 않는다. unsafe XML/media mismatch/closure 실패는 전체 import를 거부한다.
6. aggregate XML elements/tokens/overlapping subtree fingerprint hashing 양을 제한한다. configured bounds는 hard default profile보다 커질 수 없다.
7. fresh verification은 whole ZIP/graph/preservation/XML을 재import하고 original bytes/topology/all anchors/receipt를 비교한다. stored digest만 비교하지 않는다.
8. Debug/error/receipt는 문서 텍스트·attribute value·private part path를 출력하지 않는다. 객체는 Deserialize/public mutation/실행 권한을 제공하지 않는다.

## 완료 경계

이것은 **whole-package source stage**다. typed DocumentGraph를 반환하지 않는다. 본문·표·도형·수식·폼·notes/references·catalog 전체 의미 변환 및 source anchor 연결, unknown exact preservation/security qualification을 구현해야 한다.

Artifact/Revision에 실제 Source/Result/IR lineage를 저장하거나 previous-result→input chain을 연결한 결과가 아니다. issuer/ExecutionManifest/idempotent publication/IR retention·GC·sync·recovery/whole qualification replay+new admission/licensed native 의미·render·differential/P09 Gate는 미완료다. P65 synthetic prior Source/scanner/caller IR/authority를 실제 계보로 승격하지 않는다.

Goal ACTIVE/P09 완료 false/P10 시작 false/current native INPUT_CHANGED_RE_ADMISSION_REQUIRED/full34 NOT_RUN/0green 유지.
