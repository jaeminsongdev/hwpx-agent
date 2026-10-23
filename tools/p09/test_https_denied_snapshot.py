"""Pure bounded aggregate tests; no cluster, SQL, Cargo, key generation or native app execution."""
import unittest
from native_postgres_storage import denied_snapshot
def original():
    return dict(artifacts=7,available=7,jobs=2,succeeded_jobs=1,successful_records=1,attempts=2,authorizations=1,intents=1,revisions=1,seals=1,head=1)
class Snapshot(unittest.TestCase):
    def test_exact_denial_has_retained_lease_and_unchanged_head(self):
        row=dict(snapshots=[]);value=original();denied_snapshot(row,value,7)
        self.assertEqual(row['snapshots'],[original()]);value['head']=99;self.assertEqual(row['snapshots'],[original()])
    def test_each_wrong_count_is_retained_but_rejected(self):
        for key in original():
            with self.subTest(key=key):
                row=dict(snapshots=[]);value=original();value[key]+=1
                with self.assertRaises(ValueError):denied_snapshot(row,value,7)
                self.assertEqual(row['snapshots'],[value])
    def test_previous_zero_authorization_expectation_is_rejected_and_retained(self):
        row=dict(snapshots=[]);value=original();value['authorizations']=0
        with self.assertRaises(ValueError):denied_snapshot(row,value,7)
        self.assertEqual(row['snapshots'],[value])
    def test_completed_product_state_cannot_be_accepted_as_denied(self):
        row=dict(snapshots=[]);value=original();value.update(succeeded_jobs=2,successful_records=2,authorizations=0,revisions=2,seals=2,head=2)
        with self.assertRaises(ValueError):denied_snapshot(row,value,7)
        self.assertEqual(row['snapshots'],[value])
    def test_untrusted_shape_is_not_recorded(self):
        values=[[],{**original(),'head':True},{**original(),'head':-1},{**original(),'head':10_000_001},
            {**original(),'extra':1},{k:v for k,v in original().items()if k!='head'}]
        for value in values:
            with self.subTest(shape=type(value).__name__):
                row=dict(snapshots=[])
                with self.assertRaises(ValueError):denied_snapshot(row,value,7)
                self.assertEqual(row['snapshots'],[])
if __name__=='__main__':unittest.main()
