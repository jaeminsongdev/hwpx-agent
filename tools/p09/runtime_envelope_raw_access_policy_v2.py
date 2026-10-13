"""Raw-source guard only: never obstruct original output/cleanup file opens.

V1 invoked the live Native checkpoint before every Python open, including the
original failed-run receipt writer. A terminal Native latch can prevent that
writer before the engine's original close/diagnostic path runs. Preserve the
guard-before-deny rule for mapped source paths; other paths keep their original
reader/resource guards rather than acquiring an unrelated extra Native guard.
"""
import os
import runtime_envelope_raw_access_policy_v1 as original
source=original.source
SELF="tools/p09/runtime_envelope_raw_access_policy_v2.py"
TEST="tools/p09/tests/test_runtime_envelope_raw_access_policy_v2.py"


class Policy(original.Policy):
    def check_access(self,name,api):
        source.require(api in self.calls_by_API,"DECLARED_OPEN_API")
        same_owner=self.identity()==self.owner
        if type(name) is int:
            if same_owner:self.non_path_calls+=1
            return
        try:value=os.fspath(name)
        except TypeError:return
        if type(value) is bytes:value=os.fsdecode(value)
        if type(value) is not str:return
        path=os.path.normcase(os.path.abspath(value))
        if same_owner:
            self.path_calls+=1;self.calls_by_API[api]+=1
        if path in self.blocked:
            if same_owner:self.checkpoint()
            if self.active():
                if same_owner:self.raw_attempts+=1
                raise ValueError("STOP_LIVE_RAW_ENVELOPE_RECEIPT_ACCESS")

    def evidence(self):
        return dict(super().evidence(),mapped_raw_source_original_guard_before_denial_retained=True,
            unrelated_output_or_cleanup_opens_not_given_extra_live_Native_checkpoint=True,
            original_physical_reader_resource_Frame_and_decoder_guards_not_replaced=True)
