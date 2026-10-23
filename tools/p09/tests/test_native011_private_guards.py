"""Whole pinned preparation guards in private namespaces, never a run."""
from pathlib import Path
import sys
import unittest
import accept_case112_current_epoch as a
import native011_parent_plan as plan
import runtime_envelope_namespace_bundle_v1 as loader


class PrivateGuardContracts(unittest.TestCase):
    def test_all_four_whole_guard_sources_and_no_hidden_default_modules(self):
        root=Path(__file__).resolve().parents[3]
        before=dict(sys.modules)
        names,proof=loader.load(root,list(plan.GUARDS),{})
        self.assertEqual(len(proof),4)
        self.assertTrue(all(p['original_function_class_constants_and_initialization_AST_retained'] for p in proof))
        self.assertTrue(all(sys.modules.get(n) is module for n,module in before.items()))
        for pin in plan.GUARDS:
            key=Path(pin['path']).stem
            self.assertIs(sys.modules.get(key),before.get(key))
            self.assertTrue(getattr(names,key).__name__.startswith('p09_exact_'))

    def test_same_original_guard_base_acquire_close_and_policy(self):
        root=Path(__file__).resolve().parents[3]
        names,_=loader.load(root,list(plan.GUARDS),{})
        final=names.distinct_final_sample_guard_v1.guard_type(a.Guard)
        attributed=names.preparation_attributed_cpu_v1.guard_type(final,role='whole_metadata_preflight')
        selected=names.owned_cpu_baseline_v1.guard_type(attributed)
        self.assertIs(selected.__mro__[-2],a.Guard)
        for method in ('acquire','close'):
            self.assertIs(getattr(selected,method),getattr(a.Guard,method))
        self.assertEqual(names.preparation_attributed_cpu_v1.POLICY['immediate_system_stop_percent'],90)
        self.assertEqual(names.preparation_attributed_cpu_v1.POLICY['system_warning_percent'],75)
        self.assertEqual(names.distinct_final_sample_guard_v1.INTERVAL,.5)


if __name__=='__main__':unittest.main()
