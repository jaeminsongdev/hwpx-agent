"""Closed P156 source binding and fresh product suffix, without any OS child."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import build_immutable_graph_product as s


class ImmutableGraphBuildTests(unittest.TestCase):
    def row(self):
        pins=[dict(path=f'fixture/{i}.dat',bytes=1,sha256='0'*64) for i in range(1183)]
        pins.extend(dict(path=f'target/history-{i}.exe',bytes=1,sha256='0'*64) for i in range(61))
        changes=[dict(path=n,bytes=1,sha256='0'*64) for n in
            ('crates/domain-ir/src/document_graph.rs','crates/domain-ir/tests/document_graph.rs')]
        pins.extend(changes)
        row=dict(state='PASS_CURRENT_IMMUTABLE_GRAPH_DELTA_AND_UNITS15_ONLY_NOT_FULL249_OR_GATE',source_closing_exact=True,
            whole_original_core_inverse_exact=True,all_original_domain_tests_preserved=True,actual_unit_tests_passed=15,
            typecheck_accepted=True,protected_EXE_inputs_exact=60,current_Rust_input_count=785,resource_stop_reason=None,
            resource_watcher_cleanup_confirmed=True,P09_gate='OPEN',bound_input_pins=pins,
            fresh_domain_unit_executable_pin=pins[-3],declared_Rust_source_changes=changes)
        row.update({k:False for k in ('current_compiled249_qualified','full249_current_qualified','signed16_current_qualified',
            'product_complete','PC_freeze_resolved','full_product_performance_improvement_measured')})
        return row

    def test_exact_current_closing_accepts61_not_old54(self):
        expected,protected=s.parent_scope(self.row());self.assertEqual(len(expected),1246);self.assertEqual(len(protected),61)

    def test_old_scope_or_failed_source_rejected(self):
        for key,value in (('state','PASS_SCOPED_NOT_GATE'),('source_closing_exact',False),('whole_original_core_inverse_exact',False),
            ('all_original_domain_tests_preserved',False),('actual_unit_tests_passed',14),('typecheck_accepted',False),
            ('protected_EXE_inputs_exact',54),('current_Rust_input_count',784),('resource_stop_reason','STOP_RAM'),
            ('resource_watcher_cleanup_confirmed',False),('P09_gate','PASS')):
            row=self.row();row[key]=value
            with self.assertRaises(ValueError):s.parent_scope(row)

    def test_all_product_promotions_rejected(self):
        for k in ('current_compiled249_qualified','full249_current_qualified','signed16_current_qualified',
            'product_complete','PC_freeze_resolved','full_product_performance_improvement_measured'):
            row=self.row();row[k]=True
            with self.assertRaises(ValueError):s.parent_scope(row)

    def test_missing_whole_input_rejected(self):
        row=self.row();row['bound_input_pins'].pop(0)
        with self.assertRaises(ValueError):s.parent_scope(row)

    def test_duplicate_whole_input_rejected(self):
        row=self.row();row['bound_input_pins'][0]=row['bound_input_pins'][1]
        with self.assertRaises(ValueError):s.parent_scope(row)

    def test_different_rust_delta_rejected(self):
        row=self.row();row['declared_Rust_source_changes'][0]=dict(path='crates/other.rs',bytes=1,sha256='0'*64)
        with self.assertRaises(ValueError):s.parent_scope(row)

    def test_domain_exe_identity_must_be_protected(self):
        row=self.row();row['fresh_domain_unit_executable_pin']=dict(row['fresh_domain_unit_executable_pin'],sha256='1'*64)
        with self.assertRaises(ValueError):s.parent_scope(row)

    def test_new_suffix_cannot_overlap_history(self):
        with self.assertRaises(ValueError):s.fresh_scope({s.b.executable_name(s.RUN):{}})
        with patch.object(s.s,'scoped_path',return_value=SimpleNamespace()) as check:
            self.assertTrue(s.fresh_scope({}).endswith('p152-r02.exe'));check.assert_called_once_with(s.b.executable_name(2),fresh=True)

    def test_recipe_original_profile_and_owned_policy_unchanged(self):
        before=copy.deepcopy(s.c.POLICY);r=s.s.recipe(s.RUN)
        self.assertEqual(len(r['test_package_profile_config']),81);self.assertEqual(r['compile_maximum_seconds'],600)
        self.assertEqual(r['full249_maximum_seconds'],1200);self.assertTrue(r['full249_unfiltered_required'])
        self.assertEqual(s.c.POLICY,before);self.assertEqual(s.RUN,2)

    def test_no_history_executor_load_is_connected(self):
        self.assertNotEqual(s.PARENT,s.b.AUDIT_PIN);self.assertEqual(s.b.task_for(s.RUN),'p152-current-stored-build-r02')


if __name__=='__main__':unittest.main()
