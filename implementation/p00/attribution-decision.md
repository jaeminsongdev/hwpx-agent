# P00-04 Official Source and Attribution Decision

- Decision state: approved_current_personal_noncommercial_scope
- Gate state: pass_current_scope_only
- Production state: disabled
- Date: 2026-09-01

## Locked official material

The current local source set contains the official Hancom HWP/HWPML public-format documents, the official KS X 6101 revision metadata, and the machine-readable KS X 6101 reform 03 response. The response identifies the current revision date as 2024-10-30 and contains 521 matched title/content records.

The machine-readable standard service is treated as a restricted local reference. Its wrapper describes the service as a trial, disclaims legal authority, points to the notified original for accuracy, and prohibits commercial use. The archived response SHALL NOT be shipped, republished, or used for a commercial/production release under the current decision.

## Required Hancom attribution

Every future distributed product UI, About/help surface, user manual, and source repository notice that relies on the public HWP format documents SHALL include the following wording before release:

> 본 제품은 한컴의 HWP 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다.

The current repository root README carries the development-stage notice. P19 release review MUST verify the final product placements and the then-current source conditions.

## Font decision

The HCR Batang/Dotum family may be used in generated publications and works under Hancom's official HCR FAQ. The project does not modify or separately redistribute font files. Other bundled fonts, HancomEQN assets, and any production embedding/redistribution route remain restricted and are reopened at the feature or release Gate that needs them.

## Scope boundary

This decision closes P00-04 only for the user's confirmed personal, non-commercial, local Hangul 2020 implementation scope. It does not grant commercial, internal organization, hosted, server/VM, customer distribution, standards-content redistribution, or provider rights. Those paths remain disabled until a new source and rights review is recorded.

Evidence: evidence/official-source-rights.20260901.json.
