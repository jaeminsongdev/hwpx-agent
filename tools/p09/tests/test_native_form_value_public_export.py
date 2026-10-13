from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from tools.p09 import qualify_native_form_value_public_export as q
from tools.p09.tests import test_native_form_value_output as previous


class NativeFormValuePublicExportTests(previous.NativeFormValueOutputTests):
    """Inherited whole-output forgery cases now consume actual public-library outputs."""
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="p09-40-component-", dir=q.ROOT/"fixtures/target-build")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory = Path(cls.temporary.name)
        cls.actual = q.generate(cls.directory)
        cls.original = {p.name:p.read_bytes() for p in cls.directory.iterdir()}

    def test_five_actual_compiled_outputs_independently_verify_full_parts_gaps_values_and_fingerprints(self):
        self.assertEqual(self.actual["compiled_tests"]["passed"],22)
        self.assertEqual(set(self.actual["compiled_tests"]["names"]),q.old.INTEGRATION_TESTS)
        frozen=q.q.shared.lifecycle.checked_json(q.ROOT/q.history.CAPSULE,q.history.CAPSULE_SHA)
        self.assertEqual(self.actual["independent_oracle"],frozen["independent_oracle"])
        self.assertEqual(self.actual["fixture_manifest"],frozen["fixture_manifest"])
        self.assertEqual(q.oracle.inspect_bundle(self.directory),self.actual["independent_oracle"])
        self.assertFalse(self.actual["independent_oracle"]["native_execution_qualified"])

    def test_artifact_directory_and_nonempty_generation_boundaries_reject(self):
        with self.assertRaises(ValueError): q.oracle.directory_guard(Path("relative"))
        with self.assertRaises(ValueError): q.oracle.directory_guard(self.directory.parent)
        with self.assertRaisesRegex(ValueError,"value_public_generation_nonempty"): q.generate(self.directory)

    def test_compiled_protocol_requires_all_exact_cases_without_skip_filter_duplicates(self):
        names=q.old.INTEGRATION_TESTS
        good="\n".join(f"test {name} ... ok" for name in sorted(names))+"\ntest result: ok. 22 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1s\n"
        self.assertEqual(q.protocol(good,names,22)["passed"],22)
        first,second=sorted(names)[:2]
        for bad in (good.replace(first,second),good.replace("... ok","... ignored",1),good.replace("0 filtered out","1 filtered out"),good+f"test {first} ... ok\n"):
            with self.assertRaises(ValueError): q.protocol(bad,names,22)

    def test_export_inverse_requires_entire_authentic_original_bytes(self):
        actual=q.public.bounded_bytes(q.ROOT/q.LIB,2*1024*1024)
        archive=q.public.checked(q.ROOT/q.ARCHIVE,q.history.OLD_LIB)
        q.project(actual,archive)
        for changed in (actual+b"\n",actual.replace(q.DELTA,b"",1),actual+q.DELTA):
            with self.assertRaises(ValueError): q.project(changed,archive)
        with self.assertRaises(ValueError): q.project(actual,archive+b"\n")

    def test_complete_public_case_body_cannot_be_changed_or_source_included(self):
        actual=q.public.bounded_bytes(q.ROOT/q.TEST,2*1024*1024)
        pending=q.public.bounded_bytes(q.ROOT/q.old.RUST_TEST,2*1024*1024)
        self.assertTrue(q.lineage(actual,pending)["public_library_only_no_source_inclusion"])
        for changed in (actual+b"\n",b'#[path="../src/native_form_value_output.rs"]\n'+actual,b"mod hwpx_package {}\n"+actual,actual.replace(b"use hwpx_package::native_form_value_output::*;",b"use native_value::*;")):
            with self.assertRaises(ValueError): q.lineage(changed,pending)

    def test_actual_old_current_authority_failure_is_preserved_not_promoted(self):
        with self.assertRaisesRegex(ValueError,"public_export_source_identity_changed"): q.old.authority()

    def test_original_view_selection_is_bounded_and_does_not_copy_build_or_git(self):
        values=q.history.select()
        self.assertLessEqual(len(values),q.history.LIMIT_FILES)
        self.assertLessEqual(sum(map(len,values.values())),q.history.LIMIT_BYTES)
        self.assertEqual(q.q.sha(values[q.LIB]),q.history.OLD_LIB)
        for name in values:
            q.history.relative(name)
            self.assertNotIn("p09-41-",name.lower())
            self.assertNotIn(name,q.history.EXCLUDED)
        for name in ("../outside","/absolute","target/file","node_modules/file",".git/config"):
            with self.assertRaises(ValueError): q.history.relative(name)


if __name__=="__main__": unittest.main()
