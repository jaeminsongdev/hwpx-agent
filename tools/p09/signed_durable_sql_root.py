"""Fresh root derived ONLY from the journalled driver's owned UUID; retain evidence."""
import os
from pathlib import Path
from itertools import islice
import conservative_maintenance as c
import sql_container_ownership as ownership
from sql_owned_execution import scoped_path

BASE='target/p09-150-signed-durable/private'
MARKER='.p150-owned-run'
SCHEMA='hwpx-agent.p09-150-owned-blob-root/v1'
ENV=('P150_BLOB_MODE','P150_BLOB_ROOT','P150_BLOB_RUN_ID')


def require(ok,code):c.require(ok,'SQL_RUNTIME_DURABLE_'+code)


def marker(run):
    ownership.uuid_value(run);return f'{SCHEMA}\n{run}\n'.encode('ascii')


def root_name(run):
    ownership.uuid_value(run);return f'{BASE}/p150-{run}'


def verify(root,run):
    path=scoped_path(root_name(run))
    require(Path(root)==path and path.is_dir(),'ROOT_IDENTITY')
    owner=scoped_path((path/c.Path(MARKER)).relative_to(c.ROOT).as_posix())
    require(owner.is_file() and owner.stat().st_size<=129,'OWNER_SCOPE')
    with owner.open('rb') as stream:raw=stream.read(130)
    require(raw==marker(run),'OWNER_IDENTITY');return path


def create(run):
    base=scoped_path(BASE);require(base.is_dir(),'PRIVATE_BASE_MISSING')
    path=scoped_path(root_name(run),fresh=True);path.mkdir()
    owner=path/MARKER
    with owner.open('xb') as stream:
        raw=marker(run);require(stream.write(raw)==len(raw),'OWNER_SHORT_WRITE');stream.flush();os.fsync(stream.fileno())
    require(list(path.iterdir())==[owner],'INITIAL_ROOT_NOT_EMPTY')
    return verify(path,run)


def crypto_environment(env,root,run):
    verify(root,run);out=dict(os.environ if env is None else env)
    for name in ENV:out.pop(name,None)
    out.update(P150_BLOB_MODE='owned_local_v1',P150_BLOB_ROOT=str(root),P150_BLOB_RUN_ID=run)
    return out


class OwnedRootHolder:
    def __init__(self,nonce,crypto):
        ownership.uuid_value(nonce);self.nonce=nonce;self.crypto=crypto;self.root=None;self.run=None

    def factory_type(self,original):
        holder=self
        class DurableFactory(original):
            def __call__(self,args,**kw):
                require(isinstance(args,(list,tuple)) and args and all(isinstance(a,str) for a in args),
                    'COMMAND_ARGUMENT_SCOPE')
                if isinstance(args,(list,tuple)) and len(args)>1 and args[0]==self.docker and args[1]=='run':
                    intent=ownership.intent_from_run(holder.nonce,'approval',args,self.docker)
                    require(holder.root is None,'DUPLICATE_ROOT_CREATE')
                    holder.run=intent['run_id'];holder.root=create(holder.run)
                env=dict(os.environ if kw.get('env') is None else kw['env'])
                for name in ENV:env.pop(name,None)
                if args[0]==holder.crypto:
                    require(list(args)==[holder.crypto] and holder.root is not None,'CRYPTO_ROOT_CONTEXT')
                    env=crypto_environment(env,holder.root,holder.run)
                kw['env']=env
                return super().__call__(args,**kw)
        return DurableFactory

    def manifest(self,reader):
        if self.root is None:return dict(created=False,retained=True,files=[])
        root=verify(self.root,self.run);files=[];pending=[root];entries=total=0;directories={}
        while pending:
            directory=pending.pop()
            reader.resources.checkpoint_io()
            children=list(islice(directory.iterdir(),257))
            require(len(children)<=256,'ROOT_INVENTORY_BUDGET')
            directories[directory]=frozenset(p.name for p in children)
            for path in sorted(children):
                reader.resources.checkpoint_io()
                entries+=1;require(entries<=256,'ROOT_INVENTORY_BUDGET')
                path=scoped_path(path.relative_to(c.ROOT).as_posix())
                if path.is_dir():pending.append(path)
                else:
                    require(path.is_file(),'ROOT_FILE_KIND');pin=reader.pin(path.relative_to(c.ROOT).as_posix())
                    total+=pin['bytes'];require(total<=256*1024*1024,'ROOT_BYTES_BUDGET');files.append(pin)
        for directory,names in directories.items():
            reader.resources.checkpoint_io()
            current=list(islice(directory.iterdir(),257))
            require(len(current)<=256 and frozenset(p.name for p in current)==names,'ROOT_INVENTORY_DRIFT')
        verify(root,self.run)
        return dict(created=True,run_id=self.run,relative_root=root.relative_to(c.ROOT).as_posix(),
            owner_exact=True,retained=True,files=files,total_bytes=total,OS_ACL_qualified=False,
            independent_restart_or_key_custody_qualified=False)
