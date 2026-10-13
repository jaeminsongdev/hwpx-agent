"""Independent P171 r2 audit; old failure/auditor remain immutable."""
from unittest.mock import patch
import audit_observed_writer_product as prior
import build_observed_writer_product_r2 as build
SELF='tools/p09/audit_observed_writer_product_r2.py'
ACTUAL='implementation/p09/evidence/p09-171-observed-writer-product-build.actual-run02.v1.json'
OLD='implementation/p09/evidence/p09-171-observed-writer-product-build.terminal-audit-run01.v1.json'
NEW='implementation/p09/evidence/p09-171-observed-writer-product-build.terminal-audit-run02.v1.json'
def main():
    raw=build.s.scoped_path
    raw_contracts=prior.d.contracts
    def destination(name,**kw):return raw(NEW if name==OLD else name,**kw)
    def contracts():
        with patch.object(build.prior,'contracts',raw_contracts):return build.contracts()
    with patch.object(prior,'SELF',SELF),patch.object(prior,'ACTUAL',ACTUAL), \
            patch.object(prior.d,'contracts',contracts),patch.object(prior.d,'CONTRACT_COUNT',205), \
            patch.object(prior.d,'helpers',build.helpers),patch.object(build.s,'scoped_path',destination):
        return prior.main()
if __name__=='__main__':raise SystemExit(main())
