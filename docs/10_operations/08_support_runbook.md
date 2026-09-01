# 지원·문제 해결 Runbook

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 수집할 최소 정보

request/job/revision ID, target profile, failure stage, error code, validation receipt. 문서 내용·암호·전체 파일은 필요한 경우에만 사용자 동의와 secure channel로 수집한다.

## 흔한 유형

- 한/글에서 열리지 않음 → package/schema/relationship + target open evidence.
- 표/쪽이 밀림 → font inventory, paper/section, wrap, render provenance.
- 수식이 이미지/텍스트 → native object and EqEdit receipt 확인.
- 자동화 멈춤 → modal trace/process/session health.
- Web과 Codex 상태 다름 → project head/branch/cache sync.
- HWP export 손실 → conversion loss report/backend build.
- 암호/서명 문서 → credential/policy/signature invalidation path.

## escalation

L1 metadata/known errors → L2 capability/backend → L3 format/automation engineering → security/legal/vendor. 지원자가 임의로 보호/암호/서명을 우회하지 않는다.
