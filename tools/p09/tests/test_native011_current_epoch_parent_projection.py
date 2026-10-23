"""Whole parent AST inverse models only; no parent or worker is executed."""
from types import SimpleNamespace as NS
import unittest
import conservative_maintenance as c
import native011_current_epoch_parent as parent


class ParentProjectionContracts(unittest.TestCase):
    def test_complete_original_constructor_preserved_with_exact_epoch_hook(self):
        raw=(c.ROOT/'tools/p09/native011_parent_plan.py').read_text(encoding='utf-8');captured=[]
        def definitions(source,names,namespace):captured.append(source);return NS(construct=lambda *args:None)
        _,proof=parent.project_constructor(raw,definitions,{},lambda *args:None)
        self.assertTrue(proof['complete_original_constructor_AST_inverse'])
        self.assertEqual(proof['explicit_added_statements'],5)
        self.assertIn('_epoch = _install_epoch(data, batch, q, scope)',captured[0])
        self.assertIn('prepared = modules.native011_worker_preparation.prepare',captured[0])
        self.assertIn('ACTUAL_PARENT_METADATA_FAILS_CLOSED',captured[0])
        self.assertIn('context.parent_state = state',captured[0])

    def test_missing_or_duplicate_epoch_position_refused(self):
        raw=(c.ROOT/'tools/p09/native011_parent_plan.py').read_text(encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'ONE_EXACT_EPOCH_INSTALLATION_POSITION'):
            parent.project_constructor(raw.replace(parent.BOUNDARY,'other'),lambda *args:None,{},None)
        marker="    row['stage']='"+parent.BOUNDARY+"'"
        with self.assertRaisesRegex(ValueError,'ONE_EXACT_EPOCH_INSTALLATION_POSITION'):
            parent.project_constructor(raw.replace(marker,marker+'\n'+marker),lambda *args:None,{},None)


if __name__=='__main__':unittest.main()
