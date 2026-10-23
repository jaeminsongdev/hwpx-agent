"""Closed aggregate models only: no cluster, product replay, compiler, native app or shared lock."""
import hashlib,json,unittest
from unittest.mock import patch
from pathlib import Path
from native_postgres_storage import campaign,completed_snapshot

def completed(count=8):
    return dict(artifacts=count,available=count,jobs=2,succeeded_jobs=2,successful_records=2,
        attempts=2,authorizations=0,intents=1,revisions=2,seals=2,head=2)

class Snapshot(unittest.TestCase):
    def test_exact_completed_snapshot_is_copied(self):
        row=dict(snapshots=[]);value=completed();completed_snapshot(row,value,8)
        value['head']=99;self.assertEqual(row['snapshots'],[completed()])

    def test_every_changed_count_still_fails_but_is_preserved(self):
        for key in completed():
            with self.subTest(key=key):
                row=dict(snapshots=[]);value=completed();value[key]+=1
                with self.assertRaises(ValueError):completed_snapshot(row,value,8)
                self.assertEqual(row['snapshots'],[value])

    def test_nine_cannot_accept_eight_and_eight_cannot_accept_nine(self):
        for actual,expected in((8,9),(9,8)):
            row=dict(snapshots=[]);value=completed(actual)
            with self.assertRaises(ValueError):completed_snapshot(row,value,expected)
            self.assertEqual(row['snapshots'],[value])

    def test_invalid_shapes_and_counts_cannot_be_recorded(self):
        for value in([],dict(completed(),head=True),dict(completed(),head=-1),
            dict(completed(),head=10_000_001),dict(completed(),extra=1),
            {k:v for k,v in completed().items()if k!='head'}):
            row=dict(snapshots=[])
            with self.assertRaises(ValueError):completed_snapshot(row,value,8)
            self.assertEqual(row['snapshots'],[])
        for count in(True,8.0,0,10):
            row=dict(snapshots=[])
            with self.assertRaises(ValueError):completed_snapshot(row,completed(),count)
            self.assertEqual(row['snapshots'],[])

    def test_old_six_seven_nine_exact_expectations_preserved(self):
        for count in(6,7,9):
            row=dict(snapshots=[]);completed_snapshot(row,completed(count),count)
            self.assertEqual(row['snapshots'],[completed(count)])

    def test_eight_count_campaign_admission_is_only_completed_schema26_ephemeral(self):
        # Stop before paths, DB creation or subprocesses even for the admitted count.
        for schema,mode,outcome in((23,'parent_ephemeral','completed'),
            (26,'windows_owned','completed'),(26,'parent_ephemeral','https_policy_denied')):
            with self.subTest(schema=schema,mode=mode,outcome=outcome):
                with self.assertRaises(ValueError):
                    campaign({},schema_version=schema,artifact_key_mode=mode,
                        expected_artifacts=8,execution_outcome=outcome)
        with patch('native_postgres_storage.os.name','posix'):
            with self.assertRaisesRegex(ValueError,'^PG_STORAGE_WINDOWS_REPO_SCOPE$'):
                campaign({},schema_version=26,expected_artifacts=8)

    def test_failed564_stdout_digest_proves_eight_not_nine_without_database_replay(self):
        root=Path(__file__).resolve().parents[2]
        failure=root/'implementation/p09/evidence/p09-361-https-common-sql564.v1.json'
        self.assertEqual(hashlib.sha256(failure.read_bytes()).hexdigest(),
            'bbb66ab756929c1b3f923f60acb88aa5ac395ff94bc9176e9a11692fb3439436')
        obs=json.loads((root/'target/p09-https-common-sql26-observation-564.json').read_bytes())
        self.assertEqual(obs['state'],'FAILED_HTTPS_COMMON_SQL26')
        self.assertEqual(obs['stage'],'completed_before_restart')
        command=[r for r in obs['commands']if r['stage']=='completed_before_restart']
        self.assertEqual(len(command),1);command=command[0]
        raw=(json.dumps(completed(),separators=(', ',' : '))+'\r\n').encode()
        self.assertEqual(command['exit_code'],0)
        self.assertEqual(command['stdout_bytes'],len(raw))
        self.assertEqual(command['stdout_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertNotEqual(command['stdout_sha256'],hashlib.sha256(
            (json.dumps(completed(9),separators=(', ',' : '))+'\r\n').encode()).hexdigest())

if __name__=='__main__':unittest.main()
