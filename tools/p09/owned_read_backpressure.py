"""P187 bridge P185 IO yielding to existing c.run parent samples, no new sampler."""
import threading
import owned_source_read_pressure as original
import near_saturation_read_backpressure as pressure
import pre_go_parent_cpu_observer_r2 as observer
SELF='tools/p09/owned_read_backpressure.py'
TEST='tools/p09/tests/test_owned_read_backpressure.py'

class LatestOriginalSample:
    def __init__(self):self.lock=threading.Lock();self.samples=[]
    def record(self,row):
        with self.lock:self.samples[:]=[row]

def windows_type(samples):
    class Windows(observer.RAW_PARENT):
        def sample(self):
            row=super().sample();samples.record(row);return row
    return Windows

class OwnedReader(original.WeightedReader):
    def __init__(self,*args,samples,protected=(),**kw):
        super().__init__(*args,**kw)
        self.pressure=pressure.PressureCheckpoint(self.checkpoint,samples)
        self.checkpoint=self.pressure
        self.protected=frozenset(protected);self.active=self.completed=self.interrupted=None
    def _read(self,name,parse=False):
        self.active=name
        try:
            result=super()._read(name,parse=parse);self.completed=name;return result
        except (ValueError,OSError):self.interrupted=name;raise
        finally:self.active=None
    def diagnostics(self):
        closed=lambda n:n if n in self.protected and n.endswith('.exe') else None
        return dict(read_passes=self.read_passes,bytes_read=self.bytes_read,
            read_rates_by_kind=dict(binary=original.BINARY_RATE,other=original.OTHER_RATE),
            bytes_read_by_kind=dict(self.pacer.bytes_by_kind),near_saturation_read_backpressure=self.pressure.summary(),
            last_completed_protected_EXE_path=closed(self.completed),interrupted_protected_EXE_path=closed(self.interrupted),
            arbitrary_source_paths_or_private_artifact_names_saved=False,
            original_owned_read_operations_preserved=True,extra_sampler_or_native_query_started=False)
