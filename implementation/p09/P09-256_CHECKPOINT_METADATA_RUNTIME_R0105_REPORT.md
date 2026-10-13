# P09 P255~P256 불변 실행기의 실제88~89와 runtime-r105

2026-10-09. 목표 active. P09·A12·A13 OPEN. 원 STOP/FAILED 보존. PC 프리즈 원인·해결 미확정.

## 이번 결과와 수용 경계

runtime 수용83/249 · 잔여166(일반160+corpus6) · 미closing후보0 · 다음index90 · whole재조정대기80.

미실행88·89만 각각 한 번 단독 실행했다. 통과 본문 재실행 없음. 불변 P255 코드·테스트와 기존450 계약 실행을 그대로 재사용했다.450은 원398+현재26+명시적 synthetic 다음26이며 두 회차를 새로운 고유900계약이라고 주장하지 않는다. 출력 post_stop_runtime_contract_tests_passed18은 상위 유지 계약 반환값이며 전체 실행450와 구분한다.

- 88: actual_import::formula_policy_registration::source_head_quarantine_and_aead_drift_deny_before_any_registration_write
- 89: actual_import::formula_policy_registration::unverified_policy_artifact_is_retained_but_never_sent_to_registrar

88은 source head 변경·quarantine·AEAD drift 세 분기에서 등록 쓰기 전 거부와 repository 호출0을 확인한다.89는 미검증 정책 artifact를 보존하면서 registrar 호출0을 확인한다. fixed EXE/fixture/repository double 제품 CLI의 exact1이며 실제 SQL·생산 issuer·한글 UI·전체249/P09 Gate 수용은 아니다. P239 실제 pre-GO CPU STOP 경계 NOT_RUN.

## 자원·원 검사

| 실제 index | 원 parent초 | 준비+후속읽기 / bound=finalfresh / 준비 논리bytes | 전체CPUmax / 자체CPUmax % | private최대bytes / 가용RAM최소 % | JobCPU초 / peakMiB |
|---|---|---|---|---|---|
| 88 | 254.22 | 272+2 / 130 / 34651650 | 38.91 / 5.837563 | 56918016 / 35.484304 | 1.359 / 23.72 |
| 89 | 250.30 | 276+2 / 132 / 36196736 | 59.57 / 5.736823 | 56377344 / 35.262956 | 0.672 / 23.46 |

root표본729·724개 각각95%이상0/98%이상0/지속98%4연속0, Native pressure0. 두 실행 metadata finished/cleanup true/STOP없음. 원 Job active0/owned_tree_empty. 검증 부모 private 최대56918016bytes(약54.28MiB), Job peak 최대23.72MiB. 단일 표본이 아니라 해당 실행의 저장 표본이며, 모든 물리 순간이나 외부PID의 원인을 증명하지 않는다.

각 전후1545입력 각119242806bytes/COMMITTED/등록해제. 잠금1851 opened=closed, duplicate3090 closed, byte identity3090, 잔여·close 실패·reader/stream·별도 경로 byte 재열기·probe0. Native20회/s/4941예약/no-idle-burst, metadata32회/s, EXE1MiB/s·기타2MiB/s, 원1200본문 및600초 IO/Native guard·CPU/RAM/Job 제한과 전후 실제 전체 두 byte 읽기/identity/정리 유지. 원600초·CPU/RAM 기준은 변경하지 않음.

## 관련 코드 읽기 검토와 다음 중단 대응

crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_registration.rs의 실제88은 유한3분기,89는 단일 사례다. 두 본문에서 무제한 루프나 새 병렬 실행은 확인되지 않았고 실제 Job CPU1.359·0.672초였다. 검증 소요의 대부분은 원 전체 입력 검사·속도 제한과 증거 경로에 있다.

tools/p09/resume_checkpoint_metadata_runtime.py의 원 fresh 읽기/단독run_parent/record/정리·실패 보존, lower_native_acquisition_pressure.py의 instance20회 제한, metadata_read_entry_pacing.py의 원 reader 호출과 STOP후 무대기 복원, locked_runtime_inputs.py의 OpenPacer.reserve를 읽어 검토했다. pacer는 time.sleep 대기·최대64 반복·no-idle-burst로 무제한 busy wait가 아니다. observe_shared_metadata_recheck.py의 원 표본 재사용/자체 memory 조회/1440표본 상한·외부PID 비조회도 확인했다. 이 읽기 검토는 새로운 전수 최적화 완료나 PC 프리즈 해결 증거가 아니다.

이번 관측에 적용할 새 병목 근거나 CPU STOP이 없어서 수용된 helper/테스트/제품 코드를 수정하지 않았다. 이미 검증된 checkpoint 재생 축소·Native/metadata pacing을 재사용한다. CPU 보호 중단 시 자동 재시도 금지. 다음 STOP가 발생하면 실패/원본 증거 보존, 중단 단계와 표본·소유 CPU/Job 구분, 해당 본문·잠금·metadata·serialization 코드 검토, 근거 있는 새 세대 최적화·검증 후 미실행부터 재개한다. 보호 기준 완화·원 검사 제외로 통과시키지 않는다.

## Exact 증거

이전 문서 receipt: implementation/p09/evidence/locked-r07/p256-checkpoint-metadata-status-doc-r0104-run01.v1.json
55699bytes / 55332d6fe1d6f0e1e2bb03d4635e932e3f33764888a38038c1508fb5690a1a86.

원 checkpoint: p254-generic-metadata-status-doc-r0102-run01.v1.json
40000bytes / f394aded5f736eae6b46ccb8885d5e46e99a845b7135849126f526d366b49e9e.

원 actual81 anchor: p253-case-081-run003.v1.json
615984bytes / 22d57ddd87d213c6d41c39c536c5d83e2fec295ea34d110540f5406284b2a246.

아래 상대 기준 implementation/p09/evidence/locked-r07/.82~87은 증거 소비만 했으며 이번 본문을 재실행하지 않았다.

| Root/body | bytes | SHA256 |
|---|---|---|
| p255-case-082-run002.v1.json | 587528 | ed45ccea9cf1908178a26e4150176047c69e0b39801f49c3af2d703b68e79698 |
| cases/p255-case-082-run002.json | 180883 | 2d7d0fd4a8f8353c6f1567674cc34d2ad975f1969ee9e15c350118a1848212ea |
| p255-case-083-run003.v1.json | 590216 | d993f764dfbccb017a85cdfcdcc559af3a6645fff70b12c177e2e06d4b863a9f |
| cases/p255-case-083-run003.json | 186103 | 9d80988e819700b75396ac98acb4a8497feab253b37c005e65eaef4627b65d59 |
| p255-case-084-run004.v1.json | 589176 | 6af609b2f2293f1a4a1939ee9407a2f466d2d737ec35d279b3b83b75276a6204 |
| cases/p255-case-084-run004.json | 181739 | 1e4a8dceed6cad18d98ce26a7303d6dfc06e6072a20c9d9d07fc7e0ece368e80 |
| p255-case-085-run005.v1.json | 589008 | a767af5a97a20dd30bb8fc36cb6c4715a2007134b4ac598538b90f280acc88f5 |
| cases/p255-case-085-run005.json | 180387 | 4704df1035b8dbfc779c91b1d3d3ede41dc66013c4703eae2b24e6b8cea4d608 |
| p255-case-086-run006.v1.json | 590852 | 9eee6fffa7156149b868d4179cf4ea1c690e4a49766d08ce924551e2307df7d0 |
| cases/p255-case-086-run006.json | 186647 | 347b9b82ab5aabcf1aa0445d6935bf7ecc66f3af219c257dc91af47c87a4cec7 |
| p255-case-087-run007.v1.json | 590288 | 06f40a2ef211d132a18bb785cbb0f13a6b7efd7c097247ef06b23720741ffc1f |
| cases/p255-case-087-run007.json | 182731 | 2ec8ff7b92343e88e8a463873dc293f429b8cb33f498d55ffcf0b692d9abba82 |
| p255-case-088-run008.v1.json | 590452 | a879d88fd90f06c5da394aee9bcbe2954ddec47684e3aebb79c63eeee4aeb9ad |
| cases/p255-case-088-run008.json | 182091 | adad1110c322d07bd4888323343d5e576b57fba8b82b7dcc01a9a065600e30fe |
| p255-case-089-run009.v1.json | 588384 | a177b26836c7cdfc402eadb90492f76ab95f10667975b96289405a889b934f12 |
| cases/p255-case-089-run009.json | 179327 | c13a59e20723d27f9e0fd232588df7632445277b49caf13875d51ca9eb6818d0 |

## 문서와 다음 단계

새 문서 상태 snapshot/P256의 불변 원 anchor/progress/record, 문서14계약과 모든 bound 입력 최종fresh로 누적83수용을 확인한다. r104 상태 문서 두 개의 SHA/length exact 사본 runtime-progress-r104/과 현재 동일prefix/원bytes suffix를 보존한다. 이전 문서 CURRENT_STATE453620bytes SHA f9569ceff1196786711912c586f7011af74d87e0840e5e9b27efb14b5b9ebfd0, PROGRESS547252bytes SHA 9c9068aa955999cb5f66d195f91bad2887883e2970ab09600d1c83a5b4fdc690.

사전 진단 명령에서 packed root를 raw JSON으로 접근해 case_receipt_pin KeyError가 한 번 났다. 원 packed.unpack을 사용하는 진단 명령으로 바로잡아 exact suffix·동일prefix·모든증거hash·보고서words·문서helper/test불변·문서14계약을 통과했다. 제품 본문이나 guarded 문서실행 실패/CPU STOP가 아니며 수용 코드·증거는 변경하지 않았다.

원 r102 checkpoint95·compiled249·1470manifest·Rust785 baseline·known 실패 semantic·namespace 새 미검토 실패 차단은 유지한다. checkpoint보다 앞선 과거 전체 receipt를 모두 같은 범위로 fresh 재생했다고 주장하지 않는다. whole1470/historical67/full249/signed16/제품완료/PCfreezeResolved false, P09 Gate OPEN. 기존 live conformance53/P09소유46/P11deferred7/green0/actualHWPX·Hangul·automation·render·differential0은 별도 Gate축이다. phase/ROADMAP_STATUS 재조정 미완료이며 P10 새 구현에 진입하지 않는다.

실제90 NOT_RUN. 최신 preparation276+새root/body첫읽기2+최종fresh2+원후속2=다음shared282 예상≤720. 예상은 실제CPU STOP나 실행 증거가 아니며720/600/CPU/RAM 기준을 늘리지 않는다. 같은 실행기로 미실행90을 계속 진행한다. Git/Review/Cargo/build·설치·원격push·SQL·한글 GUI·접근허용·Defender/WSL/OS 설정 변경 없음. 목표 범위와 완료 기준은 축소하지 않았다.
