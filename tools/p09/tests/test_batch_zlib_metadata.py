"""Read-only owner transition contracts, not Native or product evidence."""
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import batch_zlib_metadata as module


class Guard:
    def __init__(self,role):
        self.role=role;self.cleanup=False;self.samples=[];self.fail=False;self.checked=0
        self.preparation_CPU=NS(summary=lambda:{'role':role,'Native_policy_changed':False})
        self.preparation_limits={'one_logical_CPU':True}
    def acquire(self):pass
    def check(self,**kwargs):
        self.checked+=1
        if self.fail:raise ValueError('STOP_TEST_PRESSURE')
    def close(self):self.cleanup=True


class Tests(unittest.TestCase):
    def fixture(self):
        self.owner=[(1,2)];self.guards=[]
        def factory(role):
            guard=Guard(role);self.guards.append(guard);return guard
        self.epochs=module.ReadOnlyEpochs(factory,clock=lambda:3,identity=lambda:self.owner[0])
        state=NS(attempts=0,frames=[])
        self.context=NS(parent=state,active=False,attempts=0,jobs=0,owner=None,job=None,
            bindings=[],restorations=0,frame_checks=0)
        context=self.context
        def connect_engine():return context
        class Frame:
            def check(self):pass
        self.frame=Frame
        fn=Frame.check
        connection=NS(state=state,classes=((Frame,dict(vars(Frame))),),
            methods=((fn,fn.__code__,fn.__defaults__,fn.__closure__,fn.__kwdefaults__),))
        shared=NS(identity=lambda:(1,2),owner=(1,2),metadata=None,frame=None,restored=False,error=None)
        self.batch=NS(identity=lambda:self.owner[0],owner=(1,2),phase='NEW',active=None,cases=[],
            metadata_reader_active=False,parent_connection=connection,shared=shared,
            whole={'input':{'path':'input','bytes':1,'sha256':'0'*64}},initial=None,final=None,initial_reader=None)
        built=NS(state=NS(attempts=0,calls=0),window=NS(WINDOW_LINK=NS(connect_engine=connect_engine)))
        self.result=NS(assembled=NS(batch=self.batch,built=built))
        return self.epochs

    def opened(self):
        self.batch.phase='READY'
        self.batch.initial={n:dict(p) for n,p in self.batch.whole.items()}
        self.batch.initial_reader=NS(snapshots={n:dict(p) for n,p in self.batch.whole.items()},
            read_passes=len(self.batch.whole),bytes_read=sum(p['bytes'] for p in self.batch.whole.values()))

    def ready(self):
        e=self.fixture();e.advance('construction');e.bind(self.result);return e

    def test_three_original_read_only_roles_cleanup_and_exact_order(self):
        e=self.ready();e.advance('opening_and_metadata');self.opened();e.advance('closing');e.close()
        self.assertEqual([g.role for g in self.guards],['dispatch_construction','whole_metadata_preflight','whole_metadata_preflight'])
        self.assertEqual([r['stage'] for r in e.records],list(e.STAGES))
        self.assertTrue(all(r['cleanup_confirmed'] for r in e.records));self.assertFalse(e.broken)

    def test_duplicate_or_skipped_stage_permanently_latches(self):
        for stage in ('construction','closing'):
            e=self.ready()
            with self.assertRaisesRegex(ValueError,'THREE_EXACT'):e.advance(stage)
            self.assertTrue(e.broken)
            with self.assertRaises(ValueError):e.advance('opening_and_metadata')
            self.assertEqual(len(self.guards),1);e.close()

    def test_resource_failure_cannot_rotate_or_retry(self):
        e=self.ready();self.guards[0].fail=True
        with self.assertRaisesRegex(ValueError,'STOP_TEST_PRESSURE'):e.advance('opening_and_metadata')
        self.guards[0].fail=False
        with self.assertRaises(ValueError):e.advance('opening_and_metadata')
        self.assertEqual(len(self.guards),1);e.close()

    def test_owner_change_cannot_rotate(self):
        e=self.ready();self.owner[0]=(2,2)
        with self.assertRaisesRegex(ValueError,'OWNER_CHANGE'):e.advance('opening_and_metadata')
        self.assertTrue(e.broken);e.close()

    def test_no_rotation_without_actual_constructed_parent(self):
        e=self.fixture();e.advance('construction')
        with self.assertRaisesRegex(ValueError,'ACTUAL_PARENT'):e.advance('opening_and_metadata')
        e.close();self.assertEqual(len(self.guards),1)

    def test_each_actual_execution_counter_or_frame_blocks_rotation(self):
        for changed in ('engine_calls','engine_attempts','parent_attempts','frames'):
            e=self.ready()
            if changed=='engine_calls':self.result.assembled.built.state.calls=1
            elif changed=='engine_attempts':self.result.assembled.built.state.attempts=1
            elif changed=='parent_attempts':self.batch.parent_connection.state.attempts=1
            else:self.batch.parent_connection.state.frames=[object()]
            with self.assertRaisesRegex(ValueError,'ZERO_NATIVE'):e.advance('opening_and_metadata')
            self.assertEqual(len(self.guards),1);e.close()

    def test_active_case_reader_and_broken_batch_block_rotation(self):
        for name,value in (('active',object()),('cases',[165]),('metadata_reader_active',True),('phase','BROKEN')):
            e=self.ready();setattr(self.batch,name,value)
            with self.assertRaisesRegex(ValueError,'READ_ONLY_BATCH'):e.advance('opening_and_metadata')
            e.close()

    def test_frame_class_or_original_function_mutation_blocks_rotation(self):
        for mode in ('class','method'):
            e=self.ready()
            if mode=='class':self.frame.extra=True
            else:self.frame.check.__kwdefaults__={'new':True}
            with self.assertRaisesRegex(ValueError,'UNCHANGED_FRAME'):e.advance('opening_and_metadata')
            e.close()

    def test_shared_frame_active_decoder_error_or_restoration_blocks_rotation(self):
        for name,value in (('frame',object()),('metadata',NS(active=1,error=None)),
            ('metadata',NS(active=None,error=ValueError('failed'))),('error',ValueError('failed')),('restored',True)):
            e=self.ready();setattr(self.batch.shared,name,value)
            with self.assertRaisesRegex(ValueError,'SHARED_DECODER'):e.advance('opening_and_metadata')
            e.close()

    def test_any_readiness_or_job_execution_blocks_rotation(self):
        for name,value in (('active',True),('attempts',1),('jobs',1),('owner',object()),('job',object()),
            ('bindings',[object()]),('restorations',1),('frame_checks',1),('parent',NS(attempts=0,frames=[]))):
            e=self.ready();setattr(self.context,name,value)
            with self.assertRaisesRegex(ValueError,'ZERO_READINESS'):e.advance('opening_and_metadata')
            e.close()

    def test_closed_epochs_never_reopen(self):
        e=self.ready();e.close()
        with self.assertRaises(ValueError):e.advance('opening_and_metadata')
        self.assertEqual(len(self.guards),1)

    def test_final_batch_requires_empty_real_completed_boundaries(self):
        self.fixture()
        with self.assertRaisesRegex(ValueError,'READ_ONLY_BATCH'):module.idle(self.result,closed=True)
        self.batch.phase='EMPTY_BATCH_AUDITED_NOT_ACCEPTED'
        with self.assertRaisesRegex(ValueError,'COMPLETE_WHOLE_OPENING'):module.idle(self.result,closed=True)
        self.opened();self.batch.phase='EMPTY_BATCH_AUDITED_NOT_ACCEPTED';self.batch.final=dict(self.batch.initial)
        self.assertIs(module.idle(self.result,closed=True),self.context)

    def test_ready_label_without_real_opening_cannot_rotate(self):
        e=self.ready();self.batch.phase='READY'
        with self.assertRaisesRegex(ValueError,'COMPLETE_WHOLE_OPENING'):e.advance('opening_and_metadata')
        self.assertTrue(e.broken);self.assertEqual(len(self.guards),1);e.close()

    def test_incomplete_or_changed_opening_accounting_is_rejected(self):
        for changed in ('pins','snapshots','passes','bytes'):
            self.fixture();self.opened()
            if changed=='pins':self.batch.initial={}
            elif changed=='snapshots':self.batch.initial_reader.snapshots={}
            elif changed=='passes':self.batch.initial_reader.read_passes=0
            else:self.batch.initial_reader.bytes_read=2
            with self.assertRaisesRegex(ValueError,'COMPLETE_WHOLE_OPENING'):module.idle(self.result)

    def test_closed_label_requires_actual_equal_final_pins(self):
        for final in (None,{}, {'input':{'path':'input','bytes':2,'sha256':'0'*64}}):
            self.fixture();self.opened();self.batch.phase='EMPTY_BATCH_AUDITED_NOT_ACCEPTED';self.batch.final=final
            with self.assertRaisesRegex(ValueError,'COMPLETE_WHOLE_CLOSING'):module.idle(self.result,closed=True)

    def test_process_creation_is_always_denied_and_recorded(self):
        denied=[];audit=module.process_blocker(denied)
        audit('ordinary.event',())
        for event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            with self.assertRaisesRegex(ValueError,'PERMANENTLY_DENIED'):audit(event,())
        self.assertEqual(len(denied),6)

    def test_product_native_and_arbitrary_modes_rejected_before_bootstrap(self):
        for args in ([],['--native'],['--GO'],['--metadata','--native'],['--connect']):
            with patch.object(module.sys,'argv',['entry',*args]):
                with self.assertRaisesRegex(ValueError,'ONLY_READ_ONLY'):module.main()

    def test_approved_admission_uses_exact_source_and_private_selector_only(self):
        seed=object();actual_policy=object();calls=[]
        loader=NS(load=lambda root,pins,reuse:(calls.append(pins) or NS(preparation_attributed_cpu_v1=seed),None))
        selected=object()
        def select(original,policy,instances):
            self.assertIs(original,loader);self.assertIs(policy,seed)
            guard=Guard('dispatch_construction');guard.close();instances.append(guard);return selected
        def admit(root,actual,entry,a,c):
            self.assertIs(actual,selected);return actual_policy,{'closed':True},'Reader','chunk'
        prep=NS(POLICY={'path':'exact-qualified-source'},policy_loader=select,admission=admit)
        policy,witness,reader,chunk=module.approved_admission(None,prep,loader,None,None,None)
        self.assertIs(policy,actual_policy);self.assertEqual(calls,[[prep.POLICY]])
        self.assertTrue(witness['closed']);self.assertFalse(witness['default_admission_policy_changed'])
        self.assertEqual((reader,chunk),('Reader','chunk'))

    def test_failed_admission_retains_actual_closed_owner_telemetry(self):
        guard=Guard('dispatch_construction');guard.close();guard.samples=[{'system_cpu_percent':90.5}]
        def select(loader,policy,instances):instances.append(guard);return loader
        def fail(*args):raise ValueError('STOP_PREPARATION_SYSTEM_PRESSURE90')
        loader=NS(load=lambda *args:(NS(preparation_attributed_cpu_v1=object()),None))
        prep=NS(POLICY={},policy_loader=select,admission=fail)
        with self.assertRaises(ValueError) as caught:module.approved_admission(None,prep,loader,None,None,None)
        record=caught.exception.preparation_evidence
        self.assertTrue(record[0]['cleanup_confirmed'])
        self.assertEqual(record[0]['terminal_resource_samples'],guard.samples)

    def test_terminal_sample_tail_is_bounded_without_new_observations(self):
        for count in (0,3,20):
            samples=[{'time_utc':str(i),'system_cpu_percent':i} for i in range(count)]
            record={'stage':'closing','samples':samples,'cleanup_confirmed':True}
            row=module.epoch_evidence(record)
            self.assertEqual(row['original_resource_sample_count'],count)
            self.assertEqual(row['terminal_resource_samples'],samples[-8:])
            self.assertLessEqual(len(row['terminal_resource_samples']),8)
            self.assertFalse(row['additional_sampler_or_query_started']);self.assertNotIn('samples',row)

    def test_terminal_sample_tail_keeps_unknown_attribution_as_none(self):
        row=module.epoch_evidence({'samples':[{'system_cpu_percent':90.1,'parent_cpu_machine_percent':None}]})
        self.assertIsNone(row['terminal_resource_samples'][0]['parent_cpu_machine_percent'])
        self.assertNotIn('parent_private_mib',row['terminal_resource_samples'][0])

    def test_terminal_tail_is_independent_and_drops_nonmetric_fields(self):
        samples=[{'system_cpu_percent':90.2,'parent_cpu_machine_percent':.2,'unrelated_payload':'fixture-only'}]
        row=module.epoch_evidence({'samples':samples,'cleanup_confirmed':True})
        self.assertNotIn('unrelated_payload',row['terminal_resource_samples'][0])
        row['terminal_resource_samples'][0]['system_cpu_percent']=1
        self.assertEqual(samples[0]['system_cpu_percent'],90.2)


if __name__=='__main__':unittest.main()
