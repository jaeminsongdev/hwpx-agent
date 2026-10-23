# 프로젝트 캐시 정리 — 2026-10-23

## 커밋과 범위

작업 저장 커밋은 `732d5559159ad80166aa15d453d07018b454f17c`다. 현재까지의 소스·문서·공개 검증 기록5198경로를 먼저 커밋하고 삭제를 시작했다. P09 비공개 원자료722개는 Git에 추가하지 않고 로컬에 보존했다. `.gitignore`에 해당 private 경로 제외를 추가했다. 원격 push는 하지 않았다.

대상은 `D:\개발\hwpx-agent` 안의 재생성 가능한 Rust 중간 산출물, 증분 캐시, PDB/rlib/rmeta/link sidecar, Python bytecode 및 Ruff 캐시다. 공유 Cargo/Rustup/Temp·다른 프로젝트·DB·원본·검증 증거·source-archive·Git history를 지우지 않았다. 활성 Node 서버가 사용하는 node_modules/dist도 보존했다. target 전체나 workspace root를 재귀 삭제하지 않았다.

## 최종 결과

| 항목 | 결과 |
| --- | --- |
| 삭제 파일 | 299,767개 |
| 삭제 파일의 논리 크기 합계 | 481643569417bytes / 448.57GiB |
| 제거한 빈 캐시 디렉터리 | 9,346개 |
| 선택 정책에 해당하는 잔여 캐시 | 0파일 |
| 주요 생성 위치의 논리 크기 | 462.11GiB → 13.58GiB |
| 정리 직전 D 여유 / 보존 감사 시점 D 여유 | 617.68GiB → 1152.04GiB |
| 관측된 D 여유 증가 | 534.36GiB |
| 캡처 보존 | 8종48파일 byte/SHA 일치 |
| forensic 보존 | 원875415bytes와14조각 그대로 |
| 원본 문서 | source SHA 일치 |
| 보존 감사 | 65fresh/final65 |
| 새 Native·제품 시험 재실행 | 0 |

디스크 여유는 파일시스템의 지연 반영 및 다른 프로세스의 쓰기/삭제에 영향을 받는다. 따라서 관측된 여유 증가를 전부 이번 삭제의 단독 효과라고 단정하지 않는다. 삭제한 파일의 논리 합계와 실제 드라이브 여유를 구분했다.

## 삭제한 정확한 범위

- `D:\개발\hwpx-agent\target\…\debug\incremental\…`, release incremental 및 fuzz/target의 같은 위치: 허용한 Rust 캐시 확장자만 삭제.
- Cargo deps/examples의 `.pdb`, `.rlib`, `.rmeta`, `.lib`, `.exp`, `.obj`.
- 표준 Cargo profile 루트(debug/release)의 같은 sidecar43개: 총6132822016bytes.
- `D:\개발\hwpx-agent\tools\…\__pycache__\*.pyc/*.pyo`.
- `D:\개발\hwpx-agent\.ruff_cache`.
- 이미 빈 위 캐시 폴더만 rmdir로 제거. 내용이 남거나 사용 중인 폴더는 강제로 지우지 않았다.

파일은 휴지통으로 이동하지 않고 삭제했다. 재빌드/도구 실행으로 재생성할 수 있지만 과거 캐시 파일의 동일 SHA 재현을 보장하는 백업은 아니다. 다음 필요한 Rust 빌드는 느려질 수 있다. 이를 이유로 과거 통과 시험을 전부 다시 실행하거나 역사 빌드 캐시를 일괄 재생성하지 않는다.

## 보존한 항목

정리 전후 메타데이터 집계에서 Rust EXE, DLL, dep-info, build-script 산출물, fingerprint 메타데이터, pnpm 의존성은 크기 합계가 모두 동일했다. 이 분류는 캐시와 검증/런타임 자료가 섞일 수 있어 보존한 범위이며, 원본 전체를 별도로 byte 검증했다는 뜻은 아니다.

특히 아래는 삭제하지 않았다.

- `implementation/p09/evidence/private`, 전체 source-archive·실패 원본·공개 영수증.
- target 안의 원본/관측 JSON·HWPX/PDF/이미지·DB·비공개 자료·Git snapshot.
- 현재 실행 중인 web dist와 node_modules, 공용 Cargo cache·Rustup·PostgreSQL·D:/devdata의 공용 Temp/보관 자료.
- 설치 도구·Codex runtime/trust/cache·Windows/Defender/WSL 설정과 다른 앱.

## 자원 보호·중단·최적화

첫 실행은76975파일/157827408246bytes 삭제 후 시스템 CPU93.87% 표본에서 보호 중단됐다. 실패 결과와 원 실행 코드를 보존하고 동일 정책을 즉시 반복하지 않았다.

검토 결과 첫 삭제기는 파일100개당 휴식만 있어 큰 PDB에서 여러 GiB 삭제가 짧게 몰릴 수 있었다. 두 번째 실행에는 논리 삭제량1GiB/s·순간64MiB credit·최대1000파일/s와 CPU50%에서 추가 slowdown을 적용했다. CPU90% 즉시/75% 지속, RAM/commit95% 중단 조건과1코어·BelowNormal은 유지했다. 새 pacing3조건과 선택/순회/강한 중단 함수 본문3개 불변, 선택17조건을 확인했다.

두 번째 실행은 890.453초, CPU 최고46.71%, 가용 RAM 최저30.1270%, 삭제 오류/skip0·추가 보호 중단0이었다. 특정 외부 프로세스가 최초 CPU spike의 원인이라고 확정하지 않았으며 다른 프로그램을 종료하거나 보안 설정을 낮추지 않았다.

## 증거

- [정리 전 집계](cache-inventory-20261023.v1.json)
- [원 계획](cache-prune-plan-20261023.v1.json), [최초 보호 중단](cache-prune-result-20261023.v1.json)
- [최적화 후 계획](cache-prune-plan-20261023.v2.json), [완료 기록](cache-prune-result-20261023.v2.json)
- [프로필 sidecar/빈 폴더 정리](cache-prune-profile-roots-20261023.v1.json)
- [정리 후 집계](cache-inventory-after-20261023.v1.json)
- [원본/캡처/forensic 보존 감사](cache-preservation-20261023.v1.json)

목표 API의 ACTIVE를 확인했다. P09/A12/A13 OPEN 및31마감묶음/65기능은 바꾸지 않는다. 다음 작업은 현재24문서의 제품 대상/Field/DocumentGraph 결속이다.
