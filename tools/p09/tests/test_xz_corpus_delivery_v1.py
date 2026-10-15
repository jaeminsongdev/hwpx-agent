import copy
import hashlib
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
import xz_corpus_delivery_v1 as MODULE


class Tests(unittest.TestCase):
    def fixture(self):
        rows=[];samples=[]
        for index in range(61):
            stem=f"implementation/p09/evidence/p361-lossless-runtime-inputs/case112-runtime-run{index+1:03}"
            row=dict(schema_version="hwpx-agent.p09-lossless-runtime-source-projection/v1",next_case=165,
                semantic_original_pin=dict(path=f"implementation/p09/evidence/p09-361-case112-current-runtime-run{index+1:03}.v1.json",bytes=100,sha256="a"*64),
                physical_envelope_pin=dict(path=stem+".level6.envelope.v1.json",bytes=90,sha256="b"*64))
            rows.append(row);samples.append(dict(semantic_original_pin=row["semantic_original_pin"],existing_physical_pin=row["physical_envelope_pin"],
                proposed_physical_pin=dict(path=stem+".xz8m.envelope.v1.json",bytes=20,sha256="c"*64)))
        for index in range(7):
            rows.append(dict(schema_version="hwpx-agent.p09-lossless-runtime-source-projection/v1",next_case=165,
                semantic_original_pin=dict(path=f"special{index}",bytes=1,sha256="d"*64),
                physical_envelope_pin=dict(path=f"special{index}.failed.envelope.v1.json",bytes=2,sha256="e"*64)))
        measured=dict(state="PASS_ORDINARY61_XZ_MEASUREMENT_NOT_FULL68_PROFILE_OR_RUNTIME",cleanup_confirmed=True,GO_authorized=False,
            accepted_count_delta=0,Native_or_product_executed=False,fresh_inputs=211,final_fresh_hashes=211,
            decoder_budget=dict(aggregate_limit_seconds=5.,attempted_decodes=122,completed_decodes=122,elapsed_decoder_work_seconds=2.,active_decode=False,terminal_error_seen=False),
            candidates=samples,special_descriptors_unchanged=rows[61:])
        return rows,measured

    def planned(self):
        rows,measured=self.fixture()
        with patch.object(MODULE,"ORDINARY_DIGEST",MODULE.digest(rows[:61])):return MODULE.plan(rows,measured,1)

    def test_full_mapping_preserves_semantics_specials_order_and_input_objects(self):
        rows,measured=self.fixture();before=copy.deepcopy((rows,measured))
        with patch.object(MODULE,"ORDINARY_DIGEST",MODULE.digest(rows[:61])):result=MODULE.plan(rows,measured,1)
        self.assertEqual((rows,measured),before);self.assertEqual(result[61:],rows[61:])
        self.assertEqual([r["semantic_original_pin"] for r in result],[r["semantic_original_pin"] for r in rows])
        self.assertEqual(sum(MODULE.is_xz(r) for r in result),61)

    def test_generation_is_finite_and_has_no_overwrite_path_alias(self):
        rows,m=self.fixture()
        with patch.object(MODULE,"ORDINARY_DIGEST",MODULE.digest(rows[:61])):
            first=MODULE.plan(rows,m,1);last=MODULE.plan(rows,m,8)
            self.assertNotEqual(first[0]["physical_envelope_pin"]["path"],last[0]["physical_envelope_pin"]["path"])
            for value in (True,0,9,"1"):
                with self.assertRaises(ValueError):MODULE.plan(rows,m,value)

    def test_missing_duplicate_reordered_or_modified_source_rows_rejected(self):
        rows,m=self.fixture();variants=[rows[:-1]];changed=copy.deepcopy(rows);changed[0],changed[1]=changed[1],changed[0];variants.append(changed)
        changed=copy.deepcopy(rows);changed[0]["semantic_original_pin"]["sha256"]="0"*64;variants.append(changed)
        changed=copy.deepcopy(rows);changed[-1]=copy.deepcopy(changed[-2]);variants.append(changed)
        with patch.object(MODULE,"ORDINARY_DIGEST",MODULE.digest(rows[:61])):
            for variant in variants:
                with self.assertRaises(ValueError):MODULE.plan(variant,m,1)

    def test_incomplete_or_runtime_measurement_cannot_authorize_publication(self):
        rows,m=self.fixture()
        with patch.object(MODULE,"ORDINARY_DIGEST",MODULE.digest(rows[:61])):
            for key,value in (("cleanup_confirmed",False),("GO_authorized",True),("Native_or_product_executed",True),("accepted_count_delta",False),("final_fresh_hashes",210)):
                bad=copy.deepcopy(m);bad[key]=value
                with self.assertRaises(ValueError):MODULE.plan(rows,bad,1)
            bad=copy.deepcopy(m);bad["decoder_budget"]["elapsed_decoder_work_seconds"]=5.
            with self.assertRaises(ValueError):MODULE.plan(rows,bad,1)

    def test_changed_specials_new_path_or_duplicate_candidate_cannot_slip_through(self):
        rows,m=self.fixture();variants=[]
        bad=copy.deepcopy(m);bad["special_descriptors_unchanged"][0]["physical_envelope_pin"]["bytes"]+=1;variants.append(bad)
        bad=copy.deepcopy(m);bad["candidates"][0]["proposed_physical_pin"]["path"]="outside.envelope.v1.json";variants.append(bad)
        bad=copy.deepcopy(m);bad["candidates"][-1]=copy.deepcopy(bad["candidates"][0]);variants.append(bad)
        with patch.object(MODULE,"ORDINARY_DIGEST",MODULE.digest(rows[:61])):
            for bad in variants:
                with self.assertRaises(ValueError):MODULE.plan(rows,bad,1)

    def test_logical_oracle_rejects_changed_raw_bytes_and_nonbytes(self):
        raw=b"original";pin=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        MODULE.verify_decoded(raw,pin)
        for value in (b"changed!",bytearray(raw)):
            with self.assertRaises(ValueError):MODULE.verify_decoded(value,pin)

    def test_two_fresh_reader_calls_route61_and7_without_decode_cache(self):
        pairs=self.planned();raw=b"original";original=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());calls=[]
        for pair in pairs:pair["semantic_original_pin"].update(original)
        pins={r["physical_envelope_pin"]["path"]:r["physical_envelope_pin"] for r in pairs}
        class Base:
            def _read(self,name,parse=False):return pins[name],bytearray(b"encoded")
        class Budget:
            def run(self,fn):return fn(lambda:None)
        def decoder(label):
            def decode(data,check):calls.append(label);check();return raw
            return NS(decode=decode)
        def exact(left,right,label):self.assertEqual(left,right)
        counts={};Reader=MODULE.reader_type(Base,pairs,Budget(),decoder("xz"),decoder("old"),counts,exact);reader=Reader()
        for _ in range(2):
            for pair in pairs:self.assertIsNone(reader._read(pair["physical_envelope_pin"]["path"])[1])
        self.assertEqual((calls.count("xz"),calls.count("old")),(122,14));self.assertEqual(set(counts.values()),{2})
        self.assertEqual(len(counts),68)

    def test_reader_guard_or_wrong_physical_pin_failure_is_not_cached_or_relabelled(self):
        pairs=self.planned();counts={};calls=[]
        class Base:
            def _read(self,name,parse=False):return dict(wrong=True),bytearray(b"encoded")
        class Budget:
            def run(self,fn):calls.append(True);raise ValueError("ORIGINAL_STOP")
        def exact(left,right,label):
            if left!=right:raise ValueError("ORIGINAL_PHYSICAL_PIN_MISMATCH")
        Reader=MODULE.reader_type(Base,pairs,Budget(),NS(),NS(),counts,exact)
        with self.assertRaisesRegex(ValueError,"ORIGINAL_PHYSICAL_PIN_MISMATCH"):Reader()._read(pairs[0]["physical_envelope_pin"]["path"])
        self.assertEqual(calls,[]);self.assertEqual(counts,{})
        class Correct(Base):
            def _read(self,name,parse=False):return pairs[0]["physical_envelope_pin"],bytearray(b"encoded")
        Reader=MODULE.reader_type(Correct,pairs,Budget(),NS(decode=lambda *a:None),NS(),counts,exact)
        with self.assertRaisesRegex(ValueError,"ORIGINAL_STOP"):Reader()._read(pairs[0]["physical_envelope_pin"]["path"])
        self.assertEqual(calls,[True]);self.assertEqual(counts,{})

    def test_lossless_seed_requires_original_identity_after_original_budget(self):
        raw=b"opaque\x00\xff";pin=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());calls=[]
        class Budget:
            def run(self,fn):calls.append("budget");return fn(lambda:calls.append("guard"))
        def decode(encoded,check):check();self.assertEqual(encoded,b"existing");return raw
        self.assertEqual(MODULE.decode_seed(b"existing",pin,decode,Budget()),raw)
        self.assertEqual(calls,["budget","guard"])
        with self.assertRaises(ValueError):MODULE.decode_seed(b"existing",dict(pin,sha256="0"*64),decode,Budget())

    def test_observation_uses_only_fresh_original_samples_and_preserves_stop(self):
        class Original:
            def __init__(self):self.samples=[]
            def check(self,force=False):
                if not force:return "cached"
                self.samples.append(dict(system_cpu_percent=92.,parent_cpu_machine_percent=1.,available_ram_percent=20.,parent_private_percent=.1))
                raise ValueError("ORIGINAL_STOP")
        metrics={};phase=dict(value="write");guard=MODULE.observed_guard(Original,metrics,phase)()
        self.assertEqual(guard.check(),"cached");self.assertEqual(metrics,{})
        with self.assertRaisesRegex(ValueError,"ORIGINAL_STOP"):guard.check(force=True)
        self.assertEqual(metrics["write"]["fresh_samples"],1);self.assertEqual(metrics["write"]["parent_CPU_max"],1.)
        self.assertEqual(len(guard.samples),1)

    def test_missing_observation_stays_missing_not_a_fabricated_zero(self):
        metrics={};MODULE.resource_observation(metrics,"admission",dict(system_cpu_percent=30.,parent_cpu_machine_percent=None))
        self.assertIsNone(metrics["admission"]["parent_CPU_max"]);self.assertEqual(metrics["admission"]["parent_CPU_missing_samples"],1)
        with self.assertRaises(ValueError):MODULE.resource_observation(metrics,"unbounded",{})
