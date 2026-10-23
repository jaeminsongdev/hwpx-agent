//! Sparse readback oracle, shared verbatim with its focused tamper test, not the patch renderer.
use std::ops::Range;
pub(crate) struct LexicalEdit {pub(crate) old:Range<usize>,pub(crate) output:Vec<u8>}
pub(crate) fn verify(old:&[u8],new:&[u8],edits:&[&LexicalEdit])->Result<(),()>{
    let(mut before,mut after)=(0usize,0usize);
    for e in edits{
        if e.old.start<before||e.old.end<e.old.start||e.old.end>old.len(){return Err(());}
        let untouched=e.old.start-before;let end=after.checked_add(untouched).ok_or(())?;
        if old.get(before..e.old.start)!=new.get(after..end){return Err(());}after=end;
        let end=after.checked_add(e.output.len()).ok_or(())?;
        if new.get(after..end)!=Some(e.output.as_slice()){return Err(());}after=end;before=e.old.end;
    }
    if old.get(before..)!=new.get(after..){return Err(());}Ok(())
}
