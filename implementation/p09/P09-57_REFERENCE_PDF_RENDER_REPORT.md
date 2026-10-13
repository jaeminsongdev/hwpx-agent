# P09-57 전체 페이지 PDF 화면 비교 / 현재 결과 소비

2026-10-03. 최신 사람 지시 `접근허용 띄우지 말고 딴거 해`에 따라
한글/COM/native dispatcher를 호출하지 않고 P09의 offline rendering 경로를 구현했다.
Goal ACTIVE, P09 Gate는 열려 있으며 P10은 시작하지 않는다.

## 실제 구현과 검증

`reference_pdf_render.py`는 byte snapshot으로 고정한 PDF의 모든 대응 페이지를
96/192 DPI에서 MediaBox 전체 RGB로 비교한다. 페이지 추가·누락·geometry 변경과
pixel 차이는 거부/불일치로 유지한다. mask, 허용 오차, resize, metadata 정규화가 없다.
geometry/pixel/resource 한계는 renderer 실행 전에 검사하며 parser/renderer 실패는
native 성공으로 바꾸지 않는다. 검사 과정에서 만든 exclusive scratch만 정리한다.

`reference_render_consumer.py`는 고정 P56 전체17 dispatch와 기존 actual binder를
재사용하여 child exit/trace/아티팩트 SHA에 연결한다. lifecycle 실패 또는 두 PDF
claim 부재는 NOT_RUN이다. 실제 비교 후 전체 입력을 다시 결합한다. 현재17개 direct
baseline은 없으므로 별도17행 NOT_RUN이다. 과거 PDF를 현재 candidate baseline으로
대체하지 않는다. Current 명령은 native/current receipt를 작성하지 않는 조회다.

18개 실제 Python unit test가 통과했다. malformed/magic/hash, geometry/회전/UserUnit,
encryption, allocation, embedded font/recursive resources, unsupported appearances,
RGB/mode/blank, failed/unclaimed stage, 전체17 baseline 부재, 12페이지 숫자 순서/누락,
동일 pixel에서도 geometry 차이를 숨기지 않는 component controls를 포함한다.
합성 parser/raster fixture는 private native trace/dispatch/current 증거를 만들지 않는다.
다중 페이지 자체는 합성 component 검사이며 실제 다중 페이지 native 수락이 아니다.

실제 과거 P22 PDF3개를 읽고 다음 원래의 결과를 재현했다.

| 비교 | 96 DPI | 192 DPI | 해석 |
| --- | --- | --- | --- |
| 과거 SDK direct saved vs native same-value filled | 920 changed pixels / RGB delta215567 / bbox113,132,273,145 | 2822 /930553 /227,266,546,291 | 과거 mismatch 유지, 수정 증거 아님 |
| 과거 direct saved vs reopened | 0 pixels /0 delta | 0 pixels /0 delta | 과거 pair stability, 현재 lifecycle 아님 |

PDF 원본 SHA 고정값:

- direct saved `8e8e567f0b7a47ecd91c3e3763791c1bbdd3c05f9b3f4282184415833f0f5afd`
- native filled `97a271a0c93fdae2b3753065b22fb8caabec147f09e8964d5bcfc971604eb067`
- direct reopened `0528f2a8508dc18db0dffafa45506a5057195037275b0bda30331af12cf5ff81`

192 DPI의 direct/native 전체1페이지 미리보기를 각각 시각 확인했다. direct에는
빨간 기울임, native에는 검은 일반 문자 차이가 보였다. 둘 모두 콘텐츠는 페이지
상단에 있고 나머지는 공백이다. reopened는 두 profile 모두 direct와 RGB SHA/전체
pixel이 같았다. 이 사실을 native worker repair라고 주장하지 않는다.
미리보기 및 테스트 scratch는 자기 소유 임시 폴더만 정리했다. source PDF는 재작성하지 않았다.

## 원장 / 재현

SOURCE 공개 실행 session55635와 독립 fresh 전체 검증 session94330 모두 exit0.
문서 동기화 후 별도 integrity session5178도 exit0:5개 source pin 일치,
새 native 디렉터리0/dispatch·current capsule 없음/Hwp0/소유 scratch 잔여0을 확인했다.
새6개 source·문서와 PLANS의 scoped whitespace 검사도 PASS였다.
단순 이전 준비 단계 재실행이 아니라 신규 renderer/component 테스트와 실제3 PDF
회귀를 새로 실행했다. P56의 preflight/native dispatcher 및 오래된 ordinary suite를
다시 실행하지 않았다.

SOURCE capsule:
`implementation/p09/evidence/p09-57-reference-pdf-render.source.v1.json`,
23740 bytes, SHA256 `c001c5f34fcbc4310c5d531954712ca911a471301a24d29bd35ec44f3d18335d`.
5개 새 source pin, 실제 renderer EXE+121 DLL identity, pypdf6.13.3/Pillow12.2.0와
parser entry/raster extension/Python version, 전체 P56 context, 실제18 unit/과거 PDF
회귀 결과 및 current NOT_RUN을 포함한다. 전체 OS/Python 환경 attestation은 아니다.

```powershell
python tools/p09/verify_reference_pdf_render.py --verify
python tools/p09/verify_reference_pdf_render.py --current
```

## 남은 경계

P56 실제17 native dispatch가 아직 없으므로 current0cases/NOT_RUN이다.
별도 실제 `--current` 조회 session59730도 exit0/NOT_RUN/0cases였으며17개 direct
baseline 부재를 전부 반환했다. native/current receipt를 작성하지 않았다. 현재 실행
자료가 있는 분기의 end-to-end 소비는 native batch 이후에만 검증할 수 있다.
현재 exact-candidate direct capture/admission lane도 아직 구현/실행되지 않았다.
saved/reopened raster stability만으로 direct-vs-automation differential을 닫을 수 없다.

지원하지 않는 PDF 입력의 독립 승인, 실제 다중 페이지/native semantics/style/ownership/
cleanup/rollback/package/render/direct differential, signed product 경로, 46개 reference
coverage/Gate는 별개로 남아 있다. 기존920-pixel 결함은 **미수정/현재 미검증**이다.
P48-P56 source/context/receipt/plan/candidate 및 기존75 native 파일 identity는 frozen
선행 검사에서 보존 확인했다. 새 native directory/trace/dispatch/current 증거는 없다.
한글 실행·접근 허용 유발·보안/registry 변경·commit/push는 수행하지 않았다.

다음 useful offline work는 exact-candidate direct baseline의 전체 수집 계약/보호된
capture 경로 또는 남은 실제 제품 경로 구현이다. 닫힌 P57 SOURCE를 wrapper로 다시
감싸거나 historical PDF를 current baseline으로 복사하는 것은 진행으로 취급하지 않는다.
