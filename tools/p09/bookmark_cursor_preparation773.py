"""Existing Native initial/reopened pairs for a NEW direct bookmark cursor query."""
from bookmark_native_preparation629 import loaded_dependencies,require_absent,inspection,runtime,inspect_current
import prepared_bookmark690_receipt as codec
PREPARED='implementation/p09/evidence/p09-361-bookmark-cursor773-prepared.v1.json'
PROOF='implementation/p09/evidence/p09-361-renamed-bookmark766-product001.v1.json'
INPUTS='implementation/p09/evidence/p09-361-renamed-bookmark764-inputs.v1.json'
NATIVE='implementation/p09/evidence/p09-361-prepared-bookmark761-native001.v1.json'
SOURCE_PIN=dict(path='implementation/p09/evidence/private/p09-361-block-bookmark681-prepared001/source.hwpx',bytes=64944,sha256='f6d7315048f5d460aa280761c7653656dd0560b64c4e30f90d751b51f0bdcaa1')

def require(ok,code):
    if not ok:raise ValueError('XREF_CURSOR773_'+code)

def validate_prepared(reader):
    value=reader.json(PREPARED);proof=codec.unpack(reader.json(PROOF),reader.checkpoint);inputs=reader.json(INPUTS)
    require(reader.snapshots[PROOF]['sha256']=='dbd47a12db46bbdbedd21f0c4bd99a33acd9341d36ecf9dacb6c3215b0862a7f'
        and proof['state']=='QUALIFIED766_RENAMED_NATIVE24_PRODUCT32_SAVED_EXTENT_AND24_PIXELS_NOT_NATIVE_CURSOR_OR_P09'
        and proof['cleanup']is True and proof['fresh_inputs']==proof['final_fresh_hashes']==1049
        and proof['artifact_final_fresh_hashes']==2 and proof['all_eight_visible_three_role_pixel_groups_equal']is True
        and proof['Native_started']is False,'CURRENT_PRODUCT766_NOT_PREVIOUS_CURSOR')
    original={p['path']:p for p in proof['source_pins']}
    require(reader.snapshots[INPUTS]==original[INPUTS],'EXACT_PRODUCT_INPUT_MANIFEST')
    require(value['schema']=='hwpx-agent.private.bookmark-cursor773-prepared/v1'
        and value['state']=='EIGHT_PAIRS_EXISTING_NATIVE_FILES_FOR_DIRECT_BOOKMARK_CURSOR_NOT_LINK_ACTIVATION'
        and value['source']==SOURCE_PIN and reader.pin(SOURCE_PIN['path'])==SOURCE_PIN
        and value['product_receipt']==PROOF and value['native_execution_authorized']is False and value['P09_complete']is False
        and value['SaveAs_invoked']is False and value['hyperlink_activation_qualified']is False,'EXACT_NEW_PURPOSE')
    require(reader.pin(NATIVE)==value['native_receipt']==inputs['native_capture']
        and value['native_receipt']['sha256']=='ce781b13e006970ccc9fb9bdebe137c3699e679fd4e1c52f117208942aa2e63b','CONSUMED761_ONLY_AS_SOURCE')
    require(value['target_name_sha256']==inputs['target_name_sha256']and value['target_content_sha256']==inputs['target_content_sha256'],'EXACT_SOURCE_TARGET_HASHES')
    expected=[dict(case_index=c['case_index'],display=c['display'],hyperlink=c['hyperlink'],output=c['stages']['initial']['pin'],reopened=c['stages']['reopened']['pin'])for c in inputs['cases']]
    require(value['cases']==expected and len(expected)==8 and len(proof['product']['observations'])==32,'EIGHT_PAIRS_NO_PARTIAL')
    for index,case in enumerate(expected,1):
        require(type(case['case_index'])is int and case['case_index']==index and type(case['hyperlink'])is bool and case['hyperlink']is(index%2==0),'ORDER_AND_MODE')
        for label,pin in(('initial',case['output']),('reopened',case['reopened'])):
            require(pin['path']==f'implementation/p09/evidence/private/p09-361-prepared-bookmark755-native001-c{index:02}/'+label+'.hwpx'
                and reader.pin(pin['path'])==pin,'EXACT_EXISTING_FILE')
    return value
