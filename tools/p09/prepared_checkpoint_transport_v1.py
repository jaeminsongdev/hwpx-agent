"""Explicit lossless checkpoint carrier; no original raw Native-lock claim.

원 checkpoint의 모든 바이트를 복원·검사한 뒤 원 scope 검사를 그대로
호출한다. 실제 reader 원장에는 읽은 carrier만 기록하며 캐시하지 않는다.
"""
import hashlib
import json
import runtime_record_envelope_v2 as codec
import runtime_envelope_physical_io_v1 as physical
import prepared_scope_handoff_v1 as original

SELF="tools/p09/prepared_checkpoint_transport_v1.py"
TEST="tools/p09/tests/test_prepared_checkpoint_transport_v1.py"

def require(ok,label):
    if not ok:raise ValueError("PREPARED_CHECKPOINT_TRANSPORT_"+label)

class Reader:
    def __init__(self,q,semantic_pin,physical_pin):
        self.q=q;self.semantic=original.prepared.pin(semantic_pin)
        self.physical=original.prepared.pin(physical_pin)
        require(self.semantic["path"]!=self.physical["path"],"DISTINCT_EXPLICIT_REPRESENTATIONS")
        require(self.semantic["bytes"]<=original.MAX_CHECKPOINT_BYTES and
            self.physical["bytes"]<=original.MAX_CHECKPOINT_BYTES,"BOUNDED_CHECKPOINT_REPRESENTATIONS")
        self.budget=physical.DecoderBudget(q.checkpoint)
        self.snapshots=q.snapshots;self.checkpoint=q.checkpoint
    def json(self,path):
        require(path==self.physical["path"],"ONLY_EXACT_CARRIER_READ")
        actual,buffer=self.q._read(path,parse=True);self.q._bind(path,actual)
        require(original.same(actual,self.physical),"ACTUAL_PHYSICAL_BYTE_PIN")
        raw=bytes(buffer)
        header=json.loads(raw.decode("utf-8"),object_pairs_hook=codec.unique)
        require(type(header) is dict and type(header.get("original_bytes")) is int
            and header["original_bytes"]==self.semantic["bytes"]
            and header.get("original_sha256")==self.semantic["sha256"],"EXACT_ORIGINAL_BEFORE_EXPANSION")
        decoded=self.budget.run(lambda check:codec.decode(raw,check))
        require(len(decoded)==self.semantic["bytes"] and hashlib.sha256(decoded).hexdigest()==self.semantic["sha256"],
            "ALL_ORIGINAL_CHECKPOINT_BYTES_RESTORED")
        self.q.checkpoint()
        row=json.loads(decoded.decode("utf-8"),object_pairs_hook=codec.unique)
        self.q.checkpoint()
        return row

def load(q,semantic_pin,physical_pin,binding,**expected):
    reader=Reader(q,semantic_pin,physical_pin)
    scope,rust,proof=original.load(reader,reader.physical,binding,**expected)
    require(proof.pop("checkpoint_original_added_to_required_scope") is True,"ORIGINAL_FULL_CHECKER_RETAINED")
    require(scope.get(reader.physical["path"])==reader.physical and reader.semantic["path"] not in scope,
        "EXPLICIT_PHYSICAL_CHECKPOINT_NOT_RELABELED_RAW_IO")
    proof.update(checkpoint_physical_transport_added_to_required_scope=True,
        checkpoint_semantic_original_pin=dict(reader.semantic),checkpoint_physical_pin=dict(reader.physical),
        exact_original_checkpoint_bytes_decoded=True,semantic_original_claimed_as_live_raw_Native_input=False,
        actual_runtime_Native_semantic_relation_and_independent_oracle_still_require_qualification=True,
        preparatory_decoder_attempts=reader.budget.attempts,preparatory_decoder_completed=reader.budget.completed,
        preparatory_decoder_elapsed_seconds=reader.budget.elapsed,preparatory_decoder_limit_seconds=5.0,
        file_bytes_hash_or_JSON_cache=False)
    return scope,rust,proof
