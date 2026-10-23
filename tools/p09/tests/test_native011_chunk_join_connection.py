import unittest
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import hashlib
import native011_chunk_join_connection as m
import native011_decoder_chunk_join as candidate
import current_stored_runtime_scope as scope
import runtime_record_envelope_v2 as codec
import runtime_envelope_namespace_bundle_v1 as loader
import runtime_envelope_source_projection_v1 as default_source
import fresh_lossless_metadata_reader_v1 as fresh
import runtime_envelope_physical_io_v1 as physical
import shared_metadata_frame_decoder_budget_v1 as shared


class Tests(unittest.TestCase):
    def raw(self,pin):return (Path(__file__).resolve().parents[3]/pin['path']).read_bytes()
    def fixture(self,*,default=False):
        root=Path(__file__).resolve().parents[3]
        libs,_=loader.load(root,[m.SOURCE,m.METADATA],dict(current_stored_runtime_scope=scope,runtime_record_envelope_v2=codec))
        source=default_source if default else libs.runtime_envelope_source_projection_v1
        metadata=libs.lossless_metadata_connection_v1
        original=b'{"profile":"fixture"}';encoded=codec.encode(original,lambda:None)
        rows=[];semantic={}
        for index in range(1,163):
            old=dict(path=f'implementation/p09/evidence/p09-361-case112-current-runtime-run{index:03}.v1.json',
                bytes=len(original),sha256=hashlib.sha256(original).hexdigest())
            new=dict(path=source.PREFIX+f'case112-runtime-run{index:03}.envelope.v1.json',
                bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            rows.append(source.descriptor(old,new,next_case=165));semantic[old['path']]=old
        manifest=dict(path='implementation/p09/evidence/p09-codec-fixture-manifest.v1.json',bytes=1,sha256='c'*64)
        semantic[manifest['path']]=manifest
        def project(required,checkpoint):return source.Projection(required,rows,next_case=165,checkpoint=checkpoint),{}
        binding=NS(descriptors=lambda:rows,manifest_pin=manifest,project=project)
        class Reader:
            def __init__(self,*args):raise AssertionError('NO_READER_OR_IO_DURING_CONNECTION')
        def run(*args):pass
        engine=NS(run_owned=FunctionType(run.__code__,dict(__name__='p09_exact_fixture_engine',build=NS(
            BuildReader=Reader,pressure_summary=lambda *args:{}))))
        budget=shared.SharedBudget()
        connection=metadata.connect_engine(engine,binding,fresh,physical.DecoderBudget,lambda:None,budget)
        declared=project(semantic,lambda:None)[0]
        owner=NS(phase='NEW',shared=budget,metadata_connection=connection)
        linked=NS(engine=engine,state=NS(attempts=0,calls=0))
        return linked,owner,declared,rows,original,encoded
    def connect(self,fixture):
        return m.connect(*fixture[:3],candidate,self.raw(m.SOURCE),self.raw(m.METADATA),self.raw(candidate.SOURCE))

    def test_actual_metadata_router_and_future_projection_share_new_private_codec(self):
        fixture=self.fixture();linked,owner,projection,rows,original,encoded=fixture
        old=type(projection).decode_fresh;saved_codec=codec.decode;saved_globals=dict(old.__globals__)
        link,proof=self.connect(fixture)
        new=type(projection).decode_fresh
        self.assertIs(new.__code__,old.__code__);self.assertIs(codec.decode,saved_codec)
        self.assertTrue(all(old.__globals__[name] is value for name,value in saved_globals.items()))
        factory=linked.engine.run_owned.__globals__['build'].BuildReader.__new__
        router_type=m.cells(factory)['Router'];router=router_type(physical.DecoderBudget(lambda:None))
        row=rows[0];name=row['semantic_original_pin']['path'];pin=row['physical_envelope_pin']
        self.assertEqual(router.decode_fresh(name,pin,encoded,lambda:None),original)
        self.assertEqual(projection.decode_fresh(name,pin,encoded,lambda:None),original)
        self.assertEqual(owner.metadata_connection.readers,[]);self.assertEqual(owner.metadata_connection.budgets,[])
        self.assertTrue(proof['exact_same_metadata_and_Frame_projection_class'])
        self.assertIs(link.projection_type,type(projection));self.assertIs(link.method,new)
        self.assertFalse(proof['reader_or_Frame_or_budget_created']);self.assertFalse(proof['installed_in_product'])

    def test_source_drift_rejected_without_codec_installation(self):
        fixture=self.fixture();cls=type(fixture[2]);before=cls.decode_fresh
        with self.assertRaisesRegex(ValueError,'EXACT_ENTIRE_SOURCE'):
            m.connect(*fixture[:3],candidate,self.raw(m.SOURCE)+b'\n',self.raw(m.METADATA),self.raw(candidate.SOURCE))
        self.assertIs(cls.decode_fresh,before)

    def test_default_projection_class_is_never_modified(self):
        fixture=self.fixture(default=True);old=default_source.Projection.decode_fresh
        with self.assertRaisesRegex(ValueError,'NO_DEFAULT_PROJECTION'):self.connect(fixture)
        self.assertIs(default_source.Projection.decode_fresh,old)

    def test_nonfresh_parent_or_metadata_connection_rejected(self):
        for kind in ('phase','reader','worker'):
            fixture=self.fixture();linked,owner=fixture[:2]
            if kind=='phase':owner.phase='READY'
            elif kind=='reader':owner.metadata_connection.readers.append(object())
            else:linked.state.attempts=1
            with self.assertRaises(ValueError):self.connect(fixture)

    def test_wrong_frame_projection_class_and_changed_body_rejected(self):
        fixture=self.fixture()
        with self.assertRaisesRegex(ValueError,'SAME_FULL162_PRIVATE_PROJECTION'):
            m.connect(fixture[0],fixture[1],object(),candidate,self.raw(m.SOURCE),self.raw(m.METADATA),self.raw(candidate.SOURCE))
        cls=type(fixture[2]);old=cls.decode_fresh
        def changed(*args):return b'wrong'
        cls.decode_fresh=FunctionType(changed.__code__,old.__globals__)
        with self.assertRaisesRegex(ValueError,'ALL_ORIGINAL_PROJECTION'):self.connect(fixture)

    def test_second_installation_cannot_silently_replace_an_active_dependency(self):
        fixture=self.fixture();self.connect(fixture);installed=type(fixture[2]).decode_fresh
        with self.assertRaises(ValueError):self.connect(fixture)
        self.assertIs(type(fixture[2]).decode_fresh,installed)

    def test_original_live_guard_failure_and_corrupt_wire_still_fail(self):
        fixture=self.fixture();self.connect(fixture);projection=fixture[2];row=fixture[3][0]
        name=row['semantic_original_pin']['path'];pin=row['physical_envelope_pin']
        def stop():raise ValueError('ORIGINAL_LIVE_GUARD')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_LIVE_GUARD'):
            projection.decode_fresh(name,pin,fixture[5],stop)
        with self.assertRaises(ValueError):projection.decode_fresh(name,pin,fixture[5]+b'x',lambda:None)


if __name__=='__main__':unittest.main()
