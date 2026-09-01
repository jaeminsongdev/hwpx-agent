# 제품 완료 기준

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## Alpha

- HWPX package reader/preserving writer가 100개 fixture를 손상 없이 round-trip.
- 일반 텍스트, 글자/문단 스타일, 사용자 정의 용지, 구역, 기본 표, native 수식 지원.
- operation dry-run과 semantic diff 제공.

## Beta

- 표 전체, 그림/도형/차트, 필드·각주/미주·참조, 템플릿 surgical edit 지원.
- Windows automation worker에서 지정 한/글 빌드 open/save/render/export 가능.
- Web ChatGPT와 Codex remote에서 create/edit/validate/resume 성공.

## GA

1. 대상 한/글 빌드마다 capability registry completeness 100%.
2. 핵심 capability conformance pass 100%, 비핵심 생성/수정 capability ≥ 98%.
3. native equation Tier A 100%, Tier B ≥ 99%, unsupported syntax silent fallback 0.
4. table/page/layout golden suite에서 semantic mismatch 0, 허용된 visual tolerance 초과 0.
5. untouched HWPX parts 보존 정책 위반 0.
6. 암호·서명·배포용·스크립트·OLE security negative test 통과.
7. duplicate revision, stale write, partial commit 0.
8. Windows worker hang 자동 회수, tenant temp cleanup, secret redaction 검증.
9. OpenAI plugin manifest, MCP schemas/annotations, HTTPS endpoint, auth, UI CSP, submission 요구 충족.
10. 상업 오토메이션 라이선스 및 운영 권한 문서화 완료.

## “검증됨” 표시 조건

`verified`는 다음 중 실제 수행된 evidence만 기록한다: package schema, semantic reopen, DirectHWPX round-trip, Hancom open, Hancom save/reopen, PDF/image render, visual diff, manual equation edit smoke. 미수행 항목은 `unverified`다.
