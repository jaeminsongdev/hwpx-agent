from __future__ import annotations
import copy
import io
from pathlib import Path
import tempfile
import unittest
import zipfile
from tools.p09 import qualify_native_form_package_output as q
from tools.p09 import verify_p08_additive_export_source_bridge_v4 as current


def archive(parts, order=None, compression=None):
    order = list(parts) if order is None else order
    compression = [zipfile.ZIP_STORED]*len(order) if compression is None else compression
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as writer:
        for name, method in zip(order, compression):
            writer.writestr(name, parts[name], compress_type=method)
    return buffer.getvalue()


class NativeFormPackageOutputTests(unittest.TestCase):
    def test_real_compiled_outputs_predecessor_and_complete_independent_comparison(self):
        with self.assertRaisesRegex(ValueError,"public_export_source_identity_changed"):
            q.qualify()
        value = current.record("P09-30")
        current.historical_sources("P09-30")
        public_result = current.public_output()
        self.assertEqual(public_result["passed"],19)
        self.assertEqual(public_result["actual_library_unit_tests"]["passed"],2)
        self.assertEqual(value["actual_rust_tests"]["passed"],21)
        self.assertEqual(set(value["independent_generated_package_checks"]),set(q.CASES))
        self.assertTrue(value["claims"]["actual_package_output_lowering_implemented"])
        self.assertTrue(value["claims"]["independent_all_expanded_part_output_comparison"])
        for key in ("public_package_exports_connected","complete_native_target_cases_prepared","new_native_target_execution",
                    "general_document_protection_qualified","nonzero_form_border_type_qualified","production_routing_qualified",
                    "zip_headers_raw_byte_exact","p09_complete","product_complete"):
            self.assertFalse(value["claims"][key])
        public = q.SHARED.lifecycle.canonical_bytes(value).decode()
        for private in ("P08FORMINSERT",str(q.ROOT),q.prior.prior.CAPTURE): self.assertNotIn(private,public)

    def test_failed_ignored_missing_extra_or_coerced_named_tests_rejected(self):
        original = "\n".join("test "+name+" ... ok" for name in sorted(q.EXPECTED_TESTS))+"\ntest result: ok. 21 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1s\n"
        q.test_output(original)
        for changed in (original.replace("21 passed","20 passed"),original.replace(" ... ok"," ... FAILED",1),
                        original.replace(" ... ok"," ... ignored",1),original+"test extra ... ok\n"):
            with self.subTest(length=len(changed)), self.assertRaisesRegex(ValueError,"native_form_output_test_inventory_invalid"):
                q.test_output(changed)

    def test_forged_changed_target_nonsection_and_unchanged_output_rejected(self):
        raw, baseline = q.original()
        expected = dict(baseline["parts"])
        expected["Contents/section0.xml"] = expected["Contents/section0.xml"].replace(b'enabled="1"',b'enabled="0"')
        correct = archive(expected,baseline["order"],baseline["compression"])
        proof = q.verify_case("actual-property",raw,correct,raw,baseline)
        self.assertEqual(proof["changed_attributes"],1)
        for part in expected:
            mutated = dict(expected); mutated[part] += b" "
            with self.subTest(part=part), self.assertRaises(ValueError):
                q.verify_case("actual-property",raw,archive(mutated,baseline["order"],baseline["compression"]),raw,baseline)
        with self.assertRaises(ValueError): q.verify_case("actual-property",raw,raw,raw,baseline)
        with self.assertRaises(ValueError): q.verify_case("actual-property",correct,correct,raw,baseline)

    def test_multisection_source_derivation_and_full_tab_edits_are_independent(self):
        raw, baseline = q.original()
        for case in q.CASES[1:]:
            source = q.derived_parts(case,baseline["parts"])
            expected = dict(source)
            for part,replacements in q.expected_edits(case).items():
                for old,new in replacements: expected[part] = expected[part].replace(old,new)
            order = ["mimetype",*sorted(p for p in source if p != "mimetype")]
            methods = [zipfile.ZIP_STORED,*([zipfile.ZIP_DEFLATED]*(len(order)-1))]
            source_raw, output = archive(source,order,methods),archive(expected,order,methods)
            proof = q.verify_case(case,source_raw,output,raw,baseline)
            self.assertTrue(proof["derived_fixture_not_native_save_evidence"])
            wrong = dict(source); wrong["Contents/header.xml"] += b" "
            with self.subTest(case=case), self.assertRaisesRegex(ValueError,"native_form_output_complete_source_derivation_mismatch"):
                q.verify_case(case,archive(wrong,order,methods),output,raw,baseline)
            with self.assertRaises(ValueError): q.verify_case(case,source_raw,source_raw,raw,baseline)

    def test_extra_omitted_order_compression_and_archive_limits_fail(self):
        raw,baseline = q.original(); expected = dict(baseline["parts"])
        expected["Contents/section0.xml"] = expected["Contents/section0.xml"].replace(b'enabled="1"',b'enabled="0"')
        mutations = [archive({**expected,"extra.bin":b"extra"}),archive({p:v for p,v in expected.items() if p != "Preview/PrvImage.png"}),
                     archive(expected,list(reversed(baseline["order"])),list(reversed(baseline["compression"]))),
                     archive(expected,baseline["order"],[zipfile.ZIP_STORED]*len(expected))]
        for output in mutations:
            with self.assertRaises(ValueError): q.verify_case("actual-property",raw,output,raw,baseline)
        for bad in (b"",b"x"*(32*1024*1024+1),"not bytes"):
            with self.assertRaises(ValueError): q.read_package(bad)
        with self.assertRaises(ValueError): q.read_package(archive({"oversized.bin":b"x"*(2*1024*1024+1)}))
        with self.assertRaises(ValueError): q.read_package(archive({"../escape":b"x"}))

    def test_missing_original_authority_and_oracle_files_are_not_synthetic_or_skip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises((OSError,ValueError)): q.original(root)
            with self.assertRaises((OSError,ValueError)): q.sources(root)
            with self.assertRaises((OSError,ValueError)): q.artifacts(root)

    def test_probe_values_types_false_raw_zip_and_legacy_pass_are_rejected(self):
        raw,baseline = q.original(); expected = dict(baseline["parts"])
        expected["Contents/section0.xml"] = expected["Contents/section0.xml"].replace(b'enabled="1"',b'enabled="0"')
        proof = q.verify_case("actual-property",raw,archive(expected,baseline["order"],baseline["compression"]),raw,baseline)
        independent = q.prior.independent_actual()
        value = {"profile":q.PROFILE,"source_package_sha256":proof["source_package_sha256"],"output_package_sha256":proof["output_package_sha256"],
                 "document_flow_sha256":independent["document_flow_sha256"],"changed_sections":1,"changed_attributes":1,
                 "non_section_parts_expanded_byte_exact":True,"outside_declared_edits_byte_exact":True,"entry_order_and_compression_preserved":True,
                 "zip_header_policy":"rewritten_not_byte_exact","legacy_reference_state":"id_index_validation_failed",
                 "verified_native_reference_overlay_issues":2,"output_section_sha256":proof["output_section_sha256"]}
        q.verify_probe(value,proof,independent)
        for key,changed in (("changed_attributes",True),("verified_native_reference_overlay_issues",0),("legacy_reference_state","pass"),
                            ("zip_header_policy","raw_byte_exact"),("output_package_sha256","0"*64),("unknown",False)):
            mutated = copy.deepcopy(value); mutated[key] = changed
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,"native_form_output_independent_probe_mismatch"):
                q.verify_probe(mutated,proof,independent)


if __name__ == "__main__": unittest.main()
