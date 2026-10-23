# 원본 전체 보호 신호와 manifest 결속

`hwpx-agent.source-protection-signals/partial-v1`은 실제 불변 원본 전체에서 기존 검사기가 정의한
보호·서명·암호화·권한 신호를 관측한다. 관측된 문서 신호를 caller의 Unprotected 값으로 우회하지
못하게 manifest 준비 경로에 결속한다. 신호 부재는 보호 없음이 아니며 Native 보안 상태를 증명하지 않는다.

## 원 검사기의 관측 범위

ImportedSourcePackage::observe_protection_signals는 이미 수입된 모든 part와 XML을 사용한다.
기존 native_form_package의 sensitive 이름 판정은 protect/password/encrypt/signature/rights/readonly를
ASCII 소문자로 비교하는 원 알고리즘 그대로다. 그 함수의 가시성만 crate 내부로 넓혀 공유했다.
원 native scanner와 HP lock/TC protect/직접 table SZ protect의 선택 보호 알고리즘은 변경하지 않았다.

META-INF/signatures.xml, META-INF/encryption.xml, META-INF/rights.xml의 존재를 각각 센다.
기존 metadata 범위인 Contents/header.xml과 대소문자 무관 settings.xml 및 위 민감 part에서는
element/attribute 이름의 민감 신호를 관측한다. namespace 선언과 텍스트 값은 신호 이름이 아니다.
이는 원 보수적 판정으로, protect='0' 같은 속성도 원본의 보호 해제가 확인됐다는 뜻으로 해석하지 않는다.

원 observed_protection의 상위 lock·TC/SZ 전파 결과는 local_blocked_elements에 센다. 이 수는
고유 잠금 속성 수가 아니라 원 guard가 막은 element 수다. 로컬 잠금만으로 문서 전체를 막지 않으며,
선택 밖 잠긴 표가 보존되는 정상 편집과 선택 안 보호 거부를 별도로 검증했다.

## 불변 원본 결속과 한도

SourceProtectionObservation은 외부 생성자와 역직렬화가 없다. profile, document_id,
source_package_sha256, source_provenance_sha256, counts 및 다음 false 필드를 직렬화한다.
native_protection_verified, cryptographic_signature_verified, execution_authority다.
원본 text/anchor·비밀정보 값은 직렬화하지 않고 Debug에는 집계만 표시한다.

counts는 parts, xml_parts, xml_elements, protection_element_visits, local_blocked_elements,
document_signal_parts, document_xml_signal_elements, signature_parts, encryption_parts,
rights_parts다. 실제 관측 part/XML/element 수를 원 SourceImportReceipt의 전체 수에 대조한다.
verify_binding은 같은 document/source SHA/provenance와 전체 수를 확인하며 다른 문서나 원본에 재결속하지 않는다.

기존 source import의 part/expanded/XML/element/token/fingerprint 한도를 유지한다. 원본 수입이나
ZIP 재개방 없이 같은 parsed XML을 사용하고 part마다 원 local guard vector 하나를 일시 보관한다.
원 guard의2pass와 metadata 범위의 추가1pass를 protection_element_visits로 정확히 센다.
1000개 문단의 방문 수를 독립 계산해 대조했다. 부재나 unknown을 Unprotected로 변환하지 않는다.

## manifest 준비와 현재 접근

prepare_execution_manifest는 원 compiled with_verified_bytes 안에서 관측 결과를 한 번 만들고
같은 후보와 함께 소유한다. make는 현재 원본에 결속된 관측인지 확인한 뒤 문서 신호가 있으면
SourceProtectionObservationError::ObservedDocumentSignal로 거부한다. 외부 관측 receipt를 입력으로 받지 않는다.

보관 후 verify/byte 전달은 이 관측을 다시 만들지 않는다. 원 provider의 현재 write/scope/head/
ACL/quarantine/AEAD·source/output integrity, 현재 routing·manifest·routing 뒤 최종 head를 유지한다.
관측 성공이 접근 lease, 서명 검증, key claim 또는 실행 권한이 되지 않는다. 원 RouteUnqualified도 그대로다.

## 검증과 실패 보존

components222는 원본10pass·제품33pass/1fail이었다. 임의 문단 lock 속성을 사용한 양성 fixture가
기존 TextFlowReader의 문단 속성 허용 목록에서 거부됐다. 같은 형태의 음성 시험도 단순 실패 여부만으로
원 보호가 검증됐다고 볼 수 없어 강화 대상으로 분리했다. 원222 실패는 보존했다.

제품 코드는 그대로 두고 기존 수입 검증된 잠긴 표로 두 fixture만 고쳤다. recovery223은 선택 밖
잠긴 표 보존 양성과 선택 안 표의 정확한 Compile::Protection 거부를2pass·764fresh/final764·
진단/경고없음·cleanupTrue로 확인했다. 원본10+신규제품8+영향manifest26=고유44개이며 현재44개 단일 실행이 아니다.
통과42개·무관 compiler36·공식249는223에서 반복하지 않았다. 원 native scanner/local guard와 기존
compiler/route·다른 시험 본문은 역변환·불변 입력으로 보존했다.

원본 시험은 전체 수·unknown 상태·6종 민감 이름/false 값·spine 밖 settings·세 META-INF part·원 lock/
TC/SZ·namespace/entity/상위 전파·텍스트와 선언의 비신호·다른 문서/패키지·1000문단·다중 신호를 확인했다.
제품 시험은 모든16계열의 caller Unprotected 우회 거부·원본 settings·선택 안/밖 보호·불변 관측 재사용·
현재권한/ACL·비노출·원 source binding을 확인한다. 영향26개는 바뀐 manifest 준비 경로의 원 시험 그대로다.

223 전체108.390초·명령10.450초/시험0.59초·Job CPU9.047초·private최고988.14MiB/3.1014%·
시스템CPU최고18.85%·가용RAM최저28.0594%다. 222 시스템CPU최고58.59%·Job private최고1859.44MiB/5.8361%다.
두 Job active0/empty/handle closed와 한 코어 affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·
RAM/commit95%·명령300초·guard600초를 유지했다. OS/Defender/다른 앱 변경이나 PC 프리즈 해결을 주장하지 않는다.
근거는 implementation/p09/evidence의 p09-361-source-protection-manifest-components222.v1.json 및
p09-361-source-protection-manifest-recovery223.v1.json이다.

## 남은 실제 실행 경계

이 부분 관측은 암호학적 서명·암호화 해석이나 Native 전체 보호 상태의 자격 검증이 아니다.
신뢰 registry/현재 target·전체 Native 보호, 실제 실행 dispatcher·ingest/commit/CAS·영속 멱등 실행·
transport/게시·전체 검색/참조·target match_set/semantic_diff/reopen·Native/Gate는 미완료다.
P02 routing_allowed=false를 승격하지 않는다. source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정 CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다.
