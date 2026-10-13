# P09-304~305 101 anchor 재개·102 준비 STOP·안쪽 checkpoint90 qualification

2026-10-09. 목표 ACTIVE. P09/A12/A13 OPEN.

## 현재 판정

실제 runtime 수용95/249, 잔여154(일반148+corpus6), 다음102, whole 재조정92, 독립 source 마감 후보0을 유지한다. 102는 제품/Native 실행 전 준비의 final_fresh_preparation에서 CPU STOP했다. 102 수용0이며, whole1470/historical67/full249/signed16/제품 완료/PC프리즈 해결은 FALSE다.

## P304 새 anchor 및 반복 비용 개선

`resume_completed101_compound_runtime.py`와42거부조건 테스트를 추가했다. 원101 P291 FAILED/bodySTOPPED, 원100 pair, P299 독립 full source, P300 결합 실패, P302 exact compound를 literal pin과 원 typed classifier로 재계산해서95/next102를 확인한다. 옛 실행 이력을 모든 세대에 걸쳐 매번 다시 펼치는 대신 현재 수용101의 정확한 원 증거를 사용한다. 기존 본체 및 P299 Native/두전체 읽기는 반복하지 않는다.

- 기존 source/code의 고정 pin과 P291 light qualification에 연결된1486계약은 재사용 증거다. 이번 실행한 계약 수에 합산하거나 재실행했다고 표시하지 않는다.
- 이번 실행은 현재42+다음42+원 frame/parent30+leading18=132 합성 계약이다. 신규1631 scope/current·following 선택과 거부조건을 검사했다. 합성 PASS를 actual Native/제품/Gate PASS로 승격하지 않는다.
- 계획 입력은 P299검증1625 +기존post metadata4 +새controller/test2 =1631개, ancestor308, controller164 전체. 600초·720read·획득14/global20/metadata32·byte1/2MiB·CPU98x4/RAM비율·Job 제한·두전체byte/Nativeidentity/cleanup을 유지한다.
- 준비 light:188read/10325197bytes/79bound/fresh79 완료. systemCPUmax21.48%, ownCPUmax5.85901%, private47816704bytes, availableRAMmin24.10774613049025%.
- 명목 예산584.9007402420044초는 완료 보장이 아니며 실측 deadline600은 늘리지 않았다.

light receipt: `implementation/p09/evidence/locked-r07/p304-light-run001.v1.json`
27993 bytes / SHA256 `f1dc5cd70aed230d3a01c9d18ff8ab3a476bd1a18367f82eeccf2e2d611a9e9b`.

## 실제102 준비 STOP

receipt: `implementation/p09/evidence/locked-r07/p304-case-102-run002.v1.json`
81902 bytes / SHA256 `a37eb691a8cb786f7b26d445267ecc550cdaf5b140e6a73f37f0b82d79249a5f`.

- 선택102, 실제132 계약 완료 뒤 final_fresh_preparation에서 STOP_SUSTAINED_SYSTEM_CPU.
- 154read/9753235bytes/80bound/fresh44; finished FALSE. 부분 최종 읽기를 수용하지 않았다.
- Frame/입력잠금/Job/제품 실행 이전. old body 파일, source frame 및 sidecar 없음. Native 핸들 수는 측정되지 않아 NULL로 남긴다; 임의0 측정값으로 채우지 않는다.
- 원 큐95/next102/잔여154, 수용0, watcher cleanup 확인. 원 실패·코드·통과 light를 수정하지 않았다.
- 표본25: system CPUmax100%, ownCPUmax5.753283%, private47341568bytes, availableRAMmin23.34310685051423%.
- 마지막4개 system100/ownCPU0/read증가0. 직접 검증 연산이 포화 원인이라는 증거는 없으며 간접/외부 원인도 배제하지 않았다.
- pre-entry leading90 대기0. 기존 inner95 대기1회/3window/1.5초, 기존 outer90 대기1회/2window/1초. 읽기 진입 전 대기만으로는 내부 checkpoint/pacer 대기 중 시작되는95% 경고를 선행 처리할 수 없는 경로를 확인했다.

## P305 안쪽90 개선

`leading_metadata_checkpoint_pressure.py`와30검사를 추가했다.

원95 pressure object와 outer90/entry32 callback은 그대로 둔다. **원95 안의 hard guard callback을 감싸서** original CPU/RAM/IO600 검사를 항상 먼저 호출하고, 90% 이상이면 기존 표본만으로 bounded 대기한다. 그 뒤 원95/outer90 처리가 그대로 진행된다. 신규 sampler/Native query/thread, clock credit/read counter reset, guard/deadline/읽기·범위 제외는 없다. 정리 시 guard/sleep을 호출하지 않고 hard callback을 복원한 다음 기존 pre-entry/entry cleanup을 실행한다.

- callback30 =안쪽 동작18 +원 실패102 거부조건12.
- CPU96에서 새 안쪽90이 두 cold sample을 기다린 뒤 원95 경고 대기는 진입하지 않는 합성 경로를 검증했다.
- hard CPU/RAM/600 STOP가 항상 우선하고 매 sleep 뒤 재검사; stale/unknown sample 및8window 상한; 원 callback/entry32/pacer 보존·guard 없는 복원을 검증했다.
- 실제 작은 metadata qualification:6bound/fresh6,12read/341280bytes, inner guard87회, callback복원·cleanup 확인, CPU STOP 없음.
- 실제 qualification의 안쪽90 경고는0이었다. 합성 검증이나 낮은 실측 CPU만으로102 제품 연결/최적화 효과/PC프리즈 해결을 증명하지 않는다.
- P304 source/test의 기존 light pin과 현재 byte SHA를 확인해 보존했다.

qualification receipt: `implementation/p09/evidence/locked-r07/p305-inner-checkpoint90-qualification-run01.v1.json`
11746 bytes / SHA256 `c3f44a308be85c4bef41ae11e997024f1a2ca4e4b657c24f140bea77d2727277`.

## 다음 경계

P305는 작은 독립 qualification만 통과했다. 다음 actual runtime의 준비·최종 reader에 아직 연결되지 않았다. 미검토 P304 실패가 있는 동일 세대를 바로 재시도하지 않는다. 다음 단계는 이 literal STOP 검토와 P305 qualification을 바인딩한 새 controller generation을 구성하고, 현재/다음 full-scope 계약을 검증한 후 미수용102만 실행하는 것이다.

추가 정적 검토에서 metadata의 controller 그룹들이 겹쳐 같은 helper를 여러 번 fresh 읽는 부분도 확인했다. 이 중복을 줄이더라도 모든 서로 다른 입력의 실제 시작/종료 fresh 읽기, original reader guard/parse/byte/counter 및 제품의 두 full-source 읽기는 유지해야 한다. 아직 이 중복 읽기 최적화를 구현·검증했다고 주장하지 않는다.

기존 실제수용95와 원본/private/P00~P08/dirty 변경은 보존. 한글/접근허용/빌드/Git/OS·Defender/WSL 설정 변경, 실패 삭제·덮어쓰기 없음. P09 Gate를 닫기 전 P10으로 넘어가지 않는다.
