# 현재 8종 렌더 보존과 내용 참조 제약 — 637~638

## 렌더 보존은 확인, 전체 상호참조 정답은 아님

[637 render003](evidence/p09-361-prepared-bookmark637-render003.v1.json)은 현재 캡처8종의 최초/독립 재열기 렌더를 **같은 매체 안에서만** 비교했다. PDF2종은 내장 글꼴·정적 Link 속성/URI 해시·문자 해시·쪽 geometry와96/192dpi 전체 페이지 픽셀을 비교했다. BMP6종은 Native CreatePageImage의96dpi RGB24 전체 페이지와 trace의 페이지 수/순서/크기/해시를 비교했다. 모든8쌍의 해당 픽셀은 정확히 같고 빈 페이지가 아니다. mask/crop/resize/tolerance는 사용하지 않았다.

PDF와 Native BMP를 서로 같다고 판정하지 않았으며, 원본 입력 전 렌더나 별도 SDK 삽입 렌더와의 동등성도 주장하지 않는다. 기존 Native010에는 이 비교에 쓸 렌더 파일이 없으므로 635의 필드 oracle을 렌더 oracle로 확대하지 않는다. 링크 속성 비교는 PDF 안의 정적 데이터 보존이지 실제 한글 내부 탐색 실행이 아니다.

| 항목 | 결과 |
| --- | --- |
| 같은 매체의 최초/재열기 보존 | 8/8쌍, 해당 픽셀 차이0 |
| BMP 페이지 수/픽셀 geometry | 6종 각각1쪽,794×1122,96dpi RGB24 |
| PDF 렌더 | 2종 각각1쪽,96/192dpi, 총8개 PNG |
| 새 comparator 제어 | 8개 통과 후 보존 + trace형태2개 신규 통과 |
| render003 입력 fresh/final | 41/41 |
| Poppler 실행 파일/DLL fresh/final | 122/122 |
| render003 시간/CPU 최고/가용 RAM 최저 | 92.656초 /13.00% /51.1365% |
| 새 Native/COM/접근 허용 | 0 |
| 보호 중단 | 0 |

render003은16,619bytes / SHA256 `80876d96f410d252977e4035a856f10c8fa1b47ca7c7f55bc605d8372a68e4a6`다. 완료된 PDF8개 render job과8개 제어 시험은 재실행하지 않았다. 부분 실패002의 정확한 source/renderer/입력/PNG와 종료된 job 증거를 재결속했고, 바뀌지 않은 함수 AST를 확인한 다음 새6종 BMP만 비교했다. render002 전체 실패는 그대로 보존한다.

검사기 자체의 render001은 PDF indirect annotation 배열을 먼저 resolve하지 않아 파싱 단계에서 실패했다. render002는 새8제어/PDF2쌍을 완료한 뒤, path가 없는 Native trace pin과 path를 포함한 입력 pin의 전체 dict를 같다고 요구해 실패했다. 두 실패 영수증과 당시 source archive를 보존했다. render003은 크기/SHA의 정확한 trace shape를2개 신규 제어로 확인했고, 이미 끝난 PDF와8제어를 재실행하지 않았다. 이들 실패는 Native 실패나 문서 손상으로 분류하지 않는다.

## 시각 검토와 미리보기 정정

[638 review001](evidence/p09-361-prepared-bookmark638-review001.v1.json)은 BMP12개를 비공개 PNG로 변환하고 역디코딩해 전체 RGB SHA/geometry가 원본과 같은지 확인했다. 기존 PDF192dpi PNG4개는 그대로 재사용했다. 입력31fresh/final31·Python/Pillow/pypdf 파일6/6·cleanup=true,49.500초·CPU 최고6.20%·가용 RAM 최저51.0630%다. 새 PDF 렌더나 기존 제어 시험 재실행은 없다.

[별도 시각 검토 기록](evidence/p09-361-prepared-bookmark638-visual-review.v1.json)은 위 프로그램 실행 뒤 assistant가 재열기8쪽의 전체 PNG를 읽은 관측이다. 같은 RGB 그룹은1/2,3/4,5/6,7/8의4그룹이다. 본문 영역과 기존 링크/문자 줄이 남아 있고 관측된 잘림/겹침은 없었다. 프로그램이 이미지를 보았다고 주장하지 않는다.

초기 BMP 미리보기 하나가 하얗게 보였던 것은 문서 손실의 증거가 아니다. 원본 전체 RGB는 최초/재열기에서 같고 nonwhite bbox도 남아 있으며, 손실 없는 PNG에서 내용을 확인했다. 미리보기의 표시만으로 빈 페이지라고 판단한 초기 추측을 철회한다. 미리보기 표시가 달랐던 내부 원인까지 특정한 것은 아니다.

## 새로 발견한 의미 제약: 보통 책갈피의 content는 양성 사례가 아니다

시각 검토에서 content 두 사례5/6은 `?`를 표시했다. 633의 initial/saved/reopened6개 필드 해시도 모두 단일 `?`와 일치한다. 634의 기존 Native 삽입 oracle과 같다는 사실은 이 잘못된 조합을 정상 내용 표시로 승격하지 못한다. 635/636은 실제 값 읽기/결속·보존 증거로 유지하되 content의 의미 정답이나 전체 F11 PASS가 아니다.

[한글2020 공식 책갈피 참조 도움말](https://help.hancom.com/hoffice110/ko-KR/Hwp/insert/cross_reference/cross_reference%28bookmark%29.htm)은 책갈피 내용 표시를 **블록 책갈피**에서 제공하며, 보통 책갈피를 고르면 GUI가 책갈피 이름 표시로 바뀐다고 설명한다. 현재 원본과 source-bound 모델은 point/보통 책갈피이고 블록 범위를 자격 검증한 대상이 아니다. raw SDK discovery의 content 명령을 그대로 시험한 두 사례를 block-content 양성 증거로 사용하면 안 된다. 하이퍼링크 옵션이 외관을 같게 둘 수 있다는 공식 설명도 있으며, 외관이 같다는 이유로 탐색 기능의 성공/실패를 판정하지 않는다.

따라서 다음 구현 우선순위는 제품 경로의 대상 종류/범위와 표시 옵션 admission이다. 보통 책갈피에 content를 요청한 경우 요청 의도를 몰래 바꾸지 않고 명확히 거부/진단해야 하며, 실제 블록 책갈피 내용에 대한2개 양성 사례는 별도로 구현·검증해야 한다. SDK의 inert discovery와 소비된8종 캡처는 역사 근거로 남기고 바꾸거나 다시 실행하지 않는다. 정확한 블록 HWPX 원본/범위 근거가 없으면 지원을 선언하지 않는다.

## 남은 P09 경계

현재8종의 **렌더 보존** 부분 작업은 확인했다. 그러나 올바른 block-content 대상/표시 조합, 대상 이동·이름 변경·없음/중복/깨짐과 다른 필수 대상 family, 실제 내부 hyperlink 탐색, 필요한 현재 권한/head/선택 backend/새 출력의 로컬 제품 경계는 여전히 남는다. REF-036 독립 refresh나 범용 oracle/운영 서비스 전체를 P09에 합치지 않는다.

P09/A12/A13 OPEN·미마감31묶음/65기능·전체 P09~P20 목표 ACTIVE를 유지한다. 지금 새 사용자 명령이나 접근 허용은 필요 없다. 새 P10은 시작하지 않았다.
