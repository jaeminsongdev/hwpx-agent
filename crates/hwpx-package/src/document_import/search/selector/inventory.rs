//! Bounded selector discovery from one immutable index; no body, query or native defaults.
use super::*;
pub const SOURCE_SCOPE_INVENTORY_PROFILE:&str="hwpx-agent.source-index-scope-inventory/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceIndexBlockDescriptor {pub paragraph_handle:LogicalId,pub block_index:usize,pub normalized_scalars:usize}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceIndexNodeDescriptor {pub node_id:LogicalId,pub source_handle:LogicalId}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceScopeInventory {
    pub profile:&'static str,pub index:SourceSearchIndexReceipt,pub section_ids:Vec<LogicalId>,pub nodes:Vec<SourceIndexNodeDescriptor>,
    pub blocks:Vec<SourceIndexBlockDescriptor>,pub full_source_visibility_native_flow_or_revision_authority:bool,
    #[serde(skip)] maximum:usize,
}
impl SourceScopeInventory {
    /// # Errors
    /// Includes all admitted descriptors or fails at the finite response bound.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {
        let mut output=Output {bytes:Some(Vec::new()),length:0,maximum:self.maximum};
        serde_json::to_writer(&mut output,self).map_err(|_|E::Output)?;output.bytes.ok_or(E::Output)
    }
    /// # Errors
    /// Pure discovery digest, not revision or access authority.
    pub fn binding_sha256(&self)->Result<[u8;32],E> {let mut hash=ScopeHash::new(self.maximum);
        serde_json::to_writer(&mut hash,self).map_err(|_|E::Output)?;Ok(hash.finish())}
}
impl SourceTextIndex<'_> {
    /// # Errors
    /// Actual section/node IDs and NFC block limits from this original index only.
    pub fn scope_inventory(&self)->Result<SourceScopeInventory,E> {
        self.scope_inventory_with_nodes(None)
    }
    pub(in crate::document_import::search) fn scope_inventory_with_nodes(&self,supplemental:Option<&SupplementalNodes>)->Result<SourceScopeInventory,E> {
        let mut nodes=BTreeMap::new();
        for section in self.original.graph().sections(){self.inventory_nodes(&section.body,&mut nodes,0)?;}
        for note in self.original.graph().notes(){self.inventory_nodes(&note.body,&mut nodes,0)?;}
        if let Some(extra)=supplemental {for (id,anchor) in extra {
            if nodes.len()>=self.limits.0.blocks{return Err(E::Limit);}
            self.original.source().resolve_anchor(anchor).map_err(|_|E::Source)?;
            if nodes.insert(id.clone(),SourceIndexNodeDescriptor {node_id:id.clone(),source_handle:anchor.opaque_handle.clone()}).is_some(){return Err(E::Mapping);}
        }}
        let inventory=SourceScopeInventory {profile:SOURCE_SCOPE_INVENTORY_PROFILE,index:self.receipt.clone(),
            section_ids:self.original.graph().sections().iter().map(|s|s.section_id.clone()).collect(),nodes:nodes.into_values().collect(),
            blocks:self.blocks.iter().enumerate().map(|(i,b)|SourceIndexBlockDescriptor {paragraph_handle:b.paragraph.opaque_handle.clone(),block_index:i,normalized_scalars:b.units.len()}).collect(),
            full_source_visibility_native_flow_or_revision_authority:false,maximum:self.limits.0.result_bytes};
        inventory.binding_sha256()?;Ok(inventory)
    }
    fn inventory_nodes(&self,flow:&Flow,nodes:&mut BTreeMap<LogicalId,SourceIndexNodeDescriptor>,depth:usize)->Result<(),E> {
        if depth>128{return Err(E::Limit);}for node in &flow.children {
            if nodes.len()>=self.limits.0.blocks{return Err(E::Limit);}
            let common=node.common();let anchor=common.source_anchor.as_ref().ok_or(E::Source)?;
            self.original.source().resolve_anchor(anchor).map_err(|_|E::Source)?;
            if nodes.insert(common.node_id.clone(),SourceIndexNodeDescriptor {node_id:common.node_id.clone(),source_handle:anchor.opaque_handle.clone()}).is_some(){return Err(E::Mapping);}
            match node {Node::Table(t)=>for cell in &t.cells {self.inventory_nodes(&cell.body,nodes,depth+1)?;},Node::Drawing(d)=>self.inventory_nodes(&d.children,nodes,depth+1)?,_=>{}}
        }Ok(())
    }
}
