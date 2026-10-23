//! Explicit dollar grammar; bad or unknown references fail instead of silently becoming empty text.
use super::*;
use crate::document_import::search::captures::CaptureSink;
enum Token<'a> {Literal(&'a str),Reference(&'a str)}
enum Resolved<'a> {Literal(&'a str),Group(usize)}
pub(super) struct Collector<'a> {tokens:Vec<Token<'a>>,resolved:Vec<Resolved<'a>>,values:Vec<String>,bytes:usize,maximum:usize,work:usize,max_work:usize,error:Option<R>}
/// # Errors
/// Validates syntax, text and the original per-value byte ceiling. Group existence is checked
/// against the one compiled regex before scanning any selected block, even if it has no matches.
pub fn validate_regex_replacement_template(value:&str)->Result<(),SourceRegexReplacementError> {parse(value).map(|_|())}
fn parse(value:&str)->Result<Vec<Token<'_>>,R> {
    validate_literal_replacement(value).map_err(|e|if e==E::Limit{R::Limit}else{R::Template})?;
    let mut tokens=Vec::new();let bytes=value.as_bytes();let(mut i,mut literal)=(0,0);
    while i<bytes.len() {
        if bytes[i]!=b'$'{i+=1;continue;}
        if literal<i{tokens.push(Token::Literal(&value[literal..i]));}i+=1;
        if bytes.get(i)==Some(&b'$'){tokens.push(Token::Literal("$"));i+=1;}
        else if bytes.get(i)==Some(&b'{') {let start=i+1;let relative=value[start..].find('}').ok_or(R::Template)?;let end=start+relative;
            if start==end{return Err(R::Template);}tokens.push(Token::Reference(&value[start..end]));i=end+1;}
        else {let start=i;while i<bytes.len()&&(bytes[i].is_ascii_alphanumeric()||bytes[i]==b'_'){i+=1;}
            if start==i{return Err(R::Template);}tokens.push(Token::Reference(&value[start..i]));}
        literal=i;
    }
    if literal<value.len(){tokens.push(Token::Literal(&value[literal..]));}Ok(tokens)
}
impl<'a> Collector<'a> {
    pub(super) fn new(value:&'a str,limits:SourceSearchLimits)->Result<Self,R> {
        let tokens=parse(value)?;let work=tokens.len();let max_work=limits.0.decomposed_scalars;if work>max_work{return Err(R::Limit);}
        Ok(Self {tokens,resolved:Vec::new(),values:Vec::new(),bytes:0,maximum:limits.0.result_bytes,work,max_work,error:None})
    }
    pub(super) fn work_counters(&self)->(usize,usize) {(self.work,self.max_work)}
    pub(super) fn error(&self,error:SourceSearchError)->R {self.error.unwrap_or(R::Search(error))}
    fn reject<T>(&mut self,error:R)->Result<T,SourceSearchError> {self.error=Some(error);Err(SourceSearchError::Filter)}
    pub(super) fn expansions(&self)->RegexExpansions<'_> {let mut sha=Sha256::new();sha.update(b"hwpx-agent.regex-expansion-sequence/v1");sha.update((self.values.len()as u64).to_le_bytes());
        for value in &self.values {sha.update((value.len()as u64).to_le_bytes());sha.update(value.as_bytes());}
        RegexExpansions {values:&self.values,sha256:sha.finalize().into(),bytes:self.bytes}}
}
impl CaptureSink for Collector<'_> {
    fn compiled(&mut self,expression:&::regex::Regex)->Result<(),SourceSearchError> {
        let names:BTreeMap<_,_>=expression.capture_names().enumerate().filter_map(|(i,n)|n.map(|n|(n,i))).collect();
        let mut resolved=Vec::new();
        for token in &self.tokens {resolved.push(match token {Token::Literal(v)=>Resolved::Literal(v),Token::Reference(name)=>{
            let index=if name.bytes().all(|b|b.is_ascii_digit()){name.parse::<usize>().ok().filter(|n|*n<expression.captures_len())}else{names.get(name).copied()};
            let Some(index)=index else{return self.reject(R::Template)};Resolved::Group(index)}});}
        self.resolved=resolved;Ok(())
    }
    fn matched(&mut self,captures:&::regex::Captures<'_>)->Result<(),SourceSearchError> {
        // Empty optional captures consume work even when their output consumes zero bytes.
        let Some(work)=self.work.checked_add(self.resolved.len()).filter(|n|*n<=self.max_work) else{return self.reject(R::Limit)};self.work=work;
        let mut value=String::new();let maximum=PatchLimits::default().config().max_value_bytes.min(self.maximum.saturating_sub(self.bytes));
        for token in &self.resolved {let piece=match token {Resolved::Literal(v)=>*v,Resolved::Group(i)=>captures.get(*i).map_or("",|m|m.as_str())};
            if append(&mut value,piece,maximum).is_err(){return self.reject(R::Limit);}}
        if validate_literal_replacement(&value).is_err(){return self.reject(R::Template);}
        self.bytes=self.bytes.checked_add(value.len()).filter(|n|*n<=self.maximum).ok_or(SourceSearchError::Limit)?;
        self.values.push(value);Ok(())
    }
}
