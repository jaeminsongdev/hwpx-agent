"""Controller/entry/producer checks on models, never Native execution."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import block_bookmark_source650 as m
import run_block_bookmark_source650 as entry

class Guard:
    def __init__(self):self.samples=[];self.cleanup=True;self.deadline=0;self.denied=False;self.events=[];self.windows=object()
    def check(self,force=False):
        if self.denied:raise ValueError('STOP_CPU_LIMIT')
    def acquire(self):pass
    def close(self):pass
    def advance(self,label,closed):assert closed()is True;self.events.append(label)
    def complete(self,closed,**kw):assert closed()is True
    def section_summary(self):return {'modeled':True}

class Reader:
    def __init__(self,root=None,checkpoint=None):
        self.root=m.r.c.ROOT if root is None else root;self.snapshots={'input':dict(path='input',bytes=1,sha256='0'*64)};self.final_fresh_hashes=0
    def pin(self,path):
        value=dict(path=path,bytes=1,sha256='0'*64);self.snapshots[path]=value;return value
    def fresh_pin(self,path):return self.pin(path)
    def finish(self):self.final_fresh_hashes=len(self.snapshots)

def artifact_fixture():
    owners=[{'model_owner':1},{'model_owner':2}]
    artifacts={name:dict(pin=dict(bytes=64,sha256='a'*64),owner=owners[0 if name.startswith('created')else 1],effect_semantics_qualified=False)
        for name in m.NAMES}
    for name,row in artifacts.items():
        if name.endswith('.bmp'):row['bitmap']=dict(depth=24,resolution=96,format='BMP',visual_semantics_qualified=False)
    trace=dict(schema_version='hwpx-agent.private.block-bookmark-source648-trace/v1',case_index=1,
        state='source_capture_returned_semantics_unqualified',error_code=None,cleanup_error=None,source_identity_preserved=True,
        input_leases_closed=True,block_content_support_qualified=False,P09_complete=False,artifacts=artifacts,
        sessions=[dict(process=v)for v in owners],block_ranges=[dict(case_index=c['case_index'],selection=c['selection'],
            action_returned=True,native_source_or_block_content_qualified=False)for c in m.planned_cases()])
    host=NS(schedule=NS(done=True,stopped=False),scope=NS(closed=True,current=None,pending_admission=False,
        sessions=[{},{}],finished=[dict(case_index=1,case_status='returned')]),source_case=None)
    reader=Reader();reader.json=lambda p:trace
    def pin(path):
        value=dict(path=path,bytes=64,sha256='a'*64);reader.snapshots[path]=value;return value
    reader.pin=pin
    return reader,host,trace

class Tests(unittest.TestCase):
    def test_parser_only_exact_inspect_or_execute(self):
        self.assertTrue(entry.parser().parse_args(['--inspect-only']).inspect_only)
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):entry.parser().parse_args(['--execute-source-once','--inspect-only'])
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):entry.parser().parse_args(['--execute'])
    def test_sections_fixed_order_no_retry(self):
        g=m.sections.guard_type(Guard)()
        with self.assertRaises(ValueError):g.advance('capture',lambda:True)
        self.assertTrue(g.section_failed)
        with self.assertRaises(ValueError):g.advance('qualification',lambda:True)
    def test_sections_closed_inputs_required(self):
        g=m.sections.guard_type(Guard)()
        with self.assertRaises(ValueError):g.advance('qualification',lambda:False)
        self.assertEqual(g.section_index,0)
    def test_sections_resource_failure_cannot_gain_budget(self):
        g=m.sections.guard_type(Guard)();g.denied=True
        with self.assertRaises(ValueError):g.advance('qualification',lambda:True)
        self.assertEqual(g.deadline,0);self.assertTrue(g.section_failed)
    def test_sections_keep_history_and_exact_completion(self):
        g=m.sections.guard_type(Guard)();g.samples.append({'model':1})
        for label in m.sections.SECTIONS[1:]:g.advance(label,lambda:True)
        g.complete(lambda:True);self.assertEqual(len(g.samples),1)
        self.assertFalse(g.section_summary()['Native_operation_timeout_changed'])
    def test_capture_producer_and_five_exact_pins_only(self):
        q,h,trace=artifact_fixture()
        with patch.object(m.prior.evidence,'producer')as producer:v=m.capture_metadata(q,h)
        producer.assert_called_once_with(trace,h.scope.sessions)
        self.assertFalse(v['actual_block_XML_mapping_qualified']);self.assertEqual(len(v['artifacts']),5)
        self.assertEqual(q.final_fresh_hashes,len(q.snapshots))
    def test_capture_missing_bool_range_or_positive_flag_denied(self):
        for change in('missing','bool','positive'):
            q,h,t=artifact_fixture()
            if change=='missing':t['block_ranges'].pop()
            elif change=='bool':t['block_ranges'][0]['case_index']=True
            else:t['block_content_support_qualified']=True
            with patch.object(m.prior.evidence,'producer'),self.assertRaises(ValueError):m.capture_metadata(q,h)
    def test_capture_changed_sha_or_wrong_producer_denied(self):
        for change in('sha','owner'):
            q,h,t=artifact_fixture();a=t['artifacts']['created.hwpx']
            if change=='sha':a['pin']['sha256']='b'*64
            else:a['owner']={'model_owner':2}
            with patch.object(m.prior.evidence,'producer'),self.assertRaises(ValueError):m.capture_metadata(q,h)
    def test_capture_live_or_partial_owner_not_promoted(self):
        q,h,t=artifact_fixture();h.scope.current=object()
        with self.assertRaises(ValueError):m.capture_metadata(q,h)
    def code_proof(self):
        paths=m.SOURCES|m.prior.prepared.loaded_dependencies(m.r.c.ROOT)|{entry.SELF}
        return dict(state=entry.STATE,cleanup=True,fresh_inputs=1,final_fresh_hashes=1,all_new_tests_passed=True,
            Native_started=False,whole_source_execution_qualified=False,execution_dependency_paths=sorted(paths),
            source_pins=[dict(path=p,bytes=1,sha256='0'*64)for p in paths])
    def test_changed_code_denied(self):
        p=self.code_proof();p['source_pins'][0]['sha256']='1'*64;q=Reader();q.json=lambda name:p
        with patch.object(entry.publisher.codec,'unpack',side_effect=lambda v:v),self.assertRaises(ValueError):entry.load_code(q)
    def test_bool_fresh_count_not_code_qualification(self):
        p=self.code_proof();p['fresh_inputs']=True;q=Reader();q.json=lambda name:p
        with patch.object(entry.publisher.codec,'unpack',side_effect=lambda v:v),self.assertRaises(ValueError):entry.load_code(q)
    def test_failed_qualification_never_constructs_capture_worker(self):
        guard=Guard();boundary=NS(source=Reader(),native_pin=Mock(),shell_pin=Mock())
        def fail(*args):args[-1].update(exit_code=2,cleanup=True);return {'state':'failed'}
        with patch.object(m,'absent'),patch.object(m.base.installed,'current_identity',return_value={}),patch.object(m.base,'Boundary',return_value=boundary),\
            patch.object(m.base.candidate,'SessionWorker'),patch.object(m.base.session,'SessionQualifier'),patch.object(m.prior.io,'run',side_effect=fail),\
            patch.object(m.worker_code,'Worker')as capture,self.assertRaises(ValueError):m.execute(guard,{},set(),{}, {},Mock(),{})
        capture.assert_not_called()
    def test_controller_success_branch_closes_boundaries_before_artifacts(self):
        class Boundary:
            def __init__(self,guard,manifest,paths,label,shell_expected,**kw):
                self.label=label;self.source=Reader();self.native_pin=Mock();self.shell_pin=Mock();self.fingerprint='0'*64;self.closed=False
            def finish(self):self.closed=True
            def summary(self):return dict(closed=self.closed,readers={k:dict(fresh_inputs=1,final_fresh_hashes=1)for k in('source','native','shell','runtime')})
        guard=Guard();hosts=[];handoff=NS(consumed=True)
        def host(*args,**kw):
            value=NS(scope=NS(closed=True),worker_lease=NS(closed=True),begin=args[7],end=args[8]);hosts.append(value);return value
        def run(*args):
            record=args[-1];record.update(exit_code=0,cleanup=True)
            if args[5]=='hwpx-agent.private.crossref-session-worker-result/v1':return {'state':'model_lifecycle'}
            hosts[0].begin(1);hosts[0].end(1);record['requests']=55
            return dict(state='block_source_callbacks_returned_semantics_unqualified',completed_callback_cases=1,planned_cases=1,
                planned_block_ranges=8,retained_live_or_uncertain_owners=0,block_content_support_qualified=False)
        with patch.object(m,'absent'),patch.object(m.base.installed,'current_identity',return_value={'same':True}),\
            patch.object(m.base,'Boundary',Boundary),patch.object(m.base.candidate,'SessionWorker'),patch.object(m.base.session,'SessionQualifier'),\
            patch.object(m.base.batch,'issue_handoff',return_value=handoff),patch.object(m.prior.io,'run',side_effect=run),\
            patch.object(m.worker_code,'Worker',return_value=NS(closed=True,start_fixed_worker=Mock())),\
            patch.object(m.host_code,'Host',side_effect=host),patch.object(m.r.a,'AcceptanceReader',Reader),\
            patch.object(m,'capture_metadata',return_value={'modeled':True})as artifacts:
            row={};self.assertEqual(m.execute(guard,{},set(),{}, {},Mock(),row),{'modeled':True})
        self.assertTrue(row['batch_closed_for_final_audit']);self.assertEqual(guard.events,['capture','batch_close'])
        self.assertEqual(len(row['case_source_boundaries']),1);self.assertTrue(row['capture_boundary']['closed']);artifacts.assert_called_once()
    def modeled_main(self,mode):
        guard=Guard();published=[];kept=[]
        shell_name=Path(m.base.candidate.original.SHELL).name
        proof=dict(worker_shell_pin=dict(path=shell_name,bytes=1,sha256='0'*64))
        with contextlib.ExitStack()as stack:
            stack.enter_context(patch.object(m.prior.prepared,'require_absent'))
            stack.enter_context(patch.object(m,'absent'))
            stack.enter_context(patch.object(m.r.tools,'select_own_single_cpu',return_value={}))
            stack.enter_context(patch.object(m.r.shared.host,'configure_host_policy'))
            stack.enter_context(patch.object(m.sections,'guard_type',return_value=lambda:guard))
            stack.enter_context(patch.object(m.r.a,'AcceptanceReader',side_effect=Reader))
            stack.enter_context(patch.object(entry,'load_code',return_value=({},set(),proof)))
            stack.enter_context(patch.object(m.prior.prepared.runtime,'require_qualification',return_value={}))
            stack.enter_context(patch.object(m.prior.prepared.runtime,'verify_current_reader'))
            stack.enter_context(patch.object(m.base.installed.prerequisites,'inspect',return_value=dict(all_observed_prerequisites_passed=False)))
            execute=stack.enter_context(patch.object(m,'execute'))
            def retain(root,path,row):kept.append(copy.deepcopy(row));return row,{}
            stack.enter_context(patch.object(entry.publisher.retention,'retain',side_effect=retain))
            def publish(path,value):published.append(path);return dict(path=path,bytes=1,sha256='0'*64)
            stack.enter_context(patch.object(entry.publisher,'publish',side_effect=publish))
            with contextlib.redirect_stdout(io.StringIO()):code=entry.main([mode])
            execute.assert_not_called()
        return code,published,kept[-1]
    def test_inspect_mode_no_claim_or_capture(self):
        code,published,row=self.modeled_main('--inspect-only')
        self.assertEqual(code,0);self.assertEqual(published,[entry.INSPECT]);self.assertFalse(row['native_claim_created'])
        self.assertFalse(row['source_capture_executed'])
    def test_denied_prerequisites_no_claim_or_capture(self):
        code,published,row=self.modeled_main('--execute-source-once')
        self.assertEqual(code,2);self.assertEqual(published,[entry.OUTPUT]);self.assertFalse(row['native_claim_created'])
        self.assertFalse(row['source_capture_executed'])

if __name__=='__main__':
    result=unittest.TestResult()
    selected=('test_controller_success_branch_closes_boundaries_before_artifacts','test_failed_qualification_never_constructs_capture_worker',
        'test_inspect_mode_no_claim_or_capture','test_denied_prerequisites_no_claim_or_capture')
    suite=unittest.TestSuite([Tests(n)for n in selected])if sys.argv[1:]==['--changed-fixture-paths-only']else unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    suite.run(result)
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),
        failed_tests=[t.id().rsplit('.',1)[-1]for t,_ in result.errors+result.failures],actual_native_started=False)))
    raise SystemExit(0 if result.wasSuccessful()else 2)
