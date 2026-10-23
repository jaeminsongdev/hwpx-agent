"""Project an unopened original Batch; retain history and all162 wire aliases."""
from types import SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_plan.py'
TEST='tools/p09/tests/test_native011_current_epoch_plan.py'


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_PLAN_'+code)


def plain(rows):return {n:dict(p) for n,p in rows.items()}


class Versions:
    """Only five exact old/new source triples; original alias parser stays intact."""
    def __init__(self,declared,rows,scope,changed):
        require(type(rows) is list and len(rows)==5,'EXACT_FIVE_SOURCE_VERSIONS')
        self.base=declared;self.scope=scope;self.rows={};self.archives={}
        for row in rows:
            before=row['original_pin'];after=row['proposed_archive_pin'];current=row['current_pin']
            scope.pins([before]);scope.pins([after]);scope.pins([current])
            name=before['path']
            require(name==current['path'] and name not in self.rows and after['path'] not in self.archives
                and after['bytes']==before['bytes'] and after['sha256']==before['sha256']
                and current!=before,'EXACT_DISJOINT_OLD_ARCHIVE_NEW_TRIPLE')
            require(declared.normalize([before])=={name:before}
                and declared.to_physical([before])=={name:before},'SOURCE_VERSION_NOT_A162_WIRE_ALIAS')
            self.rows[name]=(dict(before),dict(after),dict(current));self.archives[after['path']]=dict(after)
        require(set(self.rows)==set(changed),'ONLY_CLOSED_FIVE_CHANGED_SOURCES')

    def normalize(self,rows):
        result={}
        for name,pin in self.base.normalize(rows).items():
            if name in self.rows:
                before,after,current=self.rows[name]
                require(pin==before or pin==current,'NO_THIRD_SOURCE_VERSION_OR_HASH_REBASE')
                if pin==before:pin=after;name=after['path']
            elif name in self.archives:
                require(pin==self.archives[name],'EXACT_ARCHIVE_SOURCE_VERSION')
            require(name not in result or result[name]==pin,'NO_VERSION_PROJECTION_COLLISION')
            result[name]=dict(pin)
        return self.scope.pins(list(result.values()))

    def physical(self,rows):
        normalized=self.normalize(rows)
        return self.base.to_physical(list(normalized.values()))


def apply(data,cohort,preimages,controls,batch,scope,changed,checkpoint):
    require(callable(checkpoint),'ORIGINAL_CHECKPOINT_REQUIRED');checkpoint()
    old=data.planned;owner=old.batch;owner.check()
    require(type(owner) is batch.Batch and owner.phase=='NEW' and owner.first_index==165
        and owner.parent_connection is None and owner.initial is owner.final is owner.active is None
        and not owner.cases and not owner.metadata_reader_active,'UNOPENED_UNCONNECTED_BATCH_ONLY')
    whole,current,history,logical=(plain(getattr(old,n)) for n in ('whole','current','history','logical'))
    require(all(plain(getattr(owner,n))==rows for n,rows in (('whole',whole),('current',current),('history',history))),
        'EXACT_ORIGINAL_BATCH_PARTITION')
    require(set(controls)=={SELF,TEST} and scope.pins(list(controls.values()))==controls,'TWO_NAMED_PROJECTOR_CONTROLS')
    versions=Versions(data.declared,preimages,scope,changed)
    require(not(set(changed)|set(versions.archives))&set(history),'NO_VERSION_OR_ARCHIVE_IS_HISTORY')
    for name,(before,after,new) in versions.rows.items():
        require(all(rows.get(name)==before for rows in (whole,current,logical)),'OLD_SOURCE_IN_ALL_PRIOR_PLAN_VIEWS')
        require(cohort.required.get(name)==new and cohort.required.get(after['path'])==after,
            'EXACT_ADMITTED_CURRENT_AND_PRIOR_SOURCE')
    manifest=data.manifest;descriptors=manifest['descriptors']
    require(type(descriptors) is list and len(descriptors)==162,'ALL162_DESCRIPTORS_RETAINED')
    for row in descriptors:
        before=row['semantic_original_pin'];carrier=row['physical_envelope_pin']
        require(versions.physical([before])=={carrier['path']:carrier},'EVERY_ORIGINAL162_CARRIER_UNCHANGED')
    additions=scope.extend(cohort.required,controls)
    logical_additions=versions.normalize(list(additions.values()))
    physical_additions=versions.physical(list(additions.values()))
    require(versions.physical(list(history.values()))==history,'EVERY_PRESERVED_PIN_AND_PATH_UNCHANGED')
    for name in set(physical_additions)&set(history):
        require(physical_additions[name]==history[name],'NO_HISTORY_PIN_CHANGE_OR_RECLASSIFICATION')
    next_whole=scope.extend(versions.physical(list(whole.values())),physical_additions)
    next_current=scope.extend(versions.physical(list(current.values())),
        {n:p for n,p in physical_additions.items() if n not in history})
    next_logical=scope.extend(versions.normalize(list(logical.values())),logical_additions)
    require(set(next_current).isdisjoint(history) and {**next_current,**history}==next_whole,
        'LOSSLESS_DISJOINT_SAME_HISTORY_PARTITION')
    require(versions.physical(list(next_logical.values()))==next_whole,'FULL_NEW_LOGICAL_PHYSICAL_EQUALITY')
    next_owner=batch.Batch(next_whole,next_current,history,first_index=165,checkpoint=checkpoint,identity=owner.identity)
    require(plain(next_owner.history)==history and owner.phase=='NEW','ORIGINAL_OWNER_AND_HISTORY_NOT_MUTATED')
    next_plan=NS(**{**vars(old),'batch':next_owner,'whole':next_whole,'current':next_current,
                    'history':history,'logical':next_logical})
    next_declared=NS(**{**vars(data.declared),'normalize':versions.normalize,'to_physical':versions.physical})
    checkpoint()
    proof=dict(whole_before=len(whole),whole_after=len(next_whole),current_before=len(current),
        current_after=len(next_current),history_count=len(history),history_reclassified=0,
        exact_unchanged_descriptors=162,source_versions_preserved=5,original_batch_unmodified=True,
        original_normalizer_and_carrier_rules_retained=True,actual_parent_Frame_or_worker_qualified=False,
        full_source_byte_boundary_qualified=False,GO_authorized=False)
    return NS(**{**vars(data),'planned':next_plan,'declared':next_declared}),proof,versions
