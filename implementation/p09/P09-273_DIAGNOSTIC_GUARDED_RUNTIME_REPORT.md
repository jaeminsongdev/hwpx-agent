# P273 실패 진단·기존 보호·metadata90 통합 실행

## 범위와 수용 경계

2026-10-09. 목표 ACTIVE. 접근허용·한글 UI·빌드·Git·설치·OS/Defender/WSL 설정 변경 없이 P09 검증 경로만 다룬다. 기존 실패와 통과 본체는 보존한다. P09/A12/A13 OPEN. 전체249·signed16·전체소스1470·historical67·제품 완료·프리즈 해결을 주장하지 않는다.

P273 actual run002 완료 후 실제 수용은 88/249, 다음 95번, 잔여 161(regular155+corpus6)이다. whole 재조정대기85, 독립source 마감대기0. 이는 개별 runtime subset 수용이며 P09 전체 완료율이 아니다. 기존 P26594 실패를 소급 통과로 바꾸지 않으며 새 실행의 완결된 증거로만 1개를 추가했다.

## 검토·수정

- P271 light run001: 생성자 단계에서 끝난 기존 P270 run001에 없는 `IO` 키를 필수처럼 읽어 KeyError. 본체 실행/선택/Native 전체 Frame 전에 FAILED. CPU STOP 없음, watcher 정리 확인. 실패 기록과 실행 소스를 수정하지 않았다.
- P272: 실제 실패에 `IO`가 없음을 명시적으로 검토하고 PASS·산출물·Job 정리를 발명하지 않는다. 이후 실패는 단계·예외 클래스·파일 basename/줄번호만 보존하고 비밀정보가 포함될 수 있는 예외 메시지는 제외한다. 사전검증 646개 통과.
- P272 actual run002: 기존 generic Reader가 canonical carrier를 검사·해제한 뒤 새 Reader가 해제된 값을 원 carrier SHA와 재비교하여 `P208_COMPACT_RUNTIME_EXACT_CANONICAL_BYTES_NOT_ONLY_DECLARED_STYLE`로 selection 단계 실패. 본체/Native 전체 Frame은 실행하지 않았고 수용은 0. 원 실패와 P272 사전검증/소스 보존.
- P273: 원 P255와 동일한 protected byte-bound raw JSON 경로를 사용하여 canonical carrier 검증·해제를 한 번 수행한다. 기존 fresh 읽기·identity·원 샘플러·모든 자원 제한 유지. 실제 carrier 검증 횟수와 byte drift 거부 계약을 추가했다. 오류 위치 보존은 재현만을 위한 불필요한 재실행을 줄이는 진단 개선이며 CPU/프리즈 개선의 실증은 아니다.

P269의 rejected-parent 원 기록 보존·원 600초/단계 계측, P270의 metadata 조기90 경고를 통합했다. 원95 경고/CPU98 연속4 STOP/Job6.25%/affinity1/BelowNormal/Native20/s/metadata32/s/binary1·other2MiB/s/IO600/metadata720/parent1200/두 전체 byte 읽기/전체 identity/핸들·Job 정리를 유지한다. 새 sampler/thread·자동 body 재시도·검사 생략·deadline 연장을 추가하지 않았다. 단일 다음 항목만 실행한다.

## P273 사전검증

원 계약558 + 현재 synthetic46 + 다음 synthetic46 = 650, 모두 통과. 원 입력1563 + 새 연결/보존 코드16 = 1579, extras112. 이 숫자는 실제 제품 본체 수용 수가 아니다. nominal 예측은 원600 제한 내일 뿐 완료 보장은 아니다.

IO406 reads, bound196/final fresh196, finished true, STOP null, watcher cleanup true. 기존 표본77개: 시스템 CPU 최대27.22%, own CPU 최대6.010391%, own private 최대58,757,120 bytes, 가용 RAM 최저36.495927%. 제품 본체/전체Native Frame은 사전검증에서 실행하지 않았다.

## 고정 증거

| 파일 | bytes | SHA256 |
| --- | ---: | --- |
| `tools/p09/resume_diagnostic_guarded_runtime_r3.py` | 33681 | `bb63c8268ba9e5549e9e848ddabc2818d679ce735b33f32e3cccb17802314a64` |
| `tools/p09/tests/test_diagnostic_guarded_runtime_r3.py` | 5945 | `5f62854da975611ba4b281713ccaad650b924a6b0d83996e679daf37e6315425` |
| `implementation/p09/evidence/locked-r07/p271-light-run001.v1.json` | 43372 | `618acd5d4647b83970dbd4dd6133896af51cc901a0096ab4e31b7bf1fe426120` |
| `implementation/p09/evidence/locked-r07/p272-light-run001.v1.json` | 39038 | `834092d05d380052564e901ad3256fbf62ff97ea261f5c623f472f8f4155c7ba` |
| `implementation/p09/evidence/locked-r07/p272-admission-run002.v1.json` | 75373 | `fe57558dbf6d1824c5a54534c302c87e6531dbeb1944396f726a69e1275a2f81` |
| `implementation/p09/evidence/locked-r07/p273-light-run001.v1.json` | 39522 | `a241c4dd90793a7c57dd03bfcc656ae9dc49933acc575229e3e3d30ca4826811` |

## 후속

P273 actual run002의 단일94 본체·전후 전체1579 byte·identity·Job/핸들 정리·fresh metadata·650계약이 닫혀 88/249로 수용했다. 다음95만 실행할 수 있으며 통과92·93·94 본체는 재실행하지 않는다. STOP/실패 시 원 기록을 보존하고 해당 단계의 관측값과 코드부터 검토한다.

## 실제94 결과와 시스템 경고

본체 `PASS_SCOPED_NOT_GATE`, exact1 test, elapsed272.07초. Frame COMMITTED/등록 해제, before와 after 각각1579개·119639255bytes. 원 held identity1579 regular/306 directory 확인. 원 잠금1885/duplicate3158 전부 정리, pathname byte 재열기0, 원 metadata 체크6928. Job active0, 소유 프로세스 트리 비움·원 정리 확인. 원600초 timing의 acquire완료98.913824초/parent완료371.034218초/release직전371.251173초, first original error null. 새로운 CPU/Native query/cleanup guard는 없음.

prep408 reads/bound197/fresh197, post2 reads/bound1/fresh1, 공유410<=720, 모두 finished. STOP null, watcher cleanup true. 관측801개: 시스템 CPU 최대100%, own CPU 최대6.096436%, own private 최대56283136bytes(약53.68MiB), 가용 RAM 최저21.661715%. Job peak private32.92MiB/CPU총14.969초/active0, 원 Job cap6.25%·affinity1·BelowNormal 유지.

시스템 CPU100% 표본3개에서는 own CPU0%였다. early90 경고1회/5개 pause windows/대기2.5초, 기존 Native95 pause0, metadata90 pause0. 이것은 시스템 전체 고부하가 관측됐다는 뜻이며 단독 원인/외부 프로세스/Defender/WSL/프리즈 해결의 증명이 아니다. 샘플 간 순간 peak의 부재도 보장하지 않는다. 외부 프로세스 종료·시스템 설정 변경은 하지 않았다.

수용 root `implementation/p09/evidence/locked-r07/p273-case-094-run002.v1.json`: bytes624020, SHA256 `4c8b5cb8db208be26487e966653747a2ad92c3bc37d1c5268047957b6b166eb5`. 본체 `implementation/p09/evidence/locked-r07/cases/p273-case-094-run002.json`: bytes190211, SHA256 `aa18a99412c8546d35b70142ecf87ec097faaf328daebaee2684e2a4f6d7171e`.

문서 r111은 동일 prefix를 두 상태 문서에 추가하며 r110 원문 byte suffix와 `implementation/p09/evidence/runtime-progress-r110/`의 SHA 일치 원본을 보존한다. 문서 갱신은 source/body 재실행·전체 Gate 수용을 뜻하지 않는다.
