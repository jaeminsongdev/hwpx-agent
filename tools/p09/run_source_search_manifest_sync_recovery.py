"""Preserve220 doc-only mismatch; clarify final head wording, no Rust/Cargo replay."""
from types import SimpleNamespace as NS
import run_source_search_manifest_sync as target
OUTPUT='implementation/p09/evidence/p09-361-source-search-manifest-sync-recovery221.v1.json'
DRIVER='tools/p09/run_source_search_manifest_sync_recovery.py'
FAILED=target.OUTPUT
ORIGINAL_SELECTED=target.RETAINED|target.DOCS|{target.DRIVER}
OriginalReader=target.a.AcceptanceReader
OLD='routing과 manifest 대조 뒤 source head를 한 번 더 확인하고'
NEW='routing과 manifest 대조 뒤 source 최종 head를 한 번 더 확인하고'


class RecoveryReader(OriginalReader):
    def __init__(self,root,check):
        super().__init__(root,check);failed=self.json(FAILED)
        target.c.require(self.snapshots[FAILED]['sha256']=='023648f7c782333415812a22c8dc8eb9f4b704da261e878df3fc5c6966c1a753'
            and failed['state']=='FAILED_SOURCE_MANIFEST_DOC_SYNC'and failed['cleanup']and not failed['actual_Cargo_or_tests']
            and failed['error_code']=='DOCUMENTED_ACTUAL26_AND_PER_CALL_ROUTING_NOT_TRUSTED_EXECUTION','EXACT220_DOC_WORDING_FAILURE_NOT_RUST_OR_PRODUCT_FAILURE')
        old={p['path']:p for p in failed['source_pins']}
        for name in sorted(ORIGINAL_SELECTED):
            self.pin(name)
            if name==target.PROFILE:
                text=self.text(name);target.c.require(text.count(NEW)==1,'ONE_CLARIFIED_FINAL_HEAD_PHRASE')
                target.audit.inverse(text.replace(NEW,OLD),old[name],'ENTIRE220_PROFILE_EXCEPT_FINAL_WORD_PRESERVED')
            else:target.c.require(self.snapshots[name]==old[name],'ALL220_SOURCE_TESTS_DOCS_AND_VERIFIER_UNCHANGED')


target.OUTPUT=OUTPUT
target.DRIVER=DRIVER
target.a=NS(Guard=target.a.Guard,AcceptanceReader=RecoveryReader)
if __name__=='__main__':raise SystemExit(target.main())
