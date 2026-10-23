//! One pure predicate's last selected definition pair; operation-local and allocation-free.
use std::cell::Cell;
pub(super) struct LastPredicate<K:Copy+Eq> {previous:Cell<Option<(K,bool)>>}
impl<K:Copy+Eq> Default for LastPredicate<K> {fn default()->Self {Self {previous:Cell::new(None)}}}
impl<K:Copy+Eq> LastPredicate<K> {
    pub(super) fn test(&self,key:K,evaluate:impl FnOnce()->bool)->bool {
        if let Some((previous,value))=self.previous.get()&&previous==key{return value;}
        let value=evaluate();self.previous.set(Some((key,value)));value
    }
}
