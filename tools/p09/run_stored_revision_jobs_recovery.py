"""Register newly in-scope unchanged P14 SQL by read-only Git HEAD blob; preserve261 preflight."""
import run_stored_revision_jobs_components as base
OUTPUT='implementation/p09/evidence/p09-361-stored-revision-jobs-recovery262.v1.json'
DRIVER='tools/p09/run_stored_revision_jobs_recovery.py'
FAILED=base.OUTPUT
ORIGINAL_SQL=base.sql_contract.OLD
# One bounded git --no-optional-locks show HEAD:<file>, no status/tree traversal or writes.
SQL_BASELINE=dict(path=ORIGINAL_SQL,bytes=113376,sha256='cc60353df6cf3c51155417e39d0f1f4c348d2a6282bba7d63de9ea0282be5e5d')
OriginalReader=base.a.AcceptanceReader


class RecoveryReader(OriginalReader):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        failed=base.compact.unpack(self.json(FAILED))
        base.c.require(self.snapshots[FAILED]['sha256']=='f20c7a0edb81157d0d2adfc2aa6160d0157d34d7b89d9c8999c74943df1d53bf'
            and failed['cleanup']and not failed['steps']and failed['error_code']=='ALL_OTHER_PRODUCT_POSTGRES_SQL1_TO22_ROUTING_NATIVE_AND_TEST_INPUTS_UNCHANGED',
            'EXACT261_NEWLY_SCOPED_OLD_SQL_MISSING_PRIOR_PIN_NO_CARGO_OR_TESTS')
        self.pin(ORIGINAL_SQL)
        base.c.require(self.snapshots[ORIGINAL_SQL]==SQL_BASELINE,'FROZEN_P14_SQL_EXACT_READONLY_GIT_HEAD_BYTES_AND_SHA')
        previous={p['path']:p for p in failed['source_pins']}
        base.c.require(previous[ORIGINAL_SQL]==SQL_BASELINE,'261_LIVE_ORIGINAL_SQL_WAS_ALREADY_UNMODIFIED')


if __name__=='__main__':
    base.OUTPUT=OUTPUT;base.DRIVER=DRIVER;base.NEW=base.NEW|{ORIGINAL_SQL,DRIVER};base.a.AcceptanceReader=RecoveryReader
    try:raise SystemExit(base.main())
    finally:base.a.AcceptanceReader=OriginalReader
