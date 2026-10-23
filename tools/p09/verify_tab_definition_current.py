"""508: fresh scratch identity; all nineteen cases still unexecuted after two prep failures."""
import verify_tab_definition_search as d
import character_detail_receipt as layout
d.SELF='tools/p09/verify_tab_definition_current.py'
d.OUTPUT='implementation/p09/evidence/p09-361-tab-definition508.v1.json'
d.SCRATCH='target/p09-tab-definition-scratch508'
original_inventory=d.inventory.inventory
failures=(('implementation/p09/evidence/p09-361-tab-definition506.v1.json','e068a5707a532daf0449926e9ee14e3a8141331c116de81b47ced84cb5f0af67'),
    ('implementation/p09/evidence/p09-361-tab-definition507.v1.json','e105669745257ba8b824efd14e0e79a26171d268db0b9ae4cb0b9824f0f2b043'))

def inventory(guard):
    names=original_inventory(guard);q=d.r.a.AcceptanceReader(d.r.c.ROOT,guard.check)
    for path,sha in failures:
        old=layout.unpack(q.json(path));d.r.c.require(q.snapshots[path]['sha256']==sha and old['cleanup']is True
            and old['final_fresh_hashes']==0 and all(not step['tests']for step in old['steps']),'TAB508_ORIGINAL_FAILURES_NO_EXECUTED_CASES_OR_NATIVE')
    archive={d.ARCHIVE+name for name in('fixture506.rs','runner506.py','core507.rs','product507.rs')}
    for path in archive:q.pin(path)
    # Keep the exact original runner and failed sources, not a replaced success receipt.
    failed506=layout.unpack(q.json(failures[0][0]));prior={pin['path']:pin for pin in failed506['source_pins']}
    saved=q.snapshots[d.ARCHIVE+'runner506.py'];old=prior['tools/p09/verify_tab_definition_search.py']
    d.r.c.require((saved['bytes'],saved['sha256'])==(old['bytes'],old['sha256']),'TAB508_ORIGINAL506_DRIVER_ARCHIVED')
    q.finish();return names|archive|{path for path,_ in failures}|{d.SELF,'tools/p09/verify_tab_definition_search.py'}

d.inventory.inventory=inventory
if __name__=='__main__':raise SystemExit(d.main())
