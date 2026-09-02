from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def write_new(path: Path, content: bytes, mode: int) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-output", required=True, type=Path)
    parser.add_argument("--public-output", required=True, type=Path)
    args = parser.parse_args()

    private_key = Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    raw_public = public_key.public_bytes_raw()
    write_new(args.private_output, private_pem, 0o600)
    try:
        write_new(args.public_output, public_pem, 0o644)
    except BaseException:
        args.private_output.unlink(missing_ok=True)
        raise
    print(
        "schema=hwpx-agent.direct-route-keygen-receipt/v1 "
        "state=pass "
        f"key_id=ed25519-sha256-{hashlib.sha256(raw_public).hexdigest()} "
        f"public_key_raw_hex={raw_public.hex()} "
        f"public_pem_sha256={hashlib.sha256(public_pem).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
