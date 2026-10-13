"""부모 경량worker 연결 계약. 실제 Job/제품 실행은 actual receipt로 따로 입증한다."""
import copy
import unittest
from unittest.mock import patch
import run_minimal_runtime_r07_case as x


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.controller={name:dict(path=name,bytes=1,sha256='a'*64) for name in x.CONTROLLERS}
        self.controller[x.m.SELF]=dict(x.WORKER_PIN);self.controller[x.m.TEST]=dict(x.WORKER_TEST_PIN)
        self.case=dict(state=x.v.CASE_PASS,task='p204-r07-case-011-tests',
            original_parent_task_before_minimal_worker='p191-r07-case-011-tests',minimal_owned_worker_path=x.m.SELF,
            minimal_worker_source_only_import_connected=True,original_parent_guard_and_full_runtime_fresh_scope_retained=True,
            actual_job_membership_checked=True,owned_limits_verified=True,job_assigned=True,writer_authorized=True,
            cleanup_confirmed=True,owned_tree_empty=True,runtime_resume_controller_input_pins=list(self.controller.values()))

    def test_original_task_maps_exactly_one(self):
        self.assertEqual(x.worker_task('p191-r07-case-011-tests'),'p204-r07-case-011-tests')

    def test_invalid_task_range_or_other_generation_rejected(self):
        for task in ('p191-r07-case-000-tests','p191-r07-case-250-tests','p191-r07-case-11-tests','p205-r07-case-011-tests'):
            with self.assertRaises(ValueError):x.worker_task(task)

    def test_original_parent_run_receives_minimal_path_task_and_same_budget(self):
        seen=[]
        def called(task,receipt,seconds):seen.append((task,receipt,seconds,x.c.__file__,x.c.TASKS));return 7
        with patch.object(x.c,'TASKS',{'p191-r07-case-011-tests':x.m.TASK_ARGS}), \
                patch.object(x.c,'TARGET',x.m.TARGET),patch.object(x,'ORIGINAL_RUN',called):
            self.assertEqual(x.owned_run('p191-r07-case-011-tests','receipt',1200),7)
        task,receipt,seconds,path,tasks=seen[0]
        self.assertEqual((task,receipt,seconds),('p204-r07-case-011-tests','receipt',1200))
        self.assertEqual(path,str(x.c.ROOT/x.m.SELF));self.assertEqual(tasks,{task:x.m.TASK_ARGS})

    def test_budget_extension_or_target_drift_rejected_before_run(self):
        with patch.object(x,'ORIGINAL_RUN',side_effect=AssertionError('NO_RUN')):
            for seconds in (1201,True,1200.0):
                with self.assertRaises(ValueError):x.owned_run('p191-r07-case-011-tests','receipt',seconds)
            with patch.object(x.c,'TASKS',{}):
                with self.assertRaises(ValueError):x.owned_run('p191-r07-case-011-tests','receipt',1200)

    def test_parent_file_tasks_restored_after_failure(self):
        original_file=x.c.__file__
        tasks={'p191-r07-case-011-tests':x.m.TASK_ARGS}
        with patch.object(x.c,'TASKS',tasks),patch.object(x.c,'TARGET',x.m.TARGET), \
                patch.object(x,'ORIGINAL_RUN',side_effect=RuntimeError('MOCK_FAIL')):
            with self.assertRaises(RuntimeError):x.owned_run('p191-r07-case-011-tests','receipt',1200)
            self.assertIs(x.c.TASKS,tasks);self.assertEqual(x.c.__file__,original_file)

    def test_actual_bridge_scope_accepted(self):
        self.assertEqual(x.case_controller(self.case,self.controller),self.controller)

    def test_current_helper_drift_rejected(self):
        current=copy.deepcopy(self.controller);current[x.SELF]['sha256']='b'*64
        with self.assertRaises(ValueError):x.case_controller(self.case,current)

    def test_partial_new_controller_set_rejected(self):
        self.case['runtime_resume_controller_input_pins'].pop()
        with self.assertRaises(ValueError):x.case_controller(self.case,self.controller)

    def test_connection_or_actual_ownership_missing_rejected(self):
        for key in ('minimal_worker_source_only_import_connected','original_parent_guard_and_full_runtime_fresh_scope_retained',
                    'actual_job_membership_checked','owned_limits_verified','job_assigned','writer_authorized','cleanup_confirmed','owned_tree_empty'):
            case=dict(self.case,**{key:False})
            with self.assertRaises(ValueError):x.validate_bridge(case,self.controller)

    def test_frozen_legacy_generation_uses_original_validator(self):
        names=x.j.s.CONTROLLERS
        old={name:self.controller[name] for name in names}
        case=dict(runtime_resume_controller_input_pins=list(old.values()))
        self.assertEqual(x.case_controller(case,self.controller),old)


if __name__=='__main__':unittest.main()
