# Release Gate 정의

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## G0 Source/License

공식 source checksum, target build, automation license, fixture rights가 확정.

## G1 Core Safety

package parser limits, transaction, checksum, idempotency, tenant isolation 통과.

## G2 Authoring Core

text/style/page/table/equation의 semantic+reopen conformance.

## G3 Full Feature Binding

609 feature rows의 disposition 100%, release-enabled 기능의 binding/test 누락 0.

## G4 Hancom Oracle

primary build open/save/reopen 핵심 suite 100%, render critical mismatch 0.

## G5 Cross-surface

ChatGPT Web/Codex project resume, conflict, artifact handoff 성공.

## G6 Security/Operations

fuzz, restore drill, worker recycle, incident/runbook, privacy/legal 완료.

## G7 Publish

plugin manifest/app/MCP/UI/auth/submission checks와 production smoke 통과.

어느 gate도 문서상 체크박스만으로 pass하지 않는다. CI run/evidence artifact/승인자를 기록한다.
