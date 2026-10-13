"""P178 lower owned pre/post-hash IO, no removed reads or resource guards.

The unchanged live independent reader keeps its original 600-second scope and
P176 2.5/4MiB rates. Only compiler-owned pre/post/EXE hash reads select 1/2MiB.
No new scope/deadline is introduced or extended; original compile600/full1200
remain unchanged. This is a candidate pressure reduction, not freeze proof.
"""
import weighted_audit_io as prior
SELF='tools/p09/owned_source_read_pressure.py'
BINARY_RATE=1024*1024
OTHER_RATE=2*1024*1024
WeightedLiveReader=prior.WeightedLiveReader
resource_tail=prior.resource_tail

class OwnedPacer(prior.WeightedPacer):
    def select(self,name):
        super().select(name)
        self.rate=BINARY_RATE if self.kind=='binary' else OTHER_RATE

class WeightedReader(prior.WeightedReader):
    def __init__(self,*args,**kw):
        super().__init__(*args,**kw);self.pacer=OwnedPacer()
