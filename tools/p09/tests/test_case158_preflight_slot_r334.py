import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_case158_preflight_slot_r334 as m


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if m.m.base.CONFIG is None:m.m.base.configure(158)
    def test_real_whole_preflight_code_inverse_and_both_admission_dependencies(self):
        source=m.m.prior.lean.source;pin=source.prior.prior.prior.METADATA_PIN
        raw=(m.m.c.ROOT/pin["path"]).read_bytes()
        self.assertEqual(len(raw),pin["bytes"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(),pin["sha256"])
        leaf=source.prior.leaf_bytes()
        old=m.m.preflight_projection(raw,leaf);new,proof=m.projection(raw,leaf,30)
        restored=new.__code__.replace(co_consts=tuple(m.slots.OLD if x==m.slots.suffix(30) else x for x in new.__code__.co_consts))
        self.assertEqual(restored,old.__code__)
        self.assertIs(new.__globals__["own_inputs"],m.admission)
        self.assertIs(new.__globals__["connection_data"],m.admission)
        self.assertFalse(proof["GO_authorized"])
    def test_existing_slot_rejected_before_full_driver_is_called(self):
        error=ValueError("EXISTING_SLOT")
        with patch.object(m.slots,"ensure_fresh",side_effect=error),patch.object(m.m.prior.LINK,"clone") as driver:
            with self.assertRaises(ValueError) as caught:m.run(30)
        self.assertIs(caught.exception,error);driver.assert_not_called()
    def test_invalid_slot_qualification_rejected_before_original_admission(self):
        class Q:
            def json(self,p):return dict(state="NOT_RUN")
        with patch.object(m.m,"own_inputs") as original:
            with self.assertRaises(ValueError):m.admission(Q())
        original.assert_not_called()
    def test_default_V22_qualified_source_remains_exact(self):
        raw=(m.m.c.ROOT/m.m.SELF).read_bytes()
        self.assertEqual(len(raw),21928)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),"1054006159af5da65911eb6129d71d4ed354ffe106f84efe6c7c6318ad7ffc89")


if __name__=="__main__":unittest.main()
