"""Fail-closed cleanup successor; published native v1 stays immutable.

Snapshot.capture error may include a failed native CloseHandle. Do not promote
an unknown cleanup to success. Stop this observer, expose uncertainty, and never
retry. Successful snapshots and closed budget stops retain v1's exact behavior.
"""
import native_process_cpu_attribution_v1 as prior

SELF = "tools/p09/native_process_cpu_attribution_v2.py"
TEST = "tools/p09/tests/test_native_process_cpu_attribution_v2.py"


class Probe(prior.Probe):
    def __init__(self, *args, **kwargs):
        self.capture_failure_cleanup_unknown = False
        super().__init__(*args, **kwargs)

    def capture(self):
        result = super().capture()
        if self.disabled_reason == "NATIVE_PROCESS_QUERY_UNAVAILABLE":
            # v1 caught an API exception; CloseHandle may have been its cause.
            self.capture_failure_cleanup_unknown = True
            self.cleanup = False
        return result

    def close(self):
        self.previous = None
        self.cleanup = not self.capture_failure_cleanup_unknown
        return self.cleanup

    def summary(self):
        row = super().summary()
        row.update(backend="NATIVE_TOOLHELP_PROCESS_TIMES_V2",
                   capture_failure_cleanup_unknown=self.capture_failure_cleanup_unknown,
                   native_capture_handle_cleanup_status=("UNRESOLVED" if self.capture_failure_cleanup_unknown else "CONFIRMED"),
                   capture_error_never_promoted_to_successful_cleanup=True,
                   automatic_retry_or_resume=False)
        return row


def windows_type(original, objects, *, factory=Probe, clock=prior.time.monotonic):
    return prior.windows_type(original, objects, factory=factory, clock=clock)


def close(objects):
    return prior.close(objects)  # original all-owner cleanup, no short circuit


def summary(objects):
    row = prior.summary(objects)
    row["backend"] = "NATIVE_TOOLHELP_PROCESS_TIMES_V2"
    return row
