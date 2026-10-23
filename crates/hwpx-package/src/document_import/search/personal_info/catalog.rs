//! Complete source-bound UTF16LE installation format catalog. Not an attested vendor default or Native matcher.
use super::*;
use std::collections::BTreeMap;
pub const PERSONAL_INFO_CATALOG_PROFILE:&str="hwpx-agent.source-personal-info-catalog/hancom2020-ini-utf16le/v1";
const RAW_MAX:usize=64*1024;const PATTERNS_MAX:usize=128;const PATTERN_TOTAL_MAX:usize=64*1024;const COMBINED_MAX:usize=128*1024;
#[derive(Clone,Copy,Debug,Eq,PartialEq,Ord,PartialOrd,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum PersonalInfoCatalogFamily{Telephone,ResidentRegistration,ForeignRegistration,Email,Account,DriverLicense,Passport,CreditCard,IpAddress,BirthDate,UserDefined}
impl PersonalInfoCatalogFamily{
    fn parse(value:&str)->Option<Self>{Some(match value{"TELEPHONE"=>Self::Telephone,"RESIDENT"=>Self::ResidentRegistration,"FOREIGNER"=>Self::ForeignRegistration,"EMAIL"=>Self::Email,
        "ACCOUNT"=>Self::Account,"LICENSE"=>Self::DriverLicense,"PASSPORT"=>Self::Passport,"CREDIT"=>Self::CreditCard,"IPADDRESS"=>Self::IpAddress,"BIRTHDAY"=>Self::BirthDate,"USERDEF"=>Self::UserDefined,_=>return None})}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]pub struct PersonalInfoCatalogSection{pub family:PersonalInfoCatalogFamily,pub patterns:usize}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]pub struct PersonalInfoCatalogReceipt{
    pub profile:&'static str,pub source_sha256:[u8;32],pub source_bytes:usize,pub source_section_order:Vec<PersonalInfoCatalogSection>,pub total_patterns:usize,
    pub original_pattern_text_preserved:bool,pub installed_vendor_authenticity_or_native_semantics_qualified:bool,
}
struct Section{family:PersonalInfoCatalogFamily,patterns:Vec<String>}
pub struct SourcePersonalInfoCatalog{sections:Vec<Section>,receipt:PersonalInfoCatalogReceipt}
impl fmt::Debug for SourcePersonalInfoCatalog{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourcePersonalInfoCatalog(<redacted>; source_observation_not_native_defaults)")}}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]pub enum PersonalInfoCatalogError{
    #[error("PERSONAL_INFO_CATALOG_SOURCE_REJECTED")]Source,
    #[error("PERSONAL_INFO_CATALOG_ENCODING_REJECTED")]Encoding,
    #[error("PERSONAL_INFO_CATALOG_SYNTAX_REJECTED")]Syntax,
    #[error("PERSONAL_INFO_CATALOG_FAMILY_COVERAGE_REJECTED")]Coverage,
    #[error("PERSONAL_INFO_CATALOG_SELECTION_REJECTED")]Selection,
    #[error("PERSONAL_INFO_CATALOG_PATTERN_REJECTED")]Pattern,
    #[error("PERSONAL_INFO_CATALOG_LIMIT")]Limit,
    #[error("PERSONAL_INFO_CATALOG_SEARCH_REJECTED")]Search(#[from]SourceSearchError),
}
type C=PersonalInfoCatalogError;
impl SourcePersonalInfoCatalog{
    /// # Errors
    /// Ten nonempty format families plus an optional, possibly empty USERDEF section, contiguous IDs and exact UTF16LE/SHA.
    pub fn parse_utf16le(raw:&[u8],expected:[u8;32])->Result<Self,C>{
        if raw.is_empty()||raw.len()>RAW_MAX{return Err(C::Limit);}if <[u8;32]>::from(Sha256::digest(raw))!=expected{return Err(C::Source);}
        if raw.len()%2!=0||!raw.starts_with(&[0xff,0xfe]){return Err(C::Encoding);}
        let units:Vec<_>=raw[2..].chunks_exact(2).map(|p|u16::from_le_bytes([p[0],p[1]])).collect();let text=String::from_utf16(&units).map_err(|_|C::Encoding)?;
        if text.contains(['\0','\u{feff}']){return Err(C::Encoding);}
        let mut sections:Vec<Section>=Vec::new();let mut seen=BTreeSet::new();let mut total=0usize;let mut bytes=0usize;
        for line in text.split('\n'){
            let line=line.strip_suffix('\r').unwrap_or(line);if line.contains('\r'){return Err(C::Syntax);}
            let trimmed=line.trim();if trimmed.is_empty()||trimmed.starts_with([';','#']){continue;}
            if let Some(name)=line.strip_prefix('[').and_then(|s|s.strip_suffix(']')){
                let family=PersonalInfoCatalogFamily::parse(name).ok_or(C::Coverage)?;if !seen.insert(family){return Err(C::Syntax);}sections.push(Section{family,patterns:Vec::new()});continue;
            }
            let(key,pattern)=line.split_once('=').ok_or(C::Syntax)?;let section=sections.last_mut().ok_or(C::Syntax)?;
            if key!=format!("pattern{}",section.patterns.len())||pattern.is_empty()||pattern.chars().any(char::is_control){return Err(C::Syntax);}
            if pattern.len()>4096{return Err(C::Limit);}total=total.checked_add(1).filter(|n|*n<=PATTERNS_MAX).ok_or(C::Limit)?;
            bytes=bytes.checked_add(pattern.len()).filter(|n|*n<=PATTERN_TOTAL_MAX).ok_or(C::Limit)?;section.patterns.push(pattern.to_owned());
        }
        if seen.iter().filter(|&&f|f!=PersonalInfoCatalogFamily::UserDefined).count()!=10
            ||sections.iter().any(|s|s.patterns.is_empty()&&s.family!=PersonalInfoCatalogFamily::UserDefined){return Err(C::Coverage);}
        let receipt=PersonalInfoCatalogReceipt{profile:PERSONAL_INFO_CATALOG_PROFILE,source_sha256:expected,source_bytes:raw.len(),total_patterns:total,
            source_section_order:sections.iter().map(|s|PersonalInfoCatalogSection{family:s.family,patterns:s.patterns.len()}).collect(),original_pattern_text_preserved:true,
            installed_vendor_authenticity_or_native_semantics_qualified:false};Ok(Self{sections,receipt})
    }
    #[must_use]pub const fn receipt(&self)->&PersonalInfoCatalogReceipt{&self.receipt}
    /// # Errors
    /// Fresh complete configuration identity; caller-provided bytes are not trusted defaults or service authority.
    pub fn verify_source(&self,raw:&[u8])->Result<(),C>{if raw.len()!=self.receipt.source_bytes||<[u8;32]>::from(Sha256::digest(raw))!=self.receipt.source_sha256{return Err(C::Source);}Ok(())}
    /// # Errors
    /// Metadata only, no regex bodies. The parser's whole source hash binds the original section/pattern order.
    pub fn canonical_json(&self)->Result<Vec<u8>,C>{json(&self.receipt,32*1024)}
    /// # Errors
    /// Every pattern in selected families is compiled unchanged. No first16/4KiB truncation or fallback pattern.
    pub fn prepare(&self,families:&[PersonalInfoCatalogFamily],limits:SourceSearchLimits)->Result<PreparedPersonalInfoCatalog,C>{
        let selected:BTreeSet<_>=families.iter().copied().collect();if selected.is_empty()||selected.len()!=families.len()
            ||selected.iter().any(|f|!self.sections.iter().any(|s|s.family==*f)){return Err(C::Selection);}
        let mut bindings=Vec::new();let mut parts=Vec::new();let mut source_bytes=0usize;
        for section in &self.sections{if !selected.contains(&section.family){continue;}
            for(i,raw)in section.patterns.iter().enumerate(){
                let expression=builder(raw,limits).build().map_err(|_|C::Pattern)?;if expression.is_match(""){return Err(C::Pattern);}
                source_bytes=source_bytes.checked_add(raw.len()).filter(|n|*n<=PATTERN_TOTAL_MAX).ok_or(C::Limit)?;
                parts.push(format!("(?P<p09cat{}>(?:{}))",bindings.len(),raw));bindings.push((section.family,i));
            }
        }
        let pattern=parts.join("|");if pattern.len()>COMBINED_MAX||bindings.len()>PATTERNS_MAX{return Err(C::Limit);}
        let expression=if bindings.is_empty(){None}else{Some(builder(&pattern,limits).build().map_err(|_|C::Pattern)?)};
        let request_sha=hash(&(PERSONAL_INFO_CATALOG_PROFILE,&self.receipt,&selected,"source_file_order_leftmost_nonoverlapping_unchanged_patterns")).map_err(C::Search)?;
        Ok(PreparedPersonalInfoCatalog{expression,bindings,receipt:self.receipt.clone(),request_sha,pattern_budget:limits.0.pattern_bytes,dfa_budget:limits.0.dfa_bytes,
            selected_families:selected.into_iter().collect(),selected_pattern_bytes:source_bytes})
    }
}
fn builder(pattern:&str,limits:SourceSearchLimits)->RegexBuilder{let mut b=RegexBuilder::new(pattern);b.unicode(true).case_insensitive(false).size_limit(limits.0.pattern_bytes).dfa_size_limit(limits.0.dfa_bytes).nest_limit(128);b}
pub struct PreparedPersonalInfoCatalog{expression:Option<regex::Regex>,bindings:Vec<(PersonalInfoCatalogFamily,usize)>,receipt:PersonalInfoCatalogReceipt,request_sha:[u8;32],
    pattern_budget:usize,dfa_budget:usize,selected_families:Vec<PersonalInfoCatalogFamily>,selected_pattern_bytes:usize}
impl fmt::Debug for PreparedPersonalInfoCatalog{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedPersonalInfoCatalog(<redacted>; unchanged_source_patterns_not_native_semantics)")}}
impl PreparedPersonalInfoCatalog{
    #[must_use]pub const fn request_sha256(&self)->[u8;32]{self.request_sha}
    #[must_use]pub const fn catalog_receipt(&self)->&PersonalInfoCatalogReceipt{&self.receipt}
    #[must_use]pub fn selected_pattern_count(&self)->usize{self.bindings.len()}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]pub struct PersonalInfoCatalogMatch{pub occurrence_index:usize,pub family:PersonalInfoCatalogFamily,pub source_pattern_index:usize}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]pub struct PersonalInfoCatalogResult{
    profile:&'static str,catalog:PersonalInfoCatalogReceipt,policy_sha256:[u8;32],selected_families:Vec<PersonalInfoCatalogFamily>,selected_patterns:usize,selected_pattern_bytes:usize,
    matching_policy:&'static str,matches:Vec<PersonalInfoCatalogMatch>,search:SourceReviewSelectorResult,
    native_defaults_identity_or_execution_qualified:bool,whole_package_personal_data_removed:bool,#[serde(skip)]maximum:usize,
}
impl PersonalInfoCatalogResult{
    #[must_use]pub const fn search(&self)->&SourceReviewSelectorResult{&self.search}
    #[must_use]pub const fn catalog_receipt(&self)->&PersonalInfoCatalogReceipt{&self.catalog}
    #[must_use]pub const fn policy_sha256(&self)->[u8;32]{self.policy_sha256}
    #[must_use]pub const fn selected_pattern_count(&self)->usize{self.selected_patterns}
    #[must_use]pub fn matches(&self)->&[PersonalInfoCatalogMatch]{&self.matches}
    /// # Errors
    /// Bounded full source/selection/pattern provenance and original coordinates, without source values or regex bodies.
    pub fn canonical_json(&self)->Result<Vec<u8>,C>{json(self,self.maximum)}
    /// # Errors
    /// Retained result navigation, never matching again or granting execution authority.
    pub fn navigate(&self,request:&navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<navigation::SourceSearchNavigationResult,C>{
        Ok(self.search.navigate(request,hash(&(PERSONAL_INFO_CATALOG_PROFILE,self.policy_sha256,context))?)?)
    }
    /// # Errors
    /// Exact original coordinates only. A later writer must freshly check source, exact mapping and protection.
    pub fn selection(&self,index:usize)->Result<PersonalInfoCatalogSelection,C>{
        let found=self.search.result().matches().get(index).ok_or(C::Selection)?;if found.zero_width||!found.source_scalar_selection_exact{return Err(C::Selection);}
        let label=self.matches.get(index).filter(|m|m.occurrence_index==index).ok_or(C::Selection)?;
        let cut=|normalized_scalar|SourceIndexBoundary{paragraph_handle:found.paragraph_anchor.opaque_handle.clone(),block_index:found.block_index,normalized_scalar};
        Ok(PersonalInfoCatalogSelection{source_package_sha256:self.search.result().index_receipt().source_package_sha256,index_sha256:self.search.result().index_receipt().index_sha256,
            request_sha256:self.search.request_sha256(),label:label.clone(),start:cut(found.start_normalized_scalar),end:cut(found.end_normalized_scalar)})
    }
}
#[derive(Clone,Eq,PartialEq,Serialize)]pub struct PersonalInfoCatalogSelection{source_package_sha256:[u8;32],index_sha256:[u8;32],request_sha256:[u8;32],label:PersonalInfoCatalogMatch,start:SourceIndexBoundary,end:SourceIndexBoundary}
impl fmt::Debug for PersonalInfoCatalogSelection{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PersonalInfoCatalogSelection(<redacted>; coordinates_not_authority)")}}
impl PersonalInfoCatalogSelection{#[must_use]pub fn scope(&self)->SourceIndexScopeSelector<'_>{SourceIndexScopeSelector::Selection{index_sha256:self.index_sha256,start:&self.start,end:&self.end}}}
struct CatalogLabels{indices:Vec<usize>,matched:Vec<usize>,count:usize,maximum:usize}
impl captures::CaptureSink for CatalogLabels{
    fn compiled(&mut self,expression:&regex::Regex)->Result<(),SourceSearchError>{
        let names:BTreeMap<_,_>=expression.capture_names().enumerate().filter_map(|(i,n)|n.map(|n|(n,i))).collect();
        for i in 0..self.count{self.indices.push(*names.get(format!("p09cat{i}").as_str()).ok_or(E::Pattern)?);}Ok(())
    }
    fn matched(&mut self,captures:&regex::Captures<'_>)->Result<(),SourceSearchError>{
        let whole=captures.get(0).filter(|m|m.start()!=m.end()).ok_or(E::Pattern)?;let mut selected=None;
        for(i,&group)in self.indices.iter().enumerate(){if let Some(found)=captures.get(group){if selected.is_some()||found.range()!=whole.range(){return Err(E::Mapping);}selected=Some(i);}}
        if self.matched.len()>=self.maximum{return Err(E::Limit);}self.matched.push(selected.ok_or(E::Mapping)?);Ok(())
    }
}
impl SourceReviewScopeIndex<'_>{
    /// # Errors
    /// The complete selected source catalog uses one existing review index and one shared finite scan, with unchanged source regex syntax.
    pub fn find_personal_info_catalog(&self,policy:&PreparedPersonalInfoCatalog,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy)->Result<PersonalInfoCatalogResult,C>{
        let limits=self.source_index().limits;if policy.pattern_budget>limits.0.pattern_bytes||policy.dfa_budget>limits.0.dfa_bytes{return Err(C::Limit);}
        let mut labels=CatalogLabels{indices:Vec::with_capacity(policy.bindings.len()),matched:Vec::new(),count:policy.bindings.len(),maximum:limits.0.matches};
        let search=self.find_precompiled_catalog(policy.expression.as_ref(),policy.request_sha,selector,body,&mut labels)?;
        if labels.matched.len()!=search.result().matches().len(){return Err(C::Selection);}
        let matches=labels.matched.into_iter().enumerate().map(|(occurrence_index,i)|PersonalInfoCatalogMatch{occurrence_index,family:policy.bindings[i].0,source_pattern_index:policy.bindings[i].1}).collect();
        let result=PersonalInfoCatalogResult{profile:"hwpx-agent.source-personal-info-catalog-result/v1",catalog:policy.receipt.clone(),policy_sha256:policy.request_sha,
            selected_families:policy.selected_families.clone(),selected_patterns:policy.bindings.len(),selected_pattern_bytes:policy.selected_pattern_bytes,
            matching_policy:"source_file_order_leftmost_nonoverlapping_unchanged_patterns",matches,search,native_defaults_identity_or_execution_qualified:false,whole_package_personal_data_removed:false,maximum:limits.0.result_bytes};
        let mut count=Output{bytes:None,length:0,maximum:result.maximum};serde_json::to_writer(&mut count,&result).map_err(|_|C::Limit)?;Ok(result)
    }
}
fn json(value:&impl Serialize,maximum:usize)->Result<Vec<u8>,C>{let mut out=Output{bytes:Some(Vec::new()),length:0,maximum};serde_json::to_writer(&mut out,value).map_err(|_|C::Limit)?;out.bytes.ok_or(C::Limit)}
