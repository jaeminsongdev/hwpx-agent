from types import SimpleNamespace as NS
import copy
import sys
import unittest


class Tests(unittest.TestCase):
    def test_arguments_cannot_request_GO_or_native_and_are_exact_current_bootstrap(self):
        self.assertEqual(MODULE.original_arguments(1),["--bootstrap","--case","165","--run","8","--attempt","1","--code-attempt","2"])
        for value in (True,0,9,"1"):
            with self.assertRaises(ValueError):MODULE.original_arguments(value)

    def test_whole_original_main_invoked_once_with_original_argv_restored(self):
        calls=[];main=object();envelope=object();old=sys.argv
        def execute(fn,proxy):calls.append((fn,proxy,list(sys.argv)));return 0
        def connect(*args,**kwargs):calls.append(kwargs);return NS(main=main,envelope=envelope,execute=execute)
        self.assertEqual(MODULE.invoke(NS(connect=connect),"root","input-envelope","a","delivery",2),0)
        self.assertEqual(calls[0],dict(require_code=True,role="graph"));self.assertIs(calls[1][0],main);self.assertIs(calls[1][1],envelope)
        self.assertEqual(calls[1][2],[MODULE.PROFILE["path"]]+MODULE.original_arguments(2));self.assertIs(sys.argv,old)

    def test_original_failure_is_not_suppressed_and_argv_always_restored(self):
        old=sys.argv
        def failed(*args):raise ValueError("ORIGINAL_FACTORY_FAILURE")
        profile=NS(connect=lambda *args,**kwargs:NS(main=object(),envelope=object(),execute=failed))
        with self.assertRaisesRegex(ValueError,"ORIGINAL_FACTORY_FAILURE"):MODULE.invoke(profile,"root","e","a","d",1)
        self.assertIs(sys.argv,old)

    def receipt(self):
        return dict(state="PASS_WORKER_CLI_NO_GO_STARTUP_NOT_PARENT_ADMISSION_NATIVE_OR_PRODUCT",index=165,
            contracts=dict(run=11,errors=0,failures=0,skipped=0),accepted_count_delta=0,product_or_Native_executed=False,
            GO_authorized=False,cleanup_confirmed=True,actual_parent_and_worker_dispatch_counts=dict(parent=0,worker=0),
            owned_worker_cli_startup_connected=True,full_current_parent_admission_deferred_to_whole_preflight=True,
            fresh_inputs=1,final_fresh_hashes=1,worker_cli_NO_GO_rejection=dict(exit_code=1,original_GO_rejection_observed=True,
                historical_runtime_or_authority_opens=0,GO_sent=False,product_child_execution_authorized=False,full_worker_product_qualification=False))

    def test_real_no_go_receipt_is_not_runtime_admission(self):
        record=self.receipt();before=copy.deepcopy(record);MODULE.check_factory(record,ACCEPTANCE);self.assertEqual(record,before)

    def test_exit_zero_missing_GO_rejection_or_historical_open_is_rejected(self):
        for key,value in (("exit_code",0),("exit_code",True),("historical_runtime_or_authority_opens",1),("original_GO_rejection_observed",False),("GO_sent",True)):
            record=self.receipt();record["worker_cli_NO_GO_rejection"][key]=value
            with self.assertRaises(ValueError):MODULE.check_factory(record,ACCEPTANCE)

    def test_product_dispatch_or_unclosed_source_is_rejected(self):
        for key,value in (("GO_authorized",True),("product_or_Native_executed",True),("cleanup_confirmed",False),("final_fresh_hashes",0)):
            record=self.receipt();record[key]=value
            with self.assertRaises(ValueError):MODULE.check_factory(record,ACCEPTANCE)
        record=self.receipt();record["actual_parent_and_worker_dispatch_counts"]["worker"]=1
        with self.assertRaises(ValueError):MODULE.check_factory(record,ACCEPTANCE)

    def test_whole_engine_not_only_a_mock_probe_contract_is_required(self):
        record=self.receipt();record["contracts"]["run"]=10
        with self.assertRaises(ValueError):MODULE.check_factory(record,ACCEPTANCE)

    def test_original_fixed_task_and_readonly_source_context_remain(self):
        record=self.receipt();record["index"]=166
        with self.assertRaises(ValueError):MODULE.check_factory(record,ACCEPTANCE)
        self.assertEqual(MODULE.PROFILE["bytes"],21098);self.assertIn("successor-connections008.v17",MODULE.GRAPH)
