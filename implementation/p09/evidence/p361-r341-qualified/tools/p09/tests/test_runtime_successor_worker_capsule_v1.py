import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_successor_worker_capsule_v1 as m
import runtime_successor_binding_v1 as successor
import runtime_failed_receipt_projection_v1 as first
import runtime_failed_receipt_projection_v2 as second
import runtime_envelope_worker_connection_v1 as original
from test_runtime_successor_binding_v1 import lineage
from test_runtime_failed_receipt_projection_v1 import graph


class Tests(unittest.TestCase):
    def setup_api(self):
        source,binding=graph();successor.connect(binding,lineage(),first,second)
        api,proof=m.connect(original,binding,successor.AUTHORITY,successor.ROOT,successor)
        desc=[source.descriptor(f.ROOT,dict(path=f.PHYSICAL,bytes=1,sha256="a"*64),next_case=159) for f in (first,second)]
        manifest=dict(path="implementation/p09/evidence/future159.json",bytes=1,sha256="b"*64)
        return api,binding.Binding(desc,manifest,next_case=159),proof
    def test_closed159_wire_authority152_and_exact_shared_Binding_roundtrip(self):
        api,binding,_=self.setup_api()
        data,pin=api.encode(binding,successor.AUTHORITY,successor.ROOT,lambda:None)
        row=json.loads(data)
        self.assertEqual(set(row),{"schema_version","next_case","accepted_count_before","manifest_pin","descriptors","authority_pin","prior_runtime_pin"})
        self.assertEqual(row["next_case"],159);self.assertEqual(row["accepted_count_before"],152)
        decoded,_=api.decode(data,pin,lambda:None)
        self.assertIs(type(decoded),type(binding));self.assertEqual(decoded.descriptors(),binding.descriptors())
    def test_metadata_inverse_restores_all_original_encoder_decoder_code(self):
        api,_,_=self.setup_api()
        for name in ("encode","decode"):
            new=getattr(api,name);old=getattr(original,name)
            self.assertEqual(new.__code__.replace(co_consts=tuple(m.constant(x,True) for x in new.__code__.co_consts)),old.__code__)
            self.assertIs(new.__defaults__,old.__defaults__);self.assertIs(new.__closure__,old.__closure__)
    def test_wrong_or_boolean_context_rejected_even_with_recomputed_transport_pin(self):
        api,binding,_=self.setup_api();data,_=api.encode(binding,successor.AUTHORITY,successor.ROOT,lambda:None)
        for values in (dict(next_case=True),dict(next_case=158),dict(accepted_count_before=151)):
            row=dict(json.loads(data),**values);raw=json.dumps(row).encode("ascii")
            with self.assertRaises(ValueError):api.decode(raw,dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),lambda:None)
    def test_bad_transport_pin_and_extra_wire_key_rejected(self):
        api,binding,_=self.setup_api();data,pin=api.encode(binding,successor.AUTHORITY,successor.ROOT,lambda:None)
        with self.assertRaises(ValueError):api.decode(data,dict(pin,sha256="0"*64),lambda:None)
        row=dict(json.loads(data),extra=True);raw=json.dumps(row).encode("ascii")
        with self.assertRaises(ValueError):api.decode(raw,dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),lambda:None)
    def test_original_worker_dispatch_code_and_default_namespace_retained(self):
        old=original.connect_worker;task=original.TASK;api,_,proof=self.setup_api()
        self.assertIs(api.connect_worker.__code__,old.__code__)
        self.assertIs(api.connect_worker.__defaults__,old.__defaults__)
        self.assertIs(api.connect_worker.__closure__,old.__closure__)
        self.assertEqual(original.TASK,task);self.assertEqual(api.TASK,m.TASK)
        self.assertFalse(proof["actual159_worker_or_GO_qualified"])
    def test_exact_original_resource_stop_identity_before_codec(self):
        api,binding,_=self.setup_api();error=ValueError("ORIGINAL_RESOURCE_STOP")
        def stop():raise error
        with self.assertRaises(ValueError) as caught:api.encode(binding,successor.AUTHORITY,successor.ROOT,stop)
        self.assertIs(caught.exception,error)


if __name__=="__main__":unittest.main()
