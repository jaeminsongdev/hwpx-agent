# P270 metadata 90% 조기 읽기 완화 연결

2026-10-09. runtime 수용87/249; 잔여162(일반156+corpus6); 다음index94.
P09·A12·A13 OPEN. 원600초·CPU/RAM 기준은 변경하지 않음. 실제 full runtime 연결 NOT_RUN.
PC 프리즈 원인·해결 미확정. 실제94 본체와 소실된 원 parent/Job 결과는 수용하지 않는다.

## 실제 P269 경고 확인

P269는 작은3파일/43874bytes 전후 읽기, Native 잠금7/duplicate6/잔여0, 종료 후 diagnostic-only 기록과88계약에 PASS했다. 최종 metadata IO371읽기/179bound=finalfresh/cleanup true/STOP null이었다. 원 부모 표본2개는 실제 원 sample 메서드로 얻었으며 최대 CPU7.36%; 제품/Job은 실행하지 않았다.

외부 watcher79개 표본 중100%는 단 한 번이고 연속≥98 최댓값1이다. phase는 `final_fresh_hash`, 당시 자체 CPU0%, Job CPU는 미측정 None이다. 앞/경고/뒤 표본은 전체CPU91.21→100→91.41%, 논리 읽기 증가1011056→973048→0bytes였다. 기존95% 완화는 실제1초(서로 다른 두 표본) 대기했다. 이 자료로 읽기가 전체CPU 상승의 원인이라고 단정하거나 외부PID를 특정하지 않는다.

## 변경

기존 Native/source 경로에 이미 qualification된 P257 90% 조기 알고리즘을 **owned metadata reader checkpoint**에 명시 연결한다. 기존95% pressure 객체를 identity 그대로 base로 유지한다. 원98x4/RAM/commit/600초/720읽기/전체 byte·finalfresh·sample을 생략하거나 연장하지 않는다.

Reader constructor의 기존95% 경로는 그대로 실행되고 constructor 종료 후 연결한다. 이 연결은 전체 constructor에90% 보호를 적용했다고 주장하지 않는다. 원 Context/reader/aggregate counter/previous/entry binding/clock를 바꾸거나 reset하지 않는다. cleanup callback도 감싸지 않는다.

91~95%의 경고 창에서 다음 chunk 읽기 전에 원 보호 코드를 호출하고 기존 owner의 서로 다른 두90% 미만 표본까지 쉰다. 최대8개 창/half-second 간격이며 cached sample은 냉각 증거가 아니다. 새 sampler/thread/CPU·Native query는 추가하지 않는다. 낮은 일반 부하를 금지하는 startup gate가 아니다.

기존 EarlySource12개 + 새 연결14개 + 경고 receipt 거부4개, 총30개 예비 계약은 통과했다. 최종 qualification은 동일 reader의 실제 metadata 읽기/모든 bound input finalfresh, 기존179bound receipt와 diagnostic 원본 SHA·길이, 기존92/93 strict pair 재계산/실패94 및0byte 보존으로 진행한다. 실제 제품/전체 Native frame/CPU stress는 실행하지 않는다.

최종 완료 여부는 `evidence/locked-r07/p270-early-metadata-pressure-run01.v1.json`의 실제 state로 판단한다. 없거나 FAILED면 연결 qualification 완료가 아니다. 정상 부하에서 PASS했다고100%/프리즈 개선을 입증한 것은 아니다. 후속 immutable 전체 실행기와 추가 controller 범위 사전검증이 남는다.

## 불변 근거

- P269 root163181bytes: `c9d9d95a434cb9b7c31dc80c460ad70eb175249c112e3dd1485baaeec669b1c5`
- 원94 root1345290bytes: `c347fd3df25cd2b4d52db6f8c27e6325c039f803ab0987f8e0902ac9005f31f9`
- P269 diagnostic11426bytes: `269f1c1365e00e512bd05e6c1386da770ecbe8bfd818e49892af6beecbfcd9bd`
