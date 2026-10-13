# P09-144 — 원본과 RAM 숫자 파생 입력의 현재 SQL22 consumer 분기

## 현재 범위

고정 P77 manifest36에서 index0 원본과 그 원본 AST/source anchor에 연결된 숫자 leaf 하나만 RAM에서 +101한 test-only 파생 입력을 current build-r8로 검증했다. 기존 corpus 기록의 원본36은 formula16 모두 Unchanged, no-formula20이다. 파생 입력을 Changed 원본이라고 바꾸어 부르지 않는다. 원본 파일·private evidence·기존 DB·설정은 수정하지 않았다.

현재 Rust 테스트는 route6 + input index5 = 11개 실제 PASS이다. index 선택은 원래 manifest의 canonical 0..35에 한정하며 임의 경로/caller AST/외부 계산 결과를 받지 않는다. 전체 manifest와 선택한 원본 bytes/SHA256를 다시 확인한다. 숫자 파생 입력은 원래 importer/evaluator의 AST와 참조 source anchor로 numeric leaf를 찾고, ZIP expanded inventory·다른 part의 전체 bytes·section의 지정 leaf 밖 전체 bytes·XML element 수/구조를 검사한다. disk package 저장은 없으며 derivative bytes/key는 RAM test-only이다.

## 실제 연결 결과

- P144 run01: index0 numeric_derivative → Changed. original SHA256와 실제 RAM source SHA256는 서로 다르며 one numeric input leaf 검사를 통과했다. 65.79초, system CPU 최대38.66%, available RAM 최소12965.02MiB.
- P144 run02: 같은 current build/index0 original → Unchanged. 실제 source SHA256가 고정 original SHA256와 같고 derivative flag=false이다. 현재 실행 결과와 resource 수치는 receipt를 권위 자료로 사용한다.
- 각 사례의 original source/revision/policy/실제 Ed25519 승인 서명/SQL commit-readback/original mandatory consumer 검사18, original full IR fixture25, SQL22 checks37, credential metadata42, fingerprint 대조2가 완료됐다. 전체 candidate bytes가 독립 evaluator와 같고 fresh trust 재검증 및 head/artifact.ingest 수 불변을 확인했다. 미승인 제품 경로는 정확한 Changed/Unchanged typed route denial로 계속 차단된다.
- strict workspace lint-r1: packages32/targets361, compiler-artifact package/name/kind 집합 exact, diagnostics0, `-D warnings`, source와 EXE48 before/after exact. source/resource guard6은 Rust/DB/native 검증과 별도의 가벼운 검사이다.

## 자원·회수·역사

CPU1/BelowNormal/jobs1 및 DB CPU1/RAM512MiB/pids64/loopback/no host mount/read-only rootfs/tmpfs를 유지했다. Postgres 최소권한·RLS·negative schema 대조 검사를 완화하지 않았다. source/EXE hash 이후 실제 실행 직전 CPU≤50%/RAM≥8192MiB 3회 안정 구간을 요구하고 CPU85% 3회/여유 RAM4096MiB 중단 기준을 유지했다.

run01 종료 후 idle-preflight-r8은 고부하로 defer했다. 이후 lint admission 첫 sample93%/RAM9163MiB에서 안정 구간이 다시 관찰된 뒤 lint를 실행했다. 이 high sample을 lint 작업 중 지속 부하나 Codex 멈춤 원인으로 단정하지 않는다. 두 UUID/label DB는 각각 자기 identity/isolation을 확인한 뒤 회수했고 ID/이름 부재도 별도 확인했다. 다른 작업 프로세스를 임의로 중단하지 않았다.

변경 전 P143 현재 main/Source 전체를 `p09-144-pre-corpus-input-selection` archive로 보존했다. P143 current progress의 959개 pin은 이제 당시 historical snapshot이며 현재 Rust/DB PASS로 재사용하지 않는다. 기존 모든 실패·defer·부분 결과를 보존했고 새 P144 원장은 전체 감사를 완료한 뒤 생성할 대상이다. native/access-allow 실행은 없다.

새 readonly current auditor의 첫 실행은 `STOP_SUSTAINED_SYSTEM_CPU`로 FAIL_CLOSED했고 성공 원장은 생성하지 않았다. 실제 Rust/DB/lint receipt와 readonly 원장 승인 여부를 구분한다. 초기 stop 기록을 보존하며, 안정 구간에서 전체 pin/EXE/역사적 preimage 연결 감사를 다시 완료해야 한다.

CPU1의 가벼운 별도 검사로 현재 main/Source에서 선언한 index/provenance/RAM derivative delta를 제거한 전체 코드가 보존한 P143 전체 preimage와 일치함은 확인했다. 이는 전체959 history pin/EXE의 before/after 감사 완료를 대신하지 않는다. 다음 재확인의 instantaneous CPU73%/RAM9104MiB에서는 full audit를 시작하지 않았다. 현재 consumer live SQL revocation/CAS/race는 아직 NOT_RUN이다.

## 목표와 남은 경계

P09/A12/A13 OPEN, product=false, goal active이다. current corpus coverage는 original index0 한 개 + RAM 파생 입력 한 개이지 원본36 전체 완료가 아니다. synthetic scanner/baseline validation, observed IR fidelity, durable storage, production key custody, atomic product publication과 native 저장·재열기·시각 qualification은 여전히 미승인이다. 현재 consumer에 대한 실제 SQL live revocation/CAS/race와 나머지 original/no-formula/changed/protected corpus가 다음 검증 대상이다. coarse 최소6개/이번에 닫힌 그룹0개 유지, 세부 최소30은 완전한 목록이나 완료율로 주장하지 않는다.
