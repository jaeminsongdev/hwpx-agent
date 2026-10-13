import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import same_reader_source_admission_once_v1 as m


class Reader:
    def __init__(self):
        self.calls=0;self.final_fresh_hashes=0;self.snapshots={"a":{"path":"a","bytes":1,"sha256":"0"*64}}
    def checkpoint(self):self.calls+=1


class Tests(unittest.TestCase):
    def test_same_reader_admits_once_but_checks_original_guard_each_call(self):
        reads=[]
        def original(q):reads.append(q);return {"value":[1]}
        fn,stats=m.connect(original);q=Reader();fn(q);fn(q)
        self.assertEqual(reads,[q]);self.assertEqual(q.calls,2)
        self.assertEqual(stats,dict(actual_admissions=1,duplicate_admissions_avoided=1))
    def test_second_reader_gets_a_separate_complete_admission(self):
        reads=[]
        fn,stats=m.connect(lambda q:(reads.append(q) or {"ok":True}))
        a,b=Reader(),Reader();fn(a);fn(b)
        self.assertEqual(reads,[a,b]);self.assertEqual(stats["actual_admissions"],2)
    def test_caller_cannot_mutate_retained_declaration(self):
        fn,_=m.connect(lambda q:{"list":[1]});q=Reader();first=fn(q);first["list"].append(2)
        second=fn(q);self.assertEqual(second,{"list":[1]});second["list"].append(3)
        self.assertEqual(fn(q),{"list":[1]})
    def test_changed_or_missing_original_pin_rejected(self):
        for missing in (True,False):
            fn,_=m.connect(lambda q:{"ok":True});q=Reader();fn(q)
            if missing:q.snapshots.clear()
            else:q.snapshots["a"]["bytes"]=2
            with self.assertRaisesRegex(ValueError,"LEDGER_UNCHANGED"):fn(q)
    def test_finish_or_final_fresh_phase_cannot_reuse_admission(self):
        fn,_=m.connect(lambda q:{"ok":True});q=Reader();fn(q);q.final_fresh_hashes=1
        with self.assertRaisesRegex(ValueError,"FINAL_FRESH_ONLY"):fn(q)
    def test_original_resource_stop_identity_precedes_cached_result(self):
        fn,_=m.connect(lambda q:{"ok":True});q=Reader();fn(q);error=ValueError("ORIGINAL_CPU_RAM_STOP")
        def stop():raise error
        q.checkpoint=stop
        with self.assertRaises(ValueError) as caught:fn(q)
        self.assertIs(caught.exception,error)
    def test_owner_change_or_failed_admission_never_creates_reuse(self):
        owner=[1];calls=[];error=ValueError("ORIGINAL_ADMISSION_FAILED")
        def original(q):calls.append(q);raise error
        fn,stats=m.connect(original,identity=lambda:owner[0]);q=Reader()
        with self.assertRaises(ValueError):fn(q)
        self.assertEqual(stats["actual_admissions"],0);owner[0]=2
        with self.assertRaisesRegex(ValueError,"SAME_OWNER"):fn(q)
        self.assertEqual(calls,[q])


if __name__=="__main__":unittest.main()
