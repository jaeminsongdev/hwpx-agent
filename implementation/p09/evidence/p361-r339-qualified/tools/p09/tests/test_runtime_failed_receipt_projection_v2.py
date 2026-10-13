from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_failed_receipt_projection_v2 as m
import runtime_envelope_namespace_bundle_v1 as bundle
import current_stored_runtime_scope as scope

PINS=[dict(path="tools/p09/runtime_record_envelope_v1.py",bytes=3596,sha256="59f4a0bc32f7c03dd1651b5e31f45ad7311fb4b8a36d6490b9b39242895337e5"),
    dict(path="tools/p09/runtime_record_envelope_v2.py",bytes=2891,sha256="9a97c8c9c9a6281992430bfc224bbfea036da6d780389ac2777fbb403d62960f"),
    dict(path="tools/p09/runtime_envelope_source_projection_v1.py",bytes=6401,sha256="728ffdbac1a4b0edb44a8f34f26f912ac79d9c3bad0b5eb26c19b5102f788d5b"),
    dict(path="tools/p09/runtime_envelope_scope_binding_v1.py",bytes=10750,sha256="0105881d365213e70bd047b5c7fa8de6fda842f3103b71870c8f2224b3e4db3b")]

def context():
    return dict(schema_version=m.ADMISSION_SCHEMA,source_role=m.ROLE,failed_runtime_pin=m.ROOT,
        independent_review_pin=m.REVIEW,current_case=158,original_failure_promoted=False,current_product_or_GO_qualified=False)
def graph():
    root=Path(__file__).resolve().parents[3]
    ns,_=bundle.load(root,PINS,{"current_stored_runtime_scope":scope})
    return ns.runtime_envelope_source_projection_v1,ns.runtime_envelope_scope_binding_v1
def physical():return dict(path=m.PHYSICAL,bytes=1,sha256="0"*64)


class Tests(unittest.TestCase):
    def test_exact_failure_alias_allowed_only_after_explicit_extension(self):
        source,binding=graph()
        with self.assertRaises(ValueError):source.descriptor(m.ROOT,physical(),next_case=158)
        proof=m.connect(source,binding,context())
        self.assertEqual(source.descriptor(m.ROOT,physical(),next_case=158)["semantic_original_pin"],m.ROOT)
        self.assertFalse(proof["GO_authorized"])
    def test_other_cases_boolean_or_wrong_failed_pin_rejected(self):
        source,binding=graph();m.connect(source,binding,context())
        for case in (True,157,159):
            with self.assertRaises(ValueError):source.descriptor(m.ROOT,physical(),next_case=case)
        with self.assertRaises(ValueError):source.descriptor(dict(m.ROOT,sha256="0"*64),physical(),next_case=158)
    def test_wrong_physical_name_is_not_a_prior_success_alias(self):
        source,binding=graph();m.connect(source,binding,context())
        with self.assertRaises(ValueError):source.descriptor(m.ROOT,dict(physical(),path=m.PHYSICAL.replace("failed.","")),next_case=158)
    def test_regular_source_executable_or_fixture_not_transformable(self):
        source,binding=graph();m.connect(source,binding,context())
        for name in ("crates/secret.rs","target/run.exe","fixtures/source.hwpx"):
            with self.assertRaises(ValueError):source.descriptor(dict(m.ROOT,path=name),physical(),next_case=158)
    def test_original_projection_and_binding_constructor_codes_retained(self):
        source,binding=graph();project=source.Projection.__init__.__code__;bind=binding.Binding.__init__.__code__
        m.connect(source,binding,context())
        self.assertIs(source.Projection.__init__.__code__,project)
        self.assertIs(binding.Binding.__init__.__code__,bind)
    def test_separate_original_graph_keeps_prior_only_rejection(self):
        source,binding=graph();other,_=graph();m.connect(source,binding,context())
        with self.assertRaises(ValueError):other.descriptor(m.ROOT,physical(),next_case=158)
    def test_representation_exposes_failure_role_and_does_not_promote(self):
        source,binding=graph();m.connect(source,binding,context())
        desc=source.descriptor(m.ROOT,physical(),next_case=158)
        manifest=dict(path="implementation/p09/evidence/future-failure-manifest.json",bytes=1,sha256="1"*64)
        obj=binding.Binding([desc],manifest,next_case=158)
        rows={m.ROOT["path"]:m.ROOT,manifest["path"]:manifest}
        projection,_=obj.project(rows,lambda:None)
        row=obj.representation(projection)
        self.assertEqual(row["same_case_failed004_receipt_provenance"]["source_role"],m.ROLE)
        self.assertFalse(row["same_case_failed004_receipt_provenance"]["original_failure_promoted"])
        self.assertEqual(row["physical_source_freeze"][1 if row["physical_source_freeze"][0]["path"]==manifest["path"] else 0]["path"],m.PHYSICAL)
    def test_wrong_or_promoted_admission_and_double_install_rejected(self):
        source,binding=graph()
        with self.assertRaises(ValueError):m.connect(source,binding,dict(context(),original_failure_promoted=True))
        m.connect(source,binding,context())
        with self.assertRaises(ValueError):m.connect(source,binding,context())
    def test_boolean_coercion_and_mutation_of_returned_provenance_rejected(self):
        source,binding=graph()
        with self.assertRaises(ValueError):m.connect(source,binding,dict(context(),original_failure_promoted=0))
        m.connect(source,binding,context())
        with self.assertRaises(TypeError):source.failed004_receipt_extension["failed_runtime_pin"]["sha256"]="0"*64


if __name__=="__main__":unittest.main()
