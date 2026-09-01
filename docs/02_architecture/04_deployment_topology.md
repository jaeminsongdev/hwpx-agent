# 배포 토폴로지

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## Production 권장

- Edge/API gateway: HTTPS, OAuth 2.1/OIDC, rate limit, request size limit.
- Rust MCP/control service: stateless replicas.
- PostgreSQL: project/revision/job/capability metadata.
- S3-compatible storage: source/result/render/evidence artifacts.
- Queue: durable job queue; correctness는 in-memory queue에 의존하지 않는다.
- Direct HWPX workers: Linux/Rust autoscaling.
- Windows Hancom workers: 고정 이미지, 제한된 동시성, interactive desktop/session 격리.
- Render/oracle workers: target build별 pool, 폰트/프린터 profile 고정.
- Optional WebHWP adapter: 별도 tenant connector.

## Windows worker lifecycle

1. clean image에서 시작.
2. 한/글 build, patch level, locale, fonts, printer driver, automation module checksum을 report.
3. tenant-scoped encrypted temp directory 생성.
4. source artifact를 checksum 검증 후 복사.
5. 한/글 process 시작, modal watchdog 연결.
6. operation 실행, 중간 save 금지 또는 temp revision으로 제한.
7. save/reopen/validate.
8. output 업로드 후 local secure delete.
9. 작업 수·메모리·오류 임계치에 따라 process 또는 VM recycle.

## 개인/로컬 배포

Codex local companion은 사용자의 Windows PC와 설치된 한/글에 연결할 수 있다. 이 경로는 remote service와 동일 OperationPlan을 사용하지만 파일 접근 권한·확인 대화·output path를 로컬 정책으로 통제한다.
