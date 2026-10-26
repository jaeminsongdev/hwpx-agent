//! Fixed new private staging evidence only; no public output or revision adoption.
#[path="../tests/stored_bookmark_insertion628.rs"]
#[allow(dead_code,unused_imports)]mod fixed;
fn main(){
    let result=(||->fixed::Result{
        fixed::require(std::env::args().skip(1).collect::<Vec<_>>()==["--fixed-eight-private-stage-once"])?;
        let root=std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../implementation/p09/evidence/private/p09-361-local-stage720-generated001");
        let raw=serde_json::to_vec(&fixed::fixed_local_stage719(&root)?)?;fixed::require(raw.len()<=32768)?;
        println!("{}",std::str::from_utf8(&raw)?);Ok(())
    })();
    if result.is_err(){eprintln!("P720_PRIVATE_LOCAL_STAGE_REJECTED_NO_RAW_VALUES");std::process::exit(2);}
}
