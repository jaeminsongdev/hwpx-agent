"""Bounded readonly XML observations of ten existing paths; not a new native qualification."""
import hashlib,io,json,re,time,zipfile
from pathlib import Path
from types import SimpleNamespace as NS
import xml.etree.ElementTree as ET
import run_resolved_style_product_components as prior
shared,c,a=prior.shared,prior.c,prior.a
OUTPUT='implementation/p09/evidence/p09-361-historical-style-observation153.v1.json'
HP='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
HH='{http://www.hancom.co.kr/hwpml/2011/head}'
OFFICIAL='fixtures/target-build/official-source-cache/hwpx-owpml-model-save-145338/OWPML/Class/Para/'
FILES=[('historical_hyperlink_saved_path','implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx')]
for i,name in enumerate(('p09-24-c01-footnote.hwpx','p09-24-c02-endnote.hwpx','p09-24-c03-footnote-endnote.hwpx'),1):
    FILES.append(('prepared_note_fixture','fixtures/target-build/p09-24-note-target-20261002-03/output/'+name))
    for lane in('saved','reopened'):
        FILES.append(('historical_note_'+lane+'_path',f'implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-24-20261002-c{i:02}-attempt01/{lane}.hwpx'))


def observe(raw,checkpoint):
    counts=dict(xml_parts=0,paragraphs=0,runs=0,text_elements=0,text_style_references=0,control_style_references=0,
        hidden_explanations=0,named_character_definitions=0,missing_direct_run_references=0,missing_direct_paragraph_references=0)
    with zipfile.ZipFile(io.BytesIO(raw))as archive:
        entries=archive.infolist();c.require(len(entries)<=512 and len({e.filename for e in entries})==len(entries),'BOUNDED_UNIQUE_ARCHIVE_ENTRIES')
        xml=[e for e in entries if e.filename.startswith('Contents/')and e.filename.endswith('.xml')]
        c.require(sum(e.file_size for e in xml)<=8*1024*1024 and all(e.file_size<=2*1024*1024 for e in xml),'BOUNDED_ORIGINAL_XML')
        for entry in xml:
            checkpoint();payload=archive.read(entry);c.require(b'<!DOCTYPE'not in payload.upper()and b'<!ENTITY'not in payload.upper(),'NO_DTD_OR_ENTITY_DECLARATIONS')
            root=ET.fromstring(payload);counts['xml_parts']+=1
            for i,node in enumerate(root.iter()):
                if i%128==0:checkpoint()
                if node.tag==HP+'p':counts['paragraphs']+=1;counts['missing_direct_paragraph_references']+=int('paraPrIDRef'not in node.attrib)
                if node.tag==HP+'run':counts['runs']+=1;counts['missing_direct_run_references']+=int('charPrIDRef'not in node.attrib)
                if node.tag==HP+'t':counts['text_elements']+=1;counts['text_style_references']+=int('charStyleIDRef'in node.attrib)
                if node.tag==HP+'ctrl':counts['control_style_references']+=int('charStyleIDRef'in node.attrib)
                if node.tag==HP+'hiddenComment':counts['hidden_explanations']+=1
                if node.tag==HH+'style'and node.attrib.get('type')=='CHAR':counts['named_character_definitions']+=1
    return counts


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'HISTORICAL_STYLE_OBSERVATION_IMMUTABLE_RUN_EXISTS')
    selection=prior.prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_HISTORICAL_STYLE_OBSERVATION',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        new_native_attestation=False,precedence_or_hidden_visibility_qualified=False,observations=[])
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(Path(__file__).relative_to(c.ROOT).as_posix());baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='5e421a1580b6b0b0830a685eb7cd0cdcf427d886762a6fe07964a6a4ec33a33d'and baseline['cleanup'],'EXACT_PRECEDING_V9_PRODUCT_EVIDENCE')
        failed=q.json('implementation/p09/evidence/p09-361-historical-style-observation152.v1.json')
        c.require(failed['state']=='FAILED_HISTORICAL_STYLE_OBSERVATION'and failed['error_type']=='KeyError'and failed['cleanup']and failed['observations']==[],
            'PRESERVED_INCOMPLETE152_MODEL_PIN_LOOKUP_FAILURE_NOT_SOURCE_OBSERVATION')
        reviewed_name='implementation/p09/evidence/p09-361-search-inspection-components048.v1.json';reviewed=q.json(reviewed_name)
        c.require(q.snapshots[reviewed_name]['sha256']=='25f6409f12938e9706e53adb2f9a518d3e1213102287a03f3fdd42e4c673b5c9'
            and reviewed['state'].startswith('PASS_')and reviewed['cleanup'],'EXACT_ORIGINAL_REVIEWED_MODEL_RECORD')
        pins={p['path']:p for p in reviewed['source_pins']}
        for name in('t.cpp','ctrl.cpp'):
            path=OFFICIAL+name;q.pin(path);c.require(q.snapshots[path]==pins[path],'ORIGINAL_REVIEWED_MODEL_SOURCE_UNCHANGED')
            c.require('m_uCharStyleIDRef'in q.text(path)and 'L"charStyleIDRef"'in q.text(path),'OFFICIAL_TEXT_AND_CONTROL_STORAGE_SITES')
        for label,name in FILES:
            q.pin(name);c.require(q.snapshots[name]['bytes']<=1024*1024,'BOUNDED_HISTORICAL_PACKAGE')
            raw=(c.ROOT/name).read_bytes();c.require(hashlib.sha256(raw).hexdigest()==q.snapshots[name]['sha256'],'OBSERVED_BYTES_MATCH_FRESH_PACKAGE_PIN')
            row['observations'].append(dict(origin_label=label,path=name,counts=observe(raw,guard.check)))
        q.pin('fixtures/target-build/p09-24-note-target-20261002-03/output/fixture-manifest.json')
        q.pin('implementation/p09/evidence/p09-26-note-native-batch-qualification.current-2020.v1.json')
        for module in tuple(__import__('sys').modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True)
        row.update(state='PASS_TEN_EXISTING_STYLE_SOURCE_OBSERVATIONS_ONLY_NOT_NATIVE_SEMANTICS_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            prepared_fixture_paths=3,historical_saved_or_reopened_paths=7,
            totals={k:sum(r['counts'][k]for r in row['observations'])for k in row['observations'][0]['counts']})
    except(ValueError,OSError,KeyError,TypeError,AttributeError,zipfile.BadZipFile,ET.ParseError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'HISTORICAL_STYLE_OBSERVATION_REJECTED_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','totals','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
