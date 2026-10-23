"""Preserve218 pre-Cargo comment false positive; exact nonbehavioral comment/test return fixes."""
from types import SimpleNamespace as NS
import run_source_search_manifest_components as target
OUTPUT='implementation/p09/evidence/p09-361-source-search-manifest-preflight-recovery219.v1.json'
DRIVER='tools/p09/run_source_search_manifest_preflight_recovery.py'
FAILED=target.OUTPUT
OriginalReader=target.a.AcceptanceReader
ORIGINAL_SELECTED=target.NEW|target.CHANGED
OLD_COMMENT='/// No public constructor/Deserialize. Manifest and routes are data for the later trusted executor.'
NEW_COMMENT='/// No public constructor or data deserialization. Manifest and routes are data for the later trusted executor.'
OLD_MATCH='''        match mode{0=>s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?,
            1=>s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("MANIFEST_SOURCE")?,6)?,_=>s.blobs.tamper.store(true,Ordering::SeqCst)}'''
NEW_MATCH='''        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?;},
            1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("MANIFEST_SOURCE")?,6)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}'''


class RecoveryReader(OriginalReader):
    def __init__(self,root,check):
        super().__init__(root,check);failed=self.json(FAILED)
        target.c.require(self.snapshots[FAILED]['sha256']=='65ee27be1f73fb73c4605bdd46baf9271c6e764875c7214ca4f23e56321054e1'
            and failed['state']=='FAILED_SOURCE_SEARCH_MANIFEST_COMPONENTS'and failed['cleanup']and failed['steps']==[]
            and failed['error_code']=='NO_FABRICATED_SUPPORT_TRUST_REIMPORT_NATIVE_OR_COMMIT','ORIGINAL218_COMMENT_FALSE_POSITIVE_BEFORE_CARGO_TEST0_PRESERVED')
        old={p['path']:p for p in failed['source_pins']}
        for name in sorted(ORIGINAL_SELECTED):
            text=self.text(name)
            if name==target.ROUTING:
                target.c.require(text.count(NEW_COMMENT)==1,'ONE_EXPLANATORY_COMMENT_ONLY')
                target.audit.inverse(text.replace(NEW_COMMENT,OLD_COMMENT),old[name],'ENTIRE218_PRODUCTION_ROUTING_BODY_UNCHANGED')
            elif name==target.TEST:
                target.c.require(text.count(NEW_MATCH)==1,'ONE_UNIT_RETURN_MATCH_EXPRESSION')
                target.audit.inverse(text.replace(NEW_MATCH,OLD_MATCH),old[name],'ALL26_NEW_REQUIREMENTS_UNCHANGED_EXCEPT_UNUSED_RETURN_VALUES')
            else:target.c.require(self.snapshots[name]==old[name],'ALL_OTHER218_NEW_CODE_AND_VERIFIER_UNCHANGED')


target.OUTPUT=OUTPUT
target.NEW=target.NEW|{DRIVER}
target.a=NS(Guard=target.a.Guard,AcceptanceReader=RecoveryReader)
if __name__=='__main__':raise SystemExit(target.main())
