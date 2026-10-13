"""Guarded current113 projection/binding/original-worker contracts only."""
import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_current_queue_native as r

CHECKPOINT=lambda:None


class QueueNativeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=r.accepted112.AcceptanceReader(r.c.ROOT,CHECKPOINT)
        cls.required,cls.rust=r.binding(cls.q)
        cls.source=cls.q.text(r.TEMPLATE_PIN["path"]).encode("utf-8")
        # The template is CRLF in the preserved Windows file. Reader.text applies
        # universal newlines; compile/projection must bind the ORIGINAL raw bytes.
        with (r.c.ROOT/r.TEMPLATE_PIN["path"]).open("rb") as stream:
            cls.source=stream.read(r.TEMPLATE_PIN["bytes"]+1)
        cls.engine,cls.proof=r.projection(cls.source)
        cls.terminal=cls.engine.terminal_api(cls.q)
    @classmethod
    def tearDownClass(cls):cls.q.finish()
    def test_original1710_and_current787_not_single_fixture_scope(self):
        self.assertEqual(len(self.required),1710);self.assertEqual(len(self.rust),787)
        self.assertEqual(self.required[r.scope.EXE_PIN["path"]],r.scope.EXE_PIN)
        for p in r.scope.ARCHIVES:self.assertEqual(self.required[p["path"]],p)
    def test_exact_metadata_projection_preserves_every_safety_statement(self):
        self.assertEqual(self.proof["metadata_only_literals"],dict(index=3,before=1,path=1,schema=1))
        self.assertTrue(self.proof["original_engine_AST_restored_exactly"])
        self.assertFalse(self.proof["Native_byte_GO_Job_resource_cleanup_statements_replaced"])
    def test_modified_template_cannot_compile(self):
        for raw in (self.source[:-1],self.source.replace(b"+720",b"+721")):
            with self.subTest(),self.assertRaises(ValueError):r.projection(raw)
    def test_next113_exact_name_and_original_terminal_summary(self):
        output="running 1 test\ntest "+r.CASE+" ... ok\n\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 248 filtered out; finished in 0.01s\n"
        self.assertEqual(self.terminal.terminal(output,"",r.CASE)["passed"],1)
        for bad in (output.replace(r.CASE,r.scope.CASE112),output.replace("248 filtered","247 filtered"),output.replace("1 passed","2 passed")):
            with self.subTest(),self.assertRaises(ValueError):self.terminal.terminal(bad,"",r.CASE)
        self.assertEqual(self.terminal.arguments(r.CASE),r.arguments())
    def test_task_input_fail_closed(self):
        for run in (True,0,1000,"1"):
            with self.subTest(),self.assertRaises(ValueError):r.task_for(run)
        for task in ("case112-current-r001-tests","case113-current-r000-tests","case113-current-r001"):
            with self.subTest(),self.assertRaises(ValueError):r.run_for(task)
    def patches(self,go=True,job=True):
        def member(process,owned,pointer):pointer._obj.value=job;return True
        return (patch.object(r.c,"Windows",return_value=NS(k=NS(GetCurrentProcess=lambda:17,IsProcessInJob=member))),
            patch.object(r.c.sys,"stdin",io.StringIO("P149_GO\n" if go else "BAD\n")),
            patch.object(r.c.shutil,"which",return_value="fake-cargo"),patch.object(r.prior.build,"direct_path"))
    def test_actual_original_worker_exact113_go_job_threads_assertions(self):
        p1,p2,p3,p4=self.patches()
        with p1,p2,p3,p4,patch.object(r.subprocess,"call",return_value=0) as call:
            self.assertEqual(self.engine.worker(r.task_for(999)),0)
        self.assertEqual(call.call_args.args[0],[str(r.c.ROOT/r.scope.EXE_PIN["path"]),*r.arguments()])
        self.assertEqual(call.call_args.kwargs["env"]["RUST_TEST_THREADS"],"1")
        self.assertEqual(call.call_args.kwargs["env"]["CARGO_PROFILE_TEST_DEBUG_ASSERTIONS"],"true")
        self.assertEqual(call.call_args.kwargs["env"]["CARGO_PROFILE_TEST_OVERFLOW_CHECKS"],"true")
    def test_original_go_and_job_membership_cannot_be_bypassed(self):
        for go,job in ((False,True),(True,False)):
            p1,p2,p3,p4=self.patches(go,job)
            with p1,p2,p3,p4,patch.object(r.subprocess,"call") as call:
                with self.assertRaises(ValueError):self.engine.worker(r.task_for(998))
            call.assert_not_called()
    def test_original_capture_failure_serializes_candidate_not_queue(self):
        stream=io.StringIO()
        def fake_run(task,destination,maximum):
            self.assertIn("case113-current-runtime-run997",str(destination));self.assertEqual(maximum,1200)
            process=NS(stdin=io.BytesIO(),stdout=io.BytesIO(b""),stderr=io.BytesIO(b""),returncode=1,wait=lambda timeout:1)
            from bounded_process_progress import BoundedProcessCapture
            cap=BoundedProcessCapture(process);cap.communicate(1);cap.close()
            json.dump(dict(state="STOPPED_NOT_ACCEPTED",writer_authorized=True,cleanup_confirmed=True,
                owned_tree_empty=True,job_final=dict(active_processes=0,owned_processes=[]),stop_reason="OWNED_COMMAND_FAILED"),stream)
            return 2
        with patch.object(r.c,"run",side_effect=fake_run):self.assertEqual(self.engine.run_owned(997),2)
        row=json.loads(stream.getvalue())
        self.assertEqual(row["selected_test_index"],113);self.assertEqual(row["prior_queue_cases"],106)
        self.assertEqual(row["next_case"],113);self.assertEqual(row["accepted_count_delta"],0)
        self.assertEqual(row["schema_version"],r.SCHEMA);self.assertFalse(row["Native_source_frame_qualified"])
        self.assertTrue(row["capture_diagnostics"]["complete_streams"])
        self.assertEqual(row["selected_test_names"],[r.CASE])
    def test_current_closure_extra_input_cost_is_charged(self):
        required=r.scope.extend(self.required,self.q.snapshots)
        for name in (r.SELF,r.TEST):
            self.q.pin(name);required=r.scope.extend(required,self.q.snapshots)
        model=r.prior.runtime_budget(required,167)
        self.assertEqual(model["selected_acquisition_rate_per_second"],14)
        self.assertLess(model["predicted_runtime_combined_seconds"],600)
        self.assertGreater(model["predicted_runtime_combined_seconds"],589.4411743981498)
    def test_prior106_must_be_actual_acceptance_not_112_candidate(self):
        real=self.q.json
        def changed(name):
            row=real(name)
            if name==r.PRIOR_ACCEPT_PIN["path"]:row=copy.deepcopy(row);row["accepted_count_delta"]=0
            return row
        with patch.object(self.q,"json",side_effect=changed),self.assertRaises(ValueError):r.binding(self.q)
    def test_passed_or_unresolved_previous_body_not_replayed(self):
        for row in (dict(product_body_observed=True,passed_test_names=[r.CASE]),
            dict(product_body_observed=False,passed_test_names=[],cleanup_confirmed=False),{}):
            q=NS(json=lambda _:row)
            with self.subTest(),self.assertRaisesRegex(ValueError,"NOT_REPLAYED"):r.binding_attempt(q,2)
    def test_clean_pre_worker_stop_may_bind_new_attempt_without_old_body_replay(self):
        q=NS(json=lambda _:dict(product_body_observed=False,passed_test_names=[],
            current_generation_runtime_candidate_qualified=False,cleanup_confirmed=True,owned_tree_empty=True),
            snapshots={r.FAILED001_PIN['path']:r.FAILED001_PIN},pin=lambda name:
                next(p for p in r.FAILED001_CODE if p['path']==name))
        with patch.object(r,"binding",return_value=("required","rust")) as called:
            self.assertEqual(r.binding_attempt(q,2),("required","rust"));called.assert_called_once_with(q)


if __name__=="__main__":
    guard=r.accepted112.Guard();result=None
    try:
        guard.acquire();CHECKPOINT=guard.check
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(QueueNativeContracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        samples=len(guard.samples),cleanup_confirmed=guard.cleanup,product_child_executed=False)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
