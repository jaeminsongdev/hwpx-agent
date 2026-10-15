"""Private connection contracts without product/Frame execution."""
import unittest
from types import FunctionType,SimpleNamespace as NS
import lossless_metadata_connection_v1 as m

CHECKPOINT=lambda:None


class Tests(unittest.TestCase):
    def setUp(self):CHECKPOINT()
    def tearDown(self):CHECKPOINT()
    def fixture(self,fail=False):
        class Reader:
            def __init__(self,*args):pass
        class Budget:
            def __init__(self,checkpoint):self.checkpoint=checkpoint
            def run(self,fn):return fn(self.checkpoint)
            def evidence(self):return dict(aggregate_limit_seconds=5,elapsed_decoder_work_seconds=0.1,
                attempted_decodes=1,completed_decodes=1,active_decode=False,terminal_error_seen=False)
        def decode(*args):
            if fail:raise ValueError("fixture_decode_error")
            return b"fresh"
        projection=NS(semantic_pins={},physical_pins={},next_case=164,decode_fresh=decode)
        binding=NS(descriptors=lambda:[{}],manifest_pin=dict(path="manifest"),project=lambda *args:(projection,{}))
        # The actual fixture descriptor is needed by the connector before routing.
        binding.descriptors=lambda:[dict(semantic_original_pin=dict(path="semantic"))]
        build=NS(BuildReader=Reader,pressure_summary=lambda guard:dict(original=True))
        def run():return "original"
        env=dict(run.__globals__,build=build);original=FunctionType(run.__code__,env)
        fresh=NS(reader_type=lambda base,router,rows:base,summary=lambda reader:dict(fresh=True))
        engine=NS(run_owned=original,worker=object())
        state=m.connect_engine(engine,binding,fresh,Budget,CHECKPOINT)
        reader=original.__globals__["build"].BuildReader("root",CHECKPOINT)
        return engine,state,reader,build
    def test_original_engine_worker_and_default_build_retained(self):
        engine,state,reader,build=self.fixture()
        self.assertIs(engine.run_owned,state.original_run)
        self.assertEqual(engine.run_owned(),"original")
        self.assertIs(build.BuildReader,state.original_reader)
    def test_successful_decode_restores_same_budget_checkpoint(self):
        engine,state,reader,build=self.fixture();router=reader._lossless_metadata_router;old=router.budget.checkpoint
        self.assertEqual(router.decode_fresh("semantic",{},b"raw",CHECKPOINT),b"fresh")
        self.assertIs(router.budget.checkpoint,old);self.assertEqual(router.counts,{"semantic":1})
    def test_failed_decode_restores_same_budget_checkpoint(self):
        engine,state,reader,build=self.fixture(True);router=reader._lossless_metadata_router;old=router.budget.checkpoint
        with self.assertRaises(ValueError):router.decode_fresh("semantic",{},b"raw",CHECKPOINT)
        self.assertIs(router.budget.checkpoint,old);self.assertEqual(router.counts,{})
    def test_metadata_summary_preserves_original_and_does_not_claim_frame_budget(self):
        engine,state,reader,build=self.fixture()
        row=engine.run_owned.__globals__["build"].pressure_summary(NS(reader=reader))
        self.assertTrue(row["original"])
        self.assertEqual(row["explicit_fresh_lossless_metadata"]["decoder"]["scope"],"metadata_reader_only_not_Native_shared_budget")


if __name__=="__main__":unittest.main()
