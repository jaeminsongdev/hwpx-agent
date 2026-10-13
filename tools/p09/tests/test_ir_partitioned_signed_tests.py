import copy
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_ir_partitioned_signed_tests as s


class IrPartitionedSignedTests(unittest.TestCase):
    def test_closed86_only_IR_package_added(self):
        s.config_contract(s.CONFIG);self.assertEqual(s.CONFIG[:81],s.BASE_CONFIG)
        self.assertEqual(len(s.IR_CONFIG),5)
        self.assertTrue(all(x.startswith('profile.test.package.domain-ir.') for x in s.IR_CONFIG))
        for wrong in (list(s.CONFIG),s.CONFIG[:-1],(*s.CONFIG,'profile.test.opt-level=3')):
            with self.assertRaises(ValueError):s.config_contract(wrong)

    def test_same_assertions_and_partition64(self):
        for required in ('opt-level=1','debug-assertions=true','overflow-checks=true','codegen-units=64','debug="line-tables-only"'):
            self.assertIn('profile.test.package.domain-ir.'+required,s.CONFIG)

    def test_finite_original_inventory_and_runtime_scope(self):
        s.require_scope(s.INVENTORY,600);s.require_scope(s.PROFILE,180)
        for task,seconds in ((s.INVENTORY,601),(s.PROFILE,181),(s.PROFILE,True),('wrong',180)):
            with self.assertRaises(ValueError):s.require_scope(task,seconds)

    def test_adapter_restores_original81_and_policy(self):
        before = (s.base.CONFIG,s.base.SELF,s.base.INVENTORY,s.base.PROFILE,s.base.config_contract)
        policy = copy.deepcopy(s.c.POLICY)
        with s.adapter():self.assertEqual(s.base.CONFIG,s.CONFIG);s.base.config_contract(s.CONFIG)
        self.assertEqual(before,(s.base.CONFIG,s.base.SELF,s.base.INVENTORY,s.base.PROFILE,s.base.config_contract))
        self.assertEqual(policy,s.c.POLICY)

    def worker(self,task,go='P149_GO\n',member=True):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=member;return True
        calls = []
        with patch.object(s.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(s.c.sys,'stdin',io.StringIO(go)),patch.object(s.c.shutil,'which',return_value='cargo'), \
                patch.object(s.subprocess,'call',side_effect=lambda a,**kw:calls.append((a,kw)) or 0):
            result = s.worker(task)
        return result,calls

    def test_worker_exact86_inventory_and_signed_scope(self):
        for task in (s.INVENTORY,s.PROFILE):
            result,calls = self.worker(task);self.assertEqual(result,0);self.assertEqual(len(calls),1)
            args,kw = calls[0];offset = 1+2*len(s.CONFIG)
            self.assertEqual(args[1:offset],[v for e in s.CONFIG for v in ('--config',e)])
            self.assertIn('--locked',args);self.assertIn('--offline',args)
            self.assertEqual(kw['env']['CARGO_BUILD_JOBS'],'1')
            self.assertEqual(kw['env']['CARGO_PROFILE_TEST_DEBUG_ASSERTIONS'],'true')
            self.assertEqual(kw['env']['CARGO_PROFILE_TEST_OVERFLOW_CHECKS'],'true')
            if task == s.INVENTORY:self.assertIn('--list',args)
            else:
                self.assertIn(s.base.signed.previous.original.NAME,args)
                self.assertIn('--exact',args);self.assertIn('--test-threads=1',args)
            self.assertNotIn('--ignored',args);self.assertNotIn('--skip',args)

    def test_worker_requires_real_GO_and_job(self):
        for go,member in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError):self.worker(s.INVENTORY,go,member)

    def test_compile15_runtime10_admission_unchanged(self):
        with s.adapter():
            self.assertEqual(s.base.admission_ram_percent(s.INVENTORY),15)
            self.assertEqual(s.base.admission_ram_percent(s.PROFILE),10)

    def test_new_inventory_not_old_profile_required(self):
        names = [s.base.signed.previous.original.NAME,*[f'fixture::case{i}' for i in range(248)]]
        with s.adapter():
            with self.assertRaises(ValueError):s.base.accept_inventory({'test_package_profile_config':list(s.BASE_CONFIG)}, {},names,['module']*59)
