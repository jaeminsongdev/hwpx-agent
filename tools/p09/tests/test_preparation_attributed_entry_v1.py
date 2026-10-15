import copy
import sys
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
import accept_case112_current_epoch as a
from tests.test_preparation_attributed_cpu_v1 import Original

MODULE=None
POLICY=None
ENTRY_MODULE=None
ENVELOPE=None


def arguments(mode="--preflight"):
    args=["--case","165","--run","8","--attempt","5","--code-attempt","1",mode]
    if mode=="--qualify":args +=["--preflight-attempt","5"]
    return args


def old_fixture():
    pressure=NS(guard_type=lambda base:("original",base),summary=lambda guard:None)
    return NS(base=NS(FIRST=NS(terminal_metadata_pressure_v1=pressure)),old=NS(token=object()))


class Tests(unittest.TestCase):
    def test_only_two_explicit_preparation_contexts(self):
        self.assertEqual(MODULE.context(arguments()).role,"whole_metadata_preflight")
        self.assertEqual(MODULE.context(arguments("--qualify")).role,"dispatch_construction")

    def test_explicit_connection_receipts_are_bounded_and_reach_every_reader(self):
        for value in (None,True,0,9,"3"):
            with self.assertRaises(ValueError):MODULE.connection_path(value)
        self.assertEqual(MODULE.connection_path(3),MODULE.PREFIX+"preparation-attributed-connection-code003.v1.json")
        calls=[]
        class Reader:pass
        entry=NS(load=lambda root,api:api)
        loader=NS(load=lambda *args,**kwargs:(NS(closed_prebody_factory_admission_fix_v1=entry),[]))
        routed=MODULE.route_loader(None,loader,POLICY,a,"whole_metadata_preflight",[],connection_attempt=3)
        with patch.dict(MODULE.witnesses.__globals__,witnesses=lambda *args,**kwargs:calls.append(kwargs)):
            modules,_=routed.load();api=modules.closed_prebody_factory_admission_fix_v1.load(None,NS(AcceptanceReader=Reader));api.AcceptanceReader()
        self.assertEqual(calls,[dict(connection=True,connection_attempt=3)])

    def test_native_worker_product_and_accept_flags_are_all_rejected(self):
        for flag in ("--native","--native=true","--owned-worker","--task","--review","--accept","--graph","--bootstrap","--code"):
            with self.subTest(flag=flag),self.assertRaises(ValueError):MODULE.context(arguments()+[flag])

    def test_wrong_case_run_duplicate_or_unqualified_code_is_rejected(self):
        for flag,value in (("--case","166"),("--run","7"),("--attempt","9"),("--code-attempt","2")):
            args=arguments();args[args.index(flag)+1]=value
            with self.subTest(flag=flag),self.assertRaises(ValueError):MODULE.context(args)
        for args in (arguments()+["--case","165"],arguments()+["--qualify"],arguments("--qualify")[:-1]):
            with self.assertRaises(ValueError):MODULE.context(args)

    def test_private_facade_registers_actual_guard_without_mutating_original(self):
        old=old_fixture().base.FIRST.terminal_metadata_pressure_v1;original=old.guard_type;instances=[]
        new=MODULE.pressure_facade(old,POLICY,"whole_metadata_preflight",instances)
        g=new.guard_type(Original)();g.row=dict(system_cpu_percent=80,parent_cpu_machine_percent=.1)
        g.check();self.assertEqual(instances,[g]);self.assertFalse(g.preparation_CPU.stopped)
        self.assertIs(old.guard_type,original);self.assertEqual(old.guard_type(Original),("original",Original))

    def test_old_base_is_copied_and_native_template_alias_is_retained(self):
        old=old_fixture();first=old.base.FIRST
        new=MODULE.connect_old(old,POLICY,"dispatch_construction",[])
        self.assertIs(old.base.FIRST,first);self.assertIs(new.old,old.old)
        self.assertIsNot(new.base,old.base);self.assertIsNot(new.base.FIRST,first)

    def test_loader_routes_only_fresh_old_namespace_family(self):
        old=old_fixture();env=dict(__name__="p09_exact_fixture_old",base=old.base)
        exec("def f():return base",env);old.__name__=env["__name__"];old.f=env["f"]
        initial=old.base;modules=NS(case160_run007_controller=old)
        loader=NS(load=lambda *args,**kwargs:(modules,["original-proof"]))
        routed=MODULE.route_loader(None,loader,POLICY,a,"whole_metadata_preflight",[])
        actual,proof=routed.load()
        self.assertEqual(proof,["original-proof"]);self.assertIs(actual.case160_run007_controller.f(),old.base)
        self.assertIsNot(old.base,initial);self.assertIsNot(old.base.FIRST,initial.FIRST)

    def test_execute_retains_whole_entry_code_and_restores_argv(self):
        def main():
            import flat_current_queue_envelope_runtime_v25 as e
            return e.token,tuple(sys.argv)
        entry=NS(main=main);before=main.__code__;argv=sys.argv
        result=MODULE.execute(entry,NS(token="private"),arguments())
        self.assertEqual(result[0],"private");self.assertEqual(result[1][1:],tuple(arguments()))
        self.assertIs(main.__code__,before);self.assertIs(sys.argv,argv)

    def test_reader_witness_is_mandatory_not_only_a_loader_comment(self):
        calls=[]
        class Reader:
            def __init__(self,*args,**kwargs):self.created=True
        def entry_load(root,api):return NS(api=api)
        entry=NS(load=entry_load);modules=NS(closed_prebody_factory_admission_fix_v1=entry)
        loader=NS(load=lambda *args,**kwargs:(modules,[]))
        routed=MODULE.route_loader(None,loader,POLICY,a,"whole_metadata_preflight",[])
        with patch.dict(MODULE.witnesses.__globals__,witnesses=lambda *args,**kwargs:calls.append(kwargs)):
            actual,_=routed.load();linked=actual.closed_prebody_factory_admission_fix_v1.load(None,NS(AcceptanceReader=Reader))
            linked.api.AcceptanceReader()
        self.assertEqual(calls,[dict(connection=True,connection_attempt=None)])

    def test_invalid_or_unclosed_qualification_cannot_be_reused(self):
        pin=dict(path="tools/p09/public.py",bytes=1,sha256="a"*64)
        good=dict(state="EXPECTED",cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,
            fresh_inputs=1,final_fresh_hashes=1,source_pins=[pin])
        for key,value in (("state","OTHER"),("fresh_inputs",True),("final_fresh_hashes",0),("cleanup_confirmed",False),("GO_authorized",True)):
            q=NS(json=lambda path,row=dict(good,**{key:value}):row,pin=lambda path:pin)
            with self.subTest(key=key),self.assertRaises(ValueError):MODULE.closure(q,"public", "EXPECTED",a)

    def audit_fixture(self):
        target=MODULE.PREFIX+"successor-recovery-preflight-run008-attempt005.v1.json"
        pin=dict(path=target,bytes=1,sha256="a"*64)
        row=dict(state="RECORDED_PREPARATION_CPU_POLICY_NOT_NATIVE_OR_ACCEPTANCE",stage="preflight",
            original_stage_exit_code=0,accepted_count_delta=0,GO_authorized=False,actual_Native_or_product_executed=False,
            Native008_absent_before_after=True,cleanup_confirmed=True,original_stage_record_pin=pin,
            bootstrap_fresh_inputs=1,bootstrap_final_fresh_hashes=1,bootstrap_source_pins=[pin],
            guard_summaries=[dict(profile=POLICY.PROFILE,role="whole_metadata_preflight",policy=POLICY.POLICY,
                stopped=False,Native_policy_changed=False,GO_authorized=False,original_hard_guard_and_RAM_commit_deadline_required=True)])
        return row,pin

    def test_typed_audit_requires_correct_target_success_and_all_guard_cleanup(self):
        good,pin=self.audit_fixture()
        for key,value in (("original_stage_exit_code",1),("cleanup_confirmed",False),("actual_Native_or_product_executed",True),
            ("bootstrap_final_fresh_hashes",0),("guard_summaries",[])):
            row=copy.deepcopy(good);row[key]=value;q=NS(json=lambda path:row,pin=lambda path:pin)
            with self.subTest(key=key),self.assertRaises(ValueError):MODULE.preflight_audit(q,a,POLICY,5)
        q=NS(json=lambda path:good,pin=lambda path:pin)
        MODULE.preflight_audit(q,a,POLICY,5)

    def test_audit_cannot_hide_stopped_native_policy_or_changed_record(self):
        good,pin=self.audit_fixture()
        for key,value in (("stopped",True),("Native_policy_changed",True),("profile","OTHER")):
            row=copy.deepcopy(good);row["guard_summaries"][0][key]=value
            with self.assertRaises(ValueError):MODULE.preflight_audit(NS(json=lambda path:row,pin=lambda path:pin),a,POLICY,5)
        with self.assertRaises(ValueError):MODULE.preflight_audit(NS(json=lambda path:good,pin=lambda path:dict(pin,bytes=2)),a,POLICY,5)

    def test_actual_frozen_constructor_keeps_window10_and_preparation_only_guard(self):
        original=ENVELOPE.namespace_bundle;seen=[];instances=[]
        def load(*args,**kwargs):
            modules,proof=original.load(*args,**kwargs)
            controller=getattr(modules,"current_queue_successor_controller",None)
            if controller is not None:
                def endpoint(index,run,attempt):
                    fn=controller.destination
                    imported=fn.__builtins__["__import__"]("case160_run007_controller",fn.__globals__,None,(),0)
                    self.assertEqual(imported.old.prior.WINDOW.SECONDS,10)
                    g=imported.base.FIRST.terminal_metadata_pressure_v1.guard_type(Original)()
                    self.assertEqual(g.preparation_CPU.role,"whole_metadata_preflight")
                    self.assertIn("-successor-recovery-code-",controller.destination(index,run,"code",attempt))
                    seen.append(True);return 0
                controller.run_code=endpoint
            return modules,proof
        base=NS(**{**vars(original),"load":load})
        routed=MODULE.route_loader(a.c.ROOT,base,POLICY,a,"whole_metadata_preflight",instances,require_connection=False,envelope=ENVELOPE)
        envelope=NS(**{**vars(ENVELOPE),"namespace_bundle":routed})
        with patch("subprocess.Popen",side_effect=AssertionError("NO_NATIVE_OR_CHILD")), \
                patch("subprocess.run",side_effect=AssertionError("NO_NATIVE_OR_CHILD")):
            result=MODULE.execute(ENTRY_MODULE,envelope,["--case","165","--run","8","--attempt","1","--code"])
        self.assertEqual(result,0);self.assertEqual(seen,[True]);self.assertEqual(len(instances),1)
