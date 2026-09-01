# 저장소 부트스트랩과 개발 규율

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 목표

P00의 target/license/source lock이 끝난 직후 생성해야 할 실제 monorepo와 개발 규율을 정의한다. 첫 커밋부터 문서 엔진, Windows worker, MCP, widget이 서로의 내부 구현에 결합되지 않게 한다.

## 권장 최종 트리

```text
hwpx-agent/
  Cargo.toml
  rust-toolchain.toml
  deny.toml
  pnpm-workspace.yaml
  Directory.Build.props
  buf.yaml
  crates/
    domain-ir/              # 순수 DocumentGraph/MathAst/FormulaAst
    operation-engine/       # selector, planner, transaction, diff
    capability-registry/    # target profile, binding, router
    hwpx-package/           # ZIP/OPF/mimetype/path limits
    hwpx-xml/               # namespace-aware token/tree layer
    hwpx-reader/            # HWPX -> snapshot/IR
    hwpx-writer/            # normalized authoring
    hwpx-preserve/          # surgical preserve patcher
    equation-engine/        # parser/normalize/EqEdit compiler
    validation-core/        # validators and evidence model
    project-state/          # revisions/checkpoints/CAS
    job-orchestrator/       # leases/retries/cancel/idempotency
    mcp-server/             # semantic public tools
    client-sdk/             # generated client models
  protocol/
    proto/                  # Rust/C# shared protobuf
    json-schema/            # public OperationPlan/tool schemas
  workers/
    windows-agent/          # service/job lease/artifact staging
    windows-hancom-worker/  # C# STA process, COM isolated
    webhwp-adapter/
    render-oracle/
    python-compat-adapter/  # optional, never source of truth
  web/plugin-widget/
  plugins/universal/
  plugins/codex-local-companion/
  capability/
    sources/ locks/ imported/ bindings/ overrides/ signed/
  fixtures/
    synthetic/ target-build/ licensed-private/ malicious/
  tests/
    conformance/ differential/ e2e/ security/ performance/
  deploy/
    control-plane/ windows-image/ kubernetes/ terraform/
  tools/
    catalog-importer/ binding-review/ macro-discovery/
    fixture-minimizer/ package-diff/ visual-diff/
```

## 경계 규칙

1. `domain-ir`은 ZIP, XML, COM, MCP, DB를 의존하지 않는다.
2. `operation-engine`은 capability ID와 backend trait만 안다. HAction 이름을 모른다.
3. `hwpx-*` crate는 OpenAI SDK, HTTP, DB를 의존하지 않는다.
4. C# worker는 protobuf 계약 외에 Rust 내부 type을 모른다.
5. public JSON Schema와 internal protobuf에는 독립적인 version이 있다.
6. generated 파일은 수동 편집하지 않는다. override는 별도 디렉터리와 review owner를 갖는다.
7. fixture의 라이선스와 개인정보 등급을 manifest에 기록한다.

## 첫 커밋의 필수 자동화

- format/lint: Rust, C#, TypeScript, Markdown, JSON/YAML.
- dependency lock 및 공급망 검사.
- JSON Schema compile, protobuf breaking-change 검사.
- unit test와 deterministic serialization test.
- ZIP/XML fuzz smoke와 path traversal regression.
- 문서 링크·manifest·feature ID 중복 검사.
- secret scan, license allowlist, artifact size limit.

## 브랜치와 변경 단위

capability 구현 PR은 다음을 한 change set으로 포함해야 한다.

```text
semantic operation type
+ capability registry row/binding
+ backend implementation
+ happy/boundary/negative/preservation fixture
+ validation evidence expectation
+ docs/ADR if contract changed
```

코드만 먼저 넣고 registry/test를 후속으로 미루지 않는다. 구현 상태는 `planned`, `bound`, `implemented_unverified`, `verified`, `degraded`, `disabled`, `removed`로만 표현한다.

## 재현 가능한 개발 환경

- Linux control-plane container와 Windows target image를 별도 lock한다.
- target profile에는 OS build, 한/글 제품/build/locale/bitness, 설치 컴포넌트, font set, printer profile, automation manual/source hashes를 포함한다.
- 실제 한/글이 없는 일반 CI는 mock으로 “성공”을 만들지 않는다. 해당 검증은 `unverified`다.
- licensed target CI는 접근 제어된 runner에서만 실행하고 fixture/output retention을 제한한다.

## 완료 기준

- 깨끗한 checkout에서 하나의 bootstrap 명령으로 schema/code generation과 unit test가 실행된다.
- Linux job은 Windows 전용 DLL/COM에 링크되지 않는다.
- C# worker를 제외한 모든 core test는 한/글 설치 없이 실행된다.
- target runner가 없을 때 release report가 oracle 검증 누락을 정확히 표시한다.
