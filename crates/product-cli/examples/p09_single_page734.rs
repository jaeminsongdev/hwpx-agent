//! Read existing exact snapshots; no Native activation or new layout authority.
#[path="../tests/single_page733.rs"]
#[allow(dead_code,unused_imports)]mod fixed;
fn main(){
    if std::env::args().skip(1).collect::<Vec<_>>()!=["--existing16-single-page-observations-only"]{
        eprintln!("P734_MODE_REJECTED");std::process::exit(2);
    }
    match fixed::observation(){Ok(v)=>println!("{v}"),Err(_)=>{eprintln!("P734_SINGLE_PAGE_SCOPE_CHECK_FAILED");std::process::exit(2);}}
}
