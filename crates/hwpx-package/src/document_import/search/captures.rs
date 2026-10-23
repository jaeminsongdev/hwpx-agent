//! Optional operation-local capture sink; legacy matching keeps find_iter and allocates no capture set.
use super::SourceSearchError;
pub(super) trait CaptureSink {
    fn compiled(&mut self,expression:&regex::Regex)->Result<(),SourceSearchError>;
    fn matched(&mut self,captures:&regex::Captures<'_>)->Result<(),SourceSearchError>;
}
pub(super) enum Scanned<'h> {Plain(regex::Match<'h>),Captured(regex::Captures<'h>)}
impl<'h> Scanned<'h> {
    pub(super) fn whole(&self)->Option<regex::Match<'h>> {match self {Self::Plain(m)=>Some(*m),Self::Captured(c)=>c.get(0)}}
    pub(super) fn captures(&self)->Option<&regex::Captures<'h>> {match self {Self::Plain(_)=>None,Self::Captured(c)=>Some(c)}}
}
pub(super) enum Scan<'r,'h> {Plain(regex::Matches<'r,'h>),Captured(regex::CaptureMatches<'r,'h>)}
impl<'h> Iterator for Scan<'_,'h> {
    type Item=Scanned<'h>;
    fn next(&mut self)->Option<Self::Item> {match self {Self::Plain(i)=>i.next().map(Scanned::Plain),Self::Captured(i)=>i.next().map(Scanned::Captured)}}
}
pub(super) fn scan<'r,'h>(expression:&'r regex::Regex,window:&'h str,captured:bool)->Scan<'r,'h> {
    if captured{Scan::Captured(expression.captures_iter(window))}else{Scan::Plain(expression.find_iter(window))}
}
