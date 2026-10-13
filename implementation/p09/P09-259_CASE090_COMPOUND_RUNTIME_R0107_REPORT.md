# P09 P258~P259 실제90 독립 source 완결과 runtime-r107

2026-10-09. 목표 active. P09·A12·A13 OPEN. 원 STOP/FAILED 보존. PC 프리즈 원인·해결 미확정.

## 수용 결과와 경계

runtime 수용84/249 · 잔여165(일반159+corpus6) · 독립source 마감대기0 · 다음index91 · whole재조정대기81.

case90 actual_import::formula_policy_revocation::changed_current_policy_denies_before_revocation_write의 원 본문 exact1/failed0/ignored0/measured0/filtered248/exit0은 앞서 완료됐다. 원 실행은 final_source_freeze의 after321/1545·53845255/119242806bytes에서 CPU STOP였고 원 root FAILED_NOT_ACCEPTED/sidecar STOPPED_NOT_ACCEPTED/placeholder0bytes는 바꾸지 않았다. 본문 재실행 없음. 기존 실패를 PASS로 재분류하거나 partial source를 full로 승격하지 않았다.

P258의 새 독립 source-frame은 원1545입력과 새 검토/마감 코드·현재 사용하는 문서helper/test6개를 모두 포함한1551입력을 실제 두 번 읽었다. 별도P259 compound만 기존본문+독립source를 결합한다. 원whole1470·historical67·full249·signed16·P09 Gate·제품완료는 별도 미완료다. 이249건 subset은 P09 전체 완료율이 아니다. SQL/생산issuer/한글UI/render 수용이 아니다.

## 실제 독립 source 검증

- source schema hwpx-agent.p09-checkpoint-stop-independent-source-frame/v1 / PASS_CASE090_INDEPENDENT_FULL_SOURCE_EARLY_CHECKPOINT_NOT_RUNTIME_OR_GATE.
- preparation20읽기/10bound=10finalfresh/finishedtrue, 원maxscope600. 계약14개. 상태 기록은 새본문없음/원partialpost미완료/runtime수용변경false.
- 전후각1551입력·119296946bytes. 원1545는119242806bytes이고 새6은54140bytes. 입력 제외·캐시 대체 없음.
- frame COMMITTED/등록해제. 잠금1857 opened=closed, duplicate3102 opened=closed=seekreset, byte identity3102. 남은handle·stream·reader·probe·close실패·별도pathnamebyte재열기0.
- 원 Native20회/s/4959예약 및 no-idle-burst, 원 EXE1MiB/s·기타2MiB/s/두전체byte읽기/metadata32, 원IO/Native600/CPU/RAMguard 유지.
- 원90 Job의 실제cleanup/ownedtreeempty/active0 witness로 frame을 마감했으며 새Job·본문을 만들지 않았다. source의before/after는 독립 검사 내 경계이며 원90 실행을 둘러싼 연속liveframe이 복구됐다고 주장하지 않는다.
- 예산은 nominal510.278539초<600(파일예약247.95+두byte읽기127.328539+metadata60+완화15+margin60). 예상은 완료보증이 아니며 실제600초 guard가 계속 적용됐다. 원600초·CPU/RAM 기준은 변경하지 않음.

## 자원·조기 완화 연결

source698표본/전체CPUmax83.95%/95%이상0/98%이상0/원 Native95%warning0/CPU STOP없음/cleanuptrue. 자체CPUmax1.500938%, private최대37556224bytes(약35.82MiB), 가용RAM최소31.777961%. 이는 해당 실행의 표본이며 외부PID 원인/물리순간 전체/PC 프리즈 해결 증거가 아니다.

P257 EarlySourceCheckpoint를 새held/frame에 실제 연결해 Native 취득과 각 byte읽기의 원guard를 보존했다. 원checkpoint를 먼저 실행한뒤 기존owner표본90%이상에서0.5초yield·90%미만서로다른2표본·최대8창/4초대기다. 원98%x4/RAM/commit/600 guard는 변경/억제/재시작하지 않았다. 원95%완화도 그대로 연결돼있다. cleanup은 조기callback으로감싸지않았다.

조기 완화 실제 경고 진입0, 실제yield0초. 실제 연결/전체 source 통과는 입증됐지만 고부하에서의CPU개선/경고STOP예방효과는입증되지않았다. 90%기준은35%startup gate가아니며 별도soft읽기완화다. 새sampler/thread/CPUstress/외부PID조회 없음.

CPU 측정의 GetSystemTimes idle/kernel/user 차분 계산도 읽어검토했으며 현재단순계산오류는확인하지못했다. 원90의rootowner100%4연속과parent94.89%는 서로다른시점표본이고, 경고자체CPU약0.20%와실제Job1.156초를host100%의원인으로확정할수없다. Defender/WSL/OS 설정을바꾸지않았다. CPU 보호 중단 시 자동 재시도 금지.

## 결합 판정·문서 검증

P259는 원m.anchor의sealedr102/95입력·compiled249·원1470manifest·Rust785/legacy 판정을 유지한다. P255 closed82~89 여덟root/body는 원m.record로 각각 확인하며본문을다시실행하지않는다. 단하나의literal p255-case-090-run010만길이/SHA/원prior83/next90과P257 review로소비한다. 다른실패·변경된literal·누락된이전8기록·90이후새기록은차단한다. 불변P255.progress의FAILED차단은수정하지않았다.

기존본문 exactmanifest/EXE/worker/core/joblimit/GO/캡처/정리와 원1545source pin을 확인하고, P258 fullsource1551과새6helper의현재byte가동일한지 확인한다. compound26계약에는 바인딩·본문/입력/핸들/guard변조거부와중복/후속기록/미검토실패차단을포함한다. 새수용수는 원g.advance로83→84/next91/잔여165/whole재조정81을 재계산한다. 모든bound입력은 원Reader의first+finalfresh로판정한다.

r106 CURRENT_STATE457433bytes SHA057940b5f889ba9ead4abb73eda0aa706a6946f850fd8ebdb3cdaaf2991b181c, PROGRESS551065bytes SHA2a5dca42bd19b6812f2573c2d07b4305be362165e8fc7de3dab108efc2c3c781을 runtime-progress-r106/에exact보존했다. 동일새prefix/원bytes suffix와r107reportproof를새compound판정에포함한다. 이전P257/P258receipt·수용된코드/테스트/보고서는수정하지않았다. 새P259만추가했으며본문/독립source를다시실행하지않았다.

## Exact 증거

문서 사전 진단 명령의 괄호 구문 오류1회와 진단 메모를 넣으려던 편집 위치 지정 오류1회가 있었다. 단순한 진단 명령으로 원suffix·동일prefix·보고서proof 해시를 확인해 통과했다. 이 두 오류는 제품본문/독립source/guarded compound 실행 실패가 아니며 원source와수용증거는바꾸지않았다.

아래 기준 implementation/p09/evidence/locked-r07/.

| 증거 | bytes | SHA256 |
|---|---|---|
| p255-case-090-run010.v1.json 원FAILED | 766447 | cc598cbc42c399b64eadcd35868f142b3ba51a09d81265029b95f2e4be3595f6 |
| cases/p255-failure-090-run010.json 원STOPPED | 483214 | 8ce9dfaa8a5efc8f7ef5290f254f6e551098dfcc50aa5ba3ec3393831d8e8e4c |
| cases/p255-case-090-run010.json 원placeholder | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| p257-case090-stop-review-run01.v1.json STOP검토/후보 | 10377 | 73ab14f7f7a66a40ac2ad3e00531541e6b0207b6a286d1e8f5bfcb4acf2b1c4b |
| p258-case090-source-frame-run01.v1.json 독립전체source | 1869973 | 4cd9bc4ffdf844d1eb54c5a30ed8ade5f4a33c203f89bab58cbda2dd503674fd |

P258에서 actual-bound됐던 새코드: close_checkpoint_stop_source_frame.py13054bytes SHA17938e8e7ca7ea6a4f345b7a39b1ec99b09ca8f983a8a6eb8a8ff6dd81be97d2; tests/test_checkpoint_stop_source_frame.py6282bytes SHA2c904a3c4304b0b1f9f46c3e928721bbd35e413e759d654be4657f438a23f3e7. 이원byte를그대로유지했다.

## 전체 목표와 다음 경계

현재live conformance행렬을 다시읽었다:53행/P09소유46/P11deferred7/componentcovered46/directHWPX11/green0/non-green53, actualHWPX·Hangul·automation·render·differential각0. 이CLI runtime수용을해당oracle/Gate수용으로대체하지않는다. P09 Gate가닫히기전P10새구현에진입하지않는다. P00~P08·원본/private·사용자변경·실패증거보존. PLANS복원없음. Git/Review/Cargo/build·원격push·SQL·한글GUI·접근허용없음.

다음미실행91은다른생성자의정책에대한현재writer의철회권한을검증한다. 새compound를소비하는실행기연결이남아있어현재91 NOT_RUN. 불변P255를강제로재개하거나90본문을재실행하지않는다. 원전체입력과현재실행코드를명시결합하고CPU/RAM/600/720제한·byte/Nativepacing·모든identity/정리를그대로검증한뒤단일91을진행한다. whole1470/historical67/full249/signed16/Gate/P09전체완료는미완료다.
