"""Published current targets and exact response negatives; no live queries."""
import copy
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import conservative_maintenance as c
import current_sql_owned_absence as subject


class CurrentSQLOwnedAbsenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def load(name):
            return json.loads((c.ROOT/name).read_text(encoding="utf-8"))
        cls.proof = load(subject.AUDIT_PIN["path"])
        cls.runs = {case: load(name) for (case, mode), name in subject.receipts.CURRENT_RUNS.items()}
        cls.build = load(subject.receipts.build_contract.CURRENT_BUILD_PIN["path"])
        cls.manifest = load(subject.receipts.MANIFEST)

    def targets(self, proof=None, runs=None):
        return subject.reference_inventory(self.proof if proof is None else proof, self.runs if runs is None else runs)

    def missing(self, refs):
        return "".join("Error: No such object: "+name+"\n" for name in refs)

    def test_three_published_current_originals_have_six_exact_references(self):
        descriptors, refs = self.targets()
        self.assertEqual(len(descriptors), 3)
        self.assertEqual(len(set(refs)), 6)
        self.assertEqual(refs, [value for case in ("approval", "trust", "policy")
            for value in (self.runs[case]["container_id"], self.runs[case]["container_name"])])

    def test_boolean_or_wrong_source_mode_or_case_is_rejected(self):
        for change in ({"source_index": False}, {"source_index": 1}, {"input_mode": "numeric_derivative"}, {"live_case": "policy"}):
            runs = dict(self.runs, approval=dict(self.runs["approval"], **change))
            with self.assertRaises(ValueError):
                self.targets(runs=runs)

    def test_invalid_uuid_name_image_or_id_is_rejected(self):
        for change in ({"run_id": "foreign"}, {"container_name": "foreign"}, {"image_id": "sha256:"+"0"*64},
                {"container_id": "0"*63}, {"container_removed": False}):
            runs = dict(self.runs, approval=dict(self.runs["approval"], **change))
            with self.assertRaises(ValueError):
                self.targets(runs=runs)

    def test_missing_case_or_duplicate_reference_is_rejected(self):
        with self.assertRaises(ValueError):
            self.targets(runs={"approval": self.runs["approval"]})
        runs = dict(self.runs, trust=dict(self.runs["trust"], container_id=self.runs["approval"]["container_id"]))
        with self.assertRaises(ValueError):
            self.targets(runs=runs)

    def test_generic_readonly_inspect_is_bound_to_local_endpoint(self):
        _, refs = self.targets()
        args = subject.query_arguments("C:/fixture/docker.exe", refs)
        self.assertEqual(args[1:6], ["--host", subject.LOCAL_DOCKER_HOST, "inspect", "--format", "{{.Id}}"])
        self.assertNotIn("--type", args)
        self.assertEqual(args[6:], refs)

    def test_all_missing_name_and_id_responses_are_required(self):
        _, refs = self.targets()
        row = subject.validate_response(SimpleNamespace(returncode=1, stdout="", stderr=self.missing(list(reversed(refs)))), refs)
        self.assertEqual(row, [{"reference": name, "absent": True} for name in refs])

    def test_partial_duplicate_foreign_absence_responses_are_rejected(self):
        _, refs = self.targets()
        for found in (refs[:-1], refs[:1]*6, refs[:-1]+["0"*64]):
            with self.assertRaises(ValueError):
                subject.validate_response(SimpleNamespace(returncode=1, stdout="", stderr=self.missing(found)), refs)

    def test_exact_empty_template_flush_decodes_only_transport_not_shared_policy(self):
        _, refs = self.targets()
        result = SimpleNamespace(returncode=1, stdout="\n", stderr=self.missing(refs))
        self.assertEqual(subject.validate_response(result, refs),
            [{"reference": name, "absent": True} for name in refs])
        self.assertTrue(subject.response_diagnostics(result, refs)["stdout_exact_empty_template_flush"])
        with self.assertRaises(ValueError):
            subject.bounded.validate_absence(result.returncode, result.stdout, result.stderr, refs, subject.ERROR)

    def test_template_flush_never_accepts_other_whitespace_or_exit_codes(self):
        _, refs = self.targets()
        for stdout in (" ", " \n", "\n\n", "\r\n", "\t\n", "\x00\n", refs[0]+"\n"):
            with self.subTest(stdout=repr(stdout)), self.assertRaises(ValueError):
                subject.validate_response(SimpleNamespace(returncode=1, stdout=stdout, stderr=self.missing(refs)), refs)
        for code in (0, True, False, 2, -1, 1.0, "1", None):
            with self.subTest(code=repr(code)), self.assertRaises(ValueError):
                subject.validate_response(SimpleNamespace(returncode=code, stdout="\n", stderr=self.missing(refs)), refs)

    def test_template_flush_still_requires_all_exact_absences_no_daemon_error(self):
        _, refs = self.targets()
        for stderr in (self.missing(refs[:-1]), self.missing(refs[:1]*6), self.missing(refs[:-1]+["0"*64]),
                self.missing(refs)+"\n", self.missing(refs)+"Error response from daemon: unavailable\n",
                "daemon unavailable", "", self.missing(refs)+"PRIVATE_FIXTURE\n"):
            with self.subTest(stderr_length=len(stderr)), self.assertRaises(ValueError):
                subject.validate_response(SimpleNamespace(returncode=1, stdout="\n", stderr=stderr), refs)

    def test_existing_or_daemon_failure_is_not_absence(self):
        _, refs = self.targets()
        for result in (SimpleNamespace(returncode=0, stdout="", stderr=self.missing(refs)),
                SimpleNamespace(returncode=True, stdout="", stderr=self.missing(refs)),
                SimpleNamespace(returncode=1, stdout="existing\n", stderr=self.missing(refs)),
                SimpleNamespace(returncode=1, stdout="", stderr="daemon unavailable")):
            with self.assertRaises(ValueError):
                subject.validate_response(result, refs)

    def test_failed_or_promoted_audit_does_not_authorize_current_targets(self):
        for change in ({"source_freeze_exact_after": False}, {"resource_watcher_cleanup_confirmed": False},
                {"product_complete": True}, {"P09_gate": "PASS"}):
            with self.assertRaises(ValueError):
                self.targets(proof=dict(self.proof, **change))

    def test_input_binding_requires_published_byte_pin_before_query(self):
        pins = {subject.AUDIT_PIN["path"]: subject.AUDIT_PIN,
            subject.receipts.build_contract.CURRENT_BUILD_PIN["path"]: subject.receipts.build_contract.CURRENT_BUILD_PIN}
        objects = {subject.AUDIT_PIN["path"]: self.proof,
            subject.receipts.build_contract.CURRENT_BUILD_PIN["path"]: self.build, subject.receipts.MANIFEST: self.manifest}
        for slot in self.proof["original_audit_summary"]["validated_current_cases"]:
            name = slot["receipt_pin"]["path"]
            pins[name] = slot["receipt_pin"]
            objects[name] = self.runs[slot["case"]]
        reader = SimpleNamespace(pin=Mock(side_effect=lambda name: pins[name]), json=Mock(side_effect=lambda name: objects[name]))
        with patch.object(subject.receipts, "validate_current_case", wraps=subject.receipts.validate_current_case) as validator:
            descriptors, refs = subject.bind_inputs(reader)
        self.assertEqual(validator.call_count, 3)
        self.assertEqual(len(refs), 6)
        changed = dict(pins[descriptors[0]["receipt_pin"]["path"]], sha256="0"*64)
        pins[changed["path"]] = changed
        with self.assertRaisesRegex(ValueError, "CURRENT_ABSENCE_RECEIPT_BYTE_DRIFT"):
            subject.bind_inputs(reader)

    def test_response_diagnostics_never_store_unknown_text_or_accept_absence(self):
        _, refs = self.targets()
        result = SimpleNamespace(returncode=1, stdout="\n", stderr=self.missing(refs)+"PRIVATE_FIXTURE\n")
        diagnostic = subject.response_diagnostics(result, refs)
        self.assertTrue(diagnostic["stdout_only_whitespace"])
        self.assertEqual(diagnostic["stderr_other_line_count"], 1)
        self.assertEqual(diagnostic["known_missing_references"], refs)
        self.assertNotIn("PRIVATE_FIXTURE", json.dumps(diagnostic))
        with self.assertRaises(ValueError):
            subject.validate_response(result, refs)
