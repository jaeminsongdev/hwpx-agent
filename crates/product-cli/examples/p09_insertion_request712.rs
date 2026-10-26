//! Fixed actual source through strict owned/common request with isolated service fixtures.
#[path="../tests/stored_bookmark_insertion628.rs"]
#[allow(dead_code,unused_imports)]
mod fixed;
fn main(){
    let result=(||->fixed::Result{
        fixed::require(std::env::args().skip(1).collect::<Vec<_>>()==["--actual-eight-owned-request-readonly"])?;
        let raw=serde_json::to_vec(&fixed::fixed_insertion_request711()?)?;fixed::require(raw.len()<=32768)?;
        println!("{}",std::str::from_utf8(&raw)?);Ok(())
    })();
    if result.is_err(){eprintln!("P712_INSERTION_REQUEST_REJECTED_NO_RAW_VALUES");std::process::exit(2);}
}
