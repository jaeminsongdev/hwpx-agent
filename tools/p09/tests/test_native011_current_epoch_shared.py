"""Private scope-slot contracts; not a shared decoder or Native qualification."""
from types import SimpleNamespace as NS
import unittest
import native011_current_epoch_shared as shared
import current_stored_runtime_scope as scope


class SharedScopeContracts(unittest.TestCase):
    def test_intrinsic_step_added_only_to_callback_sources_not_report_or_scope(self):
        pin=lambda name:dict(path=name,bytes=1,sha256='a'*64)
        existing=pin('tools/p09/model.py');step=pin('implementation/p09/evidence/model-step.json')
        admitted=NS(sources={existing['path']:existing},report=object(),proof=object())
        current={existing['path']:existing,step['path']:step}
        expanded=shared.callback_sources(admitted,step,current,scope)
        self.assertEqual(expanded.sources,current);self.assertEqual(len(admitted.sources),1)
        self.assertIs(expanded.report,admitted.report);self.assertIs(expanded.proof,admitted.proof)
        with self.assertRaisesRegex(ValueError,'EXACT_ALREADY_CURRENT_STEP_INPUT'):
            shared.callback_sources(admitted,step,{existing['path']:existing},scope)

    def test_only_scope_dependency_changed_and_same_owner_reaches_original_connector(self):
        original=lambda:None;batch=NS(install_scope=original,keep=object());scope=NS();seen=[]
        runtime=NS();owner=NS();adapted=NS()
        proof=dict(approved_three_policy_slot_proof=dict(exact_original_AST_inverse=True),entire_approved_AST_inverse=True)
        def connector(*args):seen.append(args);return adapted,proof
        api,state=shared.batch_scope_api(batch,scope,connector)
        result,inverse=api.install_scope(runtime,b'raw',owner)
        self.assertEqual(seen,[(runtime,b'raw',batch,owner,scope)])
        self.assertIs(result,adapted);self.assertIs(api.keep,batch.keep)
        self.assertIs(batch.install_scope,original)
        self.assertTrue(inverse['exact_original_AST_inverse']);self.assertIs(state.proof,proof)

    def test_second_installation_denied_without_second_connector_call(self):
        calls=[]
        def connector(*args):
            calls.append(1)
            return NS(),dict(approved_three_policy_slot_proof=dict(exact_original_AST_inverse=True),entire_approved_AST_inverse=True)
        api,_=shared.batch_scope_api(NS(),NS(),connector)
        api.install_scope(None,b'',None)
        with self.assertRaisesRegex(ValueError,'ONE_EXPLICIT_CURRENT805_SCOPE_INSTALLATION'):
            api.install_scope(None,b'',None)
        self.assertEqual(calls,[1])

    def test_missing_inverse_or_failed_connector_never_grants_followup_installation(self):
        for mode in ('inverse','failure'):
            def connector(*args):
                if mode=='failure':raise ValueError('MODEL_CONNECTOR_REFUSAL')
                return NS(),dict(approved_three_policy_slot_proof=dict(exact_original_AST_inverse=True),entire_approved_AST_inverse=False)
            api,state=shared.batch_scope_api(NS(),NS(),connector)
            with self.assertRaises(ValueError):api.install_scope(None,b'',None)
            self.assertIsNone(state.proof)
            with self.assertRaisesRegex(ValueError,'ONE_EXPLICIT_CURRENT805_SCOPE_INSTALLATION'):
                api.install_scope(None,b'',None)
