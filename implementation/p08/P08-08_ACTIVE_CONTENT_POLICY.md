# P08-08 OLE and multimedia active-content policy

## Decision

This checkpoint is package_inventory_implemented / synthetic_security_corpus_pass /
actual_hwpx_not_run / actual_hangul_not_run. Together with the earlier exact drawing-canvas
checkpoint it completes the P08-08 implementation scope, but it is not a real-document, licensed
Hangul, render, differential, production, or whole-product PASS.

## Exact package inventory

The schema is hwpx-agent.active-content-inventory/v1. Scanning first rebuilds the authoritative
bounded PackageGraph and compares it with the supplied snapshot. It then integrity-reads every XML
part and every inventoried resource. The inventory binds package graph SHA-256, exact package
paths, all manifest relationship IDs, media types, expanded lengths, raw content SHA-256,
resource/control kinds, dispositions, signature state, and an active-state digest. Ordering and
JSON serialization are deterministic and bounded.

The reviewed paragraph-namespace controls are:

- ole, with exact objectType, binaryItemIDRef, and optional canonical hasMoniker;
- video, with exact Local/0 resource or Web/1 external semantics and optional poster;
- btn, comboBox, listBox, and edit, including a non-disclosing command-presence flag;
- script only outside an equation parent. Equation script is mathematical source and is not
  promoted to active macro content.

Each active element also has a hash of its exact source span. Namespace lookalikes, duplicated or
oversized attributes, invalid enum/boolean forms, XML targets, dangling manifest IDs, and one
resource used simultaneously as incompatible active kinds fail closed.

## Resource and activation policy

Opaque OLE, audio, video, executable, script/macro, and unclassified application/octet-stream
parts are inventoried. Known MP4, MPEG audio, WAV, AVI, Ogg and WebM signatures are checked; a
known declaration/signature mismatch is rejected rather than downgraded to opaque. Executable
signatures and executable/script paths or media types are quarantined. Unrecognized opaque binary
is review-required. Compound File Binary OLE is never unpacked or interpreted; the ZIP reader
admits it only so the inventory can hash and preserve it.

PreservePassive describes byte handling, not permission to play content. The normal product tier
always denies OLE activation, multimedia playback, embedded executable launch, script/macro
execution, form commands, and external links. There is no creation, dispatch, fetch, playback, or
execution API in this profile.

## Preservation

Source and target inventories may have different package graph hashes because unrelated document
parts can change. Preservation succeeds only when every active resource has the same path,
relationship set, media type, length and raw digest, and every active control has the same
document part, kind, disposition, reference/external semantics and exact element digest. Element
ordinals are diagnostic locations and may shift after unrelated XML insertion. Addition, removal,
retargeting, command change, external-state change or payload change fails.

## Evidence boundary

The local Hancom OWPML model at commit
1453388472c703a4b299a0834f425cdac16644b9 statically establishes OLE/video attributes, enums,
run element names, and form command ownership. It does not prove current Hangul behavior.

package_inventory_implemented=true, activation_denial_implemented=true,
opaque_binary_preservation_check=true, and synthetic_security_corpus_pass=true.
actual_security_corpus=false, actual_hwpx=false, actual_hangul=false, save_reopen=false,
property_readback=false, render=false, automation=false, differential=false,
p08_08_implementation_complete=true, p08_08_green=false, p08_complete=false,
production_ready=false, and product_complete=false.

Reasoning level: max. P08-09's complete 58-row object conformance implementation remains max.

