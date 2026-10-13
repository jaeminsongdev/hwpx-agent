"""Keep exact pacer/kernel alias identities; instrument instance calls only.

V1 Timing's bounded/non-masking accounting remains. Unlike V1's proxy install,
the Native instance, pacer, kernel, phase_pacer and all checkpoint aliases retain
their exact objects. Original class methods, credits and cleanup are untouched.
Explicit fresh owned Native instances only, not a shared/default DLL object.
"""
import native_open_phase_timing_v1 as original

SELF = "tools/p09/native_open_phase_timing_v2.py"
TEST = "tools/p09/tests/test_native_open_phase_timing_v2.py"


def connect(native, acquisition, **kwargs):
    original.require(not hasattr(native, "acquisition_phase_timing"), "ONE_INSTALLATION")
    original.require(hasattr(acquisition, "current") and acquisition.current is None,
                     "INSTALL_BEFORE_ACQUISITION")
    pacer, kernel = native.pacer, native.k
    reserve, create = pacer.reserve, kernel.CreateFileW
    original.require(callable(reserve) and callable(create), "ORIGINAL_CALLABLES")
    timing = original.Timing(acquisition, **kwargs)

    def timed_reserve():
        return timing.call("original_reserve_including_checkpoints", reserve)

    def timed_create(*args):
        return timing.call("original_CreateFileW", create, *args)

    # Install transactionally. An assignment failure restores prior bindings.
    try:
        pacer.reserve = timed_reserve
        kernel.CreateFileW = timed_create
        native.acquisition_phase_timing = timing
    except BaseException:
        pacer.reserve = reserve
        kernel.CreateFileW = create
        raise
    return timing, dict(original_pacer=pacer, original_kernel=kernel,
                        original_reserve=reserve, original_CreateFileW=create,
                        original_native_instance=native,
                        pacer_kernel_and_checkpoint_alias_objects_unchanged=True,
                        original_native_class_or_default_module_mutated=False,
                        instance_call_boundaries_explicitly_instrumented=True,
                        cleanup_or_close_wrapped=False, GO_or_product_qualified=False)
