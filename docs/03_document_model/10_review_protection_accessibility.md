# 검토·보호·접근성 모델

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 변경 추적

`ChangeSpan`은 insertion/deletion/format/property change, author, timestamp, change id, parent relation을 갖는다. accept/reject operation은 change id와 expected state를 요구한다. 전체 accept/reject는 destructive confirmation 대상이다.

## 문서 비교·이력

문서 비교는 source A/B를 immutable로 유지하고 comparison artifact와 semantic diff를 별도로 저장한다. 한/글의 native history가 있으면 preserve/read-only로 가져오며, 제품의 revision DAG와 동일시하지 않는다.

## 보호

- open password/encryption state.
- distribution-document state.
- edit restriction / selection protection / object protection.
- personal-information protection spans.
- signature/certificate state.

비밀번호는 operation body가 아닌 secret channel로 전달하고 저장하지 않는다. 보호 해제는 올바른 credential과 권한이 있는 경우에만 수행한다.

## 서명

서명된 문서는 수정 시 서명이 무효화될 수 있다. planner는 signature state를 검사하고 mutation 전에 `SIGNATURE_WILL_INVALIDATE`를 반환한다. 서명 생성·위조는 범위 밖이며 승인된 external signing service만 연동 가능하다.

## 접근성

- document title, author, language.
- heading/outline semantics.
- image/object alt text.
- table header designation and logical reading order.
- hyperlink labels.
- color/contrast warnings.
- tagged PDF 가능 여부와 실제 export evidence.
- DAISY/Braille export는 external/automation capability로 분리.
