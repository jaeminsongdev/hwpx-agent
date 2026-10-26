"""Eight immutable renamed candidates from current product proof; no Native grant."""
from bookmark_native_preparation629 import loaded_dependencies,require_absent,inspection,runtime,inspect_current
PREPARED='implementation/p09/evidence/p09-361-renamed-bookmark755-prepared-batch.v1.json'
PROOF='implementation/p09/evidence/p09-361-block-bookmark-meaning754-product003.v1.json'
PINS='implementation/p09/evidence/p09-361-bookmark-navigation743-inputs.v1.json'
ORIGINAL='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
DIRECTORY='implementation/p09/evidence/private/p09-361-bookmark-rename740-generated001'
DISPLAYS=('page','bookmark_name','content','relative_position')
SOURCE_PIN=dict(path='implementation/p09/evidence/private/p09-361-block-bookmark681-prepared001/source.hwpx',bytes=64944,
    sha256='f6d7315048f5d460aa280761c7653656dd0560b64c4e30f90d751b51f0bdcaa1')

def require(ok,code):
    if not ok:raise ValueError('XREF_RENAMED755_'+code)

def validate_prepared(reader,unpack):
    value=reader.json(PREPARED);proof=unpack(reader.json(PROOF));pins=reader.json(PINS);original=reader.json(ORIGINAL)
    require(reader.snapshots[PROOF]['sha256']=='0ce3ccfad2bf535ea0050700ddd6899edf89193a9c1d64c65ead8e04d3e227fb'
        and proof['state']=='QUALIFIED754_COMMON_BLOCK_BOOKMARK_MEANING_RETAINED13_CLEAN_BUILD_EXISTING40_STILL_INCOMPLETE_NOT_NATIVE_OR_F11'
        and proof['cleanup']is True and proof['fresh_inputs']==proof['final_fresh_hashes']==1300
        and proof['artifact_final_fresh_hashes']==4 and proof['Native_started']is False,'EXACT_CURRENT_PRODUCT_BOUNDARY')
    require(value['schema']=='hwpx-agent.private.renamed-bookmark755-prepared-batch/v1'
        and value['state']=='EIGHT_RENAMED_PRODUCT_CANDIDATES_NOT_NATIVE_OR_AUTHORITY'
        and value['source_receipt']==PROOF and value['native_execution_authorized']is False and value['P09_complete']is False
        and value['source']==SOURCE_PIN==original['source']and reader.pin(SOURCE_PIN['path'])==SOURCE_PIN,'EXACT_MANIFEST_AND_ORIGINAL')
    expected=[dict(case_index=c['case_index'],display=c['display'],hyperlink=c['hyperlink'],output=p['renamed'])
        for c,p in zip(original['cases'],pins['cases'],strict=True)]
    require(value['cases']==expected and len(expected)==8,'EXACT_EIGHT_RENAMED_CASES')
    observed=[v for v in proof['product']['observations']if v['stage']=='renamed']
    require(len(observed)==8,'CURRENT_PRODUCT_RENAMED8')
    for index,(case,seen)in enumerate(zip(expected,observed,strict=True),1):
        require(type(case['case_index'])is int and case['case_index']==index and case['display']==DISPLAYS[(index-1)//2]
            and type(case['hyperlink'])is bool and case['hyperlink']is(index%2==0)
            and case['output']['path']==DIRECTORY+f'/case-{index:02}.hwpx'
            and seen['case_index']==index and seen['source']==case['output']and seen['source_unchanged']is True
            and type(case['output']['bytes'])is int and 0<case['output']['bytes']<=4194304
            and reader.pin(case['output']['path'])==case['output'],'EXACT_CURRENT_SOURCE_FILE_AND_MODE')
    return value
