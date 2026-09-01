# Open Decisions

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


아래는 설계를 막지 않지만 해당 phase를 시작하기 전에 ADR로 닫아야 한다.

| ID | 결정 | Deadline |
|---|---|---|
| OD-001 | primary/secondary 한/글 제품·정확한 build | P00 |
| OD-002 | 상업 automation 및 WebHWP 라이선스/배포 범위 | P00 |
| OD-003 | Windows interactive session/VM 운영 방식 | P00/P10 |
| OD-004 | 공식 PDF/XSD catalog parser와 저장 권한 | P02 |
| OD-005 | preserving XML crate/자체 token layer | P03 |
| OD-007 | primary render/export oracle 방식 | P10/P13 |
| OD-008 | font licensing와 server image font set | P05 |
| OD-009 | chart/OLE direct support depth | P08/P11 |
| OD-010 | metadata DB/object store/queue vendor | P14 |
| OD-011 | OAuth provider/tenant account model | P15 |
| OD-012 | public listing vs workspace/private first | P16/P19 |
| OD-013 | artifact attachment vs signed URL priority by surface | P15/P16 |
| OD-014 | retention/data residency/default privacy tier | P14/P18 |

결정 없이 진행해야 할 때는 가장 보수적인 옵션으로 feature를 disabled/unverified 상태에 두며, 추정으로 production-enable하지 않는다.

## 닫힌 결정

- OD-006: C#/.NET STA worker + protobuf/gRPC Windows Agent + local named pipe. `ADR-0015`, `ADR-0016` 참조.
