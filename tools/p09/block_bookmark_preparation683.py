"""Exactly eight current block-product files; no saved Native admission."""
from bookmark_native_preparation629 import loaded_dependencies,require_absent,inspection,runtime,inspect_current
PREPARED='implementation/p09/evidence/p09-361-block-bookmark681-prepared-batch.v1.json'
PROOF='implementation/p09/evidence/p09-361-block-bookmark681-recovery683.v1.json'
MANIFEST_SHA='bec2b5d3a244c5e7975a5b1c904d8f5ea631bf9e3679f57ea70fac474500fb13'
DIRECTORY='implementation/p09/evidence/private/p09-361-block-bookmark681-prepared001'
DISPLAYS=('page','bookmark_name','content','relative_position')
SOURCE_PIN=dict(path=DIRECTORY+'/source.hwpx',bytes=64944,sha256='f6d7315048f5d460aa280761c7653656dd0560b64c4e30f90d751b51f0bdcaa1')

def require(ok,code):
    if not ok:raise ValueError('XREF_BLOCK683_'+code)

def validate_prepared(reader,unpack):
    value=reader.json(PREPARED);proof=unpack(reader.json(PROOF))
    require(reader.snapshots[PREPARED]['sha256']==MANIFEST_SHA and reader.snapshots[PREPARED]['bytes']<16384
        and value['schema']=='hwpx-agent.private.block-bookmark681-prepared-batch/v1'
        and value['state']=='EIGHT_BLOCK_PRODUCT_CANDIDATES_NOT_NATIVE_OR_AUTHORITY'and value['source_receipt']==PROOF
        and value['native_execution_authorized']is False and value['P09_complete']is False,'EXACT_CURRENT_PREPARED_MANIFEST')
    require(proof['state']=='QUALIFIED683_EXISTING_EIGHT_BLOCK_CANDIDATES_NO_BUILD_GENERATOR_OR_NATIVE_RERUN'
        and proof['cleanup']is True and proof['fresh_inputs']==proof['final_fresh_hashes']>0
        and proof['outputs_final_fresh_hashes']==9 and proof['compiled_final_fresh_hashes']==2
        and proof['generator_build_or_Native_rerun']is False and proof['original682_failure_reclassified']is False
        and proof['prepared_manifest']==reader.snapshots[PREPARED],'EXACT_PRODUCT_GENERATION_AND_RECOVERY_PROOF')
    require(value['source']==proof['source']==SOURCE_PIN and reader.pin(SOURCE_PIN['path'])==SOURCE_PIN
        and type(value['cases'])is list and value['cases']==proof['cases']and len(value['cases'])==8,'WHOLE_SOURCE_AND_EIGHT')
    for index,case in enumerate(value['cases'],1):
        require(type(case['case_index'])is int and case['case_index']==index and case['display']==DISPLAYS[(index-1)//2]
            and type(case['hyperlink'])is bool and case['hyperlink']is(index%2==0)
            and case['output']['path']==DIRECTORY+f'/case-{index:02}.hwpx'
            and type(case['output']['bytes'])is int and 0<case['output']['bytes']<=4194304
            and reader.pin(case['output']['path'])==case['output'],'EXACT_CURRENT_FIXED_PRODUCT_CASE')
    return value
