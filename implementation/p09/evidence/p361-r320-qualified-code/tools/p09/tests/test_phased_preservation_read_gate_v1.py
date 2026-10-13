import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import phased_preservation_read_gate_v1 as m

def pin(n,size=1):return dict(path=n,bytes=size,sha256="0"*64)
H=pin("implementation/p09/evidence/history.json");N=pin("target/current.exe")
WHOLE={H["path"]:H,N["path"]:N}
def gate():return m.Gate(WHOLE,{N["path"]:N},{H["path"]:H},identity=lambda:(1,2))
class Held:
    acquired=True;closed=False
    def acquire(self,rows):return self
    def check(self):pass
    def close(self):self.closed=True;return True
    def summary(self):return dict(input_lock_handles_remaining=0,input_lock_cleanup_confirmed=True,input_lock_handles_opened=2,input_lock_handles_closed=2)
def frame(g):
    f=m.frames.Frame(m.frames.Registry(),g.native,lambda:None,held=Held())
    f.acquire();return f
def committed(f):
    # A mock commit is NOT runtime evidence. It isolates gate state contracts.
    f.boundaries=[dict(role=role,actual_byte_pins=[dict(p) for p in f.inputs.values()],
        reader_diagnostics=dict(read_passes=len(f.inputs),bytes_read=sum(p["bytes"] for p in f.inputs.values()),original_owned_read_operations_preserved=True)) for role in ("before","after")]
    f.owned_cleanup_seen=True;f.identity_after=dict(held_identity_checks_complete=True)
    f.close();f.state="COMMITTED";return f
def reader(fn=None):return NS(checkpoint=lambda:None,_read=fn or (lambda name,parse=False:(name,parse)))

class Tests(unittest.TestCase):
    def test_lossless_partition_overlap_missing_changed_pin_denied(self):
        for native,historical in ((WHOLE,{H["path"]:H}),({N["path"]:N},{}),({N["path"]:pin(N["path"],2)},{H["path"]:H})):
            with self.assertRaises(ValueError):m.Gate(WHOLE,native,historical)
    def test_serialized_frame_not_live_authority(self):
        g=gate()
        with self.assertRaises(ValueError):g.native_started(list(WHOLE.values()),{"frame_state":"COMMITTED"})
    def test_no_native_start_without_exact_initial_whole_bytes(self):
        g=gate();f=frame(g)
        with self.assertRaises(ValueError):g.native_started([N],f)
        f.close()
    def test_same_live_frame_scope_and_reference_required(self):
        g=gate();f=frame(g);g.native_started(list(WHOLE.values()),f)
        with self.assertRaises(ValueError):g.native_finished({})
        f.close()
    def test_historical_read_blocked_before_original_io_during_native(self):
        g=gate();calls=[];r=reader(lambda name,parse=False:calls.append(name));g.bind(r)
        f=frame(g);g.native_started(list(WHOLE.values()),f)
        with self.assertRaisesRegex(ValueError,"HISTORICAL_READ_DURING_NATIVE"):r._read(H["path"],parse=True)
        self.assertEqual(calls,[]);g.restore();f.close()
    def test_forwarded_return_parse_and_original_error_identity_preserved(self):
        g=gate();obj=object();calls=[];r=reader(lambda name,parse=False:(calls.append((name,parse)),obj)[1]);g.bind(r)
        self.assertIs(r._read(N["path"],parse=True),obj);self.assertEqual(calls,[(N["path"],True)])
        g.restore();error=ValueError("ORIGINAL_READ_ERROR")
        def fail(name,parse=False):raise error
        gg=gate();rr=reader(fail);gg.bind(rr)
        with self.assertRaises(ValueError) as ctx:rr._read(N["path"])
        self.assertIs(ctx.exception,error);gg.restore()
    def test_original_hard_error_precedes_gate_and_no_io(self):
        g=gate();calls=[];error=ValueError("ORIGINAL_HARD_STOP")
        def hard():raise error
        r=reader(lambda name,parse=False:calls.append(name));r.checkpoint=hard;g.bind(r)
        with self.assertRaises(ValueError) as ctx:r._read(N["path"])
        self.assertIs(ctx.exception,error);self.assertEqual(calls,[]);g.restore()
    def test_finish_before_native_cleanup_and_changed_final_hash_denied(self):
        g=gate();f=frame(g);g.native_started(list(WHOLE.values()),f)
        with self.assertRaises(ValueError):g.finish(list(WHOLE.values()))
        g.native_finished(committed(f))
        with self.assertRaises(ValueError):g.finish([N,pin(H["path"],2)])
    def test_whole_closing_allows_historical_read_then_closes_reads(self):
        g=gate();r=reader();g.bind(r);f=frame(g);g.native_started(list(WHOLE.values()),f)
        g.native_finished(committed(f));self.assertEqual(r._read(H["path"]),(H["path"],False))
        g.finish(list(WHOLE.values()))
        with self.assertRaises(ValueError):r._read(N["path"])
        g.restore()
    def test_restore_exact_original_and_idempotent_without_sampling(self):
        g=gate();r=reader();old=r._read;g.bind(r)
        r.checkpoint=lambda:self.fail("cleanup sampled")
        g.restore();g.restore();self.assertIs(r._read,old)
    def test_foreign_owner_rejected(self):
        g=gate();g.identity=lambda:(1,3)
        with self.assertRaises(ValueError):g.finish(list(WHOLE.values()))
    def test_contract_only_diagnostics_never_authorize_product_or_queue(self):
        g=gate();d=g.diagnostics()
        for key in ("Native_scope_selection_authorized","actual_whole_byte_reads_proven","actual_Native_product_qualified","queue_advance_authorized","PC_freeze_resolved"):
            self.assertIs(d[key],False)
        self.assertEqual(d["accepted_count_delta"],0)
    def test_changed_binding_is_not_restored_over_user_handler(self):
        g=gate();r=reader();g.bind(r);changed=lambda name,parse=False:None;r._read=changed
        with self.assertRaises(ValueError):g.restore()
        self.assertIs(r._read,changed)
    def test_empty_or_wrong_native_byte_boundary_rejected(self):
        g=gate();f=frame(g);g.native_started(list(WHOLE.values()),f);committed(f)
        f.boundaries[1]["actual_byte_pins"]=[H]
        with self.assertRaises(ValueError):g.native_finished(f)

if __name__=="__main__":unittest.main()
