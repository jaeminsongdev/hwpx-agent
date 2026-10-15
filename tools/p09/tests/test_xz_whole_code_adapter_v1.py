from types import SimpleNamespace as NS
import copy
import sys
import unittest


class Tests(unittest.TestCase):
    def fixture(self):return dict(state="PASS_CURRENT_SUCCESSOR_CODE_NOT_FULL_PREFLIGHT_NATIVE_OR_PRODUCT",index=165,physical_run=8,
        contracts=dict(run=74,errors=0,failures=0,skipped=0),cleanup_confirmed=True,accepted_count_delta=0,product_or_Native_executed=False,
        GO_authorized=False,runtime_imported_helper_bound=64,runtime_default_import_count=64,fresh_inputs=1,final_fresh_hashes=1,
        new_runtime_process_required_before_preflight_or_Native=True,independent_checker_source_and_controller_contracts_included=True)

    def test_original_code_arguments_only_current165_run8(self):
        self.assertEqual(MODULE.arguments(5),["--code","--case","165","--run","8","--attempt","5"])
        for value in (True,0,9,"5"):
            with self.assertRaises(ValueError):MODULE.arguments(value)

    def test_entire_original_main_called_and_argv_restored(self):
        old=sys.argv;calls=[];main=object();proxy=object()
        def execute(fn,envelope):calls.append((fn,envelope,list(sys.argv)));return 0
        def connect(*args,**kwargs):self.assertEqual(kwargs,dict(require_code=True,role="graph"));return NS(main=main,envelope=proxy,execute=execute)
        self.assertEqual(MODULE.invoke(NS(connect=connect,SELF="profile"),"root","e","a","d",5),0)
        self.assertIs(calls[0][0],main);self.assertIs(calls[0][1],proxy);self.assertEqual(calls[0][2],["profile"]+MODULE.arguments(5));self.assertIs(sys.argv,old)

    def test_original_error_is_not_skipped_or_relabelled(self):
        old=sys.argv
        def fail(*args):raise ValueError("ORIGINAL_CODE_STOP")
        with self.assertRaisesRegex(ValueError,"ORIGINAL_CODE_STOP"):MODULE.invoke(NS(SELF="profile",connect=lambda *a,**k:NS(main=None,envelope=None,execute=fail)),"root","e","a","d",5)
        self.assertIs(sys.argv,old)

    def test_all74_and_original_helper64_required(self):
        value=self.fixture();MODULE.validate(value,ACCEPTANCE)
        for field,new in (("runtime_default_import_count",65),("runtime_default_import_count",True),("runtime_imported_helper_bound",65)):
            bad=copy.deepcopy(value);bad[field]=new
            with self.assertRaises(ValueError):MODULE.validate(bad,ACCEPTANCE)
        bad=copy.deepcopy(value);bad["contracts"]["run"]=73
        with self.assertRaises(ValueError):MODULE.validate(bad,ACCEPTANCE)

    def test_source_failure_or_runtime_authorization_not_CODE_pass(self):
        for field,new in (("cleanup_confirmed",False),("final_fresh_hashes",0),("GO_authorized",True),("product_or_Native_executed",True)):
            bad=self.fixture();bad[field]=new
            with self.assertRaises(ValueError):MODULE.validate(bad,ACCEPTANCE)

    def test_current_context_and_independent_checker_cannot_be_omitted(self):
        for field,new in (("index",166),("physical_run",7),("independent_checker_source_and_controller_contracts_included",False),("new_runtime_process_required_before_preflight_or_Native",False)):
            bad=self.fixture();bad[field]=new
            with self.assertRaises(ValueError):MODULE.validate(bad,ACCEPTANCE)
