"""One five-second decoder-work ceiling across metadata and Native Frame.

Original budget classes, run bodies, owner checks, callbacks and counters stay.
Frame-only evidence remains Frame-only; combined evidence is explicitly separate.
"""
import math
import os
import threading

SELF="tools/p09/shared_metadata_frame_decoder_budget_v1.py"
TEST="tools/p09/tests/test_shared_metadata_frame_decoder_budget_v1.py"
LIMIT_SECONDS=5.0


def require(ok,label):
    if not ok:raise ValueError("SHARED_DECODER_"+label)


class SharedBudget:
    def __init__(self,identity=lambda:(os.getpid(),threading.get_ident())):
        self.identity=identity;self.owner=identity();self.metadata=self.frame=None
        self.original_checks={};self.error=None;self.restored=False;self.checks=0
    def _work(self,budget):
        if budget is None:return 0.0
        elapsed=budget.elapsed
        require(type(elapsed) in (int,float) and math.isfinite(elapsed) and elapsed>=0,"ELAPSED_WORK")
        if budget.active is not None:
            active=budget.active;now=budget.now()
            require(type(active) in (int,float) and math.isfinite(active) and now>=active,"ACTIVE_WORK")
            elapsed+=now-active
        return elapsed
    def check(self):
        require(not self.restored and self.identity()==self.owner,"LIVE_SERIAL_OWNER")
        for budget in (self.metadata,self.frame):
            if budget is not None:require(budget.owner==self.owner,"SAME_ORIGINAL_BUDGET_OWNER")
        if self.error is not None:raise self.error
        self.checks+=1
        if self._work(self.metadata)+self._work(self.frame)>LIMIT_SECONDS:
            self.error=ValueError("STOP_SHARED_METADATA_FRAME_DECODER5")
            raise self.error
    def attach(self,role,budget):
        require(role in ("metadata","frame") and getattr(self,role) is None and not self.restored,"EXACT_ONE_BUDGET_PER_ROLE")
        require(budget.owner==self.owner and budget.elapsed==0 and budget.active is None
            and budget.attempts==budget.completed==0 and budget.error is None,"FRESH_ORIGINAL_BUDGET")
        original=budget.check
        require(callable(original),"ORIGINAL_CHECK")
        def checked():
            original()  # All original resource/deadline/owner/sticky errors first.
            self.check()
        self.original_checks[role]=original;setattr(self,role,budget);budget.check=checked
        return budget
    def restore(self):
        if self.restored:return
        for role,original in self.original_checks.items():getattr(self,role).check=original
        self.restored=True
    def evidence(self):
        require(self.identity()==self.owner,"EVIDENCE_SAME_OWNER")
        require(all(b is None or b.active is None for b in (self.metadata,self.frame)),"TERMINAL_EVIDENCE_ONLY")
        meta=self._work(self.metadata);frame=self._work(self.frame)
        return dict(shared_limit_seconds=LIMIT_SECONDS,metadata_decoder_work_seconds=meta,
            Frame_decoder_work_seconds=frame,total_decoder_work_seconds=meta+frame,
            metadata_registered=self.metadata is not None,Frame_registered=self.frame is not None,
            metadata_completed=0 if self.metadata is None else self.metadata.completed,
            Frame_completed=0 if self.frame is None else self.frame.completed,
            checks=self.checks,terminal_error_seen=self.error is not None,
            original_budget_classes_run_methods_and_counters_retained=True,
            original_resource_and_owner_checks_first=True,Frame_evidence_not_relabelled_as_combined=True,
            new_sampler_thread_or_process=False,actual_Native_or_product_or_acceptance_qualified=False)


def frame_type(base,binding,original_factory,shared):
    """Register the original Frame budget after its unchanged constructor."""
    original=original_factory(base,binding)
    require(isinstance(original,type),"ORIGINAL_FRAME_TYPE")
    class Frame(original):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            require(shared.metadata is not None,"METADATA_BUDGET_BEFORE_FRAME")
            shared.attach("frame",self.decoder_budget)
        def summary(self):
            return dict(super().summary(),shared_metadata_frame_decoder=shared.evidence())
    return Frame


def main():
    import argparse,io,json,sys,time,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import runtime_envelope_physical_io_v1 as physical
    import runtime_envelope_namespace_bundle_v1 as loader
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True);parser.add_argument("--attempt",type=int,required=True)
    args=parser.parse_args();require(164<=args.case<=249 and 1<=args.attempt<=8,"CLOSED_CODE_CONTEXT")
    output=c.ROOT/f"implementation/p09/evidence/p09-361-case{args.case}-shared-metadata-frame-decoder-code{args.attempt:03}.v1.json"
    require(not output.exists(),"EXCLUSIVE_CODE_RECEIPT")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic();q=None
    row=dict(state="FAILED_SHARED_METADATA_FRAME_DECODER_CODE_NOT_ADOPTED",accepted_count_delta=0,product_or_Native_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF);test=q.pin(TEST)
        q.pin(physical.SELF)
        tests,proof=loader.load(c.ROOT,[test],{"shared_metadata_frame_decoder_budget_v1":sys.modules[__name__],"runtime_envelope_physical_io_v1":physical})
        module=tests.test_shared_metadata_frame_decoder_budget_v1
        module.Tests.setUp.__globals__["CHECKPOINT"]=guard.check
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row["contracts"]=contracts;require(contracts==dict(run=8,errors=0,failures=0,skipped=0),"ALL_SHARED_BUDGET8")
        q.finish();guard.check(force=True)
        row.update(state="PASS_SHARED_METADATA_FRAME_DECODER_CODE_NOT_NATIVE_OR_PRODUCT",source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"CODE_GUARD_CLEANUP")
    raw=(json.dumps(row,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8");require(0<len(raw)<=262144,"BOUNDED_CODE_RECEIPT")
    for parent in (output.parent,*output.parent.parents):
        require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_CODE_ANCESTORS")
        if parent==c.ROOT:break
    with output.open("xb") as stream:
        require(stream.write(raw)==len(raw),"COMPLETE_CODE_RECEIPT");stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:row.get(k) for k in ("state","contracts","fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
