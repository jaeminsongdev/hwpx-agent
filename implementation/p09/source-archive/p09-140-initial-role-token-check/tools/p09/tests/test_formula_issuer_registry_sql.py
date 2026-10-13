"""P140 disposable engine harness contracts, not actual SQL evidence by themselves."""
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
DRIVER = 'tools/p09/run_formula_issuer_registry_sql_checks.py'
FIXTURE = 'tools/p09/fixtures/formula_issuer_registry.sql'


class Contracts(unittest.TestCase):
    def setUp(self):
        self.code = (ROOT / DRIVER).read_text(encoding='utf-8')
        self.sql = (ROOT / FIXTURE).read_text(encoding='utf-8')

    def test_exact_37_ordered_assertions_with_fail_closed_helpers(self):
        names = re.findall(r"SELECT pg_temp\.(?:ok|denied)\('([a-z0-9_]+)'", self.sql)
        self.assertEqual(len(names),37)
        self.assertEqual(len(set(names)),37)
        for marker in ['condition IS DISTINCT FROM true','SQLSTATE<>expected_state','SQLERRM<>expected_message','P140_UNEXPECTED_ACCEPTANCE','SECURITY INVOKER','SET CONSTRAINTS ALL IMMEDIATE;\nCOMMIT;']:
            self.assertIn(marker,self.sql)
        self.assertIn('found == expected',self.code)
        self.assertIn('provisional_check_markers_before_rollback',self.code)

    def test_permission_profiles_do_not_lift_production_authority(self):
        for role in ['p140_root','p140_approval','p140_read','p140_policy','p140_rls_probe']:
            self.assertIn(role+' NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS',self.sql)
        for marker in ['root_profile_no_read','root_profile_no_approval','approval_profile_no_root','internal_helper_execute_denied','direct_table_read_denied','direct_table_write_denied','reader_cannot_write_approval','editor_cannot_install_root']:
            self.assertIn(marker,self.sql)
        self.assertIn('GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO p140_rls_probe;',self.sql)
        self.assertNotRegex(self.sql,r'GRANT ALL|BYPASSRLS;|SECURITY DEFINER')

    def test_actual_rls_scope_artifact_and_revocation_conditions(self):
        for marker in ['forced_rls_four_tables','nine_bounded_security_definers','rls_foreign_tenant_zero','rls_own_tenant_visible','foreign_tenant_named_read','nonmember_root_read','fresh_approval_acl_revocation','root_wrong_digest','approval_artifact_alias','revoked_root_no_fallback','old_approval_after_root_replacement','admin_revoke_after_root_revocation','failed_subtransactions_left_no_extra_rows']:
            self.assertIn(marker,self.sql)

    def test_networkless_owned_cleanup_and_unknown_outcome_recovery(self):
        for marker in ['"--network", "none"','"--read-only"','"--pull", "never"','not host["PortBindings"]','not item["Mounts"]','item["Id"] == created_id','get(LABEL) == run_id','creation_requested and created_id is None','"no such (object|container)"','re.IGNORECASE','["rm", "--force", created_id]']:
            self.assertIn(marker,self.code)
        self.assertNotRegex(self.code,r'--publish|--volume|--mount|docker.*pull|rmtree|unlink\(|remove\(')

    def test_source_image_and_final_server_readiness(self):
        for marker in ['range(1, 23)','sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568','"pg_isready", "-h", "127.0.0.1"','schema_versions_inexact','[pin(p) for p in sources] == freeze','P09_AUTHORIZED_FULL_IR_METADATA_PASS assertions=25']:
            self.assertIn(marker,self.code)
        self.assertIn('SQL metadata fixture. NOT real AEAD/signature/custody/product evidence.',self.sql)

    def test_bounded_resources_and_owned_child_handles(self):
        for marker in ['SetProcessAffinityMask(self.handle, 1)','SetPriorityClass(self.handle, 0x4000)','self.done.wait(2)','row["available_ram_mib"] < 4096','self.hot >= 3','time.monotonic()-start < 240','"--memory", "512m"','"--memory-swap", "512m"','"--cpus", "1"','"--pids-limit", "64"','process.kill()','process.communicate()']:
            self.assertIn(marker,self.code)
        self.assertNotRegex(self.code,r'taskkill|Stop-Process|HwpObject|cargo|rustc')

    def test_genuine_two_session_lock_wait_cas_and_live_readback(self):
        for marker in ["wait_event='PgSleep'","wait_event_type='Lock'",'first.returncode == 0','second.returncode != 0','FORMULA_ISSUER_GENERATION_CHANGED','"loser_rows":0','live == \'t\'','statement_timeout=\'8s\'','lock_timeout=\'6s\'','"production_retry_added":False']:
            self.assertIn(marker,self.code)
        self.assertIn('contended_scope_seed_failed',self.code)
        self.assertIn('contending_transaction_lock_wait_not_observed',self.code)

    def test_no_secret_or_log_dump_or_broad_acceptance(self):
        for marker in ['POSTGRES_PASSWORD=secrets.token_hex(32)','"operational_database_changed": False','"rust_adapters_executed": False','"real_AEAD_or_signatures_executed": False','"P09_gate": "OPEN"','"product_complete": False']:
            self.assertIn(marker,self.code)
        self.assertNotRegex(self.code,r'print\([^\n]*(?:stderr|stdout|password)|logging\.')


if __name__ == '__main__':
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(Contracts).run(result)
    print(json.dumps({'state':'PASS_HARNESS_SOURCE_ONLY_NOT_ENGINE_OR_GATE' if result.wasSuccessful() else 'FAIL_CLOSED',
        'tests':result.testsRun,'failures':[t._testMethodName for t,_ in result.failures],
        'errors':[t._testMethodName for t,_ in result.errors],'P09_gate':'OPEN'}))
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
