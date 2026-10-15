from types import SimpleNamespace as NS,FunctionType
from unittest.mock import patch
import unittest
import accept_case112_current_epoch as a

MODULE=ENTRY=POLICY=ORIGINAL=ENVELOPE=COMPONENTS=None


def native_args():
    return ["--case","165","--run","8","--attempt","1","--code-attempt","1",
        "--preflight-attempt","6","--qualification-attempt","2","--native"]


class Tests(unittest.TestCase):
    def test_native_context_rejects_other_cases_workers_modes_and_duplicate_flags(self):
        self.assertEqual(MODULE.native_context(native_args())["--run"],8)
        for flag,value in (("--case","164"),("--run","7"),("--code-attempt","2"),("--attempt","9")):
            args=native_args();args[args.index(flag)+1]=value
            with self.assertRaises(ValueError):MODULE.native_context(args)
        for args in (native_args()+["--case","165"],native_args()[:-1]+["--qualify"],native_args()[:-1]+["--owned-worker"]):
            with self.assertRaises(ValueError):MODULE.native_context(args)

    def test_unrelated_loader_graph_is_not_given_a_different_window(self):
        old=NS(__name__="p09_exact_case160_run007_controller",base=object(),old=object())
        modules=NS(case160_run007_controller=old);calls=[]
        original=NS(load=lambda *args,**kwargs:(modules,["proof"]))
        recovery=NS(prior_alias=lambda *args:calls.append(args))
        routed,seen=MODULE.connect_loader(original,NS(),recovery,None,None,lambda *args:None)
        actual,proof=routed.load(None,[dict(path="different.py")],{})
        self.assertIs(actual.case160_run007_controller,old);self.assertEqual(proof,["proof"])
        self.assertEqual(calls,[]);self.assertEqual(seen,[])

    def test_exact_fresh_load_retains_resource_guard_and_original_default(self):
        old=NS(__name__="p09_exact_case160_run007_controller",base=object(),old=NS(prior=NS(WINDOW=NS(SECONDS=15))))
        original=NS(load=lambda *args,**kwargs:(NS(case160_run007_controller=old),["whole-source"]))
        def prior_alias(value,*args):
            return NS(**{**vars(value),"old":NS(prior=NS(WINDOW=NS(SECONDS=10)))}),dict(connected=True)
        routed,seen=MODULE.connect_loader(original,NS(),NS(prior_alias=prior_alias),None,None,lambda *args:None)
        envelope=NS(namespace_bundle=original)
        actual,proof=routed.dispatch_load(envelope,None,[MODULE.CONTROLLER_PIN],{"flat_current_queue_envelope_runtime_v25":NS()})
        self.assertEqual(actual.case160_run007_controller.old.prior.WINDOW.SECONDS,10)
        self.assertIs(actual.case160_run007_controller.base,old.base)
        self.assertEqual(old.old.prior.WINDOW.SECONDS,15);self.assertEqual(proof,["whole-source"])
        self.assertEqual(seen,[dict(connected=True)])
        with self.assertRaises(ValueError):routed.dispatch_load(envelope,None,[MODULE.CONTROLLER_PIN],{})

    def test_source_witness_runs_on_each_actual_reader_without_cpu_substitution(self):
        calls=[]
        class Reader:pass
        api=NS(AcceptanceReader=Reader)
        entry=NS(load=lambda root,actual:actual)
        modules=NS(closed_prebody_factory_admission_fix_v1=entry)
        routed,_=MODULE.connect_loader(NS(load=lambda *args,**kwargs:(modules,[])),NS(),None,None,None,
            lambda *args:None,witness=lambda q:calls.append(q))
        modules,_=routed.load(None,[],{});actual=modules.closed_prebody_factory_admission_fix_v1.load(None,api)
        first=actual.AcceptanceReader();second=actual.AcceptanceReader()
        self.assertEqual(calls,[first,second]);self.assertIs(api.AcceptanceReader,Reader)

    def test_actual_frozen_dispatch_reload_keeps_window10_before_any_stage_or_child(self):
        observed={}
        instances=[]
        class InspectionComplete(BaseException):pass
        def load(*args,**kwargs):
            modules,proof=ENVELOPE.namespace_bundle.load(*args,**kwargs)
            controller=getattr(modules,"current_queue_successor_controller",None)
            dispatch=getattr(modules,"current_queue_successor_dispatch",None)
            if controller is not None and dispatch is not None:
                def endpoint(index,run,attempt):
                    original=dispatch.main;imp=original.__builtins__["__import__"]
                    reload=original.__globals__["_recovery_dispatch_reload"]
                    def fresh(*args,**kwargs):
                        ns,proof=reload(*args,**kwargs)
                        old=ns.case160_run007_controller
                        observed["fresh"]=old.old.prior.WINDOW.SECONDS
                        observed["model"]=old.old.prior.DIRECT.runtime_budget.__globals__["views"]
                        observed["same"]=old.old.prior.template.__globals__["DIRECT"] is old.old.prior.DIRECT
                        from tests.test_preparation_attributed_cpu_v1 import Original
                        guard=old.base.FIRST.terminal_metadata_pressure_v1.guard_type(Original)()
                        observed["preparation_role"]=guard.preparation_CPU.role
                        guard.close()
                        raise InspectionComplete()
                    fn=FunctionType(original.__code__,dict(original.__globals__,_recovery_dispatch_reload=fresh),argdefs=original.__defaults__,closure=original.__closure__)
                    fn.__kwdefaults__=original.__kwdefaults__
                    alias=imp("case160_run007_controller",original.__globals__,None,(),0)
                    observed["outer"]=alias.old.prior.WINDOW.SECONDS
                    return fn(NS(),True)
                controller.run_code=endpoint
            return modules,proof
        base=NS(**{**vars(ENVELOPE.namespace_bundle),"load":load})
        routed=ENTRY.route_loader(a.c.ROOT,base,POLICY,a,"whole_metadata_preflight",[],require_connection=False,envelope=ENVELOPE)
        window=COMPONENTS.post_product_recovery_window_v1
        routed,seen=MODULE.connect_loader(routed,ENVELOPE,COMPONENTS.post_product_recovery_connection_v1,window,
            (a.c.ROOT/window.WINDOW_PIN["path"]).read_bytes(),ENTRY.bind_envelope,
            controller_transform=lambda old:ENTRY.connect_old(old,POLICY,"dispatch_construction",instances))
        proxy=NS(**{**vars(ENVELOPE),"namespace_bundle":routed})
        with patch("subprocess.Popen",side_effect=AssertionError("NO_CHILD")),patch("subprocess.run",side_effect=AssertionError("NO_CHILD")):
            with self.assertRaises(InspectionComplete):ENTRY.execute(ORIGINAL,proxy,["--case","165","--run","8","--attempt","1","--code"])
        self.assertEqual((observed["outer"],observed["fresh"]),(10,10));self.assertTrue(observed["same"])
        self.assertEqual(observed["preparation_role"],"dispatch_construction")
        self.assertEqual(len(instances),1);self.assertTrue(instances[0].cleanup)
        pin=dict(path="target/a.exe",bytes=1048576,sha256="a"*64)
        other=dict(path="fixtures/a.json",bytes=1048576,sha256="b"*64)
        row=observed["model"].model({p["path"]:p for p in (pin,other)},167)
        self.assertEqual(row["product_allowance_seconds"],10);self.assertEqual(row["unallocated_margin_seconds"],60)
        self.assertEqual(len(seen),1)

    def test_native_bridge_source_does_not_call_candidate_preparation_guard(self):
        import ast
        tree=ast.parse((a.c.ROOT/MODULE.BRIDGE_SOURCE).read_text(encoding="utf-8"))
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main")
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr in ("route_loader","preparation_CPU") for n in ast.walk(main)))
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
            and isinstance(n.func.value,ast.Name) and n.func.value.id=="policy" and n.func.attr=="guard_type" for n in ast.walk(main)))
