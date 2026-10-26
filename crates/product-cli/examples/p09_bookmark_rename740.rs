#[path="../tests/bookmark_rename739.rs"]#[allow(dead_code,unused_imports)]mod fixed;
fn main(){
    if std::env::args().skip(1).collect::<Vec<_>>()!=["--fixed-eight-atomic-rename-once"]{eprintln!("P740_MODE_REJECTED");std::process::exit(2);}
    match fixed::observation(){Ok(v)=>println!("{v}"),Err(_)=>{eprintln!("P740_ATOMIC_RENAME_CHECK_FAILED");std::process::exit(2);}}
}
