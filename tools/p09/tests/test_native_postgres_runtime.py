"""Small in-memory archive/path/version models; no network, binaries or database invocation."""
import io,os,stat,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import native_postgres_runtime as runtime

def member(path,size=1):
    info=zipfile.ZipInfo(path);info.file_size=size;info.compress_size=max(1,size);info.external_attr=(stat.S_IFREG|0o600)<<16;return info
def required():return [member(p)for p in sorted(runtime.REQUIRED)]

class NativePostgresRuntimeTests(unittest.TestCase):
    def test_exact_vendor_version_archive_and_own_asset_are_pinned(self):
        self.assertEqual(runtime.VERSION,'18.6');self.assertEqual(runtime.EXPECTED_BYTES,384620317)
        self.assertEqual(runtime.URL,'https://get.enterprisedb.com/postgresql/postgresql-18.6-5-windows-x64-binaries.zip')
        self.assertEqual(runtime.ASSET,'target/p09-native-postgres-18.6-5-278')
        self.assertTrue(runtime.VENDOR_ENTRY.startswith('https://sbp.enterprisedb.com/'))
    def test_only_bin_lib_share_are_extracted(self):
        rows=required()+[member('pgsql/doc/readme.txt'),member('pgsql/include/server.h'),member('pgsql/bin/extra.dll'),member('pgsql/lib/pgcrypto.dll')]
        selected,total=runtime.select_members(rows);paths={p for _,p in selected}
        self.assertEqual(paths,runtime.REQUIRED|{'pgsql/bin/extra.dll','pgsql/lib/pgcrypto.dll'});self.assertEqual(total,len(paths))
    def test_traversal_absolute_ads_backslash_and_control_paths_are_rejected(self):
        for name in('../outside','/pgsql/bin/x','C:/pgsql/bin/x','pgsql/../x','pgsql//bin/x','pgsql/bin/x:stream','pgsql\\bin\\x','pgsql/bin/a\nx','other/bin/x','pgsql/bin/x\0hidden'):
            with self.subTest(name=name),self.assertRaises(ValueError):runtime.member_path(member(name))
    def test_windows_reserved_names_and_trailing_dot_space_are_rejected(self):
        for name in('pgsql/bin/CON','pgsql/bin/nul.dll','pgsql/bin/COM1.txt','pgsql/bin/Lpt9','pgsql/bin/x.','pgsql/bin/x '):
            with self.subTest(name=name),self.assertRaises(ValueError):runtime.member_path(member(name))
    def test_symlink_fifo_and_encrypted_entries_are_rejected(self):
        for mode in(stat.S_IFLNK,stat.S_IFIFO,stat.S_IFSOCK):
            row=member('pgsql/bin/x');row.external_attr=(mode|0o600)<<16
            with self.assertRaises(ValueError):runtime.member_path(row)
        row=member('pgsql/bin/x');row.flag_bits=1
        with self.assertRaises(ValueError):runtime.member_path(row)
    def test_case_alias_duplicates_missing_required_and_file_parent_collisions_are_rejected(self):
        for rows in(required()+[member('pgsql/bin/POSTGRES.EXE')],required()[:-1],required()+[member('pgsql/bin'),member('pgsql/bin/child/x')]):
            with self.assertRaises(ValueError):runtime.select_members(rows)
    def test_entry_count_byte_and_compression_limits_are_enforced_before_extraction(self):
        with patch.object(runtime,'MAX_ENTRIES',1),self.assertRaises(ValueError):runtime.select_members(required())
        row=member('pgsql/bin/x',runtime.MAX_FILE_BYTES+1)
        with self.assertRaises(ValueError):runtime.member_path(row)
        row=member('pgsql/bin/x',201);row.compress_size=1
        with self.assertRaises(ValueError):runtime.member_path(row)
        with patch.object(runtime,'MAX_SELECTED_BYTES',1),self.assertRaises(ValueError):runtime.select_members(required())
    def test_archive_scope_is_completely_validated_before_any_file_is_written(self):
        payload=io.BytesIO()
        with zipfile.ZipFile(payload,'w')as z:
            for path in sorted(runtime.REQUIRED):z.writestr(path,b'fixture')
            z.writestr('../outside',b'bad')
        payload.seek(0)
        with tempfile.TemporaryDirectory()as temp,zipfile.ZipFile(payload)as z:
            root=Path(temp)/'owned';root.mkdir()
            with self.assertRaises(ValueError):runtime.extract(z,root)
            self.assertEqual(list(root.iterdir()),[])
    def test_exact_extraction_manifest_and_fresh_hash_detect_tampering(self):
        payload=io.BytesIO()
        with zipfile.ZipFile(payload,'w')as z:
            for path in sorted(runtime.REQUIRED):z.writestr(path,b'fixture bytes')
            z.writestr('pgsql/doc/private.txt',b'not selected')
        payload.seek(0)
        with tempfile.TemporaryDirectory()as temp,zipfile.ZipFile(payload)as z:
            root=Path(temp)/'owned';root.mkdir();pins=runtime.extract(z,root)
            self.assertEqual({p['path']for p in pins},runtime.REQUIRED);self.assertFalse((root/'pgsql/doc').exists())
            for pin in pins:self.assertEqual(runtime.sha_file(root/pin['path']),pin['sha256'])
            first=pins[0];(root/first['path']).write_bytes(b'changed test fixture')
            self.assertNotEqual(runtime.sha_file(root/first['path']),first['sha256'])
    def test_existing_target_and_runtime_escape_are_never_overwritten(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp)/'owned';root.mkdir();(root/'existing').write_bytes(b'keep')
            with self.assertRaises(ValueError):runtime.checked_destination(root,'existing')
            with self.assertRaises(ValueError):runtime.checked_destination(root,'../outside')
            self.assertEqual((root/'existing').read_bytes(),b'keep')
    def test_version_commands_are_closed_and_only_exact18_6_is_accepted(self):
        self.assertEqual(set(runtime.EXECUTABLES),{'postgres.exe','initdb.exe','psql.exe'})
        for name,label in runtime.EXECUTABLES.items():self.assertEqual(runtime.version_line(name,f'{label} (PostgreSQL) 18.6\r\n'),f'{label} (PostgreSQL) 18.6')
        for text in('postgres (PostgreSQL) 18.4','postgres (PostgreSQL) 18.6\nextra','server started'):
            with self.assertRaises(ValueError):runtime.version_line('postgres.exe',text)
        with self.assertRaises(ValueError):runtime.version_line('pg_ctl.exe','pg_ctl (PostgreSQL) 18.6')
    def test_child_operational_pg_settings_are_removed_without_modifying_parent_environment(self):
        with patch.dict(os.environ,{'SystemRoot':'C:\\Windows','PGHOST':'private-host','PGPASSWORD':'test-only-not-real','PGSERVICEFILE':'private-path','OTHER':'keep'},clear=True):
            before=dict(os.environ);env=runtime.clean_environment(Path('D:/owned/bin'));self.assertEqual(dict(os.environ),before)
            self.assertNotIn('PGHOST',env);self.assertNotIn('PGPASSWORD',env);self.assertNotIn('PGSERVICEFILE',env);self.assertEqual(env['PG_COLOR'],'never');self.assertEqual(env['OTHER'],'keep')

if __name__=='__main__':
    import json
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(NativePostgresRuntimeTests)
    result=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    print(json.dumps(dict(state='PASS_NATIVE_PG_RUNTIME_MODELS12'if result.wasSuccessful()and result.testsRun==12 and not result.skipped else'FAILED_NATIVE_PG_RUNTIME_MODELS',
        tests_run=result.testsRun,failures=[t.id().split('.')[-1]for t,_ in result.failures+result.errors],actual_network_or_database=False)),flush=True)
    raise SystemExit(0 if result.wasSuccessful()and result.testsRun==12 and not result.skipped else 2)
