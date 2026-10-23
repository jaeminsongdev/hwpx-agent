# 원본 HTTPS 필드 목적지 변경 후보

실제 원본의 HTTPS 필드 선택을 한 번의 보존형 transaction으로 변경한다. 대상은 기존 한글2020
HTTPS/current-tab six-parameter profile의 `Command`와 `Path` 내용 두 곳이다. 다른 native 매개변수,
필드 속성·ID·쌍·표시 문자열과 나머지 패키지 내용을 보존한다. Native 필드 갱신이나 저장/재열기,
새 목적지로의 접속·외부 실행·전체 참조 검증은 하지 않는다.

## 입력과 정책

`SourceFieldMeaningIndex::lower_https_target_candidates`는 원본에 결속된 fresh form reconstruction,
reference ID·field fingerprint·meaning SHA·typed HTTPS target의 묶음을 받는다.
다른 문서/원본의 선택, 잘못된 fingerprint/의미, 중복 선택, HTTPS가 아닌 의미/목적지,
빈 묶음·no-op·초과 한도는 후보를 반환하지 않는다. 묶음 하나가 잘못돼도 일부 결과를 반환하지 않는다.

새 목적지는 `ExternalLinkPolicy`에서 해당 kind와 정확한 target digest로 승인돼 있어야 한다.
원 policy shape·정렬·중복·enablement·한도와 URI shape 규칙을 그대로 사용한다.
`validated_external_targets`는 불변 policy를 한 번 검증해 빌리고, 각 목적지는 정렬된 승인 목록에서
이진 탐색한다. 전역 캐시·정책 clone·대상마다 목록 전체 재검사는 없다. 정책 hash 출력 예산도 writer 실행 전에 검사한다.
이 policy 객체/빌린 view는 정책 데이터이지 issuer나 실제 서비스 접근 권한의 증거가 아니다.

## 보호와 원본 확인

원본 전체 part의 fieldBegin/fieldEnd coverage를 검사해 header 등 비본문의 필드를 빠뜨리지 않는다.
원 protection observation의 문서 신호를 거부하고, 기존 Unicode 작업의 잠금·TC/SZ 보호·
변경 추적 guard를 공유한다. guard 본문은 변경하지 않았다. 파트별 누적 개수를 한 번 만들어 선택 범위의
보호 신호를 확인하므로 선택마다 전체 XML을 반복 탐색하지 않는다. 범위 밖의 unrelated context는 그대로 보존한다.
신호 부재를 Native unprotected 자격으로 바꾸지 않는다.

`hp:p`/`fieldBegin`의 미지원 lock 속성은 원 구조 reader에서 먼저 거부된다.
이를 늦은 보호 시험에 도달시키려고 parser를 완화하지 않았다. 허용되는 paraTcId/charTcId는 실제 공유 guard에서 거부한다.

## 보존형 writer와 readback

원 six-parameter reader와 command formatter에서 두 기존 leaf를 얻어 기존 patch engine/writer에 넘긴다.
기존 글꼴 binary-edge ID profile 선택도 그대로 재사용한다. caller가 raw XML·byte offset·action 문자열을 넣는 경로는 없다.
한 번의 transaction과 한 번의 전체 출력 package/forms/fields/meanings import로 모든 선택의 새 목적지를 대조한다.
미선택 의미, 원 field kind/native begin ID·inline 범위·source element 위치를 비교하고,
선택한 두 leaf의 content 밖 XML 바이트 및 변경하지 않은 모든 part의 바이트를 확인한다.
원 cached 표시 텍스트는 바꾸지 않으며 그 내용이 새 목적지와 일치하거나 Native에서 갱신됐다는 뜻은 아니다.

후보는 소유 artifact와 URI 비노출 receipt다. receipt의 원 source/meaning inventory, 전체 policy,
요청/출력 digest는 실행 권한이 아니다. `with_verified_bytes`도 writer 무결성 확인만 제공한다.
원본을 in-place로 쓰거나 자동 저장/게시하지 않는다.

## 제품 API

`ReferenceValidationProductOperation::prepare_package_https_target_changes`는 실제 bytes·document ID·
예상 package SHA와 기존 평가 API가 제공한 선택을 사용해 같은 원본 결속 경로를 호출한다.
새 CLI/MCP/JSON dispatcher나 Native fallback은 추가하지 않는다.
기존 평가 API·reference-source v13, incomplete·미해결4·report 없음·exit3는 그대로다.

현재 서비스 ACL/head·서버 정책 발급/갱신, 공통 compiler/manifest·영속 job·저장/CAS·게시,
Native protection·target 의미·갱신/저장/재열기와 전체 P09 Gate는 별도 미완료 조건이다.
이 후보를 운영 route나 문서 전체 hyperlink 편집 지원으로 승격하지 않는다.

## 검증 결과와 자원 관측

[526](../../implementation/p09/evidence/p09-361-source-https-target526.v1.json)은 현재14개와 원 입력/본문이 같은 policy3개 보존의
고유17개 범위다. 현재 실행은 policy view2·source8·product4이며17개 단일 실행이 아니다.
기존 policy3은 반복하지 않았다. 이전 source7개는 정책 lookup과 실제 tracking guard가 바뀌어 직접 영향 대상으로 다시 확인했다.
검증은836fresh/final836·dep-info3final·컴파일 경고 없음·cleanupTrue, 전체258.5초다.
세 명령은25.750/57.547/67.937초, libtest 본문 합계는1.02초여서 준비/컴파일/입력 마감 시간을 본문 시간과 구분한다.

보존된 실제 HTTPS HWPX와 생성된 다중 필드 문서에서 실제 새 target readback, `&` escaping,
미선택 보존, 묶음 atomic 거부·오래된 선택/다른 원본·정확한 policy·보호·writer/URI/출력 한도를 확인했다.
524의 source7pass/1fail·경고3·final fresh 없음과525의 사전 입력 세대 대조 오류/명령0은 보존했다.
실패한 보호 fixture를 원 reader가 허용하는 구조로 구분했고 보안/구조 조건을 완화하지 않았다.

시스템 CPU 최고81.42%, 가용 RAM 최저29.777%였으며 보호 중단은 없었다.
세 소유 Job의1코어·BelowNormal·machine CPU6.25% hard cap·RAM/commit95% 정책과 정상 정리를 확인했다.
81.42% 앞/뒤 표본은26.7→81.42→59.73→39.92→21.8%다. 종료 후 Defender CPU 단일 표본0은
과거 peak의 원인을 증명하지 않는다. 검증 I/O에 따른 간접 부하나 다른 프로세스의 기여를 배제하지 않으며,
PC 프리즈 해결로 판정하지 않는다. [자원 관측 메모](../../implementation/p09/evidence/p09-361-source-https-target526-resource-note.v1.json)를 따른다.

공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·P02 routing_allowed=false는 그대로다.
한글·접근 허용·외부 URL·SQL·공식249·003은 실행하지 않았다.
