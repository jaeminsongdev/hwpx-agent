"""370: absent tests after a pressure stop stay absent; preserve369 zero-test metadata failure."""
import run_compiled_personal_info_mask_recovery as recovery
base=recovery.base
FAILED=base.OUTPUT;OLD_DRIVER=base.DRIVER
base.OUTPUT='implementation/p09/evidence/p09-361-compiled-personal-info-mask-metadata-recovery370.v1.json'
base.DRIVER='tools/p09/run_compiled_personal_info_mask_metadata_recovery.py';base.NEW|={base.DRIVER}
previous_inverse=base.inverse

def inverse(q,old):
    previous_inverse(q,old);failed=base.compact.unpack(q.json(FAILED))
    base.c.require(q.snapshots[FAILED]['sha256']=='ec48c2bab8bc469c1897752469b18f7a1227a17ddc892e81eeda4f63fa34637a'and failed['cleanup']and failed['steps']==[]
        and failed['fresh_inputs']==failed['final_fresh_hashes']==864 and failed['error_type']=='KeyError','EXACT369_ZERO_TEST_MISSING_METADATA_KEY_FAILURE_RETAINED')
    pins={p['path']:p for p in failed['source_pins']};text=q.text(OLD_DRIVER)
    base.c.require(text.count("failed['steps'][0].get('tests',[])")==1,'ONE_OPTIONAL_TEST_METADATA_READ')
    base.audit.inverse(text.replace("failed['steps'][0].get('tests',[])","failed['steps'][0]['tests']"),pins[OLD_DRIVER],'ONLY_ABSENT_TEST_RESULT_KEY_READ_HARDENED_NO_PRODUCT_TEST_GUARD_OR_INPUT_POLICY_CHANGE')
base.inverse=inverse
if __name__=='__main__':recovery.early_name_check();raise SystemExit(base.main('target/p09-compiled-personal-info-mask-scratch-370'))
