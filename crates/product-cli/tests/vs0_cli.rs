use std::error::Error;
use std::fs;

use hwpx_agent_cli::{Vs0Disposition, Vs0Engine};
use serde_json::json;

#[test]
fn creates_once_and_replays_without_second_file_or_revision() -> Result<(), Box<dyn Error>> {
    let root = tempfile::tempdir()?;
    let workspace = root.path().join("workspace");
    fs::create_dir(&workspace)?;
    let request_path = root.path().join("request.json");
    let request = json!({
        "schema_version": "hwpx-agent.vs0-create-request/v1",
        "idempotency_key": "vs0-request-1",
        "project_id": "project-1",
        "document_id": "document-1",
        "base_revision": "revision-1",
        "expected_head_generation": 1,
        "page_preset": "a4_portrait",
        "style": "default",
        "text": "HWPX Agent VS-0 한글 2020"
    });
    fs::write(&request_path, serde_json::to_vec(&request)?)?;
    let source_before = fs::read(&request_path)?;
    let engine = Vs0Engine::new()?;
    let created = engine.execute_file(&request_path, &workspace)?;
    let replayed = engine.execute_file(&request_path, &workspace)?;
    assert_eq!(created.disposition(), Vs0Disposition::Created);
    assert_eq!(replayed.disposition(), Vs0Disposition::Replayed);
    assert_eq!(created.artifact_relative(), replayed.artifact_relative());
    assert_eq!(created.artifact_sha256(), replayed.artifact_sha256());
    assert_eq!(fs::read(&request_path)?, source_before);
    assert_eq!(
        fs::read_dir(workspace.join("output").join("artifacts"))?.count(),
        1
    );
    let public = String::from_utf8(created.public_json()?)?;
    assert!(!public.contains("HWPX Agent"));
    assert!(!public.contains("vs0-request-1"));
    assert!(!public.contains(root.path().to_string_lossy().as_ref()));
    Ok(())
}

#[test]
fn rejects_unknown_fields_wrong_shape_and_key_reuse() -> Result<(), Box<dyn Error>> {
    let root = tempfile::tempdir()?;
    let workspace = root.path().join("workspace");
    fs::create_dir(&workspace)?;
    let request_path = root.path().join("request.json");
    let base = json!({
        "schema_version": "hwpx-agent.vs0-create-request/v1",
        "idempotency_key": "same-key",
        "project_id": "project-1",
        "document_id": "document-1",
        "base_revision": "revision-1",
        "expected_head_generation": 1,
        "page_preset": "a4_portrait",
        "style": "default",
        "text": "first"
    });
    fs::write(&request_path, serde_json::to_vec(&base)?)?;
    let engine = Vs0Engine::new()?;
    let _ = engine.execute_file(&request_path, &workspace)?;
    let mut changed = base;
    changed["text"] = json!("second");
    fs::write(&request_path, serde_json::to_vec(&changed)?)?;
    assert!(engine.execute_file(&request_path, &workspace).is_err());

    changed["extra"] = json!(true);
    fs::write(&request_path, serde_json::to_vec(&changed)?)?;
    assert!(
        Vs0Engine::new()?
            .execute_file(&request_path, &workspace)
            .is_err()
    );
    changed.as_object_mut().ok_or("object")?.remove("extra");
    changed["page_preset"] = json!("letter");
    fs::write(&request_path, serde_json::to_vec(&changed)?)?;
    assert!(
        Vs0Engine::new()?
            .execute_file(&request_path, &workspace)
            .is_err()
    );
    Ok(())
}
