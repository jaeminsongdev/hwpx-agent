# P09 P255~P256 불변 실행기의 실제84~87과 runtime-r104

2026-10-09. 목표 active. P09·A12·A13 OPEN. 원 STOP/FAILED 보존. PC 프리즈 원인·해결 미확정.

## 실제 결과와 경계

runtime 수용81/249 · 잔여168(일반162+corpus6) · 미closing후보0 · 다음index88 · whole재조정대기78.

이번 회차는 미실행84~87만 각각 한 번 실행해 원 판정기로 수용했다. 통과 본문 재실행 없음. 불변 P255 코드·테스트와 기존450 실행 계약을 그대로 재사용했으며 CPU STOP나 새 코드 수리는 없었다. 매 실행의450은 계약 실행 수이며 네 실행을 합쳐 새로운 고유 계약1800개라고 주장하지 않는다.

- 84: actual_import::formula_policy_registration::missing_duplicate_extra_non_formula_empty_and_oversized_decisions_fail_before_ingest
- 85: actual_import::formula_policy_registration::read_only_exhausted_generation_and_no_formula_source_cannot_create_policy
- 86: actual_import::formula_policy_registration::repository_denial_unknown_ack_and_all_15_reply_mismatches_never_retry_or_erase_evidence
- 87: actual_import::formula_policy_registration::sorted_generation_cas_and_latest_revocation_flow_keep_old_products_unusable

84는 malformed 결정의 ingest 전 거부,85는 읽기 전용·소진 generation·비수식 source의 정책 생성 거부,86은 repository 거부/unknown ack/15 reply mismatch에서 재시도·증거 삭제 금지,87은 generation CAS·최신 철회로 이전 제품 재사용 금지를 확인한다.

각 fixed EXE/fixture/repository double 제품 CLI 경로의 exact1이며 실제 SQL·생산 issuer·한글 UI·전체249/P09 Gate 수용이 아니다. P239 실제 pre-GO CPU STOP 경계 NOT_RUN. UI 접근허용이나 의도적인 CPU stress는 실행하지 않았다.

## 원 검사·자원 관측

| 실제 index | 원 parent초 | 준비+후속읽기 / bound=finalfresh / 준비 논리bytes | 전체CPUmax / 자체CPUmax % | private최대bytes / 가용RAM최소 % | JobCPU초 / peakMiB |
|---|---|---|---|---|---|
| 84 | 253.97 | 256+2 / 122 / 28469994 | 40.62 / 5.800262 | 55189504 / 29.316432 | 0.594 / 23.11 |
| 85 | 251.79 | 260+2 / 124 / 30011824 | 45.27 / 5.752212 | 55250944 / 31.953234 | 0.719 / 26.97 |
| 86 | 267.19 | 264+2 / 126 / 31550614 | 54.55 / 5.887743 | 56434688 / 35.944532 | 14.156 / 26.23 |
| 87 | 257.74 | 268+2 / 128 / 33105612 | 36.52 / 5.824151 | 54759424 / 36.674609 | 7.203 / 34.95 |

네 실행 모두 metadata finished/cleanup true/STOP없음.95%이상 경고표본0/지속98%4연속0/Native pressure0. 원 Job 종료active0/owned_tree_empty를 확인했다. 검증 부모 private 최대56434688bytes(약53.82MiB), Job peak 최대34.95MiB. 기존 관측 표본의 결과이며 물리 PC의 모든 순간이나 외부 PID 원인을 입증하지 않는다.

각 전후1545입력 각119242806bytes/COMMITTED/등록해제. 잠금1851·복제3090 모두 opened=closed, byte identity3090. 잔여·close 실패·reader/stream·별도 경로 byte 재열기·probe0. Native20회/s/4941예약/no-idle-burst, metadata32회/s, EXE1MiB/s·기타2MiB/s 유지. 원 CPU/RAM/Job limits·원600초 및본문1200초·원 두 실제 전체 byte 읽기·identity·정리를 유지했다. 원600초·CPU/RAM 기준은 변경하지 않음.

수용됐던82·83은 실행하지 않고 원 record/root/body·SHA/length만 새 문서 snapshot에서 소비한다. 기존 실패·수용 소스·원본/private 자료를 수정/삭제하지 않았다. r102 checkpoint95 및 원 baseline의 compiled249·1470 manifest·Rust785 검사, known 실패 semantic 검사와 현재 namespace 미검토 실패 차단을 유지한다. 과거 모든 receipt의 recursive fresh 재생과 같은 범위라고 주장하지 않으며 whole/historical67/full249/signed16/Gate 재조정은 여전히 미완료다.

## 전체 목표 재확인

초기 요청의 P09 소유46개와 P11 deferred7개, 정확한 Hangul2020 build11.0.0.9136/x86/ko-KR, 실제 package/readback/save-reopen/한글/render/differential 및 phase Gate 조건을 다시 확인했다. 현 live conformance행렬은53개/P09소유46/P11deferred7/component covered46/direct implemented11/green0이며 actual HWPX·Hangul·automation·render·differential은0이다. 이 행렬을 CLI 통과 숫자로 변경하지 않았다.

ROADMAP_STATUS.yaml의 상위 current_phase는P08/updated_at2026-09-14인 별도 이전 snapshot이다. 이 문서와의 최종 phase 재조정 역시 완료가 아니다. P00~P08·P11 소유권·사용자 변경을 보존했고 P10 새 구현에 진입하지 않았다. PLANS는 이후 사용자 삭제 지시가 우선하며 복원하지 않는다. 최근 Git 다중 실행/프리즈 제약 때문에 이 회차에서는 Git/Review/Cargo/build를 실행하지 않았다.

## Exact 증거

이전 문서 receipt: implementation/p09/evidence/locked-r07/p256-checkpoint-metadata-status-doc-r0103-run02.v1.json
50207bytes / d13b468052b1a3bf72ff4cf55ab487d2cf332ea2ebf8abe9dd48094f2d3b7716.

원 checkpoint: p254-generic-metadata-status-doc-r0102-run01.v1.json
40000bytes / f394aded5f736eae6b46ccb8885d5e46e99a845b7135849126f526d366b49e9e.

원 actual81 anchor: p253-case-081-run003.v1.json
615984bytes / 22d57ddd87d213c6d41c39c536c5d83e2fec295ea34d110540f5406284b2a246.

아래 상대 기준 implementation/p09/evidence/locked-r07/.82·83은 증거 소비만 했으며 새 실행하지 않았다.

| Root/body | bytes | SHA256 |
|---|---|---|
| cases/p255-case-082-run002.json | 180883 | 2d7d0fd4a8f8353c6f1567674cc34d2ad975f1969ee9e15c350118a1848212ea |
| cases/p255-case-083-run003.json | 186103 | 9d80988e819700b75396ac98acb4a8497feab253b37c005e65eaef4627b65d59 |
| p255-case-082-run002.v1.json | 587528 | ed45ccea9cf1908178a26e4150176047c69e0b39801f49c3af2d703b68e79698 |
| p255-case-083-run003.v1.json | 590216 | d993f764dfbccb017a85cdfcdcc559af3a6645fff70b12c177e2e06d4b863a9f |
| p255-case-084-run004.v1.json | 589176 | 6af609b2f2293f1a4a1939ee9407a2f466d2d737ec35d279b3b83b75276a6204 |
| cases/p255-case-084-run004.json | 181739 | 1e4a8dceed6cad18d98ce26a7303d6dfc06e6072a20c9d9d07fc7e0ece368e80 |
| p255-case-085-run005.v1.json | 589008 | a767af5a97a20dd30bb8fc36cb6c4715a2007134b4ac598538b90f280acc88f5 |
| cases/p255-case-085-run005.json | 180387 | 4704df1035b8dbfc779c91b1d3d3ede41dc66013c4703eae2b24e6b8cea4d608 |
| p255-case-086-run006.v1.json | 590852 | 9eee6fffa7156149b868d4179cf4ea1c690e4a49766d08ce924551e2307df7d0 |
| cases/p255-case-086-run006.json | 186647 | 347b9b82ab5aabcf1aa0445d6935bf7ecc66f3af219c257dc91af47c87a4cec7 |
| p255-case-087-run007.v1.json | 590288 | 06f40a2ef211d132a18bb785cbb0f13a6b7efd7c097247ef06b23720741ffc1f |
| cases/p255-case-087-run007.json | 182731 | 2ec8ff7b92343e88e8a463873dc293f429b8cb33f498d55ffcf0b692d9abba82 |

## 문서와 다음 단계

새 문서 상태 snapshot/P256의 불변 원 anchor/progress/record와 문서14 계약, 모든 bound 입력 최종 fresh로 누적81수용을 확인한다. r103 상태 문서 두 개의 SHA/length exact 사본 runtime-progress-r103/과 현재 동일 prefix/원bytes suffix를 보존한다. 새로운 reporter/테스트/실행기를 복제하거나 수정하지 않았다.

실제88 NOT_RUN. 실제87 preparation268에 새 root/body 첫 읽기2+최종fresh2+원후속2를 더한 다음 shared274는720 이내 예상이다. 예상은 실제 검증이 아니며 같은 P255로 미실행88을 진행한다. CPU 보호 중단 시 자동 재시도 금지: 중단 단계·표본·관련 코드를 검토하고 안전한 최적화·검증 후 재개한다. 전체 목표와 Gate 기준은 축소하지 않았다. Git/Review/Cargo/build·원격push·SQL·한글 GUI·접근허용·Defender/WSL/OS 설정 변경 없음.
