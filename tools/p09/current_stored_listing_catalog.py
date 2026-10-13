"""Load ONLY the original pure stored249 parser functions from audited text.

기존 runner를 import/실행하지 않는다. 실제 reader가 원 파일 exact pin을 확인한 뒤
같은 module/path/ignore/249/list-output 규칙을 원 함수 본문 그대로 결합한다.
"""
import ast
import re
from types import SimpleNamespace

SELF="tools/p09/current_stored_listing_catalog.py"
TEST="tools/p09/tests/test_current_stored_listing_catalog.py"
PARSER_PIN=dict(path="tools/p09/run_stored_comment_regression.py",bytes=36834,
    sha256="2521519520da9a07aa368952a14586d78f287a46f7d3569e3de379669a476ed2")
ROOT="crates/product-cli/tests/form_stored_provider.rs"
TASK="stored-form-tests"
COUNT=249
MODULES=59
SELECTED=("case_task","module_path","recursive_names","validate_listing")


def require(ok,code):
    if not ok:raise ValueError("CURRENT_STORED_CATALOG_"+code)


class Catalog:
    def __init__(self,audited_source):
        require(type(audited_source) is str and len(audited_source.encode("utf-8"))<=128*1024,"PARSER_TEXT_LIMIT")
        tree=ast.parse(audited_source,filename=PARSER_PIN["path"])
        functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in SELECTED]
        require(len(functions)==len(SELECTED) and {node.name for node in functions}==set(SELECTED),"EXACT_PARSER_FUNCTIONS")
        for function in functions:
            require(not function.decorator_list and function.returns is None,"PARSER_FUNCTION_SHAPE")
            require(not any(isinstance(node,(ast.Import,ast.ImportFrom)) for node in ast.walk(function)),"PARSER_IMPORT_FORBIDDEN")
            require(not any(isinstance(node,ast.Call) and isinstance(node.func,ast.Name)
                and node.func.id in {"eval","exec","__import__","open"} for node in ast.walk(function)),
                "PARSER_DYNAMIC_EXECUTION_FORBIDDEN")
        namespace=dict(re=re,maintenance=SimpleNamespace(require=require),bounded=SimpleNamespace(LIMIT=32768),
            CASES={TASK:([],{ROOT:""},COUNT)},LIST_TASKS={"stored-form-list":TASK},TASK=TASK,
            MODULE_LIMIT=100,DEPTH_LIMIT=16)
        # Only hash-admitted local function definitions, no top-level imports or runner body.
        exec(compile(ast.Module(body=functions,type_ignores=[]),PARSER_PIN["path"],"exec"),namespace)
        self.namespace=namespace
    def names(self,read_text):
        names,modules=self.namespace["recursive_names"](read_text,TASK)
        require(len(modules)==MODULES,"ALL_MODULE_INSTANCES")
        return names,modules
    def validate(self,output,names):
        self.namespace["validate_listing"](output,names,TASK)
        return True
