"""Remove only exact-identity duplicate metadata guard callback.
Every original statement is restored by an independent AST undo check.
Distinct callbacks retain original code path; CPU warning/latch/cleanup unchanged.
This is not a claim that host saturation or Defender causality is resolved.
"""
import ast,copy
from types import FunctionType

SELF="tools/p09/metadata_guard_identity_dedup_v1.py"
TEST="tools/p09/tests/test_metadata_guard_identity_dedup_v1.py"
ORIGINAL="tools/p09/metadata_pressure_failfast.py"

def require(ok,code):
    if not ok:raise ValueError("METADATA_GUARD_IDENTITY_"+code)

def checkpoint_type(original,raw):
    require(type(raw) is bytes,"EXACT_SOURCE_BYTES_REQUIRED")
    call=original.__call__
    require(type(call) is FunctionType and call.__name__=="__call__" and call.__closure__ is None,
      "ORIGINAL_UNCLOSED_CHECKPOINT_METHOD")
    tree=ast.parse(raw.decode("utf-8"))
    classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="Checkpoint"]
    require(len(classes)==1,"ONE_ORIGINAL_CHECKPOINT")
    methods=[n for n in classes[0].body if isinstance(n,ast.FunctionDef) and n.name=="__call__"]
    require(len(methods)==1,"ONE_ORIGINAL_CALL")
    node=copy.deepcopy(methods[0]);before=ast.dump(node,include_attributes=False);changes=[]
    target=ast.dump(ast.parse("self.original()").body[0],include_attributes=False)
    class Project(ast.NodeTransformer):
        def visit_Expr(self,n):
            if ast.dump(n,include_attributes=False)==target:
                replacement=ast.parse("if self.original is self.hard:\n self.identity_duplicates_avoided += 1\nelse:\n self.original()").body[0]
                replacement._original_duplicate=copy.deepcopy(n);changes.append(1)
                return ast.copy_location(replacement,n)
            return self.generic_visit(n)
    node=Project().visit(node);require(len(changes)==1,"ONLY_ONE_DUPLICATE_CALL")
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,"_original_duplicate"):return copy.deepcopy(n._original_duplicate)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,
      "ALL_ORIGINAL_STATEMENTS_RESTORED")
    # Compile source text through the SAME Python source compiler, not a
    # selected AST (which can use a different optimized control-flow layout).
    # Extract code objects only: never execute module imports or a CLI.
    def method_code(source):
        module=compile(source,call.__code__.co_filename,"exec",dont_inherit=True)
        bodies=[x for x in module.co_consts if type(x) is type(call.__code__) and x.co_name=="Checkpoint"]
        require(len(bodies)==1,"ONE_COMPILED_CLASS_BODY")
        methods=[x for x in bodies[0].co_consts if type(x) is type(call.__code__) and x.co_name=="__call__"]
        require(len(methods)==1,"ONE_COMPILED_METHOD")
        return methods[0]
    require(method_code(raw)==call.__code__,"EXACT_ORIGINAL_METHOD_CODE")
    leaves=[n for n in ast.walk(methods[0]) if isinstance(n,ast.Expr)
      and ast.dump(n,include_attributes=False)==target]
    require(len(leaves)==1 and leaves[0].lineno==leaves[0].end_lineno,"ONE_SOURCE_LINE_CALL")
    lines=raw.decode("utf-8").splitlines(keepends=True);leaf=leaves[0];line=lines[leaf.lineno-1]
    require(line.strip()=="self.original()" and line[:leaf.col_offset].strip()=="","EXACT_SOURCE_LINE")
    indent=line[:leaf.col_offset]
    replacement=(indent+"if self.original is self.hard:\n"+indent+"    self.identity_duplicates_avoided += 1\n"
      +indent+"else:\n"+indent+"    self.original()\n")
    projected="".join(lines[:leaf.lineno-1])+replacement+"".join(lines[leaf.lineno:])
    expected=copy.deepcopy(tree)
    expected_class=next(n for n in expected.body if isinstance(n,ast.ClassDef) and n.name=="Checkpoint")
    expected_class.body=[node if isinstance(n,ast.FunctionDef) and n.name=="__call__" else n for n in expected_class.body]
    require(ast.dump(ast.parse(projected),include_attributes=False)==ast.dump(expected,include_attributes=False),
      "SOURCE_REWRITE_EQUALS_SINGLE_PROJECTED_AST")
    revised=FunctionType(method_code(projected),dict(call.__globals__),argdefs=call.__defaults__)
    require(revised.__defaults__==call.__defaults__ and revised.__closure__ is None,"ORIGINAL_DEFAULTS_AND_CLOSURE")
    class Checkpoint(original):
        __call__=revised
        def __init__(self,*args,**kwargs):
            self.identity_duplicates_avoided=0
            super().__init__(*args,**kwargs)
        def summary(self):
            row=original.summary(self)
            row["identity_duplicate_guard"]=dict(source=SELF,
              original_callback_is_hard=self.original is self.hard,
              calls_avoided=self.identity_duplicates_avoided,
              original_hard_guard_called_first=True,distinct_callback_path_unchanged=True,
              original_warning_latch_validation_and_restore_retained=True,
              source_reads_rates_deadlines_or_guards_weakened=False,
              added_sampler_thread_or_native_query=False,PC_freeze_resolved=False)
            return row
    return Checkpoint,dict(exact_original_method_code_and_AST_verified=True,
      one_identity_conditional_duplicate_call_change=1,
      all_original_statements_restored_by_independent_undo=True,
      identical_guard_called_once_first_before_warning_decision=True,
      distinct_callbacks_keep_both_original_calls=True,
      original_warning_latch_error_precedence_and_restore_retained=True,
      scope_byte_reads_rates_deadlines_and_sampling_policy_not_relaxed=True,
      extra_observer_or_native_queries=False,PC_freeze_resolved=False)
