"""Explicit current805 report roles using the entire original report producer.

This is a self-free input declaration, not live Frame/source freshness credit.
The original producer64, failed Native010, package, canonical validator and
publication/cleanup code remain. No observed-import union or product authority.
"""
import hashlib
import sys
from types import SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_report.py'
TEST='tools/p09/tests/test_native011_current_epoch_report.py'
SOURCE=dict(path='tools/p09/native011_metadata_report.py',bytes=8345,
    sha256='a6a81b629a4bc9493a48db805b5e8072af9f6dd69ce6f43723d117f88bba8250')
MODULES=('native011_current_epoch_scope','native011_current_epoch_binding',
    'native011_current_cohort_listing','native011_current_epoch_plan',
    'native011_current_epoch_plan_inspection','native011_current_epoch_worker_scope',
    'native011_current_epoch_graph','native011_current_epoch_metadata',
    'native011_current_epoch_inventory_budget','native011_current_epoch_parent')
CODE=(SELF,TEST)+tuple('tools/p09/'+name+'.py' for name in MODULES)
DATA=(
    dict(path='implementation/p09/evidence/p09-361-native011-current-cohort-build002.v1.json',
        bytes=167281,sha256='7e4aeb5ace1b81b36e6aa5b246c4b10171ec7446f6eef9f32edad68fe9ccba8d'),
    dict(path='implementation/p09/evidence/p09-361-native011-current-cohort-listing001.v1.json',
        bytes=61233,sha256='6a7ef761910e267cfde57e7b2237104f9d28e588b8400cb4f1ca3d6b1adef633'),
    dict(path='implementation/p09/evidence/p09-361-native011-prior-source-preimages001.v1.json',
        bytes=92704,sha256='8bce0d752f5ff8a8f788a2cae6b79d92800e64052aeaeaeb5a1800fcb2f321a6'))
ROLES=tuple((path,'current805_report_control_source') for path in CODE)+tuple(
    (pin['path'],'fixed_current805_cohort_provenance_not_fresh805_bytes') for pin in DATA)


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_METADATA_REPORT_'+code)


def connect(raw):
    require(type(raw) is bytes and len(raw)==SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest()==SOURCE['sha256'],'EXACT_ENTIRE_ORIGINAL_PRODUCER_SOURCE')
    names=tuple(path for path,_ in ROLES)
    require(len(names)==len(set(names)) and len(names)==15,'CLOSED_FIFTEEN_NAMED_ROLES')
    # Compile the whole original source, including every original main/cleanup
    # and validator statement, in a new namespace; never mutate its module.
    env=dict(__name__='p09_current805_metadata_report_private',__file__=SOURCE['path'])
    exec(compile(raw,SOURCE['path'],'exec'),env)
    old_extra=env['EXTRA_CODE'];original_compose=env['compose']
    require(not set(names)&set(old_extra),'NEW_ROLES_DISJOINT_FROM_ORIGINAL_CONTROLS')
    env['EXTRA_CODE']=old_extra+names
    def compose(base,sources,scope,generation):
        require(type(generation) is int and generation==3,'ONLY_NEW_GENERATION003')
        require(all(sources.get(pin['path'])==pin for pin in DATA),
            'EXACT_NEW_BUILD_LIST_AND_PREIMAGE_PROVENANCE')
        return original_compose(base,sources,scope,generation)
    env['compose']=compose
    proof=dict(original_producer_source_pin=dict(SOURCE),named_current805_roles=[
        dict(path=path,role=role) for path,role in ROLES],
        original_extra_controls_retained=len(old_extra),original_compose_body_retained=True,
        entire_original_main_and_validator_code_retained=True,
        original_default_module_mutated=False,observed_input_union=False,
        whole805_or_live_Frame_or_runtime_qualified=False,GO_authorized=False)
    return NS(**env),proof


def main():
    from pathlib import Path
    require(sys.argv[1:]==['--generation','3'],'CLOSED_NEW_REPORT_ARGUMENTS')
    root=Path(__file__).resolve().parents[2]
    api,_=connect((root/SOURCE['path']).read_bytes())
    return api.main()


if __name__=='__main__':raise SystemExit(main())
