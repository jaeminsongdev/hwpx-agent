"""Exact159 actual manifest: revalidate old158 admission, bind twenty pairs.

Separate fresh159 and preserved158 graphs; no old manifest rebasing or fake
placeholder. Old source/producer/failure/authority checks are all executed.
This module is not current159 controller, whole cost, Native or GO acceptance.
"""

SELF="tools/p09/runtime_successor_manifest_v1.py"
TEST="tools/p09/tests/test_runtime_successor_manifest_v1.py"
SCHEMA="hwpx-agent.p09-successor159-source-manifest/v1"
PATH="implementation/p09/evidence/p09-361-case159-source-manifest023.v1.json"
CODE="implementation/p09/evidence/p09-361-case159-successor-binding-code9-r729.v1.json"
PRODUCER="implementation/p09/evidence/p09-361-case159-four-envelope-producer-r728.v1.json"
SELECTION="implementation/p09/evidence/p09-361-case159-step-and-lossless-selection-r727.v1.json"


def load(q,pin,a,*,old_manifest,new_module,successor,failed003,failed004):
    row=a.read_exact(q,pin)
    a.require(type(row) is dict and set(row)=={"schema_version","index","before","authority152_pin",
        "actual158_pin","prior_manifest_pin","binding_qualification_pin","extra_producer_pin",
        "prior_failure_lineage"},"CLOSED_SUCCESSOR_MANIFEST")
    a.fields(row,dict(schema_version=SCHEMA,index=159,before=152,authority152_pin=successor.AUTHORITY,
        actual158_pin=successor.ROOT),"ONLY_ACTUAL152_SUCCESSOR159")
    a.exact(pin["path"],PATH,"EXACT_CURRENT_MANIFEST_PATH")
    a.require(new_module is not None and hasattr(new_module,"successor_failure_lineage"),
        "QUALIFIED_PRIVATE159_BINDING_REQUIRED")
    a.exact(row["prior_manifest_pin"]["path"],old_manifest.PATH,"UNCHANGED_PRIOR158_MANIFEST")
    prior=a.read_exact(q,row["actual158_pin"])
    a.exact(row["prior_manifest_pin"],prior["source_input_representation"]["manifest_pin"],"SAME_ACTUAL158_MANIFEST")
    old_binding,inherited,old_proof=old_manifest.load(q,row["prior_manifest_pin"],a)
    a.require(type(old_binding) is not new_module.Binding,"SEPARATE_158_159_CONSTRUCTOR_GRAPHS")
    a.exact(len(old_binding.descriptors()),16,"ALL_OLD_SIXTEEN_PAIRS_REVALIDATED")
    a.exact(old_binding.descriptors(),prior["source_input_representation"]["descriptors"],"EXACT_ACTUAL158_PAIRS")
    a.exact(row["binding_qualification_pin"]["path"],CODE,"EXACT_SUCCESSOR_BINDING_CODE9")
    code=a.read_exact(q,row["binding_qualification_pin"])
    a.fields(code,dict(state="PASS_SUCCESSOR159_BINDING_CODE9_FRESH_TWENTY_PAIRS_NOT_CURRENT_RUNTIME_OR_GO",
        contracts=dict(run=9,errors=0,failures=0,skipped=0),source_pair_count=20,
        future_manifest_placeholder_not_published=True,future_manifest_placeholder_not_runtime_input=True,
        cleanup_confirmed=True),"CODE9_NOT_PLACEHOLDER_RUNTIME_INPUT")
    for p in code["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_SUCCESSOR_BINDING_SOURCES")
    lineage=successor.admission(q,a,failed003,failed004)
    a.exact(lineage,row["prior_failure_lineage"],"ACTUAL_FRESH_PRIOR_FAILURES_STAY_FAILURES")
    a.exact(row["extra_producer_pin"]["path"],PRODUCER,"EXACT_FOUR_PRODUCER_PATH")
    produced=a.read_exact(q,row["extra_producer_pin"])
    a.fields(produced,dict(state="PASS_FOUR_SUCCESSOR159_EXCLUSIVE_LOSSLESS_RECEIPTS_NOT_CURRENT_RUNTIME_OR_GO",
        authority152_pin=successor.AUTHORITY,actual158_pin=successor.ROOT,original_receipts_rewritten=False,
        decode_passes=8,write_rate_bytes_per_second=2097152,cleanup_confirmed=True),"FOUR_EXCLUSIVE_PRIOR_RECEIPTS")
    a.exact(produced["selection_pin"]["path"],SELECTION,"EXACT_SUCCESSOR_SELECTION")
    selection=a.read_exact(q,produced["selection_pin"])
    a.fields(selection,dict(state="PASS_ACTUAL152_SUCCESSOR159_STEP_AND_FOUR_RECEIPT_SELECTION_NOT_RUNTIME_OR_GO",
        authority152_pin=successor.AUTHORITY,actual158_pin=successor.ROOT,cleanup_confirmed=True),"QUALIFIED_FOUR_SELECTION")
    a.require(type(selection["selected_originals"]) is list and len(selection["selected_originals"])==4,
        "FOUR_ORIGINAL_SELECTIONS")
    a.require(type(produced["explicit_descriptors"]) is list and len(produced["explicit_descriptors"])==4,
        "FOUR_ACTUAL_DERIVATIVES")
    for p in produced["source_pins"]+selection["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_PRODUCER_SELECTION_SOURCES")
    source=new_module.source
    originals=source.scope.extend(source.scope.extend(inherited,
        source.scope.pins(prior["source_input_representation"]["semantic_source_freeze"])),
        source.scope.pins([successor.AUTHORITY,successor.ROOT,pin]))
    descriptors=[source.descriptor(r["semantic_original_pin"],r["physical_envelope_pin"],next_case=159)
        for r in old_binding.descriptors()]
    for desc,expected in zip(produced["explicit_descriptors"],selection["selected_originals"]):
        old,new=desc["semantic_original_pin"],desc["physical_envelope_pin"]
        a.exact(old,expected,"SAME_EXACT_SELECTED_PRIOR_ORIGINAL")
        a.exact(originals.get(old["path"]),old,"ORIGINAL_INSIDE_COMPLETE_PRIOR_SCOPE")
        a.exact(desc,source.descriptor(old,new,next_case=159),"EXACT_TYPED_NEW_PAIR")
        descriptors.append(desc)
    a.exact(len(descriptors),20,"ALL_TWENTY_EXPLICIT_PAIRS")
    a.exact(descriptors,code["explicit_descriptors"],"QUALIFIED_TWENTY_PAIRS_NOT_PLACEHOLDER_PIN")
    for desc in descriptors:
        for p in (desc["semantic_original_pin"],desc["physical_envelope_pin"]):
            a.exact(q.fresh_pin(p["path"]),p,"FRESH_ALL_ORIGINAL_AND_PHYSICAL_BYTES")
    bound=new_module.Binding(descriptors,pin,next_case=159)
    q.pin(SELF);q.pin(TEST)
    return bound,originals,dict(old_proof,source_pair_count=20,prior158_admission_not_relabelled=True,
        fresh_actual159_manifest_pin=pin,fresh_prior_failure_lineage=lineage,
        invented_manifest_placeholder_or_Native_input=False,
        current159_complete_scope_cost_or_controller_qualified=False,GO_authorized=False)
