from pathlib import Path
from types import FunctionType, SimpleNamespace as NS
import unittest
from unittest.mock import patch

import batch_product_runtime as original
import native011_product_lifecycle as m
import native011_product_once as once_api
import test_native011_product_parent_handoff as parent_fixture
import batch_zlib_metadata as metadata_original
import batch_native_checkpoint as native_checkpoint
import test_batch_zlib_metadata as preparation_fixture
import batch_post_job_checkpoint
import preparation_checkpoint_owner
import batch_post_native
import batch_pre_go_runtime
import runtime_envelope_namespace_bundle_v1 as namespace_loader
import test_batch_post_native as post_native_fixture
import native011_full_frame_worker_connection as process_connection
import subprocess
import json
import accept_case112_current_epoch as original_acceptance


class Tests(unittest.TestCase):
    def build(self):
        root=Path(__file__).resolve().parents[3]
        return m.build((root/m.SOURCE['path']).read_bytes(),original,(root/m.PARENT['path']).read_bytes())
    def fixture(self,*,authority=True,code=0):
        f=NS(events=[],claims={},readers=[],native_error=None,closing_error=None,oracle_error=None,finish_error=None)
        f.once=once_api.Once(lambda:f.events.append('guard'),authorize=None if authority is None else lambda:authority)
        f.source=parent_fixture.Tests().fixture(authorize=f.once.authorize_native)
        prior=f.source.actual.run_owned
        def current(run):
            f.events.append('original_native')
            if f.native_error is not None:raise f.native_error
            self.assertEqual(prior(run),17)  # Original fixture's synthetic return only.
            return code
        f.source.actual.run_owned=current;f.connected=f.source.install();f.compiled=self.build()
        f.batch=f.source.owner;f.batch.checkpoint=lambda:None
        f.batch.begin=lambda reader:f.events.append('whole_opening')
        f.context=NS(result=NS(assembled=NS(batch=f.batch,parent=f.source.actual,built=f.source.linked)),
            connected=NS(core={'step':{'case':'MODEL_CASE165'}}))
        f.route=NS(checkpoint=f.batch.checkpoint,context=f.connected.context)
        def finish(context):
            f.events.append('native_terminal')
            if f.finish_error is not None:raise f.finish_error
        f.relay=NS(arm=lambda:f.events.append('handoff_armed'),finish_native=finish)
        f.epochs=NS(advance=lambda role:f.events.append(('epoch',role)),
            check=lambda **kwargs:f.events.append('preparation_final'),close=lambda:f.events.append('preparation_closed'))
        f.policy=NS(attempts=1,denied=[],arm=lambda context:f.events.append('process_armed'))
        def Reader(root,checkpoint):
            reader=NS(snapshots={},bytes_read=0,final_fresh_hashes=0,checkpoint=checkpoint)
            def row(path):
                f.events.append(('fresh',path));reader.snapshots[path]=dict(path=path,bytes=1,sha256='0'*64)
                reader.bytes_read+=1;return {'samples':[]}
            reader.json=row;f.readers.append(reader);return reader
        f.Reader=Reader
        f.route.start_closing=lambda:f.events.append('closing_started')
        def closing(reader):
            f.events.append('whole_closing')
            if f.closing_error is not None:raise f.closing_error
            return dict(model_only=True)
        f.route.finish_whole=closing
        def verify(reader,*,load_inputs):
            f.events.append('oracle')
            if f.oracle_error is not None:raise f.oracle_error
            values=load_inputs(reader);self.assertEqual(len(values),5)
            reader.final_fresh_hashes=len(reader.snapshots);return {},{'model_only':True}
        f.route.verify=verify
        f.context.result.assembled.checker=NS(environment={'context':lambda config:NS(INDEX=165,BEFORE=158,CASE='MODEL_CASE165')})
        f.source.linked.window.M=NS(base=NS(CONFIG=object()))
        def read_exact(reader,pin):reader.json(pin['path']);return {'model_only':True}
        f.api=NS(c=NS(ROOT=Path('model-root')),scope=NS(LIST_PIN={'path':'model-list.json'}),
            BODY_PIN={'path':'model-body.json'},FRESH_PIN={'path':'model-fresh.json'},
            read_exact=read_exact,packed=NS(unpack=lambda row,checkpoint:row))
        def write(row):
            f.events.append('claim')
            if once_api.CLAIM in f.claims:raise FileExistsError('MODEL_EXISTING_INTENT')
            f.claims[once_api.CLAIM]=dict(row);return dict(path=once_api.CLAIM,bytes=300,sha256='a'*64)
        f.write=write
        f.run=lambda:f.compiled.invoke(f.once,once_api.Once,f.write,f.context,f.route,f.relay,f.epochs,f.Reader,
            f.policy,f.api,f.events.append)
        return f

    def test_entire_original_code_inverse_and_default_namespace_unchanged(self):
        before=(original.CANONICAL,original.execute_chain.__code__,original.oracle_inputs.__code__)
        value=self.build();self.assertTrue(value.projection['whole_original_entry_code_inverse'])
        self.assertEqual(value.projection['exact_progress_label_changes'],1)
        self.assertIs(value.oracle_inputs.__code__,original.oracle_inputs.__code__)
        self.assertEqual(before,(original.CANONICAL,original.execute_chain.__code__,original.oracle_inputs.__code__))
        self.assertFalse(value.projection['actual_controller_and_worker202_audit_connected'])

    def test_whole_sequence_and_original_five_inputs_follow_native011_namespace_model_only(self):
        f=self.fixture();value=f.run()
        self.assertLess(f.events.index('claim'),f.events.index('whole_opening'))
        self.assertLess(f.events.index('preparation_closed'),f.events.index('original_native'))
        self.assertLess(f.events.index('original_native'),f.events.index('native_terminal'))
        self.assertLess(f.events.index('native_terminal'),f.events.index('whole_closing'))
        self.assertLess(f.events.index('whole_closing'),f.events.index('oracle'))
        self.assertIn('RUNNING_ORIGINAL_NATIVE011_PRODUCT_ONCE',f.events)
        self.assertNotIn(('fresh',original.CANONICAL),f.events);self.assertIn(('fresh',m.CANONICAL),f.events)
        self.assertEqual(len([item for item in f.events if type(item) is tuple and item[0]=='fresh']),4)
        self.assertEqual(f.once.evidence()['phase'],'RETURNED_NOT_ACCEPTED');self.assertFalse(f.once.evidence()['product_acceptance_qualified'])
        self.assertEqual(value['canonical_receipt_pin']['path'],m.CANONICAL)
        self.assertEqual(f.connected.context.jobs,1);self.assertTrue(f.connected.state.cleanup_confirmed)
        self.assertEqual(f.connected.context.bindings[0].gates[0].seconds,15)

    def test_absent_or_false_authority_denies_before_claim_whole_opening_or_job(self):
        for value in (None,False):
            f=self.fixture(authority=value)
            with self.assertRaisesRegex(ValueError,'EXTERNAL_EXECUTION_AUTHORITY_REQUIRED'):f.run()
            self.assertEqual(f.claims,{});self.assertNotIn('whole_opening',f.events);self.assertEqual(f.connected.context.jobs,0)

    def test_native_nonzero_marks_terminal_but_never_opens_closing_or_oracle(self):
        f=self.fixture(code=17)
        with self.assertRaisesRegex(ValueError,'ORIGINAL_NATIVE_FAILED_NO_AUTOMATIC_RETRY'):f.run()
        self.assertIn('native_terminal',f.events);self.assertNotIn('whole_closing',f.events);self.assertNotIn('oracle',f.events)
        self.assertIn(once_api.CLAIM,f.claims);self.assertTrue(f.once.failed)

    def test_primary_native_exception_survives_teardown_exception_without_success(self):
        f=self.fixture();primary=ValueError('MODEL_PRIMARY_NATIVE_ERROR');f.native_error=primary;f.finish_error=OSError('MODEL_SECONDARY_CLEANUP')
        with self.assertRaises(ValueError) as caught:f.run()
        self.assertIs(caught.exception,primary);self.assertTrue(f.compiled.state.finish_failed)
        self.assertEqual(f.compiled.state.finish_error_type,'OSError');self.assertNotIn('whole_closing',f.events)
        self.assertFalse(f.compiled.state.original_procedure_returned)

    def test_teardown_failure_after_success_still_stops_closing_and_oracle(self):
        f=self.fixture();f.finish_error=OSError('MODEL_CLEANUP_UNCONFIRMED')
        with self.assertRaises(OSError):f.run()
        self.assertNotIn('whole_closing',f.events);self.assertNotIn('oracle',f.events);self.assertTrue(f.once.failed)

    def test_closing_or_oracle_failure_preserves_claim_and_no_retry(self):
        for where in ('closing_error','oracle_error'):
            f=self.fixture();error=ValueError('MODEL_ORIGINAL_CLOSING_OR_ORACLE_ERROR');setattr(f,where,error)
            with self.assertRaises(ValueError) as caught:f.run()
            self.assertIs(caught.exception,error);self.assertIn(once_api.CLAIM,f.claims)
            self.assertFalse(f.compiled.state.original_procedure_returned)
            with self.assertRaisesRegex(ValueError,'ONE_LIFECYCLE_INVOCATION_NO_RETRY'):f.run()

    def test_wrong_once_dependency_or_parent_context_is_rejected_before_io(self):
        for where in ('dependency','context'):
            f=self.fixture()
            if where=='dependency':f.route.context=NS(parent=object())
            else:f.batch.parent_connection.state.attempts=1
            with self.assertRaisesRegex(ValueError,'SAME_UNUSED_ORIGINAL_OWNER_AND_ONCE_DEPENDENCY'):f.run()
            self.assertEqual(f.claims,{});self.assertNotIn('whole_opening',f.events)

    def test_private_oracle_namespace_tamper_cannot_reach_intent_or_entry(self):
        f=self.fixture();f.compiled.execute_chain.__globals__['CANONICAL']=original.CANONICAL
        with self.assertRaisesRegex(ValueError,'PRIVATE_ORIGINAL_ENTRY_AND_ORACLE_BINDINGS_UNCHANGED'):f.run()
        self.assertEqual(f.claims,{});self.assertNotIn('whole_opening',f.events)

    def test_source_or_original_function_drift_is_denied_without_execution(self):
        root=Path(__file__).resolve().parents[3];raw=(root/m.SOURCE['path']).read_bytes();parent=(root/m.PARENT['path']).read_bytes()
        with self.assertRaisesRegex(ValueError,'EXACT_WHOLE_ORIGINAL_SOURCE'):m.build(raw+b' ',original,parent)
        with patch.object(original,'oracle_inputs',lambda *args:None):
            with self.assertRaises(ValueError):m.build(raw,original,parent)

    def test_inert_binding_attests_real_original_parent_without_calling_it(self):
        f=self.fixture(authority=None)
        proof=f.compiled.admit_parent_binding(f.context,f.route.context,f.batch.checkpoint,f.once,once_api.Once)
        self.assertTrue(proof['actual_original_parent_and_once_binding_attested'])
        self.assertFalse(proof['original_complete_entry_lifecycle_connected'])
        self.assertEqual(f.events,[]);self.assertEqual(f.claims,{})
        self.assertEqual(f.connected.context.jobs,0)
        self.assertEqual(f.compiled.state.invocations,0)

    def test_inert_binding_rejects_external_authority_or_changed_original_owner(self):
        for authorized in (True,False):
            f=self.fixture(authority=True if authorized else None)
            if not authorized:f.connected.context.attempts=1
            with self.assertRaises(ValueError):
                f.compiled.admit_parent_binding(f.context,f.route.context,f.batch.checkpoint,f.once,once_api.Once)
            self.assertEqual(f.claims,{});self.assertEqual(f.connected.context.jobs,0)

    def test_new_explicit_authority_parent_binding_is_inert_and_not_a_default_rebind(self):
        f=self.fixture();authority=f.once.external
        proof=f.compiled.admit_parent_binding(f.context,f.route.context,f.batch.checkpoint,f.once,once_api.Once,authorize=authority)
        self.assertTrue(proof['actual_original_parent_and_once_binding_attested'])
        self.assertEqual(f.once.external_calls,0);self.assertEqual(f.events,[]);self.assertEqual(f.claims,{})
        with self.assertRaises(ValueError):
            f.compiled.admit_parent_binding(f.context,f.route.context,f.batch.checkpoint,f.once,once_api.Once,authorize=lambda:True)

    def test_construction_instance_flags_or_unbounded_outputs_rejected_before_bootstrap(self):
        for options in (dict(authorize=True),dict(wrap=True),dict(output='D:/outside.json'),dict(output=m.CANONICAL)):
            with self.assertRaises(ValueError):m.construct(**options)

    def test_cli_is_construction_only_and_rejects_go_native_or_retry(self):
        with patch.object(m,'construct',return_value=17) as constructor,patch.object(m.sys,'argv',['test']):
            self.assertEqual(m.main(),17);constructor.assert_called_once_with()
        for flag in ('--go','--native','--runtime','--retry'):
            with patch.object(m,'construct') as constructor,patch.object(m.sys,'argv',['test',flag]):
                with self.assertRaisesRegex(ValueError,'CONSTRUCTION_ONLY'):m.main()
                constructor.assert_not_called()

    def preparation_fixture(self):
        root=Path(__file__).resolve().parents[3]
        f=preparation_fixture.Tests();f.fixture()
        # Synthetic unexecuted strict function for model-only inspection.
        env={};exec(compile('def connect_engine():\n return None\n',
            'tools/p09/strict_product_window_connection_v1.py','exec'),env)
        f.result.assembled.built.window.WINDOW_LINK.connect_engine=env['connect_engine']
        f.raw=(root/m.PREPARATION['path']).read_bytes()
        f.selected=m.preparation(f.raw,metadata_original,f.context)
        def factory(role):
            guard=preparation_fixture.Guard(role);f.guards.append(guard);return guard
        f.epochs=f.selected.Epochs(factory,clock=lambda:3,identity=lambda:f.owner[0])
        return f

    def test_actual_parent_context_selector_retains_all_original_preparation_bodies(self):
        original_selector=metadata_original.readiness_context
        original_class=metadata_original.ReadOnlyEpochs
        f=self.preparation_fixture()
        self.assertIs(f.selected.idle(f.result),f.context)
        self.assertIs(f.selected.idle.__code__,metadata_original.idle.__code__)
        for name,code in f.selected.original_method_codes.items():
            self.assertIs(code,getattr(original_class,name).__code__)
        self.assertIs(metadata_original.readiness_context,original_selector)
        self.assertIs(metadata_original.ReadOnlyEpochs,original_class)
        self.assertEqual(f.guards,[])
        self.assertFalse(f.selected.projection['actual_controller_or_Native_handoff_connected'])

    def test_original_preparation_epochs_use_actual_context_then_close_before_native_handoff(self):
        f=self.preparation_fixture();e=f.epochs
        relay=native_checkpoint.Handoff(e,f.selected.idle,identity=lambda:f.owner[0])
        e.advance('construction');relay.bind(f.result)
        e.advance('opening_and_metadata');f.opened();e.check(force=True);e.close();relay.arm()
        self.assertEqual([row['stage'] for row in e.records],['construction','opening_and_metadata'])
        self.assertTrue(all(row['cleanup_confirmed'] for row in e.records))
        self.assertEqual(relay.phase,'WAIT_ORIGINAL_NATIVE')
        self.assertIsNone(e.guard);self.assertIsNone(relay.reader)
        self.assertEqual([g.role for g in f.guards],['dispatch_construction','whole_metadata_preflight'])
        # An unbound WAIT phase remains unable to authorize arbitrary IO.
        with self.assertRaisesRegex(ValueError,'ONLY_ORIGINAL_NATIVE_CHECKPOINT'):relay.check()
        self.assertTrue(relay.broken)

    def test_preparation_context_identity_and_every_execution_counter_fail_closed(self):
        for name,value in (('parent',object()),('active',True),('attempts',1),('jobs',1),
            ('owner',object()),('job',object()),('bindings',[object()]),('restorations',1),('frame_checks',1)):
            f=self.preparation_fixture();setattr(f.context,name,value)
            with self.assertRaises(ValueError):f.selected.idle(f.result)
            self.assertEqual(f.guards,[])

    def test_preparation_projection_rejects_injected_readiness_or_wrong_strict_function(self):
        f=self.preparation_fixture()
        context=f.context
        def injected():return context
        for fn in (injected,lambda:None):
            f.result.assembled.built.window.WINDOW_LINK.connect_engine=fn
            with self.assertRaisesRegex(ValueError,'UNCHANGED_UNINJECTED_STRICT_WINDOW'):f.selected.idle(f.result)

    def test_preparation_projection_preserves_pressure_latch_and_unconditional_cleanup(self):
        f=self.preparation_fixture();e=f.epochs;e.advance('construction');e.bind(f.result)
        f.guards[0].fail=True
        with self.assertRaisesRegex(ValueError,'STOP_TEST_PRESSURE'):e.advance('opening_and_metadata')
        f.guards[0].fail=False
        with self.assertRaises(ValueError):e.advance('opening_and_metadata')
        self.assertEqual(len(f.guards),1);e.close();self.assertTrue(f.guards[0].cleanup)
        self.assertTrue(e.broken)

    def test_preparation_private_dependency_tamper_blocks_rotation_without_new_guard(self):
        f=self.preparation_fixture();e=f.epochs;e.advance('construction');e.bind(f.result)
        f.selected.idle.__globals__['readiness_context']=lambda result:f.context
        with self.assertRaisesRegex(ValueError,'SEALED_ORIGINAL_PREPARATION'):e.advance('opening_and_metadata')
        self.assertTrue(e.broken);self.assertEqual(len(f.guards),1)
        e.close();self.assertTrue(f.guards[0].cleanup)

    def test_preparation_wrong_owner_or_skipped_stage_preserves_original_denial(self):
        for mode in ('owner','stage'):
            f=self.preparation_fixture();e=f.epochs;e.advance('construction');e.bind(f.result)
            if mode=='owner':f.owner[0]=(9,9)
            with self.assertRaises(ValueError):e.advance('closing' if mode=='stage' else 'opening_and_metadata')
            self.assertEqual(len(f.guards),1);self.assertTrue(e.broken);e.close()

    def test_preparation_raw_or_epoch_code_drift_is_rejected_before_new_guard(self):
        f=self.preparation_fixture()
        with self.assertRaisesRegex(ValueError,'EXACT_WHOLE_ORIGINAL_SOURCE'):
            m.preparation(f.raw+b' ',metadata_original,f.context)
        with patch.object(metadata_original.ReadOnlyEpochs,'advance',lambda self,stage:None):
            with self.assertRaisesRegex(ValueError,'ALL_ORIGINAL_PREPARATION_EPOCH_METHOD_BODIES'):
                m.preparation(f.raw,metadata_original,f.context)
        self.assertEqual(f.guards,[])

    def controller_fixture(self,*,bind=True):
        f=self.preparation_fixture();root=Path(__file__).resolve().parents[3]
        f.raws={pin['path']:(root/pin['path']).read_bytes() for pin in m.CONTROLLERS}
        f.libraries=NS(batch_zlib_metadata=metadata_original,batch_native_checkpoint=native_checkpoint,
            batch_post_job_checkpoint=batch_post_job_checkpoint,preparation_checkpoint_owner=preparation_checkpoint_owner,
            batch_post_native=batch_post_native,batch_pre_go_runtime=batch_pre_go_runtime)
        def factory(role):
            guard=preparation_fixture.Guard(role);f.guards.append(guard);return guard
        f.factory=factory
        f.pipeline=m.controllers(f.raws,f.libraries,factory,
            lambda actual,expected,label:self.assertEqual(actual,expected),identity=lambda:f.owner[0])
        f.callback_calls=[]
        def callback(reader):f.callback_calls.append(reader);return ('model-only',[])
        f.original_callback=callback
        def engine_body():pass
        f.engine=FunctionType(engine_body.__code__,dict(engine_body.__globals__,binding=callback))
        f.result.assembled.built.engine=NS(run_owned=f.engine)
        f.result.assembled.checker=NS(validate_candidate=lambda *args:('model-only',None))
        f.result.attached=NS(callback=callback)
        f.batch.checkpoint=f.pipeline.checkpoint
        f.reader=NS(checkpoint=f.pipeline.checkpoint)
        if bind:
            f.pipeline.epochs.advance('construction');f.pipeline.bind_reader(f.reader)
            f.pipeline.bind_parent(f.result,f.context)
        return f

    def test_controller_pipeline_is_created_before_guard_and_stable_reader_capture(self):
        f=self.controller_fixture(bind=False);p=f.pipeline
        self.assertEqual(f.guards,[]);self.assertIs(p.checkpoint,p.route.checkpoint)
        self.assertIs(p.owner.original.__closure__[0].cell_contents,p.relay)
        p.epochs.advance('construction');p.bind_reader(f.reader);p.bind_parent(f.result,f.context)
        self.assertIs(p.owner.reader,f.reader);self.assertIs(p.route.context,f.context)
        self.assertIs(p.route.result,f.result);self.assertIs(p.relay.preparation,p.epochs)
        self.assertEqual(len(f.guards),1);self.assertIs(p.epochs.guard,f.guards[0]);p.close()
        self.assertTrue(p.cleanup())

    def test_controller_pipeline_retains_original_native_and_postnative_bodies(self):
        f=self.controller_fixture();p=f.pipeline
        self.assertIs(type(p.relay).__mro__[1],native_checkpoint.Handoff)
        for name in ('bind','arm','finish_native'):
            self.assertIs(getattr(type(p.relay),name).__code__,getattr(native_checkpoint.Handoff,name).__code__)
        original_post_job=batch_post_job_checkpoint.handoff_type(native_checkpoint.Handoff,
            f.raws[m.CONTROLLERS[7]['path']])
        for name in ('admit_metadata','check','_post_job','evidence'):
            self.assertIs(getattr(type(p.relay),name).__code__,getattr(original_post_job,name).__code__)
        self.assertIs(type(p.owner),preparation_checkpoint_owner.Checkpoint)
        self.assertIs(type(p.route),batch_post_native.Closing)
        self.assertIs(p.route.original_checkpoint,p.owner.checkpoint)
        self.assertEqual(p.relay.post_job_bindings,0);self.assertEqual(p.route.guard_creations,0)
        p.close();self.assertTrue(p.cleanup())

    def test_original_metadata_callback_admits_original_reader_before_callback(self):
        f=self.controller_fixture();p=f.pipeline
        callback=f.engine.__globals__['binding']
        self.assertIsNot(callback,f.original_callback)
        with self.assertRaisesRegex(ValueError,'ONE_ACTUAL_ORIGINAL_METADATA_BINDING'):callback(object())
        self.assertEqual(f.callback_calls,[]);self.assertTrue(p.relay.broken)
        p.close();self.assertIs(f.engine.__globals__['binding'],f.original_callback)
        self.assertTrue(p.cleanup())

    def test_controller_callback_restoration_and_guard_close_are_unconditional_and_once(self):
        f=self.controller_fixture();p=f.pipeline
        p.checkpoint(force=True);before=f.guards[0].checked
        p.close();p.close()
        self.assertTrue(f.guards[0].cleanup);self.assertEqual(f.guards[0].checked,before)
        self.assertIs(f.engine.__globals__['binding'],f.original_callback)
        self.assertEqual(len(p.epochs.records),1);self.assertTrue(p.cleanup())
        self.assertEqual(p.evidence()['cleanup_error_types'],[])

    def test_controller_pressure_failure_latches_all_original_checkpoints_but_allows_cleanup(self):
        f=self.controller_fixture();p=f.pipeline;f.guards[0].fail=True
        with self.assertRaisesRegex(ValueError,'STOP_TEST_PRESSURE'):p.checkpoint()
        f.guards[0].fail=False
        with self.assertRaises(ValueError):p.checkpoint()
        self.assertTrue(p.relay.broken);self.assertTrue(p.owner.failed);self.assertTrue(p.epochs.broken)
        p.close();self.assertTrue(p.cleanup());self.assertEqual(len(f.guards),1)

    def test_controller_duplicate_parent_or_reader_binding_latches_and_never_adds_guard(self):
        for mode in ('reader','parent'):
            f=self.controller_fixture();p=f.pipeline
            with self.assertRaises(ValueError):
                p.bind_reader(f.reader) if mode=='reader' else p.bind_parent(f.result,f.context)
            self.assertTrue(p.relay.broken);self.assertTrue(p.epochs.broken)
            with self.assertRaises(ValueError):p.checkpoint()
            self.assertEqual(len(f.guards),1);p.close();self.assertTrue(p.cleanup())

    def test_controller_rejects_wrong_reader_checkpoint_before_parent_binding(self):
        f=self.controller_fixture(bind=False);p=f.pipeline;p.epochs.advance('construction')
        with self.assertRaisesRegex(ValueError,'STABLE_CHECKPOINT'):p.bind_reader(NS(checkpoint=lambda:None))
        self.assertTrue(p.relay.broken);self.assertIsNone(p.owner.reader)
        self.assertFalse(p.state.parent_bound);p.close();self.assertTrue(p.cleanup())

    def test_controller_cannot_start_closing_or_claim_frame_without_original_native(self):
        f=self.controller_fixture();p=f.pipeline
        with self.assertRaisesRegex(ValueError,'SUCCESSFUL_ORIGINAL_HANDOFF_TERMINAL'):p.route.start_closing()
        self.assertEqual(p.route.guard_creations,0);self.assertEqual(p.route.oracle_attempts,0)
        self.assertEqual(f.batch.parent_connection.state.frames,[]);p.close();self.assertTrue(p.cleanup())

    def test_controller_cleanup_failure_is_recorded_without_preventing_guard_release(self):
        f=self.controller_fixture();p=f.pipeline
        f.engine.__globals__['binding']=lambda reader:None
        p.close();self.assertTrue(f.guards[0].cleanup);self.assertFalse(p.cleanup())
        self.assertEqual(p.evidence()['cleanup_error_types'],['ValueError'])
        p.close();self.assertEqual(p.evidence()['cleanup_error_types'],['ValueError'])

    def test_controller_rejects_source_or_original_method_drift_before_guard_creation(self):
        f=self.controller_fixture(bind=False);wrong=dict(f.raws)
        wrong[m.CONTROLLERS[1]['path']]+=b' '
        with self.assertRaisesRegex(ValueError,'EXACT_WHOLE_ORIGINAL_SOURCE'):
            m.controllers(wrong,f.libraries,f.factory,lambda *args:None)
        with patch.object(batch_post_native.Closing,'start_closing',lambda self:None):
            with self.assertRaisesRegex(ValueError,'ENTIRE_ORIGINAL_CONTROLLER_FUNCTION_AND_CLASS_METHODS'):
                m.controllers(f.raws,f.libraries,f.factory,lambda *args:None)
        self.assertEqual(f.guards,[])

    def test_preparation_context_can_bind_once_without_adopting_or_starting_guard(self):
        f=self.preparation_fixture()
        selected=m.preparation(f.raw,metadata_original)
        with self.assertRaisesRegex(ValueError,'ACTUAL_NEW_PARENT_CONTEXT'):selected.idle(f.result)
        selected.bind_context(f.context);self.assertIs(selected.idle(f.result),f.context)
        with self.assertRaisesRegex(ValueError,'ONE_ACTUAL_PREPARATION_CONTEXT_BINDING'):selected.bind_context(f.context)
        self.assertEqual(f.guards,[])

    def test_private_namespace_controller_code_matches_real_construction_loader(self):
        f=self.controller_fixture(bind=False);root=Path(__file__).resolve().parents[3]
        libraries,_=namespace_loader.load(root,list(m.CONTROLLERS[:6]),{})
        names=('batch_zlib_metadata','batch_native_checkpoint','batch_post_job_checkpoint',
            'preparation_checkpoint_owner','batch_post_native','batch_pre_go_runtime')
        import ast
        observed_defaults_differ=False
        for name,pin in zip(names,m.CONTROLLERS):
            default=getattr(f.libraries,name);private=getattr(libraries,name)
            tree=ast.parse(f.raws[pin['path']])
            nodes=[node for node in tree.body if not isinstance(node,(ast.Import,ast.ImportFrom))]
            expected=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),pin['path'],'exec')
            for member in vars(private):
                selected=getattr(private,member);original=getattr(default,member,None)
                if type(selected) is FunctionType and type(original) is FunctionType:
                    self.assertEqual(m.shape(selected.__code__),m.shape(m.nested(expected,member)))
                    observed_defaults_differ |= m.shape(selected.__code__)!=m.shape(original.__code__)
        self.assertTrue(observed_defaults_differ)
        p=m.controllers(f.raws,libraries,f.factory,lambda *args:None,identity=lambda:f.owner[0])
        self.assertEqual(p.evidence()['whole_original_controller_compile_forms'][m.CONTROLLERS[2]['path']],
            'pinned_namespace_loader_all_non_import_AST')
        p.epochs.advance('construction');p.close();self.assertTrue(p.cleanup())

    def coordinator_fixture(self,*,authority=True,route_callback=m.coordinator_checkpoint,bind=True):
        # The complete original entry/Once/installed parent execute are real;
        # guards, IO, terminal Frame and controller data here are synthetic.
        f=self.fixture(authority=authority);f.resource_checks=[];f.terminal_checks=[]
        f.epochs.closed=False;f.epochs.broken=False;f.epochs.guard=object()
        f.epochs.records=[dict(stage='construction',cleanup_confirmed=True)]
        f.relay.phase='PREPARATION';f.relay.broken=False;f.relay.bindings=0
        f.route.result=f.context.result;f.route.phase='ORIGINAL';f.route.broken=False
        f.route.guard=None;f.route.cleanup=None;f.route.guard_creations=f.route.oracle_attempts=0
        f.route.closing_reader=None;f.batch.active=None;f.batch.metadata_reader_active=False
        def checkpoint():
            self.assertFalse(f.epochs.closed);self.assertEqual(f.relay.phase,'PREPARATION')
            f.resource_checks.append('original-preparation-model')
        f.route.checkpoint=f.batch.checkpoint=checkpoint
        before_begin=f.batch.begin
        def begin(reader):before_begin(reader);f.batch.phase='READY'
        f.batch.begin=begin
        def close():
            f.events.append('preparation_closed');f.epochs.closed=True;f.epochs.guard=None
            f.epochs.records.append(dict(stage='opening_and_metadata',cleanup_confirmed=True))
        f.epochs.close=close
        before_arm=f.relay.arm;before_finish=f.relay.finish_native
        def arm():before_arm();f.relay.phase='WAIT_ORIGINAL_NATIVE'
        def finish(context):before_finish(context);f.relay.phase='NATIVE_TERMINAL'
        f.relay.arm=arm;f.relay.finish_native=finish
        before_start=f.route.start_closing;before_closing=f.route.finish_whole;before_verify=f.route.verify
        def start():before_start();f.route.guard_creations=1;f.route.phase='CLOSING'
        def closing(reader):
            value=before_closing(reader);f.route.closing_reader=reader
            f.batch.phase='SOURCE_BOUNDARIES_COMPLETE_NOT_ACCEPTED';f.route.phase='ORACLE';return value
        def verify(*args,**kwargs):
            value=before_verify(*args,**kwargs);f.route.oracle_attempts=1
            f.route.phase='CHECKED_NOT_ACCEPTED';f.route.cleanup=True;return value
        def terminal():
            f.terminal_checks.append('original-terminal-model')
            self.assertEqual(f.route.context.restorations,1)
            self.assertFalse(f.route.context.active)
            return f.batch,NS(state='COMMITTED',model_only=True)
        def checker():f.terminal_checks.append('original-checker-model');return f.context.result.assembled.checker
        f.route.start_closing=start;f.route.finish_whole=closing;f.route.verify=verify
        f.route._terminal=terminal;f.route._checker=checker
        def idle(result):
            self.assertIs(result,f.context.result);self.assertEqual(f.route.context.attempts,0)
            self.assertEqual(f.route.context.jobs,0);self.assertEqual(f.batch.parent_connection.state.frames,[])
            return f.route.context
        f.pipeline=NS(route=f.route,relay=f.relay,epochs=f.epochs,checkpoint=checkpoint,
            state=NS(parent_bound=True,closed=False,coordinator_bound=False),preparation=NS(idle=idle))
        f.driver=NS(lifecycle_controllers=f.pipeline,lifecycle_procedure=f.compiled,
            lifecycle_context=f.context,coordinator_boundary=None)
        root=Path(__file__).resolve().parents[3];f.once_raw=(root/m.ONCE['path']).read_bytes()
        code=m.nested(m.nested(compile(f.once_raw,m.ONCE['path'],'exec'),'construct_entry'),'checkpoint')
        values=dict(box=[f.driver],checkpoint_route=route_callback,once=f.once)
        def cell(value):return (lambda:value).__closure__[0]
        f.once.checkpoint=FunctionType(code,once_api.Once._checked.__globals__,
            closure=tuple(cell(values[name]) for name in code.co_freevars))
        if bind:
            f.driver.coordinator_boundary=m.bind_coordinator(f.once_raw,f.once,f.driver,f.pipeline,f.compiled)
        return f

    def test_coordinator_original_whole_entry_uses_two_pure_transitions_not_closed_guards_model_only(self):
        f=self.coordinator_fixture();value=f.run();e=f.driver.coordinator_boundary.evidence()
        self.assertEqual(len(f.resource_checks),3)
        self.assertEqual(e['original_preparation_checks_delegated'],3)
        self.assertEqual(e['original_pre_Native_lifecycle_checks'],1)
        self.assertEqual(e['original_terminal_lifecycle_checks'],1)
        self.assertEqual(f.terminal_checks,['original-terminal-model','original-checker-model'])
        self.assertFalse(e['failed']);self.assertFalse(e['actual_Native_transition_qualified'])
        self.assertEqual(f.once.phase,'RETURNED_NOT_ACCEPTED')
        self.assertEqual(value['canonical_receipt_pin']['path'],m.CANONICAL)

    def test_coordinator_absent_or_false_authority_still_blocks_before_intent_and_native(self):
        for authority in (None,False):
            f=self.coordinator_fixture(authority=authority)
            with self.assertRaisesRegex(ValueError,'EXTERNAL_EXECUTION_AUTHORITY_REQUIRED'):f.run()
            self.assertEqual(f.claims,{});self.assertNotIn('original_native',f.events)
            self.assertEqual(f.driver.coordinator_boundary.state.pre_native,0)

    def test_coordinator_direct_bridge_or_direct_callback_cannot_create_transition_authority(self):
        for mode in ('bridge','callback'):
            f=self.coordinator_fixture()
            with self.assertRaises(ValueError):
                f.once.checkpoint() if mode=='bridge' else m.coordinator_checkpoint(f.driver,f.once)
            self.assertTrue(f.driver.coordinator_boundary.state.failed)
            self.assertEqual(f.claims,{});self.assertEqual(f.route.context.jobs,0)

    def test_coordinator_wait_rejects_unclosed_preparation_or_missing_cleanup_before_native(self):
        for mode in ('closed','guard','records','cleanup'):
            f=self.coordinator_fixture();before=f.policy.arm
            def bad(context):
                before(context)
                if mode=='closed':f.epochs.closed=False
                elif mode=='guard':f.epochs.guard=object()
                elif mode=='records':f.epochs.records=[]
                else:f.epochs.records[-1]['cleanup_confirmed']=False
            f.policy.arm=bad
            with self.assertRaisesRegex(ValueError,'CLOSED_PREPARATION_BEFORE_UNSTARTED'):f.run()
            self.assertTrue(f.driver.coordinator_boundary.state.failed)
            self.assertNotIn('original_native',f.events);self.assertEqual(f.route.context.jobs,0)

    def test_coordinator_wait_rejects_wrong_parent_owner_or_prior_execution(self):
        f=self.coordinator_fixture();before=f.policy.arm
        def changed(context):before(context);f.route.context.jobs=1
        f.policy.arm=changed
        with self.assertRaises(AssertionError):f.run()  # Synthetic original idle rejects the counter.
        self.assertTrue(f.once.failed);self.assertTrue(f.driver.coordinator_boundary.state.failed)
        self.assertNotIn('original_native',f.events)

    def test_coordinator_terminal_requires_original_closed_oracle_counters_and_cleanup(self):
        for mode in ('phase','cleanup','oracle','guard'):
            f=self.coordinator_fixture();before=f.route.verify
            def wrong(*args,**kwargs):
                value=before(*args,**kwargs)
                if mode=='phase':f.route.phase='CLOSING'
                elif mode=='cleanup':f.route.cleanup=False
                elif mode=='oracle':f.route.oracle_attempts=0
                else:f.route.guard=object()
                return value
            f.route.verify=wrong
            with self.assertRaisesRegex(ValueError,'ONLY_COMPLETED_ORIGINAL_ENTRY'):f.run()
            self.assertIn(once_api.CLAIM,f.claims);self.assertTrue(f.once.failed)
            self.assertEqual(f.driver.coordinator_boundary.state.terminal,0)

    def test_coordinator_primary_entry_error_keeps_claim_and_no_terminal_transition_or_retry(self):
        f=self.coordinator_fixture();primary=ValueError('MODEL_PRIMARY_ORIGINAL_FAILURE');f.native_error=primary
        with self.assertRaises(ValueError) as caught:f.run()
        self.assertIs(caught.exception,primary);self.assertIn(once_api.CLAIM,f.claims)
        self.assertEqual(f.driver.coordinator_boundary.state.terminal,0)
        with self.assertRaisesRegex(ValueError,'ONE_LIFECYCLE_INVOCATION_NO_RETRY'):f.run()

    def test_coordinator_replaced_original_terminal_method_or_once_code_fails_seal(self):
        f=self.coordinator_fixture();f.route._terminal=lambda:(f.batch,NS(state='COMMITTED'))
        with self.assertRaisesRegex(ValueError,'UNCHANGED_ORIGINAL_ONCE_PARENT'):f.run()
        self.assertEqual(f.claims,{})
        g=self.coordinator_fixture()
        with patch.object(once_api.Once,'authorize_native',lambda self:True):
            with self.assertRaisesRegex(ValueError,'UNCHANGED_ORIGINAL_ONCE_PARENT'):g.driver.coordinator_boundary.seal()
        self.assertEqual(g.claims,{})

    def test_coordinator_rejects_undeclared_bridge_callback_and_raw_drift_before_binding(self):
        f=self.coordinator_fixture(route_callback=lambda *args:None,bind=False)
        with self.assertRaisesRegex(ValueError,'EXPLICIT_ORIGINAL_BRIDGE'):
            m.bind_coordinator(f.once_raw,f.once,f.driver,f.pipeline,f.compiled)
        g=self.coordinator_fixture(bind=False)
        with self.assertRaisesRegex(ValueError,'EXACT_WHOLE_ORIGINAL_SOURCE'):
            m.bind_coordinator(g.once_raw+b' ',g.once,g.driver,g.pipeline,g.compiled)
        self.assertFalse(g.pipeline.state.coordinator_bound)

    def test_coordinator_bound_once_and_bridge_cell_change_is_detected(self):
        f=self.coordinator_fixture()
        with self.assertRaisesRegex(ValueError,'ONE_UNUSED_ACTUAL_CONTROLLER'):
            m.bind_coordinator(f.once_raw,f.once,f.driver,f.pipeline,f.compiled)
        values=dict(zip(f.once.checkpoint.__code__.co_freevars,f.once.checkpoint.__closure__))
        values['once'].cell_contents=object()
        with self.assertRaisesRegex(ValueError,'UNCHANGED_ORIGINAL_ONCE_PARENT'):f.driver.coordinator_boundary.seal()

    def test_coordinator_drops_entry_and_returned_result_references_after_success_or_error(self):
        for fail in (False,True):
            f=self.coordinator_fixture()
            if fail:f.oracle_error=ValueError('MODEL_ORACLE_FAILURE')
            if fail:
                with self.assertRaises(ValueError):f.run()
            else:f.run()
            self.assertIsNone(f.compiled.state.active_entry);self.assertIsNone(f.compiled.state.returned_result)

    def test_original_terminal_and_checker_inspection_after_close_has_no_guard_or_fresh_io(self):
        f=post_native_fixture.closed(post_native_fixture.committed(post_native_fixture.fixture()))
        post_native_fixture.verify(f)
        self.assertEqual(f.route.phase,'CHECKED_NOT_ACCEPTED');self.assertIsNone(f.route.guard)
        sources=len(f.source_calls);checks=f.guards[0].checks
        batch,frame=f.route._terminal();f.route._checker()
        self.assertIs(batch,f.batch);self.assertIs(frame,f.frame)
        self.assertEqual(len(f.source_calls),sources);self.assertEqual(f.guards[0].checks,checks)

    def process_fixture(self,*,authority=True,private_transfer=False):
        root=Path(__file__).resolve().parents[3]
        raw=(root/m.PROCESS_AUDIT['path']).read_bytes()
        selected=m.product_audit_type((root/m.PROCESS_CONNECTION['path']).read_bytes(),process_connection)
        once=once_api.Once(lambda:None,authorize=None if authority is None else lambda:authority)
        f=parent_fixture.Tests().fixture(authorize=once.authorize_native)
        if private_transfer:
            libraries,_=namespace_loader.load(root,[m.PROCESS_TRANSFER],{})
            f.api.transfer=libraries.native011_product_source_handoff
        registered=[];denied=[];fault=NS(event=None,guard=False,postspawn_guard=False)
        prior_check=f.frame.check
        def check():
            f.owner.parent_connection.state.attempts=1  # Synthetic Batch counter, not execution evidence.
            if fault.guard:raise ValueError('MODEL_PRODUCT_AUDIT_NATIVE_GUARD_STOP')
            prior_check()
        f.frame.check=check
        def factory(command,**options):
            self.assertEqual(options.pop('executable'),m.sys.executable)
            values=(m.sys.executable,subprocess.list2cmdline(command),str(f.f.handoff.root),None)
            if fault.event=='cwd':values=(*values[:2],'other-root',None)
            elif fault.event=='executable':values=('other.exe',*values[1:])
            elif fault.event=='environment':values=(*values[:3],{})
            elif fault.event=='repeat':registered[0]('subprocess.Popen',values)
            elif fault.event=='guard':fault.guard=True
            registered[0]('subprocess.Popen',values)
            value=f.f.factory(command,**options)
            if fault.postspawn_guard:f.fault.guard=True
            return value
        f.sp.Popen=factory;link=f.install()
        audit=selected(f.f.handoff.root,raw,registered.append,factory=factory)
        code=m.nested(m.nested(compile(raw,m.PROCESS_AUDIT['path'],'exec'),'main'),'deny')
        def cell(value):return (lambda:value).__closure__[0]
        deny=FunctionType(code,{},closure=(cell(denied),));audit.register(deny)
        driver=NS(parent_handoff=link,lifecycle_controllers=NS(route=NS(context=link.context)),
            lifecycle_procedure=NS(state=NS(entry_calls=0)),
            coordinator_boundary=NS(seal=lambda:None,state=NS(pre_native=0,failed=False)))
        driver.lifecycle_controllers.relay=NS(phase='WAIT_ORIGINAL_NATIVE')
        original_transfer=link.handoff.api.transfer
        audit.bind_parent(driver,once,(root/m.PROCESS_TRANSFER['path']).read_bytes())
        claims=[]
        def write(row):claims.append(row);return dict(path=once_api.CLAIM,bytes=300,sha256='a'*64)
        def entry():
            driver.lifecycle_procedure.state.entry_calls=1;f.owner.phase='READY'
            audit.policy.arm(link.context);driver.coordinator_boundary.state.pre_native=1
            return f.actual.run_owned(1)
        f.audit=audit;f.once=once;f.registered=registered;f.denied=denied;f.audit_fault=fault;f.link=link
        f.driver=driver;f.original_transfer=original_transfer;f.original_deny=deny;f.claims=claims
        f.run=lambda:once.execute(entry,write)
        return f

    def test_product_process_audit_binds_privately_without_native_or_global_module_change(self):
        f=self.process_fixture(authority=None)
        try:
            self.assertEqual(f.journal,[]);self.assertEqual(f.f.created,[])
            self.assertIsNot(f.link.handoff.api.transfer,f.original_transfer)
            self.assertIs(f.original_transfer.connect,process_connection.sys.modules['native011_product_source_handoff'].connect)
            self.assertEqual(f.audit.registrations,1);self.assertEqual(f.audit.factory_attempts,0)
            self.assertFalse(f.audit.evidence()['actual_Native_or_product_process_qualified'])
        finally:f.audit.restore();f.pipe.close()
        self.assertTrue(f.audit.restored);self.assertIs(f.link.handoff.api.transfer,f.original_transfer)

    def test_product_process_audit_exact_original_parent_source_handoff_and_one_audit_event_model_only(self):
        f=self.process_fixture()
        try:
            self.assertEqual(f.run(),17)
            self.assertEqual(f.audit.connections,1);self.assertEqual(f.audit.factory_attempts,1)
            self.assertEqual(f.audit.allowed,1);self.assertEqual(f.denied,[])
            self.assertEqual(len(f.f.created),1);self.assertEqual(len(f.f.created[0][1]['startupinfo'].lpAttributeList['handle_list']),204)
            self.assertEqual(set(f.f.flags.values()),{0});self.assertIsNone(f.audit.command)
            self.assertIsNone(f.audit.actual_scope);self.assertEqual(f.link.context.jobs,1)
            self.assertEqual(f.link.context.restorations,1);self.assertTrue(f.link.state.cleanup_confirmed)
            self.assertEqual(f.link.context.bindings[0].gates[0].seconds,15)
            self.assertEqual(f.strict_state.states[0].diagnostics()['maximum_GO_to_complete_capture_seconds'],10)
        finally:f.audit.restore();f.pipe.close()

    def test_product_process_audit_absent_or_false_authority_never_reaches_job_or_factory(self):
        for authority in (None,False):
            f=self.process_fixture(authority=authority)
            try:
                with self.assertRaisesRegex(ValueError,'EXTERNAL_EXECUTION_AUTHORITY_REQUIRED'):f.run()
                self.assertEqual(f.claims,[]);self.assertEqual(f.f.created,[])
                self.assertEqual(f.audit.factory_attempts,0);self.assertEqual(f.link.context.jobs,0)
            finally:f.audit.restore();f.pipe.close()

    def test_product_process_audit_other_process_events_keep_original_deny_body(self):
        f=self.process_fixture()
        try:
            for event,args in (('subprocess.Popen',(m.sys.executable,'command',str(f.f.handoff.root),None)),
                ('os.system',('command',)),('os.startfile',('file',)),('os.exec',()),('os.posix_spawn',()),('os.fork',())):
                with self.assertRaisesRegex(ValueError,'CURRENT805_SHARED_NO_PROCESS'):f.registered[0](event,args)
            self.assertEqual(len(f.denied),6);self.assertEqual(f.audit.allowed,0)
            self.assertEqual(f.f.created,[])
        finally:f.audit.restore();f.pipe.close()

    def test_product_process_audit_wrong_executable_cwd_environment_or_repeated_event_denied(self):
        for event in ('executable','cwd','environment','repeat'):
            f=self.process_fixture();f.audit_fault.event=event
            try:
                with self.assertRaisesRegex(ValueError,'CURRENT805_SHARED_NO_PROCESS'):f.run()
                self.assertTrue(f.audit.failed);self.assertEqual(f.f.created,[])
                self.assertIsNone(f.audit.command);self.assertIsNone(f.audit.actual_scope)
                self.assertEqual(set(f.f.flags.values()),{0});self.assertEqual(f.link.context.restorations,1)
                self.assertTrue(f.link.state.cleanup_confirmed)
            finally:f.audit.restore();f.pipe.close()

    def test_product_process_audit_original_native_guard_error_preserves_cleanup_without_retry(self):
        f=self.process_fixture();f.audit_fault.event='guard'
        try:
            with self.assertRaisesRegex(ValueError,'MODEL_PRODUCT_AUDIT_NATIVE_GUARD_STOP'):f.run()
            self.assertEqual(f.audit.allowed,0);self.assertTrue(f.audit.failed)
            self.assertEqual(f.f.created,[]);self.assertEqual(set(f.f.flags.values()),{0})
            self.assertTrue(f.link.state.cleanup_confirmed);self.assertEqual(f.denied,[])
            with self.assertRaisesRegex(ValueError,'ONE_INVOCATION_NO_RETRY'):f.run()
        finally:f.audit.restore();f.pipe.close()

    def test_product_process_audit_never_loses_successfully_created_child_on_later_guard_error(self):
        f=self.process_fixture();f.audit_fault.postspawn_guard=True
        try:
            with self.assertRaisesRegex(ValueError,'MODEL_GUARD_STOP'):f.run()
            self.assertIs(f.link.handoff.actual.process,f.f.process)
            self.assertEqual(len(f.f.created),1);self.assertEqual(f.audit.allowed,1)
            self.assertEqual(set(f.f.flags.values()),{0});self.assertTrue(f.link.state.cleanup_confirmed)
        finally:f.audit.restore();f.pipe.close()

    def test_product_process_audit_uses_captured_factory_not_temporarily_wrapped_global_popen(self):
        f=self.process_fixture()
        try:
            with patch.object(m.subprocess,'Popen',side_effect=AssertionError('NO_GLOBAL_RECURSION')):
                self.assertEqual(f.run(),17)
            self.assertEqual(len(f.f.created),1);self.assertEqual(f.audit.allowed,1)
        finally:f.audit.restore();f.pipe.close()

    def test_product_process_audit_direct_factory_before_actual_source_spawn_cannot_create_process(self):
        f=self.process_fixture()
        try:
            with self.assertRaisesRegex(ValueError,'ORIGINAL_CLAIMED_NATIVE_OWNER_JOB'):
                f.audit.create([],shell=True)
            self.assertTrue(f.audit.failed);self.assertEqual(f.audit.factory_attempts,1)
            self.assertEqual(f.f.created,[]);self.assertEqual(f.audit.allowed,0)
        finally:f.audit.restore();f.pipe.close()

    def test_product_process_audit_original_registration_and_unrelated_hooks_are_preserved(self):
        f=self.process_fixture()
        try:
            other=lambda *args:None;f.audit.register(other);self.assertIs(f.registered[-1],other)
            with self.assertRaisesRegex(ValueError,'ONE_ORIGINAL_AUDIT_REGISTRATION'):f.audit.register(f.original_deny)
            self.assertEqual(f.audit.registrations,1)
        finally:f.audit.restore();f.pipe.close()

    def test_product_process_audit_restoration_is_idempotent_and_other_threads_cannot_launch(self):
        f=self.process_fixture()
        try:
            with patch.object(m.threading,'get_ident',return_value=f.audit.thread+1):
                with self.assertRaisesRegex(ValueError,'SAME_PRODUCT_AUDIT_OWNER'):f.audit.create([])
            self.assertEqual(f.f.created,[]);f.audit.restore();f.audit.restore()
            self.assertTrue(f.audit.restored);self.assertEqual(f.audit.restore_errors,[])
            with self.assertRaisesRegex(ValueError,'CURRENT805_SHARED_NO_PROCESS'):
                f.registered[0]('subprocess.Popen',(m.sys.executable,'command',str(f.f.handoff.root),None))
        finally:f.audit.restore();f.pipe.close()

    def test_product_process_audit_detects_raw_source_or_private_dependency_drift(self):
        root=Path(__file__).resolve().parents[3]
        with self.assertRaisesRegex(ValueError,'EXACT_WHOLE_ORIGINAL_SOURCE'):
            m.product_audit_type((root/m.PROCESS_CONNECTION['path']).read_bytes()+b' ',process_connection)
        f=self.process_fixture()
        try:
            f.link.handoff.api.transfer=NS(**vars(f.original_transfer))
            with self.assertRaisesRegex(ValueError,'UNCHANGED_PRIVATE_PRODUCT_FACTORY'):f.audit.seal()
            f.link.handoff.api.transfer=f.audit.adapter
        finally:f.audit.restore();f.pipe.close()

    def test_product_control_declaration_keeps_existing_common_self_role_without_duplicate(self):
        root=Path(__file__).resolve().parents[3];bound=[]
        class Base:
            def __init__(self):pass
            def bind(self,*args):pass
        names=tuple('model-existing-'+str(i) for i in range(74))
        control=NS(admit=lambda *args,**kwargs:NS(control_names=names))
        driver=m.driver_type(Base,object())()
        driver.bind(root,None,None,None,NS(load=lambda *args:(NS(),[])),control)
        checkpoint=lambda:None
        driver.lifecycle_controllers=NS(checkpoint=checkpoint,bind_reader=lambda reader:bound.append(reader))
        reader=NS(checkpoint=checkpoint);declared=control.admit(reader,None,None)
        self.assertEqual(bound,[reader]);self.assertEqual(len(declared.control_names),len(set(declared.control_names)))
        self.assertNotIn(m.PROCESS_AUDIT['path'],declared.control_names)
        for name in (m.SELF,m.TEST,m.PROCESS_CONNECTION['path'],m.PROCESS_TRANSFER['path'],*m.DISPATCH):
            self.assertIn(name,declared.control_names)
        with self.assertRaisesRegex(ValueError,'ONE_EXPLICIT_LIFECYCLE_DECLARATION'):control.admit(reader,None,None)

    def test_product_process_audit_actual_private_loader_handoff_retains_all_methods_and_one_factory(self):
        f=self.process_fixture(private_transfer=True)
        try:
            self.assertEqual(f.audit.transfer_compile_form,'pinned_namespace_loader_all_non_import_AST')
            self.assertEqual(f.run(),17);self.assertEqual(f.audit.allowed,1)
            self.assertEqual(len(f.f.created),1);self.assertTrue(f.link.state.cleanup_confirmed)
            self.assertEqual(set(f.f.flags.values()),{0})
        finally:f.audit.restore();f.pipe.close()

    def oracle_fixture(self,*,bind=True):
        f=self.fixture();root=Path(__file__).resolve().parents[3]
        row=json.loads((root/m.ORACLE_STEP['path']).read_text(encoding='utf-8'))
        step=NS(**row,path=m.ORACLE_STEP['path'],pin=dict(m.ORACLE_STEP))
        f.context.connected.core['step']=row
        f.source.linked.window.M.base.CONFIG=step
        def generator(config):
            return NS(INDEX=config.index,BEFORE=config.before,CASE=config.case,PRIOR_ACCEPT_PIN=config.prior_queue_pin,
                arguments=lambda:[config.case,'--exact','--test-threads=1','--format=pretty','--color=never'])
        def candidate(*args):raise AssertionError('MODEL_NO_CANDIDATE_VALIDATION_DURING_BINDING')
        checker=f.context.result.assembled.checker;checker.environment['context']=generator;checker.validate_candidate=candidate
        f.route.result=f.context.result;f.route.phase='ORIGINAL';f.route._checker=lambda:checker.validate_candidate
        f.prepared=NS(linked=f.source.linked,entry=NS(core=f.context.connected.core))
        f.bound=NS(connected=f.context.connected,attached=NS());f.context.result.attached=f.bound.attached
        known={pin['path']:dict(pin) for pin in (*m.ORACLE_REFERENCES,m.ORACLE_STEP)}
        f.checked=NS(checker=checker,known=known);f.pipeline=NS(route=f.route)
        names=['model-other-case-'+str(i) for i in range(249)];names[164]=row['case']
        records={m.ORACLE_STEP['path']:row,m.ORACLE_REFERENCES[0]['path']:{'source_test_names':names},
            m.ORACLE_REFERENCES[1]['path']:{'model-body':True},m.ORACLE_REFERENCES[2]['path']:{'model-fresh':True},
            m.CANONICAL:{'samples':[],'synthetic_model_only':True}}
        pins=dict(known);pins[m.CANONICAL]=dict(path=m.CANONICAL,bytes=1,sha256='0'*64)
        class Reader:
            def __init__(self,root,checkpoint):
                self.root=root;self.checkpoint=checkpoint;self.snapshots={};self.read_passes=self.bytes_read=self.final_fresh_hashes=0
                self.json_calls=[]
            def pin(self,name):
                self.checkpoint();pin=dict(pins[name]);self.snapshots[name]=pin
                self.read_passes+=1;self.bytes_read+=pin['bytes'];return pin
            def json(self,name):self.json_calls.append(name);self.pin(name);return records[name]
            def finish(self):self.checkpoint();self.final_fresh_hashes=len(self.snapshots)
        f.Reader=Reader;f.source_reader=Reader(Path('model-root'),f.route.checkpoint)
        f.reference_reader=Reader(Path('model-root'),f.route.checkpoint)
        f.input_api=NS(c=NS(ROOT=Path('model-root')),scope=NS(LIST_PIN=dict(m.ORACLE_REFERENCES[0])),
            BODY_PIN=dict(m.ORACLE_REFERENCES[1]),FRESH_PIN=dict(m.ORACLE_REFERENCES[2]),
            read_exact=original_acceptance.read_exact,exact=original_acceptance.exact,packed=NS(unpack=lambda value,check:value))
        f.bind_inputs=lambda:m.bind_oracle_inputs(f.source_reader,f.reference_reader,f.context,f.pipeline,f.compiled,
            f.prepared,f.bound,f.checked,f.input_api,f.Reader,f.policy)
        if bind:f.inputs=f.bind_inputs();f.api=f.inputs.api
        f.records=records;f.step=step;f.original_candidate=candidate
        return f

    def test_oracle_input_binding_uses_independent_step_and_three_fixed_references_without_candidate(self):
        f=self.oracle_fixture();self.assertEqual(f.inputs.proof['index'],165)
        self.assertTrue(f.inputs.proof['connected']);self.assertFalse(f.inputs.proof['canonical_candidate_read'])
        self.assertFalse(f.inputs.proof['original_candidate_validator_executed'])
        self.assertEqual(set(f.source_reader.snapshots),{m.ORACLE_STEP['path']})
        self.assertEqual(set(f.reference_reader.snapshots),{pin['path'] for pin in m.ORACLE_REFERENCES})
        self.assertEqual(f.reference_reader.json_calls,[m.ORACLE_REFERENCES[0]['path']])
        self.assertEqual(f.claims,{});self.assertEqual(f.compiled.state.invocations,0)
        self.assertIs(f.inputs.api.read_exact,original_acceptance.read_exact)
        self.assertIs(f.checked.checker.validate_candidate,f.original_candidate)

    def test_oracle_bound_api_reader_and_policy_execute_the_entire_original_input_function_model_only(self):
        f=self.oracle_fixture();result=f.run()
        self.assertEqual(result['canonical_receipt_pin']['path'],m.CANONICAL)
        self.assertEqual(f.once.phase,'RETURNED_NOT_ACCEPTED')
        self.assertFalse(f.inputs.proof['actual_Native_or_product_or_oracle_qualified'])
        self.assertIs(f.compiled.oracle_inputs.__code__,original.oracle_inputs.__code__)

    def test_oracle_input_binding_rejects_wrong_context_checker_or_prepared_graph_before_candidate(self):
        for mode in ('checker','built','core'):
            f=self.oracle_fixture(bind=False)
            if mode=='checker':f.checked.checker=NS()
            elif mode=='built':f.prepared.linked=NS()
            else:f.prepared.entry.core={}
            with self.assertRaisesRegex(ValueError,'SAME_UNUSED_ACTUAL_ORACLE_CONTEXT'):f.bind_inputs()
            self.assertEqual(f.claims,{});self.assertNotIn(m.CANONICAL,f.source_reader.json_calls)

    def test_oracle_input_binding_rejects_wrong_step_or_current_case_listing(self):
        for mode in ('step','listing'):
            f=self.oracle_fixture(bind=False)
            if mode=='step':f.step.before=157
            else:f.records[m.ORACLE_REFERENCES[0]['path']]['source_test_names'][164]='model-wrong-case'
            with self.assertRaises(ValueError):f.bind_inputs()
            self.assertEqual(f.claims,{});self.assertNotIn(m.CANONICAL,f.reference_reader.json_calls)

    def test_oracle_reference_expected_pins_cannot_come_from_modified_api_or_candidate(self):
        for mode in ('api','declaration'):
            f=self.oracle_fixture(bind=False)
            if mode=='api':f.input_api.BODY_PIN['sha256']='0'*64
            else:f.checked.known[m.ORACLE_REFERENCES[1]['path']]['sha256']='0'*64
            with self.assertRaises(ValueError):f.bind_inputs()
            self.assertEqual(f.claims,{})

    def test_oracle_context_generator_must_keep_exact_case_cursor_and_single_test_arguments(self):
        f=self.oracle_fixture(bind=False)
        f.checked.checker.environment['context']=lambda step:NS(INDEX=165,BEFORE=158,CASE=step.case,
            PRIOR_ACCEPT_PIN=step.prior_queue_pin,arguments=lambda:['other-case'])
        with self.assertRaisesRegex(ValueError,'ACTUAL_ORIGINAL_CONTEXT_GENERATOR_SELECTS_ONE_CURRENT_CASE'):f.bind_inputs()
        self.assertEqual(f.claims,{})

    def test_oracle_input_api_or_generator_drift_after_binding_denies_before_intent(self):
        for mode in ('api','generator','step'):
            f=self.oracle_fixture()
            if mode=='api':f.api.FRESH_PIN['sha256']='0'*64
            elif mode=='generator':f.checked.checker.environment['context']=lambda step:None
            else:f.step.case='model-replaced-case'
            with self.assertRaises(ValueError):f.run()
            self.assertEqual(f.claims,{});self.assertEqual(f.route.context.jobs,0)

    def test_oracle_input_binding_rejects_other_reader_or_policy_without_reusing_reference_reads(self):
        for mode in ('reader','policy'):
            f=self.oracle_fixture()
            if mode=='reader':f.Reader=lambda *args:None
            else:f.policy=NS(arm=lambda context:None,attempts=1,denied=[])
            with self.assertRaisesRegex(ValueError,'SAME_BOUND_ORACLE_CONTEXT_API_READER_AND_PROCESS_POLICY'):f.run()
            self.assertEqual(f.claims,{})
        f=self.oracle_fixture()
        with self.assertRaisesRegex(ValueError,'FRESH_REFERENCE_READER'):f.bind_inputs()
        self.assertEqual(f.compiled.state.invocations,0)

    def test_original_process_policy_adapter_counts_allowed_audit_events_and_shares_all_denials(self):
        f=self.process_fixture()
        try:
            self.assertIs(f.audit.policy.denied,f.denied);self.assertEqual(f.audit.policy.attempts,0)
            self.assertEqual(f.run(),17);self.assertEqual(f.audit.policy.attempts,1)
            self.assertEqual(f.audit.policy.attempts,f.audit.allowed);self.assertEqual(f.audit.arm_attempts,1)
            with self.assertRaisesRegex(ValueError,'CURRENT805_SHARED_NO_PROCESS'):f.registered[0]('os.system',('command',))
            self.assertTrue(f.audit.policy.denied);self.assertIs(f.audit.policy.denied,f.denied)
        finally:f.audit.restore();f.pipe.close()

    def test_original_process_policy_arm_refuses_preparation_without_claim_or_wrong_context(self):
        for mode in ('claim','context'):
            f=self.process_fixture()
            try:
                context=f.link.context if mode=='claim' else NS()
                with self.assertRaises(ValueError):f.audit.policy.arm(context)
                self.assertEqual(f.audit.allowed,0);self.assertEqual(f.f.created,[])
                self.assertTrue(f.audit.failed)
            finally:f.audit.restore();f.pipe.close()

    def test_oracle_reader_factory_uses_new_reader_bound_loader_never_old_checker_loader(self):
        reader=object();known=object();loader=object();root=object();original_base=object();calls=[]
        fresh=object();answer=object()
        def paced(actual_loader,actual_reader,actual_known):
            self.assertIs(actual_loader,loader);self.assertIs(actual_reader,reader);self.assertIs(actual_known,known)
            calls.append('new-reader-loader');return NS(api=fresh)
        api=NS(AcceptanceReader=original_base)
        def optimize(actual_root,actual_reader,actual_known,actual_loader,base,a):
            self.assertIs(actual_root,root);self.assertIs(actual_reader,reader);self.assertIs(actual_known,known)
            self.assertIs(actual_loader,fresh);self.assertIs(base,original_base);self.assertIs(a,api)
            calls.append('original-optimized-reader-body');return answer
        self.assertIs(m.oracle_reader_factory(root,reader,known,loader,NS(PacedNamespaceLoader=paced),
            NS(optimized_reader=optimize),api),answer)
        self.assertEqual(calls,['new-reader-loader','original-optimized-reader-body'])
