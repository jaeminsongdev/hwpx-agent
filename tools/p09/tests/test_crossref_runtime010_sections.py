"""Full new010 controller composition with fake closed processes, no starts."""
import contextlib,json,unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import crossref_external010_runtime as subject
import crossref_section010_policy as policy
from test_crossref_section010 import Base,receipt,host_for

@contextlib.contextmanager
def composition(*,qualification_failed=False,count=8,cleanup=True,missing_final_hash=False):
    clock=[0.];record={};hosts=[]
    def boundary(*args):
        obj=NS(source=NS(),closed=False,fingerprint='MODEL010',native_pin=Mock(),shell_pin=Mock(),label=args[3])
        def finish():obj.closed=True
        def summary():
            row=receipt(obj.label);row['closed']=obj.closed
            if missing_final_hash and obj.label=='case1':row['readers']['source']['final_fresh_hashes']=0
            return row
        obj.finish=finish;obj.summary=summary;return obj
    worker=NS(start_session_worker=Mock());full=NS(start_fixed_worker=Mock(),closed=True);handoff=NS(consumed=False)
    def host_factory(guard,worker,hand,*args):
        host=host_for(1);host.guard=guard;host.scope.closed=False;host.begin,host.end=args[-2:];host.worker_lease=NS(closed=True)
        hand.consumed=True
        def respond(raw):return json.dumps(dict(acknowledged=True))
        host.respond=respond;hosts.append(host);return host
    def transport(guard,process,source,start,handler,schema,env,notify,attempt):
        if 'session-worker'in schema:
            attempt.update(exit_code=2 if qualification_failed else 0,cleanup=True);return {'MODEL_QUALIFICATION':True}
        host=hosts[0]
        for index in range(1,count+1):
            clock[0]+=90;host.begin(index)
            host.end(index)
            after=host_for(index+1);host.scope,host.protocol=after.scope,after.protocol;host.source_case=None;host.scope.closed=False
            handler.handle(json.dumps(dict(operation='finish',case_index=index,case_status='returned')))
        host.scope.closed=True;attempt.update(exit_code=0,cleanup=cleanup)
        return dict(state='fixed_eight_callbacks_returned_semantics_unqualified',completed_callback_cases=count,
            host_messages=152,retained_live_or_uncertain_owners=0,probe_lease_closed=True)
    with contextlib.ExitStack()as stack:
        stack.enter_context(patch.object(policy.time,'monotonic',side_effect=lambda:clock[0]))
        guard=policy.guard_type(Base)();guard.advance('qualification',lambda:True)
        for p in(patch.object(subject,'Boundary',side_effect=boundary),patch.object(subject,'absent_attempts'),
            patch.object(subject.installed,'current_identity',return_value={'MODEL_CREATOR':True}),
            patch.object(subject.original.candidate,'SessionWorker',return_value=worker),
            patch.object(subject.original.session,'SessionQualifier',return_value=NS()),
            patch.object(subject.original.batch,'issue_handoff',return_value=handoff),patch.object(subject.capture,'Fixed010Worker',return_value=full),
            patch.object(subject.original.batch,'FixedEightHost',side_effect=host_factory),patch.object(subject.io,'run',side_effect=transport),
            patch.object(subject.original.session.startup,'parent_without_prompt_kill'),patch.object(subject,'capture_artifacts',return_value={'cases':[{}]*8})):
            stack.enter_context(p)
        yield NS(guard=guard,record=record,clock=clock,execute=lambda:subject.execute(guard,{},subject.CASE_PATHS,{}, {},lambda *args:None,record),
            fixed=subject.capture.Fixed010Worker,capture=subject.capture_artifacts,transport=subject.io.run)

class Runtime010(unittest.TestCase):
    def test_01_eight_real_controller_hooks_cross600_only_at_closed_case_boundaries(self):
        with composition()as m:
            self.assertEqual(len(m.execute()['cases']),8);self.assertGreater(m.clock[0],600)
            self.assertTrue(m.record['batch_closed_for_final_audit']);self.assertEqual(len(m.record['case_source_boundaries']),8)
            self.assertEqual(m.guard.section_summary()['current_section'],'batch_close');self.assertEqual(m.transport.call_count,2)
            m.guard.advance('final_audit',lambda:True);m.guard.complete(lambda:True)
    def test_02_failed_session_never_creates_fixed_worker_or_new_case_budget(self):
        with composition(qualification_failed=True)as m:
            with self.assertRaises(ValueError):m.execute()
            m.fixed.assert_not_called();m.capture.assert_not_called();self.assertEqual(m.guard.section_index,1)
    def test_03_seven_callbacks_cannot_advance_to_batch_or_final_audit(self):
        with composition(count=7)as m:
            with self.assertRaises(ValueError):m.execute()
            m.capture.assert_not_called();self.assertNotIn('batch_closed_for_final_audit',m.record)
    def test_04_incomplete_prior_fresh_inputs_stop_next_case_before_new_worker_effect(self):
        with composition(missing_final_hash=True)as m:
            with self.assertRaises(ValueError):m.execute()
            self.assertEqual(m.guard.section_index,2);self.assertTrue(m.guard.section_failed);m.capture.assert_not_called()
    def test_05_worker_cleanup_false_never_opens_final_audit(self):
        with composition(cleanup=False)as m:
            with self.assertRaises(ValueError):m.execute()
            self.assertNotIn('batch_closed_for_final_audit',m.record)
    def test_06_new010_uses603_for_both_stages_without_rebinding_consumed_runtime(self):
        import crossref_native_worker_io603 as fresh
        import crossref_native_worker_io as old
        self.assertIs(subject.io,fresh);self.assertIs(subject.original.io,old)

if __name__=='__main__':unittest.main()
