"""Models only: original audit body over exact inherited live capabilities."""
import hashlib
import time
from types import SimpleNamespace as NS
import unittest
import audit_evidence_io as audit
import owned_source_read_pressure as pressure
import native011_inherited_audit_reader as bridge
import native011_inherited_source_probe_child as child


class InheritedAuditContracts(unittest.TestCase):
    def fixture(self,body=b'{"value":7}\n'):
        pin=dict(path='tools/p09/model.py',bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
        row=dict(handle=10,pin=pin,identity=[1,2])
        class Kernel:
            def __init__(self):self.flags=True;self.offset=0;self.body=body;self.wrong_id=False;self.closed=[]
            def info(self,handle):return dict(identity=[1,3] if self.wrong_id else [1,2],size=len(body),
                directory=False,reparse=False,inheritable=self.flags)
            def clear_inheritance(self,handle):self.flags=False
            def reset(self,handle):self.offset=0
            def readinto(self,handle,view):
                raw=self.body[self.offset:self.offset+len(view)];view[:len(raw)]=raw;self.offset+=len(raw);return len(raw)
            def close(self,handle):self.closed.append(handle);return True
        api=Kernel();source=child.SourceReader([row],api,lambda:None,lambda size:None);source.admit()
        cap=bridge.HeldSources(source);Reader=bridge.reader_type(audit.AuditEvidenceReader,audit,pressure,cap)
        reader=Reader('.',lambda:None)
        return reader,cap,api,pin

    def test_original_hash_parse_bind_and_full_closing_methods_retained(self):
        reader,cap,_,pin=self.fixture();self.assertEqual(reader.json(pin['path']),{'value':7});reader.finish()
        for name in ('pin','json','text','fresh_pin','_bind','finish'):
            self.assertIs(getattr(type(reader),name),getattr(audit.AuditEvidenceReader,name))
        self.assertEqual(reader.final_fresh_hashes,1);self.assertEqual(reader.read_passes,2)
        self.assertEqual(cap.completed,{pin['path']:2});self.assertEqual(cap.actual_bytes,2*pin['bytes'])
        self.assertIs(reader.pacer.clock,time.perf_counter);self.assertTrue(cap.source.close())

    def test_fresh_pin_really_rereads_without_source_cache(self):
        reader,cap,_,pin=self.fixture();reader.pin(pin['path']);reader.fresh_pin(pin['path']);reader.finish()
        self.assertEqual(cap.completed[pin['path']],3);self.assertEqual(reader.read_passes,3)
        self.assertFalse(cap.summary()['source_byte_hash_or_AST_cache']);self.assertTrue(cap.source.close())

    def test_changed_closing_bytes_are_not_cached_or_accepted(self):
        reader,cap,api,pin=self.fixture();reader.pin(pin['path']);api.body=b'X'*pin['bytes']
        with self.assertRaisesRegex(ValueError,'FRESH_ENTIRE_BYTES_AND_REAL_EOF'):reader.finish()
        self.assertTrue(cap.source.failed);self.assertEqual(reader.final_fresh_hashes,0)
        self.assertIsNone(cap.busy);self.assertTrue(cap.source.close())

    def test_original_parse_limit_still_rejects_oversized_input(self):
        reader,cap,_,pin=self.fixture();reader.maximum_parse_bytes=1
        with self.assertRaisesRegex(ValueError,'audit_parse_budget_exceeded'):reader.json(pin['path'])
        self.assertTrue(cap.source.failed);self.assertIsNone(cap.busy);self.assertTrue(cap.source.close())

    def test_no_unknown_pathname_fallback(self):
        reader,cap,_,_=self.fixture()
        with self.assertRaisesRegex(ValueError,'NO_PATHNAME_FALLBACK'):reader.pin('tools/p09/other.py')
        self.assertEqual(cap.actual_reads,0);self.assertTrue(cap.source.close())

    def test_wrong_os_identity_rejected_before_any_read(self):
        reader,cap,api,pin=self.fixture();api.wrong_id=True
        with self.assertRaisesRegex(ValueError,'LIVE_PRE_READ_OS_IDENTITY'):reader.pin(pin['path'])
        self.assertEqual(cap.actual_reads,0);self.assertTrue(cap.source.failed);self.assertTrue(cap.source.close())

    def test_no_overlapping_stream_or_cross_stream_offset_use(self):
        _,cap,_,pin=self.fixture()
        with cap.stream(pin['path']) as first:
            with self.assertRaisesRegex(ValueError,'ONE_SAME_OWNER_STREAM'):cap.stream(pin['path']).__enter__()
            first.read(65536);first.read(65536)
        self.assertTrue(cap.source.close())

    def test_partial_read_cannot_qualify_as_complete_fresh_read(self):
        _,cap,_,pin=self.fixture()
        with self.assertRaisesRegex(ValueError,'FRESH_ENTIRE_BYTES_AND_REAL_EOF'):
            with cap.stream(pin['path']) as stream:stream.read(1)
        self.assertEqual(cap.completed,{});self.assertTrue(cap.source.failed);self.assertTrue(cap.source.close())

    def test_closed_or_reused_stream_cannot_read(self):
        _,cap,_,pin=self.fixture();stream=cap.stream(pin['path'])
        with stream:stream.read(65536);stream.read(65536)
        with self.assertRaises(ValueError):stream.read(1)
        with self.assertRaises(ValueError):stream.__enter__()
        self.assertTrue(cap.source.close())

    def test_import_uses_new_bytes_and_real_module_namespace_not_pyc(self):
        _,cap,_,pin=self.fixture(b'VALUE=7\n');finder=bridge.SourceImports('.',cap,lambda size:None)
        self.assertIsNone(finder.find_spec('undeclared'))
        spec=finder.find_spec('model');self.assertIs(spec.loader,finder)
        module=NS(__name__='model');finder.exec_module(module)
        self.assertEqual(module.VALUE,7);self.assertEqual(finder.loaded,[pin['path']])
        self.assertEqual(cap.completed,{pin['path']:1});self.assertTrue(cap.source.close())

    def test_closed_reader_or_wrong_owner_cannot_be_admitted(self):
        _,cap,_,_=self.fixture();cap.source.close()
        with self.assertRaises(ValueError):bridge.HeldSources(cap.source)

    def test_bounded_direct_source_allocation_does_not_skip_hash_or_eof(self):
        _,cap,_,pin=self.fixture()
        with self.assertRaises(ValueError):cap.read_bytes(pin['path'],1,lambda size:None)
        raw=cap.read_bytes(pin['path'],100,lambda size:None)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),pin['sha256'])
        self.assertEqual(cap.completed,{pin['path']:1});self.assertTrue(cap.source.close())
