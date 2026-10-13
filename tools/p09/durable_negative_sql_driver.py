"""Original SQL body guard842→846; old27+durable4+DS06 eight checks exactly."""
import base64
import hashlib
import types
import signed_durable_sql_driver as prior
import durable_negative_sql_contract as contract
from signed_durable_sql_root import OwnedRootHolder


def transformed_source(source):
    old='len(build["source_freeze"]) == 842';new='len(build["source_freeze"]) == 846'
    contract.require(source.count(old)==1 and source.count(new)==0,'DRIVER_DELTA_SCOPE')
    changed=source.replace(old,new)
    contract.require(changed.replace(new,old)==source,'WHOLE_DRIVER_INVERSE');return changed


def required_checks():
    previous=prior.required_checks();extra=list(contract.build.parent.CONTROL_CHECKS)
    result=previous+extra
    contract.require(len(extra)==len(set(extra))==8 and len(result)==len(set(result))==39
        and result[:31]==previous,'EXACT39_ORIGINAL31_RETAINED')
    return result


def make_driver(reader,nonce):
    archive=reader.json(contract.ARCHIVE)
    pin=next(p for p in archive['files'] if p['path']==contract.DRIVER)
    raw=base64.b64decode(pin['base64'],validate=True)
    contract.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
        and reader.pin(contract.DRIVER)=={k:pin[k] for k in ('path','bytes','sha256')},'ORIGINAL_DRIVER_EXACT')
    source=raw.decode('utf-8').replace('\r\n','\n')
    made=types.ModuleType('p151_preserved_original_SQL_driver');made.__file__=str(contract.c.ROOT/contract.DRIVER)
    exec(compile(transformed_source(source),made.__file__,'exec'),made.__dict__)
    made.bind_probe_build=contract.bind_probe_build;made.consumer_sources=contract.consumer_sources
    made.ROOT_CHECKS=required_checks()
    holder=OwnedRootHolder(nonce,str(contract.c.ROOT/contract.build.executable_name(1)))
    made.OwnedSQLJobFactory=holder.factory_type(made.OwnedSQLJobFactory)
    contract.require(made.CHECKS==prior.original.CHECKS and made.resource_policy()==prior.original.resource_policy(),
        'ORIGINAL_SQL_SECURITY_AND_RESOURCE_POLICY')
    return made,holder
