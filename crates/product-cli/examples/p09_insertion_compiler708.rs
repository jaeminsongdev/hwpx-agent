//! Fixed current block source through authenticated service fixtures and original compiler.
//! No Native, registry, CAS, durable result or source mutation.
#[path="../tests/stored_bookmark_insertion628.rs"]
#[allow(dead_code,unused_imports)]
mod fixed;
fn main(){
    let result=(||->fixed::Result{
        fixed::require(std::env::args().skip(1).collect::<Vec<_>>()==["--actual-eight-compiler-readonly"])?;
        let raw=serde_json::to_vec(&fixed::fixed_insertion_compiler708()?)?;fixed::require(raw.len()<=32768)?;
        println!("{}",std::str::from_utf8(&raw)?);Ok(())
    })();
    if result.is_err(){eprintln!("P708_COMPILED_INSERTION_REJECTED_NO_RAW_VALUES");std::process::exit(2);}
}
