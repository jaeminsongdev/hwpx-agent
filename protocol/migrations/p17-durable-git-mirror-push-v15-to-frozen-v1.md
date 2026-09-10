# P17 durable Git mirror push v15 to frozen verifier migration

The mutable v15 generator remains historical evidence. The frozen verifier selects full commit
identities and reads qualification, receipt, implementation and guard blobs only through bounded
Git object access. Existing documents and receipts are not rewritten in place.

The migration preserves the exact 27-check receipt and its original byte representation. It binds
thirty-nine implementation sources to the source commit and three guard sources to the
qualification commit. Unknown paths, duplicate JSON keys, oversized blobs, missing ancestry,
digest drift, claim expansion and receipt mutation fail closed.

This migration promotes no remote-network, durable-pull, persistent-credential, registered-host,
Hangul, production, P17-06 or product-completion claim.
