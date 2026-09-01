# 권장 저장소 구조

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


```text
hwpx-agent/
  Cargo.toml
  crates/
    domain-ir/
    operation-engine/
    capability-registry/
    hwpx-package/
    hwpx-reader/
    hwpx-writer/
    hwpx-preserve/
    equation-engine/
    validation-core/
    project-state/
    mcp-server/
    job-orchestrator/
    client-sdk/
  workers/
    windows-hancom-bridge/
    webhwp-adapter/
    render-oracle/
    python-compat-adapter/
  web/
    plugin-widget/
  plugins/
    universal/
    codex-local-companion/
  schemas/
    source/ generated/
  capability/
    source/ bindings/ generated/ overrides/
  fixtures/
    synthetic/ licensed-private/ malicious/
  tests/
    conformance/ differential/ e2e/ security/
  deploy/
    docker/ windows-image/ kubernetes/ terraform/
  docs/
  tools/
    catalog-importer/
    macro-discovery/
    fixture-minimizer/
    visual-diff/
```

## crate 경계

`domain-ir`은 XML/COM을 의존하지 않는다. `hwpx-*`는 OpenAI/MCP를 의존하지 않는다. `mcp-server`는 backend 구현이 아니라 traits에만 의존한다. Windows-specific code는 `workers/windows-hancom-bridge` 밖으로 누출하지 않는다.
