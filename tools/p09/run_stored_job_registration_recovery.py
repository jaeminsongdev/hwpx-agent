"""One missing private-ancestor import only; retain265 compile failure and all migration pins."""
import json
import run_stored_job_registration_components as base
OUTPUT='implementation/p09/evidence/p09-361-stored-job-registration-recovery266.v1.json'
DRIVER='tools/p09/run_stored_job_registration_recovery.py'
FAILED=base.OUTPUT
OriginalReader=base.a.AcceptanceReader


class RecoveryReader(OriginalReader):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        failed=base.compact.unpack(self.json(FAILED))
        base.c.require(self.snapshots[FAILED]['sha256']=='9f9ed9c66b47bbc991168177b8a15488965e5a353b887c6758ea4ad34f2b5b79'
            and failed['cleanup']and len(failed['steps'])==1 and not failed['steps'][0]['tests'],'EXACT265_COMPILATION_FAILURE_NO_TESTS')
        observed=failed['steps'][0]['bounded_output_observation']
        base.c.require(failed['steps'][0]['exit_code']==101 and observed['rust_error_codes']==['E0425']
            and observed['short_error_locations']==[[base.ADMISSION,'54','18']],'EXACT_MISSING_READ_TABLES_ANCESTOR_IMPORT_ONLY')
        old={p['path']:p for p in failed['source_pins']}
        for name in sorted(base.NEW|base.CHANGED):
            self.pin(name)
            if name==base.ADMISSION:
                text=self.text(name);marker='use crate::postgres::READ_TABLES;\n';base.c.require(text.count(marker)==1,'ONE_PRIVATE_ANCESTOR_CONSTANT_IMPORT')
                base.audit.inverse(text.replace(marker,''),old[name],'ALL_ADMISSION_MODELS_QUERIES_AND_SECURITY_RULES_UNCHANGED_EXCEPT_IMPORT')
            elif name!=DRIVER:base.c.require(self.snapshots[name]==old[name],'ALL265_PRODUCT_CONNECTOR_CALLBACK_AND_TEST_BODIES_UNCHANGED')
        for pin in failed['newly_scoped_existing_compilation_migrations']:
            self.pin(pin['path']);base.c.require(self.snapshots[pin['path']]==pin,'ALL_NEWLY_SCOPED_COMPILATION_MIGRATIONS_PRESERVED_FROM265')
        print(json.dumps(dict(state='REGISTRATION_IMPORT_REPAIR_DELTA_PASS',product_or_test_body_change=False,actual_DB=False)),flush=True)


if __name__=='__main__':
    base.OUTPUT=OUTPUT;base.DRIVER=DRIVER;base.NEW=base.NEW|{DRIVER};base.a.AcceptanceReader=RecoveryReader
    try:raise SystemExit(base.main())
    finally:base.a.AcceptanceReader=OriginalReader
