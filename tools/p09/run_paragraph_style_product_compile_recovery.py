"""Repair only the independent test numeric oracle; all product/source inputs stay exact."""
import run_paragraph_style_product_components as base

FAILED='implementation/p09/evidence/p09-361-paragraph-style-product-count-recovery145.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-paragraph-style-product-compile-recovery146.v1.json'
ORIGINAL_INVERSE=base.inverse
HELPER='''fn reference_number(raw:&str)->Result<u32,Box<dyn Error>> {
    // Read unsigned XML reference values independently without a new crate dependency.
    let mut decoded=String::new();let mut tail=raw;
    while let Some(start)=tail.find('&') {
        decoded.push_str(&tail[..start]);let entity=&tail[start+1..];let end=entity.find(';').ok_or("unterminated numeric reference")?;
        let token=&entity[..end];let scalar=if let Some(hex)=token.strip_prefix("#x"){u32::from_str_radix(hex,16)?}
            else if let Some(decimal)=token.strip_prefix('#'){decimal.parse::<u32>()?}else{return Err("non-numeric reference".into())};
        decoded.push(char::from_u32(scalar).ok_or("invalid numeric scalar")?);tail=&entity[end+1..];
    }
    decoded.push_str(tail);Ok(decoded.parse()?)
}
'''
OLD='''            .map(|a|quick_xml::escape::unescape(&raw[a.value_span().start()..a.value_span().end()]).map(|s|s.parse::<u32>())).transpose()?.transpose()?)};
'''
NEW='''            .map(|a|reference_number(&raw[a.value_span().start()..a.value_span().end()])).transpose()?)};
'''
ORACLE='''    assert_eq!(reference_number("&#48;")?,0);assert_eq!(reference_number("&#x31;2")?,12);assert!(reference_number("&amp;").is_err());assert!(reference_number("&#x110000;").is_err());
'''


def inverse(q,old):
    failed=q.json(FAILED)
    base.c.require(q.snapshots[FAILED]['sha256']=='0d40b60047d1d573a67cd853400db117fe7e22796590f2237c33a974c4bdbe81'
        and failed['state']=='FAILED_PARAGRAPH_PRODUCT_COMPONENTS' and failed['cleanup'] and len(failed['steps'])==1,
        'EXACT_FAILED145_COMPILE_RESULT_PRESERVED')
    step=failed['steps'][0];observation=step['bounded_output_observation']
    base.c.require(step['exit_code']==101 and step['tests']==[] and step['cleanup']
        and observation['rust_error_codes']==['E0433']
        and observation['short_error_locations']==[['crates/product-cli/tests/regex_replacement_product/../form_stored_provider/actual_import/paragraph_style_product.rs','26','21']]
        and step['owned_job']['owned_tree_empty'] and step['owned_job']['job_handle_closed'],
        'NO_PRODUCT_TEST_STARTED_ONE_UNRESOLVED_TEST_DEPENDENCY_AND_TERMINAL_JOB')
    pins={p['path']:p for p in failed['source_pins']}
    for name,pin in pins.items():
        q.pin(name)
        if name!=base.TEST:
            base.c.require(q.snapshots[name]==pin,'ALL_FAILED145_PRODUCT_SOURCE_CARGO_AND_HELPER_INPUTS_UNCHANGED')
    text=q.text(base.TEST)
    for marker in(HELPER,NEW,ORACLE):base.c.require(text.count(marker)==1,'EXACT_NUMERIC_TEST_ORACLE_REPAIR_WITH_OWN_CHECKS')
    base.audit.inverse(text.replace(HELPER,'').replace(NEW,OLD).replace(ORACLE,''),pins[base.TEST],
        'WHOLE_TWENTY_ONE_TEST_BODIES_UNCHANGED_EXCEPT_INDEPENDENT_NUMERIC_ORACLE')
    ORIGINAL_INVERSE(q,old)


if __name__=='__main__':
    base.OUTPUT=OUTPUT
    base.inverse=inverse
    raise SystemExit(base.main())
