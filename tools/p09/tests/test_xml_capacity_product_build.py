import copy
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import build_xml_capacity_product as d

class XmlCapacityProductBuildTests(unittest.TestCase):
    def test_closed_parent_cannot_accept_historical_or_failed(self):
        for state in ('FAILED_NOT_ACCEPTED',d.PASS,'PASS_WRITER_XML_REUSE_DELTA_AND_ALL71_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE'):
            with self.assertRaises(ValueError):d.parent_scope(dict(state=state))
    def test_exact_r07_target_recipe(self):
        r=d.recipe();self.assertEqual(r['executable_path'],d.executable_name())
        self.assertEqual(r['argv_without_cargo'][-2:],['-C','extra-filename=-p152-r07'])
        self.assertEqual(r['argv_without_cargo'][r['argv_without_cargo'].index('--target-dir')+1],str(d.TARGET))
    def test_original_profile_limits_unfiltered_plan(self):
        before=copy.deepcopy(d.c.POLICY);r=d.recipe()
        self.assertEqual(len(r['test_package_profile_config']),81);self.assertEqual(r['test_package_profile_config'],list(d.b.CONFIG))
        self.assertEqual((r['compile_maximum_seconds'],r['full249_maximum_seconds']),(600,1200))
        self.assertEqual((r['compile_admission_RAM_percent'],r['runtime_admission_RAM_percent']),(15,10))
        self.assertTrue(r['full249_unfiltered_required']);self.assertEqual(d.c.POLICY,before)
    def test_foreign_worker_cannot_launch(self):
        with patch.object(d.b,'worker',side_effect=AssertionError('NO_LAUNCH')):
            for run in (5,6,8):
                with self.assertRaises(ValueError):d.worker(d.b.task_for(run))
    def test_worker_recipe_targets_restored(self):
        before=(d.b.TARGET,d.c.TARGET);calls=[]
        def inner(task):return d.progress_command(['fixture',*d.recipe()['argv_without_cargo']],{},None)
        with patch.object(d.b,'worker',inner),patch.object(d,'RAW_COMMAND',side_effect=lambda a,k,v:calls.append(a) or 0):
            self.assertEqual(d.worker(d.b.task_for(7)),0)
        self.assertEqual(calls[0][-2:],['-C','extra-filename=-p152-r07']);self.assertEqual((d.b.TARGET,d.c.TARGET),before)
    def test_original_go_membership_and_env(self):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=True;return True
        calls=[];clean={k:'' for k in ('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER','RUSTC','CARGO_BUILD_TARGET')}
        with patch.object(d.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(d.c.sys,'stdin',io.StringIO('P149_GO\n')),patch.object(d.c.shutil,'which',return_value='fixture-cargo'), \
                patch.dict(d.c.os.environ,clean),patch.object(d,'RAW_COMMAND',side_effect=lambda a,k,v:calls.append((a,k)) or 0):
            self.assertEqual(d.worker(d.b.task_for(7)),0)
        self.assertEqual(calls[0][0],['fixture-cargo',*d.recipe()['argv_without_cargo']])
        self.assertEqual(calls[0][1]['env']['CARGO_INCREMENTAL'],'0');self.assertEqual(calls[0][1]['env']['RUSTUP_AUTO_INSTALL'],'0')
    def test_foreign_command_rejected(self):
        with patch.object(d,'RAW_COMMAND',side_effect=AssertionError('NO_LAUNCH')):
            with self.assertRaises(ValueError):d.progress_command(['fixture','--old'],{},None)
    def test_no_recursive_original_stream_patch(self):
        original=d.b.CargoStream;seen=[]
        def command(args,kw,validator):seen.append((d.b.CargoStream,d.b.legacy.stream.CargoStream));return 0
        with patch.object(d,'RAW_COMMAND',command):self.assertEqual(d.progress_command(['fixture',*d.recipe()['argv_without_cargo']],{},None),0)
        self.assertEqual(seen,[(original,d.observed.progress.CargoStream)])
    def test_protected_library_overlap_rejected(self):
        with self.assertRaises(ValueError):d.fresh_scope({d.executable_name():{}})
    def test_reader_only_scoped_original_run_preserved(self):
        before=(d.c.AuditEvidenceReader,d.b.legacy.AuditEvidenceReader,d.p.RUN,d.b.TARGET,d.c.TARGET);seen=[]
        def run(destination,*binding):
            seen.append((d.c.AuditEvidenceReader,d.b.legacy.AuditEvidenceReader,d.p.RUN,d.b.TARGET,d.c.TARGET));return 2
        with patch.object(d.p,'run_owned',run):self.assertEqual(d.run_owned('fixture',({},[],[])),2)
        self.assertTrue(issubclass(seen[0][0],d.weighted.WeightedReader));self.assertIs(seen[0][0],seen[0][1])
        self.assertEqual(seen[0][2:],(7,d.TARGET,d.TARGET))
        self.assertEqual((d.c.AuditEvidenceReader,d.b.legacy.AuditEvidenceReader,d.p.RUN,d.b.TARGET,d.c.TARGET),before)
    def test_p152_original_parser_rejects_partial_stream(self):
        with self.assertRaises(ValueError):d.RAW_PARSE('{}\n',7,require_stream=True)
    def test_fresh_suffix_does_not_overlap_library(self):
        self.assertTrue(d.executable_name().endswith('form_stored_provider-p152-r07.exe'))
        self.assertNotIn('hwpx_package-',d.executable_name());self.assertEqual(d.RUN,7)

if __name__=='__main__':unittest.main()
