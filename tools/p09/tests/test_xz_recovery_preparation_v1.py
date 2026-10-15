from types import SimpleNamespace as NS,FunctionType
from unittest.mock import patch
import ast
import copy
import unittest


class Tests(unittest.TestCase):
    def test_only_current_preparation_context_and_finite_identifiers(self):
        self.assertEqual(MODULE.context("preflight",11),["--preflight","--case","165","--run","8","--attempt","11","--code-attempt","5"])
        self.assertEqual(MODULE.context("qualify",1,11)[-2:],["--preflight-attempt","11"])
        for values in (("native",1,None),("worker",1,None),("preflight",True,None),("preflight",17,None),("qualify",9,11),("qualify",1,None)):
            with self.assertRaises(ValueError):MODULE.context(*values)

    def test_actual_code_reference_is_exact_not_a_record_copy(self):
        self.assertEqual(MODULE.code_reference(MODULE.RECOVERY_CODE),MODULE.ACTUAL_CODE)
        self.assertEqual(MODULE.code_reference(MODULE.ACTUAL_CODE),MODULE.ACTUAL_CODE)
        for value in (MODULE.RECOVERY_CODE.replace("005","001"),MODULE.ACTUAL_CODE.replace("case165","case164"),None):
            with self.assertRaises(ValueError):MODULE.code_reference(value)

    def test_whole_frozen_closure_inverse_one_dependency_hook(self):
        raw=(ROOT/ENTRY.ENTRY["path"]).read_bytes();seen=[]
        result=MODULE.project_closure(CLOSURE.main,raw,lambda fn:seen.append(fn))
        self.assertEqual(tuple(n for n in result.__code__.co_names if n!='_xz_current_recovery_profile'), CLOSURE.main.__code__.co_names)
        self.assertEqual(result.__defaults__,CLOSURE.main.__defaults__);self.assertEqual(result.__closure__,CLOSURE.main.__closure__)
        self.assertEqual(seen,[])

    def test_reference_fix_runs_after_original_binding_and_preserves_other_paths(self):
        calls=[]
        def destination(index,run,mode,attempt):calls.append((index,run,mode,attempt));return MODULE.RECOVERY_CODE if mode=="code" else "unchanged-pref"
        def context(*args,**kwargs):return NS(index=165,run=8,code=MODULE.RECOVERY_CODE,preflight="pref",qualification="qual",root="native")
        controller=NS(destination=destination);dispatch=NS(context=context);linked=NS(modules=NS(current_queue_successor_controller=controller,current_queue_successor_dispatch=dispatch))
        fix=NS(load=lambda *args,**kwargs:linked);base=NS(load=lambda:(NS(closed_prebody_factory_admission_fix_v1=fix),[]))
        loader=MODULE.reference_loader(base,NS());modules,_=loader.load();self.assertIs(modules.closed_prebody_factory_admission_fix_v1.load(),linked)
        self.assertEqual(controller.destination(165,8,"code",5),MODULE.ACTUAL_CODE)
        self.assertEqual(controller.destination(165,8,"preflight",11),"unchanged-pref")
        current=dispatch.context();self.assertEqual((current.code,current.preflight,current.root),(MODULE.ACTUAL_CODE,"pref","native"))
        self.assertEqual(len(calls),2)

    def test_other_code_epoch_is_not_silently_rebased(self):
        def destination(*args):return MODULE.RECOVERY_CODE.replace("005","006")
        linked=NS(modules=NS(current_queue_successor_controller=NS(destination=destination),current_queue_successor_dispatch=NS(context=lambda:NS(code=MODULE.RECOVERY_CODE))))
        fix=NS(load=lambda:linked);base=NS(load=lambda:(NS(closed_prebody_factory_admission_fix_v1=fix),[]))
        modules,_=MODULE.reference_loader(base,NS()).load();modules.closed_prebody_factory_admission_fix_v1.load()
        with self.assertRaises(ValueError):linked.modules.current_queue_successor_controller.destination(165,8,"code",6)

    def test_original_binding_failure_propagates(self):
        def failure(*args):raise ValueError("ORIGINAL_BINDING_STOP")
        fix=NS(load=failure);base=NS(load=lambda:(NS(closed_prebody_factory_admission_fix_v1=fix),[]))
        modules,_=MODULE.reference_loader(base,NS()).load()
        with self.assertRaisesRegex(ValueError,"ORIGINAL_BINDING_STOP"):modules.closed_prebody_factory_admission_fix_v1.load()

    def test_setup_code_reference_projection_preserves_original_family(self):
        def previous(*args):return "projected-original"
        calls=[]
        def metadata(fn,mapping):calls.append((fn,mapping));return "only-code-reference-fixed"
        driver=NS(project_setup_main=previous);base=NS(load=lambda:(NS(expanded_unhooked_setup_dependency_v1=driver),[]))
        modules,_=MODULE.reference_loader(base,NS(receipt_namespace=metadata)).load()
        self.assertIs(modules.expanded_unhooked_setup_dependency_v1.project_setup_main.__globals__,previous.__globals__)
        self.assertEqual(driver.project_setup_main(),"only-code-reference-fixed")
        self.assertEqual(calls,[("projected-original",{"successor-recovery-code-run":"successor-code-run"})])

    def test_real_completed_loader_construction_does_not_acquire_or_execute(self):
        instances=[]
        result=MODULE.build(ROOT,ENVELOPE,ACCEPTANCE,DELIVERY,ENTRY,CLOSURE,PROFILE,POLICY,"whole_metadata_preflight",instances)
        self.assertEqual(instances,[]);self.assertEqual(result.dispatch_window_observations,[])
        self.assertEqual(result.actual_CODE_reference,MODULE.ACTUAL_CODE)
        self.assertEqual(result.legacy_closure_worker_ENTRY_pin,CLOSURE.ENTRY)

    def test_frozen_closure_source_and_worker_pin_are_not_rewritten(self):
        before=copy.deepcopy(CLOSURE.ENTRY);raw=(ROOT/ENTRY.ENTRY["path"]).read_bytes()
        MODULE.project_closure(CLOSURE.main,raw,lambda value:value)
        self.assertEqual(CLOSURE.ENTRY,before);self.assertEqual(CLOSURE.ENTRY["path"],"tools/p09/level6_closed_preparation_v1.py")

    def test_projector_rejects_wrong_function_family(self):
        raw=(ROOT/ENTRY.ENTRY["path"]).read_bytes()
        with self.assertRaises(ValueError):MODULE.project_closure(lambda:None,raw,lambda value:value)

    def test_current_adapter_sources_join_the_actual_stage_reader_before_factory(self):
        seen=[]
        class Base:
            def __init__(self):seen.append("base")
        linked=NS(modules=NS(current_queue_successor_controller=NS(destination=lambda *a:MODULE.RECOVERY_CODE),
            current_queue_successor_dispatch=NS(context=lambda:NS(code=MODULE.RECOVERY_CODE))))
        def factory(*args,**kwargs):args[1].AcceptanceReader();seen.append("factory");return linked
        fix=NS(load=factory);base=NS(load=lambda:(NS(closed_prebody_factory_admission_fix_v1=fix),[]))
        modules,_=MODULE.reference_loader(base,NS(),witness=lambda q:seen.append("all-qualified-current-sources")).load()
        self.assertIs(modules.closed_prebody_factory_admission_fix_v1.load("root",NS(AcceptanceReader=Base)),linked)
        self.assertEqual(seen,["base","all-qualified-current-sources","factory"])

    def test_setup_reference_is_published_to_actual_main_not_only_wrapper_globals(self):
        legacy=dict(__name__="p09_exact_legacy_wrapper")
        exec("def project_setup_main(*args):\n return 'whole-original-setup'\n",legacy)
        actual=dict(__name__="p09_exact_actual_driver",project_setup_main=legacy["project_setup_main"])
        exec("def main():\n return project_setup_main()\n",actual)
        driver=NS(main=actual["main"],project_setup_main=legacy["project_setup_main"])
        base=NS(load=lambda:(NS(expanded_unhooked_setup_dependency_v1=driver),[]))
        MODULE.reference_loader(base,NS(receipt_namespace=lambda fn,mapping:"actual-code005")).load()
        self.assertIs(driver.project_setup_main.__globals__,driver.main.__globals__)
        self.assertIs(actual["project_setup_main"],driver.project_setup_main)
        self.assertEqual(driver.main(),"actual-code005")
