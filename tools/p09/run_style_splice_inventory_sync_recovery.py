"""Preserve211 doc-only failure; clarify one phrase and avoid recovery helper's full735-input scan."""
from types import SimpleNamespace as NS
import run_style_splice_inventory_sync as sync
OUTPUT='implementation/p09/evidence/p09-361-style-splice-inventory-sync-recovery212.v1.json'
FAILED=sync.OUTPUT
DRIVER='tools/p09/run_style_splice_inventory_sync_recovery.py'
ORIGINAL_DRIVER=sync.DRIVER
OriginalReader=sync.a.AcceptanceReader
OLD='head/ACL/quarantine/AEAD·consumer 직전 head를 재사용한다. 검색·치환·원본 수입을 추가하지 않는다.'
NEW='head/ACL/quarantine/AEAD·consumer 직전 최종 head를 재사용한다. 검색·치환·원본 수입을 추가하지 않는다.'


class SelectedRecoveryReader(OriginalReader):
    def __init__(self,root,check):
        super().__init__(root,check)
        failed=self.json(FAILED)
        sync.c.require(self.snapshots[FAILED]['sha256']=='66c7849cdd8d192f889dccbcb14f8a8d154254b81aaee617d3bcfdcd9f3089d6'
            and failed['state']=='FAILED_STYLE_SPLICE_INVENTORY_DOC_SYNC'and failed['cleanup']
            and failed['error_code']=='DOCS_ACTUAL_FINAL_SPLICE50_AND_CURRENT_CONSUMER_BOUNDARY'
            and not failed['actual_Cargo_or_tests'],'EXACT211_DOC_ONLY_FAILURE_NOT_PRODUCT_OR_CARGO_FAILURE')
        old={p['path']:p for p in failed['source_pins']}
        # Only selected tested code and these docs; do not replay the old737-input closure.
        for name in sorted((sync.RETAINED|sync.DOCS|{ORIGINAL_DRIVER})-{sync.PROGRESS}):
            self.pin(name);sync.c.require(self.snapshots[name]==old[name],'ALL_SELECTED211_CODE_DOCS_AND_ORIGINAL_VERIFIER_UNCHANGED')
        text=self.text(sync.PROGRESS);sync.c.require(text.count(NEW)==1,'ONE_CLARIFIED_CONSUMER_FINAL_HEAD_PHRASE')
        sync.audit.inverse(text.replace(NEW,OLD),old[sync.PROGRESS],'ENTIRE211_PROGRESS_EXCEPT_ONE_FINAL_HEAD_WORD_PRESERVED')


# A local namespace chooses the original surgical inverse, not the compile-recovery wrapper that
# also scans every historical input. Original source/receipt/body inverse checks are unchanged.
sync.base=NS(**vars(sync.base))
sync.base.inverse=sync.target.ORIGINAL_INVERSE
sync.a=NS(Guard=sync.a.Guard,AcceptanceReader=SelectedRecoveryReader)
sync.OUTPUT=OUTPUT
sync.DRIVER=DRIVER
if __name__=='__main__':raise SystemExit(sync.main())
