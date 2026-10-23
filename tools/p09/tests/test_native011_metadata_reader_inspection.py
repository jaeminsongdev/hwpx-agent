import time
import unittest
from types import SimpleNamespace as NS
import owned_source_read_pressure as pressure
import owned_input_read_pressure as query
import native011_metadata_reader_inspection as m


class Tests(unittest.TestCase):
    def fixture(self):
        allocated=[]
        class Reader(pressure.WeightedReader):
            def __init__(self,*args):
                super().__init__(*args);self.open_pacer=query.QueryPacer(self.checkpoint);allocated.append(self)
            def _source(self,*args):raise AssertionError('NO_SOURCE_OR_IO')
        connection=NS(original_reader=Reader,readers=[],budgets=[])
        owner=NS(phase='NEW',metadata_connection=connection,shared=NS(metadata=None,frame=None,restored=False))
        linked=NS(state=NS(attempts=0,calls=0))
        return owner,linked,allocated

    def test_exact_unused_allocator_once_no_io_or_metadata_budget(self):
        owner,linked,allocated=self.fixture()
        value=m.inspect_unused(owner,linked,'.',lambda:None)
        self.assertEqual(len(allocated),1);self.assertEqual(allocated[0].read_passes,0)
        self.assertEqual(value['independently_allocated_pacer_selected_rates'],{'binary':1048576,'other':2097152})
        self.assertIs(allocated[0].pacer.clock,time.monotonic)
        self.assertEqual(value['actual_query_reservations'],0);self.assertFalse(value['GO_authorized'])
        self.assertFalse(value['actual_allocator_result_fields_class_pacer_or_clocks_changed'])

    def test_active_owner_or_previous_decoder_or_worker_refused_before_allocation(self):
        for bad in ('owner','budget','worker'):
            owner,linked,allocated=self.fixture()
            if bad=='owner':owner.phase='READY'
            if bad=='budget':owner.shared.metadata=object()
            if bad=='worker':linked.state.attempts=1
            with self.assertRaises(ValueError):m.inspect_unused(owner,linked,'.',lambda:None)
            self.assertEqual(allocated,[])

    def test_allocator_that_has_already_read_cannot_be_credited(self):
        owner,linked,allocated=self.fixture();original=owner.metadata_connection.original_reader
        def used(*args):
            reader=original(*args);reader.read_passes=1;return reader
        owner.metadata_connection.original_reader=used
        with self.assertRaisesRegex(ValueError,'ALLOCATOR_MUST_RETURN_UNREAD'):
            m.inspect_unused(owner,linked,'.',lambda:None)
        self.assertEqual(allocated[0].read_passes,1)

    def test_driver_only_declares_two_named_roles_no_repeated_admission(self):
        class Base:
            def __init__(self,attempt,construct_only):self.attempt=attempt;self.construct_only=construct_only
            def bind(self,*args):pass
        control=NS(admit=lambda *args,**options:NS(control_names=tuple(str(i) for i in range(35))))
        driver=m.driver_type(Base)();driver.bind(None,None,None,None,None,control)
        value=control.admit(None,None,None,exact_read=True,decoder_timing=True,chunk_join=True)
        self.assertEqual(value.control_names[-2:],(m.SELF,m.TEST));self.assertTrue(driver.construct_only)
        self.assertEqual(driver.attempt,7);self.assertEqual(driver.output,m.OUTPUT)
        with self.assertRaises(ValueError):control.admit(None,None,None,exact_read=True,decoder_timing=True,chunk_join=True)

    def test_original_metadata_pacer_assignment_is_inspected_without_calling_input_body(self):
        env=dict(byte_policy=pressure)
        # This initializer must never execute during code inspection.
        exec('def run_owned():\n def input_pins():\n  q=forbidden()\n  q.pacer=byte_policy.OwnedPacer()\n return input_pins',env)
        env['forbidden']=lambda:(_ for _ in ()).throw(AssertionError('NO_READER_ALLOCATION'))
        linked=NS(engine=NS(run_owned=env['run_owned']),state=NS(attempts=0,calls=0))
        row=m.inspect_engine_assignment(linked)
        self.assertEqual(row['original_owned_pacer_assignment_count'],1)
        self.assertEqual(row['original_owned_selected_rates'],{'binary':1048576,'other':2097152})
        self.assertFalse(row['actual_metadata_input_body_executed']);self.assertFalse(row['actual_reader_allocated'])
        self.assertFalse(row['GO_authorized'])

    def test_no_pacer_assignment_is_recorded_as_absent_but_missing_function_is_not_qualified(self):
        env=dict(byte_policy=pressure);exec('def run_owned():\n def input_pins():\n  return forbidden()\n return input_pins',env)
        linked=NS(engine=NS(run_owned=env['run_owned']),state=NS(attempts=0,calls=0))
        self.assertEqual(m.inspect_engine_assignment(linked)['original_owned_pacer_assignment_count'],0)
        exec('def run_owned():\n return forbidden()',env);linked.engine.run_owned=env['run_owned']
        result=m.inspect_engine_assignment(linked)
        self.assertFalse(result['metadata_function_recognized'])
        self.assertTrue(result['unrecognized_function_not_qualified_as_absent_assignment'])

    def test_existing_original_function_closure_is_followed_without_calling_wrapper(self):
        env=dict(byte_policy=pressure)
        exec('def run_owned():\n def input_pins():\n  q=forbidden()\n  q.pacer=byte_policy.OwnedPacer()\n return input_pins',env)
        def wrapper(original):
            def execute():return original()
            return execute
        linked=NS(engine=NS(run_owned=wrapper(env['run_owned'])),state=NS(attempts=0,calls=0))
        result=m.inspect_engine_assignment(linked)
        self.assertEqual(result['metadata_input_function_count'],1)
        self.assertEqual(result['original_owned_pacer_assignment_count'],1)
        self.assertEqual(len(result['existing_function_links']),2)
