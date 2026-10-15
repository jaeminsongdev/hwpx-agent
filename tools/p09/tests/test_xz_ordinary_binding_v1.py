import copy
import hashlib
from types import SimpleNamespace as NS
import unittest


class Tests(unittest.TestCase):
    def data(self,actual=False):
        CHECKPOINT();prior=[];rows=[];encoded=None
        for i in range(1,69):
            old=dict(path=f"implementation/p09/evidence/p09-361-case112-current-runtime-run{i:03}.v1.json",bytes=100,sha256="a"*64)
            before=dict(path=f"implementation/p09/evidence/p361-lossless-runtime-inputs/case112-runtime-run{i:03}.envelope.v1.json",bytes=50,sha256="b"*64)
            after=dict(before,path=before["path"].replace(".envelope.v1.json",".xz8m-g001.envelope.v1.json"),bytes=40,sha256="c"*64) if i<=61 else before
            if actual and i==1:
                original=b"opaque\x00\xff raw\r\n";encoded=XZ.encode(original,CHECKPOINT)
                old.update(bytes=len(original),sha256=hashlib.sha256(original).hexdigest());after.update(bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            prior.append(dict(schema_version="hwpx-agent.p09-lossless-runtime-source-projection/v1",next_case=164,semantic_original_pin=old,physical_envelope_pin=before))
            rows.append(dict(prior[-1],next_case=165,physical_envelope_pin=after))
        module,_=API.connect(ROOT,LOADER,SCOPE,165,{},prior)
        spec=dict(MODULE.SPEC,mapping_sha256=MODULE.fingerprint(rows[:61]));pin=dict(path="implementation/p09/evidence/test-manifest.v1.json",bytes=1,sha256="d"*64)
        return module,prior,rows,spec,pin,encoded

    def test_all_original_binding_and_projection_methods_retained(self):
        m,prior,rows,spec,pin,_=self.data();methods={n:f for n,f in vars(m.Binding).items() if n!="__init__"};projection=dict(vars(m.source.Projection))
        MODULE.install(m,prior,XZ,spec);bound=m.Binding(rows,pin,next_case=165)
        self.assertEqual(bound.descriptors(),rows);self.assertTrue(all(vars(m.Binding)[n] is f for n,f in methods.items()))
        self.assertTrue(all(vars(m.source.Projection)[n] is f for n,f in projection.items()))
        projected,_=bound.project(SCOPE.pins([r["semantic_original_pin"] for r in rows]+[pin]),CHECKPOINT)
        self.assertEqual(len(projected.physical_pins),69)

    def test_original_table_still_uses_original_predicate(self):
        m,prior,rows,spec,pin,_=self.data();MODULE.install(m,prior,XZ,spec);old=[dict(r,next_case=165) for r in prior]
        self.assertEqual(m.Binding(old,pin,next_case=165).descriptors(),old)
        bad=copy.deepcopy(old);bad[-1]["physical_envelope_pin"]["sha256"]="e"*64
        with self.assertRaises(ValueError):m.Binding(bad,pin,next_case=165)

    def test_partial_or_modified_new_or_original_pins_rejected(self):
        for kind in ("partial","hash","original"):
            m,prior,rows,spec,pin,_=self.data();MODULE.install(m,prior,XZ,spec);bad=copy.deepcopy(rows)
            if kind=="partial":bad.pop()
            elif kind=="hash":bad[0]["physical_envelope_pin"]["sha256"]="f"*64
            else:bad[0]["semantic_original_pin"]["sha256"]="f"*64
            with self.assertRaises(ValueError):m.Binding(bad,pin,next_case=165)

    def test_current_failed_arbitrary_or_wrong_generation_xz_rejected(self):
        for kind in ("current","failed","arbitrary","generation"):
            m,prior,rows,spec,pin,_=self.data();MODULE.install(m,prior,XZ,spec);bad=copy.deepcopy(rows)
            if kind=="current":bad[0]["semantic_original_pin"]["path"]=bad[0]["semantic_original_pin"]["path"].replace("case112","case165")
            elif kind=="failed":bad[0]["physical_envelope_pin"]["path"]=bad[0]["physical_envelope_pin"]["path"].replace(".xz8m-",".failed.xz8m-")
            elif kind=="arbitrary":bad[0]["physical_envelope_pin"]["path"]="outside.xz8m-g001.envelope.v1.json"
            else:bad[0]["physical_envelope_pin"]["path"]=bad[0]["physical_envelope_pin"]["path"].replace("g001","g002")
            with self.assertRaises(ValueError):m.Binding(bad,pin,next_case=165)

    def test_private_namespace_context_and_no_level6_composition(self):
        class Projection:
            def __init__(self):pass
        with self.assertRaises(ValueError):MODULE.install(NS(source=NS(Projection=Projection)),[],XZ)
        for bad in (dict(MODULE.SPEC,index=True),dict(MODULE.SPEC,generation=9)):
            m,prior,rows,spec,pin,_=self.data()
            with self.assertRaises(ValueError):MODULE.install(m,prior,XZ,bad)
        m,prior,rows,spec,pin,_=self.data();m.level6_ordinary_profile={}
        with self.assertRaises(ValueError):MODULE.install(m,prior,XZ,spec)

    def test_idempotence_requires_identical_fixed_profile(self):
        m,prior,rows,spec,pin,_=self.data();MODULE.install(m,prior,XZ,spec);before=m.Binding.__init__
        MODULE.install(m,prior,XZ,spec);self.assertIs(before,m.Binding.__init__)
        with self.assertRaises(ValueError):MODULE.install(m,prior,XZ,dict(spec,mapping_sha256="f"*64))

    def test_only_one_scoped_metadata_seed_before_full68(self):
        m,prior,rows,spec,pin,_=self.data();MODULE.install(m,prior,XZ,spec);before=m.Binding.__init__
        with MODULE.bootstrap_seed(m,rows[0],pin):
            self.assertEqual(len(m.Binding([rows[0]],pin,next_case=165).descriptors()),1)
            with self.assertRaises(ValueError):m.Binding([rows[0]],pin,next_case=165)
            self.assertEqual(len(m.Binding(rows,pin,next_case=165).descriptors()),68)
        self.assertIs(before,m.Binding.__init__)

    def test_wrong_or_unused_seed_restores_original_constructor(self):
        for wrong in (True,False):
            m,prior,rows,spec,pin,_=self.data();MODULE.install(m,prior,XZ,spec);before=m.Binding.__init__
            with self.assertRaises(ValueError):
                with MODULE.bootstrap_seed(m,rows[0],pin):
                    if wrong:m.Binding([rows[1]],pin,next_case=165)
            self.assertIs(before,m.Binding.__init__)

    def test_two_fresh_xz_decodes_through_original_projection_byte_oracle(self):
        m,prior,rows,spec,pin,encoded=self.data(actual=True);MODULE.install(m,prior,XZ,spec);bound=m.Binding(rows,pin,next_case=165)
        projection,_=bound.project(SCOPE.pins([r["semantic_original_pin"] for r in rows]+[pin]),CHECKPOINT);pair=rows[0]
        for _ in range(2):self.assertEqual(projection.decode_fresh(pair["semantic_original_pin"]["path"],pair["physical_envelope_pin"],encoded,CHECKPOINT),b"opaque\x00\xff raw\r\n")
        bad=dict(pair["physical_envelope_pin"],sha256="e"*64)
        with self.assertRaises(ValueError):projection.decode_fresh(pair["semantic_original_pin"]["path"],bad,encoded,CHECKPOINT)

    def test_new_schema_cannot_decode_before_full_table_or_as_unknown_hash(self):
        m,prior,rows,spec,pin,encoded=self.data(actual=True);MODULE.install(m,prior,XZ,spec)
        with self.assertRaises(ValueError):m.source.codec.decode(encoded,CHECKPOINT)
        m.Binding(rows,pin,next_case=165)
        with self.assertRaises(ValueError):m.source.codec.decode(XZ.encode(b"unknown",CHECKPOINT),CHECKPOINT)

    def test_old_codec_is_unchanged_and_special_zlib_still_works(self):
        m,prior,rows,spec,pin,_=self.data();before=m.source.codec;decode=before.decode
        MODULE.install(m,prior,XZ,spec);m.Binding(rows,pin,next_case=165)
        self.assertIs(before,m.xz_original_codec);self.assertIs(before.decode,decode);self.assertIsNot(m.source.codec,before)
        encoded=before.encode(b"special",CHECKPOINT)
        self.assertEqual(m.source.codec.decode(encoded,CHECKPOINT),b"special")

    def test_original_guard_stop_propagates_without_decoder_retry(self):
        m,prior,rows,spec,pin,encoded=self.data(actual=True);MODULE.install(m,prior,XZ,spec);m.Binding(rows,pin,next_case=165);calls=[]
        def stopped():calls.append(True);raise ValueError("ORIGINAL_STOP")
        with self.assertRaisesRegex(ValueError,"ORIGINAL_STOP"):m.source.codec.decode(encoded,stopped)
        self.assertEqual(calls,[True])

    def test_full68_digest_and_ordinary_digest_are_not_timing_table_fingerprints(self):
        m,prior,rows,spec,pin,_=self.data()
        self.assertEqual(spec["mapping_sha256"],MODULE.fingerprint(rows[:61]));self.assertNotEqual(MODULE.fingerprint(rows),MODULE.fingerprint(rows[:61]))
        MODULE.install(m,prior,XZ,spec);m.Binding(rows,pin,next_case=165)
        self.assertEqual(rows, m.Binding(rows,pin,next_case=165).descriptors())
