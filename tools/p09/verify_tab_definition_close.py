"""510: complete retained-test input closure before selecting only the affected one."""
import verify_tab_definition_finalize as prior
d=prior.d
d.SELF='tools/p09/verify_tab_definition_close.py'
d.OUTPUT='implementation/p09/evidence/p09-361-tab-definition510.v1.json'
d.SCRATCH='target/p09-tab-definition-scratch510'

def inventory(guard):
    names=prior.inventory(guard);q=d.r.a.AcceptanceReader(d.r.c.ROOT,guard.check)
    old=d.layout.unpack(q.json(prior.BASE508));q.finish()
    # Historical inputs used to retain ten bodies must join the same main before/after reader.
    return names|{pin['path']for pin in old['source_pins']}|{d.SELF,'tools/p09/verify_tab_definition_finalize.py',
        'implementation/p09/evidence/p09-361-tab-definition509.v1.json'}

d.inventory.inventory=inventory
if __name__=='__main__':raise SystemExit(d.main())
