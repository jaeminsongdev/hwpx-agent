# 보안·개인정보·라이선스 구현

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## trust boundaries

1. 사용자 입력 문서/자산.
2. public MCP/API.
3. control plane/database/object storage.
4. direct parser/writer sandbox.
5. licensed Windows desktop worker.
6. external providers/WebHWP/signing/translation.
7. end-user downloads.

각 경계에서 content, identity, capability, artifact checksum을 다시 검증한다.

## 문서 위협

- ZIP bomb/path collision/traversal.
- XML entity expansion, oversized tree, malformed namespace.
- external relationship, remote image/link.
- script/macro, OLE/embedded executable, active form behavior.
- password/protected/distribution document.
- digital signature invalidation.
- PII in body, metadata, revisions, comments, previews/logs.

기본 정책은 active content를 실행하지 않고 inventory/preserve/quarantine한다.

## permission model

권한은 `document.read/write`, `template.write`, `automation.execute`, `workstation.control`, `print.execute`, `external.invoke`, `security.inspect`, `security.modify`, `sign.execute`, `admin.binding` 등 capability scope로 나눈다. tenant policy와 user role 모두 통과해야 한다.

## 고위험 확인

인쇄, 이메일/업로드, 외부 번역, 보호/암호 변경, 서명, 개인정보 제거, macro/COM add-in은 dry-run 결과·대상·side effect를 사용자에게 명확히 보여 주고 짧은 수명의 confirmation token을 요구한다.

## secret 처리

password/API key/certificate는 요청 JSON이나 로그에 plaintext로 보관하지 않는다. secret manager ref로 전달하고 worker memory에서 최소 시간만 사용한다. crash dump와 screenshot 정책에서 secret/본문 노출을 제한한다.

## 라이선스 gate

- Hancom Automation 상업 이용 승인/계약 범위.
- 서버/VM 동시 실행 및 설치 수.
- WebHWP 사용/배포 권리.
- 공식 문서/PDF/XSD 내부 저장·파싱·재배포 권리.
- font 설치/embedding/export 권리.
- third-party converter/provider 약관.

승인되지 않은 경로는 staging/private research를 넘어서 enable하지 않는다. 문서 세트에 공식 PDF 자체를 재배포하지 않고 source lock과 내부 보관 정책만 둔다.

## 감사

모든 mutation/external side effect에는 actor, tenant, capability, target, plan hash, source/output checksum, worker/binding, confirmation, validation, timestamp를 남긴다. 문서 본문은 기본 audit log에 넣지 않는다.
