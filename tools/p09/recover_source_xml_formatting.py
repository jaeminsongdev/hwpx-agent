"""Recover unintended rustfmt-only edits ONLY if whole P160 SHA256 matches.

Never writes product files. Saves exact current/recovered preimages and patches.
"""
import base64
import difflib
import hashlib
import json
import re
import source_xml_reuse_binding as b

NAMES=(
    'crates/hwpx-package/src/document_import/fields/semantics/catalog/assembly/review.rs',
    'crates/hwpx-package/src/document_import/fields/semantics/catalog/assembly.rs',
    'crates/hwpx-package/src/document_import/fields/semantics/catalog.rs',
    'crates/hwpx-package/src/document_import/structure/review/cell_body_output.rs',
    'crates/hwpx-package/src/document_import/structure/review/table_create_context.rs')

def normalized(line):return re.sub(r'\s+','',line)

def recover_token_gaps(now,old):
    pattern=r'"(?:\\.|[^"\\])*"|//[^\n]*|[A-Za-z_]\w*|\S'
    a=list(re.finditer(pattern,old));z=list(re.finditer(pattern,now));mapped={}
    matcher=difflib.SequenceMatcher(None,[x.group() for x in a],[x.group() for x in z],autojunk=False)
    for i,j,length in matcher.get_matching_blocks():
        for k in range(length):mapped[j+k]=i+k
    out=[]
    for j,t in enumerate(z):
        start=z[j-1].end() if j else 0;gap=now[start:t.start()]
        i=mapped.get(j)
        if i is not None and (j==0 and i==0 or j>0 and mapped.get(j-1)==i-1):
            gap=old[a[i-1].end() if i else 0:a[i].start()]
        out.extend((gap,t.group()))
    out.append(now[z[-1].end():] if z else now)
    return ''.join(out)

def recover(now,old):
    a=old.splitlines(keepends=True);z=now.splitlines(keepends=True);out=[]
    matcher=difflib.SequenceMatcher(None,[normalized(x) for x in a],[normalized(x) for x in z],autojunk=False)
    for tag,i,j,k,l in matcher.get_opcodes():
        left=''.join(a[i:j]);right=''.join(z[k:l])
        if tag=='equal' or (tag=='replace' and normalized(left)==normalized(right)):
            out.extend(a[i:j])
        else:out.extend(z[k:l])
    return ''.join(out)

def main():
    r=b.s.SQLRuntimeResources();r.admit();q=b.s.LiveSQLReader(r);out={}
    try:
        parent=q.json(b.PARENT['path']);expected=b.s.inputs.inventory(parent['bound_input_pins'])
        rows=[];patches=[];root=b.p.c.ROOT/'implementation/p09/source-archive'
        for n in NAMES:
            now=q.text(n);recovered=None
            if hashlib.sha256(now.encode()).hexdigest()==expected[n]['sha256']:
                rows.append(dict(path=n,current_pin=q.pin(n),expected_pin=expected[n],exact_recovered=True,already_exact=True))
                continue
            candidates=[p for p in root.rglob(n.split('/')[-1]) if p.as_posix().endswith('/'+n)]
            variants=[now]
            reordered=now.replace('mod review;\n#[cfg(test)]\nmod tests;\nuse crate::document_import::structure::review::{ReviewBodyImportError, ReviewBodyImportReceipt};\npub use review::AssembledReviewBody;',
                '#[cfg(test)]\nmod tests;\nmod review;\npub use review::AssembledReviewBody;\nuse crate::document_import::structure::review::{ReviewBodyImportError, ReviewBodyImportReceipt};')
            reordered=reordered.replace('pub mod filled_output;\npub mod output;', 'pub mod output;\npub mod filled_output;')
            variants.append(reordered)
            if n.endswith('/catalog.rs'):
                reordered=now.replace('pub mod assembly;\npub mod fonts;\nmod memo;\npub mod memo_style;\npub mod security;',
                    'pub mod security;\npub mod fonts;\npub mod assembly;\nmod memo;\npub use memo::{ImportedSectionMemoCatalogUse, MemoCatalogBinding};\npub mod memo_style;')
                reordered=reordered.replace('pub use memo::{ImportedSectionMemoCatalogUse, MemoCatalogBinding};\nuse serde::Serialize;', 'use serde::Serialize;')
                variants.append(reordered)
            # Previously archived source edits retain newer whole preimages.
            archived_text=[]
            for directory in root.glob('p09-149-*'):
                file=directory/'source-preimages.v1.json'
                if not file.is_file():continue
                data=q.json(file.relative_to(b.p.c.ROOT).as_posix())
                for item in data.get('files',[]):
                    if item.get('path')==n and 'base64' in item:
                        raw=base64.b64decode(item['base64'],validate=True)
                        if len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']:
                            archived_text.append(raw.decode('utf-8'))
            for v in variants:
                if hashlib.sha256(v.encode()).hexdigest()==expected[n]['sha256']:recovered=v
            for old in [*archived_text,*[q.text(path.relative_to(b.p.c.ROOT).as_posix()) for path in candidates]]:
                if recovered is not None:break
                previous=list(variants)
                variants.extend(recover(v,old) for v in previous)
                variants.extend(recover_token_gaps(v,old) for v in previous)
                variants=list(dict.fromkeys(variants))
                for v in variants:
                    if hashlib.sha256(v.encode()).hexdigest()==expected[n]['sha256']:recovered=v;break
                if recovered is not None:break
            rows.append(dict(path=n,current_pin=q.pin(n),current_base64=base64.b64encode(now.encode()).decode(),
                expected_pin=expected[n],exact_recovered=recovered is not None,
                recovered_base64=base64.b64encode(recovered.encode()).decode() if recovered is not None else None))
            if recovered is not None:
                delta=list(difflib.unified_diff(now.splitlines(),recovered.splitlines(),n=3,lineterm=''))
                patches.append('*** Begin Patch\n*** Update File: '+str(b.p.c.ROOT/n)+'\n'+'\n'.join(delta[2:])+'\n*** End Patch')
        q.finish()
        destination=b.s.scoped_path('implementation/p09/source-archive/p09-161-unintended-format-r42/recovery-preimages-run03.v1.json',fresh=True)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as f:json.dump(dict(baseline_closing_pin=b.PARENT,files=rows,patches=patches),f,indent=2)
        print(json.dumps(dict(recovered=[n['path'] for n in rows if n['exact_recovered']],
            unresolved=[n['path'] for n in rows if not n['exact_recovered']],patches=patches)))
    finally:b.s.finish_watcher(r,out)

if __name__=='__main__':main()
