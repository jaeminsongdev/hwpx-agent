from types import FunctionType,SimpleNamespace as NS
import unittest
from unittest.mock import patch


class FakeRoot:
    def __init__(self,exists=False,link=False):self.present=exists;self.link=link;self.paths=[]
    def __truediv__(self,name):self.paths.append(name);return self
    def exists(self):return self.present
    def is_symlink(self):return self.link
    def is_junction(self):return False


class Tests(unittest.TestCase):
    def test_exact_native006_context_and_physical_run8(self):
        args=MODULE.native_arguments(15,8)
        self.assertEqual(args,["--native","--case","165","--run","8","--attempt","1","--code-attempt","6","--preflight-attempt","15","--qualification-attempt","8"])
        self.assertEqual(MODULE.native_arguments(16,8)[10],"16")

    def test_old_metadata_and_invalid_ids_rejected(self):
        for pref,qual in ((14,7),(15,7),(17,8),(True,8),(15,True),(15,9)):
            with self.assertRaises(ValueError):MODULE.native_arguments(pref,qual)

    def test_existing_or_linked_native_record_denied_before_execution(self):
        MODULE.absent(FakeRoot())
        for root in (FakeRoot(True),FakeRoot(link=True)):
            with self.assertRaises(ValueError):MODULE.absent(root)

    def test_native_intent_prevents_automatic_replay(self):
        root=FakeRoot();MODULE.no_previous_intent(root);self.assertEqual(len(root.paths),8)
        with self.assertRaises(ValueError):MODULE.no_previous_intent(FakeRoot(True))

    def test_real_build_has_no_preparation_guard_construction(self):
        def forbidden(*args,**kwargs):raise AssertionError("PREPARATION_GUARD_IN_NATIVE")
        setup=NS(**{**vars(SETUP),"policy":NS(guard_type=forbidden)})
        original=ACCEPTANCE.Guard
        linked=MODULE.build_native(ROOT,ENVELOPE,ACCEPTANCE,ENTRY,BINDING,setup,witness=lambda q:None)
        self.assertIs(ACCEPTANCE.Guard,original);self.assertFalse(linked.Native_policy_changed)
        self.assertFalse(linked.preparation_CPU_Guard_constructed)
        self.assertEqual(linked.current_worker_entry,ENTRY.SELF)

    def test_build_uses_whole_original_closure_and_only_dependency_hook(self):
        linked=MODULE.build_native(ROOT,ENVELOPE,ACCEPTANCE,ENTRY,BINDING,SETUP,witness=lambda q:None)
        original=SETUP.raw.prepared_run_closure_v1.main
        self.assertEqual(tuple(n for n in linked.main.__code__.co_names if n!="_xz_current_recovery_profile"),original.__code__.co_names)
        self.assertEqual(linked.main.__defaults__,original.__defaults__);self.assertEqual(linked.main.__closure__,original.__closure__)
        self.assertEqual(linked.dispatch_window_observations,[])

    def test_native_dispatch_router_receives_no_preparation_controller_transform(self):
        windows=SETUP.entry.window_components(ROOT,ENVELOPE);bridge=windows.recovery_dispatch_window_v1;seen=[];original=bridge.connect_loader
        def spy(*args,**kwargs):seen.append(kwargs);return original(*args,**kwargs)
        proxy=NS(**{**vars(windows),"recovery_dispatch_window_v1":NS(**{**vars(bridge),"connect_loader":spy})})
        with patch.object(SETUP.entry,"window_components",return_value=proxy):
            MODULE.build_native(ROOT,ENVELOPE,ACCEPTANCE,ENTRY,BINDING,SETUP,witness=lambda q:None)
        self.assertEqual(len(seen),1);self.assertNotIn("controller_transform",seen[0])

    def test_preparation_witness_is_published_to_actual_entry_family(self):
        api=MODULE.preparation_api(ENTRY,BINDING)
        self.assertIs(api.recovery_adapter_code.__globals__["witnesses"],api.witnesses)
        self.assertIs(api.recovery_adapter_code.__code__,ENTRY.recovery_adapter_code.__code__)
        with self.assertRaises(ValueError):api.witnesses(None,None,None,None,None,None,None,code=False)

    def test_preparation_reader_adds_native_wiring_proof_not_just_wrapper(self):
        api=MODULE.preparation_api(ENTRY,BINDING);seen=[]
        with patch.dict(api.witnesses.__globals__,dict(witnesses=lambda *args,**kwargs:seen.append((args,kwargs)))):
            api.witnesses(1,2,3,4,5,6,7,code=True)
        self.assertEqual(seen,[((1,2,ENTRY,BINDING,3,4,5,6,7),dict(proof=True))])

    def test_native_preparation_mode_and_old_scope_rejected(self):
        for values in (("native",1,None),("review",1,None),("accept",1,None),("preflight",14,None),("qualify",7,14)):
            with self.assertRaises(ValueError):MODULE.prepare(ENTRY,BINDING,*values)

    def test_frozen_closure_and_unified_worker_sources_are_unchanged(self):
        import hashlib
        for pin in (SETUP.entry.ENTRY,BINDING.ENTRY_PIN):
            raw=(ROOT/pin["path"]).read_bytes()
            self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(pin["bytes"],pin["sha256"]))
        self.assertTrue(ENTRY.ACTUAL_CODE.endswith("attempt005.v1.json"))
        self.assertTrue(BINDING.WHOLE_CODE["path"].endswith("attempt006.v1.json"))

    def test_error_reporting_does_not_disclose_source_paths(self):
        self.assertEqual(MODULE.error_code(ValueError("C:\\private\\secret value")),"ValueError")
        self.assertEqual(MODULE.error_code(ValueError("NATIVE_BOOTSTRAP_REFUSED")),"NATIVE_BOOTSTRAP_REFUSED")
