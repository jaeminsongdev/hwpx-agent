"""Preserve failed144 and every Rust input; correct only the runner's 20/21 count."""
import run_paragraph_style_product_components as base

FAILED=base.OUTPUT
OUTPUT='implementation/p09/evidence/p09-361-paragraph-style-product-count-recovery145.v1.json'
RUNNER='tools/p09/run_paragraph_style_product_components.py'
ORIGINAL_INVERSE=base.inverse
CHANGES=(
    ('"""21 additive paragraph-axis products only;', '"""20 additive paragraph-axis products only;'),
    ("len(names)==21,'EXACT_TWENTY_ONE_NEW_PARAGRAPH_PRODUCT_CASE_IDENTITIES'", "len(names)==20,'EXACT_TWENTY_NEW_PARAGRAPH_PRODUCT_CASE_IDENTITIES'"),
    ('new_cases=21,retained_products=83', 'new_cases=20,retained_products=83'),
    ("'twenty_one_new_paragraph_style_product_cases_only'", "'twenty_new_paragraph_style_product_cases_only'"),
    ("'PASS_PARAGRAPH_PRODUCT_TWENTY_ONE_NEW_NOT_FULL_STYLE_NATIVE_OR_GATE'", "'PASS_PARAGRAPH_PRODUCT_TWENTY_NEW_NOT_FULL_STYLE_NATIVE_OR_GATE'"),
    ('new_product_cases=21,total_executed_cases=21', 'new_product_cases=20,total_executed_cases=20'),
)


def inverse(q,old):
    failed=q.json(FAILED)
    base.c.require(q.snapshots[FAILED]['sha256']=='31ca429ecbfcc1d0b6c6626a49530458f0b3998786ce1e6173998fee7e607c54'
        and failed['state']=='FAILED_PARAGRAPH_PRODUCT_COMPONENTS'
        and failed['error_type']=='ValueError'
        and failed['error_code']=='EXACT_TWENTY_NEW_PARAGRAPH_PRODUCT_CASE_IDENTITIES'
        and failed['cleanup'] and failed['steps']==[],
        'EXACT_FAILED144_COUNT_PREFLIGHT_NO_CARGO_OR_TEST_EXECUTION_PRESERVED')
    pins={p['path']:p for p in failed['source_pins']}
    for name,pin in pins.items():
        q.pin(name)
        if name!=RUNNER:
            base.c.require(q.snapshots[name]==pin,'ALL_FAILED144_RUST_TEST_FIXTURE_AND_HELPER_INPUTS_UNCHANGED')
    text=q.text(RUNNER)
    for current,original in CHANGES:
        base.c.require(text.count(current)==1,'ONE_COUNT_ONLY_RUNNER_REPAIR')
        text=text.replace(current,original)
    base.audit.inverse(text,pins[RUNNER],'WHOLE_FAILED144_RUNNER_INVERSE_EXCEPT_SIX_COUNT_LABELS')
    ORIGINAL_INVERSE(q,old)


if __name__=='__main__':
    base.OUTPUT=OUTPUT
    base.inverse=inverse
    raise SystemExit(base.main())
