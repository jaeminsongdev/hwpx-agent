"""Preserve compile-only131 failure; only public XML attribute test helper is repaired."""
import run_text_style_components as base
FAILED=base.OUTPUT
base.OUTPUT='implementation/p09/evidence/p09-361-text-style-recovery132.v1.json'
original_inverse=base.inverse
OLD='''        Ok(node.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()==name).map(|a|a.semantic_value().parse()).transpose()?)};
'''
NEW='''        let Some(a)=node.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()==name)else{return Ok(None)};
        Ok(Some(quick_xml::escape::unescape(&raw[a.value_span().start()..a.value_span().end()])?.parse()?))};
'''


def inverse(q,old):
    original_inverse(q,old);failed=q.json(FAILED)
    base.c.require(q.snapshots[FAILED]['sha256']=='9fb8b0a3040111279b70b7c330464d226d74553ffeffafe19963790a3a72df55'
        and failed['state']=='FAILED_TEXT_STYLE_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1
        and failed['steps'][0]['tests']==[]and failed['steps'][0]['exit_code']==101
        and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0624'],
        'EXACT_COMPILE_ONLY_INTERNAL_ATTRIBUTE_HELPER_FAILURE_NO_EXECUTED_TESTS')
    pins={p['path']:p for p in failed['source_pins']}
    for name in base.inventory(lambda:None)-{base.TEST}:
        base.c.require(q.snapshots[name]==pins[name],'ALL_PRODUCTION_FIXTURES_AND_ORIGINAL_TEST_INPUTS_UNCHANGED_AFTER_COMPILE_FAILURE')
    text=q.text(base.TEST);base.c.require(text.count(NEW)==1,'ONE_PUBLIC_ATTRIBUTE_READBACK_HELPER_FIX')
    base.audit.inverse(text.replace(NEW,OLD),pins[base.TEST],'WHOLE_SIXTEEN_TEST_BODIES_UNCHANGED_EXCEPT_PUBLIC_XML_ATTRIBUTE_HELPER')


base.inverse=inverse
if __name__=='__main__':raise SystemExit(base.main())
