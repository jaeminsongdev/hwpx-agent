"""Closed current source generation; no fake build/runtime promotion."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import prepare_current_stored_generation as s


class CurrentStoredGenerationTests(unittest.TestCase):
    def parent(self):
        return dict(state='PASS_CURRENT39_PRE_BACKEND_CANCEL_HOST_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE',
            source_closing_exact=True, current_Rust_input_count=785, compiled_source_count=846,
            protected_executables_exact=53, contract_tests_passed=36, required_check_count=39,
            resource_stop_reason=None, resource_watcher_cleanup_confirmed=True,
            actual_SQL_native_or_runtime_EXE_executed=False, product_complete=False, P09_gate='OPEN', bound_input_pins=[])

    def test_run_scope(self):
        self.assertEqual(s.generation(1), 'p152-r01')
        for run in (0, 100, -1, True, '1'):
            with self.assertRaises(ValueError): s.generation(run)

    def test_fresh_name_different_from_hashed_historical(self):
        self.assertEqual(s.executable_name(1), 'target/p09-149-conservative/debug/deps/form_stored_provider-p152-r01.exe')
        self.assertNotEqual(s.executable_name(1), s.executable_name(2))

    def test_recipe_test_profile_not_dev_runtime(self):
        a = s.recipe(1)['argv_without_cargo']; i = a.index('--profile')
        self.assertEqual(a[i+1], 'test'); self.assertIn('--test', a); self.assertNotIn('--example', a)

    def test_exact_profile81(self):
        r = s.recipe(1); self.assertEqual(r['test_package_profile_config'], list(s.profile.CONFIG))
        self.assertEqual(len(r['test_package_profile_config']), 81)

    def test_locked_offline_single_job_and_suffix(self):
        a = s.recipe(1)['argv_without_cargo']
        self.assertIn('--locked', a); self.assertIn('--offline', a)
        self.assertEqual(a[a.index('--jobs')+1], '1')
        self.assertEqual(a[-4:], ['--message-format=json', '--', '-C', 'extra-filename=-p152-r01'])

    def test_runtime_no_filter_or_ignored_tests(self):
        r = s.recipe(1); self.assertEqual(r['runtime_argv'], ['--test-threads=1', '--format=terse'])
        self.assertEqual(r['runtime_RUST_TEST_NOCAPTURE'], '0'); self.assertTrue(r['full249_unfiltered_required'])

    def test_original_caps_and_ram_headroom(self):
        r = s.recipe(1); self.assertEqual(r['compile_maximum_seconds'], 600)
        self.assertEqual(r['full249_maximum_seconds'], 1200)
        self.assertEqual(r['compile_admission_RAM_percent'], 15); self.assertEqual(r['runtime_admission_RAM_percent'], 10)
        self.assertEqual(r['policy'], s.c.POLICY)

    def test_plan_not_executor_or_speedup(self):
        r = s.recipe(1); self.assertFalse(r['executor_connected']); self.assertFalse(r['actual_cache_hit_or_speedup_proven'])
        self.assertTrue(r['compiled249_listing_required_before_runtime']); self.assertTrue(r['build_catalog_requires_test_true'])

    def test_parent_complete1185_inventory_required(self):
        with patch.object(s.inputs, 'inventory', return_value={}) as check: s.parent_scope(self.parent())
        check.assert_called_once_with([], 1185)

    def test_stale_generation_or_partial_parent_rejected(self):
        for key, value in (('current_Rust_input_count', 783), ('compiled_source_count', 842),
                ('source_closing_exact', False), ('protected_executables_exact', 52), ('contract_tests_passed', 35)):
            with self.assertRaises(ValueError): s.parent_scope(dict(self.parent(), **{key: value}))

    def test_stop_cleanup_or_false_product_promotion_rejected(self):
        for key, value in (('resource_stop_reason', 'STOP'), ('resource_watcher_cleanup_confirmed', False),
                ('actual_SQL_native_or_runtime_EXE_executed', True), ('product_complete', True), ('P09_gate', 'PASS')):
            with self.assertRaises(ValueError): s.parent_scope(dict(self.parent(), **{key: value}))

    def test_fresh_output_link_checks_delegated(self):
        with patch.object(s, 'scoped_path', return_value=SimpleNamespace()) as check:
            self.assertEqual(s.require_fresh_output(1, {}), s.executable_name(1))
        check.assert_called_once_with(s.executable_name(1), fresh=True)
        with self.assertRaises(ValueError): s.require_fresh_output(1, {s.executable_name(1): {}})

    def test_protected54_whole_current_closure(self):
        exe = dict(path='target/runtime.exe', bytes=1, sha256='0'*64)
        build = dict(state='PASS_CURRENT_DS06_NON_TEST_RUNTIME_BUILD_ONLY_NOT_SQL_NATIVE_OR_GATE',
            current_build_binding_accepted=True, protected_executables_exact_after=True,
            source_freeze_exact_after=True, protected_executables=[], executable_pin=exe)
        with patch.object(s.inputs, 'inventory', return_value={exe['path']: exe}) as check:
            self.assertEqual(s.protected_scope(build, dict(current_runtime_executable_pin=exe), {exe['path']: exe}), {exe['path']: exe})
            check.assert_called_once_with([exe], 54)
            with self.assertRaises(ValueError): s.protected_scope(build, dict(current_runtime_executable_pin=exe), {})

    def test_policy_mutation_not_shared(self):
        before = copy.deepcopy(s.c.POLICY); r = s.recipe(1); r['policy']['cargo_jobs'] = 99
        self.assertEqual(before, s.c.POLICY)


if __name__ == '__main__': unittest.main()
