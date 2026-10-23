"""Selected migration file scope models only. No SQL, operational DB or Native."""
import hashlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import native_postgres_cluster as cluster
from test_native_postgres_cluster import NativePostgresClusterTests
class LookupMigrationTests(unittest.TestCase):
    def test_legacy23_selection_and_explicit24_keep_identical_original_sources(self):
        old=cluster.migration_rows();new=cluster.migration_rows(24)
        self.assertEqual(len(old),23);self.assertEqual(len(new),24);self.assertEqual(old,new[:23])
        self.assertEqual(new[-1]['path'],'migrations/postgres/0024_p09_stored_request_lookup.up.sql')
        self.assertEqual(hashlib.sha256(new[-1]['text'].encode()).hexdigest(),new[-1]['sha256'])
    def test_only_explicit_integer23_or24_are_accepted(self):
        for version in (True,False,'24',22,25,0):
            with self.assertRaises(ValueError):cluster.migration_rows(version)
    def test_missing_middle_duplicate_or_nonversioned_file_cannot_hide(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);folder=root/'migrations/postgres';folder.mkdir(parents=True)
            for n in range(1,25):(folder/f'{n:04}_model.up.sql').write_text(f'-- model {n}\n',encoding='utf-8')
            with patch.object(cluster,'ROOT',root):
                self.assertEqual(len(cluster.migration_rows()),23);self.assertEqual(len(cluster.migration_rows(24)),24)
                (folder/'0011_model.up.sql').rename(folder/'0025_model.up.sql')
                with self.assertRaises(ValueError):cluster.migration_rows(24)
                (folder/'0025_model.up.sql').rename(folder/'0011_model.up.sql')
                (folder/'0011_duplicate.up.sql').write_text('-- duplicate\n',encoding='utf-8')
                with self.assertRaises(ValueError):cluster.migration_rows()
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(LookupMigrationTests)
    suite.addTest(NativePostgresClusterTests('test_all23_exact_migration_bytes_are_retained_and_not_rewritten'))
    result=unittest.TextTestRunner(stream=io.StringIO()).run(suite);ok=result.wasSuccessful()and result.testsRun==4 and not result.skipped
    print(json.dumps(dict(state='PASS_LOOKUP_MIGRATION_MODELS3_LEGACY1'if ok else'FAILED_LOOKUP_MIGRATION_MODELS',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),actual_SQL_or_Native=False)),flush=True)
    raise SystemExit(0 if ok else 2)
