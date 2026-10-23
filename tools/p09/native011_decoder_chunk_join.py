"""Candidate output storage only; original wire decoder stays immutable.

All original checks, per-output64KiB calls, hashes, guard positions and error
paths stay. Fresh immutable output chunks are joined once instead of growing
a bytearray repeatedly. No decoded byte/hash/JSON cache or budget change.
"""
import ast
import copy
import hashlib
from types import SimpleNamespace as NS

SELF='tools/p09/native011_decoder_chunk_join.py'
TEST='tools/p09/tests/test_native011_decoder_chunk_join.py'
SOURCE=dict(path='tools/p09/runtime_record_envelope_v2.py',bytes=2891,
    sha256='9a97c8c9c9a6281992430bfc224bbfea036da6d780389ac2777fbb403d62960f')


def require(ok,code):
    if not ok:raise ValueError('DECODER_CHUNK_JOIN_'+code)


def connect(raw,original):
    require(type(raw) is bytes and len(raw)==SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest()==SOURCE['sha256'],'EXACT_ENTIRE_ORIGINAL_DECODER_SOURCE')
    require(original.CHUNK_BYTES==65536 and original.MAX_BYTES==16777216,'ORIGINAL_WORK_AND_SIZE_LIMITS')
    original_node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='decode')
    node=copy.deepcopy(original_node);changes=[]
    def equal(n,text):return ast.dump(n,include_attributes=False)==ast.dump(ast.parse(text).body[0],include_attributes=False)
    class Change(ast.NodeTransformer):
        def visit_Assign(self,n):
            if equal(n,'result=bytearray()'):
                after=ast.parse('result=[]').body[0];after._join_before=copy.deepcopy(n)
                counter=ast.parse('_filled=0').body[0];counter._join_added=True
                changes.append('storage');return [after,counter]
            return self.generic_visit(n)
        def visit_While(self,n):
            class Length(ast.NodeTransformer):
                def visit_Call(self,call):
                    if ast.dump(call,include_attributes=False)==ast.dump(ast.parse('len(result)',mode='eval').body,include_attributes=False):
                        after=ast.Name(id='_filled',ctx=ast.Load());after._join_before=copy.deepcopy(call)
                        changes.append('length');return after
                    return self.generic_visit(call)
            return self.generic_visit(Length().visit(n))
        def visit_Expr(self,n):
            if equal(n,'result.extend(chunk)'):
                after=ast.parse('result.append(chunk)').body[0];after._join_before=copy.deepcopy(n)
                count=ast.parse('_filled+=len(chunk)').body[0];count._join_added=True
                changes.append('append');return [after,count]
            if (isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='require'
                and len(n.value.args)>1 and isinstance(n.value.args[1],ast.Constant)
                and n.value.args[1].value=='EXACT_ORIGINAL_BYTES_AND_HASH'):
                join=ast.parse("result=b''.join(result)").body[0];join._join_added=True
                changes.append('join');return [join,n]
            return self.generic_visit(n)
    node=Change().visit(node)
    require(sorted(changes)==['append','join','length','length','storage'],'EXACT_OUTPUT_STORAGE_CHANGES_ONLY')
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,'_join_before'):return copy.deepcopy(n._join_before)
            if hasattr(n,'_join_added'):return None
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==ast.dump(original_node,include_attributes=False),
        'FULL_ORIGINAL_DECODER_AST_INVERSE')
    env=dict(vars(original))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),SOURCE['path'],'exec'),env)
    candidate=env['decode']
    return NS(**{**vars(original),'decode':candidate}),dict(
        exact_original_decoder_AST_inverse=True,output_storage_changes=5,
        expanded_output_per_original_call_maximum=65536,original_size_limit=16777216,
        original_guard_positions_hashes_and_all_rejections_retained=True,
        one_fresh_chunk_sequence_per_call=True,decoded_byte_hash_JSON_cache=False,
        decoder5_and_Native600_unchanged=True,default_codec_changed=False,
        installed_in_Runtime=False,actual_shared_budget_or_product_qualified=False)
