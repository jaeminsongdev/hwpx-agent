from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_source_successor_pairs_v1 as pairs

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/p17/frozen_current_source_v12.py"
SPEC = importlib.util.spec_from_file_location("frozen_current_source_v12_test", PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FrozenCurrentSourceV12Tests(unittest.TestCase):
    def test_exact_qualification_exposes_bounded_current_hashes(self) -> None:
        values = MODULE.verified_source_hashes(ROOT)
        self.assertEqual(len(values), 121)
        self.assertEqual(
            values["deny.toml"],
            "a939acc670946e472480d5dde52b0bc19caa326abd14418e90b522deb03025bd",
        )
        self.assertEqual(
            values["Cargo.lock"],
            "180eb9a48c33c51bf1325b824115f40039a064aa94dc200af0dca0f60f43c1ed",
        )

    def test_exact_inspector_sources_admit_only_qualified_v12_pairs(self) -> None:
        contract = MODULE.fixed_json(
            ROOT,
            "implementation/p15/p15-inspector-staging-contract-v1.json",
            "09335ea42021c782f75010d7e873de11c36c834bb33ba8cafde529f824e3b907",
        )
        replacements = pairs.v12_replacements(ROOT, contract["source_locks"])
        self.assertEqual(
            replacements["deny.toml"],
            (
                "1b7f0c7a65ba80242847fbb24483fa82708f28b361e425c76c48233d52073ef3",
                "a939acc670946e472480d5dde52b0bc19caa326abd14418e90b522deb03025bd",
            ),
        )

    def test_git_blob_mismatch_rejects_qualified_replacement(self) -> None:
        contract = MODULE.fixed_json(
            ROOT,
            "implementation/p15/p15-inspector-staging-contract-v1.json",
            "09335ea42021c782f75010d7e873de11c36c834bb33ba8cafde529f824e3b907",
        )
        with patch.object(MODULE, "git_blob_digest", return_value="0" * 64):
            with self.assertRaisesRegex(MODULE.FrozenSourceError, "source.current"):
                MODULE.verified_replacements(ROOT, contract["source_locks"])


if __name__ == "__main__":
    unittest.main()
