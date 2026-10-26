//! Fixed read-only result semantics for already captured32 files. Never starts Native.
#[path="../tests/bookmark_results728.rs"]
#[allow(dead_code,unused_imports)]
mod fixed;
fn main(){
    if std::env::args().skip(1).collect::<Vec<_>>()!=["--existing32-source-result-oracles-only"]{
        eprintln!("P729_MODE_REJECTED");std::process::exit(2);
    }
    match fixed::observation(){Ok(v)=>println!("{v}"),Err(_)=>{eprintln!("P729_RESULT_SEMANTICS_CHECK_FAILED");std::process::exit(2);}}
}
