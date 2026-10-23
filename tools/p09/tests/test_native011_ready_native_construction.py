"""Whole constructor projection and closed-source rejection, no parent run."""
import ast
import unittest
import conservative_maintenance as c
import native011_ready_scope_connection as control


class NativeProjectionContracts(unittest.TestCase):
    def test_protection_helpers_are_private_without_module_hiding_or_count_bypass(self):
        raw=(c.ROOT/control.ENTRY).read_text(encoding='utf-8');tree=ast.parse(raw)
        names={alias.name for node in ast.walk(tree) if isinstance(node,ast.Import) for alias in node.names}
        self.assertFalse(names & {'prepared_run_closure_v1','owned_cpu_baseline_v1',
            'preparation_attributed_cpu_v1','distinct_final_sample_guard_v1'})
        self.assertIn('list(parent.GUARDS)',raw);self.assertNotIn('sys.modules',raw)

    def test_whole_original_constructor_inverse_and_exact_connection_sites(self):
        raw=(c.ROOT/control.ORIGINAL['path']).read_bytes()
        call,proof=control.project(raw,{},lambda *args:None,lambda *args:None)
        self.assertTrue(proof['entire_original_constructor_AST_inverse'])
        self.assertEqual(proof['declaration_admission_site_count'],1)
        self.assertEqual(proof['preclosing_validation_site_count'],1)
        self.assertEqual(call.__name__,'main');self.assertFalse(proof['actual_Native_or_GO_qualified'])
    def test_changed_original_source_rejected_before_compilation(self):
        raw=(c.ROOT/control.ORIGINAL['path']).read_bytes()
        with self.assertRaisesRegex(ValueError,'EXACT_FULL_ORIGINAL_SHARED_CONSTRUCTOR'):
            control.project(raw+b'\n',{},lambda *args:None,lambda *args:None)
    def test_original_guard_and_audit_sites_are_not_removed_by_the_projection(self):
        raw=(c.ROOT/control.ORIGINAL['path']).read_bytes();call,proof=control.project(raw,{},None,None)
        names=set(call.__code__.co_names)
        for name in ('finish','check','prepare','connect_parent','attach','restore','close'):
            self.assertIn(name,names)
        self.assertEqual(proof['exclusive_new_output'],control.OUTPUT)
