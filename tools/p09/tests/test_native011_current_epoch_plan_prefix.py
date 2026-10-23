"""Exact original planning prefix extraction, not parent/Frame construction."""
from types import SimpleNamespace as NS
import unittest
import conservative_maintenance as c
import native011_current_epoch_plan_inspection as inspector


class PrefixContracts(unittest.TestCase):
    def test_all_original_scope_prefix_nodes_and_no_engine_tail(self):
        raw=(c.ROOT/inspector.PARENT['path']).read_text(encoding='utf-8');captured=[]
        def definitions(source,names,namespace):captured.append(source);return NS(construct=lambda *args:None)
        _,proof=inspector.scope_prefix(raw,definitions,{})
        self.assertTrue(proof['all_retained_statements_AST_identical'])
        self.assertFalse(proof['original_engine_tail_executed'])
        self.assertIn('bind_intrinsic_failures',captured[0])
        self.assertIn('parent.project_plan',captured[0])
        self.assertIn('FULL_NEW_WHOLE_LOGICAL_PHYSICAL_EQUALITY',captured[0])
        self.assertNotIn('prepared = modules.native011_worker_preparation.prepare',captured[0])
        self.assertIn('return NS(data=data, batch=batch, delta=delta)',captured[0])

    def test_missing_or_duplicate_engine_boundary_cannot_extend_prefix(self):
        raw=(c.ROOT/inspector.PARENT['path']).read_text(encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'EXACT_BEFORE_ENGINE_BOUNDARY'):
            inspector.scope_prefix(raw.replace(inspector.BOUNDARY,'other'),lambda *args:None,{})
        marker="    row['stage']='"+inspector.BOUNDARY+"'"
        with self.assertRaisesRegex(ValueError,'EXACT_BEFORE_ENGINE_BOUNDARY'):
            inspector.scope_prefix(raw.replace(marker,marker+'\n'+marker),lambda *args:None,{})


if __name__=='__main__':unittest.main()
