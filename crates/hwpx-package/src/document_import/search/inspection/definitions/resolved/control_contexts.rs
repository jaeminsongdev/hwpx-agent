//! Selected-ancestor closure, with the original linear pass for dense/large closures.
//! This changes work performed, not namespace, inheritance or unresolved-axis rules.
use std::collections::{BTreeMap,BTreeSet,HashMap};
use crate::XmlElementToken;
use super::E;

fn local(node:&XmlElementToken)->bool {
    node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)&&node.name().local_name()=="ctrl"
        &&node.attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()=="charStyleIDRef")
}

// Values never leave this calculation or affect canonical ordering. The sparse
// cache is capped before allocation can grow to the size of the entire part.
struct Ancestors {values:HashMap<usize,bool>,budget:usize}
impl Ancestors {
    fn new(budget:usize)->Self {Self {values:HashMap::new(),budget}}
    fn observe(&mut self,elements:&[XmlElementToken],index:usize)->Result<Option<bool>,E> {
        let mut pending=Vec::new();let mut cursor=index;
        let mut inherited=loop {
            if let Some(&known)=self.values.get(&cursor){break known;}
            let node=elements.get(cursor).ok_or(E::Mapping)?;
            if self.values.len().saturating_add(pending.len())>=self.budget{return Ok(None);}
            pending.push(cursor);
            match node.parent(){Some(parent)if parent<cursor=>cursor=parent,Some(_)=>return Err(E::Mapping),None=>break false}
        };
        for index in pending.into_iter().rev() {
            inherited|=local(elements.get(index).ok_or(E::Mapping)?);
            self.values.insert(index,inherited);
        }
        Ok(Some(inherited))
    }
}

fn linear(elements:&[XmlElementToken],selected:&BTreeMap<usize,usize>)->Result<BTreeSet<usize>,E> {
    let mut selected=selected.iter().peekable();let mut inherited=Vec::with_capacity(elements.len());let mut uncertain=BTreeSet::new();
    for (i,node) in elements.iter().enumerate() {
        let parent=match node.parent(){Some(p)=>*inherited.get(p).ok_or(E::Mapping)?,None=>false};
        let unresolved=parent||local(node);inherited.push(unresolved);
        if selected.peek().is_some_and(|(element,_)|**element==i) {
            let(_,segment)=selected.next().ok_or(E::Mapping)?;if unresolved{uncertain.insert(*segment);}
        }
    }
    if selected.next().is_some(){return Err(E::Mapping);}Ok(uncertain)
}

pub(super) fn collect(elements:&[XmlElementToken],selected:&BTreeMap<usize,usize>)->Result<BTreeSet<usize>,E> {
    if selected.is_empty(){return Ok(BTreeSet::new());}
    let budget=(elements.len()/8).max(32).min(elements.len());
    if selected.len()>budget/2{return linear(elements,selected);}
    let mut ancestors=Ancestors::new(budget);let mut uncertain=BTreeSet::new();
    for (&element,&segment) in selected {
        match ancestors.observe(elements,element)? {
            Some(true)=>{uncertain.insert(segment);},Some(false)=>{},
            None=>return linear(elements,selected),
        }
    }
    Ok(uncertain)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::PreservingXmlDocument;
    type TestResult=Result<(),Box<dyn std::error::Error>>;
    fn xml(body:&str)->Result<PreservingXmlDocument,crate::PreservingXmlError> {
        PreservingXmlDocument::parse(format!("<hp:root xmlns:hp='{}' xmlns:other='urn:other'>{body}</hp:root>",crate::HANCOM_2020_PARAGRAPH_NAMESPACE).as_bytes())
    }
    #[test]
    fn p581_context_all_selected_subsets_equal_original_linear()->TestResult {
        let doc=xml("<hp:t/><hp:ctrl charStyleIDRef='0'><hp:t/><hp:ctrl><hp:t/></hp:ctrl></hp:ctrl><hp:t/><other:ctrl charStyleIDRef='0'><hp:t/></other:ctrl><hp:ctrl other:charStyleIDRef='0'><hp:t/></hp:ctrl>")?;
        let text:Vec<_>=doc.elements().iter().enumerate().filter(|(_,e)|e.name().local_name()=="t").map(|(i,_)|i).collect();
        for mask in 0..(1usize<<text.len()) {
            let selected=text.iter().enumerate().filter(|(bit,_)|mask&(1<<bit)!=0).map(|(_,i)|(*i,100+i)).collect();
            assert_eq!(collect(doc.elements(),&selected)?,linear(doc.elements(),&selected)?);
        }Ok(())
    }
    #[test]
    fn p581_context_sparse_selection_visits_only_ancestors()->TestResult {
        let mut body="<hp:p><hp:run><hp:t/></hp:run></hp:p>".repeat(4000);
        body.push_str("<hp:ctrl charStyleIDRef='0'><hp:p><hp:run><hp:t/><hp:t/></hp:run></hp:p></hp:ctrl>");
        let doc=xml(&body)?;let elements=doc.elements();
        let text:Vec<_>=elements.iter().enumerate().filter(|(_,e)|e.name().local_name()=="t").map(|(i,_)|i).collect();
        let mut ancestors=Ancestors::new(elements.len()/8);
        assert_eq!(ancestors.observe(elements,text[text.len()-2])?,Some(true));assert_eq!(ancestors.values.len(),5);
        assert_eq!(ancestors.observe(elements,text[text.len()-2])?,Some(true));assert_eq!(ancestors.values.len(),5);
        assert_eq!(ancestors.observe(elements,text[text.len()-1])?,Some(true));assert_eq!(ancestors.values.len(),6);
        assert!(elements.len()>12000);
        let selected=text[text.len()-2..].iter().map(|i|(*i,100+i)).collect();
        assert_eq!(collect(elements,&selected)?,linear(elements,&selected)?);Ok(())
    }
    #[test]
    fn p581_context_budget_exhaustion_and_dense_fallback_preserve_all_results()->TestResult {
        let doc=xml(&format!("{}<hp:ctrl charStyleIDRef='0'><hp:t/></hp:ctrl>{}","<hp:p>".repeat(40),"</hp:p>".repeat(40)))?;
        let elements=doc.elements();let index=elements.iter().position(|e|e.name().local_name()=="t").ok_or("text")?;
        let mut ancestors=Ancestors::new(2);assert_eq!(ancestors.observe(elements,index)?,None);assert!(ancestors.values.len()<=2);
        let sparse=BTreeMap::from([(index,9)]);assert_eq!(collect(elements,&sparse)?,linear(elements,&sparse)?);
        let dense=elements.iter().enumerate().map(|(i,_)|(i,100+i)).collect();
        assert_eq!(collect(elements,&dense)?,linear(elements,&dense)?);Ok(())
    }
    #[test]
    fn p581_context_namespace_siblings_and_invalid_selection_remain_fail_closed()->TestResult {
        let doc=xml("<hp:ctrl charStyleIDRef='0'><hp:t/></hp:ctrl><hp:t/><other:ctrl charStyleIDRef='0'><hp:t/></other:ctrl><hp:ctrl other:charStyleIDRef='0'><hp:t/></hp:ctrl>")?;
        let elements=doc.elements();let text:Vec<_>=elements.iter().enumerate().filter(|(_,e)|e.name().local_name()=="t").map(|(i,_)|i).collect();
        let selected=text.iter().enumerate().map(|(i,n)|(*n,i)).collect();assert_eq!(collect(elements,&selected)?,BTreeSet::from([0]));
        let invalid=BTreeMap::from([(elements.len(),0)]);
        assert!(matches!(collect(elements,&invalid),Err(E::Mapping)));assert!(matches!(linear(elements,&invalid),Err(E::Mapping)));Ok(())
    }
}
