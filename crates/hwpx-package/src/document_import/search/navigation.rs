//! Result-bound navigation; unsigned positions are selection coordinates, never authority.
use super::*;
use super::inspection::SourceControlMatch;
use super::reviews::SourceTextRegion;
use serde::Deserialize;
pub const SOURCE_SEARCH_NAVIGATION_PROFILE:&str="hwpx-agent.source-search-navigation/v1";
const CURSOR_PROFILE:&str="hwpx-agent.source-search-cursor/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceSearchDirection {Forward,Backward}
#[derive(Clone,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceSearchCursor {profile:String,binding_sha256:[u8;32],match_index:usize,occurrence_sha256:[u8;32]}
impl fmt::Debug for SourceSearchCursor {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceSearchCursor(<redacted>; not_authority)")}}
#[derive(Clone,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceSearchNavigationRequest {pub direction:SourceSearchDirection,pub wrap:bool,pub cursor:Option<SourceSearchCursor>}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
#[serde(tag="kind",content="match",rename_all="snake_case")]
pub enum SourceSearchNavigationSelection {Text(SourceSearchMatch),Control(SourceControlMatch)}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceSearchNavigationResult {
    profile:&'static str,binding_sha256:[u8;32],request_sha256:[u8;32],total_matches:usize,
    match_index:Option<usize>,selection:Option<SourceSearchNavigationSelection>,region:Option<SourceTextRegion>,
    cursor:Option<SourceSearchCursor>,wrapped:bool,exhausted:bool,full_search_native_or_execution_authority:bool,
    #[serde(skip)] output_limit:usize,
}
impl SourceSearchNavigationResult {
    #[must_use] pub fn cursor(&self)->Option<&SourceSearchCursor> {self.cursor.as_ref()}
    #[must_use] pub const fn match_index(&self)->Option<usize> {self.match_index}
    #[must_use] pub const fn exhausted(&self)->bool {self.exhausted}
    #[must_use] pub const fn wrapped(&self)->bool {self.wrapped}
    #[must_use] pub const fn selection(&self)->Option<&SourceSearchNavigationSelection> {self.selection.as_ref()}
    /// # Errors
    /// Bounds the entire selected occurrence and cursor response, without truncation.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {let mut out=Output {bytes:Some(Vec::new()),length:0,maximum:self.output_limit};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Output)?;out.bytes.ok_or(E::Output)}
}
pub(super) enum Occurrences<'a> {Text(&'a [SourceSearchMatch],Option<&'a [SourceTextRegion]>),Control(&'a [SourceControlMatch]),ControlRegions(&'a [SourceControlMatch],&'a [SourceTextRegion])}
impl Occurrences<'_> {
    fn len(&self)->usize {match self {Self::Text(m,_)=>m.len(),Self::Control(m)|Self::ControlRegions(m,_)=>m.len()}}
    fn occurrence_sha(&self,index:usize,maximum:usize)->Result<[u8;32],E> {match self {
        Self::Text(m,r)=>{let region=match r {Some(r)=>Some(r.get(index).ok_or(E::Mapping)?),None=>None};
            hash(&("text",m.get(index).ok_or(E::Cursor)?,region),maximum)},
        Self::Control(m)=>hash(&("control",m.get(index).ok_or(E::Cursor)?),maximum),
        Self::ControlRegions(m,r)=>hash(&("control_with_region",m.get(index).ok_or(E::Cursor)?,r.get(index).ok_or(E::Mapping)?),maximum)}}
    fn selection(&self,index:usize)->SourceSearchNavigationSelection {match self {
        Self::Text(m,_)=>SourceSearchNavigationSelection::Text(m[index].clone()),Self::Control(m)|Self::ControlRegions(m,_)=>SourceSearchNavigationSelection::Control(m[index].clone())}}
    fn region(&self,index:usize)->Option<SourceTextRegion> {match self {Self::Text(_,Some(r))|Self::ControlRegions(_,r)=>r.get(index).copied(),_=>None}}
}
struct HashWriter {sha:Sha256,length:usize,maximum:usize}
impl io::Write for HashWriter {
    fn write(&mut self,b:&[u8])->io::Result<usize> {self.length=self.length.checked_add(b.len()).filter(|n|*n<=self.maximum)
        .ok_or_else(||io::Error::other("navigation binding bound"))?;self.sha.update(b);Ok(b.len())}
    fn flush(&mut self)->io::Result<()> {Ok(())}
}
fn hash<T:Serialize>(value:&T,maximum:usize)->Result<[u8;32],E> {let mut out=HashWriter {sha:Sha256::new(),length:0,maximum};
    serde_json::to_writer(&mut out,value).map_err(|_|E::Output)?;Ok(out.sha.finalize().into())}
pub(super) fn navigate<T:Serialize>(original:&T,matches:Occurrences<'_>,maximum:usize,request:&SourceSearchNavigationRequest,context:[u8;32])->Result<SourceSearchNavigationResult,E> {
    if let Occurrences::ControlRegions(m,r)=&matches {if m.len()!=r.len(){return Err(E::Mapping);}}
    let count=matches.len();if let Occurrences::Text(m,Some(r))=&matches {if m.len()!=r.len(){return Err(E::Mapping);}}
    let binding_max=maximum.checked_add(1024).ok_or(E::Limit)?;
    let binding_sha256=hash(&(SOURCE_SEARCH_NAVIGATION_PROFILE,context,original),binding_max)?;
    if let Some(cursor)=&request.cursor {if cursor.profile!=CURSOR_PROFILE||cursor.binding_sha256!=binding_sha256||cursor.match_index>=count
        ||cursor.occurrence_sha256!=matches.occurrence_sha(cursor.match_index,maximum)? {return Err(E::Cursor);}}
    let mut wrapped=false;
    let next=if count==0 {None}else{match (&request.cursor,request.direction) {
        (None,SourceSearchDirection::Forward)=>Some(0),(None,SourceSearchDirection::Backward)=>Some(count-1),
        (Some(c),SourceSearchDirection::Forward) if c.match_index<count-1=>Some(c.match_index+1),
        (Some(c),SourceSearchDirection::Backward) if c.match_index>0=>Some(c.match_index-1),
        (Some(_),direction) if request.wrap=>{wrapped=true;Some(match direction {SourceSearchDirection::Forward=>0,SourceSearchDirection::Backward=>count-1})},
        _=>None}};
    let cursor=match next {Some(i)=>Some(SourceSearchCursor {profile:CURSOR_PROFILE.into(),binding_sha256,match_index:i,occurrence_sha256:matches.occurrence_sha(i,maximum)?}),
        None=>request.cursor.clone()};
    let result=SourceSearchNavigationResult {profile:SOURCE_SEARCH_NAVIGATION_PROFILE,binding_sha256,request_sha256:hash(&(binding_sha256,request),binding_max)?,
        total_matches:count,match_index:next,selection:next.map(|i|matches.selection(i)),region:next.and_then(|i|matches.region(i)),cursor,wrapped,
        exhausted:next.is_none(),full_search_native_or_execution_authority:false,output_limit:maximum};
    let mut out=Output {bytes:None,length:0,maximum};serde_json::to_writer(&mut out,&result).map_err(|_|E::Output)?;Ok(result)
}
