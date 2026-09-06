# P05-08 Header/Footer/Page Number Policy

## 상태와 범위

- Contract: `hwpx-agent.header-footer/1`
- 구현 범위: 현재 PC의 정품 한글 2020 exact build `11.0.0.9136` x86 및 HWPX 2011 namespace
- 구현 위치: `crates/hwpx-package/src/header_footer.rs`
- 현재 증거: Rust semantic/readback/negative/corpus test 완료
- 한글 2020 실제 open-save-reopen 및 odd/even/first-page render: `unverified`
- 한글 2022/2024: 해당 버전 PC에서 별도 target profile로 검증하기 전까지 `unverified`

## 근거 잠금

기계 판독 근거는 [OWPML source records](../p02/evidence/owpml/owpml.records.v1.json)의 다음 record에 고정한다.

| 의미 | SourceRecord |
|---|---|
| `header`, `footer` controls | `xsd:000414`, `xsd:000415` |
| `pageNumCtrl`, `pageNum` | `xsd:000420`, `xsd:000429`–`000432` |
| section start/restart | `xsd:000528`–`000533` |
| first-page visibility | `xsd:000538`–`000544` |
| section master-page link/count | `xsd:000576`, `xsd:000594` |
| `HeaderFooterType` | `xsd:001001`–`001004` |
| `MasterPageType` | `xsd:001103`–`001110` |
| paragraph `PType.id` | `xsd:000393`, `xsd:000520` |

로컬 공식 OWPML 모델은 commit `1453388472c703a4b299a0834f425cdac16644b9`에서 다음 선언을 교차 확인했다.

- `HeaderFooterType`: `id`, `applyPageType`, `subList`
- `pageNumCtrl`: `pageStartsOn = BOTH | EVEN | ODD`
- `pageNum`: 공식 11개 위치, `formatType`, `sideChar`
- `startNum`: 쪽·그림·표·수식 시작 번호와 시작 면
- `MasterPageType`: `BOTH | EVEN | ODD | LAST_PAGE | OPTIONAL_PAGE`
- `PType`: paragraph `id` is represented by the official model as `UINT`

## 공개 의미 계약

### 머리말과 꼬리말

- `HeaderFooterKind`는 `header`와 `footer`를 타입으로 분리한다.
- `PageVariant`는 `BOTH`, `EVEN`, `ODD`만 허용한다.
- 한 section에서 `(kind, variant)` 조합은 최대 하나이며 중복 시 첫 항목을 선택하지 않고 실패한다.
- definition 숫자 ID도 section 안에서 유일해야 한다.
- `subList`는 방향, 줄 나눔, 세로 정렬, 연결 목록, text box 크기, 참조 플래그를 보존한다.
- paragraph/run/text는 typed model로 내리고 raw XML을 public API에 노출하지 않는다.
- lowerer와 reader는 머리말·꼬리말·바탕쪽 내부 `hp:p id`를 bounded decimal `u32`로
  검증한다. 비숫자 identity를 XML에 내보내지 않고 `InvalidNumber`로 실패하며, `1`과
  `01`처럼 lexical form이 달라도 같은 숫자값이면 중복 `InvalidIdentity`로 실패한다.

### 쪽 번호 필드

- 머리말/꼬리말의 자동 번호는 `PAGE`와 `TOTAL_PAGE`만 의미 필드로 승격한다.
- 표시 값, 번호 모양, 사용자 문자, 접두·접미 문자, 위 첨자 여부를 보존한다.
- binary closure가 없는 `IMAGE` number format은 실패한다.
- `USER_CHAR`는 비어 있지 않은 사용자 문자가 필요하다.
- `hasNumRef`와 실제 typed page-field 존재 여부가 다르면 실패한다.

### 재시작·첫 쪽·위치

- `startNum`의 `pageStartsOn`, `page`, `pic`, `tbl`, `equation`을 함께 읽고 쓴다.
- first-page visibility는 네 개의 boolean 대신 `Show | Hide` 상태로 타입화한다.
- 쪽 번호 위치는 공식 `NONE` 및 위/아래의 left/center/right/outside/inside 위치 11개만 허용한다.
- `pageNumCtrl`과 `pageNum`이 둘 이상이면 모호성으로 실패한다.

### 바탕쪽 연결

- master-page part와 section의 `idRef`는 별도 타입으로 읽는다.
- `masterPageCnt`, section reference 수, 제공된 part 수가 모두 같아야 한다.
- ID 중복, dangling reference, 동일 적용 variant 중복은 실패한다.
- `OPTIONAL_PAGE`만 1 이상의 `pageNumber`를 가질 수 있고 다른 variant의 `pageNumber`는 0이어야 한다.
- part 순서는 section의 reference 순서를 보존한다.

## 안전성과 결정성

- 입력, XML element, definition, master page, paragraph, run, inline, text, output 크기는 모두 finite limit다.
- DTD, processing instruction, CDATA, legacy encoding은 공통 safe XML 경계에서 거부한다.
- 이 모듈은 XML comment도 의미 손실을 피하기 위해 거부한다.
- 관련 local name이 틀린 namespace나 구조 위치에 나타나면 무시하지 않고 실패한다.
- 공개 `Debug`는 본문 문자열과 문자열 ID 대신 byte 길이만 표시한다.
- deterministic lowering 후 동일 reader로 재승격하여 semantic equality를 확인한다.
- 128-case 고정 corpus digest는 `b1723d2df9135ab2a5051597cac64c50dc33b50d259c622fc975b24b89e6e4aa`다.

## 실제 검증 전 판정

이 정책과 테스트는 제품 코어의 구조·의미 계약 증거다. 숫자 paragraph ID로 교정한
fixture도 아직 실제 한글 2020 `Open` PASS를 만들지 못했으므로, 이 수정만으로 호환성을
주장하지 않는다. P05-08 hard gate는 target fixture를 한글 2020에서
open-save-reopen/render하고 제품 reader로 재검증할 때까지 열어 둔다.
