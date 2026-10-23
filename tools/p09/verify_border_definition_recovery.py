"""499: fixed strict absent variants; revalidate affected core8 and previously unrun products9 only."""
import json
import verify_border_definition_search as run

ORIGINAL=run.OUTPUT
OUTPUT='implementation/p09/evidence/p09-361-border-definition499.v1.json'
SELF='tools/p09/verify_border_definition_recovery.py'
base_inventory=run.inventory.inventory

def inventory(guard):
    # Include the terminal original failure and exact code/driver, never overwrite or promote it.
    names=base_inventory(guard)|{ORIGINAL,run.ARCHIVE+'border498.rs',run.ARCHIVE+'core498.rs',run.ARCHIVE+'runner498.py',run.SELF,SELF}
    guard.check()
    raw=(run.r.c.ROOT/ORIGINAL).read_bytes();run.r.c.require(len(raw)==124302,'BORDER499_ORIGINAL498_RECEIPT_SIZE')
    import hashlib
    run.r.c.require(hashlib.sha256(raw).hexdigest()=='34caa9753014d9f88cae54894ade2d11cb3ca08347dbe23e3559cf7195ff1ba5','BORDER499_ORIGINAL498_RECEIPT_UNCHANGED')
    row=run.layout.unpack(json.loads(raw));step=row['steps'][0]
    run.r.c.require(row['state']=='FAILED_REFERENCED_BORDER_DEFINITIONS'and row['cleanup']is True and row['final_fresh_hashes']==0
        and len(row['steps'])==1 and step['exit_code']==101 and len(step['tests'])==8
        and sum(status=='ok'for _,status in step['tests'])==7
        and [name for name,status in step['tests']if status!='ok']==['empty_unknown_bad_enums_and_out_of_range_nested_predicates_reject'],
        'BORDER499_CORE7_OBSERVED_NOT_PROMOTED_AND_PRODUCTS_NOT_RUN')
    return names

if __name__=='__main__':
    run.inventory.inventory=inventory
    run.OUTPUT=OUTPUT
    # Keep the immutable original harness code path pinned too. Dedicated temp avoids any reuse.
    original_environment=run.r.audit.environment
    def environment():
        env=original_environment();return env
    run.r.audit.environment=environment
    # run.main's scratch namespace is fixed498; the directory contains only the former compiler temp.
    # It must not be reused, so redirect only that literal constructor via a fresh main function.
    import inspect
    text=inspect.getsource(run.main)
    run.r.c.require(text.count("'target/p09-border-definition-scratch498'")==1,'BORDER499_ONLY_FRESH_SCRATCH_CHANGE')
    text=text.replace("'target/p09-border-definition-scratch498'","'target/p09-border-definition-scratch499'")
    namespace=dict(run.__dict__)
    exec(compile(text,SELF,'exec'),namespace)
    raise SystemExit(namespace['main']())
