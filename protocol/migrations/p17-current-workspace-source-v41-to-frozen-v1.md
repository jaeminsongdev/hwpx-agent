# P17 current workspace source v41 to frozen verifier migration

The mutable v41 generator remains historical evidence. The frozen verifier composes immutable v40
and the frozen durable-push v15 verifier, then reads the v41 qualification, source receipt,
implementation, runtime-qualification and guard blobs through bounded Git object access.

The migration preserves twenty implementation sources, six runtime-qualification sources, three
guards and twenty-eight exact successors. Unknown paths, duplicate keys, missing ancestry,
unbounded blobs, digest drift, unexpected overlaps and claim expansion fail closed.

No durable-pull, remote-network, persistent-credential, registered-host, production, P17-06 or
product-completion claim is introduced.
