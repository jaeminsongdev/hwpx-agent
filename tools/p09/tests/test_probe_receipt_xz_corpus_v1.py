import copy
from unittest.mock import patch
import unittest
import probe_receipt_codec_candidates_v1 as SAMPLE
import probe_receipt_xz_corpus_v1 as MODULE


class Tests(unittest.TestCase):
    def rows(self):
        result=[]
        for index in range(61):
            case=112+index%53;run=1+index//53
            result.append(dict(schema_version="hwpx-agent.p09-lossless-runtime-source-projection/v1",next_case=165,
                semantic_original_pin=dict(path=f"implementation/p09/evidence/p09-361-case{case:03}-current-runtime-run{run:03}.v1.json",bytes=100,sha256="a"*64),
                physical_envelope_pin=dict(path=f"implementation/p09/evidence/p361-lossless-runtime-inputs/case{case:03}-runtime-run{run:03}.level6.envelope.v1.json",bytes=90,sha256="b"*64)))
        for index in range(7):
            result.append(dict(schema_version="hwpx-agent.p09-lossless-runtime-source-projection/v1",next_case=165,
                semantic_original_pin=dict(path=f"special{index}",bytes=10,sha256="c"*64),
                physical_envelope_pin=dict(path=f"special{index}.failed.envelope.v1.json",bytes=8,sha256="d"*64)))
        return result

    def test_full61_preserves_all_original_rows_and_seven_special_descriptors(self):
        rows=self.rows();before=copy.deepcopy(rows)
        with patch.object(MODULE,"EXPECTED_TABLE",MODULE.fingerprint(rows[:61])):
            selected=MODULE.ordinary(rows,SAMPLE)
        self.assertEqual(selected,rows[:61]);self.assertEqual(rows,before)
        self.assertEqual(len([r for r in rows if r not in selected]),7)

    def test_count_digest_order_identity_and_current_product_are_not_relaxed(self):
        rows=self.rows();digest=MODULE.fingerprint(rows[:61]);cases=[]
        cases.append(rows[:-1]);changed=copy.deepcopy(rows);changed[0],changed[1]=changed[1],changed[0];cases.append(changed)
        changed=copy.deepcopy(rows);changed[0]["physical_envelope_pin"]["sha256"]="e"*64;cases.append(changed)
        changed=copy.deepcopy(rows);changed[0]["semantic_original_pin"]["path"]=changed[0]["semantic_original_pin"]["path"].replace("case112","case165");cases.append(changed)
        with patch.object(MODULE,"EXPECTED_TABLE",digest):
            for value in cases:
                with self.subTest(value=len(value)),self.assertRaises(ValueError):MODULE.ordinary(value,SAMPLE)

    def test_proposed_pin_is_explicit_new_path_not_a_published_or_overwritten_file(self):
        before=self.rows()[0];copy_before=copy.deepcopy(before);pin=MODULE.proposed_pin(before,b"new")
        self.assertTrue(pin["path"].endswith(".xz8m.envelope.v1.json"));self.assertEqual(pin["bytes"],3)
        self.assertNotEqual(pin["path"],before["physical_envelope_pin"]["path"]);self.assertEqual(before,copy_before)
        with self.assertRaises(ValueError):MODULE.proposed_pin(before,b"")
