"""Preserve272 E0425/zero tests; qualify the existing revision-id decoder, no product policy change."""
import run_stored_job_lifecycle_components as origin
import run_stored_job_lifecycle_checker_recovery as checker
OUTPUT='implementation/p09/evidence/p09-361-stored-job-lifecycle-compile-recovery273.v1.json'
DRIVER='tools/p09/run_stored_job_lifecycle_compile_recovery.py'
FAILED='implementation/p09/evidence/p09-361-stored-job-lifecycle-checker-recovery272.v1.json'
SCRATCH='target/p09-stored-job-lifecycle-scratch-273'

def inverse(q,old):
    text=q.text(origin.ROOT)
    for marker in('pub mod lifecycle;\n','        lifecycle::admit_controls(&mut client)?;\n'):
        origin.c.require(text.count(marker)==1,'EXACT_TYPED_LIFECYCLE_MODULE_AND_EXTRA_CONTROL_ADMISSION');text=text.replace(marker,'')
    origin.audit.inverse(text,old[origin.ROOT],'ALL_EXISTING_SQL23_SCHEMA_ADMISSION_SOURCE_CAS_REGISTRATION_READ_AND_LEASE_BINDING_UNCHANGED')
    for path in(origin.LIFE,origin.SQL):
        text=q.text(path).split('#[cfg(test)]\nmod tests{',1)[0]
        for forbidden in('std::process','CREATE ROLE','ALTER ROLE','GRANT EXECUTE','DROP SCHEMA','std::thread','loop {','no_effect','claim_idempotent_job_v2('):
            origin.c.require(forbidden not in text,'FULL_PRODUCTION_NO_NATIVE_GRANT_INSTALL_AUTO_RETRY_OR_NO_EFFECT_AUTHORITY')
    failed=origin.compact.unpack(q.json(FAILED))
    origin.c.require(q.snapshots[FAILED]['sha256']=='14fcecfacf017259e58d5ab8f24e5604f74d1112dee521b9c30dba93d03c827b'
        and failed['cleanup']and len(failed['steps'])==1 and failed['steps'][0]['tests']==[]
        and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0425'],'EXACT272_COMPILER_ERROR_ZERO_TESTS_RETAINED')
    previous={p['path']:p for p in failed['source_pins']}
    before='.map(revision_id).transpose()?,';after='.map(crate::postgres::revision_id).transpose()?,'
    text=q.text(origin.SQL);origin.c.require(text.count(after)==1,'ONE_QUALIFIED_EXISTING_DECODER')
    origin.audit.inverse(text.replace(after,before),previous[origin.SQL],'ALL_OTHER_SQL_ADAPTER_GUARDS_ARGUMENTS_RESPONSES_AND_NEGATIVE_TESTS_UNCHANGED')
    for path in(origin.LIFE,origin.TEST,origin.ROOT,origin.DRIVER,checker.DRIVER):
        q.pin(path);origin.c.require(q.snapshots[path]==previous[path],'ALL_OTHER_LIFECYCLE_CODE_TESTS_AND_CHECKERS_UNCHANGED_SINCE272')

if __name__=='__main__':
    origin.OUTPUT=OUTPUT;origin.SCRATCH=SCRATCH;origin.NEW|={DRIVER,FAILED,checker.DRIVER,checker.FAILED};origin.inverse=inverse
    raise SystemExit(origin.main())
