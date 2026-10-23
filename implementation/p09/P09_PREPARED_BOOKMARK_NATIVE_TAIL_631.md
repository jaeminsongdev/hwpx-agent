# P09 631 — 중단630 분석·잔여6개 캡처 인계

> 현재631은 소비됐다. 캡처/정리/최종298/298을 완료했지만 게시 압축 한도에서 실패했고, [632~635 복구·필드 읽기 결과](P09_BOOKMARK_CAPTURE_RECOVERY_AND_READBACK_632_635.md)로 원자료를 byte-exact 복구했다. 책갈피8종 저장 후 필드 읽기 profile만 qualified이며 전체 F11/P09 PASS는 아니다. 아래 외부 명령은 재실행하지 않는다. 사용자 재개 지시로 이번 작업을 진행했으나 목표 API의 최신 상태는 PAUSED다. 제품 대상/의미·렌더·이름 변경 등은 다음 작업으로 남는다.

## 현재 판정

630 native001은 실패이며 cleanup=false 그대로 보존한다. 사례1·2는 각각 두 독립 세션의 캡처 반환·정확한 kernel producer·Job 정리·사례별4-reader fresh/final 경계를 갖고 있다. 631은 해당12개 파일의 현재 byte와 기존 실행 입력/이미지를 다시 결속해 **캡처 증거로만** 재사용한다. 필드 의미/렌더·F11·P09 PASS로 수용한 것이 아니다. 사례3의 반쪽 산출물도 보존하지만 재사용 판정에 넣지 않는다.

현재 기준은 [P09 범위·31묶음](P09_SCOPE_AND_REMAINING.md)이다. 공식249의158수용/91대기/next165, P09/A12/A13 OPEN, P10 새 구현 보류는 유지한다.

## 확인된 지연과 수정

- [630 실제 실패 영수증](evidence/p09-361-prepared-bookmark630-native001.v1.json), SHA256 `c50e6898cda51fa711f3bc0d82829200da68754cf211f382e8552dd122560a78`: 868.812초, 시스템 CPU 최고28.84%, 가용 RAM 최저42.1802%. CPU 보호 중단이 아니라 `KeyboardInterrupt`가 기록됐다.
- 마지막 요청은 source case3의 `create_reopen_session`이며 `crossref_qualified_batch.wait_exited_tree` 안에 있었다. 한글 root handle은 종료됐지만 같은 Job의 자식이 남으면 기존 함수는 50ms polling을 무기한 반복했고, handler 안에서 원 sampler·기한·상태 알림이 실행되지 않았다.
- 기존630과 공유 원본은 수정하지 않았다. 새631 host만 정확한 다음 retirement checkpoint 앞에서 root handle+같은 Job을 관찰한다. 200ms 간격으로 원 guard·Native Job·worker Job의 자원 검사를 유지하고 5초마다 알림/같은 Job의 PID·birth·허용된 실행 파일 분류를 기록한다. 경로/명령줄/문서 값은 출력하지 않는다.
- 새 작업 대기는45초에서 실패하며 다음 사례나 같은 사례를 자동 재시도하지 않는다. 그 뒤 **정리 대기**는 기존 비강제 종료 정책을 유지한다. 이는 강제 종료나45초 안의 최종 cleanup 보장이 아니다. cleanup 미확인은 실패 그대로 남는다.
- 약120~150초 지연이 PDF 출력 보조 프로세스 수명과 관련됐을 가능성은 있지만, 630에는 해당 자식의 이름이 없어 원인 확정은 불가능하다. 새631은 PDF `SaveAs`를 호출하지 않고 설치된 desktop `IHwpObject.CreatePageImage`로 모든 페이지를96DPI/24bit BMP로 직접 저장한다. 페이지 수1~8, 한 파일16MiB, 파일명·signature/DIB/pixel length·producer를 제한한다. HWPX 최초/저장/독립재열기 파일과 원본/입력 lease 검사는 유지한다.

BMP/GIF 지원은 [한컴 desktop Automation 안내](https://forum.developer.hancom.com/t/topic/1062)를 근거로 했다. [한컴 후속 안내](https://forum.developer.hancom.com/t/createpageimage/1861)는 PNG 미지원과 일부 문서의 잘림 문제를 다룬다. 따라서 BMP 생성·화면 완전성·PDF와의 시각적 동등성은 실제 실행 전 미검증이며, 이를 렌더 의미 PASS로 바꾸지 않는다. WebHwp의 다른 signature/PNG 계약은 사용하지 않는다.

## 검증 근거와 실패 보존

| 근거 | 범위·결과 |
| --- | --- |
| [code001](evidence/p09-361-prepared-bookmark631-code001.v1.json) | section 정책 복제 끝의 추가 빈 줄을 exact-body 검사에서 탐지. 모델1실패, Native0, cleanup=true. 정책 검사를 완화하지 않고 추가 줄을 제거했다. |
| [code002](evidence/p09-361-prepared-bookmark631-code002.v1.json) | 새 Python 계약14+PS/BMP 모델14 통과, 실제 설치 typelib의 두 선언 관측. ready 거부 검증기의 fresh-shell 인자에 callback 대신 pin을 전달한 오류로 실패. Native0·cleanup=true. 원본 보존. |
| [code003](evidence/p09-361-prepared-bookmark631-code003.v1.json) | 28조건의 변경 없는 source/실행 결과를 보존하고 실제 x86 새 worker의 READY **거부**만 다시 확인. Native 생성0, 문서 사례0, worker/query handle/Job cleanup=true. 297fresh/final297·57.500초·시스템 CPU 최고32.55%·가용 RAM 최저43.0970%. |

기존630의26조건과 현재 session worker의 상위 Job 거부 근거는 source byte 일치로 보존했으며 재실행하지 않았다. 631도 설치된 typelib SHA `abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9`에서 `PageCount` int getter와 `CreatePageImage` bool/5개 인자를 관측했다. 선언 관측/모델/READY 거부는 실제 문서 API 성공의 대체 근거가 아니다.

[게시된 entry reader 확인](evidence/p09-361-prepared-bookmark631-published-entry-check.v1.json)은 실제 `load_code`와8후보 검사를 Native 없이 실행했다. 248개 현재 실행 입력과50개 별도 이력/바깥 입력을298fresh/final298로 닫았다. 39.000초·시스템 CPU 최고21.98%·가용 RAM 최저45.0985%·cleanup=true다. code002에서28모델이 실행된 entry와 현재 entry의 차이는 code receipt 포인터 한 곳뿐임을 전체 본문 역변환으로 확인했다. 같은 모델·249·실제 제품은 다시 실행하지 않았다.

실패한 코드 세대의 source는 `source-archive/p361-prepared-bookmark631-code001/`, `...code002/`에, 이전 상태 문서는 `...631-docs/`에 보존했다. 630 원 실패·private forensic·원본·후보8개·부분 산출물은 삭제/덮어쓰기하지 않았다.

## 외부 PowerShell — 잔여6개 한 번만

Codex 상위 Job의 lifecycle을 우회하지 않으므로, 관리자가 아닌 **별도로 연 PowerShell**에서 아래 한 줄을 한 번 실행한다. 새631 claim이 없는 현재 세대만 가능하다. 현재 한글이 없어야 하며 접근 허용 창이 나오면 직접 눌러야 할 수 있다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_prepared_bookmark_native631.py' --execute-remaining-six-once
```

이 명령은 과거630 재실행이 아니다. 현재 입력/이미지/환경 확인 → 새 단발 claim → 같은 호출의 현재 세션 자격 → **원본 사례3~8**의 새 캡처 → 전체 최종 hash 순서다. 내부 ordinal1~6은 source case3~8이며 사용자 임의 case/path/retry 인수는 없다. 새 output 폴더는 `evidence/private/p09-361-prepared-bookmark631-native001-c03`~`c08`이다.

새 Native의 CPU/RAM/commit95%·1코어·낮은 우선순위·원 Job hard cap/메모리 분할·owner/window/birth·입력 lease·Native 작업 제한은 유지한다. 구간600초/전체1800초를 늘리지 않고 새6개에만 구간을 배정한다. 과거 이력은 묶음 시작/끝에서 확인하고 현재 실행 입력은 각 사례 전후에 확인한다. 다른 프로그램 종료/Defender/시스템 설정 변경은 없다.

`DRAIN631_SAME_NATIVE_TREE_WORK_GUARDED`는 새 작업 대기의 root/자식/CPU/RAM 상태다. `WAITING_SAME_OWNED_NATIVE_EXIT_NO_FORCE_KILL`와 `work_continuing:false`는 실패 후 정리 대기이며 진전/통과가 아니다. 오류 또는 정리 대기가 나오면 같은 명령을 다시 실행하지 말고 마지막 JSON을 전달한다.

모두 반환돼도 우선 `CAPTURED631...SEMANTICS_UNQUALIFIED`만 가능하다. 원 캡처2개의 PDF와 새6개의 BMP는 다른 매체이며 render diff는 별도 판정한다. 원630 전체 cleanup은 소급 변경하지 않는다. 최초 계산/보존·대상 결속/이동/이름 변경·다른 target family·필요 제품 경로와 F11 마감은 계속 남는다.

명령 인계 뒤 사용자의 정지 요청에 따라 목표를 PAUSED로 둔다. 자동 Native 실행·재시도·다음 목표 진행은 하지 않는다.
