# P06 table automation binding overlay v1 to v2 migration

The v2 review is an additive, target-scoped successor to the immutable v1 review and overlay. It
keeps the same licensed current-PC Hangul 2020 target and exact official Action Table source locks.

V1 admitted only one-to-one capability names and therefore left 29 table rows unavailable. V2 also
admits an exact official Action when the feature specialization is carried by a reviewed
ParameterSet or disposable-document context. Shared Actions do not inherit runtime support: every
feature still requires its own target-bound effect, rollback, persistence and differential result.

The v2 pre-runtime state is 61 `candidate_unverified`, zero unavailable, zero runtime verified and
zero routing enabled. It does not promote P06-09, P06, production or other target builds.
