"""P188 aggregate IO of an explicit owned Job; no new PID or sampler query.

These are transfer/operation counters, not physical disk counters or causal
evidence about Defender. Missing/reset observations fail closed, not as zero.
"""
import ctypes
import conservative_maintenance as c

SELF='tools/p09/owned_job_io_observer.py'
TEST='tools/p09/tests/test_owned_job_io_observer.py'
REFERENCE='https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject'
STRUCT_REFERENCE='https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_and_io_accounting_information'
FIELDS=dict(read_operations='read_ops',write_operations='write_ops',other_operations='other_ops',
    read_bytes='read',write_bytes='write',other_bytes='other')

class CombinedAccounting(ctypes.Structure):
    _fields_=[('basic',c.Accounting),('io',c.IoCounters)]

class JobIoReader:
    def __init__(self,k):self.k=k;self.job=None;self.previous=None;self.completed_queries=0
    def query(self,job):
        c.require(type(job) is int and job>0,'OWNED_IO_EXPLICIT_JOB_REQUIRED')
        c.require(self.job is None or self.job==job,'OWNED_IO_JOB_SCOPE_CHANGED')
        info=CombinedAccounting()
        c.require(self.k.QueryInformationJobObject(job,8,ctypes.byref(info),ctypes.sizeof(info),None),
            'OWNED_IO_QUERY_FAILED')
        current={key:getattr(info.io,field) for key,field in FIELDS.items()}
        c.require(all(type(v) is int and 0<=v<=2**64-1 for v in current.values()),'OWNED_IO_COUNTER_INVALID')
        delta=None
        if self.previous is not None:
            c.require(all(current[k]>=self.previous[k] for k in current),'OWNED_IO_COUNTER_RESET')
            delta={k:current[k]-self.previous[k] for k in current}
        self.job=job;self.previous=current;self.completed_queries+=1
        return dict(job_IO_observed=True,job_IO_totals=current,job_IO_delta_since_previous_query=delta,
            job_IO_query_sequence=self.completed_queries,job_IO_scope='explicit_owned_job_aggregate_including_exited_members',
            job_IO_physical_disk_or_external_cause_proven=False)

def windows_type(base):
    class Windows(base):
        def __init__(self):super().__init__();self.job_io=JobIoReader(self.k)
        def accounting(self,job):
            # Preserve the entire original CPU/RAM/owned-members observation.
            # Only one extra query of this already-owned Job is added.
            row=super().accounting(job);row.update(self.job_io.query(job));return row
    return Windows
