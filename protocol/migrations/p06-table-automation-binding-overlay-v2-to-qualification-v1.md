# P06 table automation v2 qualification migration

The reviewed v2 ActionTable overlay remains an immutable candidate input. Qualification creates a
separate private overlay so source review and runtime promotion cannot be confused.

Promotion requires all 61 exact capability identities, the exact Hangul 2020 build and executable,
an observed semantic pre/post change, a closed disposable-document rollback or the already frozen
chart lifecycle/retry, and an existing direct `oracle_verified` result for the same capability.

The public receipt contains hashes and states only. Raw Action/ParameterSet identifiers, document
content, private trace paths and absolute local paths remain private. The scope is bounded current-PC
development; it does not claim arbitrary user-document compatibility, another version, production,
or total product completion.
