# Golden 문서 corpus

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 구성

최소 500개 공개/자체 생성 fixture를 목표로 한다.

- 100 text/style/page/section.
- 100 table/cell/calculation.
- 80 equation Tier A/B/C.
- 80 drawing/image/chart/OLE-preserve.
- 60 fields/notes/references/forms.
- 40 review/security/history.
- 40 corrupt/adversarial/edge-size.

## 출처와 개인정보

실사용 문서는 명시적 동의와 비식별화를 거치지 않으면 corpus에 넣지 않는다. 가능하면 synthetic generator와 공개 라이선스 template을 사용한다. 각 fixture는 origin/license/PII review/checksum을 기록한다.

## fixture manifest

```yaml
id: table-merge-017
source: synthetic
license: project-owned
features: [table.create, table.merge_cells, table.cell_border, table.cell_padding]
targets: [hancom-2024-13.x]
expected:
  semantic_hash: ...
  pages: 2
  warnings: []
allowed_visual_regions: []
```

## golden update

테스트 실패 시 자동으로 golden을 덮어쓰지 않는다. semantic/render diff, 원인, target build change, reviewer 승인을 포함한 proposal로 갱신한다.
