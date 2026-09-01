# Windows 한/글 Worker 운영

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## topology

- 사용자 desktop이 아닌 전용 licensed worker VM/pool.
- worker image마다 exact Hancom build, patch, locale, fonts, printer/export driver.
- interactive desktop/session이 필요한 automation 제약을 image 검증에 포함.
- job별 새 프로세스 또는 bounded reuse 후 recycle.

## lifecycle

1. clean VM/session lease.
2. tenant temp root 생성.
3. source artifact staging/checksum.
4. HwpObject/register security module.
5. document open and unexpected dialog detection.
6. allowlisted operations.
7. save to new path.
8. readback/render/evidence.
9. process close, recovery files cleanup.
10. session health check/recycle.

## watchdog

CPU/memory/wall time, window/modal, message queue, process descendants를 감시한다. dialog text는 민감정보 redaction 후 분류한다. known safe dialog만 policy에 따라 자동 응답하며 unknown은 job quarantine 후 worker 폐기.

## capacity

작업 유형별 service time을 측정해 pool을 분리한다: open/save, render, export, heavy chart/OLE-preserve. 한 프로세스에 여러 tenant 문서를 동시에 열지 않는다.

## patching

Hancom patch는 새 image/profile로 추가하고 drift suite 후 승격한다. 기존 production image를 in-place patch하지 않는다.
