"""Intent and pre-GO ordering mocks; no live journal, Docker or private values."""
import ast
import hashlib
import io
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import conservative_maintenance as c
import sql_container_ownership as subject

NONCE = "12345678-1234-4234-8234-123456789abc"
RUN = "87654321-4321-4321-8321-cba987654321"


class SQLContainerOwnershipTests(unittest.TestCase):
    def intent(self, case="approval"):
        return subject.make_intent(NONCE, case, RUN)

    def factory(self, writer):
        delegated = Mock(return_value="original-delegate-result")
        class Original:
            def __init__(self):
                self.docker = "fixture-docker"
            def __call__(self, args, **kwargs):
                return delegated(args, **kwargs)
        return subject.journalled_factory_type(Original, NONCE, "approval", writer=writer)(), delegated, Original

    def checked(self):
        return {"intent": self.intent(), "journal_fsync_before_delegate_completed": True}

    def test_canonical_intent_binds_nonce_case_run_label_and_fixed_image(self):
        for case in subject.CASES:
            row = self.intent(case)
            self.assertEqual(subject.validate_intent(row, NONCE, case), row)
            self.assertEqual(row["container_name"], subject.CASES[case][0]+RUN)
            self.assertEqual(set(row), subject.FIELDS)

    def test_extra_fields_wrong_epoch_or_other_case_are_rejected(self):
        for mutation in ({"private": "PRIVATE_FIXTURE"}, {"parent_nonce": RUN}, {"case": "trust"},
                {"image_id": "sha256:"+"0"*64}, {"container_name": "other"}):
            row = dict(self.intent(), **mutation)
            with self.assertRaises(ValueError):
                subject.validate_intent(row, NONCE, "approval")

    def test_only_lowercase_v4_UUID_is_a_journal_path_component(self):
        for nonce in ("..", "", None, NONCE.upper(), NONCE.replace("4234", "1234")):
            with self.assertRaises(ValueError):
                subject.uuid_value(nonce)

    def test_both_original_driver_run_arrays_match_exact_intent_guard(self):
        pairs = (("approval", "tools/p09/run_formula_issuer_live_sql_probe.py"),
            ("trust", "tools/p09/run_formula_issuer_authority_sql_probe.py"))
        for case, path in pairs:
            row = self.intent(case)
            tree = ast.parse((c.ROOT/path).read_text(encoding="utf-8"))
            calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name) and node.func.id == "command" and node.args
                and isinstance(node.args[0], ast.List) and len(node.args[0].elts) > 1
                and isinstance(node.args[0].elts[1], ast.Constant) and node.args[0].elts[1].value == "run"]
            self.assertEqual(len(calls), 1)
            actual = eval(compile(ast.Expression(calls[0].args[0]), path, "eval"),
                {"docker": "fixture-docker", "name": row["container_name"], "LABEL": row["label_key"],
                    "run_id": RUN, "IMAGE": subject.IMAGE})
            self.assertEqual(actual, subject.run_arguments("fixture-docker", row))
            self.assertEqual(subject.intent_from_run(NONCE, case, actual, "fixture-docker"), row)

    def test_run_pull_port_image_label_or_inline_secret_drift_cannot_get_GO(self):
        original = subject.run_arguments("fixture-docker", self.intent())
        for position, value in ((4, "always"), (12, "0.0.0.0::5432"), (8, "other=PRIVATE_FIXTURE"),
                (29, "POSTGRES_PASSWORD=PRIVATE_FIXTURE"), (30, "other-image")):
            actual = list(original)
            actual[position] = value
            with self.assertRaises(ValueError):
                subject.intent_from_run(NONCE, "approval", actual, "fixture-docker")

    def test_factory_journals_before_delegate_preserves_same_arguments_and_env(self):
        trace = []
        writer = Mock(side_effect=lambda row: trace.append("journal") or self.checked())
        factory, delegated, original = self.factory(writer)
        delegated.side_effect = lambda *args, **kwargs: trace.append("delegate") or "same"
        args, env = subject.run_arguments("fixture-docker", self.intent()), {"POSTGRES_PASSWORD": "PRIVATE_FIXTURE"}
        self.assertEqual(factory(args, env=env), "same")
        self.assertIsInstance(factory, original)
        self.assertEqual(trace, ["journal", "delegate"])
        delegated.assert_called_once_with(args, env=env)
        self.assertNotIn("PRIVATE_FIXTURE", json.dumps(writer.call_args.args[0]))

    def test_non_creation_command_delegates_without_writing_intent(self):
        writer = Mock()
        factory, delegated, _ = self.factory(writer)
        args = ["fixture-docker", "image", "inspect", subject.IMAGE]
        factory(args, mode="same")
        writer.assert_not_called()
        delegated.assert_called_once_with(args, mode="same")

    def test_write_or_fsync_failure_never_delegates_original_launcher(self):
        for error in (OSError("PRIVATE_FIXTURE"), ValueError("SQL_OWNED_INTENT_EXCLUSIVE_REQUIRED")):
            factory, delegated, _ = self.factory(Mock(side_effect=error))
            with self.assertRaises((ValueError, OSError)):
                factory(subject.run_arguments("fixture-docker", self.intent()))
            delegated.assert_not_called()

    def test_false_fsync_or_readback_binding_cannot_delegate_GO(self):
        for checked in ({"intent": self.intent(), "journal_fsync_before_delegate_completed": False},
                {"intent": self.intent("trust"), "journal_fsync_before_delegate_completed": True}):
            factory, delegated, _ = self.factory(Mock(return_value=checked))
            with self.assertRaises(ValueError):
                factory(subject.run_arguments("fixture-docker", self.intent()))
            delegated.assert_not_called()

    def test_exclusive_file_creation_refuses_existing_journal(self):
        path = Mock()
        path.exists.return_value = True
        with patch.object(subject, "journal_path", return_value=path):
            with self.assertRaisesRegex(ValueError, "SQL_OWNED_INTENT_EXCLUSIVE_REQUIRED"):
                subject.write_intent(self.intent())
        path.open.assert_not_called()

    def test_write_flush_fsync_and_full_readback_order_is_checked(self):
        trace = []
        row = self.intent()
        raw = (json.dumps(row, sort_keys=True, separators=(",", ":"))+"\n").encode()
        stream = Mock()
        stream.write.side_effect = lambda data: trace.append("write") or len(data)
        stream.flush.side_effect = lambda: trace.append("flush")
        stream.fileno.return_value = 11
        manager = Mock()
        manager.__enter__ = Mock(return_value=stream)
        manager.__exit__ = Mock(return_value=False)
        path = Mock()
        path.exists.return_value = False
        path.open.return_value = manager
        checked = {"intent": row, "journal_pin": {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}}
        with patch.object(subject, "journal_path", return_value=path), \
                patch.object(subject.os, "fsync", side_effect=lambda fd: trace.append("fsync")), \
                patch.object(subject, "load_intent", side_effect=lambda *args: trace.append("readback") or checked):
            self.assertTrue(subject.write_intent(row)["journal_fsync_before_delegate_completed"])
        self.assertEqual(trace, ["write", "flush", "fsync", "readback"])
        path.open.assert_called_once_with("xb")

    def test_bounded_read_rejects_oversize_truncated_or_duplicate_JSON(self):
        row = json.dumps(self.intent()).encode()
        for raw in (b"x"*4097, row[:-1], row[:-1]+b',"case":"approval"}'):
            path = Mock()
            path.is_file.return_value = True
            path.open.return_value = io.BytesIO(raw)
            with patch.object(subject, "journal_path", return_value=path):
                with self.assertRaises(ValueError):
                    subject.load_intent(NONCE, "approval")

    def test_parent_link_or_junction_is_rejected_before_open(self):
        for method in ("is_symlink", "is_junction"):
            with patch.object(subject.Path, method, return_value=True):
                with self.assertRaisesRegex(ValueError, "SQL_OWNED_INTENT_PATH_LINK"):
                    subject.journal_path(NONCE)
