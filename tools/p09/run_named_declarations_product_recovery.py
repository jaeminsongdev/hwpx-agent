"""358: preserve357 compile failure; fix only storage serializer ownership, same26+affected3 not yet run."""
import run_named_declarations_product as base
FAILED=base.OUTPUT
base.OUTPUT='implementation/p09/evidence/p09-361-named-declarations-product-recovery358.v1.json'
base.DRIVER='tools/p09/run_named_declarations_product_recovery.py'
base.NEW|={base.DRIVER}
original_inverse=base.inverse

def inverse(q,old):
    original_inverse(q,old);failed=base.compact.unpack(q.json(FAILED))
    base.c.require(q.snapshots[FAILED]['sha256']=='a427a58a759672606bcd74d0661e7deb9f5e6d4d7f6d699a0b63c29ead887e9a'
        and failed['cleanup']and len(failed['steps'])==1 and failed['steps'][0]['exit_code']==101 and not failed['steps'][0]['tests']
        and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0603'],'EXACT357_PRIVATE_SERIALIZER_COMPILE_FAILURE_ZERO_TESTS_RETAINED')
    pins={p['path']:p for p in failed['source_pins']}
    for path in(base.PRODUCT,base.TEST,base.CORE,base.STORE_PARENT,base.PRODUCT_PARENT):
        base.c.require(q.snapshots[path]==pins[path],'ALL357_STRICT_REQUESTS_TESTS_BINDINGS_AND_LIMITS_UNCHANGED')
    text=q.text(base.STORE);marker='// Storage owns its finite serializer; no reverse dependency on a private product-request helper.\n'
    base.c.require(text.count(marker)==1,'ONE_FINITE_STORAGE_OWNED_METADATA_SERIALIZER');text=text[:text.index(marker)]
    text=text.replace('bounded_metadata(&receipt,limits.maximum_result_bytes())?','crate::form_product_request::bounded(&receipt,limits.maximum_result_bytes()).map_err(|_|E::Limit)?')
    text=text.replace('bounded_metadata(&self.receipt,self.maximum_bytes)?','crate::form_product_request::bounded(&self.receipt,self.maximum_bytes).map_err(|_|E::Limit)?')
    base.audit.inverse(text,pins[base.STORE],'ONLY_PRIVATE_PRODUCT_SERIALIZER_CALLS_REPLACED_WITH_FINITE_STORAGE_SERIALIZER_NO_REQUEST_OUTPUT_LIMIT_OR_AUTHORITY_CHANGE')
base.inverse=inverse
if __name__=='__main__':raise SystemExit(base.main())
