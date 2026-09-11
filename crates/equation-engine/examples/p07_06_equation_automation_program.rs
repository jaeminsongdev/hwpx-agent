use std::env;
use std::error::Error;

use domain_ir::MathAstLimits;
use equation_engine::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_PROFILE_VERSION, EqEditEngine, EqEditLimits,
    EqEditParseRequestDraft,
};
use serde_json::json;

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args();
    let _program = arguments.next();
    let initial = arguments
        .next()
        .ok_or("initial EqEdit program is required")?;
    let edited = arguments
        .next()
        .ok_or("edited EqEdit program is required")?;
    if arguments.next().is_some() || initial == edited {
        return Err("exactly two distinct programs are required".into());
    }
    let engine = EqEditEngine::new(EqEditLimits::default(), MathAstLimits::default())?;
    let initial = compile(&engine, initial)?;
    let edited = compile(&engine, edited)?;
    if initial.semantic_sha256() == edited.semantic_sha256() {
        return Err("programs are semantically identical".into());
    }
    println!(
        "{}",
        serde_json::to_string(&json!({
            "schema_version": "hwpx-agent.p07-06-equation-automation-program/v1",
            "initial": {
                "script": initial.script(),
                "script_sha256": initial.script_sha256(),
                "semantic_sha256": initial.semantic_sha256(),
            },
            "edited": {
                "script": edited.script(),
                "script_sha256": edited.script_sha256(),
                "semantic_sha256": edited.semantic_sha256(),
            },
        }))?
    );
    Ok(())
}

fn compile(
    engine: &EqEditEngine,
    source: String,
) -> Result<equation_engine::EqEditCompileResult, Box<dyn Error>> {
    let parsed = engine.parse(EqEditParseRequestDraft {
        schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
        profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
        source,
    })?;
    Ok(engine.compile(parsed.ast())?)
}
