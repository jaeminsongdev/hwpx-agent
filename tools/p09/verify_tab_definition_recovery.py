"""507: fix only test XML access; 506 failed compilation, zero cases were executed."""
import verify_tab_definition_search as d
d.SELF='tools/p09/verify_tab_definition_recovery.py'
d.OUTPUT='implementation/p09/evidence/p09-361-tab-definition507.v1.json'
failed='implementation/p09/evidence/p09-361-tab-definition506.v1.json'
fixture='crates/hwpx-package/tests/support/tab_definition_fixture.rs'
saved=d.ARCHIVE+'fixture506.rs'
original_inventory=d.inventory.inventory

def inventory(guard):
    names=original_inventory(guard)
    q=d.r.a.AcceptanceReader(d.r.c.ROOT,guard.check)
    old=d.layout.unpack(q.json(failed))
    d.r.c.require(q.snapshots[failed]['sha256']=='e068a5707a532daf0449926e9ee14e3a8141331c116de81b47ced84cb5f0af67'
        and old['state']=='FAILED_PARAGRAPH_REFERENCED_TAB_DEFINITIONS'and old['cleanup']is True
        and old['fresh_inputs']==955 and old['final_fresh_hashes']==0 and len(old['steps'])==1
        and old['steps'][0]['exit_code']==101 and old['steps'][0]['tests']==[],'TAB507_EXACT506_COMPILE_FAILURE_NO_CASE_REPLAY')
    q.pin(saved);text=q.text(fixture)
    before='.map(|a|a.semantic_value());'
    after='.map(|a|&result[a.value_span().start()..a.value_span().end()]);'
    d.r.c.require(text.count(after)==1,'TAB507_ONLY_PUBLIC_XML_SPAN_ACCESS_FIX')
    d.r.audit.inverse(text.replace(after,before),q.snapshots[saved],'TAB507_OTHER_FIXTURE_SOURCE_EXACT506')
    for pin in old['source_pins']:
        if pin['path']==fixture:
            d.r.c.require((pin['bytes'],pin['sha256'])==(q.snapshots[saved]['bytes'],q.snapshots[saved]['sha256']),'TAB507_ARCHIVE_EXACT506_FIXTURE')
    q.finish()
    return names|{failed,fixture,saved,d.SELF,'tools/p09/verify_tab_definition_search.py'}

d.inventory.inventory=inventory
if __name__=='__main__':raise SystemExit(d.main())
