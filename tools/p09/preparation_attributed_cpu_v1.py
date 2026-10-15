"""Candidate CPU policy for preparation only; no Native/GO installation.

Retain original hard guard, sampling, RAM/commit, deadline and cleanup. Only
fresh samples count toward pressure; cached source checkpoints cannot turn
one sample into a sustained event. All decisions latch and fail closed.
"""
import ctypes
import math

SELF="tools/p09/preparation_attributed_cpu_v1.py"
TEST="tools/p09/tests/test_preparation_attributed_cpu_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
PROFILE="P09_PREPARATION_ATTRIBUTED_CPU_V1_DESIGN"
RESPONSE="준비 단계 정책 재설계 허용"
CODE_STATE="PASS_PREPARATION_ATTRIBUTED_CPU_DESIGN_NOT_INSTALLED_OR_NATIVE"
POLICY=dict(system_warning_percent=75,immediate_system_stop_percent=90,
    consecutive_warning_samples=4,minimum_warning_span_seconds=1.5,
    owned_single_CPU_measurement_tolerance_factor=1.25,consecutive_owned_overload_samples=2)


def require(ok,label):
    if not ok:raise ValueError("PREPARATION_CPU_"+label)


def number(value):return type(value) in (int,float) and math.isfinite(value)


class State:
    def __init__(self,processors,role):
        require(type(processors) is int and 1<=processors<=64,"PROCESSOR_COUNT")
        require(type(role) is str and role in ("whole_metadata_preflight","dispatch_construction"),"NO_NATIVE_OR_PRODUCT_ROLE")
        self.processors=processors;self.role=role;self.index=0;self.fingerprint=None;self.stopped=False
        self.warning_run=0;self.warning_start=None;self.warning_samples=0;self.owned_run=0
        self.owned_limit=100/processors*POLICY["owned_single_CPU_measurement_tolerance_factor"]
        self.decisions=0;self.last_time=None;self.last_decision=None
    def stop(self,label):
        self.stopped=True;raise ValueError("STOP_PREPARATION_"+label)
    def observe(self,index,stamp,row):
        require(not self.stopped,"STOP_LATCHED")
        try:
            require(type(index) is int and index>0 and number(stamp),"FRESH_SAMPLE_ID_TIME")
            require(type(row) is dict,"SAMPLE_OBJECT")
            cpu=row.get("system_cpu_percent");parent=row.get("parent_cpu_machine_percent")
            require(number(cpu) and 0<=cpu<=100,"SYSTEM_SAMPLE_VALID")
            require(parent is None or number(parent) and 0<=parent<=100,"OWNED_SAMPLE_VALID")
            fingerprint=(stamp,cpu,parent)
            if index==self.index:
                require(fingerprint==self.fingerprint,"CACHED_SAMPLE_NOT_MUTATED")
                return self.last_decision
            require(index==self.index+1 and (self.last_time is None or stamp>self.last_time),"FRESH_SAMPLE_SEQUENCE")
            self.index=index;self.fingerprint=fingerprint;self.last_time=stamp;self.decisions+=1
            if cpu>=POLICY["immediate_system_stop_percent"]:self.stop("SYSTEM_PRESSURE90")
            if parent is None:
                if index!=1 or cpu>=POLICY["system_warning_percent"]:self.stop("CPU_ATTRIBUTION_MISSING")
            if parent is not None and parent>self.owned_limit:self.owned_run+=1
            else:self.owned_run=0
            if self.owned_run>=POLICY["consecutive_owned_overload_samples"]:self.stop("OWNED_CPU_OVERLOAD")
            if cpu>=POLICY["system_warning_percent"]:
                self.warning_samples+=1;self.warning_run+=1
                if self.warning_start is None:self.warning_start=stamp
                if self.warning_run>=POLICY["consecutive_warning_samples"]:
                    if stamp-self.warning_start<POLICY["minimum_warning_span_seconds"]:self.stop("SAMPLE_CADENCE_INVALID")
                    self.stop("SUSTAINED_SYSTEM_PRESSURE75")
                self.last_decision="WARNING_LOW_OWNED_LOAD" if self.owned_run==0 else "WARNING_OWNED_LOAD"
            else:
                self.warning_run=0;self.warning_start=None;self.last_decision="BELOW_SYSTEM_WARNING"
            return self.last_decision
        except ValueError:
            self.stopped=True;raise
    def summary(self):
        return dict(profile=PROFILE,role=self.role,policy=dict(POLICY),fresh_samples=self.decisions,
            warning_samples=self.warning_samples,consecutive_warning_samples=self.warning_run,
            parent_CPU_machine_percent_limit=self.owned_limit,stopped=self.stopped,
            cached_checkpoints_counted_as_new_samples=False,original_hard_guard_and_RAM_commit_deadline_required=True,
            Native_policy_changed=False,GO_authorized=False)


def owned_limits(windows):
    allowed=ctypes.c_size_t();system=ctypes.c_size_t();handle=windows.k.GetCurrentProcess()
    require(windows.k.GetProcessAffinityMask(handle,ctypes.byref(allowed),ctypes.byref(system)),"OWNED_AFFINITY_READBACK")
    require(allowed.value==windows.mask and allowed.value>0 and allowed.value&(allowed.value-1)==0,"OWNED_ONE_CPU_READBACK")
    require(windows.k.GetPriorityClass(handle)==0x4000,"OWNED_BELOW_NORMAL_READBACK")
    return dict(one_logical_CPU=True,priority="BelowNormal",readback_verified=True)


def guard_type(original,*,role):
    require(type(original) is type,"ORIGINAL_HARD_GUARD_TYPE")
    require(type(role) is str and role in ("whole_metadata_preflight","dispatch_construction"),"NO_NATIVE_OR_PRODUCT_ROLE")
    class Guard(original):
        def __init__(self):
            super().__init__()
            self.preparation_limits=owned_limits(self.windows)
            self.preparation_CPU=State(self.windows.processors,role)
        def check(self,force=False):
            require(not self.preparation_CPU.stopped,"STOP_LATCHED")
            try:
                require(type(force) is bool,"EXACT_FORCE_FLAG")
                # Original 98%/4 hard stop, RAM/commit, deadline and sampler first.
                result=super().check(force=force)
                require(type(self.samples) is list and bool(self.samples),"SAMPLE_MISSING")
                self.preparation_CPU.observe(len(self.samples),self.last,self.samples[-1])
                return result
            except (ValueError,OSError):
                self.preparation_CPU.stopped=True;raise
    return Guard


def main():
    import argparse,io,json,re,sys,time,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    host_policy=host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as old_pressure
    import distinct_final_sample_guard_v1 as distinct
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument("--attempt",type=int,required=True)
    parser.add_argument("--human-response",required=True);args=parser.parse_args()
    require(type(args.attempt) is int and 1<=args.attempt<=8,"BOUNDED_DESIGN_ATTEMPT")
    require(args.human_response==RESPONSE,"EXPLICIT_DESIGN_AUTHORIZATION")
    output=PREFIX+f"preparation-attributed-CPU-design-code{args.attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_DESIGN_RECEIPT")
    # Candidate is NOT installed in this producer. Its qualification itself
    # retains the original 75% fail-fast policy until the design is closed.
    guard=old_pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic();q=None
    row=dict(state="FAILED_PREPARATION_CPU_DESIGN_NOT_ADOPTED",accepted_count_delta=0,GO_authorized=False,
        runtime_policy_installed=False,next_preflight_start_authorized=False,host_resource_policy=host_policy,
        authorization=dict(source="explicit_user_reply_in_current_chat",response=args.human_response,scope="design_and_verify_preparation_only"))
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for path in (SELF,TEST):q.pin(path)
        from tests import test_preparation_attributed_cpu_v1 as tests
        tests.MODULE=sys.modules[__name__]
        q.pin(tests.REPLAY_PATH)
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        a.exact(row["contracts"],dict(run=20,errors=0,failures=0,skipped=0),"ALL_CPU_DESIGN20")
        row["owned_limits_readback"]=owned_limits(guard.windows)
        for module in tuple(sys.modules.values()):
            filename=getattr(module,"__file__",None)
            if filename and Path(filename).absolute().is_relative_to(c.ROOT/"tools/p09"):
                q.pin(Path(filename).absolute().relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True)
        row.update(state=CODE_STATE,CPU_policy=dict(POLICY),source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            original_hard_guard_RAM_commit_Job_IO_deadlines_and_Native_unchanged=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"DESIGN_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","fresh_inputs","final_fresh_hashes",
        "CPU_max","RAM_min","cleanup_confirmed","elapsed_seconds","error_code")}))
    return 0 if row["state"]==CODE_STATE else 1


if __name__=="__main__":raise SystemExit(main())
