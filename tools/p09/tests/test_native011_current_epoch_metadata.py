"""Real approved Batch projection plus explicit805 slots; no source audit/GO."""
import ast
from types import SimpleNamespace as NS
import unittest
import conservative_maintenance as c
import current_stored_runtime_scope as scope
import batch_verification as batch
import native011_current_epoch_metadata as upgrade


def original_runtime():
    raw=(c.ROOT/batch.RUNTIME).read_bytes()
    node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='current_input_scope')
    env={};exec(compile(ast.Module(body=[node],type_ignores=[]),batch.RUNTIME,'exec'),env)
    return NS(current_input_scope=env['current_input_scope']),raw


def owner():
    pin=dict(path='current.exe',bytes=1,sha256='a'*64);rows={pin['path']:pin}
    return batch.Batch(rows,rows,{},first_index=165,checkpoint=lambda:None)


class MetadataContracts(unittest.TestCase):
    def test_real_approved_policy_and_complete_four_slot_inverse(self):
        runtime,raw=original_runtime();policy=owner();epoch=NS()
        projected,proof=upgrade.connect(runtime,raw,batch,policy,epoch)
        self.assertTrue(proof['approved_three_policy_slot_proof']['exact_original_AST_inverse'])
        self.assertTrue(proof['entire_approved_AST_inverse'])
        self.assertEqual(set(proof['epoch_slots']),{'scope_import','listing_field','rust_guard','rust_error_label'})
        self.assertIs(projected.current_input_scope.__globals__['_batch'],policy)
        self.assertIs(projected.current_input_scope.__globals__['_current_epoch_scope'],epoch)
        self.assertNotIn('_batch',runtime.current_input_scope.__globals__)

    def test_real_NEW_batch_still_denies_before_metadata_reads_or_imports(self):
        runtime,raw=original_runtime();policy=owner();projected,_=upgrade.connect(runtime,raw,batch,policy,NS())
        class Reader:
            def pin(self,*args):self.fail('metadata IO started')
        with self.assertRaisesRegex(ValueError,'READY_METADATA_OWNER_ONLY'):
            projected.current_input_scope(Reader(),NS(binding=None),{},None,None,{})
        self.assertEqual(policy.phase,'NEW');self.assertIsNone(policy.initial)

    def test_listing_view_accepts_only_exact_real_new_schema_and_no_freshness_promotion(self):
        record=dict(current_whole805_freshness_qualified=False,product_test_bodies_executed=False,names=['original'])
        pin=dict(path='crates/x.rs',bytes=1,sha256='a'*64)
        view=upgrade.ListingView(scope,record,{pin['path']:pin})
        self.assertEqual(view.listing_inputs(dict(record)),{pin['path']:pin})
        record['names'].append('changed')
        with self.assertRaisesRegex(ValueError,'EXACT_REAL_COMPILED_LIST_RECORD_NOT_OLD_SCHEMA'):
            view.listing_inputs(record)

    def test_unpinned_source_cannot_be_used_to_rebuild_approved_policy(self):
        runtime,raw=original_runtime()
        with self.assertRaisesRegex(ValueError,'EXACT_ORIGINAL_SCOPE_SOURCE'):
            upgrade.connect(runtime,raw+b'\n',batch,owner(),NS())
