# P17 Windows credential custody v1 migration

This additive private contract introduces an independent Windows-only crate implementing
`local-sync`'s existing `RemoteCredentialProvider` for one explicit generic Windows Credential
Manager target. Existing `local-sync` source and callers using `SingleUseCredentialProvider`
remain wire-compatible and unchanged.

The new target is deterministically derived from two bounded opaque identifiers as
`hwpx-agent.remote-sync:{account}:{service}`. Both identifiers exclude the colon delimiter, path
separators, whitespace, controls and non-ASCII bytes. Migration must not import environment
variables, plaintext files, command-line values or existing credential entries. Product code is
retrieval-only; a trusted installer or identity broker owns creation, rotation and deletion.

The stored value is only the compact JWT body. Retrieval accepts at most 2,560 bytes, matching
`CRED_MAX_CREDENTIAL_BLOB_SIZE`, constructs the exact `Bearer ` header inside zeroizing storage,
and consumes the provider instance on the first attempt whether retrieval succeeds or fails.
Missing/inaccessible platform state is `Unavailable`; malformed or ambiguous state is `Rejected`.

Rollback removes the independent crate, its workspace membership and Windows-target dependencies
only. It never searches for, deletes or rewrites Credential Manager entries. Any credential
installed by a later trusted lifecycle must be removed by that lifecycle using its exact
independently retained target.

The v1 qualification may create only one unique synthetic `Local`-persistence entry after exact
`NoEntry` preflight, and must delete it and prove exact `NoEntry` afterward. This proves the local
custody mechanism, not a real service credential, issuance, rotation, remote TLS, registered host,
production authentication, P17-06 completion or product completion.
