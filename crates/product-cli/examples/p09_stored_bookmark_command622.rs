//! Fixed captured source + isolated memory service fixture. Never Native.
#[path = "../tests/stored_bookmark_command_output622.rs"]
#[allow(dead_code, unused_imports)]
mod isolated;
fn main() {
    let result = (|| -> Result<(), Box<dyn std::error::Error>> {
        if std::env::args().skip(1).collect::<Vec<_>>() != ["--fixed-captured-readonly"] {
            return Err("P622_FIXED_ONLY".into());
        }
        let bytes = serde_json::to_vec(&isolated::captured_fixture_observation()?)?;
        if bytes.len() > 32768 {
            return Err("P622_OBSERVATION_LIMIT".into());
        }
        println!("{}", String::from_utf8(bytes)?);
        Ok(())
    })();
    if result.is_err() {
        eprintln!("P622_STORED_OBSERVATION_FAILED");
        std::process::exit(2);
    }
}
