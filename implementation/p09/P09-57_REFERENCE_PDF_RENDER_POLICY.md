# P09-57 접근 허용 없는 전체 페이지 raster 검사

허용 범위: 고정 원본 PDF를 읽고 SOURCE 회귀 검사 및 실제 P56 전체17 결과의
저장·재열기 raster 진단을 수행한다. CLI에는 native 실행 옵션이 없다.
한글/COM 생성, 보안 설정 변경, 접근 허용 자동화, 이전 native 원본 변경은 금지한다.

## 비교 계약

- 실제 입력 SHA-256/크기를 고정하고 원본 그대로 scratch snapshot을 만든다.
  PDF 재저장/재작성/메타데이터 정규화를 하지 않는다.
- 모든 대응 페이지를 96/192 DPI 두 profile로 비교한다. 숫자 page index를 쓰며
  누락/추가 페이지도 목록에 남긴다. PDF MediaBox 전체를 렌더링한다.
  CropBox/rotation/UserUnit도 비교하며 영역 mask, 허용 오차, resize, 색 정규화가 없다.
- RGB SHA, 실제 변경 pixel 수/색 차이 합/bbox, nonwhite bbox와 페이지 geometry를
  기록한다. blank/blank pixel equality는 문서 의미의 일치를 증명하지 않는다.
- 최대 PDF32MiB,32페이지, 페이지별8M pixel, 전체128M pixel이다. geometry/DPI 예산을
  native renderer 호출 전에 검사한다. 출력 geometry와 RGB mode도 확인한다.
- embedded font만 허용한다. encryption, UserUnit!=1, annotation/AcroForm,
  pattern/graphics-state font 등 아직 독립 검증하지 않은 리소스는 거부한다.
  지원하지 않는 입력을 blank/skip/PASS로 바꾸지 않는다.
- 실제 Poppler EXE와 같은 디렉터리 DLL 전부, parser entry/raster extension,
  Python/Pillow/pypdf version을 고정한다. 이것은 전체 OS/Python 환경 attestation이나
  악의적인 PDF를 위한 security sandbox가 아니다. 하위 프로세스 timeout30초는
  renderer hang 한계이며 완전한 memory sandbox가 아니다.
- linked/junction 경로를 거부한다. `tmp/pdfs/p09-57-*` exclusive 소유 scratch만
  자동 정리한다. 원본/private native 폴더나 기존 사용자 파일은 삭제하지 않는다.

## 증거 분리

P22 원본 direct/automation PDF는 과거 regression으로만 사용한다. 96 DPI 원래의
920 pixel/215567 RGB delta/bbox와 기존 saved/reopened0 pixel을 그대로 요구한다.
새192 DPI 비교도 mismatch를 유지한다. 이를 현재 exact-candidate baseline, 버그 수정,
P51/P55 runtime 수락 또는 Gate 증거로 재사용하지 않는다.

현재 consumer는 frozen P56 full17 dispatch/실제 child 종료·trace·artifact binder를
먼저 호출한다. 성공 lifecycle 및 두 claimed PDF가 없는 case는 NOT_RUN이다.
성공 사례의 PDF SHA를 actual binder 값에 묶고, 비교 뒤 전체 입력을 재결합한다.
거부/불일치/실패 case는 전체17 목록에 그대로 남긴다. 실제 dispatch가 없으면
case_count0/NOT_RUN이고 native/current capsule을 생성하지 않는다.

현재 direct baseline17개는 모두 없으며 NOT_RUN이다. 새 current exact-candidate
direct capture/admission lane 및 direct-vs-automation 수락은 이번 구현 범위에 없다.
saved/reopened stability는 direct differential이 아니다. 다음 native 실행도 반드시
전체 ready queue 정책과 사람의 허용을 따라야 한다. 17개는 P09 전체46개 coverage가
아니다. SOURCE PASS는 native/style/semantics/cleanup/rollback/제품/Gate를 닫지 않는다.

고정 선행 P56 admission:12622 bytes,
SHA256 `3869c502ed4b7e1ba08f85e181f9dada3622a72a45e63a222fe8d6a267dd0de7`.
P48-P56 전체 source/context, 기존75 native 파일, P55 계획과 candidate는 보존한다.
전체 오래된 workflow/ordinary suite 재실행이나 증거 상태 승격은 하지 않는다.
