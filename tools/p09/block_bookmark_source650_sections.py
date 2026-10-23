"""Five closed source-capture phases; original resource history/Native limits stay."""
import time
from prepared_bookmark631_sections import closed_boundary
SECTIONS=('preparation','qualification','capture','batch_close','final_audit')
SECTION_SECONDS=600
WHOLE_SECONDS=1800

def require(ok,code):
    if not ok:raise ValueError('XREF_BLOCK650_SECTION_'+code)

def guard_type(original):
    class Sections(original):
        def __init__(self):
            super().__init__()
            require(not hasattr(self,'preparation_CPU'),'ORIGINAL_NATIVE_POLICY')
            self.section_index=0;self.section_started=time.monotonic();self.whole_deadline=self.section_started+WHOLE_SECONDS
            self.section_rows=[];self.section_failed=False;self.section_completed=False
        def check(self,force=False):
            try:
                require(not self.section_failed and not self.section_completed,'SEALED')
                require(time.monotonic()<self.whole_deadline,'WHOLE1800_TIMEOUT')
                return super().check(force=force)
            except BaseException:self.section_failed=True;raise
        def _close_section(self):
            now=time.monotonic()
            self.section_rows.append(dict(section=SECTIONS[self.section_index],elapsed_seconds=round(now-self.section_started,3),cumulative_sample_count=len(self.samples),closed=True))
            return now
        def advance(self,label,closed):
            try:
                self.check(force=True)
                require(self.section_index+1<len(SECTIONS)and label==SECTIONS[self.section_index+1],'EXACT_NEXT_NO_RETRY')
                require(callable(closed)and closed()is True,'PREVIOUS_INPUTS_AND_OWNERS_CLOSED')
                self.check(force=True);now=self._close_section();self.section_index+=1;self.section_started=now;self.deadline=now+SECTION_SECONDS
            except BaseException:self.section_failed=True;raise
        def complete(self,closed,*,preflight=False):
            try:
                require(type(preflight)is bool and self.section_index==(0 if preflight else len(SECTIONS)-1),'EXACT_COMPLETION_PHASE')
                self.check(force=True);require(callable(closed)and closed()is True,'FINAL_CLOSURE');self.check(force=True)
                self._close_section();self.section_completed=True
            except BaseException:self.section_failed=True;raise
        def section_summary(self):
            return dict(policy='block-source650-five-closed-phases/v1',section_seconds=SECTION_SECONDS,whole_seconds=WHOLE_SECONDS,
                current_section=SECTIONS[self.section_index],closed_sections=list(self.section_rows),failed=self.section_failed,
                completed=self.section_completed,resource_history_reset=False,Native_operation_timeout_changed=False,
                original_exact_owner_cleanup_policy_changed=False)
    return Sections
