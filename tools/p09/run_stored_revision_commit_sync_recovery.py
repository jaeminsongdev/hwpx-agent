"""Reuse selected sync logic after naming the actual engine Unknown variant in its contract."""
import run_stored_revision_commit_sync as base

OUTPUT='implementation/p09/evidence/p09-361-stored-revision-commit-sync-recovery258.v1.json'
DRIVER='tools/p09/run_stored_revision_commit_sync_recovery.py'
FAILED=base.OUTPUT
FAILED_DRIVER=base.DRIVER
OriginalReader=base.a.AcceptanceReader


class RecoveryReader(OriginalReader):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        failed=self.json(FAILED)
        base.c.require(self.snapshots[FAILED]['sha256']=='43adb1d1d035add93735f89c647806aae9e28ed0a84410d1ef502df3aa919f18'
            and failed['cleanup']and failed['error_code']=='ACCURATE_SERVICE39_SCOPE_FAILURE_RECOVERY_METRICS_AND_OPEN_GATES',
            'EXACT257_SELECTED_DOC_MARKER_FAILURE_NO_CARGO_OR_TESTS')
        old={p['path']:p for p in failed['source_pins']}
        self.pin(FAILED_DRIVER);base.c.require(self.snapshots[FAILED_DRIVER]==old[FAILED_DRIVER],'ORIGINAL_SELECTED_DOC_SYNC_DRIVER_UNMODIFIED')
        before='| CommitOutcomeUnknown 또는 다른 성공 receipt | RevisionOutcomeUnknown, Incomplete/CommittedOutcomeUncertain |'
        after='| CommitOutcomeUnknown 또는 다른 성공 receipt | RevisionCasOutcome::Unknown → RevisionOutcomeUnknown, Incomplete/CommittedOutcomeUncertain |'
        text=self.text(base.PROFILE);base.c.require(text.count(after)==1,'NAME_EXISTING_ENGINE_UNKNOWN_VARIANT_IN_CONTRACT')
        base.audit.inverse(text.replace(after,before),old[base.PROFILE],'ONLY_DOC_ENUM_NAME_ADDED_NO_IMPLEMENTATION_OR_TEST_CHANGE')


if __name__=='__main__':
    base.OUTPUT=OUTPUT;base.DRIVER=DRIVER;base.a.AcceptanceReader=RecoveryReader
    try:raise SystemExit(base.main())
    finally:base.a.AcceptanceReader=OriginalReader
