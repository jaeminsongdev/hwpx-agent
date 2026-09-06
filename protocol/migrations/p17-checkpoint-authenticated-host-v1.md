# P17 checkpoint authenticated host v1

This is the first authenticated private checkpoint host contract. There is no predecessor host
payload or state to migrate. It accepts only the exact canonical v3 private checkpoint bytes and
encodes the existing v1 bound remote-sync response.

One valid short-lived service credential is consumed before canonical body decoding. A caller whose
body is malformed after successful authentication must obtain a fresh credential. This prevents a
failed exchange from reusing the same service bearer and is covered by a negative test.

The host preserves the existing division between definitive rejection and uncertain outcome. An
authorized stale head is a bound conflict, while an alias, non-idle mirror or service denial is a
bound rejection. Repository failure, uncertain dispatch and an invalid post-dispatch receipt are
unavailable because the host cannot safely assert whether a mutation occurred.

Future versions may add a network listener, asymmetric identity-provider adapter, durable
credential provider and a transactional reservation spanning admission and dispatch. They must not
weaken request bounds, one-time token consumption, canonical decoding, authenticated tenant/subject
binding, exact mirror/head admission, response digest binding or uncertain-outcome handling.
