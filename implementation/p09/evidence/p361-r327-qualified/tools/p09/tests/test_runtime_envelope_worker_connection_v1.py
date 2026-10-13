import builtins
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime_envelope_worker_connection_v1 as m
from test_runtime_envelope_scope_binding_v1 import fixture


def capsule():
    binding, *_ = fixture()
    data, pin = m.encode(binding, m.AUTHORITY, m.ROOT, lambda: None)
    return binding, data, pin


def altered(row):
    data = json.dumps(row, ensure_ascii=True).encode("ascii")
    return data, dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


class Tests(unittest.TestCase):
    def test_roundtrip_retains_every_descriptor_without_history_IO(self):
        before, data, pin = capsule()
        with patch.object(builtins, "open", side_effect=AssertionError("UNEXPECTED_IO")), \
                patch.object(Path, "open", side_effect=AssertionError("UNEXPECTED_IO")):
            after, proof = m.decode(data, pin, lambda: None)
        self.assertEqual(after.descriptors(), before.descriptors())
        self.assertEqual(dict(after.manifest_pin), dict(before.manifest_pin))
        self.assertEqual(proof["historical_receipt_files_read_by_capsule_decoder"], 0)
        self.assertFalse(proof["GO_authorized"])

    def test_transport_hash_or_size_change_denied(self):
        _, data, pin = capsule()
        for changed in (dict(pin, bytes=pin["bytes"]+1), dict(pin, sha256="0"*64)):
            with self.assertRaises(ValueError): m.decode(data, changed, lambda: None)

    def test_size_and_type_checked_before_json_decode(self):
        for data in (b"", b"x"*(m.MAX_BYTES+1), "not bytes", bytearray(b"{}")):
            with self.assertRaises(ValueError): m.decode(data, {}, lambda: None)

    def test_closed_context_rejects_unknown_field_boolean_and_wrong_authority(self):
        _, data, _ = capsule(); row = json.loads(data)
        for changed in (dict(row, extra=True), dict(row, next_case=True),
                dict(row, accepted_count_before=150), dict(row, authority151_pin=m.ROOT)):
            raw, pin = altered(changed)
            with self.assertRaises(ValueError): m.decode(raw, pin, lambda: None)

    def test_duplicate_JSON_fields_rejected_even_with_matching_transport_hash(self):
        _, data, _ = capsule(); data = data[:-1]+b',"next_case":158}'
        pin = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        with self.assertRaisesRegex(ValueError, "DUPLICATE_KEY"):
            m.decode(data, pin, lambda: None)

    def test_encoder_requires_exact151_and157_anchors(self):
        binding, *_ = fixture()
        for authority, root in ((dict(m.AUTHORITY, bytes=1), m.ROOT), (m.AUTHORITY, m.AUTHORITY)):
            with self.assertRaises(ValueError): m.encode(binding, authority, root, lambda: None)

    def test_original_checkpoint_exception_precedes_decoder(self):
        _, data, pin = capsule(); error = ValueError("ORIGINAL_RESOURCE_STOP")
        def stop(): raise error
        with self.assertRaises(ValueError) as caught: m.decode(data, pin, stop)
        self.assertIs(caught.exception, error)

    def test_original_worker_function_identity_args_return_and_globals_unchanged(self):
        binding, *_ = fixture(); seen=[]; token=object()
        def worker(task): seen.append(task); return token
        original=(worker.__code__, worker.__defaults__, worker.__closure__, worker.__globals__)
        policy=m.raw_policy.Policy(Path.cwd(), binding, lambda: True, lambda: None)
        execute, state=m.connect_worker(worker, policy)
        self.assertIs(execute(m.TASK), token); self.assertEqual(seen, [m.TASK])
        self.assertIs(state.original, worker)
        self.assertEqual((worker.__code__,worker.__defaults__,worker.__closure__,worker.__globals__),original)
        self.assertTrue(policy.restored)

    def test_blocked_raw_worker_path_restores_APIs_and_does_not_retry(self):
        binding, *_ = fixture(); name=next(iter(binding.originals))
        def worker(task): return (Path.cwd()/name).open("rb")
        policy=m.raw_policy.Policy(Path.cwd(), binding, lambda: True, lambda: None)
        execute,state=m.connect_worker(worker,policy)
        with self.assertRaisesRegex(ValueError,"STOP_LIVE_RAW"): execute(m.TASK)
        self.assertEqual(policy.raw_attempts,1);self.assertTrue(policy.restored)
        with self.assertRaisesRegex(ValueError,"NO_AUTOMATIC_RETRY"): execute(m.TASK)
        self.assertEqual(state.calls,1)

    def test_original_worker_error_identity_returned_not_relabelled(self):
        binding, *_=fixture(); error=OSError("ORIGINAL_WORKER_FAILED")
        def worker(task): raise error
        policy=m.raw_policy.Policy(Path.cwd(),binding,lambda:True,lambda:None)
        execute,state=m.connect_worker(worker,policy)
        with self.assertRaises(OSError) as caught: execute(m.TASK)
        self.assertIs(caught.exception,error);self.assertTrue(policy.restored)
        self.assertFalse(state.completed)

    def test_wrong_task_rejected_before_worker_and_policy_install(self):
        binding,*_=fixture();calls=[]
        def worker(task):calls.append(task)
        policy=m.raw_policy.Policy(Path.cwd(),binding,lambda:True,lambda:None)
        execute,state=m.connect_worker(worker,policy)
        for task in ("case157-current-r001-tests", "case158-current-r002-tests", True):
            with self.assertRaises(ValueError):execute(task)
        self.assertEqual(state.attempts,0);self.assertEqual(calls,[]);self.assertFalse(policy.installed)

    def test_evidence_never_promotes_to_product_dispatch_or_OS_sandbox(self):
        binding,*_=fixture()
        def worker(task):return 2
        policy=m.raw_policy.Policy(Path.cwd(),binding,lambda:True,lambda:None)
        execute,state=m.connect_worker(worker,policy);self.assertEqual(execute(m.TASK),2)
        proof=m.evidence(state,policy)
        self.assertFalse(proof["current158_whole_worker_dispatch_qualified"])
        self.assertFalse(proof["product_or_Gate_qualified"])
        self.assertTrue(proof["external_Rust_child_and_unwrapped_OS_APIs_not_guarded"])


if __name__=="__main__":unittest.main()
