"""Explicit extension of preserved eight-input manifest with three receipts.

V1's exact sources/authority/qualifiers/focus checks remain. This version checks
new producer original/physical pins independently, then returns an eleven-pair
binding; no extra focused/whole/product/Gate qualification is inferred.
"""
import runtime_envelope_source_manifest_v1 as original
SELF="tools/p09/runtime_envelope_source_manifest_v2.py"
TEST="tools/p09/tests/test_runtime_envelope_source_manifest_v2.py"
SCHEMA="hwpx-agent.p09-envelope-full-source-manifest/v2"
PATH="implementation/p09/evidence/p09-361-case158-envelope-full-source-manifest020.v2.json"
EXTRA="implementation/p09/evidence/p09-361-case158-extra-three-envelope-producer-r635.v1.json"


def load(q,pin,a):
    row=a.read_exact(q,pin)
    a.require(type(row) is dict and set(row)=={"schema_version","index","before","base_manifest_pin","extra_producer_pin","extra_descriptors"},"CLOSED_ENVELOPE_MANIFEST_V2")
    a.fields(row,dict(schema_version=SCHEMA,index=158,before=151),"EXPLICIT_MANIFEST_V2_ONLY158")
    a.exact(pin["path"],PATH,"NEW_MANIFEST_V2_PATH")
    base,inherited,admission=original.load(q,row["base_manifest_pin"],a)
    a.exact(row["extra_producer_pin"]["path"],EXTRA,"EXTRA_PRODUCER_PATH")
    produced=a.read_exact(q,row["extra_producer_pin"])
    a.fields(produced,dict(state="PASS_THREE_EXTRA_EXCLUSIVE_LOSSLESS_RECEIPTS_NOT_CURRENT_NATIVE_OR_PRODUCT",
        original_receipts_rewritten=False,decode_passes=6,write_rate_bytes_per_second=2097152,cleanup_confirmed=True,
        authority151_pin=q.snapshots["implementation/p09/evidence/p09-361-case157-current-epoch-accept001.v1.json"],
        actual157_pin=q.snapshots["implementation/p09/evidence/p09-361-case157-current-runtime-run001.v1.json"]),"EXTRA_FRESH_PRODUCER_NOT_NATIVE")
    a.exact(produced["explicit_descriptors"],row["extra_descriptors"],"ACTUAL_EXTRA_PAIRS")
    a.require(type(row["extra_descriptors"]) is list and len(row["extra_descriptors"])==3,"THREE_EXTRA_PAIRS")
    for frozen in produced["source_pins"]:a.exact(q.pin(frozen["path"]),frozen,"EXTRA_PRODUCER_CURRENT_CODE")
    for desc in row["extra_descriptors"]:
        old,new=desc["semantic_original_pin"],desc["physical_envelope_pin"]
        a.exact(inherited.get(old["path"]),old,"EXTRA_ORIGINAL_IN_PRIOR_WHOLE_SCOPE")
        a.exact(q.fresh_pin(old["path"]),old,"FRESH_EXTRA_ORIGINAL")
        a.exact(q.fresh_pin(new["path"]),new,"FRESH_EXTRA_DERIVATIVE")
    descriptors=base.descriptors()+row["extra_descriptors"]
    binding=original.scope_binding.Binding(descriptors,pin,next_case=158)
    inherited=original.scope_binding.source.scope.extend(inherited,original.scope_binding.source.scope.pins([pin]))
    q.pin(SELF);q.pin(TEST)
    return binding,inherited,dict(admission,manifest_fresh_pin=pin,base_manifest_preserved=True,
        source_pair_count=11,extra_current_Native_or_whole_product_qualified=False,
        full_current158_oracle_or_runtime_connected=False,GO_authorized=False)
