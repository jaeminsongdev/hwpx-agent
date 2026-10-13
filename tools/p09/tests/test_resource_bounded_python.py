"""P145 admission/order/output tests. No actual Rust, DB or native application."""
from argparse import Namespace
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import Mock

import run_resource_bounded_python as bootstrap


def args(mode="current-audit", **changes):
    result = Namespace(mode=mode,
        target_receipt="implementation/p09/evidence/p09-144-corpus-consumer.progress.v1.json",
        build_receipt=None, source_index=None, input_mode=None, expected_outcome=None)
    for name, value in changes.items():
        setattr(result, name, value)
    return result


class ResourceBootstrap(unittest.TestCase):
    def test_audit_has_only_closed_receipt_argument(self):
        target, arguments = bootstrap.target_arguments(args())
        self.assertEqual(target, bootstrap.TARGETS["current-audit"][0])
        self.assertEqual(arguments, ["--receipt", args().target_receipt])

    def test_arbitrary_target_or_path_is_rejected(self):
        for value in (args(mode="arbitrary"), args(target_receipt="../outside.json"),
            args(target_receipt="C:/outside.json"), args(target_receipt=args().target_receipt + "/../x")):
            with self.subTest(mode=value.mode, path=value.target_receipt), self.assertRaises(ValueError):
                bootstrap.target_arguments(value)

    def test_audit_cannot_smuggle_build_or_SQL_options(self):
        for changes in ({"build_receipt": "x"}, {"source_index": 0}, {"input_mode": "original"},
            {"expected_outcome": "unchanged"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                bootstrap.target_arguments(args(**changes))

    def test_SQL_source_and_mode_boundary(self):
        valid = args(mode="sql", target_receipt="implementation/p09/evidence/p09-144-corpus-consumer-run03.v1.json",
            build_receipt="target/p09-121-resource-optimized/p143-issuer-product-build-r8.json",
            source_index=35, input_mode="original", expected_outcome="unchanged")
        target, arguments = bootstrap.target_arguments(valid)
        self.assertEqual(target, bootstrap.TARGETS["sql"][0])
        self.assertIn("35", arguments)
        for name, value in (("source_index", -1), ("source_index", 36), ("source_index", True),
            ("input_mode", "arbitrary"), ("expected_outcome", "anything"), ("build_receipt", "../x")):
            bad = Namespace(**vars(valid))
            setattr(bad, name, value)
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                bootstrap.target_arguments(bad)

    def test_unit_rejects_SQL_options(self):
        unit = args(mode="unit", target_receipt="target/p09-121-resource-optimized/p144-corpus-unit-run2.json",
            build_receipt="target/p09-121-resource-optimized/p143-typed-route-unit-build-r3.json")
        self.assertEqual(bootstrap.target_arguments(unit)[0], bootstrap.TARGETS["unit"][0])
        unit.source_index = 0
        with self.assertRaises(ValueError):
            bootstrap.target_arguments(unit)

    def test_stable_window_resets_after_hot_sample(self):
        resource = Mock(stop=threading.Event(), reason=None)
        resource.sample.side_effect = [{"system_cpu_percent": cpu, "available_ram_mib": 8192}
            for cpu in (50, 51, 50, 50, 50)]
        self.assertEqual(bootstrap.admit(resource, sleep=lambda _: None, clock=lambda: 0), 3)
        self.assertEqual(resource.sample.call_count, 5)

    def test_resource_stop_and_timeout_do_not_admit(self):
        resource = Mock(stop=threading.Event(), reason="STOP_SUSTAINED_SYSTEM_CPU")
        resource.stop.set()
        resource.sample.return_value = {"system_cpu_percent": 90, "available_ram_mib": 8192}
        with self.assertRaisesRegex(ValueError, "STOP_SUSTAINED_SYSTEM_CPU"):
            bootstrap.admit(resource, sleep=lambda _: None, clock=lambda: 0)
        clock = Mock(side_effect=[0, 21])
        resource.stop.clear()
        with self.assertRaisesRegex(ValueError, "bootstrap_idle_window_not_admitted"):
            bootstrap.admit(resource, sleep=lambda _: None, clock=clock)

    def test_output_is_discarded_and_bounded_in_UTF8_bytes(self):
        output = bootstrap.BoundedOutput(limit=3)
        self.assertEqual(output.write("가"), 1)
        with self.assertRaisesRegex(ValueError, "target_output_limit_exceeded"):
            output.write("x")
        self.assertFalse(hasattr(output, "getvalue"))

    def test_same_process_execution_restores_argv_and_preserves_failure(self):
        before = sys.argv
        def runner(path, run_name):
            self.assertEqual(run_name, "__main__")
            self.assertEqual(sys.argv[1:], ["--receipt", "x"])
            self.assertTrue(path.endswith("verify_formula_issuer_corpus_current.py"))
            print("discarded metadata")
            raise SystemExit(7)
        code, output = bootstrap.run_target(bootstrap.TARGETS["current-audit"][0], ["--receipt", "x"], runner=runner)
        self.assertEqual(code, 7)
        self.assertGreater(output["stdout_bytes_discarded"], 0)
        self.assertIs(sys.argv, before)

    def test_non_numeric_exit_cannot_be_accepted(self):
        def runner(*_args, **_kwargs):
            raise SystemExit("sensitive failure text")
        with self.assertRaisesRegex(ValueError, "target_exit_not_numeric"):
            bootstrap.run_target(bootstrap.TARGETS["current-audit"][0], [], runner=runner)

    def test_limits_are_before_hash_admission_and_target(self):
        # 보존된 target을 수정하거나 런타임 monkeypatch하지 않는 source boundary.
        source = (bootstrap.ROOT / bootstrap.SELF).read_text(encoding="utf-8")
        body = source[source.index("def main(args):"):source.index('\nif __name__ == "__main__":')]
        self.assertLess(body.index("resources = Resources()"), body.index("admit(resources)"))
        self.assertLess(body.index("admit(resources)"), body.index("freeze = [pin(path)"))
        self.assertLess(body.index("freeze = [pin(path)"), body.index("run_target(target, arguments)"))
        self.assertNotIn("setattr", body)
        self.assertNotIn("exec(", source)


if __name__ == "__main__":
    unittest.main()
