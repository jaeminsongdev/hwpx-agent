> 현재 기준(2026-10-26): [755 증거 읽기 오류 수정761~762](P09_RENAMED_ENTRY_CODEC_761.md) 완료. 755는 XZ 코드를 legacy DEFLATE reader로 읽어 첫파일에서 실패했으며 claim/한글/사례0·cleanup=true였다. 실패와 기존 실행기 보존. 새761은 코드XZ/제품754 legacy decoder를 명시적으로 분리한다. 신규12검사＋실제 entry.load_code 경로 통과·기존27/READY 재실행0·source1319/1319·shell1·cleanup=true·guard449·시스템CPU최고75%·가용RAM최저27.8780%·보호중단0. 새8종은 아직 미실행이며 별도 외부 PowerShell의761명령1회를 기다린다. 사용자 요청대로 안내 후 목표 일시정지. 최신 제품754·실물의미/링크/cursor/host/출력/head 미수용·P09/A12/A13 OPEN·31묶음/65기능·158/249·next165·새P10 미시작. 아래는 이전 이력이다.

# 이름변경 새8종 Native755 실행 준비

**외부 실행 대기 / NOT_RUN**. 명령 안내 후 사용자 요청대로 목표를 일시정지한다. 최신 제품 검증754·P09/A12/A13 OPEN은 유지한다.

## 실행 범위

742가 생성한 이름변경 후보8개를 변경 없이 읽는다. 표시4종(Page, BookmarkName, Content, Relative) × hyperlink false/true다. 기존684/690 입력/실행을 반복하지 않는다.

각 사례의 initial → saved → fresh-session reopened HWPX와 각 단계 전체 페이지 BMP를 수집한다. Saved 이미지 수집 전후 saved 원본을 결속하고, 저장/재열기 세션의 정확한 owner/PID/생성 시각/종료 경계를 보존한다. 단계별1~8쪽의 완전한 목록이어야 한다. 링크 클릭/cursor 이동, SDK 삽입/새로고침, 공개 출력/head 채택은 수행하지 않는다. 수집 성공은 의미 또는 P09 Gate 수용이 아니다.

## 준비 검증

- 증거: implementation/p09/evidence/p09-361-renamed-bookmark760-code001.v1.json
- 상태: QUALIFIED760_RENAMED_EIGHT_SAVED_RENDER_CODE_READY_DENIAL_NOT_NATIVE
- 크기120475bytes, SHA256 213634045eb75100c3ed92963a88ad4ef8c25bc5b6c46937185a3660a7da7972.
- Python21＋PowerShell6 신규검사 통과. 실제 worker READY1회 거부, 사례0/한글0/정리완료.
- source1314/final1314, shell final1, cleanup=true, 자원453표본,227.015초. CPU최고15.83%, 가용RAM최저38.7891%, 보호중단0.
- Manifest: implementation/p09/evidence/p09-361-renamed-bookmark755-prepared-batch.v1.json;3239bytes/SHA256 6c329d7be60765b693fa71bfbd8a77f59bfadc0d1498794664b7b0d260a318c8.
- 최초759는 변경된 제품 Rust까지 과거692 해시와 대조해 모델 실행 전에 실패했다. 원본 실패와 정확한 코드는 source-archive/p361-renamed-bookmark759-001/에 보존했다. 760은 현재 제품 입력을754로, 공유 Native 시작/보호/통신/종료 코드를692로 각각 결속한다. 과거 실패를 통과로 바꾸지 않는다.

## 보호 및 실행

논리CPU2(mask4)·BelowNormal·기존 CPU 및 RAM/commit95% 보호 유지. 시작15초/실제 Native 작업10초/구간600초/전체1800초/drain45초 및 정확한 owner 검증을 유지한다. 자동 재시도와 기존 증거 덮어쓰기는 없다.

Codex 상위 Job 제약 때문에 별도로 연 외부 PowerShell에서 실행한다. 관리자 권한은 필요 없으며 접근 허용 창이 나타나면 사용자가 눌러야 한다.

한 번 실행:

    & (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_prepared_bookmark_native755.py' --execute-renamed-eight-once

종료 후 마지막 JSON을 전달한다. 오류/cleanup=false/보호중단 시 같은 명령을 다시 실행하지 않고 증거와 코드를 점검한다.

## 남은 범위

수집 후 이름변경 표시/저장/재열기 및 Saved extent 판정, 필수 Native 링크/cursor, 필요한 대상/아래/다중쪽 flow, 실제 local host/지속 출력/head 채택, 공식 대기열과 P09 기능/Gate 마감은 미완료다. 전체 원장은 P09_SCOPE_AND_REMAINING.v1.json. 31묶음/65기능은 원자 항목수나 완료율이 아니며 공식249는158수용/91대기/next165 유지.

변경 전8개 문서는 source-archive/p361-renamed-bookmark760-docs/에 보존했다.
