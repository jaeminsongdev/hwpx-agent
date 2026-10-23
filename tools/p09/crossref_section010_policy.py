"""Fixed010 timing only: closed program boundaries, never a retry or Native permit.

The SAME original Native guard/Windows/mutex/CPU history survives every section.
Only its orchestration deadline changes after a closed boundary. Native startup,
operation and cleanup implementations are not changed by this module.
"""
import time

SELF='tools/p09/crossref_section010_policy.py'
SECTIONS=('preparation','qualification',*('case'+str(i)for i in range(1,9)),'batch_close','final_audit')
SECTION_SECONDS=600
WHOLE_SECONDS=1800

def require(ok,code):
    if not ok:raise ValueError('XREF_SECTION010_'+code)

def closed_boundary(row):
    if type(row)is not dict or row.get('closed')is not True:return False
    readers=row.get('readers')
    return(type(readers)is dict and set(readers)=={'source','native','shell','runtime'}
        and all(type(v)is dict and type(v.get('fresh_inputs'))is int and v['fresh_inputs']>0
            and type(v.get('final_fresh_hashes'))is int and v['final_fresh_hashes']==v['fresh_inputs']for v in readers.values()))

def guard_type(original):
    require(type(original)is type,'ORIGINAL_GUARD_TYPE')
    class SectionGuard(original):
        def __init__(self):
            super().__init__()
            require(not hasattr(self,'preparation_CPU'),'ORIGINAL_NATIVE_RESOURCE_POLICY')
            self.section_index=0;self.section_started=time.monotonic();self.whole_started=self.section_started
            self.whole_deadline=self.whole_started+WHOLE_SECONDS
            self.section_rows=[];self.section_failed=False;self.section_completed=False
        def check(self,force=False):
            try:
                require(not self.section_failed and not self.section_completed,'SEALED_NO_CONTINUATION')
                require(time.monotonic()<self.whole_deadline,'WHOLE1800_TIMEOUT')
                return super().check(force=force)
            except BaseException:
                self.section_failed=True
                raise
        def _close_section(self):
            now=time.monotonic()
            self.section_rows.append(dict(section=SECTIONS[self.section_index],elapsed_seconds=round(now-self.section_started,3),
                cumulative_sample_count=len(self.samples),closed=True))
            return now
        def advance(self,label,closed):
            try:
                self.check(force=True)
                require(self.section_index+1<len(SECTIONS)and label==SECTIONS[self.section_index+1],'EXACT_NEXT_SECTION_NO_RETRY')
                require(callable(closed)and closed()is True,'PREVIOUS_INPUTS_AND_OWNERS_CLOSED')
                # Expiration or pressure DURING closure cannot earn a new budget.
                self.check(force=True);now=self._close_section()
                self.section_index+=1;self.section_started=now;self.deadline=now+SECTION_SECONDS
            except BaseException:
                self.section_failed=True
                raise
        def complete(self,closed,*,preflight=False):
            try:
                require(type(preflight)is bool and self.section_index==(0 if preflight else len(SECTIONS)-1),'EXACT_COMPLETION_SECTION')
                self.check(force=True);require(callable(closed)and closed()is True,'FINAL_INPUTS_AND_OWNERS_CLOSED')
                self.check(force=True);self._close_section();self.section_completed=True
            except BaseException:
                self.section_failed=True
                raise
        def section_summary(self):
            return dict(policy='fixed010-closed-sections/v1',section_seconds=SECTION_SECONDS,whole_seconds=WHOLE_SECONDS,
                current_section=SECTIONS[self.section_index],closed_sections=list(self.section_rows),failed=self.section_failed,
                completed=self.section_completed,resource_history_reset=False,Native_operation_timeout_changed=False,
                original_exact_owner_cleanup_policy_changed=False)
    return SectionGuard
