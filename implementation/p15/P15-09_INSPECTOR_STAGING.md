# P15-09 Inspector staging boundary

P15-09 is a local interoperability and transport qualification for the current-PC Hangul 2020
target. It exposes the existing P15 public control plane through one loopback-only HTTPS
Streamable HTTP endpoint and verifies the endpoint with the pinned MCP Inspector CLI. It is not a
public deployment, production identity provider, ChatGPT attachment, or Hangul 2022/2024 claim.

## Runtime boundary

- `web/mcp-staging` uses the official TypeScript MCP server and Node transport packages. It binds
  only `127.0.0.1`, selects an ephemeral port and exposes only `/mcp` over HTTPS.
- The process creates a short-lived P-256/SHA-256 self-signed certificate. The private key is never
  written to disk or printed. The acceptance harness writes only the public certificate into its
  automatically deleted temporary directory so Inspector can perform verified TLS.
- The official localhost Host and Origin validators run before routing. Missing or invalid bearer
  authentication returns `401`; wrong paths, methods, oversized bodies, hostile Host/Origin values
  and plaintext HTTP fail closed.
- One persistent Rust driver process owns the real `McpControlPlane` for the complete server run.
  Quota and telemetry state therefore survive individual HTTP exchanges. The Node process does not
  reimplement tool schema, authorization, quota, telemetry, output validation or correlation.
- Each HTTP request is authenticated by the Rust middleware before MCP body parsing. A tool call is
  passed over bounded NDJSON stdin to the same Rust process and returns a correlated bounded NDJSON
  response. Bearers never appear in child command lines or diagnostics.
- The harness closes the server control pipe and requires a clean Node exit after the persistent
  Rust driver exits; only then can it atomically publish a receipt marked `graceful_shutdown`.
- The driver uses a safe synthetic gateway to exercise all 18 public contracts without starting
  Hangul, opening a user document, producing an artifact or creating an external effect.

## Acceptance

Run from a clean exact source commit:

```powershell
python tools/p15/run_inspector_staging.py
```

The harness builds the locked Rust and TypeScript products, generates an in-memory 32-byte HMAC key
and a ten-minute test token, starts the server, and creates an Inspector configuration only inside an
automatically deleted temporary directory. It deletes that directory before publishing the final
receipt. It then requires:

1. strict `tools/list` discovery with exactly the catalog's 18 ordered tools and exact input/output
   schemas, annotations and metadata;
2. one successful Inspector `tools/call` for each tool with request and public metadata correlation;
3. all eight network/authentication negative probes to fail with the exact bounded outcome; and
4. a receipt that contains hashes and status only—never the bearer, HMAC key, certificate, private
   key, tool arguments, result payloads, absolute paths or Hancom/user document data.

Receipts are written under the Git-ignored
`implementation/p15/evidence/staging-runs/<run-id>/receipt.json`. A dirty tracked checkout can produce
only `DEVELOPMENT_PASS`; only an exact clean commit can produce `PASS` with `qualifying: true`.

## Version and scope posture

The locked package graph selects `@modelcontextprotocol/server` 2.0.0,
`@modelcontextprotocol/node` 2.0.0 and `@modelcontextprotocol/inspector` 2.5.0. The server advertises
the current 2026-07-28 exchange and the SDK's bounded 2025 stateless fallback from one tool factory;
the qualification client explicitly selects `modern`.

This card does not claim a production OAuth/JWKS adapter, public hostname/certificate, hosted
retention, distributed quota, remote ChatGPT/Codex connectivity, real Hangul execution, or any
behavior on Hangul 2022/2024. Those require their own later environment and evidence gates.
