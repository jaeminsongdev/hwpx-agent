//! Explicit personal-info format candidates, not identity validation, native defaults or document sanitization.
pub mod catalog;
use super::*;
use super::{reviews::{SourceReviewTextPolicy,selector::{SourceReviewScopeIndex,SourceReviewSelectorResult}},
    selector::{SourceIndexScopeSelector,SourceIndexBoundary}};
use serde::Deserialize;
use unicode_normalization::UnicodeNormalization as _;
pub const SOURCE_PERSONAL_INFO_DETECTION_PROFILE:&str="hwpx-agent.source-personal-info-format-candidates/v1";
const MAX_RULES:usize=16;
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourcePersonalInfoKind{Telephone,ResidentRegistration,ForeignRegistration,Email,Account,CreditCard,IpAddress,BirthDate,Address,Custom}
#[derive(Clone,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourcePersonalInfoRule{
    pub rule_id:String,pub kind:SourcePersonalInfoKind,pub query:String,pub regex:bool,pub case_sensitive:bool,pub whole_word:bool,
}
impl fmt::Debug for SourcePersonalInfoRule{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourcePersonalInfoRule(<redacted>)")}}
/// Rule order is explicit precedence for equal-start alternatives. Candidates are leftmost non-overlapping.
pub struct SourcePersonalInfoDetectionPolicy{rules:Vec<SourcePersonalInfoRule>,sha:[u8;32]}
impl fmt::Debug for SourcePersonalInfoDetectionPolicy{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourcePersonalInfoDetectionPolicy(<redacted>; explicit_formats_not_native_defaults)")}}
impl SourcePersonalInfoDetectionPolicy{
    /// # Errors
    /// No empty, duplicate or unbounded policy. Labels are safe ASCII identifiers, never copied matched values.
    pub fn new(rules:Vec<SourcePersonalInfoRule>)->Result<Self,E>{
        if rules.is_empty()||rules.len()>MAX_RULES{return Err(E::Limit);}
        let mut ids=BTreeSet::new();let mut bytes=0usize;
        for rule in &rules{
            if rule.rule_id.is_empty()||rule.rule_id.len()>64||!rule.rule_id.bytes().all(|b|b.is_ascii_alphanumeric()||b==b'_'||b==b'-')||!ids.insert(&rule.rule_id){return Err(E::Filter);}
            bytes=bytes.checked_add(rule.query.len()).filter(|n|*n<=4096).ok_or(E::Limit)?;
            if rule.query.is_empty(){return Err(E::Pattern);}
        }
        let sha=hash(&(SOURCE_PERSONAL_INFO_DETECTION_PROFILE,"leftmost_then_rule_order_nonoverlapping",&rules))?;
        Ok(Self{rules,sha})
    }
    #[must_use]pub const fn canonical_sha256(&self)->[u8;32]{self.sha}
    fn expression(&self,limits:SourceSearchLimits)->Result<String,E>{
        let mut parts=Vec::with_capacity(self.rules.len());let mut bytes=0usize;
        for(i,rule)in self.rules.iter().enumerate(){
            bytes=bytes.checked_add(rule.query.len()).filter(|n|*n<=limits.0.query_bytes).ok_or(E::Limit)?;
            let raw=if rule.regex{rule.query.clone()}else{regex::escape(&rule.query.nfc().collect::<String>())};
            let raw=if rule.whole_word{format!(r"\b(?:{raw})\b")}else{raw};
            // Validate each isolated expression before adding wrappers: flags/groups cannot escape a rule.
            let checked=RegexBuilder::new(&raw).unicode(true).case_insensitive(!rule.case_sensitive)
                .size_limit(limits.0.pattern_bytes).dfa_size_limit(limits.0.dfa_bytes).nest_limit(128).build().map_err(|_|E::Pattern)?;
            if checked.is_match(""){return Err(E::Pattern);}
            let raw=format!("(?P<p09pi{i}>(?{}:{raw}))",if rule.case_sensitive{"-i"}else{"i"});
            parts.push(raw);
        }
        let pattern=parts.join("|");if pattern.len()>limits.0.query_bytes{return Err(E::Limit);}Ok(pattern)
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourcePersonalInfoRuleMatch{pub occurrence_index:usize,pub rule_id:String,pub kind:SourcePersonalInfoKind}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourcePersonalInfoDetectionResult{
    profile:&'static str,policy_sha256:[u8;32],request_sha256:[u8;32],rule_count:usize,
    matching_policy:&'static str,rule_matches:Vec<SourcePersonalInfoRuleMatch>,search:SourceReviewSelectorResult,
    personal_identity_or_native_format_validated:bool,whole_package_personal_data_removed:bool,mutation_or_execution_authority:bool,
    #[serde(skip)]maximum:usize,
}
impl SourcePersonalInfoDetectionResult{
    #[must_use]pub const fn request_sha256(&self)->[u8;32]{self.request_sha256}
    #[must_use]pub const fn search(&self)->&SourceReviewSelectorResult{&self.search}
    #[must_use]pub fn rule_matches(&self)->&[SourcePersonalInfoRuleMatch]{&self.rule_matches}
    /// # Errors
    /// Whole bounded metadata only, not matched text, regexes or per-value hashes.
    pub fn canonical_json(&self)->Result<Vec<u8>,E>{let mut out=Output{bytes:Some(Vec::new()),length:0,maximum:self.maximum};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Output)?;out.bytes.ok_or(E::Output)}
    /// # Errors
    /// Navigates the retained original match set; no rematching, package import or mutation.
    pub fn navigate(&self,request:&navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<navigation::SourceSearchNavigationResult,E>{
        self.search.navigate(request,hash(&(SOURCE_PERSONAL_INFO_DETECTION_PROFILE,self.request_sha256,context))?)
    }
    /// # Errors
    /// Only an exact nonempty original mapping can produce a selection. The consumer still revalidates source and protection.
    pub fn selection(&self,occurrence_index:usize)->Result<SourcePersonalInfoDetectionSelection,E>{
        let found=self.search.result().matches().get(occurrence_index).ok_or(E::Scope)?;
        if found.zero_width||!found.source_scalar_selection_exact{return Err(E::Scope);}
        let label=self.rule_matches.get(occurrence_index).filter(|r|r.occurrence_index==occurrence_index).ok_or(E::Mapping)?;
        let boundary=|normalized_scalar|SourceIndexBoundary{paragraph_handle:found.paragraph_anchor.opaque_handle.clone(),block_index:found.block_index,normalized_scalar};
        Ok(SourcePersonalInfoDetectionSelection{request_sha256:self.request_sha256,source_package_sha256:self.search.result().index_receipt().source_package_sha256,
            index_sha256:self.search.result().index_receipt().index_sha256,start:boundary(found.start_normalized_scalar),end:boundary(found.end_normalized_scalar),label:label.clone()})
    }
}
/// Coordinates, not an execution permit. No Deserialize or file/output API is provided.
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct SourcePersonalInfoDetectionSelection{request_sha256:[u8;32],source_package_sha256:[u8;32],index_sha256:[u8;32],start:SourceIndexBoundary,end:SourceIndexBoundary,label:SourcePersonalInfoRuleMatch}
impl fmt::Debug for SourcePersonalInfoDetectionSelection{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourcePersonalInfoDetectionSelection(<redacted>; coordinates_not_authority)")}}
impl SourcePersonalInfoDetectionSelection{
    #[must_use]pub fn scope(&self)->SourceIndexScopeSelector<'_>{SourceIndexScopeSelector::Selection{index_sha256:self.index_sha256,start:&self.start,end:&self.end}}
    #[must_use]pub const fn source_package_sha256(&self)->[u8;32]{self.source_package_sha256}
    #[must_use]pub const fn request_sha256(&self)->[u8;32]{self.request_sha256}
}
struct Labels{groups:Vec<usize>,matches:Vec<usize>,count:usize,maximum:usize}
impl captures::CaptureSink for Labels{
    fn compiled(&mut self,expression:&regex::Regex)->Result<(),E>{
        for i in 0..self.count{let name=format!("p09pi{i}");self.groups.push(expression.capture_names().position(|n|n==Some(name.as_str())).ok_or(E::Pattern)?);}Ok(())
    }
    fn matched(&mut self,captures:&regex::Captures<'_>)->Result<(),E>{
        let whole=captures.get(0).filter(|m|m.start()!=m.end()).ok_or(E::Pattern)?;
        let mut selected=None;
        for(i,&group)in self.groups.iter().enumerate(){if let Some(found)=captures.get(group){
            if selected.is_some()||found.range()!=whole.range(){return Err(E::Mapping);}selected=Some(i);
        }}
        if self.matches.len()>=self.maximum{return Err(E::Limit);}self.matches.push(selected.ok_or(E::Mapping)?);Ok(())
    }
}
impl SourceReviewScopeIndex<'_>{
    /// # Errors
    /// One original review index and one combined match scan. Explicit rule formats do not assert real identity or native equivalence.
    pub fn find_personal_info_candidates(&self,policy:&SourcePersonalInfoDetectionPolicy,selector:SourceIndexScopeSelector<'_>,review_policy:SourceReviewTextPolicy)->Result<SourcePersonalInfoDetectionResult,E>{
        let limits=self.source_index().limits;let pattern=policy.expression(limits)?;
        let mut labels=Labels{groups:Vec::with_capacity(policy.rules.len()),matches:Vec::new(),count:policy.rules.len(),maximum:limits.0.matches};
        let search=self.find_with_captures(SourceSearchQuery{query:&pattern,mode:SourceSearchMode::Regex,case_sensitive:true,whole_word:false,max_results:limits.0.matches},selector,review_policy,Some(&mut labels))?;
        if labels.matches.len()!=search.result().matches().len(){return Err(E::Mapping);}
        let rule_matches=labels.matches.into_iter().enumerate().map(|(occurrence_index,i)|{
            let rule=&policy.rules[i];SourcePersonalInfoRuleMatch{occurrence_index,rule_id:rule.rule_id.clone(),kind:rule.kind}
        }).collect();
        let request_sha256=hash(&(SOURCE_PERSONAL_INFO_DETECTION_PROFILE,policy.sha,search.request_sha256()))?;
        let result=SourcePersonalInfoDetectionResult{profile:SOURCE_PERSONAL_INFO_DETECTION_PROFILE,policy_sha256:policy.sha,request_sha256,rule_count:policy.rules.len(),
            matching_policy:"leftmost_then_rule_order_nonoverlapping",rule_matches,search,personal_identity_or_native_format_validated:false,
            whole_package_personal_data_removed:false,mutation_or_execution_authority:false,maximum:limits.0.result_bytes};
        let mut count=Output{bytes:None,length:0,maximum:result.maximum};serde_json::to_writer(&mut count,&result).map_err(|_|E::Output)?;Ok(result)
    }
}
fn hash(value:&impl Serialize)->Result<[u8;32],E>{
    struct Hash{sha:Sha256,length:usize}
    impl io::Write for Hash{fn write(&mut self,b:&[u8])->io::Result<usize>{self.length=self.length.checked_add(b.len()).filter(|n|*n<=4*1024*1024).ok_or_else(||io::Error::other("personal_info_detection_binding_limit"))?;
        self.sha.update(b);Ok(b.len())}fn flush(&mut self)->io::Result<()>{Ok(())}}
    let mut out=Hash{sha:Sha256::new(),length:0};serde_json::to_writer(&mut out,value).map_err(|_|E::Output)?;Ok(out.sha.finalize().into())
}
