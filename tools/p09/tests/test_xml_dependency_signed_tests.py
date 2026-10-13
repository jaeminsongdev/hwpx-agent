import copy
import io
import json
import unittest
from unittest.mock import patch

import run_xml_dependency_signed_tests as s


class XMLDependencySignedTests(unittest.TestCase):
    def test_actual_recursive_inventory_helper_namespace_exists(self):
        self.assertTrue(callable(s.signed.previous.parent.recursive_names))

    def test_config_is_exact_unique26_and_only_quick_xml_delta(self):
        s.config_contract(s.CONFIG)
        self.assertEqual(s.CONFIG[:21], s.BASE_CONFIG)
        self.assertEqual(len(s.XML_CONFIG), 5)
        self.assertNotIn('profile.test.package.domain-ir.opt-level=1', s.CONFIG)
        self.assertNotIn('profile.test.package.artifact-service.opt-level=1', s.CONFIG)

    def test_weakening_assertions_or_global_config_or_duplicates_is_denied(self):
        for bad in (list(s.CONFIG), s.CONFIG[:-1], (*s.CONFIG[:-1], s.CONFIG[0]),
                tuple(e.replace('checks=true', 'checks=false') for e in s.CONFIG),
                tuple(e.replace('assertions=true', 'assertions=false') for e in s.CONFIG),
                (*s.CONFIG, 'profile.test.opt-level=3')):
            with self.assertRaises(ValueError): s.config_contract(bad)

    def test_finite_scopes_and_original_policy_unchanged(self):
        before = copy.deepcopy(s.c.POLICY)
        for task, maximum in ((s.DIAGNOSTIC, 180), (s.PROFILE, 180), (s.INVENTORY, 600)):
            s.require_duration(task, maximum)
            for bad in (True, 29, maximum+1, 1200):
                with self.assertRaises(ValueError): s.require_duration(task, bad)
        self.assertEqual(before, s.c.POLICY)

    def test_closed_inventory_run_paths(self):
        self.assertEqual(s.inventory_path(1), 'implementation/p09/evidence/p09-149-xml-dependency.inventory-run01.v1.json')
        for bad in (True, 0, 100, '1'):
            with self.assertRaises(ValueError): s.inventory_path(bad)

    def worker(self, task, go='P149_GO\n', member=True):
        from types import SimpleNamespace
        class Kernel:
            def GetCurrentProcess(self): return 1
            def IsProcessInJob(self, process, job, out): out._obj.value=member; return True
        calls=[]
        with patch.object(s.c, 'Windows', return_value=SimpleNamespace(k=Kernel())), \
                patch.object(s.c.sys, 'stdin', io.StringIO(go)), patch.object(s.c.shutil, 'which', return_value='cargo'), \
                patch.object(s.subprocess, 'call', side_effect=lambda args, **kw: calls.append((args, kw)) or 0):
            result = s.run_worker(task)
        return result, calls

    def test_diagnostic_original_worker_exact26_config_full_numeric_mode(self):
        result, calls = self.worker(s.DIAGNOSTIC)
        self.assertEqual(result, 0); self.assertEqual(len(calls), 1)
        args, kw = calls[0]
        self.assertEqual(args[1:53], [v for e in s.CONFIG for v in ('--config', e)])
        self.assertEqual(args[-2:], ['--', '--reconstruction-timing-only'])
        self.assertEqual(kw['env']['CARGO_PROFILE_TEST_DEBUG_ASSERTIONS'], 'true')

    def test_signed_original_worker_preserves_complete_test_and_checks(self):
        result, calls = self.worker(s.PROFILE)
        self.assertEqual(result, 0); self.assertEqual(len(calls), 1)
        args, kw = calls[0]
        self.assertEqual(args[1:53], [v for e in s.CONFIG for v in ('--config', e)])
        self.assertEqual(args[-5:], ['--', s.signed.previous.original.NAME, '--exact', '--nocapture', '--test-threads=1'])
        self.assertEqual(kw['env']['CARGO_PROFILE_TEST_OVERFLOW_CHECKS'], 'true')

    def test_inventory_original_worker_lists_all_tests_without_selection(self):
        result, calls = self.worker(s.INVENTORY)
        self.assertEqual(result, 0)
        self.assertEqual(calls[0][0][-4:], ['--', '--list', '--format', 'terse'])
        self.assertNotIn('--exact', calls[0][0])

    def test_all_workers_have_real_original_GO_and_Job_membership_gate(self):
        for task in (s.DIAGNOSTIC, s.INVENTORY, s.PROFILE):
            for go, member in (('wrong\n', True), ('P149_GO\n', False)):
                with self.assertRaises(ValueError): self.worker(task, go, member)

    def test_current_inventory_delegates_all_source_name_cleanup_checks(self):
        row={'source_variant': s.VARIANT, 'task': s.INVENTORY, 'test_package_profile_config': list(s.CONFIG),
            'xml_dependency_opt_level': 1, 'original_owned_resource_policy_changed': False}
        before = s.signed.CONFIG
        with patch.object(s.signed, 'accept_inventory') as accept: s.accept_inventory(row, {}, [], [])
        accept.assert_called_once(); self.assertEqual(accept.call_args.args[0]['test_package_profile_config'], list(s.CONFIG))
        self.assertIs(before, s.signed.CONFIG)
        for key, bad in (('source_variant', 'foreign'), ('task', 'foreign'), ('xml_dependency_opt_level', 0),
                ('original_owned_resource_policy_changed', True), ('test_package_profile_config', list(s.BASE_CONFIG))):
            wrong=copy.deepcopy(row); wrong[key]=bad
            with self.assertRaises(ValueError): s.accept_inventory(wrong, {}, [], [])

    def test_complete36_profile_and_original_signed_test_cannot_be_partial(self):
        from tests.test_reconstruction_stage_profile import ReconstructionStageTests
        row=ReconstructionStageTests().row(); row['tamper_denied']=35
        with self.assertRaises(ValueError): s.reconstruction.validate(json.dumps(row))
        with self.assertRaises(ValueError): s.signed.previous.original.validate_output('running 1 test\n')

    def test_failed_annotation_never_claims_product_or_changes_policy(self):
        stream=io.StringIO()
        def terminal(*args): json.dump({'state':'STOPPED_NOT_ACCEPTED'}, stream); return 2
        before=copy.deepcopy(s.c.POLICY)
        with patch.object(s.signed, 'run_owned', side_effect=terminal):
            self.assertEqual(s.run_owned(None, {}, [], [], s.PROFILE, 180), 2)
        row=json.loads(stream.getvalue()); self.assertEqual(row['source_variant'], s.VARIANT)
        for key in ('product_complete', 'full249_current_qualified', 'original_owned_resource_policy_changed', 'PC_freeze_resolved'):
            self.assertFalse(row[key])
        self.assertEqual(before, s.c.POLICY)
