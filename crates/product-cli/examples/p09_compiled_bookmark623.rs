//! Original compiler + fixed captured bytes; fixture services, not Native.
#[path = "../tests/stored_bookmark_command_output622.rs"]
#[allow(dead_code, unused_imports)]
mod isolated;
fn main() {
    let result = (|| -> Result<(), Box<dyn std::error::Error>> {
        if std::env::args().skip(1).collect::<Vec<_>>() != ["--fixed-captured-readonly"] {
            return Err("P623_FIXED_ONLY".into());
        }
        let bytes = serde_json::to_vec(&isolated::compiler623::observation()?)?;
        if bytes.len() > 32768 {
            return Err("P623_OBSERVATION_LIMIT".into());
        }
        println!("{}", String::from_utf8(bytes)?);
        Ok(())
    })();
    if result.is_err() {
        eprintln!("P623_COMPILED_OBSERVATION_FAILED");
        std::process::exit(2);
    }
}
