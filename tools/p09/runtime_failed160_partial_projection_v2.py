"""Keep role v1 immutable; project attribute names as well as constants."""
from types import FunctionType
import runtime_failed160_partial_projection_v1 as previous

SELF="tools/p09/runtime_failed160_partial_projection_v2.py"
TEST="tools/p09/tests/test_runtime_failed160_partial_projection_v2.py"
ROOT=previous.ROOT
REVIEW=previous.REVIEW
PHYSICAL=previous.PHYSICAL
ROLE=previous.ROLE
ADMISSION_SCHEMA=previous.ADMISSION_SCHEMA
CODE=previous.CODE
MAPPING=previous.MAPPING
original=previous.original
attempt=previous.attempt
declaration=previous.declaration
admission=previous.admission


def project(code,mapping):
    revised=previous.project(code,mapping)
    return revised.replace(co_names=tuple(mapping.get(name,name) for name in code.co_names),
        co_consts=tuple(project(x,mapping) if isinstance(x,type(code)) else x for x in revised.co_consts))


def connect(source,binding,admitted):
    fn=previous.connect
    execute=FunctionType(fn.__code__,dict(fn.__globals__,project=project),
        argdefs=fn.__defaults__,closure=fn.__closure__)
    execute.__kwdefaults__=fn.__kwdefaults__
    proof=execute(source,binding,admitted)
    expected=declaration()
    provenance=dict(source.failed160_partial_receipt_extension)
    provenance["failed_runtime_pin"]=dict(provenance["failed_runtime_pin"])
    provenance["independent_review_pin"]=dict(provenance["independent_review_pin"])
    binding.exact(provenance,expected,"ACTUAL_PARTIAL160_ATTRIBUTE_PROVENANCE")
    return dict(proof,original_attribute_and_constant_metadata_inverse_code_equal=True,
        actual_partial160_attribute_not_old_failed004_name=True)
