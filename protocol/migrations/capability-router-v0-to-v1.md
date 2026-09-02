# Capability router v0 to v1 migration

P04-05 replaces conceptual preferred/fallback backend strings with a fail-closed typed routing
snapshot. Existing clients must not choose the first backend, route from a family-level version, or
treat catalog presence as verified support.

For every compiled operation, clients must supply:

1. an exact target profile ID, build and architecture;
2. the signature-verified registry payload SHA-256 and sequence used to create route bindings;
3. current-PC policy scope, document protection state and preservation requirement;
4. bounded backend health observations with generation, timestamp, TTL and explicit state;
5. binding evidence whose support state is exactly `verified`.

The v1 decision receipt schema is `hwpx-agent.capability-route-decision/v1`. Consumers must bind the
receipt to the operation ID, registry snapshot and health generation before transaction execution.
Unknown fields, unknown enum values, stale health, profile or registry drift, confirmation-required
paths and equal top-ranked candidates must stop rather than fall back to a weaker route.

The Rust in-memory structs are not the final permissive public JSON boundary. A future wire adapter
must deny unknown fields and validate serialized-size ceilings before constructing these types.
