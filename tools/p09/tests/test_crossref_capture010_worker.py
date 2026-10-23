"""No process starts: exact fixed worker command and unchanged lifecycle inheritance."""
import inspect,json,unittest
from pathlib import Path
from unittest.mock import patch
import crossref_capture010_worker as worker

class Reader:
    def __init__(self):self.root=worker.original.prior.original.c.ROOT;self.snapshots={};self.calls=[]
    def pin(self,path):
        self.calls.append(path)
        value=dict(path=path,bytes=1,sha256='a'*64)
        if path==worker.original.prior.original.BOOTSTRAP:value['sha256']=worker.original.prior.original.BOOTSTRAP_SHA
        if path==worker.namespace.PROBE:value.update(bytes=worker.PROBE_PIN[0],sha256=worker.PROBE_PIN[1])
        self.snapshots[path]=value;return value

class Capture010Worker(unittest.TestCase):
    def test_fixed010_command_pins_all_inputs_and_uses_original_waiting_bootstrap(self):
        reader=Reader();command=worker.command(reader);args=json.loads(command[-1])
        self.assertEqual(reader.calls,list(worker.SOURCES));self.assertEqual(command[-2],'--worker')
        self.assertTrue(command[2].endswith(worker.original.prior.original.BOOTSTRAP.replace('/','\\')))
        self.assertEqual(args[-2:], [str(reader.root/worker.TARGET),'-FixedEightAfterSession'])
        self.assertNotIn('--retry',args);self.assertNotIn('--case',args)

    def test_original_default_worker_command_is_unchanged(self):
        reader=Reader();old=object.__new__(worker.original.FixedWorker)
        self.assertEqual(old._fixed_command(reader),worker.original.command(Reader()))
        self.assertIn(str(reader.root/worker.original.TARGET),json.loads(old._fixed_command(Reader())[-1]))

    def test_fixed010_reuses_exact_non_killing_worker_lifecycle_and_limits(self):
        self.assertIs(worker.Fixed010Worker.start_fixed_worker,worker.original.FixedWorker.start_fixed_worker)
        self.assertIs(worker.Fixed010Worker.observe,worker.original.FixedWorker.observe)
        self.assertIs(worker.Fixed010Worker.close,worker.original.FixedWorker.close)
        self.assertEqual(set(worker.Fixed010Worker.__dict__)-{'__module__','__doc__'}, {'_fixed_command'})
        reader=Reader();current=object.__new__(worker.Fixed010Worker)
        self.assertEqual(current._fixed_command(reader),worker.command(Reader()))

    def test_foreign_root_is_denied_before_any_input_or_process(self):
        reader=Reader();reader.root=reader.root.parent
        with self.assertRaises(ValueError):worker.command(reader)
        self.assertEqual(reader.calls,[])

    def test_wrong_probe_size_or_digest_and_wrong_bootstrap_remain_denied(self):
        for field in ('bytes','sha256','bootstrap'):
            class BadReader(Reader):
                def pin(self,path):
                    value=super().pin(path)
                    if path==worker.namespace.PROBE and field!='bootstrap':value[field]=0 if field=='bytes'else'0'*64
                    if path==worker.original.prior.original.BOOTSTRAP and field=='bootstrap':value['sha256']='0'*64
                    return value
            with self.assertRaises(ValueError):worker.command(BadReader())

    def test_command_builders_never_start_processes_and_have_no_selector_arguments(self):
        with patch('subprocess.Popen',side_effect=AssertionError('NO_PROCESS_START')):
            worker.command(Reader());worker.original.command(Reader())
        self.assertEqual(list(inspect.signature(worker.command).parameters),['reader'])
        self.assertEqual(worker.PROBE_PIN,(5152256,'379d55499a0e4acefb323fc0904e03809f099416239c2c6757fe2b5d2a76a46c'))

