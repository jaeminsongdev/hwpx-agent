"""Read-only rerun planning; never a replacement for fresh admission.

Hash each distinct input once for this short diagnostic only. Actual stage
admission still performs its original independent source checks. No executor,
artifact publisher, persistent hash cache, GO or queue writer is provided.
"""
import hashlib
import json
import math
from pathlib import Path
from pathlib import PurePosixPath
import time

PREFIX="implementation/p09/evidence/p09-361-case165-"
PLANNING_BOUNDS=("PLANNING_BYTE_BOUND","PLANNING_TIME_BOUND","PLANNING_RECORD_BOUND")
MAX_PREFLIGHT_RECORDS=16


def stages(preflight_attempt=1):
    if type(preflight_attempt) is not int or not 1<=preflight_attempt<=MAX_PREFLIGHT_RECORDS:raise ValueError("BOUNDED_PREFLIGHT_ATTEMPT")
    def stage(name,suffix,state,dependencies=()):return dict(name=name,path=PREFIX+suffix+".v1.json",state=state,dependencies=dependencies)
    rows=[
        stage("window_code","post-product-recovery-window-code006","PASS_RECOVERY_PRODUCT_WINDOW10_CODE_NOT_RUNTIME_CONNECTION_OR_RETRY"),
        stage("window_pipe","post-product-recovery-window-pipe005","PASS_ACTUAL_OWNED_WINDOW10_SHORT_CAPTURE_AND_TIMEOUT_NOT_NATIVE_OR_RETRY",("window_code",)),
        stage("failure_code","post-product-recovery-code003","PASS_POST_PRODUCT_STOP_REVIEW_CODE8_NOT_RUNTIME_RETRY_OR_ACCEPTANCE"),
        stage("failure_review","post-product-recovery-review003","PASS_READ_ONLY_POST_PRODUCT_FAILURE_CLASSIFICATION_NOT_RETRY_DISPATCH_OR_ACCEPTANCE",("failure_code",)),
        stage("recovery_code","prepared-recovery-code002","PASS_PREPARED_CLOSURE_AND_EXPLICIT_RECOVERY_CODE27_NOT_NATIVE_OR_PRODUCT")]
    for run in (4,5,6):rows.append(stage(f"closure{run}",f"prepared-only-closure-run{run:03}-attempt007",
        "PASS_PREPARATION_ONLY_CLOSED_WITHOUT_NATIVE_NOT_RUNTIME_OR_PRODUCT",("recovery_code",)))
    rows.append(stage("whole_CODE","successor-recovery-code-run008-attempt001",
        "PASS_CURRENT_SUCCESSOR_CODE_NOT_FULL_PREFLIGHT_NATIVE_OR_PRODUCT",tuple(r["name"] for r in rows)))
    rows.append(stage("whole_preflight",f"successor-recovery-preflight-run008-attempt{preflight_attempt:03}",
        "PASS_CURRENT_SUCCESSOR_WHOLE_METADATA_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",("whole_CODE",)))
    return rows


def valid_path(path):
    return type(path) is str and bool(path) and "\\" not in path and ":" not in path and all(
        part not in ("",".","..") for part in path.split("/"))


def discover_attempts(exists):
    """A setup-only failure consumes its slot too; never fill old gaps."""
    consumed=[]
    for attempt in range(1,MAX_PREFLIGHT_RECORDS+1):
        paths=[PREFIX+f"{kind}run008-attempt{attempt:03}.v1.json" for kind in (
            "successor-recovery-preflight-","closed-recovery-io-preflight-setup-","closed-recovery-io-preflight-")]
        if any(exists(path) for path in paths):consumed.append(attempt)
    last=max(consumed,default=0)
    return dict(consumed_attempts=consumed,latest_attempt=last or None,
        next_unused_attempt=last+1 if last<MAX_PREFLIGHT_RECORDS else None)


def safe_error(row):
    code=row.get("error_code") if type(row) is dict else None
    return code if type(code) is str and 0<len(code)<=160 and all(c.isascii() and (c.isalnum() or c=="_") for c in code) else None


def declared_cost(rows,product):
    """Original serial terms, for a mandatory subset, never a full-run PASS."""
    import current_stored_runtime_scope as scope
    pins=scope.pins(list(rows.values()))
    if type(product) is not int or product not in (10,15):raise ValueError("KNOWN_DECLARED_PRODUCT_WINDOW")
    dirs=len({p.as_posix() for name in pins for p in PurePosixPath(name).parents})
    binary=sum(p["bytes"] for n,p in pins.items() if n.lower().endswith(".exe"))
    other=sum(p["bytes"] for n,p in pins.items() if not n.lower().endswith(".exe"))
    if not(binary>0 and other>0):raise ValueError("BINARY_AND_OTHER_INPUTS_REQUIRED")
    total=(len(pins)+dirs)/14+2*binary/1048576+2*other/2097152+60+product+3+167/20+11+5+2.05+.5+5
    return dict(inputs=len(pins),directories=dirs,binary_bytes=binary,other_bytes=other,predicted_seconds=total)


def budget_lower_bound(reader):
    import current_stored_runtime_scope as scope
    import current_queue_successor_binding as bindings
    import prior_preparation_alias_v1 as aliases
    refs=[]
    def load(name,pin=None):
        raw=bytearray()
        for chunk in reader.chunks(name):
            raw.extend(chunk)
            if len(raw)>16*1048576:raise ValueError("BOUNDED_COST_METADATA")
        actual=dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        if pin is not None and actual!=pin:raise ValueError("EXACT_COST_METADATA_PIN")
        refs.append(actual)
        return json.loads(raw,object_pairs_hook=unique_json),actual
    authority,ap=load("implementation/p09/evidence/p09-361-case164-current-epoch-accept001.v1.json")
    if not(authority["accepted_count_after"]==158 and authority["next_runtime_index"]==165
        and authority["resource_cleanup_confirmed"] is True):raise ValueError("CURRENT_COST_PREDECESSOR")
    prior,pp=load(authority["runtime_candidate_pin"]["path"],authority["runtime_candidate_pin"])
    rep=prior["source_input_representation"]
    graph,gp=load(PREFIX+"successor-connections008.v10.json")
    manifest,mp=load(graph["manifest_pin"]["path"],graph["manifest_pin"]);pairs=manifest["descriptors"]
    if len(pairs)!=68:raise ValueError("COMPLETE_COST_TABLE68")
    code,cp=load(PREFIX+"successor-recovery-code-run008-attempt001.v1.json")
    if code["state"]!="PASS_CURRENT_SUCCESSOR_CODE_NOT_FULL_PREFLIGHT_NATIVE_OR_PRODUCT":raise ValueError("COST_DECLARED_CODE")
    failed,fp=load(PREFIX+"current-runtime-run007.v1.json",dict(path=PREFIX+"current-runtime-run007.v1.json",
        bytes=4199057,sha256="3271eb9b07cd0eb1462630bb0f61e7ca7894545ec67f0c516ea8d898391a0f6c"))
    mandatory=scope.pins(code["source_pins"])
    mandatory=scope.extend(mandatory,scope.pins([ap,pp,gp,mp,cp,fp]))
    mandatory=scope.extend(mandatory,scope.pins([r["semantic_original_pin"] for r in pairs]))
    mandatory,_=aliases.normalize(scope,rep["descriptors"],mandatory,165,reader.check)
    semantic=bindings.inherited_scope(scope,rep,authority["fresh_input_pins"],mandatory,reader.check)
    forward={r["semantic_original_pin"]["path"]:r for r in pairs}
    reverse={r["physical_envelope_pin"]["path"]:r for r in pairs}
    if len(forward)!=len(reverse) or len(forward)!=68:raise ValueError("BIJECTIVE_COST_TABLE")
    normalized={}
    for name,pin in semantic.items():
        if name in reverse:
            row=reverse[name]
            if pin!=row["physical_envelope_pin"]:raise ValueError("EXACT_COST_PHYSICAL_ALIAS")
            pin=row["semantic_original_pin"];name=pin["path"]
        if name in forward and pin!=forward[name]["semantic_original_pin"]:raise ValueError("EXACT_COST_LOGICAL_PIN")
        if name in normalized and normalized[name]!=pin:raise ValueError("NO_COST_CONFLICT_REBASE")
        normalized[name]=pin
    physical={}
    for name,pin in normalized.items():
        pin=forward[name]["physical_envelope_pin"] if name in forward else pin
        if pin["path"] in physical and physical[pin["path"]]!=pin:raise ValueError("NO_COST_PHYSICAL_CONFLICT")
        physical[pin["path"]]=pin
    if len(physical)!=len(normalized):raise ValueError("BIJECTIVE_COST_INPUTS")
    oldpins=scope.pins(failed["source_frame"]["actual_byte_boundaries"][0]["actual_byte_pins"])
    original=failed["complete_runtime_budget"]["predicted_runtime_combined_seconds"]
    if not math.isclose(declared_cost(oldpins,15)["predicted_seconds"],original,abs_tol=1e-8):raise ValueError("EXACT_OLD_MODEL_CALIBRATION")
    result=declared_cost(physical,10)
    return dict(scope="MANDATORY_DECLARED_LOWER_BOUND_NOT_FULL_PREFLIGHT_OR_GO",
        prior_model_formula_checked_against_original=original,mandatory_lower_bound=result,
        remaining_headroom_seconds=600-result["predicted_seconds"],
        future_pref_qualification_and_other_inputs_not_included=True,metadata_pins=refs,GO_authorized=False)


def unique_json(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError("NO_DUPLICATE_PLANNING_KEYS")
        result[key]=value
    return result


def analyze(rows,read_json,signature):
    result=[];by_name={};cache={};hashed=0
    for stage in rows:
        name=stage["name"];dependencies=stage["dependencies"]
        if name in by_name or any(n not in by_name for n in dependencies):raise ValueError("ORDERED_UNIQUE_STAGE_DAG")
        if not valid_path(stage["path"]):raise ValueError("DIRECT_RELATIVE_STAGE_PATH")
        item=dict(name=name,path=stage["path"])
        try:row=read_json(stage["path"])
        except ValueError as error:
            if error.args not in tuple((code,) for code in PLANNING_BOUNDS):raise
            item.update(status="BOUNDED_CHECK_INCOMPLETE_NOT_REUSABLE",error_code=error.args[0])
        except FileNotFoundError:
            item["status"]="MISSING_NOT_RUN"
            if name=="whole_preflight":
                number=stage["path"].rsplit("-attempt",1)[1].split(".",1)[0]
                setup_path=PREFIX+f"closed-recovery-io-preflight-setup-run008-attempt{number}.v1.json"
                try:setup=read_json(setup_path)
                except FileNotFoundError:pass
                else:
                    failed=type(setup) is dict and type(setup.get("state")) is str and setup["state"].startswith("FAILED_")
                    item.update(status="FAILED_SETUP_NO_PREFLIGHT" if failed else "SETUP_EXISTS_PREFLIGHT_MISSING",
                        setup_path=setup_path,error_code=safe_error(setup))
        else:
            item["record_state"]=row.get("state") if type(row) is dict else None
            if type(row) is not dict or row.get("state")!=stage["state"]:
                item.update(status="FAILED_OR_OTHER_STATE",error_code=safe_error(row))
            elif not(row.get("cleanup_confirmed") is True and type(row.get("accepted_count_delta")) is int
                and row["accepted_count_delta"]==0 and row.get("GO_authorized") is False
                and type(row.get("fresh_inputs")) is int and row["fresh_inputs"]>0
                and type(row.get("final_fresh_hashes")) is int and row["final_fresh_hashes"]==row["fresh_inputs"]):
                item["status"]="INCOMPLETE_OR_INVALID_RECEIPT"
            else:
                pins=row.get("source_pins",row.get("current_source_pins"));stale=[];seen=set();bound=None
                if type(pins) is not list or len(pins)!=row["fresh_inputs"]:raise ValueError("EXACT_PLANNING_INPUT_INVENTORY")
                for pin in pins:
                    if not(type(pin) is dict and set(pin)=={"path","bytes","sha256"} and valid_path(pin["path"])
                        and type(pin["bytes"]) is int and pin["bytes"]>0 and type(pin["sha256"]) is str
                        and len(pin["sha256"])==64 and all(c in "0123456789abcdef" for c in pin["sha256"])
                        and pin["path"] not in seen):raise ValueError("EXACT_UNIQUE_PLANNING_PIN")
                    path=pin["path"];seen.add(path)
                    if path not in cache:
                        try:cache[path]=signature(path)
                        except FileNotFoundError:cache[path]=None
                        except ValueError as error:
                            if error.args not in tuple((code,) for code in PLANNING_BOUNDS):raise
                            bound=error.args[0];break
                        hashed+=1
                    if cache[path]!=pin:stale.append(path)
                item.update(status="STALE_INPUTS" if stale else "REUSE_CANDIDATE_NOT_RERUN",
                    inputs=len(pins),changed_inputs=len(stale),first_changed_paths=stale[:5])
                if bound:item.update(status="BOUNDED_CHECK_INCOMPLETE_NOT_REUSABLE",error_code=bound)
        waiting=[n for n in dependencies if by_name[n]["status"]!="REUSE_CANDIDATE_NOT_RERUN"]
        if waiting:item["waiting_for_dependencies"]=waiting
        if waiting and item["status"]=="REUSE_CANDIDATE_NOT_RERUN":item["status"]="WAIT_FOR_DEPENDENCIES"
        by_name[name]=item;result.append(item)
    return dict(scope="READ_ONLY_PLANNING_NOT_QUALIFICATION_OR_EXECUTION",stages=result,
        reusable_stages=sum(r["status"]=="REUSE_CANDIDATE_NOT_RERUN" for r in result),
        distinct_inputs_hashed_once=hashed,actual_stage_admission_must_recheck_all_inputs=True,
        persistent_cache_created=False,GO_authorized=False,queue_advance_authorized=False)


class BoundedReader:
    def __init__(self,root,*,seconds=5,max_bytes=64*1048576):
        self.root=root;self.deadline=time.monotonic()+seconds;self.max_bytes=max_bytes;self.bytes=0
    def check(self):
        if time.monotonic()>=self.deadline:raise ValueError("PLANNING_TIME_BOUND")
    def path(self,name):
        self.check()
        if not valid_path(name):raise ValueError("DIRECT_PLANNING_PATH")
        target=self.root/name
        for path in (target,*target.parents):
            if path.is_symlink() or path.is_junction():raise ValueError("NO_PLANNING_LINKS")
            if path==self.root:break
        return target
    def chunks(self,name):
        with self.path(name).open("rb") as stream:
            while True:
                self.check();data=stream.read(65536)
                if not data:break
                self.bytes+=len(data)
                if self.bytes>self.max_bytes:raise ValueError("PLANNING_BYTE_BOUND")
                yield data
    def json(self,name):
        raw=bytearray()
        for chunk in self.chunks(name):
            raw.extend(chunk)
            if len(raw)>2*1048576:raise ValueError("PLANNING_RECORD_BOUND")
        return json.loads(raw,object_pairs_hook=unique_json)
    def signature(self,name):
        digest=hashlib.sha256();size=0
        for chunk in self.chunks(name):digest.update(chunk);size+=len(chunk)
        return dict(path=name,bytes=size,sha256=digest.hexdigest())
    def exists(self,name):return self.path(name).exists()


def main():
    import argparse,sys
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()  # BelowNormal/one CPU, no whole-tree or Git discovery.
    parser=argparse.ArgumentParser();parser.add_argument("--preflight-attempt",type=int)
    parser.add_argument("--details",action="store_true")
    parser.add_argument("--budget-lower-bound",action="store_true")
    args=parser.parse_args();reader=BoundedReader(c.ROOT);started=time.monotonic()
    history=discover_attempts(reader.exists)
    chosen=args.preflight_attempt if args.preflight_attempt is not None else history["latest_attempt"] or 1
    report=analyze(stages(chosen),reader.json,reader.signature)
    report.update(elapsed_seconds=time.monotonic()-started,actual_bytes_read=reader.bytes,preflight_attempts=history)
    if not args.details:
        report=dict(scope=report["scope"],reusable_stages=report["reusable_stages"],
            keep_without_rerun=[r["name"] for r in report["stages"] if r["status"]=="REUSE_CANDIDATE_NOT_RERUN"],
            needs_work=[r for r in report["stages"] if r["status"]!="REUSE_CANDIDATE_NOT_RERUN"],
            distinct_inputs_hashed_once=report["distinct_inputs_hashed_once"],
            actual_stage_admission_must_recheck_all_inputs=True,GO_authorized=False,
            elapsed_seconds=report["elapsed_seconds"],actual_bytes_read=reader.bytes,preflight_attempts=history)
    if args.budget_lower_bound:
        report["budget_lower_bound"]=budget_lower_bound(reader)
        report.update(elapsed_seconds=time.monotonic()-started,actual_bytes_read=reader.bytes)
    print(json.dumps(report,ensure_ascii=True))
    return 0


if __name__=="__main__":raise SystemExit(main())
