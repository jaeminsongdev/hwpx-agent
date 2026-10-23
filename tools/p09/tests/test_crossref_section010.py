"""Non-Native virtual-clock timing and actual boundary hook contracts."""
import copy,json,unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import crossref_section010_policy as subject
import crossref_external010_runtime as runtime
import run_external_crossref_fixed_batch010 as entry

class Base:
    def __init__(self):
        self.deadline=600.;self.samples=[];self.hot=2;self.cpu=12.;self.last=1.;self.windows=object();self.mutex=object();self.cleanup=False;self.pressure=False
    def check(self,force=False):
        if subject.time.monotonic()>=self.deadline:raise ValueError('CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT')
        if self.pressure:raise ValueError('STOP_ORIGINAL_RESOURCE_PRESSURE')
        self.samples.append(dict(model_only=True));self.last=subject.time.monotonic();self.cpu+=.25
    def close(self):self.cleanup=True

def receipt(label='model'):
    return dict(label=label,closed=True,readers={name:dict(fresh_inputs=3,final_fresh_hashes=3)for name in('source','native','shell','runtime')})

def host_for(index):
    sessions=[dict(case_index=i//2+1,session_label='save'if i%2==0 else'reopen',startup_profile=dict(cleanup_confirmed=True))for i in range(2*(index-1))]
    return NS(ready=True,source_case=None,scope=NS(current=None,pending_admission=False,stopped=False,
        case_index=index,cursor=0,sessions=sessions,finished=[dict(case_index=i,case_status='returned')for i in range(1,index)]),
        protocol=NS(protocol=NS(stopped=False,case_index=index)))

class Policy(unittest.TestCase):
    def setUp(self):
        self.now=0.;self.clock=patch.object(subject.time,'monotonic',side_effect=lambda:self.now);self.clock.start();self.addCleanup(self.clock.stop)
        self.guard=subject.guard_type(Base)()
    def next(self,label=None,closed=lambda:True):self.guard.advance(label or subject.SECTIONS[self.guard.section_index+1],closed)
    def test_01_whole_over600_but_all_closed_sections_complete_without_replaying(self):
        for label in subject.SECTIONS[1:]:self.now+=90;self.next(label)
        self.now+=90;self.guard.complete(lambda:True)
        row=self.guard.section_summary();self.assertTrue(row['completed']);self.assertEqual(len(row['closed_sections']),12);self.assertGreater(self.now,600)
    def test_02_expired_section_cannot_be_renewed(self):
        self.now=600
        with self.assertRaisesRegex(ValueError,'ORIGINAL600_TIMEOUT'):self.next()
        self.assertEqual(self.guard.deadline,600)
    def test_03_deadline_during_closure_cannot_be_renewed(self):
        def closure():self.now=600.;return True
        with self.assertRaises(ValueError):self.next(closed=closure)
        self.assertEqual(self.guard.section_index,0)
    def test_04_whole1800_bound_is_not_twelve_unbounded600_windows(self):
        for label in subject.SECTIONS[1:7]:self.now+=250;self.next(label)
        self.now=1800
        with self.assertRaisesRegex(ValueError,'WHOLE1800_TIMEOUT'):self.guard.check()
    def test_05_wrong_order_subset_or_repeated_section_seals(self):
        for label in('case2','preparation','qualification '):
            guard=subject.guard_type(Base)()
            with self.assertRaises(ValueError):guard.advance(label,lambda:True)
            with self.assertRaises(ValueError):guard.advance('qualification',lambda:True)
    def test_06_unclosed_or_nonboolean_boundary_denies(self):
        for value in(False,1,None,{},'true'):
            guard=subject.guard_type(Base)()
            with self.assertRaises(ValueError):guard.advance('qualification',lambda:value)
            self.assertEqual(guard.deadline,600)
    def test_07_resource_failure_cannot_be_cleared_by_boundary(self):
        self.guard.pressure=True
        with self.assertRaisesRegex(ValueError,'STOP_ORIGINAL_RESOURCE_PRESSURE'):self.next()
        self.guard.pressure=False
        with self.assertRaisesRegex(ValueError,'SEALED_NO_CONTINUATION'):self.guard.check()
    def test_08_original_windows_mutex_cpu_history_and_hot_counter_are_not_reset(self):
        samples=self.guard.samples;windows=self.guard.windows;mutex=self.guard.mutex
        self.guard.check();cpu=self.guard.cpu;last=self.guard.last;self.now=12;self.next()
        self.assertIs(self.guard.samples,samples);self.assertIs(self.guard.windows,windows);self.assertIs(self.guard.mutex,mutex)
        self.assertEqual(self.guard.hot,2);self.assertGreater(self.guard.cpu,cpu);self.assertGreater(self.guard.last,last)
        self.assertFalse(hasattr(self.guard,'preparation_CPU'));self.assertEqual(len(samples),3)
    def test_09_failed_completion_does_not_make_it_final(self):
        with self.assertRaises(ValueError):self.guard.complete(lambda:True)
        self.assertFalse(self.guard.section_completed)
    def test_10_preflight_cannot_become_qualification_or_new_permit(self):
        self.guard.complete(lambda:True,preflight=True)
        with self.assertRaises(ValueError):self.next()
    def test_11_boundary_callback_exception_seals_and_cleanup_stays_available(self):
        def fail():raise OSError('private-canary-not-published')
        with self.assertRaises(OSError):self.next(closed=fail)
        self.guard.close();self.assertTrue(self.guard.cleanup);self.assertTrue(self.guard.section_failed)
    def test_12_all_original_four_readers_must_close_fresh(self):
        self.assertTrue(subject.closed_boundary(receipt()))
        for field in('closed','readers'):
            bad=receipt();bad[field]=None;self.assertFalse(subject.closed_boundary(bad))
        for value in(0,True,2):
            bad=receipt();bad['readers']['native']['final_fresh_hashes']=value;self.assertFalse(subject.closed_boundary(bad))
    def test_13_actual_case_hook_cannot_advance_with_live_owner_or_pending_admission(self):
        for field,value in(('current',object()),('pending_admission',True),('stopped',True),('cursor',1),('case_index',3)):
            cases=runtime.CaseInputs(self.guard,{},{});cases.bind(host_for(1),NS(summary=lambda:receipt()),NS(consumed=True))
            setattr(cases.host.scope,field,value)
            with self.assertRaises(ValueError):cases.between_cases(1)
        self.assertEqual(self.guard.section_index,0)
    def test_14_actual_case_hook_requires_source_final_rereads_and_exact_retired_profiles(self):
        cases=runtime.CaseInputs(self.guard,{},{});cases.rows=[receipt('case1')];cases.bind(host_for(2),NS(summary=lambda:receipt()),NS(consumed=True))
        self.assertTrue(cases.between_cases(2))
        cases.rows[0]['readers']['source']['final_fresh_hashes']=2
        with self.assertRaises(ValueError):cases.between_cases(2)
        cases.rows=[receipt()];cases.host.scope.sessions[0]['startup_profile']['cleanup_confirmed']=False
        with self.assertRaises(ValueError):cases.between_cases(2)
    def test_15_actual_case_begin_advances_only_after_original_previous_finish(self):
        self.next('qualification');cases=runtime.CaseInputs(self.guard,{},{});cases.bind(host_for(1),NS(summary=lambda:receipt()),NS(consumed=True))
        with patch.object(runtime,'Boundary',return_value=NS(label='case1'))as boundary:cases.begin(1)
        self.assertEqual(self.guard.section_index,2);boundary.assert_called_once();self.assertEqual(cases.current.label,'case1')
        with self.assertRaises(ValueError):cases.begin(1)
    def test_16_first_case_requires_current_consumed_qualified_handoff(self):
        cases=runtime.CaseInputs(self.guard,{},{});cases.bind(host_for(1),NS(summary=lambda:receipt()),NS(consumed=False))
        with self.assertRaises(ValueError):cases.between_cases(1)
    def test_17_failed_finish_or_nonfinal_ack_does_not_advance(self):
        for value in(dict(operation='finish',case_index=8,case_status='failed'),dict(operation='finish',case_index=7,case_status='returned'),dict(operation='checkpoint',case_index=8)):
            host=NS(ready=True,respond=Mock(return_value=json.dumps(dict(acknowledged=True))),guard=NS(advance=Mock()))
            handler=runtime.BatchHandler(host,NS(between_cases=Mock(return_value=True)));handler.handle(json.dumps(value));host.guard.advance.assert_not_called()
    def test_18_final_finish_ack_requires_all_eight_closed_before_batch_close(self):
        host=NS(ready=True,respond=Mock(return_value=json.dumps(dict(acknowledged=True))),guard=NS(advance=Mock()))
        cases=NS(between_cases=Mock(return_value=True));handler=runtime.BatchHandler(host,cases)
        handler.handle(json.dumps(dict(operation='finish',case_index=8,case_status='returned')))
        label,closed=host.guard.advance.call_args.args;self.assertEqual(label,'batch_close');self.assertTrue(closed());cases.between_cases.assert_called_once_with(9)
    def test_19_final_audit_constructs_new_readers_and_physically_checks_all_initial_pins(self):
        prior=NS(root='MODEL_ROOT',snapshots={'one':dict(path='one',bytes=2,sha256='a'*64)})
        new=NS(pin=Mock(return_value=prior.snapshots['one']))
        with patch.object(entry.r.a,'AcceptanceReader',return_value=new)as reader:
            result=entry.final_readers({'source':prior},self.guard)
        self.assertIs(result['source'],new);self.assertIsNot(new,prior);new.pin.assert_called_once_with('one');reader.assert_called_once_with('MODEL_ROOT',self.guard.check)
    def test_20_final_changed_pin_is_denied_not_rebased(self):
        prior=NS(root='MODEL_ROOT',snapshots={'one':dict(path='one',bytes=2,sha256='a'*64)})
        with patch.object(entry.r.a,'AcceptanceReader',return_value=NS(pin=Mock(return_value={}))),self.assertRaises(ValueError):entry.final_readers({'source':prior},self.guard)
    def test_21_prep_close_calls_each_original_finish_once_and_checks_counts(self):
        readers={name:NS(snapshots={'a':{}},final_fresh_hashes=1,finish=Mock())for name in('source','native','shell','runtime')}
        self.assertTrue(subject.closed_boundary(entry.close_readers(readers)))
        for reader in readers.values():reader.finish.assert_called_once()
        readers['source'].final_fresh_hashes=0
        with self.assertRaises(ValueError):entry.close_readers(readers)

if __name__=='__main__':unittest.main()
