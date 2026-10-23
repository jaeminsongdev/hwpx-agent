import ast
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import unittest
import native011_metadata_tail_connection as m
import native011_metadata_tail_candidate as candidate
import native011_exact_read_budget as exact
import native011_chunk_join_connection as codes
import audit_evidence_io as audit
import owned_source_read_pressure as pressure
import owned_input_read_pressure as query
import reusable_audit_chunk_v1 as chunk
import runtime_envelope_namespace_bundle_v1 as loader
import fresh_lossless_metadata_reader_v1 as fresh
import runtime_envelope_physical_io_v1 as physical
import shared_metadata_frame_decoder_budget_v1 as shared


class Tests(unittest.TestCase):
    def raw(self,pin):return (Path(__file__).resolve().parents[3]/pin['path']).read_bytes()
    def fixture(self):
        root=Path(__file__).resolve().parents[3]
        namespace,_=loader.load(root,[m.METADATA],{})
        tree=ast.parse(self.raw(m.BUILD));node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='BuildReader')
        env=dict(__name__='p09_exact_fixture_build',base=NS(weighted=pressure.prior),QueryPacer=query.QueryPacer)
        exec(compile(ast.Module(body=[node],type_ignores=[]),m.BUILD['path'],'exec'),env)
        Base=chunk.reader_type(env['BuildReader'],self.raw(exact.ORIGINAL))[0]
        old=dict(path='semantic.json',bytes=1,sha256='a'*64);pin=dict(path='physical.json',bytes=1,sha256='b'*64)
        descriptor=dict(schema_version='fixture',semantic_original_pin=old,physical_envelope_pin=pin,next_case=165)
        projection=NS(semantic_pins={old['path']:old},physical_pins={pin['path']:pin},next_case=165)
        binding=NS(descriptors=lambda:[descriptor],manifest_pin=dict(path='manifest.json',bytes=1,sha256='c'*64),
            project=lambda *args:(projection,{}))
        def run(*args):pass
        engine=NS(run_owned=FunctionType(run.__code__,dict(__name__='p09_exact_fixture_engine',
            build=NS(BuildReader=Base,pressure_summary=lambda *args:{}))))
        budget=shared.SharedBudget()
        connection=namespace.lossless_metadata_connection_v1.connect_engine(engine,binding,fresh,
            physical.DecoderBudget,lambda:None,budget)
        owner=NS(phase='NEW',shared=budget,metadata_connection=connection,whole={pin['path']:pin})
        linked=NS(engine=engine,state=NS(attempts=0,calls=0))
        return linked,owner,dict(owner.whole)
    def connect(self,fixture,**raws):
        return m.connect(*fixture,candidate,exact,pressure,chunk,self.raw(exact.ORIGINAL),
            raws.get('metadata',self.raw(m.METADATA)),raws.get('build',self.raw(m.BUILD)),codes)

    def test_only_private_factory_dependency_changes_no_reader_budget_or_default_mutation(self):
        fixture=self.fixture();linked,owner,pins=fixture;old=linked.engine.run_owned.__globals__['build']
        original=old.BuildReader;constructor=owner.metadata_connection.original_reader.__init__
        link,proof=self.connect(fixture)
        self.assertIs(old.BuildReader,original);self.assertIs(link.previous,original)
        self.assertIs(owner.metadata_connection.original_reader.__init__,constructor)
        self.assertEqual(owner.metadata_connection.readers,[]);self.assertIsNone(owner.shared.metadata)
        self.assertTrue(proof['original_metadata_two_point_five_four_MiB_rates_retained'])
        self.assertFalse(proof['default_modules_classes_or_ctors_changed'])
        self.assertEqual(proof['metadata_reader_allocations_during_connection'],0)

    def test_original_factory_creates_one_tracked_fresh_routed_metadata_reader(self):
        import time
        fixture=self.fixture();linked,owner,pins=fixture;link,proof=self.connect(fixture)
        reader=linked.engine.run_owned.__globals__['build'].BuildReader('.',lambda:None)
        self.assertIsInstance(reader,link.selected_reader);self.assertIsInstance(reader,link.original_reader)
        self.assertEqual(owner.metadata_connection.readers,[reader]);self.assertEqual(len(owner.metadata_connection.budgets),1)
        self.assertIsNotNone(owner.shared.metadata);self.assertIsNone(owner.shared.frame)
        self.assertEqual(reader.read_passes,0);self.assertEqual(reader.open_pacer.requests,0)
        self.assertIs(reader.pacer.clock,time.perf_counter);self.assertIs(reader.open_pacer.clock,time.perf_counter)
        reader.pacer.select('a.exe');self.assertEqual(reader.pacer.rate,2621440)
        reader.pacer.select('a.json');self.assertEqual(reader.pacer.rate,4194304)
        self.assertEqual(owner.shared.metadata.completed,0)

    def test_full_source_drift_is_refused_without_factory_replacement(self):
        for kind in ('metadata','build'):
            fixture=self.fixture();linked,owner,pins=fixture;before=linked.engine.run_owned.__globals__['build']
            with self.assertRaises(ValueError):self.connect(fixture,**{kind:self.raw(m.METADATA if kind=='metadata' else m.BUILD)+b'\n'})
            self.assertIs(linked.engine.run_owned.__globals__['build'],before)

    def test_active_owner_worker_or_shared_decoder_refused(self):
        for kind in ('owner','worker','decoder'):
            fixture=self.fixture();linked,owner,pins=fixture
            if kind=='owner':owner.phase='READY'
            if kind=='worker':linked.state.calls=1
            if kind=='decoder':owner.shared.metadata=object()
            with self.assertRaisesRegex(ValueError,'UNUSED_PARENT'):self.connect(fixture)

    def test_omitted_physical_inputs_cannot_silently_be_added_from_observed_modules(self):
        fixture=self.fixture();linked,owner,pins=fixture
        with self.assertRaisesRegex(ValueError,'COMPLETE_DECLARED_PHYSICAL'):
            self.connect((linked,owner,{}))

    def test_changed_factory_code_or_old_reader_reference_rejected(self):
        fixture=self.fixture();linked,owner,pins=fixture;factory=linked.engine.run_owned.__globals__['build'].BuildReader
        factory.__new__=staticmethod(lambda *args:None)
        with self.assertRaisesRegex(ValueError,'ENTIRE_ORIGINAL_METADATA_FACTORY'):self.connect(fixture)
        fixture=self.fixture();fixture[1].metadata_connection.original_reader=object
        with self.assertRaisesRegex(ValueError,'ORIGINAL_ALLOCATOR_ROUTER'):self.connect(fixture)
