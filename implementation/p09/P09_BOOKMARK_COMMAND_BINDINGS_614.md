# P09 책갈피 CROSSREF Command 제품 경로 614

상태: **읽기 전용 source-local 명령 결속 구현·검증 완료 / P09 Gate OPEN / 목표 ACTIVE**.

## 제품 변경

- `crates/hwpx-package/src/document_import/fields/bookmark_crossref.rs`: 원래 package/form/field/전체 CROSSREF coverage를 유지하고 정확한 HP `stringParam name="Command"` 하나만 해석한다. 중복·다른 key/type/namespace·nested/comment·비정규 SDK 명령·외부 경로·지원되지 않은 대상 종류는 거부한다.
- 기존 SDK builder로 명령을 역구성해 동일성을 확인한다. 책갈피 표시 Page/BookmarkName/Content/RelativePosition과 hyperlink bit를 typed 값으로 반환한다. 이름/명령 원문은 결과·Debug에 노출하지 않고 해시를 사용한다.
- 같은 immutable package의 target index를 한 번 만들어 실제 책갈피를 `Bound / Missing / Ambiguous`로 구분한다. source-local ID를 서로 다른 저장본 사이에서 동일 ID라고 간주하지 않으며 Native window/flow/page 좌표나 링크 승인을 만들어내지 않는다.
- `crates/product-cli/src/reference_validation_product/source_crossref/bookmark_bindings.rs`: 공개 Rust 제품 API `ReferenceValidationProductOperation::read_source_bookmark_crossrefs`를 추가했다. 입력은 실제 package bytes/document ID/SHA/한도이며 caller가 name/command/target-map/graph/허가를 공급하는 경로는 없다.
- 기존 부모 파일2개는 module 선언 추가만 했고 전체 기존 본문 inverse를 검증했다. 기존 observation/semantics/Source v13 동작·Native probe EXE·010 실행기/claim/spool/실물 원본은 변경하거나 재실행하지 않았다.

## 근거와 검증 범위

| 근거 | 확인 범위 |
| --- | --- |
| [613 준비](evidence/p09-361-bookmark-binding-corpus613-preparation.v1.json) | 기존611/612로 고정한 source1+실물24 및40산출물 계보;47fresh/final47. Native permit 아님 |
| [고정 corpus](evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json) | 9284B/SHA9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f; 원문 명령 없이 case/표시/hyperlink/command SHA/파일 pin만 포함 |
| [614 audit002](evidence/p09-361-bookmark-command-product614-audit002.v1.json) | 컴파일 성공·새 시험10 중9 통과(실물24 포함),1은 input_bytes>output_bytes인 시험 설정으로 InvalidLimit 실패. 전체 FAILED 원본 유지·cleanup true |
| [614 audit003](evidence/p09-361-bookmark-command-product614-audit003.v1.json) | 실패 fixture의 input/output 예산을 유효하게 고치고 Limit 거부까지 확인. 변경된 실패 시험1만 실행. 나머지9의 전체 body/compiled input 동일성을 fresh 대조해 유지. 일반 실행 빌드+고정 실물24도 별도 실행.889fresh/final889·모든3step exit0/cleanup true·진단0 |

최종 새 바이너리 `target/debug/examples/p09_bookmark_command_bindings613.exe`는4943360B/SHA bcd6119a046c3766c9c8d3153c76eed658659fd840f185f585c3f4e357f7481b다. 원010 readonly probe5152256B/SHA379d55499a0e4acefb323fc0904e03809f099416239c2c6757fe2b5d2a76a46c는 byte-exact 유지했다. 새 source-local 결속 결과의 Native/complete-reference qualification은 모두 false다.

## 자원·검증기 최적화

첫614 시도는 시험 본체 시작 관측 없이 compile30.3초 지점의 Job private6.335%/시스템CPU6.82%가 보였으나, 이후 tuple 자료형을610 strict JSON codec에 직접 전달하면서 결과 게시가 실패했다. 따라서 최초 Cargo/Guard 종료 원인은 확정 복원하지 않는다. [615 부분 관측](evidence/p09-361-bookmark-binding614-publication-incident615.v1.json)은 원래 유실 row를 복원한 영수증이 아니다.

동일 시험/입력/보호를 유지하고 hwpx-agent-cli 패키지만 코드 생성 단위를16→2로 낮췄다. Cargo jobs1, debug assertions/overflow checks, RAM/commit/Job/CPU 한도는 그대로다. [Rust 공식 설명](https://rustc-dev-guide.rust-lang.org/parallel-rustc.html)의 codegen 병렬 작업 구분을 참고한 후보를 실제 측정했으며, audit002의 compile+10시험은17초, 최고 Job private1319.06MiB/4.140%였다. 원래 실패의 정확한 terminal cause나 일반적인 성능 개선을 단정하지 않는다. 전역 Cargo/OS/Defender 설정은 바꾸지 않았다.

검증기 출력은 tuple을 JSON array로 표현하는 원래 canonical bytes가 변하지 않음을 확인한 뒤 JSON-native 값으로 정규화한다. `metadata_forensic_retention615.py`의4모형이 이 경계를 확인했고 audit003에서는 소스 동일성으로 유지했다. optional encoding 전에4MiB 이하 row를64KiB씩 immutable private spool에 보존·재읽기·SHA 확인한다. audit003 원문264855B/SHA f2c00e5baef91cad7f6b6a5171290eefae6cd79616da58a57bb061a543e7eed3, 파생 self-contained packet95776B/SHA b07d3018fe5d921cfd85e3627c2c5857f879d6e446821433edf078cd1067beee이며 원256KiB writer 한도는 그대로다.

613 준비 자체는47/47·cleanup true였지만 새 상태명 PASS613_와 반환 조건 PASS_의 prefix 차이로 잘못된 CLI 종료가 있었음을 보존한다. 당시 소스를 archive에 그대로 남긴 뒤 반환 조건을 고쳤다. 이미 생성된 corpus를 덮거나 반복 생성하지 않았고614는 CLI exit가 아니라 고정 SHA와 실제 닫힌 데이터 경계를 확인했다.

최종144.891초, 시스템CPU 관측최고19.34%, 가용RAM 최저51.764%. Native/Hancom/COM·기존249 시험·010 재실행·보안 설정 변경은 없다.

## 남은 작업

1. 이 API를 기존 `ImportedFieldMeaning / SourceFieldMeaningIndex`와 공개 Source assessment 흐름에 통합한다. 현재 기존 필드 의미/Source API v13은 여전히 불완전하며 이 API 추가만으로 미해결4개가 닫힌 것은 아니다.
2. 지원하지 않은 객체·각주/미주 CROSSREF 및 실제 대상 해석/표시·재평가/Native 의미 자격을 검증한다. 저장된 Command 해석은 Native 대상 해석·cached display/레이아웃 정답·실행 허가가 아니다.
3. 원래249 큐 잔여91/next165, 나머지 P09 운영 경로·통합 감사·Gate를 실제 근거로 마감한다. 기존158 수용 결과와 실패/허가 경계를 보존하며 P10은 시작하지 않는다.
