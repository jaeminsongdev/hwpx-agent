"""Current envelope preparation through the unchanged frozen flat oracle.

Historical per-case source-stat DATA is not invented or retroactively inserted.
Validate current controller admission/inherited scope and invoke the identical
frozen prepare AST with only the explicitly current validator/root/context.
This adapter requires independent read-only qualification before queue writes.
"""
from types import SimpleNamespace as NS

SELF="tools/p09/current_envelope_acceptance_prepare_v1.py"


def prepare(q,root_pin,m):
    m.only158()
    m.a.exact(root_pin["path"],m.RETRY.root_path(m.base.CONFIG),"EXACT_CURRENT_ENVELOPE_ROOT")
    m.own_inputs(q)
    inherited=m.API.inherited_for_step(q,m.base.CONFIG)
    source=m.API.accept.__globals__["source"].prior.accepted.original
    raw=q.text(source.SELF).encode("utf-8")
    def projector(generator,*args,**kwargs):
        # Compose inherited semantic scope BEFORE the qualified physical adapter.
        # Its returned wrapper deliberately has no legacy ORACLE_SCOPE globals.
        factory=lambda raw,ctx,flat=True:(generator,{})
        scoped,_=m.API.previous.scoped_validator(factory,inherited)(None,None)
        return m.full_oracle.projector(scoped,*args,**kwargs)
    oracle=NS(**{**vars(m.full_oracle),"projector":projector})
    validator=m.prior.LINK.clone(m.validator,full_oracle=oracle)
    full=m.prior.LINK.clone(m.validate_candidate,validator=validator)
    unchanged=m.CURRENT_SOURCE.prepare_projection(raw)
    unchanged.__globals__.update(validate_candidate=full,
        r=NS(**{**vars(unchanged.__globals__["r"]),"context":m.context}))
    row,listing,evidence,proof=unchanged(q,root_pin)
    expected=m.base.scope.pins(row["source_freeze"])
    for name in (m.SELF,m.TEST,m.DATA):
        m.a.exact(expected.get(name),q.snapshots[name],"ACTUAL_CURRENT_CONTROLLER_DATA_AND_CODE_IN_FRAME")
    for pin in m.ATTEMPT_PINS+m.NAMESPACE_SOURCE_PINS+m.ROLE_PINS+m.TIMING_PINS+[m.ROLE_ONCE_PIN,m.CAPSULE]:
        m.a.exact(expected.get(pin["path"]),pin,"EVERY_CURRENT_ALIAS_TIMING_ATTEMPT_SOURCE_IN_FRAME")
    m.RETRY.validate_actual(row,m.base.CONFIG,root_pin)
    return row,listing,evidence,dict(proof,current_envelope_data_replaces_inapplicable_historical_case_data=True,
        original_frozen_flat_prepare_AST_and_complete_oracle_retained=True,
        original_current_controller_admission_and_inherited_scope_checked=True,
        invented_source_stat_DATA_or_retroactive_Native_input=False)
