"""Strict readback of the fixed 670 source profile, not a general HWPX importer."""
import hashlib
from xml.etree import ElementTree as E
from block_bookmark_source_plan643 import cases
HP='http://www.hancom.co.kr/hwpml/2011/paragraph'
HS='http://www.hancom.co.kr/hwpml/2011/section'

def require(ok,code):
    if not ok:raise ValueError('BLOCK672_'+code)

def digest(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()

def read_section(raw):
    require(type(raw)is bytes and 0<len(raw)<=4*1024*1024 and b'<!DOCTYPE'not in raw.upper()
        and b'<!ENTITY'not in raw.upper(),'XML_BUDGET_OR_DECLARATION')
    try:root=E.fromstring(raw)
    except E.ParseError:raise ValueError('BLOCK672_XML_PARSE')from None
    require(root.tag=='{'+HS+'}sec','SECTION_NAMESPACE')
    paragraphs=list(root)
    require(len(paragraphs)==8 and all(p.tag=='{'+HP+'}p'for p in paragraphs),'FIXED_EIGHT_PARAGRAPHS')
    field_count=sum(e.tag in('{'+HP+'}fieldBegin','{'+HP+'}fieldEnd')for e in root.iter())
    require(field_count==16 and not any(e.tag=='{'+HP+'}bookmark'for e in root.iter()),'EXACT_BLOCK_FIELD_COVERAGE_NOT_POINT_MARKERS')
    rows=[];seen=set()
    for index,(paragraph,expected)in enumerate(zip(paragraphs,cases())):
        full='';selected='';begin=None;end=None;active=False;start=None;stop=None
        for run in paragraph:
            if run.tag=='{'+HP+'}linesegarray':continue
            require(run.tag=='{'+HP+'}run','RUN_ENVELOPE')
            for child in run:
                if child.tag=='{'+HP+'}secPr':
                    require(index==0 and begin is None,'SECTION_PROPERTY_LOCATION');continue
                if child.tag=='{'+HP+'}t':
                    require(len(child)==0,'PLAIN_TEXT_ONLY_PROFILE')
                    text=child.text or '';full+=text
                    if active:selected+=text
                    continue
                require(child.tag=='{'+HP+'}ctrl'and len(child)==1,'CONTROL_ENVELOPE')
                control=child[0]
                if control.tag=='{'+HP+'}colPr':
                    require(index==0 and begin is None,'COLUMN_PROPERTY_LOCATION');continue
                if control.tag=='{'+HP+'}fieldBegin':
                    require(begin is None and end is None and not active,'ONE_NONNESTED_BEGIN')
                    begin=control
                    require(set(begin.attrib)=={'id','type','name','editable','dirty','zorder','fieldid'}
                        and begin.get('type')=='BOOKMARK'and begin.get('name')==expected['bookmark_name']
                        and begin.get('editable')=='0'and begin.get('dirty')=='1'and begin.get('zorder')=='-1',
                        'EXACT_OBSERVED_BOOKMARK_HEADER')
                    identity=begin.get('id');require(identity.isascii()and identity.isdecimal()
                        and 0<int(identity)<=4294967295 and identity not in seen,'UNIQUE_BEGIN_ID')
                    seen.add(identity)
                    require(len(begin)==1 and begin[0].tag=='{'+HP+'}parameters'
                        and begin[0].attrib=={'cnt':'1','name':''}and len(begin[0])==1,'PARAMETERS_ENVELOPE')
                    prop=begin[0][0]
                    require(prop.tag=='{'+HP+'}integerParam'and prop.attrib=={'name':'Prop'}
                        and len(prop)==0 and prop.text=='2','OBSERVED_BLOCK_PROP_TWO')
                    start=len(full);active=True
                elif control.tag=='{'+HP+'}fieldEnd':
                    require(begin is not None and active and end is None,'END_REQUIRES_CURRENT_BEGIN')
                    end=control
                    require(end.attrib=={'beginIDRef':begin.get('id'),'fieldid':begin.get('fieldid')}
                        and len(end)==0,'END_BOUND_TO_BEGIN_ID_NOT_SHARED_FIELDID')
                    stop=len(full);active=False
                else:raise ValueError('BLOCK672_UNEXPECTED_CONTROL')
        logical=expected['selection']
        require(begin is not None and end is not None and not active and full==expected['seed_text']
            and selected==expected['selected_text']and (start,stop)==(logical['spos'],logical['epos']),
            'EXACT_LOGICAL_RANGE_AND_TEXT')
        rows.append(dict(case_index=index+1,paragraph_index=index,bookmark_name_sha256=digest(begin.get('name')),
            selected_text_sha256=digest(selected),selected_text_characters=len(selected),
            seed_text_sha256=digest(full),logical_start=start,logical_end=stop,
            native_begin_id=begin.get('id'),native_fieldid=begin.get('fieldid'),Prop=2,
            pair_key='begin.id_to_end.beginIDRef',raw_text_present=False))
    return rows
