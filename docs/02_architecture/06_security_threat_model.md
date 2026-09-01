# 보안 위협 모델

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 신뢰 경계

- 사용자/LLM 입력
- public MCP gateway
- artifact parser
- direct worker
- Windows automation worker
- optional external services
- object storage and metadata DB
- widget/local companion

## 주요 위협과 통제

| 위협 | 통제 |
|---|---|
| ZIP bomb/path traversal | entry count/size/ratio 제한, canonical path 검사, symlink 금지 |
| XML entity expansion/XXE | DTD/entity/network resolution 비활성, bounded parser |
| 문서 스크립트/매크로 | 기본 실행 금지, preserve-only, 별도 trusted policy |
| OLE exploit | 실행/활성화 금지, binary scan, isolated worker |
| 외부 링크 추적/SSRF | network 기본 차단, allowlist, link metadata only |
| 암호/보호 우회 | 비밀번호 명시 입력과 권한 검증, bypass 기능 없음 |
| 임의 automation action injection | capability registry의 allowlisted binding만 실행 |
| modal/hang | watchdog, timeout, process kill, VM recycle |
| cross-tenant leak | tenant-scoped paths/keys, worker cleanup, audit |
| prompt injection in document | 문서 텍스트는 untrusted data로 표기, tool policy 변경 금지 |
| font/license leak | font file 업로드/배포 금지, worker inventory만 사용 |
| signed document mutation | signature state 검사, 명시 동의 없이는 실패 |

## 권한

`document.read`, `document.write`, `document.export`, `automation.use`, `external_service.use`, `security.modify`, `review.accept`, `macro.execute`, `admin.capability.manage`를 분리한다.

## 안전 기본값

- 오토메이션 action은 registry key로만 호출.
- `macro.execute`와 OLE activation은 기본 deny.
- 외부 네트워크 deny.
- 인쇄는 가상 PDF printer 또는 승인된 printer profile만.
- 민감 로그는 parameter value가 아니라 schema field와 hash만 기록.
