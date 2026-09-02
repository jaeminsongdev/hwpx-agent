from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True, type=Path)
    parser.add_argument("--private-key", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = args.payload.read_bytes()
    key_value = serialization.load_pem_private_key(
        args.private_key.read_bytes(), password=None
    )
    if not isinstance(key_value, Ed25519PrivateKey):
        raise SystemExit("P04_ROUTE_SIGNING_KEY_TYPE_INVALID")
    signature = key_value.sign(payload)
    output = (signature.hex() + "\n").encode("ascii")
    descriptor = os.open(
        args.output,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(output)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            args.output.unlink()
        except FileNotFoundError:
            pass
        raise
    print(
        "schema=hwpx-agent.direct-route-signing-receipt/v1 "
        "state=pass "
        f"payload_sha256={hashlib.sha256(payload).hexdigest()} "
        f"signature_sha256={hashlib.sha256(signature).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
