"""Original complete memory qualification, explicit role7 metadata."""
import qualify_partial160_role_r354 as original
import runtime_failed160_partial_projection_v2 as role
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/qualify_partial160_role_v2_r355.py"
EXTRA=("tools/p09/runtime_failed160_partial_projection_v1.py",
    "tools/p09/tests/test_runtime_failed160_partial_projection_v1.py",original.SELF)
readers=[]
class Reader(original.a.AcceptanceReader):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for path in EXTRA:self.pin(path)
        readers.append(self)
def publish(row):
    if type(row) is str:row=original.json.loads(row)
    if row["state"].startswith("PASS_"):
        original.a.require(len(readers)==1,"ONE_ORIGINAL_ROLE_READER")
        row["source_pins"] += [dict(readers[0].snapshots[path]) for path in EXTRA]
        row["all_retained_v1_and_qualifier_test_sources_in_original_final_reader"]=True
    print(original.json.dumps(row,ensure_ascii=True,allow_nan=False))
fn=original.main;code=fn.__code__
changes={6:7,"test_runtime_failed160_partial_projection_v1.py":"test_runtime_failed160_partial_projection_v2.py",
    "PASS_PARTIAL160_FAILURE_ROLE_CODE6_TWO_MEMORY_DECODES_NOT_REAL_MANIFEST_NATIVE_OR_GO":
    "PASS_PARTIAL160_FAILURE_ROLE_CODE7_ATTRIBUTE_AND_TWO_MEMORY_DECODES_NOT_REAL_MANIFEST_NATIVE_OR_GO"}
revised=code.replace(co_consts=tuple(changes.get(x,x) if type(x) in (int,str) else x for x in code.co_consts))
reverse={v:k for k,v in changes.items()}
if revised.replace(co_consts=tuple(reverse.get(x,x) if type(x) in (int,str) else x for x in revised.co_consts))!=code:
    raise ValueError("ENTIRE_ORIGINAL_PARTIAL_ROLE_QUALIFIER_METADATA_INVERSE")
main=FunctionType(revised,dict(fn.__globals__,role=role,SELF=SELF,print=publish,
    a=NS(**{**vars(original.a),"AcceptanceReader":Reader})),
    argdefs=fn.__defaults__,closure=fn.__closure__)
main.__kwdefaults__=fn.__kwdefaults__
if __name__=="__main__":raise SystemExit(main())
