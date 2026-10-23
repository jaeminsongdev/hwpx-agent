# P09 책갈피 이름 캐시 진단과 자원 관측

저장된 책갈피 이름을 같은 원본의 CROSSREF 명령과 비교하는 읽기 전용 제품 경로를 구현했다. 대상 없음·중복·미해석 구조를 이름 일치와 구분하며, 일치하더라도 Native 표시·이동·재평가나 캐시 최신성으로 판정하지 않는다. P09 전체 Gate와 A12/A13은 OPEN이며 목표는 ACTIVE다. P10은 시작하지 않았다.

## 원본에 결속된 제품 진단

`ReferenceValidationProductOperation::diagnose_source_bookmark_name_caches`는 package/forms/field를 한 번씩 import한다. 원래 SHA·전체 field coverage·형식·예산 검사를 유지하고 같은 field에서 command binding과 cache observation을 읽는다. 호출자가 이름이나 대상 맵을 제공하는 경로는 없다.

Core의 `SourceBookmarkCrossReferenceBindings::diagnose_cached_source`는 package SHA뿐 아니라 document·원래 graph·field range를 포함한 field import receipt 전체가 같은지 검사한다. 다른 package/document의 cache는 거부한다. 별도로 import한 동일 snapshot은 읽기 진단에 사용할 수 있지만 실행·저장·현재 head 권한이 되지는 않는다. 원래 graph와 파일을 변경하지 않고 graph clone도 추가하지 않는다.

| 진단 | 판정 범위 |
| --- | --- |
| StoredNameMatchesCommand | 원본에서 대상 책갈피가 하나로 결속되고, 이름 표시의 디코딩된 저장 캐시 SHA가 명령의 정확한 대상 이름 SHA와 일치 |
| StoredNameDiffersFromCommand | 같은 조건에서 저장 데이터가 다름. 빈 캐시·대소문자·공백 차이를 정규화하지 않으며 stale 판정은 하지 않음 |
| StructuredCacheUnqualified | 이름 표시지만 캐시 범위에 중첩 필드·제어가 있어 텍스트로 펼치지 않음 |
| SourceTargetMissing | 명령의 정확한 이름에 대응하는 source-local 책갈피가 없음 |
| SourceTargetAmbiguous | 대응하는 source-local 책갈피가 여러 개임. 첫 대상을 임의 선택하지 않음 |
| OtherDisplayNotCompared | 페이지·본문·상대위치 표시는 이름 비교 대상이 아니며 계산 결과를 합성하지 않음 |

결과에는 원문 이름·명령·캐시 대신 field ID, SHA, typed 진단만 남긴다. Native display/target-resolution, cache-currentness, complete-reference qualification은 항상 false다. 빈 결과도 전체 PASS가 아니다. 항목·텍스트·누적 입력·출력 예산과 overflow를 검사하고, 출력은 보관 전에 크기를 계산한다. 주 Source v15, field-meaning v2와 의미 graph partial-v3 및 미해결4개는 변경하지 않았다.

구현: `crates/hwpx-package/src/document_import/fields/bookmark_crossref/cache_diagnostics.rs`, `crates/product-cli/src/reference_validation_product/source_crossref/bookmark_cache_diagnostics.rs`. 두 parent 파일은 module 선언 한 줄만 추가했으며 기존 reader 본문은 archive와 역비교했다.

## 고정 저장본과 시험 결과

[최종 audit002](evidence/p09-361-bookmark-cache-diagnostics620-audit002.v1.json)는 Rust31조건과 관측기 모형20개를 뒷받침한다. Rust는 신규11·기존 cache reader10·strict command binding reader10이다. 이 중 원래 통과한 신규10개의 본문·공통 함수 및 관련 제품/모형 입력은 동일성을 확인해 유지하고 반복하지 않았다. 최종 실행에서는 수정1+직접 영향20개만 실행했다.

신규 시험은8가지 표시/하이퍼링크 조합, 정확한 일치/불일치/빈 값/공백, 중첩 구조, 대상 부재/중복, 다른 package/document 거부, 동일 snapshot 별도 import, graph 불변, 정확한 출력 경계와 텍스트/누적 입력/항목 한도, 원문 비노출·Native 권한 부재, 잘못된 SHA·지원 밖 명령, 빈 field와 실제 저장본을 확인한다.

일반 실행 빌드는 기존 고정010 산출물24개를 새 제품 API로 읽었다. opened8개에는 새 CROSSREF가 없고 saved/reopened16개에는 각각 진단1개가 있다. 책갈피 이름 표시4개는 StoredNameMatchesCommand, 나머지12개는 OtherDisplayNotCompared였다. 파일은 읽기 전후 bytes/SHA가 동일했다. 이 결과는 저장된 이름 비교이며 기존010의 effect_unknown과 Native 미자격 상태는 그대로다.

일반 EXE는 `target/debug/examples/p09_bookmark_cache_diagnostics620.exe`,5089280B/SHA256 `6a95e00d674d7da2fe2ea93c6351b2359d91c216dd63f3fd5fd734054dff330d`다. 경고·실패0,945fresh/final945·빌드 산출물8개 전후 일치·cleanup true다. 원 소비된010 probe 이미지는 SHA가 그대로이며 실행하거나 재빌드하지 않았다.

[audit001](evidence/p09-361-bookmark-cache-diagnostics620-audit001.v1.json)은 Rust 신규11 중10통과/1실패로 보존한다. 실패는 시험에서 output_bytes만 줄이고 기본 input_bytes를 유지해 `input_bytes <= output_bytes` 구성 조건에 먼저 걸린 InvalidLimit였다. 시험의 입력/출력 예산을 함께 맞추고, 텍스트·누적 입력량·항목 제한을 실제로 검사하도록 강화했다. 제품 구현·기존 보호 한도는 바꾸지 않았다. 최초 finalfresh0와 전체 FAILED를 PASS로 변경하지 않았고 소스는 `source-archive/p361-cache-diagnostics620/`에 보존한다.

## 낮은 부하의 자원 관측

`metadata_cpu_observer620.Attached`는 기존 V4 Toolhelp/GetProcessTimes 관측기를 현재 Guard의 Windows 인스턴스 하나에만 붙였다. 원래 K32 CPU·RAM 표본을 먼저 얻고 그 값과 보호 판단을 유지한다. 추가 process 조회는 같은 thread에서8초 간격, 관측1회50ms·누적2초·128query 이내다. CPU75% 이상에서는 추가 process 조회를 억제하고 unavailable로 기록한다. 전역 Windows 타입·다른 실행기·관리자 권한·WMI/PDH·새 감시 thread/process·시스템 설정을 변경하지 않는다. 종료하면 원래 인스턴스 메서드를 복원하며 정리 불명은 성공으로 바꾸지 않는다.

모형20개는 원래 값/단일 표본·8초 간격·warning 억제·owner·비정상 값·비용/부분 관측·handle 정리 불명·전역 변경 없음·메서드 복원·중복 부착 거부를 확인했다. audit001에서 실행한 뒤 audit002에서는 전체 관련 입력 동일성으로 유지했다.

최종210.843초 동안 시스템 CPU 관측최고34.57%, 가용RAM 최저43.263%였고 보호 중단은 없었다. 앞선 실패 시도는 CPU23.48%/가용RAM39.891%였다. 두 실행 모두1코어·머신CPU6.25% hard cap·낮은 우선순위·breakaway disabled와 기존 RAM/commit95% 보호를 유지했다. 최종 시험/빌드 Job peak private는 최대756.78MiB, 실제 읽기 Job은55.20MiB/CPU0.922초였다.

최종 기존 표본279회에 추가 process query19회(기준1+비교18), 최대1회16ms·누적46ms였고 budget stop·정리 불명은 없었다. 비교18개에서 읽을 수 있는 role의 CPU는 낮았지만 Defender는 모두 UNAVAILABLE_OR_NEW_PID였다. 초기 시도의 짧은 컴파일 구간에서는 rustc의 머신CPU 약6.08%를 관측했다. 8초 process 구간과 원래 CPU 구간은 같지 않고 짧은 작업은 표본 사이에서 끝날 수 있다. 따라서 특정 앱/Defender의 인과나 PC 프리즈 해결을 확정하지 않는다. 원문 command line·경로·비밀정보를 수집하지 않는다.

최종 packet122837B/SHA256 `6f9f0298096fdb1042bdefb805446b9c8800c0a2b095951666f745ee859bacb3`와 원문450133B/SHA256 `52d0e05eb4bb79e98bbd18db0d4af274de3b35d056aaebfd250e461d28c2ea36`를 분리 보존한다. 원문은 immutable private spool에 먼저 보존하며 원256KiB publisher·4MiB 복원 한도는 유지했다.

## 남은 제품 경계

이번 단계는 한글/COM/Native·공식249 전체·기존 Native 시험을 실행하지 않았다. 공식249 큐의158수용/91대기/next165 표기와 새 수용0을 유지한다. 이는 P09 전체 잔여 작업 수나 완료율이 아니다.

실제 Native 대상 해석·이동·표시·재평가·캐시 최신성, 다른 CROSSREF 대상 종류와 전체 reference/auxiliary/flow 의미, 운영 등록·게시/복구 자격 및 통합 Gate는 남는다. 다음 구현은 원본 의미의 미해결 범위를 제품 경로에서 좁히는 데 집중한다. 이 관측/진단 성공을 새 Native 실행 허가나 과거 실패의 재실행 허가로 사용하지 않는다.
