"""Preserve271 pre-Cargo failure; scan production, not the intentional SQL-injection negative test."""
import run_stored_job_lifecycle_components as origin
OUTPUT='implementation/p09/evidence/p09-361-stored-job-lifecycle-checker-recovery272.v1.json'
DRIVER='tools/p09/run_stored_job_lifecycle_checker_recovery.py'
FAILED=origin.OUTPUT
SCRATCH='target/p09-stored-job-lifecycle-scratch-272'

def inverse(q,old):
    text=q.text(origin.ROOT)
    for marker in('pub mod lifecycle;\n','        lifecycle::admit_controls(&mut client)?;\n'):
        origin.c.require(text.count(marker)==1,'EXACT_TYPED_LIFECYCLE_MODULE_AND_EXTRA_CONTROL_ADMISSION');text=text.replace(marker,'')
    origin.audit.inverse(text,old[origin.ROOT],'ALL_EXISTING_SQL23_SCHEMA_ADMISSION_SOURCE_CAS_REGISTRATION_READ_AND_LEASE_BINDING_UNCHANGED')
    for path in(origin.LIFE,origin.SQL):
        text=q.text(path).split('#[cfg(test)]',1)[0]
        for forbidden in('std::process','CREATE ROLE','ALTER ROLE','GRANT EXECUTE','DROP SCHEMA','std::thread','loop {','no_effect','claim_idempotent_job_v2('):
            origin.c.require(forbidden not in text,'PRODUCTION_NO_NATIVE_GRANT_INSTALL_AUTO_RETRY_OR_NO_EFFECT_AUTHORITY')
    text=q.text(origin.SQL)
    origin.c.require('query("x); DROP SCHEMA hwpx_agent").is_err()'in text,'SQL_INJECTION_NEGATIVE_TEST_RETAINED_NOT_EXECUTABLE_SQL')
    for marker in('self.inner.scoped','self.authorize_context','tx.query_one','r.expect','admit_controls','control_security','MIGRATIONS[6]','returned_commit_authorization_id'):
        origin.c.require(marker in text,'SCOPED_SQL_TRANSACTIONS_EXACT_TYPED_RESPONSES_AND_FROZEN_CONTROL_ADMISSION')
    failed=origin.compact.unpack(q.json(FAILED))
    origin.c.require(q.snapshots[FAILED]['sha256']=='08e68eadca18e6df3aa0019dfabbfa81511062841f7581fe109ee94ab9509428'
        and failed['cleanup']and failed['steps']==[]and failed['error_code']=='NO_NATIVE_GRANT_INSTALL_AUTO_RETRY_OR_NO_EFFECT_AUTHORITY','ORIGINAL271_CHECKER_FAILURE_ZERO_CARGO_RETAINED')
    for pin in failed['source_pins']:
        if pin['path']in origin.NEW|{origin.ROOT}:
            q.pin(pin['path']);origin.c.require(q.snapshots[pin['path']]==pin,'PRODUCT_AND_NEGATIVE_TEST_SOURCES_UNCHANGED_SINCE271')

if __name__=='__main__':
    origin.OUTPUT=OUTPUT;origin.SCRATCH=SCRATCH;origin.NEW|={DRIVER,FAILED};origin.inverse=inverse
    raise SystemExit(origin.main())
