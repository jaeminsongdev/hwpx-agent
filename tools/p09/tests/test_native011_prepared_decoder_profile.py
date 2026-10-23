import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
import native011_prepared_decoder_profile as m
import runtime_envelope_physical_io_v1 as physical
import runtime_record_envelope_v2 as codec
import native011_decoder_chunk_join as chunk_join


class FakeGC:
    def __init__(self):self.callbacks=[];self.enabled=True;self.threshold=(700,10,10)
    def isenabled(self):return self.enabled
    def get_threshold(self):return self.threshold


class Tests(unittest.TestCase):
    def test_gc_observation_records_only_original_budget_overlap_and_restores_callbacks(self):
        gc=FakeGC();old=lambda *args:None;gc.callbacks=[old]
        budget=NS(active=1.);window=m.GCWindow(budget,module=gc,clock=iter((1.,1.25,2.,2.5)).__next__)
        window.open();window.observe('start',dict(generation=0));window.observe('stop',dict(generation=0))
        budget.active=None;window.observe('start',dict(generation=1));window.observe('stop',dict(generation=1))
        window.close();result=window.evidence()
        self.assertEqual(gc.callbacks,[old]);self.assertEqual(result['inside_decoder_seconds'],.25)
        self.assertEqual(result['outside_decoder_seconds'],.5);self.assertFalse(result['failed'])
        self.assertTrue(result['enabled_and_thresholds_unchanged'])

    def test_gc_callback_errors_are_sticky_and_do_not_replace_original_exceptions(self):
        gc=FakeGC();window=m.GCWindow(NS(active=None),module=gc,clock=lambda:1.)
        window.open();window.observe('stop',dict(generation=0));window.close()
        self.assertTrue(window.evidence()['failed']);self.assertEqual(gc.callbacks,[])

    def test_foreign_callback_or_threshold_change_is_preserved_not_silently_repaired(self):
        for kind in ('callback','threshold'):
            gc=FakeGC();window=m.GCWindow(NS(active=None),module=gc);window.open()
            foreign=lambda *args:None
            if kind=='callback':gc.callbacks.append(foreign)
            else:gc.threshold=(1,2,3)
            window.close();self.assertTrue(window.evidence()['failed'])
            if kind=='callback':self.assertEqual(gc.callbacks,[foreign])
            else:self.assertEqual(gc.threshold,(1,2,3))

    def component_fixture(self,*,stop=False):
        rows=[dict(physical_envelope_pin=dict(path=f'physical{i}',bytes=1,sha256='a'*64),
            semantic_original_pin=dict(path=f'logical{i}')) for i in range(162)]
        calls=[];ticks=[0.]
        def decode(name,pin,raw,check):
            if stop:ticks[0]+=5.1
            check();return b'x'
        projection=NS(decode_fresh=decode)
        binding=NS(project=lambda *args:(projection,{}),descriptors=lambda:rows)
        budget_type=(lambda checkpoint:physical.DecoderBudget(checkpoint,clock=lambda:ticks[0])) if stop else physical.DecoderBudget
        prepared=NS(entry=NS(graph=NS(binding=binding,frames=NS(connection=NS(original=NS(DecoderBudget=budget_type))))))
        def read(name,parse=False):
            calls.append((name,parse));return next(row['physical_envelope_pin'] for row in rows
                if row['physical_envelope_pin']['path']==name),b'x'
        q=NS(_read=read,_bind=lambda *args:None)
        a=NS(exact=lambda actual,expected,label:self.assertEqual(actual,expected))
        entry=NS(current_logical=lambda *args:{})
        return q,a,entry,NS(scope=None),NS(),prepared,calls

    def test_profile_loop_uses_every_fresh_input_and_original_budget_and_cleanup(self):
        args=self.component_fixture();before=tuple(m.gc.callbacks);enabled=m.gc.isenabled();threshold=m.gc.get_threshold()
        row=m.measured_profile(*args[:6],lambda:None)
        self.assertEqual(row['completed_decodes'],162);self.assertEqual(len(args[-1]),162)
        self.assertTrue(all(parse for name,parse in args[-1]));self.assertEqual(row['physical_bytes'],162)
        self.assertEqual(row['decoder']['completed_decodes'],162);self.assertEqual(row['decoder']['aggregate_limit_seconds'],5.)
        self.assertFalse(row['combined_metadata_Frame5_or_Native_qualified'])
        self.assertEqual(tuple(m.gc.callbacks),before);self.assertEqual(m.gc.isenabled(),enabled)
        self.assertEqual(m.gc.get_threshold(),threshold)

    def test_original_decoder_stop_is_recorded_not_passed_or_retried(self):
        args=self.component_fixture(stop=True);row=m.measured_profile(*args[:6],lambda:None)
        self.assertEqual(len(args[-1]),1);self.assertEqual(row['completed_decodes'],0)
        self.assertEqual(row['original_decoder_error'],'STOP_AGGREGATE_ENVELOPE_DECODER5')
        self.assertTrue(row['decoder']['terminal_error_seen']);self.assertTrue(row['GC_observation']['callbacks_restored'])

    def test_driver_only_adds_two_named_roles_and_never_enters_native(self):
        class Base:
            def __init__(self,attempt,construct_only):
                self.attempt=attempt;self.construct_only=construct_only;self.stage='construction';self.native=None
                self.check=lambda **kwargs:None
            def bind(self,*args):pass
            def run(self,*args):return dict(actual_Native_Frame_created=False,actual_product_executed=False)
        old=lambda *args,**kwargs:NS(control_names=tuple(f'model{i}' for i in range(31)))
        control=NS(admit=old);driver=m.driver_type(Base)();driver.bind(None,None,None,None,None,control)
        declaration=control.admit(None,None,None,exact_read=True,decoder_timing=True,chunk_join=False)
        self.assertEqual(declaration.control_names[-2:],(m.SELF,m.TEST));self.assertTrue(driver.construct_only)
        self.assertEqual(driver.output,m.OUTPUT)
        with self.assertRaises(ValueError):control.admit(None,None,None,exact_read=True,decoder_timing=True,chunk_join=False)
        data=NS(planned=NS(batch=NS(phase='NEW')))
        reader=NS(finish=lambda:None,snapshots={},final_fresh_hashes=0,read_passes=0,bytes_read=0)
        a=NS(AcceptanceReader=lambda *args:reader)
        with patch.object(m,'measured_profile',return_value=dict(original_decoder_error=None)):
            row=driver.run(None,None,a,None,None,None,data,None,None,None,None,{},None,None)
        self.assertFalse(row['actual_Native_Frame_created']);self.assertFalse(row['actual_product_executed'])
        self.assertIn('NOT_NATIVE_OR_PRODUCT',row['state'])
        self.assertFalse(row['prepared_decoder_profile']['actual_component_reader']['constructor_reader_reused_or_counters_reset'])

    def test_candidate_changes_codec_slot_without_mutating_original_module(self):
        original=codec.decode;raw=codec.encode(b'x',lambda:None);pins={}
        for i in range(162):pins[f'physical{i}']=dict(path=f'physical{i}',bytes=len(raw),sha256=m.hashlib.sha256(raw).hexdigest())
        descriptors=[dict(physical_envelope_pin=pin,semantic_original_pin=dict(path=f'logical{i}')) for i,pin in enumerate(pins.values())]
        env=dict(codec=codec)
        exec('def decode_fresh(self,name,pin,raw,checkpoint):\n checkpoint()\n return codec.decode(raw,checkpoint)',env)
        projection=type('FixtureProjection',(),dict(decode_fresh=env['decode_fresh']))()
        binding=NS(project=lambda *args:(projection,{}),descriptors=lambda:descriptors)
        prepared=NS(entry=NS(graph=NS(binding=binding,frames=NS(connection=NS(original=physical)))))
        q=NS(_read=lambda name,parse=False:(pins[name],raw),_bind=lambda *args:None)
        a=NS(exact=lambda left,right,label:self.assertEqual(left,right))
        candidate=NS(api=chunk_join,original_raw=(m.Path(__file__).resolve().parents[3]/chunk_join.SOURCE['path']).read_bytes())
        result=m.measured_profile(q,a,NS(current_logical=lambda *args:{}),NS(scope=None),None,prepared,lambda:None,candidate=candidate)
        self.assertEqual(result['codec_variant'],'chunk_join');self.assertEqual(result['completed_decodes'],162)
        self.assertIs(codec.decode,original)
        self.assertTrue(result['codec_connection_proof']['exact_original_decoder_AST_inverse'])
        self.assertFalse(result['combined_metadata_Frame5_or_Native_qualified'])

    def test_candidate_profile_is_closed_and_declares_its_two_extra_sources(self):
        class Base:
            def __init__(self,attempt,construct_only):self.construct_only=construct_only
            def bind(self,*args):pass
        old=lambda *args,**kwargs:NS(control_names=tuple(f'model{i}' for i in range(31)))
        control=NS(admit=old);driver=m.driver_type(Base,chunk_join=True)()
        driver.bind(None,None,None,None,None,control)
        declared=control.admit(None,None,None,exact_read=True,decoder_timing=True,chunk_join=False)
        self.assertEqual(declared.control_names[-4:],(m.SELF,m.TEST)+m.CANDIDATE)
        self.assertEqual(driver.output,m.CANDIDATE_OUTPUT);self.assertTrue(driver.construct_only)
        with self.assertRaises(ValueError):m.driver_type(Base,chunk_join=1)


if __name__=='__main__':unittest.main()
