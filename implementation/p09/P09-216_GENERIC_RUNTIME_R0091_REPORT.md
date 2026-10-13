# P09 r91: 시간·신뢰 루트·승인 파서 일반3개 수용

2026-10-09. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용51/249 · 잔여198(일반192+corpus6) · 미closing후보0 · 다음index58.
whole 수용3 / whole재조정대기48. 원 legacy pending1은 별도다.
원 STOP/FAILED 보존. compiled249=true/full249=false/signed16=false.
PC 프리즈 원인·해결 미확정. 고정 r07 개별 runtime 수용 수는 P09 전체 완료율이 아니다.

## 실행 근거와 코드 검토

이전 r90 terminal receipt runtime48/다음55/141bound=fresh/finished/cleanup/
오류·stop=null을 현재 파일에서 확인했다. 직전 턴은 실제5개 수용과 문서 동기화 진전이다.
같은 P222로 case055/run015·case056/run016·case057/run017을 직렬 exact-one 실행했다.
성공1~54의 수용48개 본문은 재실행하지 않았다. corpus47~52 여섯 항목은 미수용으로 유지한다.
각 지원88계약 PASS는 같은 계약을 매번 확인한 것이며 서로 다른264계약이라는 뜻은 아니다.
실제 Native pressure frame 연결 및 실제 packed parent/root writer 연결을 유지했다.
accepted Rust/driver/guard/compact/packed source, 고정 EXE, 원 parent/validator를 변경하지 않았다.
Git/Cargo/build/SQL/한글/접근 허용/설치/삭제/이동/Defender·WSL·OS 변경 없음.

issuer/provider.rs의 read_signed는 scope 검사·descriptor/byte 길이·digest·서명과
전후 policy/approval/trust/clock 재검사를 수행한다. 이 전후 재검사는 철회와 읽기 중 drift를
막으므로 캐시나 generation-only 비교로 대체하지 않았다.
product.rs의 with_verified_bytes는 fresh 검증 후 callback 경계에서 issuer receipt를
다시 비교한다. 검사 직후 철회 보호를 제거하지 않았다.
wire.rs의 승인16KiB/claims8KiB/서명hex128 제한, issuer.rs의 활성 키1~8개/identifier64/
유효기간 제한을 확인했다. 신뢰 snapshot 직렬화의 키 개수도 이 생성자 상한을 받는다.
registry/trust_wire.rs는 trust32KiB/키8개 상한을 적용한다. 이 파일의 읽기 검토는
현재 합성 fixture 실행을 실제 SQL registry 인수로 승격하는 근거가 아니다.
검토한 위 경로에는 무제한 반복문이 없으며, 보안 재검사를 보존하며 즉시 적용할
추가 최적화는 찾지 못했다. 모든 코드/프로젝트의 최적화 완료를 주장하지 않는다.
CPU 보호 중단/Native 경고가 없으므로 이 턴은 새 소스 수정 없이 기존 최적화와
다음 미수용 제품 사례를 검증했다. CPU 보호 중단 시 자동 재시도 금지.
중단 시 실패/STOP 보존→실제 중단 경로·관측 검토→안전한 최적화·연결 검증 후 재개한다.

## 실제 제품 검사와 설명 정정

- case055: 시각0/4/5/300/1000/u64::MAX에서 cached byte 소비/callback 거부,
  clock failure와 읽는 도중 역행 거부, 다시 서명한5종 issued/not-before/expiry/
  trust lifetime 위반 거부, no_publication을 확인했다.
- case056: foreign key·새 generation·같은 generation의 lifetime 변화 뒤 cached byte
  소비/callback 거부, 읽는 도중 trust 변경 및 root denial 뒤 새 준비/재검증 거부,
  no_publication을 확인했다.
- case057:11종 envelope/claims 변형, positional 승인/claims와 malformed·duplicate·
  trailing 입력을 제품 준비 경로에서 거부하고 no_publication을 확인했다.
  실제 선택 이름은 malformed_unknown_duplicate_coerced_positional_and_trailing_approval_never_grants_permission이다.

실행 전 commentary에서57을 callback 직전 철회 사례로 잘못 설명한 것을 terminal
선택 이름 및 고정249 inventory로 정정했다. 실제 driver는 원 plan의 다음 index를
선택했고 실행/원장을 바꾸거나 해당 미실행 사례를 PASS로 세지 않았다.
callback 직전 proof/clock 철회는 index59로 별도 미수용이다.
다음 index58은 one_bit_bad_signature_wrong_domain_foreign_key_and_missing_latest_approval_are_denied.
선택 index와 실제 수용 수는 corpus 제외 때문에 다르다.
issuer 그룹35개 중 현재8개 수용/27개 잔여(일반21+corpus6)이다.
위 실행은 합성 store/trust/clock·fixture crypto 제품 경로이며 실제 운영 issuer/
SQL/trust 설치/native/UI/atomic/product/full249/signed16/Gate 인수가 아니다.

각 exact1 PASS/248filtered/exit0/COMMITTED, 전후1503입력 각118841107bytes 일치.
잠금1809/복제stream3006 전부close/잔여0/close 실패0, Job active0/tree empty.
원 Rust785/두 실제 전체 byte 읽기/final fresh/identity/seek/affinity1/BelowNormal/
Job·GO/한 sampler/원 CPU·RAM·commit 보호·32open/s/no burst 유지.
별도 전체249 결합 예산·600초 Reader·1440표본 수명의 전체 큐 인수는 아직 미수용이다.

## 실제 자원 관측

|case|system CPU max %|controller CPU machine %|controller private bytes|RAM free min %|Job CPU seconds|Job peak private MiB|parent elapsed seconds|samples|bound/fresh/finished|preparation read bytes|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
|55|32.62|1.346154|40153088|43.0444|3.75|28.48|201.14|684|126/126/true|183318883|
|56|91.1|1.711027|40841216|42.3653|5.734|29.74|201.72|686|128/128/true|184952120|
|57|53.5|1.375246|40816640|36.2755|2.203|24.24|250.82|758|130/130/true|186589789|

세 실행 stop=null/cleanup=true/Native warning=0/pause=0이며 root sampler 증설 없음.
시스템 CPU 최고91.10%, RAM 여유 최저36.2755%를 관측했다. controller private 최고
40841216bytes/Job peak private 최고29.74MiB이다.
관측 최고값은 원인 귀속·동일 workload 성능 비교·PC 해결 증거가 아니다.
원 root 저장은 resource cleanup 후 terminal lifecycle 검사이며 위 표본이 root 저장
전체를 감시했다는 뜻이 아니다.
누적 preparation 읽기 증가 1677497/1633237/1637669bytes는 각각 직전 물리 packed root2회+
body3회와 일치했다. 검사 삭제·read 제외·CPU 성능 향상을 주장하지 않는다.

## 이전 고부하 진단 보존

이전 case043 시스템 CPU 100% 표본2회 연속과 P223 원본 진단을 보존한다.
P224의8계약/6bound=fresh/cleanup 진단을 같은 P225가 재대조한다.
Job 값 없음은 0이 아님: root metadata의 누락 Job 값은 null/0관측으로 기록하고
부하가0이었다고 주장하지 않는다. 원 parent hot표본의 Job active4/최대0.483665%
machine CPU 및4회 연속 hardSTOP 미도달을 유지한다. 외부PID/직간접 원인 미확정.
진단 receipt SHA659a277ae8be29c1ca60b7b76c3df4a445008145fd6fabee2fd66f72bb12a254.
이번 새 사례를 이전 고부하의 CPU 개선/PC 프리즈 해결로 승격하지 않는다.

## 물리 receipt pin

모두 implementation/p09/evidence/locked-r07/ 아래 root/body carrier이며 전체 JSON 값을 보존한다.

|path suffix|bytes|SHA256|
|---|---:|---|
|locked-r07/p222-case-055-run015.v1.json|567128|d10c73e4e1342137f638cd8886d73b40e94725fd35c5fd56911e6c0cd70b367a|
|cases/p222-case-055-run015.json|166327|372f384667f32e4631971c7494275f1e9e6c1b6c251d83806883c84299b7db42|
|locked-r07/p222-case-056-run016.v1.json|567484|1ae9fb2c7065dabab02b8db749ebb06b0a462175cdc0e80ae983854f83ef19de|
|cases/p222-case-056-run016.json|167567|7884491b99aab6e648eb8ccdfbc6f22ec4fb01481ad5b8df5ebb50c02a0229fd|
|locked-r07/p222-case-057-run017.v1.json|577392|2ad0ecded1a8f8544fab6db2a153e60fec2a3e34dd2c4d3fd79b91762579c4aa|
|cases/p222-case-057-run017.json|178063|3ceba4c728c129e5e403dc78a8868c29943e9fdf26ee2cb2d43ad8e93b1d4888|

## 문서 동기화와 다음 경계

r90 두 문서의 이전 receipt 길이/SHA pin을 확인한 뒤 evidence/runtime-progress-r90/에
복사했다. overwrite 없이 동일 byte 복사를 대조했다.
동일 r91 prefix를 추가하고 기존 byte suffix·원 날짜·실패 원장을 보존한다.
보고서 작성만으로 문서 PASS를 선언하지 않는다. 같은 P225의 별도 terminal r91
문서 receipt가 새 pair3개/runtime88+document8+diagnostic8/전체fresh/cleanup/
기존 byte 보존/원 STOP 보존/오류·stop=null/GateOPEN을 검증해야 수용한다.
문서 validator는 새 제품 본문/source frame을 실행하지 않는다.
그 뒤 다음 미수용 index58부터 이어간다. P09 Gate가 권위 있게 닫히기 전 P10 새 구현 없음.

