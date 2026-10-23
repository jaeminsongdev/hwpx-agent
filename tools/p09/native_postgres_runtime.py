"""Owned portable PG18 runtime acquisition/version qualification; NEVER starts a database/service.

The ZIP is obtained over validated vendor HTTPS. Its locally observed SHA is an inventory pin,
not a vendor-signed checksum. Retain partial downloads and failed extractions for diagnosis.
"""
import hashlib,json,os,re,shutil,stat,struct,subprocess,sys,time,urllib.request,zipfile
from pathlib import Path,PurePosixPath
from bounded_process_progress import BoundedProcessCapture

ROOT=Path(__file__).resolve().parents[2]
SOURCE_PAGE='https://www.enterprisedb.com/download-postgresql-binaries'
VENDOR_ENTRY='https://sbp.enterprisedb.com/getfile.jsp?fileid=1260609'
URL='https://get.enterprisedb.com/postgresql/postgresql-18.6-5-windows-x64-binaries.zip'
EXPECTED_BYTES=384620317
VERSION='18.6'
ASSET='target/p09-native-postgres-18.6-5-278'
MAX_ENTRIES=30000
MAX_SELECTED_BYTES=1024*1024*1024
MAX_FILE_BYTES=256*1024*1024
REQUIRED=frozenset(('pgsql/bin/postgres.exe','pgsql/bin/initdb.exe','pgsql/bin/psql.exe','pgsql/bin/pg_ctl.exe',
    'pgsql/bin/pg_isready.exe','pgsql/bin/libpq.dll','pgsql/share/postgresql.conf.sample'))
EXECUTABLES={'postgres.exe':'postgres','initdb.exe':'initdb','psql.exe':'psql'}
RESERVED=frozenset(['con','prn','aux','nul']+[f'{p}{n}'for p in('com','lpt')for n in range(1,10)])
def require(ok,code):
    if not ok:raise ValueError(code)

def member_path(info):
    name=info.orig_filename
    require(name==info.filename,'PG_ARCHIVE_NORMALIZED_NAME_OR_NUL')
    require(isinstance(name,str)and 1<=len(name)<=240 and '\\'not in name and ':'not in name
        and not any(ord(c)<32 or ord(c)==127 for c in name),'PG_ARCHIVE_PATH_ENCODING')
    path=PurePosixPath(name)
    parts=name.rstrip('/').split('/')
    require(not path.is_absolute()and parts[0]=='pgsql'and all(p not in('','.','..')for p in parts),'PG_ARCHIVE_PATH_SCOPE')
    require(all(not p.endswith((' ','.'))and p.split('.')[0].casefold()not in RESERVED for p in parts),'PG_ARCHIVE_WINDOWS_ALIAS')
    mode=(info.external_attr>>16)&0xffff
    require(stat.S_IFMT(mode)in(0,stat.S_IFREG,stat.S_IFDIR),'PG_ARCHIVE_LINK_OR_SPECIAL_FILE')
    require(not(info.flag_bits&1),'PG_ARCHIVE_ENCRYPTED_ENTRY')
    require(0<=info.file_size<=MAX_FILE_BYTES and info.compress_size>=0,'PG_ARCHIVE_ENTRY_SIZE')
    require(info.file_size<=max(1,info.compress_size)*200,'PG_ARCHIVE_COMPRESSION_RATIO')
    return '/'.join(parts)

def select_members(infos):
    require(isinstance(infos,list)and 1<=len(infos)<=MAX_ENTRIES,'PG_ARCHIVE_ENTRY_COUNT')
    seen=set();files=set();selected=[];total=0
    for info in infos:
        path=member_path(info);key=path.casefold();require(key not in seen,'PG_ARCHIVE_DUPLICATE_WINDOWS_PATH');seen.add(key)
        if not info.is_dir():files.add(key)
        if not info.is_dir()and len(PurePosixPath(path).parts)>=3 and PurePosixPath(path).parts[1]in('bin','lib','share'):
            total+=info.file_size;require(total<=MAX_SELECTED_BYTES,'PG_ARCHIVE_SELECTED_SIZE');selected.append((info,path))
    paths={p for _,p in selected};require(REQUIRED<=paths,'PG_ARCHIVE_REQUIRED_RUNTIME_FILES')
    # Validate file-vs-directory collisions before creating anything under the new root.
    folded_files=files
    for _,path in selected:
        require(not any(p.as_posix().casefold()in folded_files for p in PurePosixPath(path).parents if p.as_posix()!='.'),'PG_ARCHIVE_FILE_PARENT_COLLISION')
    return selected,total

def clean_environment(binary):
    # Only child-local settings. Do not inherit a user's operational PG destination/options.
    env={k:v for k,v in os.environ.items()if not k.upper().startswith('PG')}
    env['PATH']=str(binary)+os.pathsep+str(Path(os.environ['SystemRoot'])/'System32')
    env.update(PG_COLOR='never',LC_ALL='C')
    return env

def sha_file(path):
    h=hashlib.sha256()
    with path.open('rb')as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def checked_destination(root,path):
    target=root.joinpath(*PurePosixPath(path).parts)
    require(target.resolve().is_relative_to(root.resolve())and not target.exists(),'PG_NEW_EXTRACTION_TARGET_ONLY')
    # New extraction ancestors must not resolve through a link/junction introduced mid-run.
    for parent in [root,*target.parents]:
        if parent==root.parent:break
        require(not parent.is_symlink()and not parent.is_junction(),'PG_EXTRACTION_LINK_ANCESTOR')
    return target

def extract(archive,root):
    selected,total=select_members(archive.infolist());pins=[]
    for info,path in selected:
        target=checked_destination(root,path);target.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();size=0
        with archive.open(info)as source,target.open('xb')as destination:
            while True:
                block=source.read(1024*1024)
                if not block:break
                size+=len(block);require(size<=info.file_size,'PG_EXTRACT_DECLARED_SIZE');h.update(block);destination.write(block)
        require(size==info.file_size,'PG_EXTRACT_EXACT_SIZE');pins.append(dict(path=path,bytes=size,sha256=h.hexdigest()))
    require(sum(p['bytes']for p in pins)==total,'PG_EXTRACT_INVENTORY_TOTAL')
    return pins

def version_line(name,output):
    require(name in EXECUTABLES,'PG_VERSION_EXECUTABLE_SCOPE')
    expected=f'{EXECUTABLES[name]} (PostgreSQL) {VERSION}'
    require(output.strip()==expected,'PG_VERSION_EXACT18_6');return expected

def pe_x64(path):
    with path.open('rb')as stream:
        header=stream.read(64);require(len(header)==64 and header[:2]==b'MZ','PG_PE_HEADER')
        offset=struct.unpack_from('<I',header,60)[0];require(64<=offset<=1048576,'PG_PE_OFFSET')
        stream.seek(offset);signature=stream.read(6);require(signature==b'PE\0\0\x64\x86','PG_PE_X64_ONLY')

def run_versions(root,pins):
    binary=root/'pgsql/bin';inventory={p['path']:p for p in pins};results=[]
    for name in EXECUTABLES:
        path=binary/name;pin=inventory['pgsql/bin/'+name];require(path.stat().st_size==pin['bytes']and sha_file(path)==pin['sha256'],'PG_EXECUTABLE_CURRENT_HASH')
        pe_x64(path);process=capture=None
        try:
            process=subprocess.Popen([str(path),'--version'],cwd=binary,env=clean_environment(binary),stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            capture=BoundedProcessCapture(process,output_limit=32768,parse_markers=False);out,err=capture.communicate(timeout=10)
            require(process.returncode==0 and not err.strip(),'PG_VERSION_EXIT_AND_STDERR')
            results.append(dict(binary=name,version=version_line(name,out),sha256=pin['sha256']))
        finally:
            if process is not None:
                if process.poll()is None:process.kill()
                process.wait(timeout=2)
                if capture is not None:capture.close()
    return results

def acquire():
    require(os.name=='nt'and Path.cwd().resolve()==ROOT.resolve(),'PG_RUNTIME_WINDOWS_REPO_SCOPE')
    parent=ROOT/'target';root=ROOT/ASSET
    require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not root.exists()
        and root.resolve().is_relative_to(parent.resolve()),'PG_RUNTIME_FRESH_OWNED_ROOT')
    require(shutil.disk_usage(parent).free>EXPECTED_BYTES+MAX_SELECTED_BYTES+1024*1024*1024,'PG_RUNTIME_DISK_RESERVE')
    root.mkdir();partial=root/'vendor.zip.partial';started=time.monotonic();count=0;h=hashlib.sha256()
    # Exact HTTPS endpoint, normal certificate validation, no resumed/unknown download reuse.
    with urllib.request.urlopen(URL,timeout=15)as response:
        require(response.geturl()==URL and response.status==200 and response.headers.get_content_type()=='application/zip'
            and int(response.headers.get('Content-Length','0'))==EXPECTED_BYTES,'PG_VENDOR_RESPONSE_IDENTITY')
        with partial.open('xb')as destination:
            while True:
                require(time.monotonic()-started<240,'PG_DOWNLOAD_DEADLINE')
                block=response.read(1024*1024)
                if not block:break
                count+=len(block);require(count<=EXPECTED_BYTES,'PG_DOWNLOAD_EXACT_BYTE_CAP');destination.write(block);h.update(block)
                # Bounded disk/Defender work; no shell fan-out or large concurrent extraction.
                delay=count/(8*1024*1024)-(time.monotonic()-started)
                if delay>0:time.sleep(min(delay,.25))
    require(count==EXPECTED_BYTES,'PG_DOWNLOAD_NOT_TRUNCATED')
    archive_path=root/'vendor.zip';partial.rename(archive_path)
    with zipfile.ZipFile(archive_path)as archive:pins=extract(archive,root)
    # Fresh byte verification for every extracted runtime input before any binary is executed.
    for pin in pins:
        p=root/pin['path'];require(p.stat().st_size==pin['bytes']and sha_file(p)==pin['sha256'],'PG_RUNTIME_FRESH_ALL_FILES')
    versions=run_versions(root,pins)
    for pin in pins:
        p=root/pin['path'];require(p.stat().st_size==pin['bytes']and sha_file(p)==pin['sha256'],'PG_RUNTIME_FINAL_ALL_FILES')
    require(archive_path.stat().st_size==EXPECTED_BYTES and sha_file(archive_path)==h.hexdigest(),'PG_VENDOR_ARCHIVE_FINAL_BYTES')
    manifest=dict(schema='hwpx-agent.p09-native-postgres-runtime/v1',state='ACQUIRED_VERSION_ONLY_NOT_DATABASE',
        source_page=SOURCE_PAGE,vendor_entry=VENDOR_ENTRY,url=URL,archive_bytes=count,archive_observed_sha256=h.hexdigest(),
        vendor_signed_checksum_available=False,https_origin_only_not_vendor_hash_attestation=True,
        archive_extract_files=len(pins),archive_extract_bytes=sum(p['bytes']for p in pins),runtime_pins=pins,versions=versions,
        actual_database_or_service_started=False,actual_SQL_executed=False,actual_Docker_WSL_Hangul_started=False)
    path=root/'runtime-manifest.json'
    with path.open('x',encoding='utf-8',newline='\n')as stream:json.dump(manifest,stream,ensure_ascii=False,separators=(',',':'))
    return dict(state=manifest['state'],manifest_path=path.relative_to(ROOT).as_posix(),manifest_bytes=path.stat().st_size,
        manifest_sha256=sha_file(path),archive_bytes=count,archive_observed_sha256=h.hexdigest(),runtime_files=len(pins),
        runtime_bytes=manifest['archive_extract_bytes'],versions=versions,actual_database_or_service_started=False)

if __name__=='__main__':
    try:
        require(sys.argv[1:]==['--acquire-version-only'],'PG_RUNTIME_CLOSED_WORKER_MODE')
        print(json.dumps(acquire(),separators=(',',':')),flush=True)
    except (ValueError,OSError,zipfile.BadZipFile,subprocess.SubprocessError)as error:
        code=str(error);safe=code if re.fullmatch('PG_[A-Z0-9_]{1,100}',code)else'PG_RUNTIME_OPERATION_FAILED_NO_RAW_DETAIL'
        print(json.dumps(dict(state='FAILED_NATIVE_PG_RUNTIME_NO_DATABASE',error_type=type(error).__name__,error_code=safe)),flush=True)
        raise SystemExit(2)from None
