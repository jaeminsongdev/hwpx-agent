import copy
import unittest
import probe_receipt_codec_candidates_v1 as MODULE

ENCODER=DECODER=None


class Tests(unittest.TestCase):
    def rows(self):
        return [dict(schema_version="hwpx-agent.p09-lossless-runtime-source-projection/v1",next_case=165,
            semantic_original_pin=dict(path=f"implementation/p09/evidence/p09-361-case112-current-runtime-run{i:03}.v1.json",bytes=1000+i,sha256="a"*64),
            physical_envelope_pin=dict(path=f"implementation/p09/evidence/p361-lossless-runtime-inputs/case112-runtime-run{i:03}"+
                (".level6.envelope.v1.json" if i<=61 else ".failed.envelope.v1.json"),bytes=100+i,sha256="b"*64)) for i in range(1,69)]

    def test_sample_selection_keeps_all_table_entries_and_is_deterministic(self):
        rows=self.rows();before=copy.deepcopy(rows);selected=MODULE.select(rows)
        self.assertEqual(rows,before);self.assertEqual(selected,[rows[60],rows[59],rows[58]])
        with self.assertRaises(ValueError):MODULE.select(rows[:-1])
        rows[-1]=copy.deepcopy(rows[0])
        with self.assertRaises(ValueError):MODULE.select(rows)

    def test_current_product_source_unknown_or_partial_table_is_rejected(self):
        for key,value in (("next_case",True),("schema_version","unknown")):
            rows=self.rows();rows[0][key]=value
            with self.assertRaises(ValueError):MODULE.select(rows)
        for path in ("tools/p09/source.py","implementation/p09/evidence/p09-361-case165-current-runtime-run007.v1.json"):
            rows=self.rows();rows[0]["semantic_original_pin"]["path"]=path
            with self.assertRaises(ValueError):MODULE.select(rows)

    def test_deflate9_has_complete_inverse_same_checkpoints_and_original_decoder(self):
        raw=bytes(range(256))*1025;original=ENCODER;changed=MODULE.deflate9(original)
        old=[];new=[]
        original(raw,lambda:old.append(True));encoded=changed(raw,lambda:new.append(True))
        self.assertEqual(old,new);self.assertEqual(DECODER(encoded,lambda:None),raw)
        constants=list(changed.__code__.co_consts);i=next(i for i,v in enumerate(constants) if type(v) is int and v==9)
        constants[i]=1;self.assertEqual(changed.__code__.replace(co_consts=tuple(constants)),original.__code__)
        with self.assertRaises(ValueError):MODULE.deflate9(changed)
