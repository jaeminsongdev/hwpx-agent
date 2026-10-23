"""Lifecycle/call-order models only: no actual Frame, source IO or product."""
from types import FunctionType,SimpleNamespace as NS,MappingProxyType
import unittest
import native011_readonly_frame_probe as probe


class ReadonlyFrameContracts(unittest.TestCase):
    def fixture(self):
        events=[];clock=[0.0];mode=NS(read_error=False,close_fail=False,flag_fail=False,missing_budget=False)
        current={f'tools/p09/model{i}.py':dict(path=f'tools/p09/model{i}.py',bytes=1,sha256='0'*64) for i in range(201)}
        whole=dict(current);state=NS(frames=[],attempts=0);shared=NS(metadata=None,frame=None,restored=False)
        shared.evidence=lambda:dict(shared_limit_seconds=5,metadata_registered=True,Frame_registered=True)
        owner=NS(phase='READY',active=None,cases=[],metadata_reader_active=False,whole=whole,current=current,
            initial=dict(whole),initial_reader=NS(snapshots=dict(whole),read_passes=201,bytes_read=201),shared=shared)
        class Locks:
            def __init__(self,*args,api):
                self.closed=False;self.maximum_seconds=600;self.phase_pacer=api.pacer
                self.phase_clock=api.pacer.clock;self.phase_used=False
            def mark(self,name):events.append(name)
            def close(self):self.closed=True;return True
        class Frame:
            def __init__(self,registry,required,checkpoint,held):
                events.append('construct_frame');self.inputs=MappingProxyType(dict(required));self.held=held
                self.state='NEW';self.registered=False;self.readers=[];self.boundaries=[]
                self.raw_policy=NS(restored=False,installed=False);state.frames.append(self);shared.frame=object()
            def acquire(self):
                if state.attempts!=1 or state.frames!=[self]:raise ValueError('MODEL_EXACT_OWNED_PARENT_FRAME_REFERENCE')
                events.append('acquire');self.state='HELD';self.registered=True;self.raw_policy.installed=True
                owner.phase='CASE_ACTIVE';owner.active=(165,self,None)
            def close(self):
                events.append('close');self.held.closed=True;self.state='CLOSED';self.registered=False
                self.raw_policy.installed=False;self.raw_policy.restored=True;owner.phase='BROKEN'
                return not mode.close_fail
            def summary(self):return dict(frame_state=self.state,fixture_only_not_actual_Frame=True)
        native=NS(frames=NS(Frame=Frame));env={}
        def original(run):raise AssertionError('PRODUCT_BODY_MUST_NOT_RUN')
        state.original=original
        def execute(run):
            if run!=1 or state.attempts!=0:raise ValueError('MODEL_PARENT_NO_RETRY')
            state.attempts+=1;env['native']=native
            try:return original(run)
            finally:env.pop('native',None)
        wrapper=FunctionType(execute.__code__,env,closure=execute.__closure__)
        owner.parent_connection=NS(lifecycle_connected=True,state=state,registry_type=lambda:object(),frame_type=Frame,
            parent=NS(run_owned=wrapper))
        context=NS(data=NS(planned=NS(batch=owner)),prepared=NS(linked=NS(state=NS(attempts=0,calls=0))))
        def read(frame,factory,checkpoint,guards):
            events.append('read');checkpoint()
            if mode.read_error:raise ValueError('MODEL_PRIMARY_READ_FAILURE')
            frame.readers.append(factory(checkpoint));frame.boundaries.append(object())
            frame.state='BEFORE_READ' if len(frame.boundaries)==1 else 'AFTER_READ'
        api=NS(InputLocks=Locks,EarlySourceCheckpoint=lambda checkpoint,resources:checkpoint,read_with_held_path_guards=read)
        from locked_runtime_inputs import OpenPacer
        class Native:
            def __init__(self,checkpoint):self.pacer=OpenPacer(checkpoint)
        def metadata(checkpoint):
            events.append('metadata');checkpoint()
            if not mode.missing_budget:shared.metadata=object()
            return NS(api=api,required=current,proof=dict(fixture_only=True),native_type=Native,pacer_type=OpenPacer)
        class Loan:
            def __init__(self,*args,**kwargs):self.state='NEW'
            def arm(self):events.append('flags_arm');self.state='ARMED';return tuple(range(1,202))
            def restore(self):events.append('flags_restore');self.state='RESTORED';return not mode.flag_fail
            def summary(self):return dict(fixture_only=True)
        def verify(frame,required,**kwargs):
            events.append('coverage_'+kwargs['boundary']);return dict(fixture_only=True)
        phase=probe.NativePhase(clock=lambda:clock[0])
        args=(context,'.',metadata,lambda *args:NS(fresh=True),NS(),lambda:None,
            NS(verify=verify),NS(SourceInheritance=Loan),current)
        return phase,args,owner,events,clock,mode
    def test_original_order_both_boundaries_flags_restore_and_intentional_abort(self):
        phase,args,owner,events,_,_=self.fixture();result=phase.run(*args)
        self.assertEqual(events.count('read'),2);self.assertEqual(events.count('metadata'),1)
        self.assertLess(events.index('flags_restore'),len(events)-1-events[::-1].index('read'))
        self.assertEqual(owner.phase,'BROKEN');self.assertEqual(owner.cases,[])
        self.assertEqual(result['actual_accepted_count_delta'],0)
        self.assertFalse(result['actual_owned_Native_acceptance_qualified'])
        self.assertFalse(result['proof']['original_Job_commit_supplied'])
        self.assertEqual(events[-1],'close')
    def test_previous_pass_or_partial_whole_opening_is_not_accepted(self):
        phase,args,owner,events,_,_=self.fixture();owner.initial_reader.bytes_read=1
        with self.assertRaisesRegex(ValueError,'ACTUAL_COMPLETE_NEW_WHOLE_OPENING'):phase.run(*args)
        self.assertEqual(events,[])
    def test_disconnected_lifecycle_cannot_bypass_original_case_start(self):
        phase,args,owner,events,_,_=self.fixture();owner.parent_connection.lifecycle_connected=False
        with self.assertRaisesRegex(ValueError,'ORIGINAL_CONNECTED_LIFECYCLE'):phase.run(*args)
        self.assertEqual(events,[])
    def test_missing_real_metadata_budget_rejected_before_frame_construction(self):
        phase,args,_,events,_,mode=self.fixture();mode.missing_budget=True
        with self.assertRaisesRegex(ValueError,'REAL_METADATA_BEFORE_FRAME'):phase.run(*args)
        self.assertEqual(events,['metadata'])
    def test_metadata_time_is_in_same600_clock_not_a_fresh_frame_clock(self):
        phase,args,_,events,clock,_=self.fixture();before=args[2]
        def metadata(checkpoint):
            value=before(checkpoint);clock[0]=600;return value
        args=list(args);args[2]=metadata
        with self.assertRaisesRegex(ValueError,'ORIGINAL600_INCLUDES_METADATA'):phase.run(*args)
        self.assertNotIn('construct_frame',events)
        with self.assertRaisesRegex(ValueError,'ONE_READONLY_PHASE_NO_RETRY'):phase.run(*args)
    def test_original_read_error_survives_additional_cleanup_failure(self):
        phase,args,owner,events,_,mode=self.fixture();mode.read_error=True;mode.close_fail=True
        with self.assertRaisesRegex(ValueError,'MODEL_PRIMARY_READ_FAILURE'):phase.run(*args)
        self.assertIn('FRAME_CLOSE_UNCONFIRMED',phase.cleanup_errors)
        self.assertEqual(events.count('read'),1);self.assertEqual(events[-1],'close')
        self.assertTrue(phase.failed);self.assertEqual(owner.cases,[])
    def test_failed_flag_restore_prevents_second_read_and_acceptance(self):
        phase,args,owner,events,_,mode=self.fixture();mode.flag_fail=True
        with self.assertRaisesRegex(ValueError,'ORIGINAL_SOURCE_FLAGS_RESTORED'):phase.run(*args)
        self.assertEqual(events.count('read'),1);self.assertEqual(owner.phase,'BROKEN')
        self.assertEqual(owner.cases,[]);self.assertTrue(phase.failed)
    def test_successful_readonly_abort_also_cannot_be_reused_or_committed(self):
        phase,args,owner,events,_,_=self.fixture();phase.run(*args)
        with self.assertRaisesRegex(ValueError,'ONE_READONLY_PHASE_NO_RETRY'):phase.run(*args)
        self.assertEqual(events.count('acquire'),1);self.assertEqual(owner.cases,[])
    def test_actual_original_parent_wrapper_records_own_attempt_without_calling_engine_or_worker(self):
        import runtime_envelope_parent_connection_v1 as parent
        from test_runtime_envelope_parent_connection_v1 import make_engine
        engine,binding,_,_,made,seen,_=make_engine()
        connected,state=parent.connect_engine(engine,binding)
        closure=dict(zip(connected.run_owned.__code__.co_freevars,
            (cell.cell_contents for cell in connected.run_owned.__closure__)))
        frame_type=closure['native'].frames.Frame
        connection=NS(parent=connected,state=state,frame_type=frame_type)
        saved=dict(engine.run_owned.__globals__)
        result=probe.parent_readonly(connection,lambda run:('readonly',run,state.attempts))
        self.assertEqual(result,('readonly',1,1));self.assertEqual(state.frames,[])
        self.assertEqual(state.bootstrap_calls,state.budget_calls);self.assertEqual(state.dump_calls,0)
        self.assertEqual(made,[]);self.assertEqual(seen,[])
        self.assertTrue(all(engine.run_owned.__globals__[key] is value for key,value in saved.items()))
        with self.assertRaises(ValueError):probe.parent_readonly(connection,lambda run:None)
    def test_direct_frame_without_original_parent_attempt_is_rejected_by_model(self):
        _,args,owner,_,_,_=self.fixture();parent=owner.parent_connection
        frame=parent.frame_type(parent.registry_type(),owner.current,lambda:None,
            held=NS(closed=False,maximum_seconds=600))
        with self.assertRaisesRegex(ValueError,'EXACT_OWNED_PARENT_FRAME_REFERENCE'):frame.acquire()
    def test_native_pacing_selection_keeps_class_rate_guard_sleeper_and_unused_state(self):
        import time
        from locked_runtime_inputs import OpenPacer
        saved=[];checkpoint=lambda:None
        class Native:
            def __init__(self,check):self.pacer=OpenPacer(check);saved.append(self.pacer)
        native,proof=probe.precise_native(Native,OpenPacer,checkpoint)
        self.assertIs(type(native.pacer),OpenPacer);self.assertIs(native.pacer.clock,time.perf_counter)
        self.assertIs(saved[0].clock,time.monotonic);self.assertIs(native.pacer.checkpoint,checkpoint)
        self.assertEqual(native.pacer.rate,32);self.assertEqual(native.pacer.opens,0)
        self.assertIsNone(native.pacer.previous);self.assertEqual(native.pacer.sleep_seconds,0)
        self.assertTrue(proof['saved_phase_clock_captured_after_selection'])
    def test_used_or_nonoriginal_native_pacer_is_rejected_before_clock_change(self):
        from locked_runtime_inputs import OpenPacer
        for key,value in (('opens',1),('previous',1.),('rate',20),('sleep_seconds',.1)):
            saved=[]
            class Native:
                def __init__(self,check):
                    self.pacer=OpenPacer(check);setattr(self.pacer,key,value);saved.append(self.pacer)
            with self.assertRaisesRegex(ValueError,'ONLY_UNUSED_ORIGINAL_NATIVE_PACER'):
                probe.precise_native(Native,OpenPacer,lambda:None)
            self.assertEqual(getattr(saved[0],key),value)
