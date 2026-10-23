# P09 폰트 헤더 자원과 본문 편집 목록

`hwpx-agent.source-font-edit-inventory/v1`은 폰트 후보를 만든 실제 원본 편집 목록이다.
헤더 자원 효과와 본문 최종 splice를 구분하며 원본/출력·기존 영수증·compiled edit 지문에 결속한다.
원 IR 대상이나 CompiledOperationPlan, 접근·실행·commit 권한을 대신하지 않는다.

## 편집 종류와 실제 원본 위치

모든 SourceFontEdit는 source_part_path, source_anchor, source_start/end, replacement_sha256,
replacement_bytes, fragments를 보관한다. byte 범위는 원 XML의 UTF8 범위이며 NFC 검색 좌표가 아니다.
kind는 다음 네 종류로 닫혀 있다.

- CharacterPropertyCount는 header charProperties의 실제 itemCnt 속성 index와 값 범위, 원/출력 정의 수다.
- AppendCharacterProperties는 header의 마지막 기존 charPr anchor와 그 outer span 끝의 길이0 삽입, 추가 수다.
- RunSubtree는 원본 run의 전체 outer span과 기존 renderer가 병합한 최종 fragment다.
- TextSubtree는 원본 t의 전체 outer span과 기존 text renderer의 최종 fragment다.

정의 수와 추가는 각각 정확히1건이며 추가 수는 receipt.cloned_character_properties와 같다.
본문 splice는1개 이상이고 명시한 run/text 축과 일치해야 한다. 원본 part/byte 시작 순서로 정렬하며
중복 anchor, 범위 겹침, 실제 patch intent 수 불일치를 거부한다. 기존 compiled_edits_sha256의
part/start/end/치환 SHA 튜플 지문과 전체 목록을 대조한다. 최대4096개·직렬화8MiB이며 상한 초과는 오류다.

## 불변 목록과 현재 전달

SourceFontReplacementCandidate.edit_inventory는 생성 시 검증한 불변 metadata를 빌려준다.
source/output package SHA, 기존 font receipt SHA, compiled edit SHA, axis와 전체 편집을 canonical hash로
결속한다. hash는 bounded streaming으로 계산한다. 목록은 fragment XML·본문·폰트 이름을 보관하지 않으며
Debug도 비노출이다. 후보와 목록은 Deserialize하거나 caller 자료로 구성할 수 없다.

저장/제품의 with_verified_edit_inventory는 원래 with_verified_bytes의 현재 write/scope/head·
ACL/격리/AEAD·원본·writer 무결성 및 consumer 직전 head 검사를 공유한다. 권한이 없거나 변경된
원본/head이면 metadata consumer도 호출하지 않는다. 원본 재수입·폰트 검색·lowering을 추가하지 않는다.

## 컴파일러 연결 경계

기존 공통 owner resolver는 실제 본문 노드만 찾으므로 header anchor에는 본문 소유자가 없다.
이 목록은 헤더를 첫 문단이나 가상 노드로 바꾸지 않는다. 후속 [폰트 공통 계획](p09-compiled-font-resources-v1.md)은
두 헤더 효과를 필수 잠금 자원 인자로 보존하고 실제 본문 소유자에 결속한다. 공통 준비와 compiler는
연결했지만 실제 실행 route는 여전히 미완료다.
빈 계획이나 헤더 편집을 누락한 목록으로 자격을 부여하지 않는다.

## 검증 범위

실제 원본 anchor/속성/삽입 위치와 출력의 모든 치환 SHA·크기·편집 밖 바이트를 독립 대조했다.
양 축·부분 선택/NFC 한글 기여자·엔티티/다중 byte·공유/별개 원형·전체 원 정의/폰트 catalog 보존,
core/borrowed/owned/제품 동일성과 현재 권한·격리/AEAD·최종 consumer head 경합을 확인했다.
319 원본9pass와 helper의 E0624 실패를 보존했다. 공개 원본 byte reader로 helper만 고친320은
신규12+영향 제품24=36pass·745fresh/final745다. 원본9개를 반복하지 않은 고유45개이며 단일45개 실행은 아니다.
기존 무관 원본11·바이너리24·공식249는 반복하지 않았다. production은319와 동일하다.

전체 옵션·풍부한 review/field/protection·실제 유효 서식/fallback·실행/저장/게시·Native는 남는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작을 유지한다.
