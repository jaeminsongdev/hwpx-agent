import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_envelope_source_manifest_v2 as m

class Tests(unittest.TestCase):
    def test_distinct_explicit_schema_preserves_v1_manifest_path(self):
        self.assertNotEqual(m.PATH,m.original.PATH);self.assertNotEqual(m.SCHEMA,m.original.SCHEMA)
    def test_original_guard_exception_identity_first(self):
        error=ValueError("ORIGINAL_STOP")
        class A:
            @staticmethod
            def read_exact(q,p):raise error
        with self.assertRaises(ValueError) as caught:m.load(None,{},A)
        self.assertIs(caught.exception,error)
    def test_wrong_shape_fails_before_delegating_prior_admission(self):
        class A:
            @staticmethod
            def read_exact(q,p):return {"index":158}
            @staticmethod
            def require(ok,code):
                if not ok:raise ValueError(code)
        with patch.object(m.original,"load",side_effect=AssertionError("NO_PRIOR_READ")):
            with self.assertRaisesRegex(ValueError,"CLOSED_ENVELOPE_MANIFEST_V2"):m.load(None,{},A)

if __name__=="__main__":unittest.main()
