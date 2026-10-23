"""Fix a checker-only newline boundary, run cheap delta contracts before the full source walk."""
import json
import run_stored_revision_jobs_recovery as origin
base=origin.base
OUTPUT='implementation/p09/evidence/p09-361-stored-revision-jobs-checker-recovery263.v1.json'
DRIVER='tools/p09/run_stored_revision_jobs_checker_recovery.py'
FAILED='implementation/p09/evidence/p09-361-stored-revision-jobs-recovery262.v1.json'


def inverse(q,old):
    text=q.text(base.MODEL)
    marker='''
    /// Exact precommit receipt bytes for immutable receipt storage; does not authorize CAS.
    /// # Errors
    /// Returns the same stable serialization error as the precommit digest.
    pub fn canonical_json(&self) -> Result<Vec<u8>, TransactionError> {
        serde_json::to_vec(self).map_err(|_| TransactionError::ReceiptSerialization)
    }
'''
    base.c.require(text.count(marker)==1,'EXACT_GETTER_WITH_LEADING_BLANK_AND_NO_TRAILING_BLANK');text=text.replace(marker,'')
    after='        let bytes = self.canonical_json()?;\n';before='        let bytes = serde_json::to_vec(self).map_err(|_| TransactionError::ReceiptSerialization)?;\n'
    base.c.require(text.count(after)==1,'PRECOMMIT_DIGEST_SAME_SERIALIZATION');base.audit.inverse(text.replace(after,before),old[base.MODEL],'ALL_ENGINE_FILE_BYTES_INTEGRITY_CAS_UNKNOWN_STATE_FAULT_AND_CANONICAL_FIELDS_UNCHANGED')
    text=q.text(base.base.ADAPTER)
    markers=['    retained_precommit: Option<ArtifactDescriptor>,\n',
        '            .field("precommit_retained", &self.retained_precommit.is_some())\n',
        '    #[must_use]\n    pub const fn retained_precommit(&self) -> Option<&ArtifactDescriptor> { self.retained_precommit.as_ref() }\n',
        '        self.persist_precommit(request)?;\n']
    for marker in markers:base.c.require(text.count(marker)==1,'EXACT_ADDITIVE_PRECOMMIT_STORAGE_BEFORE_INTENT_AND_CAS');text=text.replace(marker,'')
    after='retained_intent: None, retained_precommit: None, intent_sha256: None'
    base.c.require(text.count(after)==1,'EMPTY_PRECOMMIT_INITIAL_STATE');base.audit.inverse(text.replace(after,'retained_intent: None, intent_sha256: None'),old[base.base.ADAPTER],'ALL_OLD_SERVICE_AUTH_BINDING_JOURNAL_CAS_AND_RECOVERY_LOGIC_UNCHANGED')
    text=q.text(base.base.INTENT);start=text.index('    pub(super) fn persist_precommit(');end=text.index('    pub(super) fn persist_intent(',start)
    base.audit.inverse(text[:start]+text[end:],old[base.base.INTENT],'ORIGINAL_INTENT_FORMAT_AND_READONLY_RECOVERY_UNCHANGED')
    text=q.text(base.base.PARENT);base.c.require(text.endswith(base.CHILD)and text.count(base.CHILD)==1,'ONE_NEW_PRECOMMIT_TEST_CHILD')
    base.audit.inverse(text[:-len(base.CHILD)],old[base.base.PARENT],'ALL13_ORIGINAL_SERVICE_TEST_BODIES_UNCHANGED')
    text=q.text(base.RECOVERY_TEST);after='request.kind == ArtifactKind::Receipt && request.file_name.as_str() == "revision-intent.json"'
    base.c.require(text.count(after)==1,'OLD_NEGATIVE_SCANNER_STILL_DENIES_ONLY_ITS_INTENT_UNDER_TEST')
    base.audit.inverse(text.replace(after,'request.kind == ArtifactKind::Receipt'),old[base.RECOVERY_TEST],'ALL12_ORIGINAL_RECOVERY_TEST_BODIES_UNCHANGED_ONLY_SCANNER_TARGET_NAMED')


class RecoveryReader(origin.RecoveryReader):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        failed=base.compact.unpack(self.json(FAILED))
        base.c.require(self.snapshots[FAILED]['sha256']=='6c811b8289635d3726659aeb951ccb48c7fadf7347540b3a15c2830d5a62c390'
            and failed['cleanup']and not failed['steps']and failed['error_code']=='ONE_READONLY_PRECOMMIT_JSON_GETTER',
            'EXACT262_CHECKER_NEWLINE_MISMATCH_NO_CARGO_OR_TESTS')
        old=base.compact.unpack(self.json(base.base.OUTPUT))
        old={p['path']:p for p in old['source_pins']}
        for name in sorted(base.CHANGED|{base.sql_contract.UP,base.sql_contract.DOWN}):self.pin(name)
        inverse(self,old);base.sql_contract.check(self,base.c)
        print(json.dumps(dict(state='CHEAP_DELTA_CONTRACTS_PASS_BEFORE_FULL_SOURCE_WALK',product_inputs_changed_since262=False,SQL_runtime=False)),flush=True)


if __name__=='__main__':
    base.OUTPUT=OUTPUT;base.DRIVER=DRIVER;base.NEW=base.NEW|{origin.ORIGINAL_SQL,origin.DRIVER,DRIVER}
    base.a.AcceptanceReader=RecoveryReader;base.inverse=inverse
    try:raise SystemExit(base.main())
    finally:base.a.AcceptanceReader=origin.OriginalReader
