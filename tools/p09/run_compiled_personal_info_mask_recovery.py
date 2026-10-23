"""369: preserve367 pressure stop/zero tests; redacted Debug and early bounded name validation, no guard change."""
import re
import run_compiled_personal_info_mask as base
FAILED=base.OUTPUT;OBSERVATION='implementation/p09/evidence/p09-361-compiled-mask-post-stop-observation368.v1.json'
base.OUTPUT='implementation/p09/evidence/p09-361-compiled-personal-info-mask-recovery369.v1.json'
base.DRIVER='tools/p09/run_compiled_personal_info_mask_recovery.py';base.NEW|={base.DRIVER,OBSERVATION}
base.FONTS={'compiled_font_v1::common_dispatch_font_receipt_and_output_match_standalone_and_keep_route_denied','compiled_font_v2::appended_v2_family_preserves_all_nineteen_original_schema_positions'}
original_inverse=base.inverse
DEBUG='impl fmt::Debug for SourcePersonalInfoMaskEditInventory{fn fmt(&self,f:&mut fmt::Formatter<\'_>)->fmt::Result{f.write_str("SourcePersonalInfoMaskEditInventory(<redacted>; metadata_only)")}}\n'

def inverse(q,old):
    original_inverse(q,old);failed=base.compact.unpack(q.json(FAILED));observation=q.json(OBSERVATION)
    base.c.require(q.snapshots[FAILED]['sha256']=='ff9221ba74e9cc0fee9f2c6ea19b5c07057f6b5323ec6af1461cfdb3a0973b97'and failed['cleanup']and len(failed['steps'])==1
        and failed['steps'][0].get('tests',[])==[]and not failed['steps'][0]['bounded_output_observation']['observed_harness_started']
        and failed['error_code']=='STOP_PREPARATION_SYSTEM_PRESSURE90'and failed['failed_final_fresh_check'],'EXACT367_PRESSURE_STOP_BEFORE_TESTS_NO_PRODUCT_RESULT_OR_FINAL_FRESH_PROMOTION')
    pins={p['path']:p for p in failed['source_pins']}
    for path in base.CHANGED-{base.CORE}:base.c.require(q.snapshots[path]==pins[path],'ALL367_MODE_TYPES_STRICT_PARSERS_COMPILER_INVENTORY_AND_TEST_BODIES_UNCHANGED')
    text=q.text(base.CORE);base.c.require(text.count(DEBUG)==1,'ONE_REDACTED_INVENTORY_DEBUG_IMPLEMENTATION');base.audit.inverse(text.replace(DEBUG,''),pins[base.CORE],'ONLY_DEBUG_WARNING_FIXED_NO_MASKING_INVENTORY_HASH_OUTPUT_OR_BUDGET_CHANGE')
    base.c.require(not observation['peak_cause_attributed']and observation['original_owned_job']['owned_tree_empty']and observation['defender']['repo_exclusion_coverage']=='UNAVAILABLE_NOT_FALSE',
        'POST_STOP_SAMPLE_NOT_PEAK_ATTRIBUTION_OR_ASSUMED_DEFENDER_EXCLUSION_STATUS')
base.inverse=inverse

def early_name_check():
    # Small read-only fail-fast check, not a replacement for the guarded full fresh-source closure.
    specs=[(base.ROOT_TEST,'',base.AFFECTED),(base.TEST,'compiled::',None),
        ('crates/product-cli/tests/support/named_style_compiled.rs','compiled_named::',{s for s in base.NAMED if s.startswith('compiled_named::')}),
        ('crates/product-cli/tests/support/named_style_options_compiled.rs','named_options::compiled::',{s for s in base.NAMED if s.startswith('named_options::compiled::')}),
        ('crates/product-cli/tests/support/scoped_font_compiled.rs','compiled_font_v1::',{s for s in base.FONTS if s.startswith('compiled_font_v1::')}),
        ('crates/product-cli/tests/support/scoped_font_options_compiled.rs','compiled_font_v2::',{s for s in base.FONTS if s.startswith('compiled_font_v2::')}),
        ('crates/hwpx-package/tests/personal_info_mask.rs','',base.SOURCE)]
    for relative,prefix,wanted in specs:
        path=base.c.ROOT/relative;base.c.require(path.is_file()and not path.is_symlink()and path.stat().st_size<=128*1024,'FINITE_NAME_PREFLIGHT_SOURCE')
        names={prefix+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',path.read_text(encoding='utf-8'))}
        base.c.require(len(names)>0 and(wanted is None or wanted<=names),'ALL_SELECTED_ORIGINAL_TEST_IDENTITIES_EXIST_BEFORE_SOURCE_PREFLIGHT_OR_COMPILE')
if __name__=='__main__':early_name_check();raise SystemExit(base.main('target/p09-compiled-personal-info-mask-scratch-369'))
