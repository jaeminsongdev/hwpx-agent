# P09-33 native root manifest package preparation policy

Implement the actual production source component for bounded whole-package
manifest href preparation. This is a packaging transition, not a native failure
resolution, normalization acceptance, source lock refresh or product Gate.

The independently read closed PackageGraph decides actual manifest targets.
Only OPF manifest-item href VALUE spans may change to root-relative target paths;
XML escaping and percent-literal encoding must preserve those exact targets.
Every other metadata byte, every other expanded package part, entry order and
compression must remain exact. Original package raw bytes remain exact for a
no-op. Changed ZIP headers are explicitly rewritten, not preserved.

All input parts must pass finite bounded ZIP/CRC/closed-graph checks. The plan is
immutable and has no deserializer. Stale source, unresolved/ambiguous targets,
external references, root escapes, duplicated IDs/spine, altered output content,
entry order/compression and finite bounds must reject without publishing an
artifact. Output verification must read an actual external package; it must not
trust its receipt. Errors and debug output must redact document values/paths.

This component intentionally does not reinterpret form values, styles, native
IDs or typed reference declarations. It cannot qualify a previously failing
IdIndex or general field/form/reference semantics. That qualification remains
explicitly unqualified in the receipt. Native reader/lifecycle/render/product
acceptance remains separate, with every P09-32 failure preserved.

At this checkpoint the new source is pending public export: an explicit pending
integration target compiles that exact production source, while the actual
unchanged public package reader verifies both complete text/radio results. Never
claim this is a connected public preparation API or production route. Do not
dispatch new native cases through source-included/mock APIs. The next explicit
source successor must connect the public API with exact predecessor preservation
before all genuinely changed dependency-ready cases are collected for a batch.

Independent Python qualification must execute all named compiled tests, read six
actual emitted source/output artifacts, compare original and the two failed
source packages to their immutable raw identities, derive exact href edits
independently, compare all expanded parts/order/compression, and validate a real
compiled receipt. Raw P09-31/P09-32 capsules and every pinned source must remain
unchanged. No old capsule/hash may be refreshed to fit new code.

Preserve the original native capture, native failed attempts and caller policies.
Do not strip native-name characters or silently replace requested foreground
colors. Those failures require their own full implementation/evidence contract,
not a passing smaller substitute. No P10 before authoritative P09 Gate; zero
green remains. No native/trust/registry/network/stage/commit/push/delete work is
part of this offline component checkpoint.
