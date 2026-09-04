# P15-06 public error mapping policy

Date: 2026-09-05
Scope: current development PC, licensed Hancom Hangul 2020, local MCP control-plane reference
Status: implementation candidate until the P15-06 report closes the card

## Frozen public boundary

Every rejected public tool call returns `isError=true` and one
`hwpx-agent.error/v2` structured envelope. The digest-pinned
`protocol/mcp/p15-public-error-catalog-v1.json` is the only source of public code, category,
retryability, safe message, allowed stage and recovery action. The response `_meta` contains both
the P15-02 tool catalog digest and the P15-06 error catalog digest.

The envelope has exactly `schema_version`, `request_id`, `error_code`, `category`, `safe_message`,
`retryable`, `stage`, `details` and `recovery`. P15-06 emits an empty `details` object and one bounded
recovery action. It never emits an internal trace, raw error, stack, local path, tenant identifier,
subject digest, bearer token, signed URL, document content or backend payload.

## Correlation and ordering

Authentication still precedes argument parsing. A request ID inside untrusted JSON is not read or
echoed before authentication and schema validation. Admission, authentication, parse and input
validation failures use a server-generated `req_server_<uuid>` correlation ID. Once the frozen
input schema has validated `request_id`, policy, dispatch and output-validation failures use that
public ID. The same value is present in the structured envelope and `_meta["hwpx/requestId"]`.

The fixed stages are `admission`, `authenticate`, `parse`, `input_validation`, `policy`, `dispatch`
and `output_validation`. The P15-03 execution order and single-dispatch rule remain unchanged.

## Closed mappings

- Client authentication failures collapse to `AUTHENTICATION_FAILED`; authentication
  configuration, capacity and identity registry conflict collapse to retryable
  `AUTHENTICATION_UNAVAILABLE`. This prevents an authentication oracle.
- Missing or cross-tenant policy records return `RESOURCE_NOT_FOUND`; explicit role denial returns
  `POLICY_DENIED`; policy configuration, conflict and capacity failures return retryable
  `POLICY_UNAVAILABLE`.
- Gateway missing, conflict, unavailable and rejected states map to `RESOURCE_NOT_FOUND`,
  `REQUEST_CONFLICT`, `SERVICE_UNAVAILABLE` and `SERVICE_REJECTED` respectively.
- All P15-04 async-job and P15-05 artifact-delivery variants first collapse into that four-value
  gateway vocabulary. Parameterized internal values such as total object size are discarded.
- Tool admission, JSON parsing, schema validation, output validation and result correlation use six
  dedicated `TOOL_*` codes from the same catalog.

The Rust mapping tests enumerate every current variant. Adding an internal variant therefore
creates a non-exhaustive compile failure until a public mapping and its acceptance evidence exist.

## Deferred claims

No Hangul process, COM call, HWPX/PDF/user document or external identity service is used by this
card. HTTP status mapping, production telemetry correlation, hosted MCP transport and Hancom
2022/2024 remain later integration work. Internal logs may use a separate opaque trace identifier,
but P15-06 does not place it in the public result.
