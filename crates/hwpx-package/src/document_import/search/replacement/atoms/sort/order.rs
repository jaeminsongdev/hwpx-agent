//! Fallible stable merge ordering with a finite byte-comparison budget, including equal/empty keys.
use super::{SourceParagraphSortSpec,SourceParagraphSortDirection,SourceParagraphSortError as E};
use std::cmp::Ordering;
pub(super) fn sort(keys:&[&str],spec:SourceParagraphSortSpec)->Result<(Vec<usize>,usize),E> {
    let n=keys.len();let mut order=Vec::new();order.try_reserve_exact(n).map_err(|_|E::ComparisonLimit)?;order.extend(0..n);
    let mut scratch=Vec::new();scratch.try_reserve_exact(n).map_err(|_|E::ComparisonLimit)?;scratch.resize(n,0);
    let mut width=1usize;let mut work=0usize;
    while width<n {
        let stride=width.checked_mul(2).ok_or(E::ComparisonLimit)?;
        for start in(0..n).step_by(stride){let middle=(start+width).min(n);let end=(start+stride).min(n);let(mut a,mut b)=(start,middle);
            for slot in &mut scratch[start..end] {
                let left=if a==middle{false}else if b==end{true}else{
                    let cmp=compare(keys[order[a]],keys[order[b]],&mut work,spec.max_comparison_bytes)?;
                    match spec.direction {SourceParagraphSortDirection::Ascending=>cmp!=Ordering::Greater,SourceParagraphSortDirection::Descending=>cmp!=Ordering::Less}
                };
                if left{*slot=order[a];a+=1;}else{*slot=order[b];b+=1;}
            }
        }std::mem::swap(&mut order,&mut scratch);width=stride;
    }Ok((order,work))
}
fn compare(a:&str,b:&str,work:&mut usize,maximum:usize)->Result<Ordering,E> {
    for i in 0..=a.len().min(b.len()) {
        *work=work.checked_add(1).filter(|n|*n<=maximum).ok_or(E::ComparisonLimit)?;
        match(a.as_bytes().get(i),b.as_bytes().get(i)){(Some(a),Some(b))if a==b=>{},(a,b)=>return Ok(a.cmp(&b))}
    }Ok(Ordering::Equal)
}
