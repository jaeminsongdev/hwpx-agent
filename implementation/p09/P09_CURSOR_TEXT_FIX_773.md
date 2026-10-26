# 768 본문 읽기 오류 수정773~775와 세션 마무리

**현재: 수정 코드검증 완료 / 새773 실물 NOT_RUN / 사용자 외부1회 실행 대기.** 사용자 최신 지시대로 이번768 오류정리만 마무리한 뒤 목표를 일시정지한다. 별도의 작업속도 개선작업은 시작하지 않았다.

## 실제768 결과

원본: implementation/p09/evidence/p09-361-prepared-bookmark768-native001.v1.json
125293bytes / SHA256 08cd85dacfa68a15aef48829ec5f51ac9b2976ada09754262f1c02ede10b8e3a.

- 세션자격 검사는 성공했고 첫사례의 initial_image 자원경계에서 P09_XREF_BIND_CURSOR768_WHOLE_TEXT_BEFORE로 실패했다.
- 원래코드에서 본문읽기는 SetPos/GetDefault/Bookmark Execute보다 앞이므로 실제이동에 도달하지 않았다. 완료사례0·전체8종미실행이며 과거실패를 통과로승격하지 않는다.
- capture worker exit2/요청10,전체cleanup=true. 남아있는한글프로세스는 결과확인시 없었다.
- source1409/final1409는 준비reader의수치이며 실패사례의 모든사후경계가닫혔다고 해석하지 않는다.
- 475.313초/945표본/시스템CPU최고38.67%/가용RAM최저47.1428%. 자원보호중단이 아니다.

## 수정 범위와 근거

이전코드는 전체본문읽기에 TEXT/saveblock:false를 전달했다. 실제반환형식·길이는 원래실패기록에없으므로 null인지 빈문자열인지 단정하지 않는다.

[한컴의 데스크톱 오토메이션 예제](https://forum.developer.hancom.com/t/topic/669)는 전체본문에 GetTextFile("TEXT", "")를 사용한다. [한컴의 선택블록 안내](https://forum.developer.hancom.com/t/hwpctrl/586/6)는 선택영역을 saveblock으로 구분한다. 이에따라 새773은 **전체본문은 빈옵션, 선택영역은 saveblock**으로 명시했다. 웹기안기문서를 설치된2020의실물수용증거로 사용하지 않는다. 실제2020에서수정효과가확인됐다고 주장하지않으며 아래새실행이필요하다.

새helper는 before/selected/after의3회읽기를 고정한다. 반환전후에 role/option_mode/반환성공여부/형식/UTF16길이/UTF8길이/SHA와오류시안전한형식·HRESULT만 기록한다. 문서본문·선택문자열·예외메시지는내보내지않는다. null/비문자열/빈값/짧은전체본문은이동전에거부하며 다른옵션/형식으로재시도하거나 trim/coercion으로통과시키지않는다.

전체본문은11~65536문자,선택문자열은기존정확한10문자와원본SHA를유지한다. 전체본문전후SHA와6좌표/확인좌표/현재문서·owner·sourceSHA·독립세션·종료검사도유지한다. 진단3개의옵션/형식/길이/해시까지evidence reader가확인한다.

기존768 실행기·PS/Python코드·실패·trace를 수정하지않고773 네임스페이스로분리했다. 저장/필드삽입/새로고침/링크활성화는추가하지않았다.

## 검증

증거: implementation/p09/evidence/p09-361-bookmark-cursor774-code001.v1.json
상태: QUALIFIED774_CURSOR_TEXT_OPTIONS_AND_DIAGNOSTICS_CODE_NOT_NATIVE
136643bytes / SHA256 c8484d612970a3edd475624ab65e215858fffa79842e142d72db25991a004f3d.

- 구문5개를전체입력대조보다먼저검사.
- 새진단·evidence·XZ entry Python8개와직접영향PS13개 통과. 빈본문/비문자열/선택문자열불일치/사후빈본문·본문변경/잘못된옛옵션을거부한다.
- 기존프로토콜/owner/CPU·RAM/단계·기한/통신/retirement는 namespace외에달라지지않음을확인했다. 영향없는옛시험이나 제품766/실물761·768을재실행하지않았다.
- 실제worker READY1회를거부했고 사례0/한글0/cleanup=true였다. entry.load_code 실제XZ경로도확인했다.
- source1424/final1424,shell final1,642표본,322.266초. 시스템CPU최고31.21%,가용RAM최저37.3886%,보호중단0.
- 원래단일논리CPU2(mask4)/BelowNormal/CPU·RAM·commit95%·시작15초/작업10초/구간600초/전체1800초/drain45초를유지했다.

## 다음 명령

새773은 기존initial8/reopened8 파일의 직접책갈피이동16건을 한묶음으로확인한다. 필드링크클릭이나 저장시험 재실행이아니다. 별도로연외부PowerShell에서한번실행한다. 관리자권한은필요없고 접근허용창이뜨면직접눌러야할수있다.

    & (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_prepared_bookmark_native773.py' --execute-bookmark-cursor-eight-once

종료후마지막JSON을보낸다. 오류/보호중단/cleanup=false면동일명령을다시실행하지않는다. 768/761/755와과거Native시험도재실행하지않는다.

최신제품766·Native761/763 수용범위와 P09/A12/A13 OPEN·31묶음/65기능·158/249·next165·새P10미시작은유지한다. 코드검증은새Native/직접이동/링크활성화/전체P09 수용이아니다. 문서원본9개는 source-archive/p361-cursor768-text773-docs/에보존했다.
