# P04-05 Capability router policy

## Scope

`domain-ir::capability_router` is a pure decision boundary between a P04-04 compiled operation and
a later transaction/backend executor. It may inspect immutable typed values only. It must not mutate
the graph, read files, use the network, start a process, call COM/HAction or execute a backend.

This task is scoped to the current PC's licensed Hangul 2020 local-development profile. A target
profile is the exact tuple of typed profile ID, build identifier and architecture. Hangul 2022/2024
or another PC is not inferred from a family or minimum version and must receive independent evidence
when that environment is available.

## Required evidence

A route binding is admissible only when every item below is true at the same immutable snapshot:

- capability ID equals the compiled operation capability;
- target profile ID, build and architecture equal the current context;
- signed-registry payload SHA-256 and monotonic sequence equal the context, and the context trust
  state is `signature_verified`;
- support state is `verified`; `candidate_unverified`, `unavailable`, `failed`, `risk_blocked` and
  `not_run` never route;
- policy scope is `current_pc_personal_local_development` and the binding has no network, external
  provider, unsafe action or unresolved confirmation restriction;
- preservation impact meets or exceeds the requested `normalized`/`surgical`/`exact` strength,
  never loses opaque data, and preserves a signature when the document is signed;
- backend health has a nonzero generation, is observed no later than `now`, remains within bounded
  TTL and is `healthy`; `degraded` is admitted only by an explicit binding opt-in.

Protected documents and confirmation-required routes return `confirmation_required`; P04-05 does
not manufacture or consume a user-confirmation token. Production/provider scope, unsafe/macro-like
work, stale health and unknown signature impact remain fail-closed.

## Deterministic selection and receipt

Admissible bindings are ordered by descending priority, ascending cost and then typed backend ID for
stable evaluation. Backend ID is not a semantic tie-breaker: two top candidates with the same
priority and cost return `ambiguous_route`. Filtering a preferred candidate never relaxes evidence,
policy, preservation or health requirements for a fallback.

The selected route emits versioned `hwpx-agent.capability-route-decision/v1` canonical JSON. It binds
the operation/capability/backend, exact target profile, registry digest and sequence, backend health
generation, preservation impact and ranking values. Public `Debug` output redacts identities, build
and registry data.

## Finite and integration boundaries

Catalog size, health-entry count, build bytes and health TTL have hard ceilings. Duplicate exact
bindings and duplicate health observations are rejected. This pure model accepts an already
signature-verified registry claim; wiring the P02 verifier output into this typed context is a later
integration Gate. It does not prove actual capability execution, document mutation, Hancom behavior,
public JSON admission or cross-version compatibility.
