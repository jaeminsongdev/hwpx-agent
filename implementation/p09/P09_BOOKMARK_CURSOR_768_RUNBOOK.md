> 현재 기준(2026-10-26): [768 본문읽기 실패 수정773~775](P09_CURSOR_TEXT_FIX_773.md) 완료. 768은 첫사례의 이동전 본문읽기에서실패했고 완료사례0·cleanup=true·자원보호중단0이다. 실패/코드원본을보존하고 전체문서옵션빈값/선택블록saveblock으로분리했다. 반환형식·길이·SHA 진단과잘못된반환시이동전거부를추가했다. 코드774의구문5＋Python8＋PS13 및실제READY차단/entry읽기통과·source1424/1424·cleanup=true·Native0. 새773은실물NOT_RUN이며외부1회실행대기. 사용자최신요청에따라이번오류정리만마무리하고목표일시정지하며별도속도개선작업은시작하지않는다. 최신제품766·P09/A12/A13 OPEN·31묶음/65기능·158/249·next165·새P10미시작. 아래는이전이력이다.

# 기존파일8쌍의 직접 책갈피커서768 실행안내

**현재: 코드 준비 완료 / 실물 NOT_RUN / 외부1회 실행 대기.** 사용자 요청에 따라 이 명령 안내 후 목표를 일시정지한다.

## 새로 확인하는 것

761의 저장·재열기 시험은 완료됐고 재실행하지 않는다. 이번에는 기존 Native initial8파일과 reopened8파일을 각각 독립적인 한글 세션에서 열어, 설치된 typed HBookMark.name/type/Command를 사용한 **Bookmark Command=1 직접이동**을16번 확인한다. 새 책갈피 생성·SaveAs·이미지 재생산·필드삽입/새로고침·공개출력/head 채택은 없다.

이것은 F11 연결대상의 실제한글커서 근거를 얻는 지원검증이다. 현재상호참조 필드 자체의 링크를 클릭/활성화하는 시험은 아니며 P11 전체책갈피기능 또는 P09 Gate 수용이 아니다. 링크 on/off 별 source해석 결과는766에 별도로 보존한다.

현재 문단origin을 Native GetPosBySet으로 직접 읽는다. 고정+16을 넣지 않는다. 한 번의 GetDefault/typed readback/Execute 이후 두 개의 GetSelectedPosBySet 결과6좌표가 정확히같고, source문단/선택길이/선택텍스트 SHA와 전체TEXT 전후SHA가 일치해야 한다. 실패 시 다른 API로 대체하거나 재시도하지 않는다. 원본파일 SHA·현재문서/정확한owner·독립세션/종료경계를 유지한다.

호환된 기존16체크포인트 이름의 saved/image 등은 이 경로에서 자원 경계 식별자일 뿐이며 저장/이미지 작업을 호출하지 않는다. trace는 SaveAs_invoked=false와 direct_bookmark_cursor_only=true를 따로 기록한다.

## 코드 검증과 수정 이력

증거: implementation/p09/evidence/p09-361-bookmark-cursor772-code001.v1.json,134607bytes/SHA256 e031368b1ead123659e19852a5637a2a3df763df714b33f9c883c2059bc73898.
상태: QUALIFIED772_BOOKMARK_CURSOR_SYNTAX_FIRST_RETAINED15_AND_READY_DENIAL_NOT_NATIVE.

- 구문5파일을 **전체입력대조 전에** 검사한다. 현재5개 모두 통과.
- PS 동작/거부/실제junction 출력부모 거부11개 통과. 타입/선택실패·다른텍스트·본문변경은 거부하며 Native 실행0.
- 770의 Python15 성공관측은 정확한코드/입력과 아카이브를 재결속해 유지했다. 재실행하지 않았고770 실패묶음을 통과로 승격하지 않는다.
- 새 실제 worker READY1회를 거부했고 사례0·한글0·완전정리를 확인했다. entry.load_code의 실제XZ 읽기경로도 확인했다.
- source1408/final1408,shell final1,cleanup=true,639표본,320.453초. 시스템CPU최고65.43%,가용RAM최저27.5456%,보호중단0.
- 770은 PS 출력의 JSON 해석오류,771은 기록개선 후 query script의 Windows PowerShell 구문오류로 확인됐다. 두 실패와 정확한변경전소스를 source-archive/p361-bookmark-cursor770-001/ 및771-001/에 보존했다. 줄바꿈 앞 -and를 호환되는표현으로 고쳤으며 조건/명령/선택요건은 바꾸지 않았다.
- 출력폴더 조상 reparse 거부를 원래수준으로 유지하고 두번째입력의고정경로/해시도 PS에서 검사한다. 검사과정의 실패시 exit/hash/구조화된진단을 JSON 파싱보다 먼저 보존한다. 전체로그/문서값은 출력하지 않는다.

## 실행

원래 단일논리CPU2(mask4)/BelowNormal/CPU·RAM·commit95% 보호, 시작준비15초/Native작업10초/구간600초/전체1800초/drain45초 및 정확한PID·birth·owner검사를 유지한다. Codex 상위 Job 제약 때문에 **별도로 연 외부 PowerShell**에서 실행한다. 관리자권한은 필요 없고 접근허용 창이 나타나면 사용자가 눌러야 한다.

    & (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_prepared_bookmark_native768.py' --execute-bookmark-cursor-eight-once

끝나면 마지막 JSON을 전달한다. 같은명령을 다시 실행하지 않는다. 보호중단/오류/cleanup=false면 먼저 증거와 관련코드를 점검한다. 761·755 및 과거Native 시험 재실행은 포함하지 않는다.
