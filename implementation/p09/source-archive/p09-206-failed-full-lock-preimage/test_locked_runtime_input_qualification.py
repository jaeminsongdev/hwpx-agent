"""새 입력 union은 기존 scope를 그대로 유지한다."""
import copy
import unittest
import qualify_locked_runtime_inputs as q


class QualificationTests(unittest.TestCase):
    def setUp(self):self.pin=dict(path='tools/a.py',bytes=1,sha256='a'*64)
    def test_identical_overlap_only_deduplicated_all_original_inputs_retained(self):
        extra=dict(path='fixtures/a.hwpx',bytes=2,sha256='b'*64)
        result=q.combine({'tools/a.py':self.pin},{'tools/a.py':dict(self.pin)},{'fixtures/a.hwpx':extra},{})
        self.assertEqual(result,{'tools/a.py':self.pin,'fixtures/a.hwpx':extra})
    def test_conflicting_duplicate_pin_rejected(self):
        with self.assertRaises(ValueError):q.combine({'tools/a.py':self.pin},{'tools/a.py':dict(self.pin,sha256='b'*64)},{},{})
    def test_additional_path_escape_or_invalid_pin_rejected(self):
        with self.assertRaises(ValueError):q.combine({'tools/a.py':self.pin},{},{},{'../a.py':dict(self.pin,path='../a.py')})
    def test_source_objects_not_modified_or_aliased(self):
        before=copy.deepcopy(self.pin);result=q.combine({'tools/a.py':self.pin},{},{},{})
        result['tools/a.py']['bytes']=2;self.assertEqual(self.pin,before)


if __name__=='__main__':unittest.main()
