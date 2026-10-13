"""Reuse Native READ/seek count scratch; no byte or identity cache.
Original pinned API/guards/64KiB/fresh buffer/ReadFile/error statements remain.
Opt-in component only; NOT current149 input or a PC-freeze resolution claim.
"""
import ast
import copy
import ctypes
from ctypes import wintypes as w
import hashlib
import threading
import held_native_read_views_v1 as prior

SELF="tools/p09/native_read_call_scratch_v1.py"
TEST="tools/p09/tests/test_native_read_call_scratch_v1.py"
ORIGINAL_PIN=dict(path="tools/p09/held_native_read_views_v1.py",bytes=13370,
 sha256="3aeb0c2ae50f2de0aeeba3c992aac5c0797367eac09c7693a5b3a7d5782e0584")

def require(ok,code):
    if not ok:raise ValueError("NATIVE_READ_SCRATCH_"+code)

def project(raw):
    require(type(raw) is bytes and len(raw)==ORIGINAL_PIN["bytes"] and
            hashlib.sha256(raw).hexdigest()==ORIGINAL_PIN["sha256"],"EXACT_OLD_API_SOURCE")
    cls=[n for n in ast.parse(raw.decode("utf-8")).body if isinstance(n,ast.ClassDef) and n.name=="NativeRead"]
    require(len(cls)==1,"ONE_NATIVE_API")
    functions={n.name:n for n in cls[0].body if isinstance(n,ast.FunctionDef) and n.name in ("reset","readinto")}
    require(set(functions)=={"reset","readinto"},"BOTH_ORIGINAL_API_BODIES")
    output={};proof={}
    for name,original in functions.items():
        variable,field=("result","_seek_result") if name=="reset" else ("count","_read_count")
        node=copy.deepcopy(original);assignments=pointers=0
        expected=ast.parse(variable+" = "+("ctypes.c_longlong()" if name=="reset" else "w.DWORD()")).body[0]
        pointer=ast.parse("ctypes.byref("+variable+")",mode="eval").body
        class Change(ast.NodeTransformer):
            def visit_Assign(self,n):
                nonlocal assignments
                if ast.dump(n,include_attributes=False)==ast.dump(expected,include_attributes=False):
                    assignments+=1
                    alias=ast.parse(variable+" = self."+field).body[0]
                    alias._scratch_original=copy.deepcopy(n)
                    reset=ast.parse(variable+".value = 0").body[0];reset._scratch_added=True
                    return [alias,reset]
                return self.generic_visit(n)
            def visit_Call(self,n):
                nonlocal pointers
                if ast.dump(n,include_attributes=False)==ast.dump(pointer,include_attributes=False):
                    pointers+=1
                    replacement=ast.parse("self."+field+"_pointer",mode="eval").body
                    replacement._scratch_original=copy.deepcopy(n)
                    return replacement
                return self.generic_visit(n)
        changed=Change().visit(node)
        require(assignments==1 and pointers==1,"ONE_SCRATCH_ALLOCATION_AND_POINTER_ONLY")
        class Undo(ast.NodeTransformer):
            def visit(self,n):
                if getattr(n,"_scratch_added",False):return None
                if hasattr(n,"_scratch_original"):return copy.deepcopy(n._scratch_original)
                return super().visit(n)
        require(ast.dump(Undo().visit(copy.deepcopy(changed)),include_attributes=False)==
                ast.dump(original,include_attributes=False),"ALL_ORIGINAL_STATEMENTS_RESTORED")
        env=dict(vars(prior))
        exec(compile(ast.fix_missing_locations(ast.Module(body=[changed],type_ignores=[])),
             ORIGINAL_PIN["path"],"exec"),env)
        output[name]=env[name]
        proof[name]=dict(original_AST_restored_exactly=True,per_call_scratch_allocations_moved=1,
                        per_call_pointer_wrappers_moved=1,zero_reset_before_each_OS_call=True,
                        original_guard_error_identity_and_fresh_buffer_statements_removed=0)
    return output,proof

def native_read_type(raw):
    bodies,proof=project(raw)
    class NativeRead(prior.NativeRead):
        def __init__(self,native):
            super().__init__(native)
            self._owner=threading.get_ident();self._busy=False
            self._read_count=w.DWORD();self._read_count_pointer=ctypes.byref(self._read_count)
            self._seek_result=ctypes.c_longlong();self._seek_result_pointer=ctypes.byref(self._seek_result)
        def _enter(self):
            require(threading.get_ident()==self._owner,"SERIAL_ORIGINAL_OWNER")
            require(not self._busy,"NO_REENTRANT_SCRATCH")
            self._busy=True
        def reset(self,handle):
            self._enter()
            try:return bodies["reset"](self,handle)
            finally:self._busy=False
        def readinto(self,handle,buffer):
            self._enter()
            try:return bodies["readinto"](self,handle,buffer)
            finally:self._busy=False
    return NativeRead,dict(original_methods=proof,count_and_seek_scratch_allocations_per_API=2,
     pointer_wrappers_per_API=2,fresh_buffer_binding_before_each_ReadFile=True,
     original_API_constructor_and_ReadFile_SetFilePointerEx_calls_retained=True,
     original_chunk_ceiling=prior.CHUNK_BYTES,byte_hash_JSON_identity_cache=False,
     new_sampler_thread_or_process=False,original_native_source_oracle_weakened=False,
     current149_runtime_connection=False,PC_freeze_resolved=False)
