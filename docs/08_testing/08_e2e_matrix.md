# End-to-End 시나리오 행렬

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


| ID | Surface | 시나리오 | 필수 증거 |
|---|---|---|---|
| E2E-01 | ChatGPT Web | A4 보고서 새로 생성 | HWPX, preview, Hancom open |
| E2E-02 | ChatGPT Web | 템플릿 업로드 후 surgical fill | preservation report |
| E2E-03 | Web→Codex | Web 초안을 Codex에서 수정 | 같은 project/revision DAG |
| E2E-04 | Codex local | fixture 100개 batch validation | job summary, no duplicate |
| E2E-05 | Both | A3 가로 2단 수학 시험지 | native equations, split report |
| E2E-06 | Both | 60행 표와 반복 머리글 | page/table render |
| E2E-07 | Both | HWP import→HWPX edit→HWP export | conversion loss report |
| E2E-08 | Both | 그림·도형·차트 포함 문서 | object readback/visual diff |
| E2E-09 | Both | 각주·목차·상호 참조 갱신 | field/reference readback |
| E2E-10 | Both | 변경 추적 문서 수정 | track state/accept-reject |
| E2E-11 | Both | 암호/서명/배포용 문서 | safe block/confirmation |
| E2E-12 | Both | worker hang/retry | no partial commit/idempotent |
| E2E-13 | Web | upload/download and expired URL | artifact ACL/reissue |
| E2E-14 | Widget | preview/diff/revision keyboard flow | accessibility audit |
| E2E-15 | Conflict | 두 surface 동시 수정 | conflict object/branch |

각 시나리오는 primary target build에서 성공하고, 지원 tier별 secondary build 결과를 별도 기록한다.
