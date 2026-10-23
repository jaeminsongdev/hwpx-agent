"""Preparation-only nested quota normalization, not Native policy mutation.

Windows nested CpuRate is relative to its parent. Verify the current actual
parent with the original readback, then give an inner subtree 100% of that
already capped quota. Global cap, RAM, affinity, priority and teardown stay.
Never use outside the verified limited parent or for a product permission.
"""
import copy

SELF='tools/p09/native011_nested_preparation_job.py'


def require(ok,label):
    if not ok:raise ValueError('NESTED_PREPARATION_'+label)


class InnerPreparationJob:
    def __init__(self,windows):
        self.original=windows;self.parent=windows.verify_job_limits(None)
        require(self.parent['verified'] is True and self.parent['breakaway_disabled'] is True
            and self.parent['kill_on_close'] is True and self.parent['affinity_mask']==1
            and self.parent['priority_class']==0x4000 and self.parent['active_process_limit']==16,
            'CURRENT_REAL_PARENT_ORIGINAL_PROTECTIONS')
        require(type(windows.cpu_rate) is int and type(windows.processors) is int and windows.processors>0
            and windows.cpu_rate==max(1,10000//windows.processors)
            and self.parent['cpu_hard_cap_machine_percent']==windows.cpu_rate/100,
            'CURRENT_PARENT_ONE_CPU_UPPER_BOUND_NOT_UNLIMITED')
        self.relative=copy.copy(windows);self.relative.cpu_rate=10000
        require(self.relative is not windows and windows.cpu_rate!=self.relative.cpu_rate,
            'PRIVATE_RELATIVE_CONFIGURATION_NOT_DEFAULT_POLICY_CHANGE')
        self.created=False
    def parent_check(self):
        require(self.original.verify_job_limits(None)==self.parent,'SAME_ACTUAL_PARENT_LIMITS_STILL_HELD')
    def create(self):
        require(not self.created,'ONE_INNER_JOB_CREATION');self.parent_check();self.created=True
        return self.relative.job()
    def verify(self,job):
        self.parent_check();inner=self.relative.verify_job_limits(job)
        require(inner['cpu_hard_cap_machine_percent']==100 and inner['verified'] is True
            and all(inner[key]==self.parent[key] for key in (
                'job_private_limit_mib','affinity_mask','priority_class','active_process_limit',
                'kill_on_close','breakaway_disabled')),'SAME_INNER_PROTECTIONS_PARENT_RELATIVE_CPU')
        # Do not label a nested relative percentage as a machine percentage.
        return dict(verified=True,parent_original_limit_readback=dict(self.parent),
            relative_parent_cpu_hard_cap_percent=inner['cpu_hard_cap_machine_percent'],
            maximum_system_CPU_percent=self.parent['cpu_hard_cap_machine_percent'],
            job_private_limit_mib=inner['job_private_limit_mib'],affinity_mask=inner['affinity_mask'],
            priority_class=inner['priority_class'],active_process_limit=inner['active_process_limit'],
            kill_on_close=inner['kill_on_close'],breakaway_disabled=inner['breakaway_disabled'],
            default_Windows_or_Native_policy_changed=False,product_or_GO_authorized=False)
