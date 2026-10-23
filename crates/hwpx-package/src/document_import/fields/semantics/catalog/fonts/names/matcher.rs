//! Shared bounded declared-name matcher; replacement and search choose their own zero-width policy.
use super::FontNameResolutionError as E;
use regex::{Regex,RegexBuilder};

pub(in crate::document_import) fn declared_matcher(query:&str,is_regex:bool,case_sensitive:bool,whole_word:bool,
    query_bytes:usize,pattern_bytes:usize,dfa_bytes:usize)->Result<Regex,E> {
    if query_bytes==0||pattern_bytes==0||dfa_bytes==0||query.len()>query_bytes.min(4096){return Err(E::Limit);}
    if query.is_empty()||query.chars().any(char::is_control){return Err(E::Pattern);}
    let pattern=if is_regex{query.to_owned()}else{regex::escape(query)};
    let pattern=if whole_word{format!(r"\b(?:{pattern})\b")}else{pattern};
    RegexBuilder::new(&pattern).case_insensitive(!case_sensitive).size_limit(pattern_bytes.min(1024*1024))
        .dfa_size_limit(dfa_bytes.min(1024*1024)).build().map_err(|_|E::Pattern)
}
