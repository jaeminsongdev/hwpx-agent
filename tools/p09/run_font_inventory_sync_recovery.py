"""322: reuse every321 check after equivalent report wording fix; retain its failed artifact."""
import run_font_inventory_sync as previous
BASE_READER=previous.a.AcceptanceReader
FAILED=previous.OUTPUT
LIBRARY=previous.DRIVER

class RecoveryReader(BASE_READER):
    """Add recovery provenance only; original reader bounds/freshness and all checks stay intact."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.pin(LIBRARY)
        failed=self.json(FAILED)
        previous.c.require(self.snapshots[FAILED]['sha256']=='a453ee57a3454eddf44a27c50b930557fed48a4fb3d38e9c62617ee2b15f25f1'
            and failed['state']=='FAILED_FONT_INVENTORY_SYNC'and failed['error_code']=='EXACT_INVENTORY_COMPONENT_COUNT_RESOURCE_AND_GATE_SCOPE'
            and failed['cleanup'],'EXACT321_REPORT_WORDING_FAILURE_RETAINED')

def main():
    previous.a.AcceptanceReader=RecoveryReader
    previous.OUTPUT='implementation/p09/evidence/p09-361-font-edit-inventory-sync-recovery322.v1.json'
    previous.DRIVER='tools/p09/run_font_inventory_sync_recovery.py'
    return previous.main()

if __name__=='__main__':raise SystemExit(main())
