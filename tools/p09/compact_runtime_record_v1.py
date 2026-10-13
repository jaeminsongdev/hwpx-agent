"""Private final-JSON whitespace projection; every original body byte retained.
Only ONE raw_dump global lookup uses a lazy wrapper. The real json module and
its original patch/commit/cleanup chain remain. No fields dropped or old rewrite.
"""
import dis
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/compact_runtime_record_v1.py"
TEST="tools/p09/tests/test_compact_runtime_record_v1.py"
ALIAS="_p09_compact_raw_json_v1"

def require(ok,code):
    if not ok:raise ValueError("COMPACT_RUNTIME_RECORD_"+code)

def wrap(original,state):
    def dump(row,file,**kwargs):
        indent=kwargs.get("indent")
        require(indent is None or type(indent) is int and indent==2,"EXACT_ORIGINAL_INDENT_PROFILE")
        sep=kwargs.get("separators")
        require(sep is None or type(sep) is tuple and sep in ((",",": "),(", ",": ")), "ORIGINAL_SEPARATOR_PROFILE")
        options=dict(kwargs,indent=None,separators=(",",":"))
        state.actual_dump_calls+=1
        try:return original(row,file,**options)
        except BaseException:
            state.writer_errors_propagated+=1
            raise
    return dump

def connect(function):
    require(type(function) is FunctionType,"FUNCTION")
    code=function.__code__;instructions=list(dis.get_instructions(function))
    matches=[]
    for i,x in enumerate(instructions[:-2]):
        a,b=instructions[i+1:i+3]
        if (x.opname=="LOAD_GLOBAL" and x.argval=="json" and a.opname=="LOAD_ATTR" and a.argval=="dump"
            and b.opname in ("STORE_FAST","STORE_DEREF") and b.argval=="raw_dump"):
            matches.append(x)
    require(len(matches)==1 and ALIAS not in code.co_names and ALIAS not in function.__globals__,"ONE_CAPTURE_LEAF")
    ins=matches[0];index=len(code.co_names);argument=(index<<1)|(ins.arg&1)
    require(argument<=255 and ins.arg<=255 and code.co_code[ins.offset]==dis.opmap["LOAD_GLOBAL"]
            and code.co_code[ins.offset+1]==ins.arg and (ins.arg>>1)<len(code.co_names),"EXACT_SINGLE_BYTE_GLOBAL_OPCODE")
    patched=bytearray(code.co_code);patched[ins.offset+1]=argument
    fixed=code.replace(co_code=bytes(patched),co_names=code.co_names+(ALIAS,))
    require(fixed.replace(co_code=code.co_code,co_names=code.co_names)==code,"ALL_OTHER_ORIGINAL_CODE_FIELDS")
    state=NS(actual_capture_count=0,actual_dump_calls=0,writer_errors_propagated=0)
    original_json=function.__globals__["json"]
    class LazyJson:
        @property
        def dump(self):
            # Resolve at the SAME original capture time, including outer writers.
            state.actual_capture_count+=1
            return wrap(original_json.dump,state)
    env=dict(function.__globals__,**{ALIAS:LazyJson()})
    result=FunctionType(fixed,env,argdefs=function.__defaults__,closure=function.__closure__)
    return result,state,dict(one_global_lookup_argument_changed=True,all_other_original_code_fields_restored_exactly=True,
       original_defaults_closure_and_write_commit_cleanup_statements_retained=True,
       actual_json_dump_resolved_at_original_capture_time=True,default_json_module_mutated=False,
       all_fields_types_history_arrays_and_error_kwargs_retained=True,
       only_indent_and_separator_whitespace_changed=True,record_content_cache_or_extra_sampler=False,
       runtime151_product_or_Native_qualified=False,PC_freeze_resolved=False)
