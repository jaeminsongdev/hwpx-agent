"""509: retain ten exact508 bodies; fix referenced-font lookup and run one core/eight stored."""
import verify_tab_definition_search as d
d.SELF='tools/p09/verify_tab_definition_finalize.py'
d.OUTPUT='implementation/p09/evidence/p09-361-tab-definition509.v1.json'
d.SCRATCH='target/p09-tab-definition-scratch509'
BASE508='implementation/p09/evidence/p09-361-tab-definition508.v1.json'
FIXTURE='crates/hwpx-package/tests/support/tab_definition_fixture.rs'
FAILED='tab_definitions::combined_font_privacy_projection_keeps_tab_conditions_and_distinct_request_identity'
BEFORE='    Ok(catalog.font_faces.iter().find(|group|group.language==hwpx_package::LanguageSlot::Hangul).ok_or("hangul")?.fonts.first().ok_or("font0")?.face.clone())\n'
AFTER='    let id=catalog.styles.first().ok_or("char0")?.font_refs.hangul;\n    Ok(catalog.font_faces.iter().find(|group|group.language==hwpx_package::LanguageSlot::Hangul).ok_or("hangul")?.fonts.get(id as usize).ok_or("referenced font")?.face.clone())\n'
original_inventory=d.inventory.inventory

def inventory(guard):
    return original_inventory(guard)|{BASE508,d.SELF,'tools/p09/verify_tab_definition_search.py'}|{d.ARCHIVE+name for name in
        ('fixture506.rs','fixture508.rs','runner506.py','runner508.py','core507.rs','product507.rs')}

def select(q,core,stored):
    c=d.r.c;old=d.layout.unpack(q.json(BASE508))
    c.require(q.snapshots[BASE508]['sha256']=='d266b621fba17d54740d8a892459091f2d5dfaabe00fa5f029138c70ec8fe7af'
        and old['cleanup']is True and old['fresh_inputs']==962 and old['final_fresh_hashes']==0 and len(old['steps'])==1,'TAB509_EXACT508_ORIGINAL_FAILURE')
    step=old['steps'][0];passed={name for name,status in step['tests']if status=='ok'}
    c.require(step['exit_code']==101 and len(step['tests'])==11 and len(passed)==10 and passed|{FAILED}==core
        and [(name,status)for name,status in step['tests']if status!='ok']==[(FAILED,'FAILED')]
        and step['panic_locations']==['crates/hwpx-package/tests/support/tab_definition_contract.rs:91:48'],'TAB509_RETAIN_EXACT_TEN_OBSERVED_BODIES')
    for pin in old['source_pins']:
        name=pin['path']
        if name in(FIXTURE,'tools/p09/verify_tab_definition_search.py'):
            saved=q.snapshots[d.ARCHIVE+('fixture508.rs'if name==FIXTURE else'runner508.py')]
            c.require((saved['bytes'],saved['sha256'])==(pin['bytes'],pin['sha256']),'TAB509_CHANGED_FIXTURE_AND_DRIVER_ARCHIVED')
        else:c.require(q.snapshots[name]==pin,'TAB509_LIBRARY_GUARDS_AND_ALL_PREVIOUS_BODIES_UNCHANGED')
    fixture=q.text(FIXTURE);c.require(fixture.count(AFTER)==1,'TAB509_ONE_REFERENCED_FONT_LOOKUP_FIX')
    d.r.audit.inverse(fixture.replace(AFTER,BEFORE),q.snapshots[d.ARCHIVE+'fixture508.rs'],'TAB509_ALL_OTHER_FIXTURE_AND_TAB_SOURCE_UNCHANGED')
    driver=q.text('tools/p09/verify_tab_definition_search.py').replace('SELECT_CASES=None\n','').replace(
        '        if SELECT_CASES is not None:core,stored,retained=SELECT_CASES(q,core,stored);row.update(retained_case_names=sorted(retained),retained_cases=len(retained))\n','')
    d.r.audit.inverse(driver,q.snapshots[d.ARCHIVE+'runner508.py'],'TAB509_ONLY_EXPLICIT_CASE_SELECTION_HOOK_NO_GUARD_OR_VALIDATION_CHANGE')
    # font_name is used only by the failed source case and the never-executed new stored case.
    for name in(d.NEWCORE,d.NEWPRODUCT):
        c.require(q.text(name).count('font_name()')==1,'TAB509_FIXTURE_LOOKUP_CHANGE_HAS_TWO_EXACT_CALLERS')
    return {FAILED},stored,passed

d.inventory.inventory=inventory;d.SELECT_CASES=select
if __name__=='__main__':raise SystemExit(d.main())
