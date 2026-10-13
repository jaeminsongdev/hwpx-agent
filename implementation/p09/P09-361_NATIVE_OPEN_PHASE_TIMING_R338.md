# P09 r338 — Native open 대기와 OS 호출의 분리 계측

## 공식 상태

권위 151/249, 잔여 98, 다음 case158. P09/A12/A13 OPEN, P10 새 구현 0, P09~P20 목표 ACTIVE. 성공157 및 실패 run004 재실행·수정 0. 이 작업은 계측 부품·연결 자격이며 제품 승인이나 PC 프리즈 해결 증거가 아니다.

## 코드 검토의 결론

원 `locked_runtime_inputs.Native.create`는 `pacer.reserve()` 다음 `CreateFileW`를 호출한다. 원 `AcquisitionNative.open`의 `open_with_pacing` 계측은 이 전체 호출을 감싸므로 pacing sleep·checkpoint·OS open을 구분하지 못했다. 따라서 run004 최대 5.27702초를 순수 OS open 지연 또는 Python busy loop로 해석할 수 없다. 입력 조상 수집의 중복 순회는 이미 제거돼 있으며, 실제 run004의 metadata inspect 총 시간은 약 0.05630초였다. 원 scope 제외, reads 감소, pacing/600초/CPU-RAM 보호 완화로 통과시키지 않는다.

## 새 계측과 안전성

- V1 `Timing`: 원 reserve와 원 CreateFileW의 bounded 집계만 기록. 추가 OS/resource 조회·thread·per-input 로그·path/handle/error 값 기록 없음. clock 미확인은 0으로 만들지 않고 unknown으로 표시한다.
- ctypes thread-local last-error를 모든 clock 앞뒤로 보존한다. 계측 기록 실패가 성공한 handle 반환 또는 원 exception을 가리지 않도록 보강했다. accounting_unavailable이면 완전 계측의 통과 근거로 사용할 수 없다.
- V1 proxy 설치는 제한된 fixture에서는 동작했지만 실제 bridge의 pacer object identity 계약에는 맞지 않았다. 전체 제품에 연결하지 않고 V1을 보존했다.
- V2는 새 소유 Native 인스턴스의 reserve/CreateFileW 호출 경계만 감싸며 Native/pacer/kernel/phase_pacer/checkpoint alias 객체와 credit/rate/카운터를 유지한다. 원 class method와 close는 변경하지 않는다. 설치 실패 시 원 callable binding을 복원한다.
- connection V1은 원 complete API의 반환 namespace에 새 InputLocks subclass를 추가한다. 원 acquire/check/take/close/verify_held_identities를 그대로 상속하며, 설치 전후 모든 관련 alias를 확인한다. 공개/default module·원 historical source 변경 0.

## 실행과 실패 기록

1. r705: 처음 CODE12 실행은 원 자원 admission에서 STOP. 가용 RAM 6.02495%, tests/fixture Native NOT_RUN. 별도 OS 조회도 가용 약 1.9GB를 확인했다. 외부 앱 종료·설정 변경 0, 기록/원 source preimages 보존.
2. 이후 별도 두 sample에서 가용 RAM 22.63/22.65%를 확인하고 새 보강 CODE14를 실행했다.
3. r706: V1 CODE14 14/14, 실제 기존 fixture Native handle 1 opened/1 closed/remaining False. fresh 5/final 5, CPU 최대 17.69%, 가용 RAM 최저 21.84395%, cleanup True. 해당 단일 fixture에서는 reserve 약 2.3us, CreateFileW 약 24.3us였으나 대량 case158 또는 경고 시 latency를 설명하는 근거는 아니다.
4. r707: 생성된 V2 qualifier 첫 docstring 앞의 잘못된 unary plus로 top-level TypeError. tests/Native NOT_RUN; 원 source 보존 후 생성 오류만 수정했다.
5. r708: V2 CODE8는 8/8이나 fixture pin index를 source list 끝으로 잘못 선택해 metadata 검사 FAILED. 열린 fixture handle은 닫혔다. pin index를 명시적 fixture index로 수정했다. 이를 원 Native 오류로 포장하지 않는다.
6. r709: V2 CODE8 8/8 및 실제 fixture handle 1/1/remaining False, fresh/final 완전, CPU 최대 1.41%, 가용 RAM 최저 27.07385%, cleanup True. Native/pacer/kernel/checkpoint alias identity 유지. 기존 CODE14 suite를 재실행한 것이 아니라 source pin을 확인해 재사용했다.
7. r710: 연결 CODE6 중 경고가 handle 취득 전 ancestor admission에서 발생했을 때 `held.closed`를 즉시 True로 잘못 기대한 test failure. 원 acquire의 이 경로는 owned-handle try/finally 앞이며 enclosing Frame가 close한다. 원 제품 코드를 바꾸지 않고 시험의 소유자 close 동작을 정확히 확인하도록 수정했다.
8. r711: 실제 원 bridge와 fail-fast API를 사용한 연결 CODE6 6/6, fresh 22/final 22, CPU 최대 20.07%, 가용 RAM 최저 25.62378%, cleanup True. Native 호출은 fake lifecycle이며 현재 case158의 live whole scope/GO/product 검증이 아니다.

## 다음 실제 제품 작업

새 계측을 다음 immutable controller/Native namespace에 연결하고 run004 원 실패와 독립 r703 review를 새 attempt에서 명시적으로 검증해야 한다. controller DATA·capsule·source graph·전체 scope/cost·사전검증도 새로 결속해야 한다. 기존 V24의 wholepreflight032 모델 599.620531초를 새 코드의 비용으로 재사용하지 않는다. 필요 시 원 receipt를 유지한 명시적 무손실 표현을 확대해 IO를 줄일 수 있으나 최종 fresh·두 byte·aggregate decode 5초·원 600초와 모든 제품 oracle은 유지한다. 그 후에만 새 독립 attempt의 실제 제품과 별도 acceptance를 진행한다.

접근 허용/한글/UAC 없음. OS/Defender/WSL 변경, 외부 process 종료, 원본 삭제·이동, 실패 replay 또는 Gate 승격 없음. warning 순간 원인 attribution은 여전히 미확인이다.
