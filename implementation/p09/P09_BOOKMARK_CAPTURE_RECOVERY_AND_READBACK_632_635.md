# P09 632~635 — 완료 캡처 게시 복구와 책갈피8종 저장 후 필드 읽기 검증

## 결과

631은 원본 사례3~8의 캡처와 전체 최종 감사를 완료했으나, 최종 영수증 압축에서 `XREF_LOSSLESS610_COMPRESSED_LIMIT`로 실패했다. 한글을 다시 실행하지 않고 이미 보존된 원자료를 새 명시적 형식으로 복구했다. 기존 사례1·2와 합쳐8종 캡처를 다시 결속했고, **현재 책갈피4표시×hyperlink2종의 저장 후 필드 값/매개변수 및 독립 재열기 보존을 기존 Native 삽입 oracle과 대조**했다.

이는 모든 REF-035 대상의 의미/DocumentGraph/이동/이름 변경/렌더나 F11/P09 전체 완료가 아니다. 31개 마감 묶음은 그대로 UNCLOSED이고 P09/A12/A13 OPEN, 공식249의158수용/91대기/next165, P10 새 구현 보류를 유지한다. 이 결과 인계 당시 목표 API는 PAUSED였으나, 이후 사용자의 커밋·캐시 정리 후 재개 지시 뒤 API에서 ACTIVE를 확인했다. [캐시 정리 기록](../maintenance/CACHE_CLEANUP_2026-10-23.md)을 보존하며 제품 대상/DocumentGraph 검증을 이어간다.

## 632: 한글 재실행 없는 게시 복구

- 원자료: `evidence/private/p09-361-prepared-bookmark631-native001-forensic/manifest.v1.json`과14개 조각. 875,415bytes / SHA256 `add83a105a27be7b738a814dd2cace669de4b70eecaffa8765575ead9c57387e`.
- 원자료에 `CAPTURED631_REMAINING_SIX_AND_RETAINED_TWO_SEMANTICS_UNQUALIFIED`, cleanup=true, 6개 사례별4-reader 경계, qualification/capture worker cleanup=true, 최종298fresh/final298과 section completed가 남아 있었다. 원 실행769.094초의 결과다.
- 기존 zlib 게시 오류를 Native 없이 재현했다. 소비631 코드/claim/원자료/실패를 변경하지 않았고, 원631 최종 경로에 성공 영수증을 만들어 과거 게시 실패를 지우지 않았다.
- 기존 XZ 모듈을 재사용하는 **새 profile** `hwpx-agent.prepared631-lossless-xz-publication-recovery/v1`을 만들었다. 원4MiB/100000-node/64-depth/180000-compressed-byte/256KiB 게시 상한은 유지한다. 기존610 decoder를 몰래 교체하지 않았으며 새 reader를 명시적으로 사용한다.
- [복구된 자기완결 영수증](evidence/p09-361-prepared-bookmark631-recovered632.v1.json)은83,547bytes / SHA256 `3488031c67cccc998e621c001c3ec1afc0de5b02609e0137a65fb5a324f00aed`다. 파일 자체만으로 원875,415bytes를 byte-exact 복원하며 forensic 포인터만 저장한 것이 아니다.
- [독립 복구 감사](evidence/p09-361-prepared-bookmark632-recovery001.v1.json): 오류/크기/손상/이전 decoder/guard/경로 주입 등12조건, 새6+보존2사례의48파일 및 정확한 producer/정리 증거 결속, 354fresh/final354·cleanup=true. 100.860초·CPU 최고41.99%·가용 RAM 최저35.5092%다.

새 Native/COM/문서 열기·쓰기·refresh/접근 허용·사용자 명령 재실행은0회다. 원630 전체 실패/cleanup=false도 그대로다. 메타데이터 복구를 원631 dispatcher 게시 성공이나 제품 Gate PASS로 부르지 않는다.

## 633~635: 실제 저장/재열기 필드 결과

1. [633 관측](evidence/p09-361-prepared-bookmark633-semantic-triage001.v1.json)은 원본·후보8·Native initial/saved/reopened24개의 fieldBegin/fieldEnd 범위를 읽었다. 원 임시 표시32자는 저장 후 계산된 값으로 바뀌고 dirty가1→0으로 바뀌었다. 모든 원문은 노출하지 않고 SHA/길이/상태만 기록했다. 38fresh/final38·cleanup=true.
2. [634 oracle 대조](evidence/p09-361-prepared-bookmark634-oracle-triage001.v1.json)는 같은 source SHA/책갈피/표시/hyperlink 조합을 가진 기존010 **Native가 직접 삽입한** saved/reopened16개와 비교했다. 8종 모두 표시 값·Command·매개변수 전체와 저장/재열기 보존이 일치했다. 57fresh/final57·cleanup=true. 기존010을 다시 실행하지 않았다.
3. [635 제한된 field-readback 자격](evidence/p09-361-prepared-bookmark635-field-readback001.v1.json)은 변경 없는 읽기 함수의12조건(정확한 필드 범위/외부 문단 제외/분할 run/잘못된 end/미종결/구조화 display/중복 인수/원문 비노출/namespace/빈 값/매개변수와 표시 분리/dirty 관측)을 실행했다. 현재24개 문서의 읽기 및 기존16개 oracle의 모든 입력 byte를 다시 결속했다. **8종 저장 후 필드 읽기 profile만** qualified다. 60fresh/final60·cleanup=true·9.047초·CPU 최고32.62%·가용 RAM 최저36.2638%다.

| 표시4종 | hyperlink | 실제 저장 후 결과 | 독립 재열기·기존 Native oracle |
| --- | --- | --- | --- |
| page | false/true | dirty0·표시1자 | 값/Command/전체 인수 일치 |
| bookmark_name | false/true | dirty0·표시29자 | 값/Command/전체 인수 일치 |
| content | false/true | dirty0·표시1자 | 값/Command/전체 인수 일치 |
| relative_position | false/true | dirty0·표시2자 | 값/Command/전체 인수 일치 |

저장 전 화면을 직접 관측했다고 주장하지 않는다. dirty0만으로 계산 정답을 판정한 것이 아니라 독립적인 기존 Native 결과와 실제 값을 대조했다. 그래도 oracle 자체를 모든 문서/대상/한글 버전에 일반화하지 않는다. Python의 제한된 XML 관측은 전체 제품 DocumentGraph 재구성 검증을 대신하지 않는다.

## 현재 F11에 남은 직접 작업

1. 현재24개 저장본의 source-bound 제품 대상/Field/캐시와 의미 그래프 읽기·그래프 JSON 재열기는 [636](P09_PREPARED_BOOKMARK_PRODUCT_GRAPH_636.md)에서 확인했다. 새 HWPX writer/Native 재평가나 전체 F11까지 닫힌 것은 아니다.
2. 캡처된 PDF2종/BMP6종의 페이지/글자·geometry·의도하지 않은 변경을 실제로 비교한다. 다른 매체를 무조건 동등하다고 하지 않는다.
3. 대상 이동·이름 변경·대상 없음/중복/깨짐과 보존, 다른 P09 필수 target family의 실제 ID/순서/인수 근거를 닫는다.
4. 현재 원본/권한/head/허용 backend/지속 가능한 새 출력의 로컬 제품 경계를 마감한다. P11의 독립 refresh나 전체 운영 SQL/key custody를 P09에 합치지 않는다.

실제 통과 근거가 유지된 시험은 반복하지 않는다. 필요한 신규/직접 영향 검증만 직렬·1코어·낮은 우선순위·기존CPU/RAM/commit95% 보호 아래 실행한다. 현재 새 사용자 실행 명령이나 접근 허용은 필요 없다.
