# P03-06 ID/reference index policy

- State: implemented for current-PC local core and approved disposable 한글 2020 validation
- Rule profile: `hancom-2020-hwpml-2011-core/v1`
- Product boundary: typed, part-scoped declaration/reference validation over P03-05 `TokenStable` XML
- Consumer: P03-07 patch conflict validation and later ID allocation

## 1. Evidence and version scope

The v1 profile is limited to the current PC target, exact 한글 2020, and the HWPML 2011 core QName/attribute pairs observed in its already-qualified disposable fixtures. Official OWPML extraction supplied schema-level corroboration, but restricted source records and raw XML are not copied into the repository or report.

The profile recognizes OPF package/manifest identity, `hwpml/2011/head` core resource declarations and references, and `hwpml/2011/paragraph` paragraph/section declarations plus fixed `Contents/header.xml` resource references. The OPF allowlist contains the specification spelling without a trailing slash and the exact trailing-slash spelling observed in current 한글 2020 output; it does not perform arbitrary URI trimming. It does not claim qualification for 한글 2022/2024, OWPML 2024 runtime output, arbitrary extension namespaces, application settings references or every future HWPML element.

Unknown attributes are never guessed from spelling. In a supported namespace, an unprofiled exact `id`/`idRef`/`*IDRef` shape is an explicit validation issue so a partially understood index cannot be published as valid. Other attributes and unsupported namespaces remain untouched and unclassified.

The already-qualified 2020 fixtures use seven independent `fontface@lang` ID domains (`HANGUL`, `LATIN`, `HANJA`, `JAPANESE`, `OTHER`, `SYMBOL`, `USER`). v1 maps their repeated `font@id` values and corresponding `fontRef` attributes to seven distinct `IdKind` values. An unknown/missing parent language is a malformed declaration, not a duplicate or guessed font domain.

The fixtures also use field-specific absent/sentinel values: empty optional `package@id`, `secPr@id` and `colPr@id`; zero for unassigned `p@id`; zero as no-target for `heading@idRef`, `secPr@memoShapeIDRef` and `secPr@outlineShapeIDRef`; and unsigned-32 maximum as no-target for `paraHead@charPrIDRef`. v1 skips those values only for those exact profiled QNames. Nonzero `heading@idRef` is rejected until its numbering/bullet discriminator is modeled; the two `secPr` references resolve normally when nonzero.

## 2. Trust chain and scan boundary

`IdIndex::build` first rebuilds P03-05 `PreservationReport` from the bounded reader and supplied graph. Any rejected preservation part blocks indexing. Only `TokenStable` XML parts are reparsed; opaque parts are never interpreted. Token SHA-256 must match preservation evidence before semantic values are inspected.

The XML safety/token limits, namespace resolution and exact source spans come from P03-03/P03-04. Attribute semantic values are retained only inside private token/index fields. Public records expose canonical package path, element/attribute ordinal, checked value span, `IdKind`, target part and resolved declaration index.

## 3. Namespace and identity model

Declaration identity is `(canonical part collision key, IdKind, normalized value)`.

- Same value in different parts is valid.
- Same numeric value in different kinds in one part is valid; current 2020 header resources use this pattern.
- Decimal IDs accept ASCII digits only and normalize leading zeroes through checked `u64` parsing.
- Text IDs are XML-normalized strings with no whitespace, controls, URI/path separators or fragment delimiters.
- Existing values are never exposed, renumbered or rewritten by P03-06.

Cross-part HWPML references in this profile do not consume a path from XML. Their target selector is the versioned fixed canonical part `Contents/header.xml`. This removes traversal, URI and external-scheme interpretation from v1. OPF `itemref@idref` resolves in the package-document part. New path-bearing reference syntax requires a new profile version and its own portable-path validation.

## 4. Validation semantics

The builder returns an `IdIndex` only when every profiled reference resolves to exactly one declaration of the expected kind. It collects deterministic non-sensitive issues for:

- duplicate declaration in the same part and kind;
- dangling reference;
- same-value declaration of the wrong kind;
- malformed value;
- unknown ID-like attribute in a supported namespace;
- missing or non-token-stable fixed target part.

Issues contain source/related locations and expected/actual kinds, never the ID value. A validation report is an error result, not a partially valid index. Package, preservation, token identity, allocation and finite-limit failures are separate hard errors with stable codes.

## 5. Finite limits and diagnostics

Validated limits bound scanned parts, declarations, references, semantic value bytes and collected issues. Zero and over-ceiling configurations are rejected rather than clamped. Vectors use fallible reservation where product code grows them.

`Debug` for XML attributes, declarations, references and the final index is summary-only. Semantic values remain private and are omitted from diagnostics. Public lookup resolves an `IdReference` only by its declaration index.

The `validate_id_index` diagnostic example accepts only explicitly supplied local fixture paths and runs the same bounded reader/graph/preservation/index chain. It never starts Hancom/COM/UI and prints no input path, XML, ID value or document text; output is limited to fixture ordinal, stable failure/issue code, profile and aggregate counts. This is the reproducible current-PC and future other-PC debugging entry point for approved fixtures.

## 6. Compatibility and remaining work

P03-01 through P03-05 APIs remain compatible. P03-04 adds a private semantic attribute value retained from the already-safe parser and a custom non-disclosing `Debug`; no public raw-value getter is added.

P03-06 does not allocate IDs, reserve ranges, renumber existing values, patch XML, serialize modified tokens, write ZIPs or claim actual user-document completeness. Extending kinds/rules, accepting an unknown ID-like shape, changing zero-sentinel semantics, adding context-dependent bullet/number resolution, or adding path/fragment reference syntax requires a versioned profile migration and negative corpus.
