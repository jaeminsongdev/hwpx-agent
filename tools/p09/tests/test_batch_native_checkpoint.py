"""Original pressure guard and restoration, synthetic ownership only."""
import threading
from types import SimpleNamespace as NS
import unittest
import batch_native_checkpoint as module
import metadata_pressure_failfast as original_pressure


def fixture():
    checks=[];ident=[(1,2)];state=NS(attempts=0,frames=[])
    shared=NS(metadata=None,frame=None)
    connection=NS(readers=[],budgets=[])
    batch=NS(phase='READY',shared=shared,parent_connection=NS(state=state),metadata_connection=connection)
    result=NS(assembled=NS(batch=batch))
    prep=NS(closed=False,broken=False,guard=object(),records=[],
        check=lambda *a,**kw:checks.append((a,kw)),bind=lambda r:checks.append(('bind',r)))
    idle=[];bridge=module.Handoff(prep,lambda r:idle.append(r),identity=lambda:ident[0]);bridge.bind(result)
    context=NS(parent=state,active=False,attempts=0,jobs=0,restorations=0)
    return NS(bridge=bridge,prep=prep,batch=batch,result=result,state=state,context=context,
        checks=checks,idle=idle,ident=ident)


def arm(f):
    f.prep.closed=True;f.prep.guard=None
    f.prep.records=[dict(stage=s,cleanup_confirmed=True) for s in ('construction','opening_and_metadata')]
    f.bridge.arm()


def reader(f):
    calls=[]
    def hard():calls.append('original')
    r=NS(checkpoint=hard);owner=NS(checkpoint_io=hard,lock=threading.Lock(),samples=[{'system_cpu_percent':20}])
    p=original_pressure.Checkpoint(r,owner)
    f.batch.metadata_connection.readers.append(r);f.batch.metadata_connection.budgets.append(object())
    f.context.active=True;f.context.attempts=1;f.state.attempts=1
    return r,p,calls


class Tests(unittest.TestCase):
    def test_preparation_delegates_exact_original_arguments(self):
        f=fixture();f.bridge.check(force=True)
        self.assertEqual(f.checks[-1],((),{'force':True}));self.assertEqual(f.bridge.phase,'PREPARATION')

    def test_closed_owners_and_original_idle_check_before_one_way_handoff(self):
        f=fixture();arm(f)
        self.assertEqual(f.idle,[f.result]);self.assertEqual(f.bridge.phase,'WAIT_ORIGINAL_NATIVE')
        with self.assertRaises(ValueError):f.bridge.arm()
        self.assertTrue(f.bridge.broken)

    def test_any_unclosed_or_failed_preparation_prevents_handoff(self):
        for name,value in (('closed',False),('broken',True),('guard',object())):
            f=fixture();f.prep.closed=True;f.prep.guard=None
            f.prep.records=[dict(stage=s,cleanup_confirmed=True) for s in ('construction','opening_and_metadata')]
            setattr(f.prep,name,value)
            with self.assertRaises(ValueError):f.bridge.arm()
            self.assertTrue(f.bridge.broken)

    def test_missing_or_bad_stage_cleanup_prevents_handoff(self):
        for records in ([],[dict(stage='construction',cleanup_confirmed=True)],
            [dict(stage='construction',cleanup_confirmed=True),dict(stage='opening_and_metadata',cleanup_confirmed=False)]):
            f=fixture();f.prep.closed=True;f.prep.guard=None;f.prep.records=records
            with self.assertRaises(ValueError):f.bridge.arm()

    def test_original_idle_failure_preserved_not_ignored(self):
        f=fixture();error=ValueError('TEST_INCOMPLETE_WHOLE_OPENING')
        def fail(result):raise error
        f.bridge.idle=fail;f.prep.closed=True;f.prep.guard=None
        f.prep.records=[dict(stage=s,cleanup_confirmed=True) for s in ('construction','opening_and_metadata')]
        with self.assertRaises(ValueError) as caught:f.bridge.arm()
        self.assertIs(caught.exception,error)

    def test_no_metadata_or_frame_from_previous_preparation_admitted(self):
        for name in ('metadata','frame'):
            f=fixture();setattr(f.batch.shared,name,object())
            with self.assertRaises(ValueError):arm(f)

    def test_waiting_never_uses_closed_preparation_guard(self):
        f=fixture();arm(f);before=list(f.checks)
        with self.assertRaisesRegex(ValueError,'ONLY_ORIGINAL_NATIVE'):f.bridge.check()
        self.assertEqual(f.checks,before);self.assertTrue(f.bridge.broken)

    def test_actual_registered_reader_and_original_pressure_called_without_new_sampler(self):
        f=fixture();arm(f);r,p,calls=reader(f);f.bridge.admit_metadata(r,f.context)
        self.assertIs(f.bridge.reader,r);self.assertIs(f.bridge.pressure,p)
        self.assertEqual(calls,['original','original'])
        before=list(f.checks);f.bridge.check();self.assertEqual(f.checks,before)
        self.assertEqual(calls,['original']*4);self.assertEqual(p.checks,2)

    def test_original_pressure_restoration_followed_without_inactive_guard_reuse(self):
        f=fixture();arm(f);r,p,calls=reader(f);f.bridge.admit_metadata(r,f.context);p.restore()
        f.bridge.check();self.assertEqual(calls,['original']*3)
        self.assertIs(r.checkpoint,p.original);self.assertTrue(p.restored);self.assertFalse(p.active)

    def test_original_75_warning_stops_and_never_returns_to_preparation(self):
        f=fixture();arm(f);r,p,_=reader(f);p.owner.samples[-1]['system_cpu_percent']=75
        with self.assertRaisesRegex(ValueError,'STOP_METADATA_WARNING'):f.bridge.admit_metadata(r,f.context)
        self.assertTrue(p.latched);self.assertTrue(f.bridge.broken)
        p.owner.samples[-1]['system_cpu_percent']=0
        with self.assertRaises(ValueError):f.bridge.check()
        self.assertEqual(f.bridge.phase,'NATIVE')

    def test_foreign_original_reader_or_context_denied_before_checkpoint(self):
        for kind in ('reader','parent','attempts','job','frame'):
            f=fixture();arm(f);r,p,calls=reader(f)
            if kind=='reader':f.batch.metadata_connection.readers[0]=object()
            if kind=='parent':f.context.parent=NS(attempts=1,frames=[])
            if kind=='attempts':f.state.attempts=0
            if kind=='job':f.context.jobs=1
            if kind=='frame':f.state.frames.append(object())
            with self.assertRaises(ValueError):f.bridge.admit_metadata(r,f.context)
            self.assertEqual(calls,[])

    def test_original_owner_checkpoint_substitution_rejected(self):
        f=fixture();arm(f);r,p,calls=reader(f);p.owner.checkpoint_io=lambda:None
        with self.assertRaises(ValueError):f.bridge.admit_metadata(r,f.context)
        self.assertEqual(calls,[])

    def test_arbitrary_reader_checkpoint_substitution_after_binding_rejected(self):
        f=fixture();arm(f);r,p,calls=reader(f);f.bridge.admit_metadata(r,f.context)
        r.checkpoint=lambda:None
        with self.assertRaises(ValueError):f.bridge.check()
        self.assertTrue(f.bridge.broken);self.assertEqual(calls,['original']*2)

    def test_preparation_force_parameter_not_forwarded_into_native(self):
        f=fixture();arm(f);r,p,calls=reader(f);f.bridge.admit_metadata(r,f.context)
        with self.assertRaises(ValueError):f.bridge.check(force=True)
        self.assertEqual(calls,['original']*2)

    def test_original_hard_guard_failure_identity_preserved(self):
        f=fixture();arm(f);r,p,calls=reader(f);error=ValueError('TEST_ORIGINAL_NATIVE_CPU_STOP')
        def fail():raise error
        p.original=p.hard=p.owner.checkpoint_io=fail
        with self.assertRaises(ValueError) as caught:f.bridge.admit_metadata(r,f.context)
        self.assertIs(caught.exception,error);self.assertTrue(f.bridge.broken)

    def test_owner_change_latches_failure(self):
        f=fixture();f.ident[0]=(1,3)
        with self.assertRaises(ValueError):f.bridge.check()
        f.ident[0]=(1,2)
        with self.assertRaises(ValueError):f.bridge.check()

    def test_duplicate_reader_binding_denied(self):
        f=fixture();arm(f);r,p,calls=reader(f);f.bridge.admit_metadata(r,f.context)
        with self.assertRaises(ValueError):f.bridge.admit_metadata(r,f.context)
        self.assertEqual(f.bridge.bindings,1)

    def test_recursive_checkpoint_cannot_spin_or_silently_skip_check(self):
        f=fixture()
        f.prep.check=lambda:f.bridge.check()
        with self.assertRaisesRegex(ValueError,'RECURSIVE_CHECKPOINT'):f.bridge.check()
        self.assertTrue(f.bridge.broken);self.assertFalse(f.bridge.checking)

    def test_original_owner_scope_must_end_before_terminal(self):
        f=fixture();arm(f);r,p,_=reader(f);f.bridge.admit_metadata(r,f.context)
        with self.assertRaises(ValueError):f.bridge.finish_native(f.context)
        f.context.active=False;f.context.restorations=1;f.bridge.finish_native(f.context)
        self.assertEqual(f.bridge.phase,'NATIVE_TERMINAL')
        self.assertFalse(f.bridge.evidence()['Native_or_product_or_Frame_cleanup_qualified'])

    def test_failed_resource_guard_never_prevents_terminal_cleanup_accounting(self):
        f=fixture();arm(f);r,p,_=reader(f);f.bridge.admit_metadata(r,f.context)
        p.owner.samples[-1]['system_cpu_percent']=75
        with self.assertRaises(ValueError):f.bridge.check()
        f.context.active=False;f.context.restorations=1;f.bridge.finish_native(f.context)
        self.assertTrue(f.bridge.evidence()['failed']);self.assertEqual(f.bridge.phase,'NATIVE_TERMINAL')
