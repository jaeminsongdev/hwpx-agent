"""Preserve265/266 and source identity; fresh owned scratch with an early collision check."""
import json
import run_stored_job_registration_recovery as origin
base=origin.base
OUTPUT='implementation/p09/evidence/p09-361-stored-job-registration-fresh-temp267.v1.json'
DRIVER='tools/p09/run_stored_job_registration_fresh_temp.py'
FAILED=origin.OUTPUT
SCRATCH='target/p09-stored-job-registration-scratch-267'


class RecoveryReader(origin.OriginalReader):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        parent=base.c.ROOT/'target';scratch=base.c.ROOT/SCRATCH
        base.c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not scratch.exists()
            and scratch.resolve().is_relative_to(parent.resolve()),'EARLY_FRESH267_OWNED_TEMP_PARENT_ONLY')
        failed=base.compact.unpack(self.json(origin.FAILED))
        base.c.require(self.snapshots[origin.FAILED]['sha256']=='9f9ed9c66b47bbc991168177b8a15488965e5a353b887c6758ea4ad34f2b5b79'
            and failed['cleanup']and len(failed['steps'])==1 and not failed['steps'][0]['tests'],'EXACT265_COMPILE_FAILURE_NO_TESTS_RETAINED')
        collision=base.compact.unpack(self.json(FAILED))
        base.c.require(self.snapshots[FAILED]['sha256']=='44e5d9bfc4e7980427168d96833041d0108adea57ea8fe2e0140b72bc6a6ce40'
            and collision['cleanup']and not collision['steps']and collision['error_code']=='NEW_OWNED_REGISTRATION_TEMP_PARENT_ONLY',
            'EXACT266_SCRATCH_COLLISION_PREFLIGHT_NO_CARGO_OR_TESTS')
        old={p['path']:p for p in failed['source_pins']};second={p['path']:p for p in collision['source_pins']}
        for name in sorted(base.NEW|base.CHANGED):
            self.pin(name)
            if name==base.ADMISSION:
                text=self.text(name);marker='use crate::postgres::READ_TABLES;\n';base.c.require(text.count(marker)==1,'ONE_MISSING_ANCESTOR_IMPORT_ONLY')
                base.audit.inverse(text.replace(marker,''),old[name],'ADMISSION_RULES_AND_MODELS_IDENTICAL_TO265_EXCEPT_IMPORT')
            elif name not in{DRIVER,origin.DRIVER}:base.c.require(self.snapshots[name]==old[name],'ALL_PRODUCT_CONNECTOR_CALLBACK_AND_TESTS_UNCHANGED')
        self.pin(origin.DRIVER);base.c.require(self.snapshots[origin.DRIVER]==second[origin.DRIVER],'266_RECOVERY_DRIVER_PRESERVED')
        for pin in failed['newly_scoped_existing_compilation_migrations']:
            self.pin(pin['path']);base.c.require(self.snapshots[pin['path']]==pin,'ALL23_COMPILED_MIGRATIONS_UNCHANGED')
        print(json.dumps(dict(state='EARLY_FRESH_TEMP_AND_IMPORT_DELTA_PASS',product_or_test_body_change=False,actual_DB=False)),flush=True)


if __name__=='__main__':
    base.OUTPUT=OUTPUT;base.DRIVER=DRIVER;base.NEW=base.NEW|{origin.DRIVER,DRIVER};base.SCRATCH=SCRATCH;base.a.AcceptanceReader=RecoveryReader
    try:raise SystemExit(base.main())
    finally:base.a.AcceptanceReader=origin.OriginalReader
