from pathlib import Path
from contextlib import nullcontext
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
import native011_engine_owned_metadata_callback as m
import native011_engine_owned_metadata_connection as connection
import native011_metadata_audit as audit


class Tests(unittest.TestCase):
    def raw(self,pin):return (Path(__file__).resolve().parents[3]/pin['path']).read_bytes()
    def project(self,**kwargs):
        return m.project(kwargs.get('raw',self.raw(m.SOURCE)),kwargs.get('original',audit.metadata),
            kwargs.get('engine',self.raw(connection.ENGINE)),connection)
    def fixture(self):
        events=[];pin=dict(path='helper.py',bytes=1,sha256='model')
        reader=NS(snapshots={'helper.py':pin},final_fresh_hashes=0,read_passes=2,bytes_read=2)
        def finish():events.append('closing');reader.final_fresh_hashes=1
        reader.finish=finish;reader.pin=lambda name:(events.append('helper') or pin)
        owner=NS(phase='READY',whole={'helper.py':pin},initial={'helper.py':pin},
            metadata_connection=NS(readers=[],budgets=[]),shared=NS(metadata=None,frame=None,evidence=lambda:{}))
        owner.metadata_reader=lambda *args:nullcontext()
        required={'helper.py':pin};build=object();pressure=object()
        def run():pass
        # A model namespace is distinct from the test module's defaults.
        from types import FunctionType
        run=FunctionType(run.__code__,dict(build=build,byte_policy=pressure))
        def original(reader):events.append('callback');return required,{'helper.py'}
        binding=NS(project=lambda required,check:(NS(physical_pins=required),None))
        context=NS(data=NS(planned=NS(batch=owner,current=required)),
            prepared=NS(entry=NS(graph=NS(binding=binding)),linked=NS(engine=NS(run_owned=run))),
            bound=NS(attached=NS(callback=original,calls=[None])),batch=NS(plain=lambda value:value),
            oracle_result=NS(known=required),row={'oracle_construction':{'helper_inventory':{'original_Native_helper_union':['helper.py']}}},
            shared=NS(components=NS(fresh_lossless_metadata_reader_v1=NS(summary=lambda value:{}))))
        epochs=NS(check=lambda **kwargs:events.append('check'),validator=lambda value:events.append('validate'))
        a=NS(exact=lambda actual,expected,label:self.assertEqual(actual,expected))
        def allocate(raw,b,r,checkpoint,p):
            self.assertIs(b,build);self.assertIs(p,pressure);self.assertEqual(raw,self.raw(connection.ENGINE))
            self.assertEqual(r,'model-root');events.append('allocate');owner.metadata_connection.readers.append(reader)
            owner.metadata_connection.budgets.append(object());owner.shared.metadata=object()
            return reader,dict(original_statements_executed=2,GO_authorized=False)
        return context,epochs,a,allocate,events
    def test_projection_has_no_io_or_default_mutation_and_restores_entire_original_ast(self):
        before=audit.metadata
        with patch.object(connection,'allocate_original_prefix',side_effect=AssertionError('NO_ALLOCATION')):
            link,proof=self.project()
        self.assertIs(audit.metadata,before);self.assertEqual(link.state.attempts,0)
        self.assertTrue(proof['entire_original_metadata_body_inverse']);self.assertEqual(proof['changed_allocation_dependency_sites'],1)
        self.assertFalse(proof['GO_authorized']);self.assertFalse(proof['shared_decoder_or_deadlines_or_resource_checks_modified'])
    def test_original_complete_callback_helpers_and_finish_execute_after_original_owned_prefix(self):
        link,proof=self.project();context,epochs,a,allocate,events=self.fixture()
        with patch.object(connection,'allocate_original_prefix',side_effect=allocate) as called:
            result=link.callback('model-root',epochs,context,a)
        called.assert_called_once();self.assertEqual((link.state.attempts,link.state.completed,link.state.failed),(1,1,False))
        self.assertLess(events.index('allocate'),events.index('callback'));self.assertLess(events.index('callback'),events.index('helper'))
        self.assertLess(events.index('helper'),events.index('closing'));self.assertEqual(result['final_fresh_hashes'],1)
        self.assertFalse(result['complete_product_input_pins_qualified']);self.assertFalse(result['Frame_created'])
        with self.assertRaisesRegex(ValueError,'NO_RETRY'):link.callback('model-root',epochs,context,a)
    def test_source_or_function_drift_refused_before_allocation(self):
        with patch.object(connection,'allocate_original_prefix',side_effect=AssertionError('NO_ALLOCATION')):
            for kwargs in ({'raw':self.raw(m.SOURCE)+b'\n'},{'engine':self.raw(connection.ENGINE)+b'\n'},
                {'original':lambda root,epochs,context,a:None}):
                with self.assertRaises(ValueError):self.project(**kwargs)
    def test_callback_failure_is_sticky_and_original_error_retained(self):
        link,proof=self.project();context,epochs,a,allocate,events=self.fixture()
        def fail(reader):raise ValueError('ORIGINAL_MODEL_SOURCE_FAILURE')
        context.bound.attached.callback=fail
        with patch.object(connection,'allocate_original_prefix',side_effect=allocate):
            with self.assertRaisesRegex(ValueError,'ORIGINAL_MODEL_SOURCE_FAILURE'):link.callback('model-root',epochs,context,a)
        self.assertTrue(link.state.failed);self.assertEqual(link.state.completed,0);self.assertNotIn('closing',events)
        with self.assertRaisesRegex(ValueError,'NO_RETRY'):link.callback('model-root',epochs,context,a)
    def test_no_prior_opening_or_used_reader_can_enter_owned_allocator(self):
        for change in ('no_opening','used_reader'):
            link,proof=self.project();context,epochs,a,allocate,events=self.fixture();owner=context.data.planned.batch
            if change=='no_opening':owner.phase='NEW'
            else:owner.metadata_connection.readers.append(object())
            with patch.object(connection,'allocate_original_prefix',side_effect=AssertionError('NO_ALLOCATION')):
                with self.assertRaises(ValueError):link.callback('model-root',epochs,context,a)
            self.assertTrue(link.state.failed);self.assertEqual(link.state.completed,0)
    def test_original_resource_failure_before_allocation_is_sticky(self):
        link,proof=self.project();context,epochs,a,allocate,events=self.fixture()
        original=epochs.check
        def fail(**kwargs):raise ValueError('ORIGINAL_MODEL_RESOURCE_STOP')
        epochs.check=fail
        with patch.object(connection,'allocate_original_prefix',side_effect=AssertionError('NO_ALLOCATION')):
            with self.assertRaisesRegex(ValueError,'ORIGINAL_MODEL_RESOURCE_STOP'):link.callback('model-root',epochs,context,a)
        self.assertTrue(link.state.failed);self.assertEqual(link.state.attempts,0)
        epochs.check=original
        with self.assertRaisesRegex(ValueError,'NO_RETRY'):link.callback('model-root',epochs,context,a)
