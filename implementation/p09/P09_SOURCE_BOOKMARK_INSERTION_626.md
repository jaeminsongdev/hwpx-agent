# P09 626 — 실제 새 필드 삽입의 제한된 source 경로

## 확인한 결과

[audit003](evidence/p09-361-bookmark-insertion626-audit003.v1.json)은 고유8조건을 뒷받침한다. audit002의 통과6조건(실제 저장본8종 포함)은 원본 코드·시험 본문·helper·입력 동일성을 확인해 보존했고, 수정한 보호1조건과 새 숫자 ID 소진1조건만 실행했다. 새 코드가 기존 필드를 편집하는 것이 아니라 **새 CROSSREF 범위1개를 추가**하며 선택한 기존 run 및 삽입 지점 밖 XML이 정확히 보존됨을 검증했다.

이는 source lowerer의 부분 수용이다. 실제 한글을 실행하지 않았고 표시 결과·이동·저장/독립 재열기를 새로 검증하지 않았다. 등록된 제품 실행 route/CLI·CAS·Native·F11 전체·P09 Gate는 완료가 아니다.

## 구현 경계

`crates/hwpx-package/src/document_import/fields/bookmark_insertion.rs`는 다음 경계로 동작한다.

1. 정확한 원본 모델에 대한 whole-source/form 재구성 proof와 실제 source run 앵커를 요구한다. caller XML/바이트 위치/대상 이름/원본 graph/Native 매개변수를 받지 않는다.
2. 실제 책갈피 target 인덱스와 typed 표시/이동 옵션에서 Command를 결속한다. 같은 원본의 실제 필드 중 **Command·결속 target이 모두 일치하는 형식**만 재사용한다. 모르는 RefPath/RefType 등은 추측하거나 다른 target으로 복사하지 않는다.
3. 기존 필드 밖의 한 plain-text run만 감싼다. 숫자 ID 두 종류를 전체 원본에서 한 번 수집하고 중복/소진·관측 보호/변경 추적·필드 중첩/겹침을 거부한다.
4. 새 범위의 ID만 새로 할당하고 dirty를 설정한다. 현재 원본의 다른 매개변수는 그대로 보존하며 새 의미/Native 효과가 검증됐다고 주장하지 않는다. 선택된 기존 표시 텍스트는 계산/갱신된 결과가 아니다.
5. 원 preserving patch/writer와 원 source/form/field/meaning readback을 사용한다. 필드 수 증가·새 Command의 원본 대상 결속·유일한 변경 part·삽입 전후 바깥/선택 run의 byte equality를 검사한다.

원 field importer는 새 모듈 선언 한 줄을 제외하면 보존된 원본과 동일하다. 다른 기존 Rust 본문도624/002 입력 pin과 동일하다. 새 경로에서도 기존 signed route·ACL/head/owner·실행 허가를 해제하지 않는다. 부분 Source/meaning/graph를 full-context로 승격하지 않는다.

## 아직 지원/검증하지 않은 F11 범위

- 동일 Command의 원본 필드 형식이 없는 문서에서의 최초 생성, 다른 대상/표시로의 새 매개변수 생성.
- 책갈피 이외의 실제 대상 종류, 임의 범위·필드 내부·모든 namespace/복잡 구조에 대한 삽입.
- 새 삽입의 공통 제품 요청/compiler/허용된 backend→지속 가능한 새 출력 경로.
- 실제 한글의 표시·이동·대상 이름 변경 시 결속·저장/독립 재열기·필수 렌더 근거.

없는 범위는 자동 fallback/가짜 기본값으로 채우지 않는다. 같은 원본 형식을 복제했다는 사실만으로 Native 호환성/효과를 선언하지 않는다. 이 제한을 F11 전체 범위 축소로 사용하지 않는다.

## 원 실패와 최적화

- [audit001](evidence/p09-361-bookmark-insertion626-audit001.v1.json): 시작 입력80개에서 시스템 CPU100% 표본으로 준비 보호 중단. Cargo/제품 시험0·cleanup true. 원인과 프리즈 해결은 미확정이다.
- 이후 새 lowerer의 불필요한 두 번째 전체 필드 graph 재구성을 제거하고, 시험의 명백히 선택 불가능한 run에 대한 반복 시도를 줄였다. whole-source/form proof와 실제 output/readback 검사는 유지했다. 기존 검증된 저비용620 관측기를 초기 입력 검사부터 연결했다. WMI/새 sampler/thread를 추가하지 않았다.
- [audit002](evidence/p09-361-bookmark-insertion626-audit002.v1.json): 실제 저장본8종을 포함한6조건 통과, 보호 fixture1조건 실패. unsupported run lock은 importer에서 먼저 거부되는데 lowerer 단계까지 도달한다고 가정했던 시험 결함이다. FAILED는 보존했다.
- audit003: importer의 typed 거부와 유효한 변경 추적/보호 표본의 lowerer 거부를 구분해 더 엄격히 확인했다. 소진 ID는 재사용하지 않는다. 원6조건을 다시 실행하거나 기존 실패를 PASS로 바꾸지 않았다. 이전 실행 파일/dep-info와 원 verifier·fixture도 archive에 보존했다.

## 최종 자원과 증거

- 전체165.219초, 수정/신규 시험 실행 구간2.562초, job CPU1.625초, job private 최고612.2MiB.
- 시스템 CPU 최고31.4%, 가용 RAM 최저44.4591%, 해당 실행 보호 중단0. 종료 owned process0·cleanup true.
- 입력935개 시작/종료 hash 일치, compiled artifact2개 최종 확인.
- 1코어·낮은 우선순위·machine CPU hard cap6.25%·RAM/commit95%·breakaway 금지 유지.
- 최종 영수증113817bytes / SHA256 `ab0f33440a08a7d79182c3d396a51de1b03afe8e9475cdf6c7ee2292d96651c6`.

원본 값/전체 로그는 private evidence에 보존하고 공개 보고서에는 싣지 않는다. Defender/다른 앱·OS 설정은 바꾸지 않았으며 이 시험으로 PC 프리즈 원인을 확정하지 않는다.

## 작업 속도 관찰과 다음 순서

전체165.219초 중 build/test 구간은2.562초였다. 기존 CLI 검증기의 inventory를 재사용하면서 이번 hwpx-package 단독 시험에도 전체935입력의 준비/마감 확인이 들어간다. 따라서 이 측정에서 시험 본문 이외 준비·입력 감사·보존의 비중이 크다. 원본 byte 확인이나 open-rate/CPU 보호를 낮추는 해결은 사용하지 않는다.

현재 manifest상 이 시험의 로컬 Rust 의존성은 hwpx-package/domain-ir/equation-engine/foundation 네 package이며 source Rust 파일은317개로 관찰됐다. **317은 새 전체 입력 수나 이미 자격을 얻은 축소 profile이 아니다.** 이후 해당 package만 검사할 때 manifest·build/include/runtime helper·실제 compiler dep-info까지 대조한 전이 의존 범위를 먼저 검증해 적용한다. 공통 CLI 변경이면 해당 CLI의 더 넓은 입력 범위를 그대로 확인한다. 필수 입력을 제외하거나 성공한626을 새 방식 시험 때문에 다시 실행하지 않는다.

다음 기능 작업은 F11의 아직 빠진 최초 삽입/대상·제품 출력 경계를 연결하는 것이다. 외부 실물 근거가 필요한 범위는 초기에 모으고, 자격/허가가 없으면 독립적인 로컬 기능 작업을 진행한다. 목표 ACTIVE·31미마감묶음·P09/A12/A13 OPEN·공식158/249/91대기/next165·새 P10 구현 보류는 유지한다.
