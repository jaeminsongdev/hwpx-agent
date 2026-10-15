"""Read-only rerun planning; never a replacement for fresh admission.

Hash each distinct input once for this short diagnostic only. Actual stage
admission still performs its original independent source checks. No executor,
artifact publisher, persistent hash cache, GO or queue writer is provided.
"""
import hashlib
import json
from pathlib import Path
import time

PREFIX="implementation/p09/evidence/p09-361-case165-"


def stages(preflight_attempt=1):
    if type(preflight_attempt) is not int or not 1<=preflight_attempt<=8:raise ValueError("BOUNDED_PREFLIGHT_ATTEMPT")
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


def analyze(rows,read_json,signature):
    result=[];by_name={};cache={};hashed=0
    for stage in rows:
        name=stage["name"];dependencies=stage["dependencies"]
        if name in by_name or any(n not in by_name for n in dependencies):raise ValueError("ORDERED_UNIQUE_STAGE_DAG")
        if not valid_path(stage["path"]):raise ValueError("DIRECT_RELATIVE_STAGE_PATH")
        item=dict(name=name,path=stage["path"])
        try:row=read_json(stage["path"])
        except FileNotFoundError:item["status"]="MISSING_NOT_RUN"
        else:
            item["record_state"]=row.get("state") if type(row) is dict else None
            if type(row) is not dict or row.get("state")!=stage["state"]:
                item.update(status="FAILED_OR_OTHER_STATE",error_code=row.get("error_code") if type(row) is dict else None)
            elif not(row.get("cleanup_confirmed") is True and type(row.get("accepted_count_delta")) is int
                and row["accepted_count_delta"]==0 and row.get("GO_authorized") is False
                and type(row.get("fresh_inputs")) is int and row["fresh_inputs"]>0
                and type(row.get("final_fresh_hashes")) is int and row["final_fresh_hashes"]==row["fresh_inputs"]):
                item["status"]="INCOMPLETE_OR_INVALID_RECEIPT"
            else:
                pins=row.get("source_pins",row.get("current_source_pins"));stale=[];seen=set()
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
                        hashed+=1
                    if cache[path]!=pin:stale.append(path)
                item.update(status="STALE_INPUTS" if stale else "REUSE_CANDIDATE_NOT_RERUN",
                    inputs=len(pins),changed_inputs=len(stale),first_changed_paths=stale[:5])
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
        def unique(pairs):
            result={}
            for key,value in pairs:
                if key in result:raise ValueError("NO_DUPLICATE_PLANNING_KEYS")
                result[key]=value
            return result
        return json.loads(raw,object_pairs_hook=unique)
    def signature(self,name):
        digest=hashlib.sha256();size=0
        for chunk in self.chunks(name):digest.update(chunk);size+=len(chunk)
        return dict(path=name,bytes=size,sha256=digest.hexdigest())


def main():
    import argparse,sys
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()  # BelowNormal/one CPU, no whole-tree or Git discovery.
    parser=argparse.ArgumentParser();parser.add_argument("--preflight-attempt",type=int,default=1)
    parser.add_argument("--details",action="store_true")
    args=parser.parse_args();reader=BoundedReader(c.ROOT);started=time.monotonic()
    report=analyze(stages(args.preflight_attempt),reader.json,reader.signature)
    report.update(elapsed_seconds=time.monotonic()-started,actual_bytes_read=reader.bytes)
    if not args.details:
        report=dict(scope=report["scope"],reusable_stages=report["reusable_stages"],
            keep_without_rerun=[r["name"] for r in report["stages"] if r["status"]=="REUSE_CANDIDATE_NOT_RERUN"],
            needs_work=[r for r in report["stages"] if r["status"]!="REUSE_CANDIDATE_NOT_RERUN"],
            distinct_inputs_hashed_once=report["distinct_inputs_hashed_once"],
            actual_stage_admission_must_recheck_all_inputs=True,GO_authorized=False,
            elapsed_seconds=report["elapsed_seconds"],actual_bytes_read=reader.bytes)
    print(json.dumps(report,ensure_ascii=True))
    return 0


if __name__=="__main__":raise SystemExit(main())
