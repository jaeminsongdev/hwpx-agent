"""Integrated real entry/identity byte guards using memory-only Binding models."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import current_queue_successor_connections as metadata
import native011_worker_transport as transport
import native011_zlib_binding as zlib
import native011_package as module


class Native011PackageContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[3]
        cls.worker = transport.connect((root/transport.SOURCE['path']).read_bytes())
        cls.binding = zlib.connect((root/zlib.SOURCE['path']).read_bytes())

    def fixture(self):
        self.calls = []; self.references = []
        rows = [{'model_descriptor':i} for i in range(162)]
        manifest_raw = b'new-model-manifest'; manifest_pin = self.binding.pin(zlib.MANIFEST,manifest_raw)
        old_wire = b'original-reference'; old_wire_pin = self.binding.pin(transport.PREFIX+'successor-worker-capsule009.compact.v6.json',old_wire)
        previous = dict(schema_version='original-schema',index=165,run=9,
            step=dict(index=165,before=158,prior_queue_pin={'prior':'queue'},prior_candidate_pin={'prior':'candidate'}),
            capsule_pin=old_wire_pin,manifest_pin={'old':'manifest'},first_descriptor={'old':'first'},
            historical_pairs=[],historical_provenance={})
        old_raw = self.binding.canonical(previous)
        declaration = NS(REFERENCE_MANIFEST={'original':'manifest'},
            REFERENCE_BOOTSTRAP=self.binding.pin(transport.PREFIX+'successor-worker-bootstrap009.v6.json',old_raw),
            REFERENCE_WIRE=old_wire_pin)
        def reference():
            obj = NS(binding=NS(manifest_pin=declaration.REFERENCE_MANIFEST),
                binding_module=NS(source=NS(scope='scope')))
            self.references.append(obj); return obj
        def connect(*args):
            self.calls.append('full-constructor')
            return NS(binding=NS(descriptors=lambda:copy.deepcopy(rows),manifest_pin=manifest_pin),
                manifest_pin=manifest_pin,manifest_raw=manifest_raw)
        def worker_graph(*args):
            prepared = args[7]; self.calls.append('graph')
            raw = b'original-complete-inner'; expected = dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            def encode(binding,authority,prior,guard):
                self.calls.append('encode'); return raw,expected
            def decode(data,pin,guard):
                self.calls.append('decode')
                self.assertEqual(data,raw); self.assertEqual(pin,expected)
                return NS(descriptors=lambda:copy.deepcopy(rows),manifest_pin=manifest_pin),{}
            wire = self.worker.identity_wire(NS(TASK=transport.TASK,MAX_BYTES=16384,encode=encode,decode=decode),lambda:None)
            return NS(graph=NS(worker=wire),runtime=NS(validate_worker_hint=lambda core,task:(165,11)))
        binding = NS(**vars(self.binding)); binding.connect=connect; binding.worker_graph=worker_graph
        references = {declaration.REFERENCE_BOOTSTRAP['path']:old_raw,declaration.REFERENCE_WIRE['path']:old_wire}
        def read(pin,maximum):
            self.calls.append('read-reference'); self.assertEqual(maximum,16384); return references[pin['path']]
        def reconstruct(prior,packet,guard):
            self.calls.append('reference-constructor'); self.assertEqual(prior,previous)
            self.assertEqual(packet,old_wire); return reference(),{}
        constructor = NS(metadata=metadata,read_reference=read,reconstruct=reconstruct)
        return (None,None,{},constructor,None,None,reference(),previous,declaration,None,None,binding,self.worker,lambda:None)

    def test_real_new_identity_and_entry_integrate_without_disk_or_history_suite(self):
        args = self.fixture(); original = copy.deepcopy(args[7])
        result = module.prepare(*args)
        self.assertEqual([pin['path'] for pin in result.pins],[zlib.MANIFEST,zlib.WIRE,zlib.BOOTSTRAP])
        self.assertEqual(self.calls,['full-constructor','graph','encode','read-reference','read-reference',
            'reference-constructor','full-constructor','graph','decode'])
        self.assertEqual(args[7],original)
        self.assertEqual(result.entry.core['run'],11)
        self.assertEqual(len(self.references),2)
        self.assertFalse(result.proof['files_published'])
        self.assertFalse(result.proof['GO_authorized'])
        self.assertFalse(result.proof['fresh_physical_new_file_IO_claimed'])

    def test_wrong_reference_or_task_stops_before_any_constructor(self):
        args = list(self.fixture()); args[6].binding.manifest_pin={'wrong':'manifest'}
        with self.assertRaisesRegex(ValueError,'PACKAGE_ORIGINAL009_REFERENCE'):
            module.prepare(*args)
        self.assertEqual(self.calls,[])
        args = list(self.fixture()); args[12]=NS(TASK='case165-current-r010-tests')
        with self.assertRaisesRegex(ValueError,'PACKAGE_NEW_TASK'):
            module.prepare(*args)
        self.assertEqual(self.calls,[])


if __name__ == '__main__':
    unittest.main()
