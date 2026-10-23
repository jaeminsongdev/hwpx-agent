"""363: one missing test fixture module, original masking code/25 bodies unchanged; unique scratch."""
import run_personal_info_mask as base
FAILED=base.OUTPUT;OLD_DRIVER=base.DRIVER
base.OUTPUT='implementation/p09/evidence/p09-361-personal-info-mask-recovery363.v1.json'
base.DRIVER='tools/p09/run_personal_info_mask_recovery.py';base.NEW|={base.DRIVER}
original_inverse=base.inverse

def inverse(q,old):
    original_inverse(q,old);failed=base.compact.unpack(q.json(FAILED))
    base.c.require(q.snapshots[FAILED]['sha256']=='25d45769baac973b43e3c742020de1eedf1a86eb1b323679831de358405db042'and failed['cleanup']
        and failed['fresh_inputs']==failed['final_fresh_hashes']==848 and len(failed['steps'])==1 and failed['steps'][0]['tests']==[]and failed['steps'][0]['exit_code']==101
        and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0432'],'EXACT362_MISSING_FIXTURE_MODULE_COMPILE_FAILURE_ZERO_TESTS_PRESERVED')
    pins={p['path']:p for p in failed['source_pins']};base.c.require(q.snapshots[base.CORE]==pins[base.CORE],'ALL_MASKING_SOURCE_POLICIES_PROTECTION_BUDGETS_AND_PRIVACY_FLAGS_UNCHANGED')
    line='#[allow(dead_code)]#[path="support/document_import_review_assembly_fixture.rs"]mod assembly;\n';text=q.text(base.TEST)
    base.c.require(text.count(line)==1,'ONE_EXISTING_FIXTURE_MODULE_DECLARATION');base.audit.inverse(text.replace(line,''),pins[base.TEST],'ALL25_ORIGINAL_TEST_BODIES_UNCHANGED')
    text=q.text(OLD_DRIVER).replace("def main(scratch_relative='target/p09-personal-info-mask-scratch-362'):","def main():")
    text=text.replace('guard.acquire();scratch=c.ROOT/scratch_relative',"guard.acquire();scratch=c.ROOT/'target/p09-personal-info-mask-scratch-362'")
    base.audit.inverse(text,pins[OLD_DRIVER],'ONLY_NEW_RUN_SCRATCH_ARGUMENT_ADDED_TO_RUNNER_NO_GUARD_OR_INPUT_POLICY_CHANGE')
base.inverse=inverse
if __name__=='__main__':raise SystemExit(base.main('target/p09-personal-info-mask-scratch-363'))
