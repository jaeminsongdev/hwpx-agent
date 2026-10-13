# P09-37 atomic form input and default restoration

Implement actual value-only typed input, not another property-only alias or
test implementation. Preserve frozen domain-ir form-control/v1 and shared lib,
every P09-34/r02, P09-35 and P09-36 source/receipt, originals and failed evidence.
Compile the new production module through separate pending-export integration
targets; it is not yet a public API/export/native/production route. No shared
source lock refresh or source-included native candidate is permitted. This is
the typed input stage of the full product work, not substitution for required
complete HWPX, native save/reopen, validation, render and differential closure.

Support all six semantic input kinds: text, checkbox, radio, combo, list, date;
keep date's native binding explicitly UnverifiedDateControl. SetValues applies
the complete ordered caller assignment set atomically; ResetDefaults restores
only current values/selections from the existing explicitly supplied defaults.
Never change defaults, validation, items, captions, flags, common properties,
native binding/IDs, anchors, geometry, unknown data, catalogs, resource/reference/
protection/opaque digests or document flow. No insertion/type conversion or
implicit extra radio targets. Radio selections spanning logical paragraphs
validate globally only after all requested changes, independent of assignment
order. Partial required-group transitions fail without any returned partial
state. Empty, duplicated, missing/wrong-kind targets and global no-ops reject.

Every requested target, even a no-op member of a larger batch, must be shape-
unlocked, enabled and editable; text must not be read_only. Caller access must
explicitly allow input and match the complete source protection digest. This
is caller policy only, NEVER observed native security/permission proof. The
complete current state is sealed independently and rechecked during planning
and build. Build requires a fresh caller access policy and rejects revocation
or any difference from the sealed request, even with unchanged document state.
Reuse unchanged actual domain validators for current/default text,
length/multiline/numeric rules, checkbox/tri-state, radio group, selection/item
membership and Gregorian date/range requirements. Any external-validator digest
requires an actually qualified validation implementation, so mutation rejects
ExternalValidationUnqualified here; a digest is not executed validation proof.
Do not call external services or run document commands. Built-in validation
does not qualify native protection, external validation or native output.

Requests are strict duplicate-free/unknown-field-free/coercion-free JSON with
finite existing domain limits, equally enforced for typed callers. Private
immutable plans have no Deserialize and seal source/target/flow/access/operation/
request/counts. Build replays and compares the entire freshly reconstructed
plan, rejecting changed state/protection/flow and private seal tampering. Bound
new JSON writer growth before allocation; never silently clamp or drop values.
Debug/error/public hash-only receipts must not expose document values, names,
defaults, group/caption/selection/date content or private absolute paths.

Test the actual production body, not a mocked copy, with every value kind and
default restoration, atomic required-radio switch, order parity, preservation,
access/protection, validation, external-validator rejection, retry, private
tamper, JSON and finite-bound failures. Separately bind the unchanged actual
P08-20 capture through the real stable public complete-package reader/policies
to a value plan. Independently assert every other complete domain field exact
and native identity remains Missing. Explicitly exercise and retain the old
complete HWPX lowerer's NonRepresentable rejection; do not claim that typed
input now writes a native document or silently change its opaque binding.

The qualification capsule must pin the new production/tests/policy/verifier and
all immediate historical dependencies; execute exact named compiled suites,
zero ignored/failed/missing/extra tests, actual capture/hash-only probe, strict
independent claims and predecessor source authority checks before/after. Keep
initial failures visible, publish append-only and reproduce exact receipt bytes.
Reports/PLANS are mutable pointers; frozen source changes need a successor.

The user's sleep-time no-native/access-dialog hold remains in force. No COM/
Hancom/UI, trust/security/registry, network, staging/commit/push or original
deletion/move. Keep zero green/P09 Gate open, no new P10. Actual native value
lowering/opaque separation, caller-policy persistence/default/validation native
contract, native date shape, production routing and all broader gaps remain.
The existing complete15-case diagnostic native matrix remains NOT_RUN; do not
add a typed-only/unimplemented input case to the future permission batch.
