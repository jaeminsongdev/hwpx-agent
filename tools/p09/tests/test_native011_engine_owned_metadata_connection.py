from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_engine_owned_metadata_connection as m
import native011_engine_owned_metadata_adoption as adoption
import native011_metadata_tail_connection as connection
import native011_metadata_tail_candidate as candidate
import native011_exact_read_budget as exact
import native011_chunk_join_connection as codes
import reusable_audit_chunk_v1 as chunk
import owned_source_read_pressure as pressure
import test_native011_metadata_tail_connection as metadata_fixture


class Tests(unittest.TestCase):
    def raw(self,pin):return (Path(__file__).resolve().parents[3]/pin['path']).read_bytes()
    def fixture(self):return metadata_fixture.Tests().fixture()
    def connect(self,fixture,**raws):
        return m.connect(*fixture,connection,candidate,adoption,exact,pressure,chunk,self.raw(exact.ORIGINAL),
            raws.get('metadata',self.raw(connection.METADATA)),self.raw(connection.BUILD),codes)

    def test_only_selector_dependency_changes_no_reader_or_budget_allocation(self):
        fixture=self.fixture();linked,owner,pins=fixture;before=linked.engine.run_owned.__globals__['build']
        selector=candidate.reader_type;link,proof=self.connect(fixture)
        self.assertIs(candidate.reader_type,selector);self.assertIs(before.BuildReader,link.previous)
        self.assertEqual(owner.metadata_connection.readers,[]);self.assertIsNone(owner.shared.metadata)
        self.assertEqual(proof['reader_allocations_during_connection'],0)
        self.assertEqual(proof['original_engine_metadata_IO_rates'],{'binary':1048576,'other':2097152})
        self.assertFalse(proof['GO_authorized'])

    def test_actual_original_prefix_assigns_owned_pacer_once_before_any_io(self):
        fixture=self.fixture();linked,owner,pins=fixture;link,proof=self.connect(fixture)
        reader,prefix=m.allocate_original_prefix(self.raw(m.ENGINE),linked.engine.run_owned.__globals__['build'],'.',lambda:None,pressure)
        self.assertIsInstance(reader,link.selected_reader);self.assertEqual(owner.metadata_connection.readers,[reader])
        self.assertEqual(len(owner.metadata_connection.budgets),1)
        self.assertTrue(adoption.summary(reader)['original_engine_owned_assignment_adopted'])
        self.assertEqual(reader.read_passes,0);self.assertEqual(reader.open_pacer.requests,0)
        self.assertEqual(prefix['original_statements_executed'],2)
        reader.pacer.select('a.exe');self.assertEqual(reader.pacer.rate,1048576)
        reader.pacer.select('a.json');self.assertEqual(reader.pacer.rate,2097152)
        with self.assertRaises(ValueError):reader.pacer=pressure.OwnedPacer()

    def test_original_source_drift_rejected_before_allocation_or_replacement(self):
        fixture=self.fixture();linked,owner,pins=fixture;before=linked.engine.run_owned.__globals__['build']
        with self.assertRaises(ValueError):self.connect(fixture,metadata=self.raw(connection.METADATA)+b'\n')
        self.assertIs(linked.engine.run_owned.__globals__['build'],before)
        with self.assertRaisesRegex(ValueError,'WHOLE_ORIGINAL_ENGINE_SOURCE'):
            m.allocate_original_prefix(self.raw(m.ENGINE)+b'\n',before,'.',lambda:None,pressure)
        self.assertEqual(owner.metadata_connection.readers,[])

    def test_owned_selection_failure_restores_private_factory_without_default_mutation(self):
        fixture=self.fixture();linked,owner,pins=fixture;before=linked.engine.run_owned.__globals__['build']
        def refused(*args,**kwargs):raise ValueError('MODEL_OWNED_SELECTOR_STOP')
        with self.assertRaisesRegex(ValueError,'MODEL_OWNED_SELECTOR_STOP'):
            m.connect(*fixture,connection,candidate,NS(reader_type=refused),exact,pressure,chunk,self.raw(exact.ORIGINAL),
                self.raw(connection.METADATA),self.raw(connection.BUILD),codes)
        self.assertIs(linked.engine.run_owned.__globals__['build'],before)
        self.assertEqual(owner.metadata_connection.readers,[]);self.assertIsNone(owner.shared.metadata)

    def test_prefix_has_only_two_original_calls_not_callback_frame_worker_or_go(self):
        calls=[];reader=NS()
        factory=NS(BuildReader=lambda root,check:(calls.append((root,check)) or reader))
        checkpoint=lambda:None
        actual,proof=m.allocate_original_prefix(self.raw(m.ENGINE),factory,'component-root',checkpoint,pressure)
        self.assertIs(actual,reader);self.assertEqual(calls,[('component-root',checkpoint)])
        self.assertIs(type(reader.pacer),pressure.OwnedPacer)
        self.assertFalse(proof['original_metadata_input_body_or_Native_or_product_executed'])
