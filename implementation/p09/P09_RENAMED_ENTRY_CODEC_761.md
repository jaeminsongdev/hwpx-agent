> 현재 기준(2026-10-26): [761 실물8종 및 후속 제품 검증763~767](P09_RENAMED_NATIVE_READBACK_763_767.md) 완료. 이름변경 초기/저장/재열기24파일＋후보8의 제품판정과24쪽 픽셀 일치 확인. 기존 통과 실물 시험 재실행0. 다음은 [768 실제 책갈피 커서16건](P09_BOOKMARK_CURSOR_768_RUNBOOK.md)이며 코드772 준비 검증 완료·실물 NOT_RUN. 새 외부 명령1회 안내 후 사용자 요청대로 목표 일시정지. 링크 활성화/일반flow/local host·지속출력·현재head는 미수용. P09/A12/A13 OPEN·31묶음/65기능·158/249·next165·새P10 미시작. 아래는 이전 이력이다.

# 755 실행 전 증거 읽기 오류 수정761~762

**외부761 실행 대기 / NOT_RUN**. 사용자 요청대로 새 명령을 안내한 뒤 목표를 일시정지한다.

## 확인된 원인과 변경

755 결과는 FAILED755_BLOCK_PRODUCT_CAPTURE / XREF_LOSSLESS610_ENVELOPE다. 코드760 증거는 prepared690 XZ 형식으로 저장됐지만 실행기의 load_code가 legacy DEFLATE reader를 호출했다. 첫파일을 읽다가 중단됐으며 fresh_inputs=1, claim=false, Native/사례 실행0, cleanup=true다. 자원 보호 중단이 아니다.

실패 receipt1889bytes/SHA256 ec9326440f4915e60b83be1ee0b5966a6beaba824ffcd8956c25d0fc36036a45와 기존755 코드/760 증거를 그대로 보존했다. 새761 실행기는 코드762를 XZ reader로, 제품754는 원래 legacy reader로 명시적으로 읽는다. 형식을 자동 추측하거나 다른 형식으로 재시도하지 않는다. XZ reader에도 원래 자원 checkpoint를 전달한다.

새 파일은 run_prepared_bookmark_native761.py, tests/test_renamed_entry761.py, verify_renamed_entry762.py다. Native worker/시작/CPU·RAM 보호/통신/세션 종료/16체크포인트 코드는 변경하지 않았다. 기존755 worker와 출력슬롯은 Native가 한 번도 실행되지 않았으므로 이 새761 시도에서 처음 사용한다. 외부 결과/claim/공지/forensic/scratch는761로 분리해 실패755를 덮어쓰지 않는다.

## 검증

- 증거: implementation/p09/evidence/p09-361-renamed-bookmark762-code001.v1.json
- 상태: QUALIFIED762_RENAMED_ENTRY_CODEC_RETAINED760_NOT_NATIVE
- 크기116501bytes / SHA256 4912f86a4fb67f4716753540c4a52d4272ec448a58798b5c93cef666f2cc4873.
- 신규12검사: 실제760 XZ에 옛 decoder가 실패함을 재현, 실행기의 올바른 reader/전체pin 확인,754 legacy 형식 유지, 잘못된 형식/profile/hash 거부, 원래 상태/READY/closure/원본변경 검사 유지, 자원 stop 전파, 전체 변경범위/미실행 namespace 확인.
- 실제 entry.load_code 함수에 새 코드 증거 봉투와 보유 reader를 넣어 전 경로를 확인했다. 옛27검사와 실제 READY 차단은760의 정확한 입력/코드가 현재도 같음을 확인해 보존했으며 재실행하지 않았다. 이번 실제 READY/Native/사례0.
- source1319/final1319,shell final1,cleanup=true,449표본,225.282초. **시스템 CPU 표본 최고75%, 가용RAM 최저27.8780%**. 검증 프로세스만의 CPU 사용률로 해석하지 않는다. 자원 보호 중단0.

## 다음 실행

새 이름변경 파일8종: Page/BookmarkName/Content/Relative × hyperlink false/true. initial/saved/reopened HWPX와 모든쪽 BMP를 수집한다. 기존684/690의 통과 시험은 반복하지 않는다. 링크 클릭/cursor 이동, SDK 삽입/refresh, 공개 출력/head 채택, 의미/Gate 수용은 이 수집에 포함하지 않는다.

원래 논리CPU2(mask4)·BelowNormal·CPU/RAM/commit95%·준비15초/작업10초/구간600초/전체1800초/drain45초·정확한owner 검증을 유지한다. Codex 상위 Job 제약 때문에 별도로 연 외부 PowerShell에서 한 번 실행한다. 관리자 권한은 필요 없고 접근 허용 창이 나오면 사용자가 눌러야 한다.

    & (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_prepared_bookmark_native761.py' --execute-renamed-eight-once

마지막 JSON을 전달한다. 오류/cleanup=false/보호중단이면 같은 명령을 다시 실행하지 않고 원본 증거와 관련 코드를 점검한다. **755 명령은 다시 실행하지 않는다.**

현재 제품754 및 Native693 수용 범위를 유지한다. 실제 의미/필수Native cursor·링크·이름변경 표시/저장/Saved extent·필요flow/local host/지속출력/현재head 및 P09 Gate는 아직 미완료다. P09/A12/A13 OPEN,31묶음/65기능,158/249,next165,새P10 미시작.

문서 원본9개는 source-archive/p361-renamed-entry762-docs/에 보존했다.
