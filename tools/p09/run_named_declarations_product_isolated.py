"""359: unique prechecked scratch; preserve357 compile and358 zero-test preflight failure, no guard change."""
import run_named_declarations_product_recovery as recovery
base=recovery.base
FAILED=base.OUTPUT
base.OUTPUT='implementation/p09/evidence/p09-361-named-declarations-product-isolated359.v1.json'
base.DRIVER='tools/p09/run_named_declarations_product_isolated.py'
base.NEW|={base.DRIVER}
previous_inverse=base.inverse

def inverse(q,old):
    previous_inverse(q,old);failed=base.compact.unpack(q.json(FAILED))
    base.c.require(q.snapshots[FAILED]['sha256']=='3b3385878710f7d3fa3b3e31cee972ba22174dfda967417d4e8df77f5d93ae4e'
        and failed['cleanup']and failed['steps']==[]and failed['fresh_inputs']==failed['final_fresh_hashes']==840
        and failed['error_code']=='NAMED_DECLARATIONS_PRODUCT_NEW_TEMP','EXACT358_OLD_SCRATCH_PREFLIGHT_ZERO_TEST_FAILURE_RETAINED')
    pins={p['path']:p for p in failed['source_pins']}
    for path in(base.STORE,base.PRODUCT,base.TEST,base.CORE):base.c.require(q.snapshots[path]==pins[path],'ALL358_PRODUCT_SOURCE_HELPER_LIMITS_AND_TESTS_UNCHANGED')
    driver='tools/p09/run_named_declarations_product.py';text=q.text(driver)
    text=text.replace("def main(scratch_relative='target/p09-named-declarations-product-scratch-357'):","def main():")
    block="""        guard.acquire();scratch=c.ROOT/scratch_relative
        c.require(scratch.parent==c.ROOT/'target'and not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_DECLARATIONS_PRODUCT_EARLY_NEW_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);old_run=compact.unpack(q.json(BASE));docs=q.json(DOCS))"""[:-1]
    base.c.require(text.count(block)==1,'ONE_EARLY_TEMP_PREFLIGHT_CHECK')
    text=text.replace(block,"        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);old_run=compact.unpack(q.json(BASE));docs=q.json(DOCS)")
    text=text.replace("        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_DECLARATIONS_PRODUCT_NEW_TEMP')",
        "        scratch=c.ROOT/'target/p09-named-declarations-product-scratch-357';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_DECLARATIONS_PRODUCT_NEW_TEMP')")
    base.audit.inverse(text,pins[driver],'ONLY_SCRATCH_ARGUMENT_AND_EARLY_PATH_EXISTENCE_CHECK_CHANGED_NO_CPU_RAM_INPUT_OR_TEST_POLICY_CHANGE')
base.inverse=inverse
if __name__=='__main__':raise SystemExit(base.main('target/p09-named-declarations-product-scratch-359'))
