from types import FunctionType,SimpleNamespace as NS
import unittest
from unittest.mock import patch


class Tests(unittest.TestCase):
    def test_real_entry_sources_are_exact_and_unchanged(self):
        import hashlib
        raw=(ROOT/MODULE.ENTRY_PIN["path"]).read_bytes()
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(MODULE.ENTRY_PIN["bytes"],MODULE.ENTRY_PIN["sha256"]))
        self.assertTrue(ENTRY.ACTUAL_CODE.endswith("attempt005.v1.json"))

    def test_whole_function_family_preserved_and_not_published_to_original(self):
        adapted=MODULE.adapt(ENTRY)
        for name in ("build","project_closure","reference_loader","recovery_adapter_code"):
            self.assertIs(getattr(adapted,name).__code__,getattr(ENTRY,name).__code__)
            self.assertIsNot(getattr(adapted,name).__globals__,getattr(ENTRY,name).__globals__)
        self.assertNotEqual(ENTRY.ACTUAL_CODE,adapted.ACTUAL_CODE)
        self.assertEqual(adapted.ACTUAL_CODE,MODULE.WHOLE_CODE["path"])

    def test_context_changes_only_current_code_identifier(self):
        revised=MODULE.adapt(ENTRY)
        before=ENTRY.context("preflight",13);after=revised.context("preflight",13)
        self.assertEqual(before[:-1],after[:-1]);self.assertEqual((before[-1],after[-1]),("5","6"))
        self.assertEqual(revised.context("qualify",7,13)[-2:],["--preflight-attempt","13"])

    def test_current_reference_accepts_real006_not_old005_or_other_case(self):
        api=MODULE.adapt(ENTRY)
        self.assertEqual(api.code_reference(MODULE.RECOVERY_CODE),MODULE.WHOLE_CODE["path"])
        self.assertEqual(api.code_reference(MODULE.WHOLE_CODE["path"]),MODULE.WHOLE_CODE["path"])
        for value in (ENTRY.ACTUAL_CODE,MODULE.WHOLE_CODE["path"].replace("case165","case164")):
            with self.assertRaises(ValueError):api.code_reference(value)

    def test_actual_stage_requires_binding_source_qualification(self):
        api=MODULE.adapt(ENTRY)
        with self.assertRaises(ValueError):api.witnesses(None,None,None,None,None,None,None,code=False)
        def missing(*args,**kwargs):raise ValueError("MISSING_CURRENT_BINDING")
        with patch.dict(api.witnesses.__globals__,dict(witnesses=missing)):
            with self.assertRaisesRegex(ValueError,"MISSING_CURRENT_BINDING"):
                api.witnesses(None,None,None,None,None,None,None,code=True)

    def test_native_worker_review_accept_and_invalid_attempts_rejected(self):
        api=MODULE.adapt(ENTRY)
        for values in (("native",1,None),("worker",1,None),("review",1,None),("accept",1,None),("preflight",17,None),("qualify",9,13)):
            with self.assertRaises(ValueError):api.context(*values)

    def test_witness_dependency_keeps_current_program_closure(self):
        api=MODULE.adapt(ENTRY);seen=[]
        with patch.dict(api.witnesses.__globals__,dict(witnesses=lambda *args,**kw:seen.append((args,kw)))):
            api.witnesses(1,2,3,4,5,6,7,code=True)
        self.assertEqual(seen,[((1,2,ENTRY,3,4,5,6,7),dict(proof=True))])

    def test_invocation_restores_arguments_and_does_not_invoke_for_invalid_mode(self):
        import sys
        original=list(sys.argv)
        with self.assertRaises(ValueError):MODULE.invoke(ENTRY,"native",1)
        self.assertEqual(sys.argv,original)
