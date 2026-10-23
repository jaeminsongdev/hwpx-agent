//! One actual graph walk and one forward parent map per selected XML part. No ID-name inference.
use super::*;
use domain_ir::{Flow,Node,LogicalId,SourceAnchorHandle};
use std::collections::BTreeMap;
type Owner<'a>=Result<&'a LogicalId,()>;
pub(super) fn resolve(v:&CompilationView<'_>,p:&projection::Projection<'_>)->Result<Vec<LogicalId>,CompiledSearchError>{
    let graph=v.source.imported().graph();let source=v.source.imported().source();
    resolve_parts(graph,source,&p.edits)
}
fn resolve_parts(graph:&domain_ir::DocumentGraph,source:&hwpx_package::document_import::ImportedSourcePackage,
    edits:&[projection::Edit<'_>])->Result<Vec<LogicalId>,CompiledSearchError>{
    let mut direct:BTreeMap<&LogicalId,(&SourceAnchorHandle,Owner<'_>)>=BTreeMap::new();
    let mut flows:Vec<&Flow>=graph.sections().iter().map(|s|&s.body).chain(graph.notes().iter().map(|n|&n.body)).collect();
    while let Some(flow)=flows.pop(){for node in &flow.children{
        let c=node.common();if let Some(anchor)=&c.source_anchor{
            let at=source.resolve_anchor(anchor).map_err(|_|CompiledSearchError::Target)?;
            if at.element_index().is_none(){return Err(CompiledSearchError::Target);}
            direct.entry(&anchor.opaque_handle).and_modify(|(_,owner)|*owner=Err(())).or_insert((anchor,Ok(&c.node_id)));
        }
        match node{Node::Table(t)=>flows.extend(t.cells.iter().map(|c|&c.body)),Node::Drawing(d)=>flows.push(&d.children),_=>{}}
    }}
    let mut requests:BTreeMap<_,Vec<(usize,usize)>>=BTreeMap::new();
    for(n,edit)in edits.iter().enumerate(){let at=source.resolve_anchor(edit.anchor).map_err(|_|CompiledSearchError::Target)?;
        let i=at.element_index().ok_or(CompiledSearchError::Target)?;
        if let Some(expected)=edit.subtree{let span=at.element().and_then(|e|e.outer_span()).ok_or(CompiledSearchError::Target)?;
            if expected!=(span.start(),span.end()){return Err(CompiledSearchError::Target);}}
        requests.entry(at.part().path()).or_default().push((n,i));
    }
    let mut result:Vec<Option<LogicalId>>=vec![None;edits.len()];let mut seen=BTreeSet::new();
    for(path,items)in requests{let part=source.parts().iter().find(|part|part.path()==path).ok_or(CompiledSearchError::Target)?;
        let xml=part.xml().ok_or(CompiledSearchError::Target)?;let mut inherited:Vec<Option<Owner<'_>>>=Vec::with_capacity(xml.elements().len());
        for(i,node)in xml.elements().iter().enumerate(){let anchor=part.element_anchor(i).ok_or(CompiledSearchError::Target)?;
            let owner=if let Some((expected,owner))=direct.get(&anchor.opaque_handle){
                if *expected!=anchor{return Err(CompiledSearchError::Target);}Some(*owner)
            }else if let Some(parent)=node.parent(){if parent>=i{return Err(CompiledSearchError::Target);}inherited[parent]}else{None};
            inherited.push(owner);
        }
        for(n,i)in items{if !seen.insert(&edits[n].anchor.opaque_handle){return Err(CompiledSearchError::Target);}
            result[n]=Some(inherited.get(i).copied().flatten().ok_or(CompiledSearchError::Target)?.map_err(|_|CompiledSearchError::Target)?.clone());}
    }
    result.into_iter().map(|n|n.ok_or(CompiledSearchError::Target)).collect()
}
#[cfg(test)]
#[path="owners/tests.rs"] mod tests;
