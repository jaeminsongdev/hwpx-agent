# P09 158번 실패 기록 보존 및 무손실 입력 표현 — r335

공식 승인151/249, 미완료98, 다음158, 현재generation개별46.
P09/A12/A13 OPEN. P10 새 구현0. 목표ACTIVE.
이번에는 제품 실행·입력 잠금·승인 증가가 없다.

## 확인한 현재 상태

관련P09 Python프로세스0과r334의원문서·원본실패003을확인했다.
잠금코드를읽어기존의조상경로중복순회제거,취득당1회open/inspect,실패시close,
14/s취득·20/s전체open·64회pacer진행상한을확인했다.
이번검토로비정상CPU의원인또는추가잠금코드수정필요를확정하지않았다.
원Native/자원보호코드및성공157/권위151/실패001002003은변경하지않았다.

## 다음 시도의 상속 비용

r690은원failed003바이트와독립STOP검토r688/source2를원guarded Reader로fresh읽었다.
원선언physical2611/258975696bytes의기존비용597.0661093575613초와원비용식이정확히일치했다.
실패003+독립검토+source2만추가하면2615개/599.4692257199969초.
다음controller/DATA/qualification/worker새증거는포함되지않았으므로완전한새GO모델이아니다.
원600초/60margin/15capture/decoder5/rates및scope를유지했다.
가벼운검토CPUmax20.9%·가용RAMmin68.21957%·fresh17/final17/cleanupTrue.

## 실패 역할을 보존하는 명시적 표현

원descriptor는현재case의기록을이전제품기록처럼변환하는것을거부한다.
새runtime_failed_receipt_projection_v1은현재158/run003의정확한실패pin과
r688의정확한독립검토·현재source를검증한경우에만별도의failed물리경로를허용한다.
성공·COMMITTED·제품실행·GO로승격하지않는다.
다른source/EXE/fixture/잘못된pin/다른case/boolean coercion/중복설치를거부한다.

새private source graph의descriptor dependency만확장하고원Projection/codec메서드와
Binding생성자code를보존한다. Binding representation은원메서드에위임한뒤
same_case_failed_receipt_provenance를명시적으로추가한다.
원namespace/defaultmodule은변경하지않았다.
후보manifest에서도실패pin/독립검토pin/실패역할/승격false가노출된다.

CODE9/r691:9/9 PASS·fresh12/final12·CPUmax20.77%·RAMmin69.11502%·cleanupTrue.
실제원본2209026bytes→921707bytes를메모리에서두번새로decode하여전체바이트일치를확인했다.
12개descriptor의semantic/physical후보투영에는기존11개를그대로포함했다.
원래실패가제품성공이었다고재해석하지않았다.

## 실제 별도 파일 생성

r692는원본/코드/STOP검토를fresh검증한후다른경로를exclusive생성했다.
원본:
implementation/p09/evidence/p09-361-case158-current-runtime-run003.v1.json
2209026bytes/SHAe93a86080ad9fce059fe8eba26aa4d0c0f343d0c2530677dd86340d52334e609

추가파일:
implementation/p09/evidence/p361-lossless-runtime-inputs/case158-runtime-run003.failed.envelope.v1.json
921707bytes/SHA7a0b8f967a6199730485547a4666605ad190ab4f48e7c817dc28a1e9c489bbb6

1287319bytes의표현감소이며원본을보존하므로디스크정리가아니라추가921707bytes의생성이다.
기존64KiB writer·2MiB/s write pacing·flush/fsync·원checkpoint·overwrite거부를재사용했다.
두메모리복원·실제출력fresh hash·전체최종hash확인.
CPUmax16.16%·RAMmin69.54774%·fresh17/final17·cleanupTrue.
파일생성은Native입력채택/제품PASS/PC프리즈해결증거가아니다.

## 기존 전체 manifest와의 연결

새manifest021/runtime_failed_receipt_manifest_v1은원manifest020의11쌍과
이실패1쌍을연결한다. 원producer/CODE/focus/source/원본과물리파일fresh검사를모두유지한다.
CODE4+실제전체상속admission/r693:4/4 PASS·12쌍·inherited semantic2536.
fresh84/final84·CPUmax25.87%·RAMmin68.87184%·cleanupTrue.
현재controller/worker/capsule/전체제품oracle/Native실행연결은NOT_RUN이다.
원manifest020/CODE24/입력scope를사후변경하지않았다.

## 다음 경계

새12쌍manifest를다음독립attempt의parent/worker/capsule/전체oracle에같은형식으로연결한다.
실패003의source pin과역할을보존하는새identity및완전한controller/DATA 비용을검증한다.
연결후전체사전검증과실제제품·Native/독립승인전151/249를늘리지않는다.
원scope제외·한도완화·성공157재실행·동일003덮어쓰기/재실행없음.
source8개를p361-r335-qualified에exactarchive.
접근허용/한글/UAC/OS·Defender·WSL변경/Git/다른앱종료/삭제이동0.

근거:r690 상속비용,r691 CODE9/실제메모리투영,r692 exclusiveproducer,
manifest021,r693 CODE4/전체상속admission. 모두제품/Gate PASS와구분한다.
