//! Produce exactly eight private candidates through the current stored API.
#[path="../tests/stored_bookmark_insertion628.rs"]
#[allow(dead_code,unused_imports)]
mod fixed;
fn main(){
    let result=(||->fixed::Result{
        fixed::require(std::env::args().skip(1).collect::<Vec<_>>()==["--fixed-eight-private-candidates-once"])?;
        let value=fixed::fixed_block_output_batch681()?;let raw=serde_json::to_vec(&value)?;
        fixed::require(raw.len()<=32768)?;println!("{}",std::str::from_utf8(&raw)?);Ok(())
    })();
    if result.is_err(){eprintln!("BLOCK681_FIXED_STORED_GENERATION_FAILED_NO_RAW_VALUES");std::process::exit(2);}
}
