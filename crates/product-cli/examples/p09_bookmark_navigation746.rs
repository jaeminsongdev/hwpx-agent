#[path="../tests/bookmark_navigation745.rs"]#[allow(dead_code,unused_imports)]mod fixed;
fn main(){
    if std::env::args().skip(1).collect::<Vec<_>>()!=["--original-and-renamed-navigation-no-native"]{eprintln!("P746_MODE_REJECTED");std::process::exit(2);}
    match fixed::observation(){Ok(v)=>println!("{v}"),Err(_)=>{eprintln!("P746_NAVIGATION_CHECK_FAILED");std::process::exit(2);}}
}
