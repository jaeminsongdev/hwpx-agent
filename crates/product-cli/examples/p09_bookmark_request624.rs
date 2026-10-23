//! Fixed captured bytes through the common strict owned request, not Native.
#[path = "../tests/stored_bookmark_command_output622.rs"]
#[allow(dead_code, unused_imports)]
mod isolated;
fn main() {
    let result = (|| -> Result<(), Box<dyn std::error::Error>> {
        if std::env::args().skip(1).collect::<Vec<_>>() != ["--fixed-captured-readonly"] {
            return Err("P624_FIXED_ONLY".into());
        }
        let bytes = serde_json::to_vec(&isolated::request624::observation()?)?;
        if bytes.len() > 32768 {
            return Err("P624_OBSERVATION_LIMIT".into());
        }
        println!("{}", String::from_utf8(bytes)?);
        Ok(())
    })();
    if result.is_err() {
        eprintln!("P624_REQUEST_OBSERVATION_FAILED");
        std::process::exit(2);
    }
}
