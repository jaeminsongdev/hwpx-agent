> 후속 현재 상태: 684 명령은 이미 소비됐고7번에서 정리 한도 오류로 실패했다. 다시 실행하지 않는다. 완료6종은 보존688로 재확인했고, 남은7~8번의 새690 명령과 자격692는 [복구 인계](P09_BLOCK_NATIVE_TAIL_RECOVERY_688_692.md)를 따른다. 아래는 원래 준비 이력이다.

# P09 블록 책갈피 제품 파일 8종과 새 Native 묶음 준비

2026-10-25. Native670 원본 성공과680 제품 작성 검증을 잇는다. P09/A12/A13은 OPEN, 공식249는158수용·91대기·next165, 잔여31개 closure 묶음/65기능이다. 아래 준비는 전체 F11/P09 완료가 아니다.

## 제품 파일과 보존

`p09_block_bookmark_candidates681` 일반 example은 실제 stored candidate API로 Page/BookmarkName/Content/RelativePosition 각각 hyperlink false/true를 작성했다. 실제680과 같은 service 클래스를 사용하지만 repositories/scanner/commits는 메모리 fixture다. 실제 issuer/DB/등록/CAS/작업 실행/결과 채택을 검증한 것은 아니다.

고정 private 폴더 `implementation/p09/evidence/private/p09-361-block-bookmark681-prepared001`에는 파생 `source.hwpx` 1개와 `case-01.hwpx`~`case-08.hwpx` 8개가 있다. 원본670은 수정하지 않았다. 별도 plain-run 문단을 추가한 source는64,944B이며 생성 후보는65,899~65,905B다. source와 후보 모두 기존8블록 시작/끝을 보존하고 후보에는 CROSSREF 한 쌍만 추가한다. 다른 part payload와 source metadata/head를 보존하며 기존 표시 캐시는 계산·갱신된 결과로 취급하지 않는다.

682는 build와 생성 호출이 각각 성공한 뒤, 옛 POINT 준비 profile에서 가져온64KiB 출력 조건 때문에 실패했다. 실패 영수증·당시 code·생성8파일을 보존했다. 683은 원래 작성기/Native port의4MiB 한도와 동일한 준비 검사를 적용해 기존 생성 결과만 재감사했다. build/생성/Native는 재실행하지 않았다. 다른 part payload,16개 기존 fieldBegin/End, 새 CROSSREF Command SHA, source/candidate SHA, metadata/head 불변을 확인했다.

- 성공 영수증: `evidence/p09-361-block-bookmark681-recovery683.v1.json`, SHA `658c83946a18c0bd3518ff75716eb4c35abaf59b26fcdd211c00bcf3662b79d2`.
- source915/915, compiled2final, output9final, cleanup=true;135.437초, CPU최고26.42%, 가용RAM최저52.8541%.
- 준비 manifest: `evidence/p09-361-block-bookmark681-prepared-batch.v1.json`,3,948B, SHA `bec2b5d3a244c5e7975a5b1c904d8f5ea631bf9e3679f57ea70fac474500fb13`.
- 682 실패는 FAILED로 유지한다. 이전680의26조건과 이전 Native/249를 반복하지 않았다.

## 새684 한글 실행 경계

소비된631/670은 수정하지 않는다. 새684 namespace는 준비된8제품 파일을 열고 initial/saved HWPX·직접 BMP를 만든 뒤, 독립 reopen 세션으로 saved 파일을 열어 reopened HWPX·직접 BMP를 만든다. SDK 삽입/필드 강제 갱신/문서 원본 덮어쓰기/결과 채택을 하지 않는다.

원래 limited Job, 1코어·낮은 우선순위, CPU/RAM/commit95% 보호, 현재 signed Python/한글/x86 shell 이미지, 정확한 PID/생성 시각/owner, 입력 lease와 fresh/final SHA, 새 세션과 같은 실행의 handoff, 제품10초 제한, section600초/전체1800초, 실패 latch/no retry/no force kill를 유지한다. 각 사례가 입력과2개 owner를 완전히 닫아야 다음 사례로 넘어간다. Rust/과거 이력 전체는 묶음 시작·최종에 확인하고 사례별 반복 경로에는 현재 실행 code/images와9개 입력만 둔다.

8종은 READY1 + 8×(checkpoint16+admission2+close2+finish1) + RESULT1 =170프레임이다. 새 통신 profile은170프레임과 EOF 읽기를 받도록171회 bounded read와 합계64KiB를 사용한다. 개별4097B/응답4096B/stderr4096B/queue8/원래 guard·cleanup 순서는 유지한다. 실제 in-memory transport170프레임·초과 단일 프레임 거부 검사를 포함한다. 새 통신 profile만 변경하며 소비된603/631 코드는 보존한다.

최종 게시에는 기존632의 무손실 XZ 경로를 새684 profile로 사용한다. raw4MiB/tree/depth/compressed180,000B/published256KiB 한도와 전체 byte round trip을 유지하며, 먼저 원시 metadata spool을 저장한다. 게시 형식 통과가 Native 의미 PASS는 아니다.

## 준비 검사 이력

685의20조건 중18개가 통과했다. 새 PS 복제 파일 끝의 LF 차이와 source pin 잔여 위치 때문에2개 projection 비교가 실패했다. 실패 원본을 보존했다. 686은 실패한2개만 실행해 worker 비교1개를 통과했고, 마지막 원본 검사에 남아 있던 옛 source SHA를 발견했다. 시작·최종의2개 source pin을 같은681 파생 source SHA에 결속했다. 687은 통과한19개를 입력/본문 동일성으로 유지하며 실패한1개와 아직 실행하지 않은 PS14모형·실제 READY 거부를 검사한다. 한글을 시작하는 release는 READY 검사에서 보내지 않는다.

687 자격 검사는 `QUALIFIED687_BLOCK_EIGHT_CODE_AND_REAL_READY_DENIAL_NOT_NATIVE`로 통과했다. 원래20모형 중18개(685)·추가1개(686)를 정확한 입력/본문으로 유지했고, 실패한source pin 비교1개(687)·새 PS14모형은 현재 실행해 통과했다. 총34조건이며, 실제 worker READY1프레임에 거부 응답을 보내 planned8/completed0/retained owner0/exit2/cleanup=true를 확인했다. 한글 프로세스는 전후0이다. source972/972,128.797초, CPU최고30.11%·가용RAM최저49.5148%·cleanup=true다.

자격 영수증은 `evidence/p09-361-prepared-bookmark687-code001.v1.json` 82,702B, SHA `778af92a7b33701f2881e19f896cf9dd617c109dfb6d7330ea34c5a6afd76e88`이다. 685/686의 실패는 그대로 보존한다.

684의 현재 Codex caller 사전검사는 `OBSERVED684_CURRENT_PREREQUISITES_NOT_NATIVE_OR_SESSION`로 완료했다. native 실행 파일/등록/원래 자원 정책/no preexisting Hwp는 true, `caller_lifecycle_native_safe`만 false다. process/COM/document/permission dialog/claim/Native8은 모두 false다. source974/974, cleanup=true,139.344초, CPU최고24.02%·가용RAM최저49.8898%다. 영수증은 `evidence/p09-361-prepared-bookmark684-inspection001.v1.json`,72,916B, SHA `02e9f1e4bcb9b5e94903ac64fbaf0526bca10df41cd4c0e884bb8765329261c9`이다. Codex 상위 종료 정책을 우회해 분리 실행하지 않는다.

## 외부 실행과 목표 일시정지

사용자가 별도로 연 PowerShell에서 아래 명령을 **한 번만** 실행한다. 관리자 권한은 필요 없다. 현재 session 자격에 성공한 경우에만 새684의8종을 진행하고, 실패하면 원본 결과를 보존하며 자동 재시도하지 않는다. 접근 허용 창이 나오면 사용자가 직접 누른다. 중간 `NATIVE_WORKER_RESULT_RECORDED_BEFORE_CLEANUP`은 최종 결과가 아니며 마지막 JSON과 PowerShell 프롬프트 복귀를 확인한다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_prepared_bookmark_native684.py' --execute-block-eight-once
```

실제684 Native/claim은 아직 NOT_RUN/미생성이다. 사용자의 “외부 명령이 필요하면 명령 전달 후 정지” 조건에 따라 목표를 PAUSED로 인계한다. 실행 결과가 오면 같은 명령을 다시 실행하지 말고 영수증·원시 spool·실제 산출물을 먼저 확인한다.

## 남은 범위

Native684의 실제8종 저장·독립 재열기/owner 정리/원본 최종 SHA, 실제 표시값과 target 의미 readback·시각 비교, 필요한 이동/이름 변경과 내부 hyperlink 탐색, 허용 backend와 공통 제품 경로 및 다른 P09 closure가 남는다. Native capture 성공만으로 Content 의미·F11/P09를 닫지 않는다. P10 새 구현은 시작하지 않는다.
