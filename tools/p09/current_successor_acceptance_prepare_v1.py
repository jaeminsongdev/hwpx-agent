"""Independent current159 whole oracle through the unchanged frozen prepare.

Derive inherited expectations from exact prior158/authority152 and the admitted
manifest, not current candidate observations. Preserve original checker code,
physical scope projection, timing/Job/cleanup/byte checks. No queue writer.
"""
from types import SimpleNamespace as NS

SELF="tools/p09/current_successor_acceptance_prepare_v1.py"


def prepare(q,root_pin,m):
    m.only159()
    m.a.exact(root_pin["path"],m.RETRY.root_path(m.base.CONFIG),"EXACT_CURRENT159_INDEPENDENT_ROOT")
    m.own_inputs(q)
    graph=m.graph_value()
    prior=m.API.inherited_for_step(q,m.base.CONFIG)
    live,semantic,admission=m.current_binding.manifest.load(q,m.MANIFEST,m.a,
        old_manifest=m.old.manifest,new_module=graph.binding_module,
        successor=m.current_binding.successor,failed003=m.old.failed_role,failed004=m.old.failed004_role)
    m.a.exact(live.descriptors(),graph.binding.descriptors(),"CURRENT159_INDEPENDENT_MANIFEST_AND_CAPSULE_EQUAL")
    inherited=m.base.scope.extend(prior,semantic)
    source=m.old.API.accept.__globals__["source"].prior.accepted.original
    raw=q.text(source.SELF).encode("utf-8")
    def projector(generator,*args,**kwargs):
        factory=lambda raw,ctx,flat=True:(generator,{})
        scoped,_=m.API.previous.scoped_validator(factory,inherited)(None,None)
        return graph.full_oracle.projector(scoped,*args,**kwargs)
    oracle=NS(**{**vars(graph.full_oracle),"projector":projector})
    private_graph=NS(**{**vars(graph),"full_oracle":oracle})
    validator=m.prior.LINK.clone(m.validator,graph_value=lambda:private_graph)
    full=m.prior.LINK.clone(m.validate_candidate,validator=validator)
    unchanged=m.CURRENT_SOURCE.prepare_projection(raw)
    unchanged.__globals__.update(validate_candidate=full,
        r=NS(**{**vars(unchanged.__globals__["r"]),"context":m.context}))
    row,listing,evidence,proof=unchanged(q,root_pin)
    expected=m.base.scope.pins(row["source_freeze"])
    for name in (m.SELF,m.TEST,m.DATA):
        m.a.exact(expected.get(name),q.snapshots[name],"EXACT_CURRENT159_CODE_DATA_IN_REAL_NATIVE_FRAME")
    for pin in m.old.NAMESPACE_SOURCE_PINS+m.old.ROLE_PINS+m.old.TIMING_PINS+[m.old.ROLE_ONCE_PIN,m.CAPSULE,m.MANIFEST]:
        m.a.exact(expected.get(pin["path"]),pin,"ALL_CURRENT159_ALIAS_TIMING_FAILURE_SOURCES_IN_FRAME")
    m.RETRY.validate_actual(row,m.base.CONFIG,root_pin)
    return row,listing,evidence,dict(proof,current159_admission_and_independent_prior_semantic_scope_checked=True,
        original_frozen_flat_prepare_and_whole_original_oracle_retained=True,
        original_Native_Job_resource_byte_cleanup_and_strict_window_oracles_retained=True,
        actual_manifest_admission=admission,invented_source_stat_DATA_or_retroactive_Native_input=False,
        queue_acceptance_called=False,product_or_Native_reexecuted=False)
