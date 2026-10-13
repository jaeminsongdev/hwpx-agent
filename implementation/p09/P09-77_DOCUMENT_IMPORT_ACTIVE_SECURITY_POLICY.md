# P09-77 실제 원본의 활성 콘텐츠와 native 폼 보안 바인딩

## 목적과 범위

전체 문서 제품 경로에 필요한 보안 정보 누락을 줄이는 source component다. immutable Source→body/forms→ranges→meanings→catalog만 입력으로 받는다. caller inventory, 임의 graph, 외부 URL 실행, native 실행, trust 변경, 승인·게시 권한을 받지 않는다.

기존 `ActiveContentInventory::scan`을 실제 bounded ZIP와 원본 `PackageGraph`에 그대로 적용한다. 원본 검사기의 resource/control/disposition/count/state SHA를 변경하거나 재해석하지 않는다. 실제 part·element ordinal·raw subtree fingerprint를 대조하고, 표현된 body node는 같은 source anchor로만 연결한다. opaque source도 원본 위치를 보존하며 typed 완전성을 추정하지 않는다. resource는 실제 artifact SHA와 길이까지 같아야 한다.

## 별도로 확인된 native 폼 누락

기존 P08 검사기는 `btn`, `comboBox`, `listBox`, `edit`을 관찰하지만 실제 native `checkBtn`·`radioBtn`을 inventory에 넣지 않는다. 이 누락을 검사기 전체 PASS로 숨기거나 원본 검사기·증거를 변경하지 않는다.

별도 `ImportedNativeFormSecurityBinding`은 변경하지 않은 native form reader의 5종 관찰을 사용한다. 원본 namespace/tag/node/source anchor를 대조하고 원본 command attribute의 semantic SHA를 원래 reader의 `command_sha256`과 비교한다. 원래 reader의 empty command→None 규칙을 유지한다. 값은 새 binding/receipt/debug에 넣지 않는다. 명령이 있으면 `Quarantine`, 없으면 `PreserveBlocked`다. 기존 inventory에 같은 source가 있으면 kind/node/disposition까지 일치해야 한다. inventory에서 빠질 수 있는 native tag는 확인된 check/radio 2종뿐이며 누락 수를 따로 남긴다.

## 차단과 미검증 경계

- OLE·멀티미디어·실행 파일·스크립트·폼 명령·외부 링크 6종 activation은 원래 `authorize`의 정상 등급 무조건 거부를 유지한다. `require_activation`은 실행하지 않는다.
- 기존 `SecurityState`의 protected/encrypted/signed와 원래 qualification은 바꾸지 않는다. `NotAssessedByActiveContentInventory`를 명시해 검사 결과가 native 보호·암호화·문서 서명을 확인한 것처럼 보이지 않게 한다.
- 원래 `ActiveContentSignature::Verified`는 binary magic/signature 확인이다. cryptographic document signature가 아니므로 resource metadata에 `source_active_binary_signature_check_not_document_signature`로 구분한다.
- profile/scope 각각이 단독으로도 full-document product context를 거부해야 한다. 정상 readonly 관찰은 quarantine 실행·제품 수락·issuer authority가 아니다.
- graph/source/scanner/폼 바인딩/receipt 전체를 fresh 원본에서 재구성해 비교한다. 이전 graph에 이번 추가만 제거하면 모든 원래 필드가 그대로 복원돼야 한다.

## 저장 서비스와 검증

생성 전·후, cached 검증 및 activation 거부 전 원래 authenticated service/source/catalog 검증을 재사용한다. AEAD·ACL·head·tenant/subject/project/branch/document 변경을 거부한다. 정상 READ audit 외 ingest/CAS/seal/publication은 없다. 반복 head read를 atomic lock 또는 crash-recovery 증거로 주장하지 않는다.

입력은 잠긴 historical 26개와 기존 native form source/output 10개다. 새 native 실행이 아니다. script/Web video/OLE 및 native 폼 5종 command/empty command의 파생 ZIP는 메모리에서만 생성하고 원본을 덮어쓰지 않는다. 두 current-executable process의 전체 결과 equality, source 보존, 새 테스트 및 기존 Rust 회귀·strict lint로 확인한다.

전체 importer/catalog/settings/field/reference/comment 의미, 평가·외부 승인, committed Source→Result→IR lineage, real policy/scanner/issuer/ExecutionManifest, publication/idempotency/lifecycle/concurrency/crash/recovery/load, 원래 전체 qualification 재실행/current admission은 별도 미완료다. P26 non-green/P62 UNRESOLVED/INPUT_CHANGED_RE_ADMISSION_REQUIRED/full34 NOT_RUN·0green/P09 Gate OPEN/Goal ACTIVE/no P10을 유지한다. 한글·COM·UI·native dispatcher·접근허용을 실행하지 않는다.
