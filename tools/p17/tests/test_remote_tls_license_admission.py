from __future__ import annotations

import copy
import tomllib
import unittest

from tools.p17 import validate_remote_tls_license_admission as validator


class RemoteTlsLicenseAdmissionTests(unittest.TestCase):
    def test_current_exact_policy_metadata_license_files_and_cargo_deny_pass(self) -> None:
        result = validator.verify()
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["package_count"], 3)
        self.assertTrue(result["cargo_deny_all"])
        self.assertFalse(result["global_isc_allowance"])
        self.assertFalse(result["actual_external_remote_network"])
        self.assertFalse(result["production"])
        self.assertFalse(result["p17_06_complete"])

    def test_global_name_only_version_or_additional_exception_fails(self) -> None:
        document = tomllib.loads(
            (validator.ROOT / "deny.toml").read_text(encoding="utf-8")
        )
        mutations = []
        global_allow = copy.deepcopy(document)
        global_allow["licenses"]["allow"].append("ISC")
        mutations.append(global_allow)
        name_only = copy.deepcopy(document)
        name_only["licenses"]["exceptions"][0]["crate"] = "ring"
        mutations.append(name_only)
        another_version = copy.deepcopy(document)
        another_version["licenses"]["exceptions"][1]["crate"] = (
            "rustls-webpki@0.103.16"
        )
        mutations.append(another_version)
        additional = copy.deepcopy(document)
        additional["licenses"]["exceptions"].append(
            {"allow": ["ISC"], "crate": "other@1.0.0"}
        )
        mutations.append(additional)
        for mutated in mutations:
            with self.subTest(mutated=mutated["licenses"]):
                with self.assertRaises(validator.LicenseAdmissionError):
                    validator.validate_deny_document(mutated)

    def test_lock_version_source_and_checksum_tampering_fails(self) -> None:
        document = tomllib.loads(
            (validator.ROOT / "Cargo.lock").read_text(encoding="utf-8")
        )
        for key, value in [
            ("version", "0.17.15"),
            ("source", "git+https://invalid.example/repository"),
            ("checksum", "0" * 64),
        ]:
            mutated = copy.deepcopy(document)
            package = next(item for item in mutated["package"] if item["name"] == "ring")
            package[key] = value
            with self.subTest(key=key):
                with self.assertRaises(validator.LicenseAdmissionError):
                    validator.validate_lock(mutated)

    def test_contract_exception_or_gate_promotion_fails(self) -> None:
        contract, _ = validator.load_json(
            validator.ROOT, validator.CONTRACT_RELATIVE, "contract"
        )
        for group, key, value in [
            ("policy", "global_allowlist_contains_isc", True),
            ("exceptions", 0, {**contract["exceptions"][0], "crate": "ring"}),
            ("gate_decision", "actual_external_remote_network", True),
            ("gate_decision", "production", True),
            ("gate_decision", "p17_06_complete", True),
            ("gate_decision", "product_complete", True),
        ]:
            mutated = copy.deepcopy(contract)
            mutated[group][key] = value
            with self.subTest(group=group, key=key):
                with self.assertRaises(validator.LicenseAdmissionError):
                    validator.validate_contract(mutated)

    def test_evidence_license_file_privacy_and_claim_tampering_fails(self) -> None:
        evidence, raw = validator.load_json(
            validator.ROOT, validator.EVIDENCE_RELATIVE, "evidence"
        )
        for group, key, value in [
            ("packages", 0, {**evidence["packages"][0], "license_file_bytes": 500}),
            ("privacy", "absolute_registry_path_recorded", True),
            ("claims", "global_isc_allowance", True),
            ("claims", "actual_external_remote_network", True),
            ("claims", "product_complete", True),
        ]:
            mutated = copy.deepcopy(evidence)
            mutated[group][key] = value
            with self.subTest(group=group, key=key):
                with self.assertRaises(validator.LicenseAdmissionError):
                    validator.validate_evidence(mutated, raw)
        with self.assertRaises(validator.LicenseAdmissionError):
            validator.validate_evidence(evidence, raw + b"Authorization: secret")


if __name__ == "__main__":
    unittest.main()
