"""Preserved original SQL body plus explicit current-input count and closed DI."""
import base64
import hashlib
import types
import run_formula_issuer_live_sql_probe as original
import signed_durable_sql_contract as contract
from signed_durable_sql_root import OwnedRootHolder

ROOT_EXTRA=('durable_root_disk_ciphertext_tag_and_digest_exact',
            'durable_root_fresh_handle_original_service_whole_read')
CONSUMER_EXTRA=('durable_signed_consumer_fresh_handle_whole_candidate_exact',
                'durable_signed_consumer_no_head_or_ingest_change')


def transformed_source(source):
    old='len(build["source_freeze"]) == 842'
    new='len(build["source_freeze"]) == 845'
    contract.require(source.count(old)==1 and source.count(new)==0,'DRIVER_DELTA_SCOPE')
    changed=source.replace(old,new)
    contract.require(changed.replace(new,old)==source,'DRIVER_WHOLE_INVERSE');return changed


def required_checks():
    old=list(original.ROOT_CHECKS)
    contract.require(len(old)==len(set(old))==27 and old[6]=='ciphertext_not_plaintext'
        and old[17]=='consumer_preserves_head_and_artifact_ingest_count','ORIGINAL_CHECK_ORDER')
    result=old[:7]+list(ROOT_EXTRA)+old[7:18]+list(CONSUMER_EXTRA)+old[18:]
    contract.require(len(result)==len(set(result))==31
        and [name for name in result if name not in ROOT_EXTRA+CONSUMER_EXTRA]==old,'ALL_ORIGINAL_CHECKS_RETAINED')
    return result


def make_driver(reader,nonce):
    archive=reader.json(contract.ARCHIVE)
    pin=next(p for p in archive['files'] if p['path']==contract.DRIVER)
    raw=base64.b64decode(pin['base64'],validate=True)
    contract.require(hashlib.sha256(raw).hexdigest()==pin['sha256'] and len(raw)==pin['bytes']
        and reader.pin(contract.DRIVER)=={k:pin[k] for k in ('path','bytes','sha256')},'CURRENT_ORIGINAL_DRIVER')
    source=raw.decode('utf-8').replace('\r\n','\n')
    namespace=types.ModuleType('p150_preserved_original_SQL_driver')
    namespace.__file__=str(contract.c.ROOT/contract.DRIVER)
    exec(compile(transformed_source(source),namespace.__file__,'exec'),namespace.__dict__)
    # Whole body is unchanged except the 842->845 guard above. Keep old module intact.
    namespace.bind_probe_build=contract.bind_probe_build
    namespace.consumer_sources=contract.consumer_sources
    namespace.ROOT_CHECKS=required_checks()
    holder=OwnedRootHolder(nonce,str(contract.c.ROOT/contract.build.executable_name(5)))
    namespace.OwnedSQLJobFactory=holder.factory_type(namespace.OwnedSQLJobFactory)
    contract.require(namespace.CHECKS==original.CHECKS and namespace.resource_policy()==original.resource_policy(),
        'ORIGINAL_SQL_AND_RESOURCE_POLICY')
    return namespace,holder
