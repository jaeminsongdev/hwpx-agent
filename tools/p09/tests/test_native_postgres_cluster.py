"""Cluster command/auth/ownership models only; the separate worker owns real DB execution."""
import io,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import native_postgres_cluster as cluster

class NativePostgresClusterTests(unittest.TestCase):
    def setUp(self):
        self.binary=cluster.ROOT/cluster.runtime.ASSET/'pgsql/bin';self.data=cluster.ROOT/cluster.CLUSTER/'data'
    def test_initdb_is_new_reject_auth_utf8_without_password_files(self):
        a=cluster.init_args(self.binary,self.data);self.assertEqual(Path(a[0]).name,'initdb.exe')
        for value in('--auth=reject','--encoding=UTF8','--locale=C','--no-clean'):self.assertIn(value,a)
        self.assertFalse(any('pwfile'in x or 'password'in x for x in a))
    def test_bootstrap_single_user_has_no_echo_network_or_password_argument(self):
        a=cluster.bootstrap_args(self.binary,self.data);self.assertEqual(a[1],'--single');self.assertEqual(a[-1],'postgres')
        self.assertNotIn('-E',a);self.assertNotIn('-h',a);self.assertIn('log_min_error_statement=panic',a)
    def test_foreground_server_is_loopback_only_and_has_no_service_or_detach_flag(self):
        a=cluster.start_args(self.binary,self.data,55432,cluster.ROOT/cluster.HBA)
        self.assertEqual(Path(a[0]).name,'postgres.exe');self.assertEqual(a[a.index('-h')+1],'127.0.0.1')
        self.assertEqual(a[a.index('-p')+1],'55432');self.assertNotIn('start',a);self.assertNotIn('register',a)
    def test_unsafe_ports_and_foreign_data_directories_are_rejected(self):
        for port in(0,1,1023,65536,True):
            with self.assertRaises(ValueError):cluster.start_args(self.binary,self.data,port,cluster.ROOT/cluster.HBA)
        for data in(cluster.ROOT/'data',cluster.ROOT/'target/foreign/data'):
            with self.assertRaises(ValueError):cluster.init_args(self.binary,data)
            with self.assertRaises(ValueError):cluster.bootstrap_args(self.binary,data)
    def test_memory_background_and_durability_settings_are_explicit(self):
        s=cluster.SETTINGS
        for key in('fsync','synchronous_commit','full_page_writes'):self.assertEqual(s[key],'on')
        self.assertEqual(s['shared_buffers'],'16MB');self.assertEqual(s['work_mem'],'1MB');self.assertEqual(s['max_connections'],'12')
        self.assertEqual(s['max_worker_processes'],'0');self.assertEqual(s['max_parallel_workers'],'0');self.assertEqual(s['autovacuum'],'off')
    def test_psql_never_prompts_and_ignores_user_rc_with_closed_loopback_target(self):
        a=cluster.psql_args(self.binary,55432);self.assertIn('-X',a);self.assertIn('--no-password',a);self.assertIn('ON_ERROR_STOP=1',a);self.assertIn('VERBOSITY=sqlstate',a)
        self.assertEqual(a[a.index('-h')+1],'127.0.0.1');self.assertEqual(a[a.index('-U')+1],cluster.USER);self.assertEqual(a[-1],'postgres')
    def test_hba_has_only_scram_loopback_and_reject_rules(self):
        rows=[line.split()for line in (cluster.ROOT/cluster.HBA).read_text(encoding='utf-8').splitlines()if line and not line.startswith('#')]
        self.assertEqual(rows,[['host','all','all','127.0.0.1/32','scram-sha-256'],['host','all','all','0.0.0.0/0','reject'],['host','all','all','::0/0','reject']])
    def test_attestation_rejects_other_data_listener_user_version_or_auth(self):
        good=dict(data_directory=str(self.data),port=55432,listen='127.0.0.1',version=180006,user=cluster.USER,fsync='on',sync_commit='on',hba_clean=True,scram_local=True,no_trust=True)
        with patch.object(cluster,'invoke',return_value=(0,json.dumps(good))):cluster.attest_cluster(self.binary,self.data,55432,{}, {},'model')
        for key,value in(('data_directory',str(cluster.ROOT)),('listen','*'),('port',5432),('user','other'),('version',180004),('fsync','off'),('sync_commit','off'),('hba_clean',False),('scram_local',False),('no_trust',False)):
            bad=dict(good,**{key:value})
            with patch.object(cluster,'invoke',return_value=(0,json.dumps(bad))),self.assertRaises(ValueError):cluster.attest_cluster(self.binary,self.data,55432,{}, {},'model')
    def test_stop_requires_matching_pid_of_exact_live_handle_before_pg_ctl(self):
        with tempfile.TemporaryDirectory()as temp:
            data=Path(temp);(data/'postmaster.pid').write_text('999\n',encoding='utf-8');process=NS(poll=lambda:None,pid=42)
            with patch.object(cluster,'invoke')as invoke,self.assertRaises(ValueError):cluster.stop(process,None,self.binary,data,{}, {})
            invoke.assert_not_called()
            process=NS(poll=lambda:0,pid=999)
            with patch.object(cluster,'invoke')as invoke,self.assertRaises(ValueError):cluster.stop(process,None,self.binary,data,{}, {})
            invoke.assert_not_called()
    def test_all23_exact_migration_bytes_are_retained_and_not_rewritten(self):
        rows=cluster.migration_rows();self.assertEqual(len(rows),23)
        for n,row in enumerate(rows,1):
            self.assertTrue(Path(row['path']).name.startswith(f'{n:04}_'));self.assertEqual(cluster.runtime.sha_file(cluster.ROOT/row['path']),row['sha256']);self.assertEqual(len(row['text'].encode('utf-8')),row['bytes'])

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(NativePostgresClusterTests);result=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    ok=result.wasSuccessful()and result.testsRun==10 and not result.skipped
    print(json.dumps(dict(state='PASS_NATIVE_PG_CLUSTER_MODELS10'if ok else'FAILED_NATIVE_PG_CLUSTER_MODELS',tests_run=result.testsRun,
        failures=[t.id().split('.')[-1]for t,_ in result.failures+result.errors],actual_database=False)),flush=True)
    raise SystemExit(0 if ok else 2)
