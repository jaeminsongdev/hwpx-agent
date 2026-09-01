# 한/글 기능 전수 매트릭스 요약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

`FEATURE_COVERAGE_MATRIX.csv`가 canonical 원본이다. 이 목록은 2026-08-31 설계 baseline이며, P02 official catalog importer가 대상 build별 authoritative registry를 생성한다.

- 총 기능: **609개**
- 영역: **16개**
- 기능별 상세 계약: **609개**

## 지원 수준

| 수준 | 개수 |
|---|---:|
| `HYBRID` | 345 |
| `AUTOMATION_FULL` | 191 |
| `OPTIONAL_EXTERNAL` | 37 |
| `DIRECT_FULL` | 28 |
| `READ_ONLY` | 3 |
| `PRESERVE_ONLY` | 2 |
| `DISABLED_BY_POLICY` | 2 |
| `UNSUPPORTED` | 1 |

## 기능 범위

| 범위 | 개수 |
|---|---:|
| `artifact_semantics` | 405 |
| `editor_workflow` | 80 |
| `workstation_ui` | 68 |
| `external_service` | 32 |
| `security_control` | 24 |

## 영역별 개수

| 영역 | 개수 |
|---|---:|
| 파일·문서 수명주기 | 41 |
| 편집·선택·클립보드 | 28 |
| 찾기·치환·텍스트 변환 | 25 |
| 글자 모양·문자 입력 | 41 |
| 문단·탭·목록·스타일 | 45 |
| 쪽·구역·다단·머리말 | 50 |
| 표·셀·계산 | 61 |
| 수식 | 34 |
| 그림·도형·개체·차트 | 58 |
| 필드·양식·주석·참조 | 53 |
| 검토·비교·이력 | 20 |
| 보안·보호·개인정보 | 24 |
| 도구·언어·외부 서비스 | 23 |
| 스크립트·자동화·이벤트 | 25 |
| 보기·작업환경 | 47 |
| 인쇄·내보내기·접근성 | 34 |

## 읽는 법

`DIRECT_FULL`은 직접 HWPX 경로만으로 완결됨을, `AUTOMATION_FULL`은 대상 한/글 데스크톱 경로가 필수임을, `HYBRID`는 상황에 따라 두 경로를 선택함을 뜻한다. `OPTIONAL_EXTERNAL`은 별도 provider/라이선스/동의가 필요하다. `PRESERVE_ONLY`, `DISABLED_BY_POLICY`, `UNSUPPORTED`는 생성·실행을 지원한다고 표시해서는 안 된다.
