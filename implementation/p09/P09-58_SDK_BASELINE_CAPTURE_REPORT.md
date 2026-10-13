# P09-58 현재 SDK baseline 수집 및 전체34 실행 대기열

2026-10-03. 이전 P57은 실제 renderer/component 구현과 과거3 PDF 회귀 검증을
완료한 진행 턴이었다. 이번 턴은 아직 없던 **현재 SDK native baseline 수집 경로**와
실제 전체34 대기열/actual trace-artifact 결합/current pair 소비를 구현했다.
사람의 `접근허용 띄우지 말고 딴거 해` 지시는 계속 적용하며 native 실행은 하지 않았다.

## 실제 구현

- 기존31-file P51 target에서15개, 기존 P22 SDK target에서2개를 읽어 complete17
  입력을 고정했다. HWPX 원본을 재생성/덮어쓰기하지 않았다. CLICK_HERE의 자동화
  원본2개와 SDK 기대 target2개는 서로 다른 SHA이며 이를 명시적으로 따로 결합했다.
- 새 owned-session 수집 코드는 source/harness/library/bundle/설치 EXE/DLL/security
  identity를 검사하고 SDK 문서를 그대로 Open→SaveAs HWPX/PDF→소유 서버 종료→
  새 서버에서 saved HWPX Open→새 HWPX/PDF 저장한다. source identity는 실패 및
  cleanup 뒤에도 검사한다. managed text/style/form setter는 이 기준 경로에 없다.
- HWND→PID/session/birth/EXE ownership을 Open 및 각 SaveAs 전에 확인한다. 소유권
  미확인 시 blanket Quit/kill을 하지 않는다. 실제 종료는 trace와 child exit/rootHwp에
  결합하며 partial/0byte output, failed ownership/source preservation은 보존한다.
- 단일 future queue는 SDK baseline17 다음 **원래 P56 full15+2 dispatcher 그대로**다.
  미래 실행 시 첫 activation 전에 실제34 preflight를 검사한다. native child를 접근
  허용 timeout으로 재시작하거나 강제 종료하지 않는다. 작은2/subset 배치가 없다.
- 새 actual binder는 엄격한 schema/typed claims/UTC/unique owners/도달 가능한
  artifact prefix/child exit를 실제 파일 hash/bytes/PDF header와 결합한다. 모든 expanded
  SDK package bytes도 검사하며 metadata/XML normalization 없이 drift를 유지한다.
- actual whole34 dispatch가 있는 경우 기존 P56 actual binder와 새17 baseline binder를
  연결하여 실제17 pair의 baseline stability/automation stability/saved differential/
  reopened differential을 기존 P57 full-page96/192 renderer로 진단한다. 전체 input은
  전후 다시 결합하고 실패/거부/불일치 case를 제외하지 않는다.

이 경로는 **SDK native baseline**이지 사람이 직접 편집한 독립 oracle이 아니다.
비교 코드가 있어도 아직 actual17 기준/PDF/complete34 native receipt는 없다.

## 실제 SOURCE 검증

| 증거 | 실제 결과 / 한계 |
| --- | --- |
| Python unit | 20 PASS, 원본 SDK17 전체 component comparator 포함; synthetic trace는 메모리 안에만 있음 |
| x86 PowerShell AST | 새2파일 syntax, owned library top-level은 함수 정의+StrictMode뿐; native body 미호출 |
| 새 실제 prefix |17개 모두 x86 STA에서 actual runner의 PreflightOnly 종료, COM/새 run directory 생성 전 |
| wrong hash child | bundle/library/self 해시3건 실제 exit1/거부, native boundary 전 |
| SOURCE publication | session33008 terminal exit0/PASS |
| 독립 전체 fresh | session19026 terminal exit0/PASS, tests/AST/new17 prefix/hash3/context를 실제 재실행 |
| 실제 current 조회 | session93386 exit0/NOT_RUN/0cases, partial baseline 또는 P56 단독 결과 승격 없음 |

source receipt: `implementation/p09/evidence/p09-58-sdk-baseline-capture.source.v1.json`,
24645 bytes, SHA256 `eeed077fb3fe2ea2ea258dacc1e2f1801f77e618a82064ebb20895d727af7d6e`.
8개 새 source pin에는 최초 실패 receipt도 포함한다.

문서 동기화 후 별도 integrity session9053도 exit0:8개 pin 일치/full34 native 폴더0,
baseline/P56 dispatch 및 current capsule 없음/Hwp0/10100-byte bundle exact를 확인했다.
새9개 source·문서와 PLANS의 scoped whitespace 검사도 PASS였다.

Git 공통 `*.ps1 text eol=crlf`는 두 새 LF source의 bytes를 바꿀 수 있어,
`.gitattributes`에 **이 두 파일만** `-text -eol whitespace=cr-at-eol` 예외를 추가했다.
기존 다른 규칙과 native source bytes는 변경하지 않았다. 별도 read-only Git check
chunk92b890에서 두 경로의 text/eol unset 및 `git hash-object --path`/`--no-filters`
blob 일치를 확인했다. stage/commit은 하지 않았다. 이것은 current source bytes의
Git 필터 보존 검사이지 P09 runtime/Gate 또는 Git 배포 완료가 아니다.
예외 추가 후 세 번째 independent whole fresh session58420도 exit0/PASS였고,
source receipt의24645 bytes/eeed077f SHA가 그대로 재현됐다. 선행 context도 변하지 않았다.

생성한 별도 입력 bundle은 native 증거가 아니다:
`implementation/p09/evidence/private/p09-58-sdk-baseline-plans-20261003-r01/capture-manifest.json`,
10100 bytes, SHA256 `4ecd2b934867e037b76772bcbd64d3b1aec593867b1d3b080d0ca714bf554903`.
이 한 파일에 full17 path/identity/hash만 담았으며 document values/styles를 넣지 않았다.

```powershell
python tools/p09/qualify_sdk_baseline_capture.py --verify
python tools/p09/qualify_sdk_baseline_capture.py --current
```

`--execute-native`는 지금 실행하지 않았으며 최신 사용자 지시 아래에서는 금지다.
허용 재개 시에도 현재 full34 admission 및 원본/프로세스0/unused attempts를 검사하고
한 번의 whole queue만 실행한다. old P56 standalone17/small CLICK_HERE2를 따로 실행하지 않는다.

## 최초 실패 보존과 수정

actual 첫 prefix는 command chunk9110ce에서 exit1이었다. 별도 진단13ffd2의
stderr403bytes/SHA `7ba3732658885c17c603142fa47aae304cfffe6e68185a9696ad34ea27ce5136`:
상위 `.Parent`는 native DirectoryInfo라 PSIsContainer note property가 없고 StrictMode가
이를 거부했다. 새 harness만 DirectoryInfo type으로 수정했다. reparse attribute 및
모든 ancestor 검사는 그대로 유지했다. 이후 actual17 prefix가 통과했다.
초기 source SHA/실패/진단 digest는 별도 `initial-prefix-failure.v1.json`에 보존했다.
원본 또는 오래된 source/실패/expectation을 변경하지 않았다. 전체 로그는 공개하지 않는다.

## source guard와 남은 실제 검증

새8 source callback은 baseline17의 각 case 전후와 전체 automation lane 전후에 검사한다.
원래 P56 lane 내부는 기존 P52/P55/P56 guard를 그대로 수행한다. 새8 callback을
원래 dispatcher 각 case 안에 주입/monkeypatch한 것은 아니다. policy의 activation
보호는 이 실제 구현 범위로 읽어야 하며 모든 source를 각 COM 호출마다 동적으로
attest했다고 주장하지 않는다. 실제 전체34 동적 보호/cleanup 동작은 아직 NOT_RUN이다.

Native COM/index correctness/HWND ownership/Close(false) semantics/dirty prompt/actual
save/reopen/package drift/managed-style result/render/direct differential/rollback 수락은
미검증이다. SOURCE 테스트의 fake PID/trace/PDF bytes는 actual native 증거가 아니다.
P57 renderer의 현재 populated native branch도 이번 SOURCE 턴에서 실제 실행하지 않았다.
원래920pixel mismatch 수정도 증명하지 않았다. Unsupported native/PDF scope와 signed
product path/CAS/CLI/전체46 reference coverage/Gate가 남아 있다. 34attempt는17pair이지
P09 전체46개 acceptance가 아니다.

고정 P48-P57 source/receipt/context, 기존75 native 파일, P55 plans/P51 candidates 및
P22 SDK source는 전후 identity 확인했다. 새 native attempt directory/trace/dispatch/
current evidence/Hwp server는 없다. registry/trust/security/dependency/원본 수정,
whole old preparation/ordinary suite 재실행, commit/push, P10 구현은 하지 않았다.

Goal ACTIVE/0green/P09 Gate open. 이번 source feature를 다시 wrapper로 감싸는 대신
다음 offline 작업은 남은 실제 P09 제품 경로 또는 기존 note/reference/native 의미
미구현 부분으로 진행해야 한다. 실제 권한 검증은 사람의 명시적 재개 전까지 실행하지 않는다.
