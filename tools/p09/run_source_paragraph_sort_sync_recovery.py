"""Preserve233 missing SEARCH021 section label failure; rerun unchanged selected docs checks, no Cargo."""
import run_source_paragraph_sort_sync as base
base.DOCS=base.DOCS|{base.DRIVER,base.OUTPUT}
base.OUTPUT='implementation/p09/evidence/p09-361-source-paragraph-sort-sync-recovery234.v1.json'
base.DRIVER='tools/p09/run_source_paragraph_sort_sync_recovery.py'
if __name__=='__main__':raise SystemExit(base.main())
