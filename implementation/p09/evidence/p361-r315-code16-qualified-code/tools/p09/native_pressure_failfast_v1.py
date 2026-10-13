"""Private stricter Native pressure policy: stop, never cool and resume.

Keep all input locks acquired before both real byte boundaries. Preserve the
original first hard guard, latest original sample, rate/deadline and cleanup.
Only the actual native-read cooling loop is removed from its cost allowance.
Historical sources, default modules and accepted evidence are never rewritten.
"""
import ast
import copy
import hashlib
from types import FunctionType, SimpleNamespace as NS

SELF = "tools/p09/native_pressure_failfast_v1.py"
TEST = "tools/p09/tests/test_native_pressure_failfast_v1.py"
PRESSURE_PIN = dict(path="tools/p09/near_saturation_read_backpressure.py",bytes=6072,
    sha256="82ad99f21ed2e3bf100e20809cea38173bb1e7749b71ab2430d661a8fd905162")
EARLY_PIN = dict(path="tools/p09/review_checkpoint_queue_stop.py",bytes=15604,
    sha256="2ca7510312eab46ccda26c894b84ae3900ef29688fefc25061cc1af8b2fbb797")
MODEL_PIN = dict(path="tools/p09/held_native_read_views_v1.py",bytes=13370,
    sha256="3aeb0c2ae50f2de0aeeba3c992aac5c0797367eac09c7693a5b3a7d5782e0584")
ACQUISITION_PIN = dict(path="tools/p09/current_queue_acquisition_checkpoint.py",bytes=3714,
    sha256="f737f7678f38a1d6e5118bd0a880a120b4327ac9458e4df56515c8484fe0395c")

def require(ok,code):
    if not ok:raise ValueError("NATIVE_PRESSURE_FAILFAST_"+code)

def verified_node(raw,pin,name,kind):
    require(type(raw) is bytes and len(raw)==pin["bytes"]
        and hashlib.sha256(raw).hexdigest()==pin["sha256"],"EXACT_SOURCE_PIN")
    nodes=[n for n in ast.parse(raw.decode("utf-8")).body if isinstance(n,kind) and n.name==name]
    require(len(nodes)==1,"ONE_EXACT_DEFINITION")
    return copy.deepcopy(nodes[0])

def checkpoint_type(original,raw,*,early=False,acquisition_raw=None):
    pin=EARLY_PIN if early else PRESSURE_PIN
    name="EarlySourceCheckpoint" if early else "PressureCheckpoint"
    node=verified_node(raw,pin,name,ast.ClassDef)
    acquisition_wrapper=False;source_original=original
    if early and PathName(original.__call__.__code__.co_filename)=="current_queue_acquisition_checkpoint.py":
        verified_node(acquisition_raw,ACQUISITION_PIN,"load",ast.FunctionDef)
        module=compile(acquisition_raw,original.__call__.__code__.co_filename,"exec",dont_inherit=True)
        load=next(x for x in module.co_consts if type(x) is type(original.__call__.__code__) and x.co_name=="load")
        body=next(x for x in load.co_consts if type(x) is type(load) and x.co_name=="EarlySourceCheckpoint")
        for method in ("__init__","__call__","summary"):
            expected=next(x for x in body.co_consts if type(x) is type(body) and x.co_name==method)
            require(expected==getattr(original,method).__code__,"EXACT_ACQUISITION_WRAPPER_CODE")
        source_original=original.__mro__[1];acquisition_wrapper=True
    env=dict(source_original.__call__.__globals__)
    exec(compile(ast.Module(body=[node],type_ignores=[]),
        source_original.__call__.__code__.co_filename,"exec",dont_inherit=True),env)
    expected=env[name]
    for method in ("__init__","latest","__call__","summary"):
        require(getattr(expected,method).__code__==getattr(source_original,method).__code__,"ORIGINAL_CHECKPOINT_CODE")
    warning=90 if early else 95
    require(source_original.__call__.__globals__["WARNING" if early else "WARNING_PERCENT"]==warning,
        "ORIGINAL_WARNING_UNCHANGED")
    class Checkpoint(original):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.failfast_latched=False;self.failfast_calls=0
        def __call__(self):
            require(not self.failfast_latched,"STOP_LATCHED_NATIVE_PRESSURE")
            if acquisition_wrapper and self.acquiring:
                return super().__call__()
            self.base()
            _,value=self.latest()
            self.failfast_calls+=1
            if value>=warning:
                self.warning_entries+=1;self.failfast_latched=True
                raise ValueError("STOP_NATIVE_SOURCE_PRESSURE_NO_COOLING" if early
                    else "STOP_NATIVE_READ_PRESSURE_NO_COOLING")
        def summary(self):
            row=super().summary()
            keys=("cool_distinct_samples","maximum_pause_windows") if early else (
                "cool_distinct_sample_windows","maximum_pause_windows_per_entry")
            for key in keys:row[key]=0
            row.update(terminal_failfast_pressure=True,failfast_calls=self.failfast_calls,
                warning_latched=self.failfast_latched,cooling_or_resume_permitted=False,
                original_warning_percent_retained=warning,original_first_hard_guard_retained=True,
                original_latest_sample_method_retained=True,removed_cooling_sleep_calls=True,
                additional_sampler_or_native_query=False)
            if acquisition_wrapper:
                row["acquisition_warning_checkpoint_stop"]=dict(row["acquisition_warning_checkpoint_stop"],
                    original_outside_acquisition_cooling_retained=False,
                    original_acquisition_code_and_one_way_latch_retained=True)
            require(row["completed_pause_windows"]==0 and row["requested_pause_seconds"]==0,
                "NO_REMOVED_COOLING_PATH_EXECUTED")
            return row
    return Checkpoint

def PathName(value):
    return value.replace("\\","/").rsplit("/",1)[-1]

def connect_api(api,pressure_raw,early_raw,*,acquisition_raw=None):
    Pressure=checkpoint_type(api.PressureCheckpoint,pressure_raw)
    Early=checkpoint_type(api.EarlySourceCheckpoint,early_raw,early=True,acquisition_raw=acquisition_raw)
    class InputLocks(api.InputLocks):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            previous=self.open_pressure
            require(type(previous) is api.PressureCheckpoint
                and self.api.pacer.checkpoint is previous,"EXACT_ORIGINAL_OPEN_PRESSURE")
            require(self.phase_pacer is self.api.pacer and self.phase_checkpoint is previous
                and self.original_open_checkpoint is previous
                and self.saturation_checkpoint.checkpoint is previous,
                "ALL_ORIGINAL_PRESSURE_ALIAS_IDENTITIES")
            self.open_pressure=Pressure(previous.base,previous.resources,sleep=previous.sleep)
            self.api.pacer.checkpoint=self.open_pressure
            self.phase_checkpoint=self.open_pressure
            self.original_open_checkpoint=self.open_pressure
            self.saturation_checkpoint.checkpoint=self.open_pressure
        def summary(self):
            row=super().summary()
            if "acquisition_source_warning_fail_fast" in row:
                row["acquisition_source_warning_fail_fast"]=dict(
                    row["acquisition_source_warning_fail_fast"],byte_boundary_cooling_policy_changed=True)
            row["terminal_native_pressure_connection"]=dict(
                pressure_class_installed=self.api.pacer.checkpoint is self.open_pressure,
                read_warning_percent=95,source_warning_percent=90,
                actual_cooling_loops_removed=True,hard_CPU_RAM_IO_lock_guards_retained=True,
                acquisition_and_two_byte_boundaries_not_interleaved=True,
                all_locks_before_first_read_retained=True,scope_or_byte_reads_reduced=False,
                new_sampler_or_query=False)
            return row
    return NS(**{**vars(api),"InputLocks":InputLocks,"PressureCheckpoint":Pressure,"EarlySourceCheckpoint":Early})

def model_projection(original,raw,scope):
    node=verified_node(raw,MODEL_PIN,"model",ast.FunctionDef)
    env=dict(original.__globals__)
    exec(compile(ast.Module(body=[copy.deepcopy(node)],type_ignores=[]),
        original.__code__.co_filename,"exec",dont_inherit=True),env)
    require(env["model"].__code__==original.__code__,"EXACT_ORIGINAL_COST_CODE")
    before=ast.dump(node,include_attributes=False);changes=[]
    class Project(ast.NodeTransformer):
        def visit_Call(self,n):
            if (isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name)
                and n.func.value.id=="scope" and n.func.attr=="cost"):
                value=copy.deepcopy(n);value.func=ast.Name(id="_no_cooling_cost",ctx=ast.Load())
                value._original_cost_call=copy.deepcopy(n);changes.append(1)
                return ast.copy_location(value,n)
            return self.generic_visit(n)
    node=Project().visit(node);require(len(changes)==1,"ONE_COST_DEPENDENCY")
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,"_original_cost_call"):return copy.deepcopy(n._original_cost_call)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,
        "ALL_ORIGINAL_RATES_DEADLINES_AND_MARGINS_RESTORED")
    def cost(required,rate):
        row=scope.cost(required,rate)
        require(row["nominal_early_yield_allowance_seconds"]==4 and row["unallocated_margin_seconds"]==60
            and row["unchanged_lock_deadline_seconds"]==600,"ONLY_NATIVE_COOLING_ALLOWANCE")
        total=row["predicted_combined_seconds"]-4
        return dict(row,nominal_early_yield_allowance_seconds=0,
            removed_native_cooling_allowance_seconds=4,predicted_combined_seconds=total,
            nominal_fits_unchanged_deadline=total<600,actual_failfast_connection_required_before_GO=True,
            additional_early_source_wait_allowance_not_removed=True)
    env=dict(original.__globals__,_no_cooling_cost=cost)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),
        original.__code__.co_filename,"exec",dont_inherit=True),env)
    return env["model"]
