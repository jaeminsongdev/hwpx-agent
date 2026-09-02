# ID/reference index contract migration: v0 to v1

## Status

- Migration: initial typed part-scoped ID/reference index
- Producer: `hwpx-package` P03-06
- Profile: `hancom-2020-hwpml-2011-core/v1`
- Consumer: P03-07 patch engine and later ID allocator
- Compatibility: additive; no v0 `IdIndex` existed

## v1 contract

v1 rebuilds preservation evidence, scans only `TokenStable` XML and validates token SHA-256 before indexing. Identity is scoped by canonical part, typed `IdKind` and private normalized value. Decimal values normalize leading zeroes; text values remain exact after XML normalization and conservative syntax validation.

Public declaration/reference records contain only safe structural location, kind, target part and resolved declaration index. Raw or normalized ID strings are private and omitted from `Debug`, errors and validation reports.

## Rule scope

The initial profile contains current 한글 2020 HWPML 2011 core rules for OPF manifest IDs, header resource IDs and paragraph-to-header references. OPF namespace matching allowlists only the exact standard URI and the exact trailing-slash URI observed in current 2020 output. Cross-part HWPML targets use a fixed canonical `Contents/header.xml` selector; v1 does not parse path or URI text from an ID reference.

Exact fields observed using empty, zero or unsigned-32 maximum as absent/unassigned/no-target sentinels are versioned explicitly. A nonzero context-dependent `heading@idRef` is rejected rather than guessed as numbering or bullet.

The seven current-2020 `fontface@lang` collections are distinct ID kinds. Equal numeric font IDs across languages are valid and each `fontRef` language attribute resolves only to its matching kind.

Unsupported namespaces are preserved without interpretation. An unknown exact `id`/`idRef`/`*IDRef` shape inside a supported namespace is a validation failure, not a guessed rule or silent success.

## Failure semantics

Duplicate, dangling, wrong-type, malformed, unknown ID-like and unavailable-target issues prevent construction of `IdIndex`. Stable diagnostics expose locations and types only. Rejected preservation parts, identity mismatch, invalid/overflowed limits and allocation failures are hard errors with no partial index.

## Upgrade rule

Adding or changing QName rules, reusing this profile for another Hancom version, exposing ID values, allowing a partial-valid index, accepting path/fragment syntax, changing numeric normalization, or performing allocation/renumbering requires a new profile/contract version and migration.
