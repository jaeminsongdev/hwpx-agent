"""Connection contracts; real full preflight remains required."""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import unittest
import preparation_rust_inventory_snapshot_v1 as m


class Tests(unittest.TestCase):
    def setUp(self):
        def run(value=1):return build.base.inputs.rust_inputs(value),build.marker
        def inventory(value):return value+1
        self.build=NS(base=NS(inputs=NS(rust_inputs=inventory,retained=object()),same=object()),marker=object())
        self.fn=FunctionType(run.__code__,dict(run.__globals__,build=self.build),argdefs=run.__defaults__)
        self.original=NS(run_owned=self.fn,worker=object(),retained=object());self.calls=[]
        self.counter=NS(summary=lambda:dict(requests=1))
        self.snapshot=NS(projection=lambda fn,raw:(lambda value:fn(value)*2,self.counter))
    def test_private_dependency_only_and_all_other_engine_objects_retained(self):
        new,c=m.engine(self.original,self.snapshot,b"raw")
        self.assertEqual(new.run_owned()[0],4);self.assertEqual(self.original.run_owned()[0],2)
        self.assertIs(new.worker,self.original.worker);self.assertIs(new.retained,self.original.retained)
        self.assertIs(self.build.base.inputs.retained,new.run_owned.__globals__["build"].base.inputs.retained)
        self.assertIs(c,self.counter)
    def test_full_original_function_code_defaults_closure_unchanged(self):
        new,c=m.engine(self.original,self.snapshot,b"raw")
        self.assertIs(new.run_owned.__code__,self.fn.__code__)
        self.assertIs(new.run_owned.__defaults__,self.fn.__defaults__)
        self.assertIs(new.run_owned.__closure__,self.fn.__closure__)
        self.assertIs(self.original.run_owned,self.fn)
    def test_exact_projection_error_not_swallowed_or_retried(self):
        def fail(*args):self.calls.append(1);raise ValueError("EXACT_SOURCE_OR_ORIGINAL_STOP")
        with self.assertRaisesRegex(ValueError,"EXACT_SOURCE_OR_ORIGINAL_STOP"):
            m.engine(self.original,NS(projection=fail),b"bad")
        self.assertEqual(self.calls,[1]);self.assertIs(self.original.run_owned,self.fn)
    def test_default_runtime_rejected_before_global_rebinding(self):
        def factory():return None
        runtime=NS(connect_factory=factory)
        with self.assertRaises(ValueError):m.connect(runtime,self.snapshot,b"raw")
        self.assertIs(runtime.connect_factory,factory)
    def test_missing_qualification_fails_after_source_witnesses(self):
        calls=[]
        class Reader:
            def __init__(self,*args):pass
            def pin(self,name):calls.append(name)
            def json(self,name):raise ValueError("MISSING_CODE15")
        api,readers=m.reader_api(NS(AcceptanceReader=Reader),NS(SELF="leaf",TEST="test"),"missing")
        with self.assertRaisesRegex(ValueError,"MISSING_CODE15"):api.AcceptanceReader(None,None)
        self.assertEqual(calls,[m.SELF,m.TEST,"leaf","test"]);self.assertEqual(readers,[])
    def test_full_module_context_proven_then_existing_exact_projection_used(self):
        import current_issuer_build_inputs as actual
        import rust_inventory_single_snapshot_v1 as leaf
        raw=(Path(__file__).resolve().parents[3]/leaf.ORIGINAL_PIN["path"]).read_bytes()
        original=actual.rust_inputs
        canonical=m.canonical_inventory(original,raw,leaf.ORIGINAL_PIN)
        projected,counters=leaf.projection(canonical,raw)
        self.assertIs(canonical.__globals__["os"],original.__globals__["os"])
        self.assertIs(canonical.__globals__["require"],original.__globals__["require"])
        self.assertEqual(counters.requests,0);self.assertIs(actual.rust_inputs,original)
    def test_changed_code_or_source_never_normalized_as_compiler_context(self):
        import current_issuer_build_inputs as actual
        import rust_inventory_single_snapshot_v1 as leaf
        raw=(Path(__file__).resolve().parents[3]/leaf.ORIGINAL_PIN["path"]).read_bytes()
        original=actual.rust_inputs;changed=FunctionType(original.__code__.replace(co_name="changed"),original.__globals__)
        with self.assertRaises(ValueError):m.canonical_inventory(changed,raw,leaf.ORIGINAL_PIN)
        with self.assertRaises(ValueError):m.canonical_inventory(original,raw+b"\n",leaf.ORIGINAL_PIN)


class CompactReportTests(unittest.TestCase):
    def fixture(self):
        def run_preflight(row,**options):
            import json
            return json.dumps(row,**options)
        return FunctionType(run_preflight.__code__,dict(run_preflight.__globals__,__name__="p09_exact_fixture"))
    def test_all_nested_values_types_order_whitespace_inside_strings_preserved(self):
        import json
        original=self.fixture();connected,counters=m.compact_report(original)
        row=dict(state="FAILED",source_pins=[dict(path="한글",bytes=13)],samples=[.1,True,None],text=" a \n b ")
        pretty=original(row,ensure_ascii=True,allow_nan=False,indent=2)
        compact=connected(row,ensure_ascii=True,allow_nan=False,indent=2)
        self.assertEqual(json.loads(compact),row);self.assertEqual(list(json.loads(compact)),list(row))
        self.assertLess(len(compact),len(pretty));self.assertEqual(counters.final_report_calls,1)
        self.assertIs(connected.__code__,original.__code__)
    def test_nonfinite_error_propagates_without_substitution(self):
        connected,counters=m.compact_report(self.fixture())
        with self.assertRaises(ValueError):connected(dict(x=float("nan")),ensure_ascii=True,allow_nan=False,indent=2)
    def test_summary_or_other_json_profile_not_changed(self):
        original=self.fixture();connected,counters=m.compact_report(original)
        self.assertEqual(connected(dict(x=1)),original(dict(x=1)))
        self.assertEqual(connected(dict(x=1),indent=4),original(dict(x=1),indent=4))
        self.assertEqual((counters.final_report_calls,counters.other_calls),(0,2))
    def test_default_json_and_original_function_not_mutated(self):
        import json
        dump=json.dumps;original=self.fixture();before=original(dict(x=1),indent=2)
        connected,counters=m.compact_report(original)
        connected(dict(x=1),ensure_ascii=True,allow_nan=False,indent=2)
        self.assertIs(json.dumps,dump);self.assertEqual(original(dict(x=1),indent=2),before)
    def test_default_or_other_function_rejected(self):
        def other():pass
        with self.assertRaises(ValueError):m.compact_report(other)


class PreparationLosslessTests(unittest.TestCase):
    def setUp(self):
        import fresh_lossless_metadata_reader_v1 as fresh
        import runtime_envelope_physical_io_v1 as physical
        from tests import test_fresh_lossless_metadata_reader_v1 as fixtures
        fixture=fixtures.Tests();fixture.setUp();self.fixture=fixture
        class Base(fixtures.Base):
            def __init__(self,root,checkpoint):super().__init__();self.checkpoint=checkpoint
        self.api,self.summary=m.lossless_api(NS(AcceptanceReader=Base),fresh,fixture.projection,fixture.rows,physical.DecoderBudget)
        self.reader=self.api.AcceptanceReader(None,lambda:None)
    def test_fresh_physical_decode_and_separate_semantic_accounting(self):
        self.reader._read("semantic",True);self.reader._read("semantic",True)
        row=self.summary();self.assertEqual(self.reader.bytes_read,16)
        self.assertEqual((row["mapped_physical_bytes_read"],row["mapped_semantic_bytes_restored"]),(16,14))
        self.assertEqual(row["decoder"]["completed_decodes"],2)
    def test_budget_error_propagates_and_checkpoint_restored(self):
        self.reader.checkpoint=lambda:None
        self.reader._read("semantic")
        def fail(*args):raise ValueError("ORIGINAL_DECODER_OR_RESOURCE_STOP")
        self.fixture.projection.decode_fresh=fail
        with self.assertRaisesRegex(ValueError,"ORIGINAL_DECODER_OR_RESOURCE_STOP"):self.reader._read("semantic")
        self.assertTrue(self.summary()["decoder"]["terminal_error_seen"])
    def test_second_reader_not_allowed_to_share_owner_budget(self):
        with self.assertRaises(ValueError):self.api.AcceptanceReader(None,lambda:None)
    def test_unmapped_calls_original_reader_without_decoder(self):
        self.reader._read("unmapped")
        self.assertEqual(self.reader.calls,[("unmapped",False)])
        self.assertEqual(self.summary()["decoder"]["attempted_decodes"],0)
    def test_tampered_physical_bytes_never_count_as_success(self):
        self.reader.contents=b"tampered"
        with self.assertRaises(ValueError):self.reader._read("semantic")
        self.assertEqual(self.summary()["mapped_read_completed"],0)


if __name__=="__main__":unittest.main()
