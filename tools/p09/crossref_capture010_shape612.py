"""Bounded read-only XML parameter observations. Hashes/equality only, NOT semantics.
No native launcher, document writes, command execution, target inference or acceptance.
"""
import hashlib,io,re,zipfile
import xml.etree.ElementTree as ET
MAX_BYTES=4*1024*1024
MAX_ENTRIES=128
MAX_ELEMENTS=100000

def require(ok,code):
    if not ok:raise ValueError('XREF_SHAPE612_'+code)
def sha(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()
def local(name):return name.rsplit('}',1)[-1]

def read_package(reader,pin):
    # Same original paced reader + immutable binding used by text()/json(),
    # without decoding binary HWPX bytes as text or bypassing its checkpoints.
    actual,buffer=reader._read(pin['path'],parse=True)
    require(reader._bind(pin['path'],actual)==pin,'EXACT_PACKAGE_READ_BINDING')
    return bytes(buffer)

def inspect(data,expected,all_commands,checkpoint=lambda:None):
    require(type(data)is bytes and 0<len(data)<=MAX_BYTES and type(expected)is str and 0<len(expected)<=4096,'BOUNDED_INPUT')
    require(type(all_commands)is list and len(all_commands)==8 and len(set(all_commands))==8 and expected in all_commands,'EXACT_EIGHT_CANDIDATES')
    fields=[];seen=set();total=0;elements=0
    with zipfile.ZipFile(io.BytesIO(data),'r')as archive:
        entries=archive.infolist();require(0<len(entries)<=MAX_ENTRIES,'ZIP_COUNT')
        for entry in entries:
            checkpoint();name=entry.filename
            require(name not in seen and not name.startswith(('/','\\'))and '\\'not in name and '..'not in name.split('/'),'ZIP_PATH');seen.add(name)
            require(not entry.flag_bits&1 and entry.compress_type in(zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED),'ZIP_METHOD')
            total+=entry.file_size;require(0<=entry.file_size<=MAX_BYTES and total<=MAX_BYTES,'ZIP_EXPANSION')
            if not name.endswith('.xml'):continue
            with archive.open(entry)as stream:xml=stream.read(entry.file_size+1)
            require(len(xml)==entry.file_size and b'\x00'not in xml,'UTF8_XML_ONLY')
            try:text=xml.decode('utf-8')
            except UnicodeError:raise ValueError('XREF_SHAPE612_UTF8_XML_ONLY')from None
            require('<!DOCTYPE'not in text.upper()and '<!ENTITY'not in text.upper(),'NO_DTD_OR_ENTITY')
            try:root=ET.fromstring(text)
            except ET.ParseError:raise ValueError('XREF_SHAPE612_XML_PARSE')from None
            def walk(node,depth):
                nonlocal elements
                elements+=1;require(elements<=MAX_ELEMENTS and depth<=64,'XML_TREE_LIMIT')
                if elements%128==0:checkpoint()
                if local(node.tag)=='fieldBegin'and node.get('type')=='CROSSREF':
                    roots=[child for child in node if local(child.tag)=='parameters'];require(len(roots)<=1,'SINGLE_PARAMETERS')
                    params=[]
                    for child in([]if not roots else roots[0]):
                        tag=local(child.tag);require(re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,79}',tag)is not None,'PARAMETER_TAG')
                        text=''.join(child.itertext());require(len(text.encode())<=65536,'PARAMETER_TEXT_LIMIT')
                        name_value=child.get('name','');require(len(name_value.encode())<=4096,'PARAMETER_NAME_LIMIT')
                        params.append(dict(tag=tag,name_bytes=len(name_value.encode()),name_sha256=sha(name_value),
                            value_bytes=len(text.encode()),value_sha256=sha(text),nested_children=len(child),
                            exact_selected_command_match=text==expected,other_candidate_matches=sum(text==v for v in all_commands if v!=expected),
                            attribute_names=sorted(child.attrib)))
                    fields.append(dict(xml_part=name,parameter_children=params,has_parameters=bool(roots),
                        exact_selected_matching_children=sum(p['exact_selected_command_match']for p in params)))
                for child in node:walk(child,depth+1)
            walk(root,0)
    checkpoint()
    return dict(crossref_fields=len(fields),fields=fields,parameter_key_semantics_qualified=False,
        causal_insertion_or_preservation_proved=False,native_target_resolution_qualified=False,P09_complete=False)
