import hashlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime_envelope_physical_io_v1 as m

class Clock:
    def __init__(self): self.value = 0.0
    def __call__(self): return self.value

def fixture():
    raw=b'{"original":true}\r\n'; encoded=m.source.codec.encode(raw,lambda:None)
    pin=lambda name,data:dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    logical=pin("implementation/p09/evidence/p09-361-case157-current-runtime-run001.v1.json",raw)
    physical=pin(m.source.PREFIX+"case157-runtime-run001.envelope.v1.json",encoded)
    desc=m.source.descriptor(logical,physical,next_case=158)
    p=m.source.Projection({logical["path"]:logical},[desc],next_case=158,checkpoint=lambda:None)
    return raw,encoded,logical,physical,p

class Tests(unittest.TestCase):
    def test_one_budget_shared_across_operations_and_exhaustion_latched(self):
        c=Clock(); b=m.DecoderBudget(lambda:None,c)
        def work(guard): c.value+=2.0;guard();return 1
        self.assertEqual(b.run(work),1);self.assertEqual(b.run(work),1)
        with self.assertRaisesRegex(ValueError,"STOP_AGGREGATE_ENVELOPE_DECODER5"):b.run(work)
        attempts=b.attempts
        with self.assertRaisesRegex(ValueError,"STOP_AGGREGATE_ENVELOPE_DECODER5"):b.run(work)
        self.assertEqual(b.attempts,attempts);self.assertIsNone(b.active)
        self.assertEqual(b.completed,2);self.assertEqual(b.elapsed,6.0)

    def test_original_guard_error_identity_precedes_decoder_error(self):
        c=Clock(); error=ValueError("ORIGINAL_HARD_STOP")
        b=m.DecoderBudget(lambda:None,c);b.error=ValueError("DECODER_STOP")
        def stop():raise error
        b.checkpoint=stop
        with self.assertRaises(ValueError) as caught:b.check()
        self.assertIs(caught.exception,error)

    def test_operation_error_identity_and_clock_cleanup_error_priority(self):
        c=Clock(); b=m.DecoderBudget(lambda:None,c);error=OSError("ORIGINAL_READ_FAILURE")
        def work(guard):c.value=-1;raise error
        with self.assertRaises(OSError) as caught:b.run(work)
        self.assertIs(caught.exception,error);self.assertIsNone(b.active)
        self.assertEqual(b.completed,0)

    def test_nonfinite_clock_owner_and_reentrance_rejected(self):
        c=Clock(); owner=[1];b=m.DecoderBudget(lambda:None,c,lambda:owner[0])
        owner[0]=2
        with self.assertRaisesRegex(ValueError,"EXACT_DECODER_OWNER"):b.run(lambda _:None)
        owner[0]=1;c.value=float("nan")
        with self.assertRaisesRegex(ValueError,"MONOTONIC_DECODER_CLOCK"):b.check()
        c.value=0.0
        with self.assertRaisesRegex(ValueError,"ONE_SERIAL_DECODER_OPERATION"):b.run(lambda _:b.run(lambda _:None))

    def test_idle_IO_time_does_not_erase_or_reset_work_budget(self):
        c=Clock();b=m.DecoderBudget(lambda:None,c)
        b.run(lambda _:setattr(c,"value",2.0));c.value+=100.0
        b.run(lambda _:setattr(c,"value",104.0))
        self.assertEqual(b.elapsed,4.0)
        self.assertEqual(b.evidence()["aggregate_limit_seconds"],5.0)

    def test_reader_two_fresh_physical_reads_decode_twice_return_physical_pin(self):
        raw,encoded,logical,physical,p=fixture(); calls=[]
        class Original:
            def __init__(self):pass
            def _read(self,name,parse=False):calls.append((name,parse));return physical,bytearray(encoded)
            def diagnostics(self):return dict(read_passes=len(calls),bytes_read=len(calls)*len(encoded))
        b=m.DecoderBudget(lambda:None);New=m.boundary_reader_type(Original,p,b)
        one,two=New(),New()
        self.assertEqual(one._read(physical["path"]),(physical,None))
        self.assertEqual(two._read(physical["path"]),(physical,None))
        self.assertEqual(calls,[(physical["path"],True)]*2)
        self.assertEqual(b.completed,2);self.assertEqual(one.semantic_decode_counts,{logical["path"]:1})
        self.assertEqual(two.semantic_decoded_bytes,len(raw));self.assertEqual(two.diagnostics()["bytes_read"],2*len(encoded))

    def test_untransformed_read_delegates_same_arguments_and_error(self):
        raw,encoded,logical,physical,p=fixture();calls=[];error=OSError("ORIGINAL_ERROR")
        class Original:
            def _read(self,name,parse=False):calls.append((name,parse));raise error
        New=m.boundary_reader_type(Original,p,m.DecoderBudget(lambda:None))
        with self.assertRaises(OSError) as caught:New()._read("crates/source.rs",parse=True)
        self.assertIs(caught.exception,error);self.assertEqual(calls,[("crates/source.rs",True)])

    def test_physical_pin_mismatch_fails_before_semantic_pass(self):
        raw,encoded,logical,physical,p=fixture()
        class Original:
            def _read(self,name,parse=False):return dict(physical,sha256="0"*64),bytearray(encoded)
        b=m.DecoderBudget(lambda:None);New=m.boundary_reader_type(Original,p,b)
        with self.assertRaisesRegex(ValueError,"ACTUAL_PHYSICAL_SOURCE_PIN"):New()._read(physical["path"])
        self.assertEqual(b.attempts,0)

    def test_parse_true_keeps_original_encoded_buffer_not_semantic_alias(self):
        raw,encoded,logical,physical,p=fixture();buffer=bytearray(encoded)
        class Original:
            def _read(self,name,parse=False):return physical,buffer
        New=m.boundary_reader_type(Original,p,m.DecoderBudget(lambda:None))
        actual,out=New()._read(physical["path"],parse=True)
        self.assertIs(out,buffer);self.assertEqual(actual,physical)

    def writer_patches(self,stream,exists=False):
        return (patch.object(Path,"is_dir",return_value=True),patch.object(Path,"is_symlink",return_value=False),
            patch.object(Path,"is_junction",return_value=False),patch.object(Path,"exists",return_value=exists),
            patch.object(Path,"open",return_value=stream),patch.object(m.os,"fsync"))

    def test_exclusive_chunked_publication_no_unbounded_write(self):
        raw,encoded,logical,physical,p=fixture()
        class Stream(io.BytesIO):
            def __exit__(self,*args):return False
            def fileno(self):return 1
        stream=Stream();patches=self.writer_patches(stream)
        with patches[0],patches[1],patches[2],patches[3],patches[4] as opening,patches[5]:
            self.assertEqual(m.publish_exclusive(Path.cwd(),encoded,physical,lambda:None),physical)
            opening.assert_called_once_with("xb")
        self.assertEqual(stream.getvalue(),encoded)

    def test_existing_destination_never_overwritten(self):
        raw,encoded,logical,physical,p=fixture();stream=io.BytesIO();patches=self.writer_patches(stream,True)
        with patches[0],patches[1],patches[2],patches[3],patches[4] as opening,patches[5]:
            with self.assertRaisesRegex(ValueError,"REFUSE_OVERWRITE"):m.publish_exclusive(Path.cwd(),encoded,physical,lambda:None)
            opening.assert_not_called()

    def test_short_write_fails_and_original_guard_error_is_not_wrapped(self):
        raw,encoded,logical,physical,p=fixture()
        class Stream(io.BytesIO):
            def write(self,value):return len(value)-1
        patches=self.writer_patches(Stream())
        with patches[0],patches[1],patches[2],patches[3],patches[4],patches[5]:
            with self.assertRaisesRegex(ValueError,"COMPLETE_CHUNK_WRITE"):m.publish_exclusive(Path.cwd(),encoded,physical,lambda:None)
        error=ValueError("ORIGINAL_STOP")
        def stop():raise error
        with self.assertRaises(ValueError) as caught:m.publish_exclusive(Path.cwd(),encoded,physical,stop)
        self.assertIs(caught.exception,error)

    def test_shared_original_pacer_charges_every_chunk_before_write(self):
        raw,encoded,logical,physical,p=fixture();raw=b"x"*(2*m.CHUNK+3)
        physical=dict(physical,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        pacer=m.bytes_policy.OwnedPacer();events=[];reserve=pacer.reserve;refund=pacer.refund
        def before(checkpoint):events.append("reserve");return reserve(checkpoint)
        def after(count):events.append(("refund",count));return refund(count)
        class Stream(io.BytesIO):
            def __exit__(self,*args):return False
            def fileno(self):return 1
            def write(self,data):events.append(("write",len(data)));return super().write(data)
        stream=Stream();patches=self.writer_patches(stream)
        with patches[0],patches[1],patches[2],patches[3],patches[4],patches[5], \
            patch.object(pacer,"reserve",side_effect=before),patch.object(pacer,"refund",side_effect=after):
            m.publish_exclusive(Path.cwd(),raw,physical,lambda:None,write_pacer=pacer)
        self.assertEqual(events,["reserve",("write",m.CHUNK),("refund",m.CHUNK),
            "reserve",("write",m.CHUNK),("refund",m.CHUNK),"reserve",("write",3),("refund",3)])
        self.assertEqual(pacer.bytes_paced,len(raw));self.assertEqual(pacer.rate,2097152)


if __name__=="__main__":unittest.main()
