# P09 r337 — 커밋 체크포인트와 실패 역할 admission 준비 IO 최적화

## 공식 상태와 범위

- 권위: case157 accept001의 151/249, 잔여 98, 다음 case158. P09/A12/A13 OPEN, P10 새 구현 0.
- 목표는 P09~P20 전체 구현·제품 검증·수정·최적화·통합 검증·원장 동기화 그대로 ACTIVE다.
- 선행 커밋 `7aacbdf`: P09 코드·문서·증거 6,585개 항목. 원격 push 없음. 빌드 EXE, 원본 binary 자료 및 다른 단계의 변경은 제외·보존했다.
- P09의 SHA 결속 자료는 `.gitattributes`에서 `-text -eol`로 원시 바이트를 보존한다. 핵심 6개 staged blob과 작업 파일의 바이트 Git hash가 일치했다.
- 사전 common secret-pattern 검색 일치 0. 모든 형태의 비밀정보 부재를 보장하는 검사는 아니다.

## 최적화와 검증

새 `same_reader_failed_role_admission_v1.py`는 이미 자격을 갖춘 same-reader primitive를 이용한다. 같은 private source graph, authority 객체·메서드, owner, reader, binding ledger에 한해서 **선언만** 재사용한다. 실제 root/독립 review 읽기는 첫 호출에서 그대로 수행하며, 원본 body/JSON/해시/byte stream을 캐시하지 않는다. 매 호출 checkpoint, final-phase 재사용 거부, 새 reader 완전 admission, ledger 변경 거부를 유지한다. 기본 공개 module은 변경하지 않는다.

- r700: CODE11 11/11, fresh 4/final 4, CPU 최대 7.65%, 가용 RAM 최저 56.50395%, cleanup True. 부품 검사이지 현재 제품/GO가 아니다.
- r701: 별도 interpreter의 실제 V23 private graph에서 원 failed003 admission 1회(4 reads/2,220,257 bytes), 같은 manifest namespace의 두 번째 호출은 0 reads/0 bytes. 최종 재해시 30/30. CPU 최대 8.06%, 가용 RAM 최저 56.94805%, cleanup True. 전체 manifest load/whole admission/Native dispatch는 실행하지 않았다.
- 새 V24: 원 V23을 보존하고 wrapper만 private role namespace에 연결. DATA030/whole preflight032로 구분하며 물리 attempt는 아직 실행되지 않은 run004를 사용했다. 원 manifest의 fresh_pin, 최종 finish, Native 두 byte 경계와 worker/GO/Job/제품 oracle을 변경하지 않았다.
- r702: 새 controller CODE25 25/25. CPU 최대 27.24%, 가용 RAM 최저 56.40923%, cleanup True. 기존 V23 CODE23을 재실행한 것은 아니며 새 V24 범위를 검사했다.

## 전체 사전검증032

`p09-361-case158-envelope-controller-run004-preflight032.v1.json`

- PASS_REVIEWED_METADATA_CONNECTION_PREFLIGHT_NOT_NATIVE_OR_PRODUCT_OR_ACCEPTANCE.
- 276.67403초, raw inputs 2,645/286,716,705 bytes, Rust 787, imports 63.
- fresh inputs 954, read passes 1,915/309,131,212 bytes, final fresh hashes 954.
- 물리 scope 2,633/260,006,439 bytes. semantic scope 2,633/278,734,659 bytes.
- 전체 모델 599.620531초 < 원 600초. 60초 margin, 15초 capture, aggregate decoder 5초, acquisition 14/s, byte open 20/s와 원 보호 기준 유지. 모델은 실제 완료 보장이 아니다.
- CPU 최대 52.25%, 가용 RAM 최저 54.07487%, warning stops 0, cleanup True. 제품/Native/독립 acceptance가 아니다.

## 실제 run004와 독립 중단 검토

실제 immutable root `p09-361-case158-current-runtime-run004.v1.json`:

- 2,287,363 bytes, SHA256 `7adefac75a0c1755ea4761144dfed48df3ffae90622de601b2ccfc9cc3e48329`.
- 231.07초, DEFERRED_NOT_STARTED / STOP_NATIVE_OPEN_AFTER_HOST_SATURATION.
- 제품 본문/worker/Job 실행 False, Frame CLOSED·등록 False, source_freeze []·byte boundaries 0.
- Native lock opened 1,281 / closed 1,281 / remaining 0 / close failures 0. 원 source scope 제외 0, cleanup True·owned tree empty True.
- source warning 90% fail-fast latch 1. 원 보호·600초 제한 유지, cooling/resume 추가 0, same run004 재실행·덮어쓰기 0.
- r703: CODE8 8/8 및 root의 원 guarded 읽기+최종 재해시 3/3로 중단·정리 검토 PASS. Native/제품/GO 승격은 아니다.

## 원인에 관해 확인된 것과 불확실한 것

run004 마지막 sample은 전체 CPU 98.04%, parent CPU 0%, parent private 47.953125MiB, 가용 RAM 41.86769%, commit 72.40606%다. 직전 sample은 전체 CPU 34.09%, commit 32.81652%였고 sample 사이가 약 5.42초였다. 원 K32 breakdown은 마지막 kernel busy 59.05980%, user 38.97695%다. 이 증거만으로 P09가 직접 CPU/RAM을 소비했다거나 외부 부하를 촉발하지 않았다고 결론낼 수 없다.

warning 시 optional attribution을 안전상 억제하는 기존 V4 정책 때문에 해당 순간의 MsMpEng/System/다른 process 책임은 확인되지 않았다. 직전 low-load attribution의 보호된/새 process 및 kernel 범위도 불완전하다. 따라서 Defender/WSL/Git/다른 앱 중 원인을 특정하지 않는다.

Native inspect_metadata 1,281회의 총 측정 시간은 약 0.05630초다. open_with_pacing 1,282회의 총 97.53018초·최대 5.27702초는 원 pacer와 checkpoint 대기를 포함한다. 이 최대값을 순수 CreateFile 지연 또는 P09 busy loop라고 보고하지 않는다.

동시 Git command line을 읽기 전용으로 확인했을 때 MapleRust 별도 commit의 자동 maintenance/repack이 있었다. P09 commit은 auto maintenance/gc를 command-local로 껐다. 이 관측은 run004 마지막 경고 순간의 Git 책임을 입증하지 않는다. 외부 프로세스/Defender/WSL/OS 설정은 변경하거나 종료하지 않았다.

## 다음 실제 작업

성공157과 실패004를 재실행하지 않는다. 원 Native acquisition의 pacing·checkpoint·OS-open latency 경계와 attribution의 미확인 영역을 원 code 기준으로 더 검토한다. 관련 최적화는 원 scope·최종 fresh·Native 두 byte·600초·rates·warning·Job 기준을 유지한 새 자격으로만 연결한다. 이후 새 독립 attempt와 전체 사전검증, 실제 제품, 독립 acceptance가 필요하다. 공식 delta 0 / 151/249 그대로이며 P09 완료나 PC freeze 해결을 주장하지 않는다.
