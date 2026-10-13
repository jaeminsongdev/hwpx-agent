import unittest
from unittest.mock import patch
import build_observed_writer_product_r2 as d

class WorkerRecipeBindingTests(unittest.TestCase):
    def test_actual_worker_recipe_is_r06_and_restored(self):
        before=d.d.RUN;calls=[]
        def inner(task):
            recipe=d.d.recipe()
            return d.prior.progress_command(['fixture-cargo',*recipe['argv_without_cargo']],{},None)
        def command(args,kw,validator):calls.append(args);return 0
        with patch.object(d.b,'worker',inner),patch.object(d.prior,'RAW_COMMAND',command):
            self.assertEqual(d.worker(d.b.task_for(6)),0)
        self.assertEqual(calls[0][-2:],['-C','extra-filename=-p152-r06'])
        self.assertEqual(d.d.RUN,before)
    def test_wrong_r05_command_rejected_inside_worker(self):
        old=d.d.recipe()['argv_without_cargo']
        with patch.object(d.b,'worker',side_effect=lambda task:d.prior.progress_command(['fixture',*old],{},None)):
            with self.assertRaises(ValueError):d.worker(d.b.task_for(6))
    def test_original_worker_handoff_go_and_environment(self):
        import io
        from types import SimpleNamespace
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=True;return True
        calls=[];clean={k:'' for k in ('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTC_WRAPPER',
            'RUSTC_WORKSPACE_WRAPPER','RUSTC','CARGO_BUILD_TARGET')}
        with patch.object(d.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(d.c.sys,'stdin',io.StringIO('P149_GO\n')), \
                patch.object(d.c.shutil,'which',return_value='fixture-cargo'),patch.dict(d.c.os.environ,clean), \
                patch.object(d.prior,'RAW_COMMAND',side_effect=lambda args,kw,validator:calls.append((args,kw)) or 0):
            self.assertEqual(d.worker(d.b.task_for(6)),0)
        self.assertEqual(calls[0][0][-2:],['-C','extra-filename=-p152-r06'])
        self.assertEqual(calls[0][1]['env']['CARGO_INCREMENTAL'],'0')
        self.assertEqual(calls[0][1]['env']['RUSTUP_AUTO_INSTALL'],'0')

if __name__=='__main__':unittest.main()
