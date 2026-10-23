"""Pure argv and complete-output contracts; no child process or source mutation."""
import unittest
import component_cargo_batch_v1 as m

CARGO = r"D:\devdata\Rustup\toolchains\1.96.0-x86_64-pc-windows-msvc\bin\cargo.exe"


def group(names, *, filtered=0):
    return "running %d tests\n" % len(names) + "".join("test %s ... ok\n" % name for name in names) + (
        "\ntest result: ok. %d passed; 0 failed; 0 ignored; 0 measured; %d filtered out; finished in 0.01s\n"
        % (len(names), filtered))


class Contracts(unittest.TestCase):
    def spec(self):
        return {"reference_validation_product": ["stored::b", "stored::a"],
                "document_import_reference_targets": ["core::one"],
                "reference_source_product": ["api_one"]}

    def test_01_command_exact_allowlist_one_graph_and_original_serial_settings(self):
        args = m.command(CARGO, self.spec())
        self.assertEqual(args[:6], (CARGO, "test", "--offline", "--locked", "-j", "1"))
        self.assertEqual(args.count("-p"), 2)
        self.assertEqual(args.count("--test"), 3)
        self.assertIn("--exact", args)
        self.assertIn("--test-threads=1", args)
        self.assertNotIn("--workspace", args)
        self.assertNotIn("--all-features", args)
        self.assertEqual(args[-4:], ("core::one", "api_one", "stored::a", "stored::b"))

    def test_02_deterministic_order_without_mutating_input(self):
        first = self.spec()
        before = repr(first)
        second = dict(reversed(list(first.items())))
        second["reference_validation_product"] = ["stored::a", "stored::b"]
        self.assertEqual(m.command(CARGO, first), m.command(CARGO, second))
        self.assertEqual(repr(first), before)

    def test_03_normalized_scope_is_an_immutable_snapshot(self):
        spec = self.spec()
        normalized = m.normalize(spec)
        spec["reference_validation_product"].append("stored::later")
        self.assertEqual(dict(normalized)["reference_validation_product"], ("stored::a", "stored::b"))

    def test_04_only_explicit_component_targets_no_heavy_or_native_target(self):
        for target in ("form_stored_provider", "*", "--all-targets", "reference_validation_product ", "native011"):
            with self.assertRaises(ValueError):
                m.command(CARGO, {target: ["one"]})

    def test_05_invalid_empty_duplicate_injected_and_cross_target_case_ids(self):
        for cases in ([], ["--ignored"], ["one two"], ["one\0two"], ["one", "one"], ["x::"], ["x" * 513]):
            with self.assertRaises(ValueError):
                m.command(CARGO, {"reference_source_product": cases})
        with self.assertRaises(ValueError):
            m.command(CARGO, {"reference_source_product": ["same"], "reference_validation_product": ["same"]})

    def test_06_existing_argument_count_boundary_is_not_raised(self):
        target = "reference_source_product"
        base = len(m.command(CARGO, {target: ["one"]})) - 1
        count = m.MAX_ARGUMENTS - base
        args = m.command(CARGO, {target: ["case_%d" % i for i in range(count)]})
        self.assertEqual(len(args), m.MAX_ARGUMENTS)
        with self.assertRaises(ValueError):
            m.command(CARGO, {target: ["case_%d" % i for i in range(count + 1)]})

    def test_07_existing_utf16_argument_byte_limit_is_not_raised(self):
        names = ["case_%02d_" % i + "x" * 490 for i in range(30)]
        with self.assertRaises(ValueError):
            m.command(CARGO, {"reference_source_product": names})

    def test_08_no_run_has_no_test_execution_or_hidden_filters(self):
        args = m.command(CARGO, self.spec(), no_run=True)
        self.assertIn("--no-run", args)
        self.assertNotIn("--", args)
        self.assertNotIn("--exact", args)
        self.assertNotIn("core::one", args)

    def test_09_complete_groups_can_arrive_in_any_serial_target_order(self):
        output = group(["stored::b", "stored::a"], filtered=47) + "\n" + group(["api_one"]) + group(["core::one"])
        result = m.validate_stdout(output, self.spec())
        self.assertEqual(result["passed"], 4)
        self.assertEqual(result["groups"]["reference_validation_product"]["filtered"], 47)
        self.assertFalse(result["native_authority"])
        self.assertEqual(result["acceptance_delta"], 0)

    def test_10_missing_target_or_partial_group_never_passes(self):
        for output in ("", group(["core::one"]), "running 1 tests\ntest core::one ... ok\n"):
            with self.assertRaises(ValueError):
                m.validate_stdout(output, self.spec())

    def test_11_missing_extra_foreign_duplicate_and_substring_results_rejected(self):
        for names in (["stored::a"], ["stored::a", "foreign"], ["stored::a", "stored::a"], ["stored::a", "stored::b_extra"]):
            with self.assertRaises(ValueError):
                m.validate_stdout(group(names) + group(["api_one"]) + group(["core::one"]), self.spec())

    def test_12_duplicate_complete_target_and_nested_headers_rejected(self):
        output = group(["core::one"]) + group(["api_one"]) + group(["stored::a", "stored::b"])
        with self.assertRaises(ValueError):
            m.validate_stdout(output + group(["core::one"]), self.spec())
        with self.assertRaises(ValueError):
            m.validate_stdout("running 1 tests\nrunning 1 tests\n", self.spec())

    def test_13_failed_ignored_measured_or_invented_summary_rejected(self):
        output = group(["core::one"]) + group(["api_one"]) + group(["stored::a", "stored::b"])
        changes = [("core::one ... ok", "core::one ... ignored"), ("core::one ... ok", "core::one ... FAILED"),
                   ("1 passed", "2 passed"), ("0 ignored", "1 ignored"), ("0 measured", "1 measured"),
                   ("0 failed", "1 failed"), ("test result: ok", "test result: FAILED")]
        for old, new in changes:
            with self.assertRaises(ValueError):
                m.validate_stdout(output.replace(old, new, 1), self.spec())

    def test_14_original_complete_capture_budget_and_unexpected_output_retained(self):
        with self.assertRaises(ValueError):
            m.validate_stdout("x" * (m.MAX_OUTPUT_BYTES + 1), self.spec())
        output = group(["core::one"]) + group(["api_one"]) + group(["stored::a", "stored::b"])
        with self.assertRaises(ValueError):
            m.validate_stdout(output + "unexpected\n", self.spec())

    def test_15_cargo_path_and_boolean_mode_are_not_shell_or_authorization_flags(self):
        for cargo in ("cargo.exe", r"D:\cmd.exe", r"D:\cargo.exe" + "\0"):
            with self.assertRaises(ValueError):
                m.command(cargo, self.spec())
        with self.assertRaises(ValueError):
            m.command(CARGO, self.spec(), no_run=1)


if __name__ == "__main__":
    unittest.main()
