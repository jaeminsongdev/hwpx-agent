"""Preserve136 metadata-only failure: a historical wrapper belongs to132, not135's imports."""
from pathlib import Path
import run_text_style_sync as base
FAILED=base.OUTPUT
base.OUTPUT='implementation/p09/evidence/p09-361-text-style-sync137.v1.json'
HISTORICAL='tools/p09/run_text_style_recovery.py'
base.RETAINED=base.RETAINED-{HISTORICAL}
original_inverse=base.target.inverse


def inverse(q,old,failed):
    original_inverse(q,old,failed);record=q.json(FAILED)
    base.c.require(q.snapshots[FAILED]['sha256']=='b0b37b801b7e5920ba61df4cbb5c8badd873a9ca7a6b4ab8b2a58baa4e0ce030'
        and record['state']=='FAILED_TEXT_STYLE_SYNC'and record['error_type']=='KeyError'and record['cleanup']
        and not record['actual_Cargo_or_tests'],'EXACT_METADATA_ONLY_WRONG_GENERATION_PIN_LOOKUP_FAILURE_PRESERVED')
    pins={p['path']:p for p in failed['source_pins']};q.pin(HISTORICAL)
    base.c.require(q.snapshots[HISTORICAL]==pins[HISTORICAL],'HISTORICAL_RECOVERY_HELPER_MATCHES_ITS_ACTUAL132_INPUT_GENERATION')
    q.pin(Path(__file__).relative_to(base.c.ROOT).as_posix())


base.target.inverse=inverse
if __name__=='__main__':raise SystemExit(base.main())
