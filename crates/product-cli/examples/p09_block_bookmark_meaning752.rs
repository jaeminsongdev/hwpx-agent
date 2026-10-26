#[path="../tests/block_bookmark_meaning751.rs"]#[allow(dead_code,unused_imports)]mod fixed;
fn main(){
    if std::env::args().skip(1).collect::<Vec<_>>()!=["--current-block-meanings-forty-no-native"]{eprintln!("P752_MODE_REJECTED");std::process::exit(2);}
    match fixed::observation(){Ok(v)=>println!("{v}"),Err(_)=>{eprintln!("P752_BLOCK_MEANING_CHECK_FAILED");std::process::exit(2);}}
}
