import copy
import io
import json
import unittest
from unittest.mock import patch

import run_split_domain_signed_tests as subject


class SplitDomainSignedTests(unittest.TestCase):
    def test_only_exact_three_packages_and_domain64_are_configured(self):
        subject.config_contract(subject.CONFIG)
        self.assertEqual(len(subject.CONFIG),16)
        for name in ('domain-ir','hwpx-package','hwpx-agent-cli'):
            entries=[x for x in subject.CONFIG if f'package.{name}.' in x]
            self.assertEqual(len(entries),5)
            self.assertIn(f'profile.test.package.{name}.opt-level=1',entries)
            self.assertIn(f'profile.test.package.{name}.debug-assertions=true',entries)
            self.assertIn(f'profile.test.package.{name}.overflow-checks=true',entries)
        self.assertIn('profile.test.package.domain-ir.codegen-units=64',subject.CONFIG)
        self.assertEqual(subject.CONFIG[:11],subject.BASE_CONFIG)

    def test_checks_scope_or_codegen_relaxation_is_denied(self):
        for wrong in (list(subject.CONFIG),subject.CONFIG[:-1],subject.CONFIG+('profile.test.opt-level=3',),
                tuple(x.replace('assertions=true','assertions=false') for x in subject.CONFIG),
                tuple(x.replace('checks=true','checks=false') for x in subject.CONFIG),
                tuple(x.replace('domain-ir.codegen-units=64','domain-ir.codegen-units=16') for x in subject.CONFIG)):
            with self.assertRaises(ValueError):subject.config_contract(wrong)

    def test_duration_is_not_extended_for_original_signed16(self):
        for task,maximum in ((subject.INVENTORY,600),(subject.PROFILE,180)):
            subject.require_duration(task,maximum)
            for bad in (True,29,maximum+1,1200):
                with self.assertRaises(ValueError):subject.require_duration(task,bad)

    def test_closed_fresh_inventory_path_run(self):
        self.assertEqual(subject.inventory_path(1),'implementation/p09/evidence/p09-149-signed-split-domain.inventory-run01.v1.json')
        for bad in (True,0,100,'1'):
            with self.assertRaises(ValueError):subject.inventory_path(bad)

    def test_current_compile_gates_delegate_all_original_source_name_cleanup_checks(self):
        row={'source_variant':subject.VARIANT,'task':subject.INVENTORY,
            'test_package_profile_config':list(subject.CONFIG),'domain_test_codegen_units':64,
            'original_owned_resource_policy_changed':False}
        before=subject.previous.previous.CONFIG
        with patch.object(subject.previous,'accept_inventory') as accept:subject.accept_inventory(row,{},[],[])
        accept.assert_called_once()
        self.assertEqual(accept.call_args.args[0]['test_package_profile_config'],list(subject.CONFIG))
        self.assertIs(subject.previous.previous.CONFIG,before)
        for key,bad in (('source_variant','foreign'),('task','foreign'),('domain_test_codegen_units',16),
                ('original_owned_resource_policy_changed',True),('test_package_profile_config',list(subject.BASE_CONFIG))):
            wrong=copy.deepcopy(row);wrong[key]=bad
            with self.assertRaises(ValueError):subject.accept_inventory(wrong,{},[],[])

    def test_worker_preserves_exact_original_signed16_filter_and_environment(self):
        original=subject.previous.previous.previous.original
        from tests.test_optimized_signed_tests import OptimizedSignedTests
        env=OptimizedSignedTests().env();captured=[]
        def boundary(task):
            args=['cargo.exe',*original.ARGS,'--locked','--offline','--jobs','1','--color=never',
                '--target-dir',str(subject.maintenance.TARGET),'--',original.NAME,'--exact','--nocapture','--test-threads=1']
            return subject.subprocess.call(args,cwd=subject.maintenance.ROOT,stdin=subject.subprocess.DEVNULL,env=env)
        before=subject.previous.previous.CONFIG
        with patch.object(subject.previous.previous.previous,'run_worker',boundary), \
                patch.object(subject.subprocess,'call',side_effect=lambda args,**kwargs:captured.append((args,kwargs)) or 0):
            self.assertEqual(subject.run_worker(subject.PROFILE),0)
        args,kwargs=captured[0]
        self.assertEqual(args[1:33],[value for entry in subject.CONFIG for value in ('--config',entry)])
        self.assertEqual(args[-5:],['--',original.NAME,'--exact','--nocapture','--test-threads=1'])
        self.assertEqual(kwargs['env'],env)
        self.assertIs(subject.previous.previous.CONFIG,before)

    def test_worker_compiled_inventory_has_no_runtime_test_selection(self):
        original=subject.previous.previous.previous.original
        from tests.test_optimized_signed_tests import OptimizedSignedTests
        captured=[]
        def boundary(task):
            args=['cargo.exe',*original.ARGS,'--locked','--offline','--jobs','1','--color=never',
                '--target-dir',str(subject.maintenance.TARGET),'--','--list','--format','terse']
            return subject.subprocess.call(args,cwd=subject.maintenance.ROOT,stdin=subject.subprocess.DEVNULL,
                env=OptimizedSignedTests().env())
        with patch.object(subject.previous.previous.previous,'run_worker',boundary), \
                patch.object(subject.subprocess,'call',side_effect=lambda args,**kwargs:captured.append(args) or 0):
            self.assertEqual(subject.run_worker(subject.INVENTORY),0)
        self.assertEqual(captured[0][-4:],['--','--list','--format','terse'])
        self.assertNotIn('--exact',captured[0])

    def test_original_real_GO_and_Job_membership_launch_gate_is_preserved(self):
        from tests.test_stored_signed_continuation import StoredSignedContinuationTests
        helper=StoredSignedContinuationTests();original=subject.previous.previous.previous.original
        self.assertEqual(helper.worker(original.CHANGED)[0],0)
        for go,in_job in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError):helper.worker(original.CHANGED,go=go,in_job=in_job)

    def test_annotation_never_claims_whole249_SQL_native_or_Gate(self):
        stream=io.StringIO()
        def terminal(*args):
            json.dump({'state':'STOPPED_NOT_ACCEPTED','stop_reason':'STOP_DURATION_LIMIT'},stream)
            return 2
        before=subject.previous.previous.CONFIG
        with patch.object(subject.previous,'run_owned',side_effect=terminal):
            self.assertEqual(subject.run_owned(None,{},[],[],{},subject.PROFILE,180),2)
        row=json.loads(stream.getvalue())
        self.assertEqual(row['source_variant'],subject.VARIANT)
        self.assertFalse(row['product_complete']);self.assertFalse(row['full249_current_qualified'])
        self.assertFalse(row['original_owned_resource_policy_changed'])
        self.assertIs(subject.previous.previous.CONFIG,before)

    def test_shared_resource_policy_and_reader_helpers_remain_unpatched(self):
        import scheduled_binding_resources as resources
        before=copy.deepcopy(subject.maintenance.POLICY)
        reader=resources.AuditEvidenceReader.__init__
        with self.assertRaises(ValueError):subject.run_worker('foreign-tests')
        self.assertEqual(subject.maintenance.POLICY,before)
        self.assertIs(resources.AuditEvidenceReader.__init__,reader)
