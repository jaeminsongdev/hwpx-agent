# 한/글 버전·빌드 적합성 행렬

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## TargetProfile

```yaml
profile_id: hancom-2024-13.x-ko-KR
product: Hancom Hangul
major_release: 2024
exact_build: TBD-P00
os_image: windows-11-23h2-hancom-2024-v1
locale: ko-KR
fonts_manifest: fonts-2026-08-31.json
automation_catalog: action-2504+runtime-probe
license_state: pending
```

## 지원 정책

- 최소 1개 primary build를 GA 기준으로 고정.
- 이전/최신 build는 compatibility tier로 추가.
- build 변경 시 action/parameter diff, generated documents, open/save, render smoke를 실행.
- 설치 환경, language pack, printer driver, font set을 image manifest로 고정.

## oracle suites

- `open-only`.
- `open-save-reopen`.
- `property-readback`.
- `equation-editor`.
- `print-preview/pdf-export`.
- `automation-events/modal`.

## 환경 불확실성

실제 한/글 버전과 라이선스가 확정되기 전에는 기능을 특정 build에서 완전 지원한다고 표시하지 않는다. v2 feature catalog는 구현 disposition이고, build별 `release_enabled`는 P00/P10/P13 결과로 생성한다.
