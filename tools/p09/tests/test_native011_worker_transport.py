"""Memory transport contracts, not full162 data/worker/Native qualification."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_worker_transport as module


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode('ascii')


def pin(raw, path=None):
    row = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    if path is not None:
        row['path'] = path
    return row


class Native011TransportContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (Path(__file__).resolve().parents[3] / module.SOURCE['path']).read_bytes()

    def api(self):
        return module.connect(self.raw)

    def worker(self, task=module.TASK):
        self.calls = []
        def encode(binding, authority, prior, guard):
            guard(); self.calls.append(('encode', binding, authority, prior))
            return b'original-inner', pin(b'original-inner')
        def decode(raw, expected, guard):
            guard(); self.calls.append(('decode', raw, expected))
            self.assertEqual(raw, b'original-inner'); self.assertEqual(expected, pin(raw))
            return 'complete-binding', dict(original_decoder=True)
        return NS(TASK=task, MAX_BYTES=16384, encode=encode, decode=decode)

    def test_fresh_source_exact_private_construction_only(self):
        api = self.api()
        self.assertEqual(api.TASK, module.TASK)
        self.assertEqual(set(vars(api)), {'TASK','BOOTSTRAP','WIRE','identity_wire','transport_graph','reconstruct','proof'})
        for key in ('wire','graph','entry'):
            self.assertTrue(api.proof[key]['exact_recursive_inverse'])
        self.assertFalse(api.proof['Native_or_GO_qualified'])
        with self.assertRaisesRegex(ValueError, 'ORIGINAL_SOURCE_BYTES'):
            module.connect(self.raw + b'\n')

    def test_run011_wire_roundtrip_preserves_inner_decoder(self):
        checks = []
        check = lambda: checks.append(True)
        wire = self.api().identity_wire(self.worker(), check)
        raw, expected = wire.encode('binding','authority','prior',check)
        self.assertTrue(raw.startswith(b'P09I11\n'))
        self.assertEqual(wire.decode(raw,expected,check)[0], 'complete-binding')
        self.assertEqual([c[0] for c in self.calls], ['encode','decode'])
        self.assertGreaterEqual(len(checks), 6)
        self.assertTrue(wire.decode(raw,expected,check)[1]['outer_transport_hash_and_exact_run011_checked'])

    def test_old_task_wire_hash_or_case_cannot_be_relabelled(self):
        api = self.api()
        with self.assertRaises(ValueError):
            api.identity_wire(self.worker('case165-current-r010-tests'), lambda: None)
        wire = api.identity_wire(self.worker(), lambda: None)
        raw, expected = wire.encode(None,None,None,lambda: None)
        for invalid in (raw.replace(b'P09I11',b'P09I10',1),
                        raw.replace(b'"run":11',b'"run":10',1),
                        raw.replace(b'"index":165',b'"index":166',1)):
            with self.assertRaises(ValueError):
                wire.decode(invalid,pin(invalid),lambda: None)
        with self.assertRaises(ValueError):
            wire.decode(raw,dict(expected,sha256='0'*64),lambda: None)
        self.assertEqual([c[0] for c in self.calls], ['encode'])

    def test_original_wire_limits_and_inner_pin_are_unchanged(self):
        api = self.api(); base = self.worker()
        for raw, expected in ((b'x'*16385, pin(b'x'*16385)), (b'inner',pin(b'other'))):
            base.encode = lambda *args, r=raw, p=expected: (r,p)
            wire = api.identity_wire(base,lambda: None)
            with self.assertRaises(ValueError):
                wire.encode(None,None,None,lambda: None)

    def test_graph_future_bound_is_private_and_exactly_run011_case165(self):
        from types import FunctionType
        api = self.api(); events = []
        def worker_api(worker, compact, binding, step, run):
            if not 1 <= run <= 8:
                raise ValueError('ORIGINAL_RUN_BOUND')
            return 'original-worker-result'
        def validate_worker_hint(hint, task):
            if not 2 <= hint['run'] <= 8:
                raise ValueError('ORIGINAL_HINT_BOUND')
            return hint['index'], hint['run']
        old_worker, old_hint = worker_api.__code__, validate_worker_hint.__code__
        metadata = NS(worker_api=FunctionType(old_worker,{}))
        runtime = NS(validate_worker_hint=FunctionType(old_hint,{}))
        def connect(root, loader, policy, binding_module, binding, step, run, check):
            events.append(run)
            self.assertEqual(metadata.worker_api(None,None,None,step,run),'original-worker-result')
            for bad_run in (8,10,12,True):
                with self.assertRaises(ValueError):
                    metadata.worker_api(None,None,None,step,bad_run)
            with self.assertRaises(ValueError):
                metadata.worker_api(None,None,None,dict(step,before=159),run)
            self.assertEqual(runtime.validate_worker_hint(dict(index=165,run=11),module.TASK),(165,11))
            return NS(worker=self.worker()), 'unchanged-construction'
        metadata.connect = connect
        libraries = NS(current_queue_successor_connections=metadata,current_queue_successor_runtime=runtime)
        known = {n:dict(path=n) for n in (
            'tools/p09/current_queue_successor_connections.py','tools/p09/current_queue_successor_runtime.py',
            'tools/p09/current_queue_successor_binding.py')}
        loader = NS(load=lambda *args:(libraries,{}))
        reference = NS(binding_module='binding-module',binding='binding')
        graph, actual_runtime = api.transport_graph(None,loader,known,
            NS(binary=NS(connect=lambda worker,check:(worker,{}))),
            NS(install=lambda *args:None),None,reference,dict(index=165,before=158),lambda:None)
        self.assertEqual(events,[11]); self.assertIs(actual_runtime,runtime)
        self.assertEqual(graph.worker.TASK,module.TASK)
        self.assertEqual(worker_api.__code__,old_worker)
        self.assertEqual(validate_worker_hint.__code__,old_hint)
        with self.assertRaises(ValueError):
            worker_api(None,None,None,dict(index=165,before=158),11)

    def test_entry_complete_model_retains_four_fresh_byte_admissions(self):
        api = self.api(); rows = [{'model':i} for i in range(162)]
        manifest = dict(path=module.PREFIX+'successor-run011-manifest001.v1.json',bytes=1,sha256='0'*64)
        old_wire = b'old-constructor'; new_wire = b'new-run011'
        reference_wire = pin(old_wire,module.PREFIX+'successor-worker-capsule009.compact.v6.json')
        previous = dict(run=9,index=165,capsule_pin=reference_wire,step={'model':'unchanged'})
        old_raw = canonical(previous)
        core = dict(index=165,run=11,step=previous['step'],capsule_pin=pin(new_wire,module.WIRE),
            manifest_pin=manifest,first_descriptor=rows[0])
        outer = dict(schema_version='hwpx-agent.p09-run011-worker-preparation/v1',execution=core,
            reference_bootstrap_pin=pin(old_raw,module.PREFIX+'successor-worker-bootstrap009.v6.json'),
            reference_wire_pin=reference_wire,reference_is_constructor_data_not_product_replay=True,GO_authorized=False)
        raw = canonical(outer); inputs = {module.BOOTSTRAP:raw,
            outer['reference_bootstrap_pin']['path']:old_raw,reference_wire['path']:old_wire,module.WIRE:new_wire}
        opened = []
        def read(p,limit):
            self.assertEqual(limit,16384); opened.append(p['path']); return inputs[p['path']]
        binding = NS(descriptors=lambda:rows,manifest_pin=manifest)
        def decode(data, expected, check):
            self.assertEqual(data,new_wire); self.assertEqual(expected,pin(new_wire)); return binding,{}
        graph = NS(worker=NS(TASK=module.TASK,decode=decode))
        runtime = NS(validate_worker_hint=lambda h,t:(165,11))
        result = api.reconstruct(module.TASK,pin(raw,module.BOOTSTRAP),read,
            lambda *args:(NS(binding=binding),{}),lambda *args:(graph,runtime),lambda:None)
        self.assertEqual(result.proof['metadata_byte_admissions'],4)
        self.assertEqual(result.proof['descriptor_count'],162)
        self.assertEqual(len(opened),4)
        self.assertFalse(result.proof['product_or_worker_body_or_process_executed'])
        opened.clear()
        with self.assertRaisesRegex(ValueError,'ENTRY_EXACT_TASK_BEFORE_IO'):
            api.reconstruct('case165-current-r010-tests',pin(raw,module.BOOTSTRAP),read,
                lambda:None,lambda:None,lambda:None)
        self.assertEqual(opened,[])

    def test_missing_or_noninverse_literal_projection_rejected(self):
        fn = lambda: (10,11)
        with self.assertRaisesRegex(ValueError,'ENTIRE_RECURSIVE_CODE_INVERSE'):
            module._project(fn,{}, {10:11})
        with self.assertRaisesRegex(ValueError,'EVERY_DECLARED_SLOT_PRESENT'):
            module._project(lambda:10,{}, {9:11})


if __name__ == '__main__':
    unittest.main()
