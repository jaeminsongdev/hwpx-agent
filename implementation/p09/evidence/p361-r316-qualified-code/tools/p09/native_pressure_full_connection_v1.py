"""Full Native/pressure-oracle dependency connection for156+ only.

Original code and every unrelated expectation stay intact. Four explicit AST
expectations reflect actual no-cooling/checkpoint substitutions. Historical
contexts use their original callbacks, not rewritten observations.
"""
import ast
import copy
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/native_pressure_full_connection_v1.py"
TEST="tools/p09/tests/test_native_pressure_full_connection_v1.py"

def require(ok,code):
    if not ok:raise ValueError("NATIVE_PRESSURE_FULL_"+code)

def clone(fn,**values):
    env=dict(fn.__globals__,**values)
    result=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
    result.__kwdefaults__=fn.__kwdefaults__
    require(result.__code__ is fn.__code__ and result.__defaults__ is fn.__defaults__
        and result.__closure__ is fn.__closure__,"ORIGINAL_CODE_DEFAULTS_CLOSURE")
    return result

def native_namespace(original,policy,raw,scope):
    model=policy.model_projection(original.model,raw(policy.MODEL_PIN),scope)
    def load(reader,rate,c):
        api=original.load(reader,rate,c)
        sources=[]
        for pin in (policy.PRESSURE_PIN,policy.EARLY_PIN,policy.ACQUISITION_PIN):
            current,data=reader._read(pin["path"],parse=True)
            reader._bind(pin["path"],current)
            require(current==pin,"FRESH_ORIGINAL_PRESSURE_SOURCE")
            sources.append(bytes(data))
        return policy.connect_api(api,sources[0],sources[1],acquisition_raw=sources[2])
    return NS(**{**vars(original),"load":load,"model":model})

def changed_expectations(node,changeset):
    before=ast.dump(node,include_attributes=False);node=copy.deepcopy(node);changed=[]
    for call in ast.walk(node):
        if not (isinstance(call,ast.Call) and isinstance(call.func,ast.Name)
            and call.func.id=="fields" and len(call.args)==3
            and isinstance(call.args[2],ast.Constant)):
            continue
        label=call.args[2].value
        if label not in changeset:continue
        dictionary=call.args[1]
        require(isinstance(dictionary,ast.Call) and isinstance(dictionary.func,ast.Name)
            and dictionary.func.id=="dict","EXACT_EXPECTATION_DICT")
        keywords={x.arg:x for x in dictionary.keywords}
        for key,(old,new) in changeset[label].items():
            require(key in keywords and isinstance(keywords[key].value,ast.Constant)
                and type(keywords[key].value.value) is type(old)
                and keywords[key].value.value==old,"EXACT_ORIGINAL_EXPECTATION")
            value=ast.Constant(value=new);value._pressure_original=copy.deepcopy(keywords[key].value)
            keywords[key].value=ast.copy_location(value,keywords[key].value)
            changed.append((label,key))
    expected={(label,key) for label,items in changeset.items() for key in items}
    require(len(changed)==len(expected) and set(changed)==expected,"EXACT_UNIQUE_PRESSURE_CHANGES")
    class Undo(ast.NodeTransformer):
        def visit(self,item):
            if hasattr(item,"_pressure_original"):return copy.deepcopy(item._pressure_original)
            return super().visit(item)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,
        "ALL_OTHER_FULL_ORACLE_STATEMENTS_RESTORED")
    return node

def direct_oracle(original,native):
    budget=clone(original.runtime_budget,views=native)
    cost=clone(original.cost,runtime_budget=budget)
    retained=clone(original.retained_evidence,runtime_budget=budget)
    def mechanics(node):
        node=original.mechanics_projection(node)
        return changed_expectations(node,{
            "BYTE_PRESSURE":{"cool_distinct_sample_windows":(2,0),"maximum_pause_windows_per_entry":(8,0)},
            "PHASE":{"clock_and_sleeper_and_checkpoint_retained":(True,False)},
            "FAIL_FAST":{"byte_boundary_cooling_policy_changed":(False,True)}})
    return NS(**{**vars(original),"runtime_budget":budget,"cost":cost,
        "retained_evidence":retained,"mechanics_projection":mechanics})

def projector(function,direct,index):
    require(type(index) is int and 115<=index<=249,"EXPLICIT_CONTEXT_INDEX")
    if index<=155:return function
    require("mechanics_projection" in function.__globals__ and "ORACLE_SCOPE" in function.__globals__,
        "ORIGINAL_FULL_PROJECTOR_INTERFACE")
    scope=NS(**{**vars(function.__globals__["ORACLE_SCOPE"]),"cost":direct.cost})
    return clone(function,mechanics_projection=direct.mechanics_projection,ORACLE_SCOPE=scope)

def additional_checker(original,raw):
    nodes=[n for n in ast.parse(raw.decode("utf-8")).body
        if isinstance(n,ast.FunctionDef) and n.name=="additional_observer_evidence"]
    require(len(nodes)==1,"ONE_ADDITIONAL_CHECKER")
    node=copy.deepcopy(nodes[0])
    def compiled_method(source):
        module=compile(source,original.__code__.co_filename,"exec",dont_inherit=True)
        methods=[x for x in module.co_consts if type(x) is type(original.__code__)
            and x.co_name=="additional_observer_evidence"]
        require(len(methods)==1,"ONE_COMPILED_ADDITIONAL_METHOD")
        return methods[0]
    require(compiled_method(raw)==original.__code__,"EXACT_ADDITIONAL_CHECKER_CODE")
    # This original checker calls original.fields, unlike the frozen112 body.
    before=ast.dump(node,include_attributes=False);matches=[]
    for call in ast.walk(node):
        if not (isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute)
            and isinstance(call.func.value,ast.Name) and call.func.value.id=="original"
            and call.func.attr=="fields" and len(call.args)==3
            and isinstance(call.args[2],ast.Constant) and call.args[2].value=="NEW_ACQUISITION_GUARD"):
            continue
        kw=next((x for x in call.args[1].keywords if x.arg=="original_outside_acquisition_cooling_retained"),None)
        require(kw is not None and isinstance(kw.value,ast.Constant) and kw.value.value is True,
            "EXACT_ACQUISITION_COOLING_BOOLEAN")
        value=ast.Constant(False);value._pressure_original=copy.deepcopy(kw.value)
        kw.value=ast.copy_location(value,kw.value);matches.append(1)
    require(len(matches)==1,"ONE_ADDITIONAL_EXPECTATION_CHANGE")
    class Undo(ast.NodeTransformer):
        def visit(self,item):
            if hasattr(item,"_pressure_original"):return copy.deepcopy(item._pressure_original)
            return super().visit(item)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,
        "ALL_OTHER_DIAGNOSTIC_COST_PROBE_AND_ACQUISITION_CHECKS_RESTORED")
    old="original_outside_acquisition_cooling_retained=True"
    new="original_outside_acquisition_cooling_retained=False"
    text=raw.decode("utf-8");require(text.count(old)==1,"ONE_SOURCE_COOLING_LITERAL")
    rewritten=text.replace(old,new,1)
    expected=ast.parse(text)
    expected.body=[node if isinstance(x,ast.FunctionDef) and x.name=="additional_observer_evidence" else x
        for x in expected.body]
    require(ast.dump(ast.parse(rewritten),include_attributes=False)==ast.dump(expected,include_attributes=False),
        "FULL_SOURCE_REWRITE_EQUALS_ONE_ORACLE_AST_CHANGE")
    return FunctionType(compiled_method(rewritten),dict(original.__globals__),
        argdefs=original.__defaults__,closure=original.__closure__)

def candidate_namespace(original,new_additional):
    inner=NS(**{**vars(original.original),"additional_observer_evidence":new_additional})
    return NS(**{**vars(original),"original":inner})

def evidence(row,a):
    require(type(row.get("selected_test_index")) is int and 156<=row["selected_test_index"]<=249,
        "NEW_ACTUAL_PRESSURE_EPOCH")
    frame=row["source_frame"];h=frame["handles"]
    a.fields(frame,dict(frame_state="COMMITTED",registered_live_frame=False,
        original_owned_cleanup_confirmed_before_release=True,original_two_actual_per_case_byte_reads_retained=True),
        "REAL_FULL_PRESSURE_FRAME_NOT_FOCUSED")
    a.fields(h["terminal_native_pressure_connection"],dict(pressure_class_installed=True,
        read_warning_percent=95,source_warning_percent=90,actual_cooling_loops_removed=True,
        hard_CPU_RAM_IO_lock_guards_retained=True,acquisition_and_two_byte_boundaries_not_interleaved=True,
        all_locks_before_first_read_retained=True,scope_or_byte_reads_reduced=False,new_sampler_or_query=False),
        "ACTUAL_PRIVATE_NATIVE_FACTORY")
    a.fields(h["acquisition_phase_pressure"],dict(clock_and_sleeper_and_checkpoint_retained=False,
        checkpoint_explicitly_replaced_by_stricter_failfast=True,
        phase_checkpoint_alias_rebound_by_qualified_connection=True,
        same_original_clock_sleeper_previous_and_open_counters_retained=True),"EXPLICIT_CHECKPOINT_NOT_OLD_POINTER")
    require(len(frame["actual_byte_boundaries"])==2,"BOTH_ACTUAL_BYTE_BOUNDARIES")
    for boundary in frame["actual_byte_boundaries"]:
        p=boundary["reader_diagnostics"]["near_saturation_read_backpressure"]
        a.fields(p,dict(terminal_failfast_pressure=True,cooling_or_resume_permitted=False,
            warning_latched=False,completed_pause_windows=0,requested_pause_seconds=0.0,
            original_warning_percent_retained=95,original_first_hard_guard_retained=True,
            original_latest_sample_method_retained=True,removed_cooling_sleep_calls=True,
            additional_sampler_or_native_query=False),"REAL_NATIVE_READ_TERMINAL_POLICY")
        require(type(p["failfast_calls"]) is int and p["failfast_calls"]>0,"ACTUAL_CHECKPOINT_CALLS")
    budget=row["complete_runtime_budget"]
    a.fields(budget,dict(nominal_early_yield_allowance_seconds=0,
        removed_native_cooling_allowance_seconds=4,actual_failfast_connection_required_before_GO=True,
        additional_early_source_wait_allowance_not_removed=True,additional_early_source_wait_allowance_seconds=11,
        unallocated_margin_seconds=60,unchanged_lock_deadline_seconds=600),"ONLY_REMOVED_PHYSICAL_COOLING_ALLOWANCE")
    return dict(actual_pressure_policy_and_cost_connected=True,original_full_product_source_resource_oracle_retained=True)
