"""Preserve compile-only140; use the existing Properties iterator for the same exact PARA predicate."""
import run_paragraph_style_components as base
FAILED=base.OUTPUT
base.OUTPUT='implementation/p09/evidence/p09-361-paragraph-style-recovery141.v1.json'
OLD='matches!(d.native_attributes.get("type"),Some(PropertyValue::Text(kind))if kind=="PARA")'
NEW='d.native_attributes.iter().any(|(key,value)|key=="type"&&matches!(value,PropertyValue::Text(kind)if kind=="PARA"))'
base.BUILD_MAPS=base.BUILD_MAPS.replace(OLD,NEW)
original_inverse=base.inverse


def inverse(q,old):
    original_inverse(q,old);failed=q.json(FAILED)
    base.c.require(q.snapshots[FAILED]['sha256']=='c363bd9fec2e2bc61ad8a89f5cde00b0fdc2c752399162a6e352a3685721f2ee'
        and failed['state']=='FAILED_PARAGRAPH_STYLE_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1
        and failed['steps'][0]['tests']==[]and failed['steps'][0]['exit_code']==101
        and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0599'],
        'EXACT_COMPILE_ONLY_PROPERTIES_LOOKUP_FAILURE_NO_EXECUTED_TESTS')
    pins={p['path']:p for p in failed['source_pins']}
    for name in base.inventory(lambda:None)-{base.DEFS}:
        base.c.require(q.snapshots[name]==pins[name],'ALL_OTHER_PRODUCT_TEST_FIXTURE_AND_CORE_INPUTS_UNCHANGED_AFTER_COMPILE_FAILURE')
    text=q.text(base.DEFS);base.c.require(text.count(NEW)==1,'ONE_EXACT_PARA_GUARD_USING_EXISTING_PROPERTIES_ITERATOR')
    base.audit.inverse(text.replace(NEW,OLD),pins[base.DEFS],'WHOLE_NEW_PARAGRAPH_DEFINITION_BRIDGE_UNCHANGED_EXCEPT_SUPPORTED_LOOKUP')


base.inverse=inverse
if __name__=='__main__':raise SystemExit(base.main())
