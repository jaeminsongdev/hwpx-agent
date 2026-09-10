from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_p16_artifact_successor_v1 as artifact

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p17/frozen_p16_artifact_successor_v1.py"
P14_CONTRACT = ROOT / "implementation/p14/postgres/p14-artifact-service-v1.json"


def source_locks() -> list[dict[str, str]]:
    value = json.loads(P14_CONTRACT.read_text(encoding="utf-8"))
    return value["source_locks"]


class FrozenP16ArtifactSuccessorV1Tests(unittest.TestCase):
    def test_three_replacements_are_verified_from_immutable_history(self) -> None:
        replacements = artifact.verified_replacements(ROOT, source_locks())
        self.assertEqual(replacements, artifact.EXPECTED_REPLACEMENTS)
        self.assertEqual(
            replacements["crates/artifact-service/Cargo.toml"],
            (
                "13e9eaf8ab4d754f91673190b7dbf53bb968b000c8d8d33ba5d915c4d9cf72d1",
                "574c7dbfb13194183afe5664ff1bc43142e7730e0a0ce2086687d9bed981c69f",
            ),
        )

    def test_contract_tamper_fails_closed(self) -> None:
        original = artifact.frozen.git_blob

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = artifact.frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == artifact.CONTRACT_RELATIVE:
                return raw + b"\n"
            return raw

        with patch.object(artifact.frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                artifact.FrozenP16ArtifactSuccessorError, "contract.bytes"
            ):
                artifact.verified_replacements(ROOT, source_locks())

    def test_source_has_no_mutable_qualifier_or_worktree_reader(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("postgres_artifact_qualification", source)
        self.assertNotIn("read_bytes(", source)
        self.assertNotIn("read_text(", source)


if __name__ == "__main__":
    unittest.main()
