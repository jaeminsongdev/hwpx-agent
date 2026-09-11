# P17 current workspace source v48 to frozen v1 migration

This private successor replaces mutable v48 qualification authority with immutable Git-object
verification. It does not change any public protocol, credential wire, broker record payload, issuer
state or vault content.

The verifier requires the exact base and qualification commits and their ancestry. Qualification,
current-host, receipt, implementation, runtime/component and guard bytes are read from those Git
commits with finite bounds and exact SHA-256 checks. Duplicate JSON keys, count/path drift, component
claim promotion and missing history fail closed.

Rollback leaves issuer logs, broker logs, Windows credentials and all qualification evidence
untouched. External issuer, real credentials, registered-host, power-loss and production admission
remain separate future operations.
