# P09 case160 실제 manifest와 입력 Binding 검증

160번의 실제 manifest024와24쌍 입력 Binding을 구현·검증했다. 159번 당시의 실패158 이력은 원래 값 그대로 역사적 정보로 보존하고, 현재160/before153/authority153/root159 문맥을 별도로 명시한다. 공식 상태는153/249·잔여96·next160·current-generation48이며 P09/A12/A13 Gate는 OPEN이다. 제품·Native·worker dispatch와 독립 승인은 아직160에서 실행하지 않았다.

## 코드와 역사적 문맥

runtime_successor_binding_v2.py는 원래 private159 연결을 재사용한 뒤 constructor와 실패 descriptor의 정확한 case literal을159에서160으로 연결한다. 원래 representation의 prior_failure_lineage key만 historical_case159_failure_lineage로 명시한다. 세 연결 모두 역변환 후 전체 원래 code equality를 확인하고 defaults/closure/kwdefaults를 유지한다. semantic_union/project/runtime_budget/validate_scope_evidence 메서드는 같은 원래 객체다.

새 successor_context는 authority153/root159와 역사적159 실패 이력을 함께 고정한다. 역사적 next159/before152/prior158/authority152/root158 및 실패003/004의 원본·review 핀을160 값으로 바꾸지 않는다. 실패를 제품 증거로 승격하지 않으며 일반 source·binary·fixture를 표현으로 바꾸지 않는다.

코드 검사10개는 정확한160 타입, bool/다른 index 거부, 문맥·승격·원본 bytes·physical path 변경 거부, default module 불변, 전체 원래 메서드 identity, constructor 역변환, provenance 분리·방어적 복사 및 일반 source 변환 거부를 확인했다.

## 실제 manifest와 전체 선행 admission

manifest024는 implementation/p09/evidence/p09-361-case160-source-manifest024.v2.json이다. 실제3724bytes/SHA256d4f2a5fd4a44deb4fcab40ae67e531c3c8311ebf627e1607b62eaa2678ecbea8이며 future placeholder를 사용하지 않았다.

runtime_successor_manifest_v2.py는 정확한 authority153/root159, 이전 manifest023, r753 선택과 r754 실제 publisher 핀을 closed schema로 확인한다. 별도159 constructor graph에서 원래 manifest023 전체 admission을 그대로 실행하여 기존20쌍 및 이전 source·producer·qualification·failure·authority 조건을 확인했다. 그 뒤 별도160 graph에20쌍을 정확한160 문맥으로 연결하고 추가4쌍을 더한다. 원본·physical bytes24쌍 모두 fresh 확인한다.

역사적 scope와 실제159 semantic scope, authority153/root159 및 실제manifest024를 충돌 없이 합친다. 관측된160 후보 frame에서 기대값을 복사하지 않는다.

## 검증 결과와 비용 경계

r756 상태는 PASS_ACTUAL160_BINDING_CODE10_MANIFEST24_OLD159_FULL_ADMISSION_NOT_CURRENT_CONTROLLER_OR_GO이다. 검사10/10, source_pairs24, fresh139/final139, 전체CPU 최대43.57%, 최소 가용RAM50.69241%, cleanup true를 확인했다. 제품·Native 실행0, GO 권한0, 승인 delta0이다.

상속범위 baseline은 inputs2719/directories372/physical248592796bytes/semantic291550735bytes, 전체 예측594.878490초다. 원래600초·60초margin·14/20 rates·두 실제 byte·15초capture·shared decoder5초 및CPU/RAM 보호를 유지한다. 새160 controller·DATA·전체import inventory·whole preflight를 포함한 모델은 아니므로 이 값만으로 GO를 발행하지 않는다.

## 다음 단계와 보존

다음은 실제160 worker capsule과 parent/full oracle 동일 Binding 연결, 이전159 전체 independent oracle, 새controller/DATA와 현재source/import/Rust inventory를 포함한 whole preflight다. 이를 통과한 뒤에만160 단일 제품 실행과 독립 승인을 수행한다. 통과한159는 다시 실행하지 않는다.

full249-current와signed16, 전체P09 Gate는 미완료이며 P10 새 구현은 없다. 이전authority153/152, 성공159/158, 원manifest023, 실패034와 사용자P08/P17/공유Rust 변경·private 원본을 보존했다. 한글·접근 허용·UAC 요청, OS/Defender/WSL 설정 변경, 외부 process 종료, 원본 삭제·이동, 원격 push는 없었다. 과거PC 프리즈 해결을 주장하지 않는다.

근거는 manifest024 및 implementation/p09/evidence/p09-361-case160-binding-manifest-code10-r756.v1.json이다.
