import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_envelope_source_manifest_v1 as m

class Tests(unittest.TestCase):
    def test_manifest_has_explicit_version_and_only_new_source_path(self):
        self.assertEqual(m.SCHEMA,"hwpx-agent.p09-envelope-full-source-manifest/v1")
        self.assertIn("case158-envelope-full-source-manifest019",m.PATH)
    def test_loader_original_guard_exception_identity_precedes_any_admission(self):
        error=ValueError("ORIGINAL_GUARD_STOP")
        class Authority:
            @staticmethod
            def read_exact(q,pin):raise error
        with self.assertRaises(ValueError) as caught:m.load(None,{},Authority)
        self.assertIs(caught.exception,error)
    def test_closed_manifest_rejects_missing_fields_before_other_reads(self):
        class Authority:
            @staticmethod
            def read_exact(q,pin):return {"schema_version":m.SCHEMA}
            @staticmethod
            def require(ok,code):
                if not ok:raise ValueError(code)
        with self.assertRaisesRegex(ValueError,"CLOSED_ENVELOPE_MANIFEST"):m.load(None,{},Authority)

if __name__=="__main__":unittest.main()
