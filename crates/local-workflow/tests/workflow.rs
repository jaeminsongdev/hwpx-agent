use std::error::Error;
use std::fs;
use std::path::{Path, PathBuf};

use local_workflow::{GitCommitPlan, LocalWorkflow, MaterializeSlot, WorkflowError};
use sha2::{Digest as _, Sha256};
use tempfile::TempDir;

type TestResult<T = ()> = Result<T, Box<dyn Error>>;

fn fixture(max_bytes: u64) -> TestResult<(TempDir, PathBuf, LocalWorkflow)> {
    let temporary = tempfile::tempdir()?;
    let root = temporary.path().join("workspace");
    fs::create_dir_all(root.join("input"))?;
    fs::create_dir(root.join("output"))?;
    let workflow = LocalWorkflow::open(&root, max_bytes)?;
    Ok((temporary, root, workflow))
}

fn write_input(root: &Path, name: &str, bytes: &[u8]) -> TestResult<[u8; 32]> {
    fs::write(root.join("input").join(name), bytes)?;
    Ok(Sha256::digest(bytes).into())
}

fn materialize_pair(
    root: &Path,
    workflow: &LocalWorkflow,
    source: &[u8],
    candidate: &[u8],
) -> TestResult<([u8; 32], [u8; 32])> {
    let source_sha = write_input(root, "source.hwpx", source)?;
    let candidate_sha = write_input(root, "candidate.hwpx", candidate)?;
    workflow.materialize(
        "op_01",
        MaterializeSlot::Source,
        "input/source.hwpx",
        &source_sha,
    )?;
    workflow.materialize(
        "op_01",
        MaterializeSlot::Candidate,
        "input/candidate.hwpx",
        &candidate_sha,
    )?;
    Ok((source_sha, candidate_sha))
}

#[test]
fn materialize_diff_publish_and_commit_plan_are_identity_bound() -> TestResult {
    let (_temporary, root, workflow) = fixture(1_048_576)?;
    let source = b"synthetic source hwpx";
    let candidate = b"synthetic candidate hwpx";
    let (_source_sha, candidate_sha) = materialize_pair(&root, &workflow, source, candidate)?;
    let difference = workflow.diff("op_01")?;
    assert!(!difference.identical);
    assert_eq!(difference.source.size_bytes, source.len() as u64);
    assert_eq!(difference.candidate.sha256, hex::encode(candidate_sha));
    let published = workflow.publish("op_01", "result.hwpx", &candidate_sha)?;
    assert_eq!(published.sha256, hex::encode(candidate_sha));
    assert_eq!(fs::read(root.join("output/result.hwpx"))?, candidate);
    assert!(!root.join(".hwpx-agent/work/op_01/candidate.hwpx").exists());
    assert_eq!(fs::read(root.join("input/source.hwpx"))?, source);
    fs::create_dir_all(root.join(".git/refs/heads"))?;
    fs::write(root.join(".git/HEAD"), b"ref: refs/heads/main\n")?;
    fs::write(
        root.join(".git/refs/heads/main"),
        format!("{}\n", "a".repeat(40)),
    )?;
    let plan =
        workflow.prepare_git_commit("result.hwpx", &candidate_sha, "Publish verified HWPX")?;
    assert_eq!(plan.output_pathspec, "output/result.hwpx");
    assert_eq!(plan.expected_head, "a".repeat(40));
    assert_eq!(
        plan.expected_head_reference.as_deref(),
        Some("refs/heads/main")
    );
    assert_eq!(plan.expected_output_sha256, hex::encode(candidate_sha));
    let plan_sha256 = plan.approval_plan_sha256();
    let target_sha256 = workflow.git_approval_target_sha256()?;
    assert_eq!(plan_sha256.len(), 64);
    assert_eq!(target_sha256.len(), 64);
    assert_ne!(plan_sha256, target_sha256);
    assert!(!target_sha256.contains(root.to_string_lossy().as_ref()));
    let mut drifted = plan.clone();
    drifted.message.push('!');
    assert_ne!(drifted.approval_plan_sha256(), plan_sha256);
    Ok(())
}

#[test]
fn identical_materializations_are_reported_without_content() -> TestResult {
    let (_temporary, root, workflow) = fixture(1_048_576)?;
    materialize_pair(&root, &workflow, b"same", b"same")?;
    let difference = workflow.diff("op_01")?;
    assert!(difference.identical);
    assert_eq!(difference.source, difference.candidate);
    assert!(!format!("{difference:?}").contains("same"));
    Ok(())
}

#[test]
fn traversal_absolute_reserved_and_wrong_namespace_fail_closed() -> TestResult {
    let (temporary, root, workflow) = fixture(1_048_576)?;
    let outside = temporary.path().join("outside.hwpx");
    fs::write(&outside, b"outside")?;
    let outside_text = outside.to_string_lossy().into_owned();
    let digest: [u8; 32] = Sha256::digest(b"outside").into();
    for path in [
        "../outside.hwpx",
        outside_text.as_str(),
        "output/not-input.hwpx",
        "input/CON.hwpx",
        "input/name.hwpx:ads",
    ] {
        assert!(matches!(
            workflow.materialize("op_bad", MaterializeSlot::Source, path, &digest),
            Err(WorkflowError::Path)
        ));
    }
    assert!(!root.join(".hwpx-agent/work/op_bad/source.hwpx").exists());
    Ok(())
}

#[test]
fn oversized_input_is_rejected_and_partial_target_is_removed() -> TestResult {
    let (_temporary, root, workflow) = fixture(8)?;
    let digest = write_input(&root, "large.hwpx", b"123456789")?;
    assert!(matches!(
        workflow.materialize(
            "op_large",
            MaterializeSlot::Source,
            "input/large.hwpx",
            &digest,
        ),
        Err(WorkflowError::File)
    ));
    assert!(!root.join(".hwpx-agent/work/op_large/source.hwpx").exists());
    Ok(())
}

#[test]
fn multi_buffer_file_streams_without_changing_the_input() -> TestResult {
    let (_temporary, root, workflow) = fixture(1_048_576)?;
    let bytes: Vec<u8> = (0_u32..196_625)
        .map(|index| u8::try_from(index % 251))
        .collect::<Result<_, _>>()?;
    let digest = write_input(&root, "large-fixture.hwpx", &bytes)?;
    let receipt = workflow.materialize(
        "op_stream",
        MaterializeSlot::Source,
        "input/large-fixture.hwpx",
        &digest,
    )?;
    assert_eq!(receipt.size_bytes, bytes.len() as u64);
    assert_eq!(receipt.sha256, hex::encode(digest));
    assert_eq!(fs::read(root.join("input/large-fixture.hwpx"))?, bytes);
    Ok(())
}

#[test]
fn digest_mismatch_removes_new_target_and_preserves_input() -> TestResult {
    let (_temporary, root, workflow) = fixture(1_048_576)?;
    let bytes = b"bounded fixture";
    write_input(&root, "fixture.hwpx", bytes)?;
    assert!(matches!(
        workflow.materialize(
            "op_digest",
            MaterializeSlot::Source,
            "input/fixture.hwpx",
            &[7; 32],
        ),
        Err(WorkflowError::Digest)
    ));
    assert_eq!(fs::read(root.join("input/fixture.hwpx"))?, bytes);
    assert!(!root.join(".hwpx-agent/work/op_digest/source.hwpx").exists());
    Ok(())
}

#[test]
fn slots_and_outputs_never_overwrite() -> TestResult {
    let (_temporary, root, workflow) = fixture(1_048_576)?;
    let digest = write_input(&root, "fixture.hwpx", b"first")?;
    workflow.materialize(
        "op_existing",
        MaterializeSlot::Candidate,
        "input/fixture.hwpx",
        &digest,
    )?;
    assert!(matches!(
        workflow.materialize(
            "op_existing",
            MaterializeSlot::Candidate,
            "input/fixture.hwpx",
            &digest,
        ),
        Err(WorkflowError::OutputExists)
    ));
    fs::write(root.join("output/result.hwpx"), b"keep")?;
    assert!(matches!(
        workflow.publish("op_existing", "result.hwpx", &digest),
        Err(WorkflowError::OutputExists)
    ));
    assert_eq!(fs::read(root.join("output/result.hwpx"))?, b"keep");
    Ok(())
}

#[test]
fn commit_plan_rejects_missing_malformed_or_drifted_git_state() -> TestResult {
    let (_temporary, root, workflow) = fixture(1_048_576)?;
    let digest = write_input(&root, "candidate.hwpx", b"candidate")?;
    workflow.materialize(
        "op_git",
        MaterializeSlot::Candidate,
        "input/candidate.hwpx",
        &digest,
    )?;
    workflow.publish("op_git", "result.hwpx", &digest)?;
    assert!(matches!(
        workflow.prepare_git_commit("result.hwpx", &digest, "Commit"),
        Err(WorkflowError::GitState)
    ));
    fs::create_dir(root.join(".git"))?;
    fs::write(root.join(".git/HEAD"), b"ref: ../outside\n")?;
    assert!(matches!(
        workflow.prepare_git_commit("result.hwpx", &digest, "Commit"),
        Err(WorkflowError::GitState)
    ));
    fs::write(root.join(".git/HEAD"), format!("{}\n", "b".repeat(40)))?;
    assert!(matches!(
        workflow.prepare_git_commit("result.hwpx", &[9; 32], "Commit"),
        Err(WorkflowError::Digest)
    ));
    Ok(())
}

#[test]
fn detached_and_symbolic_heads_have_distinct_approval_plan_digests() -> TestResult {
    let (_temporary, root, workflow) = fixture(1_048_576)?;
    let digest = write_input(&root, "candidate.hwpx", b"candidate")?;
    workflow.materialize(
        "op_git",
        MaterializeSlot::Candidate,
        "input/candidate.hwpx",
        &digest,
    )?;
    workflow.publish("op_git", "result.hwpx", &digest)?;
    fs::create_dir_all(root.join(".git/refs/heads"))?;
    fs::write(root.join(".git/HEAD"), b"ref: refs/heads/main\n")?;
    fs::write(
        root.join(".git/refs/heads/main"),
        format!("{}\n", "a".repeat(40)),
    )?;
    let symbolic = workflow.prepare_git_commit("result.hwpx", &digest, "Commit")?;
    fs::write(root.join(".git/HEAD"), format!("{}\n", "a".repeat(40)))?;
    let detached = workflow.prepare_git_commit("result.hwpx", &digest, "Commit")?;
    assert_eq!(detached.expected_head_reference, None);
    assert_ne!(
        symbolic.approval_plan_sha256(),
        detached.approval_plan_sha256()
    );
    Ok(())
}

#[test]
fn approval_plan_digest_has_a_stable_cross_process_vector() {
    let plan = GitCommitPlan {
        output_pathspec: "output/result.hwpx".to_owned(),
        expected_output_sha256: "a".repeat(64),
        expected_head: "b".repeat(40),
        expected_head_reference: Some("refs/heads/main".to_owned()),
        message: "Publish verified HWPX".to_owned(),
    };
    assert_eq!(
        plan.approval_plan_sha256(),
        "c4a3647a6735d43456952042e2d6c9adc2b44180c182ac060844bbaf0f1a7267"
    );
}

#[test]
fn debug_and_errors_do_not_disclose_workspace_or_file_content() -> TestResult {
    let (_temporary, root, workflow) = fixture(1_048_576)?;
    let debug = format!("{workflow:?}");
    assert!(!debug.contains(root.to_string_lossy().as_ref()));
    assert!(debug.contains("[REDACTED]"));
    let Err(error) = workflow.diff("missing") else {
        return Err("missing operation unexpectedly succeeded".into());
    };
    assert_eq!(error.to_string(), "workflow file rejected");
    Ok(())
}
