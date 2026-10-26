"""Six preserved captures are historical evidence, never a new Native permit."""
import run_prepared_bookmark_native631 as p
PROOF='implementation/p09/evidence/p09-361-prepared-bookmark688-retained-six001.v1.json'
SHA='013282e1b1fe21a06744b094f7a30a826ecaba0436279021ffeffa7109f5a836'

def validate(reader):
    value=p.codec.unpack(reader.json(PROOF),reader.checkpoint)
    require=p.r.c.require
    require(reader.snapshots[PROOF]['sha256']==SHA and value['state']=='QUALIFIED688_SIX_CLOSED684_CAPTURES_RETAINED_SEVENTH_PARTIAL_NOT_PROMOTED'
        and value['cleanup']is True and value['fresh_inputs']==value['final_fresh_hashes']==1016
        and value['Native_started']is False,'XREF_RETAIN690_EXACT688_PROOF')
    retained=value['retained']
    require(retained['retained_case_count']==6 and len(retained['cases'])==6 and retained['original_failed684_reclassified']is False
        and retained['reference_display_or_navigation_semantics_qualified']is False,'XREF_RETAIN690_SIX_CAPTURES_NOT_SEMANTIC_PASS')
    for pin in value['source_pins']:
        observed=reader.snapshots.get(pin['path'])
        if observed is None:observed=reader.pin(pin['path'])
        require(observed==pin,'XREF_RETAIN690_PRESERVED_CURRENT_INPUTS')
    require([case['source_case_index']for case in retained['cases']]==list(range(1,7)),'XREF_RETAIN690_EXACT_SIX_ORDINALS')
    return retained
