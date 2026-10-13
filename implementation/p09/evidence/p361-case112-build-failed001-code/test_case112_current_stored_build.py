import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build_case112_current_stored as build


def artifact(**overrides):
    row=dict(reason="compiler-artifact",target=dict(name="form_stored_provider",kind=["test"],
        src_path=str(build.c.ROOT/"crates/product-cli/tests/form_stored_provider.rs")),
        fresh=False,profile=dict(build.EXPECTED_PROFILE),
        executable=str(build.TARGET/"debug/deps/form_stored_provider-0123456789abcdef.exe"))
    row.update(overrides);return row


def raw_payload(*items):
    return b"".join((json.dumps(item,separators=(",",":"))+"\n").encode() for item in items)


def proof_payload(*items):
    stream=build.CargoStream();raw=raw_payload(*items)
    for start in range(0,len(raw),4096):stream.feed(raw[start:start+4096])
    return stream.finish(0),raw


def parent():
    names=[build.base.epoch.LIBRARY,build.base.epoch.MODULE]
    names += [f"crates/synthetic/src/item{i}.rs" for i in range(785)]
    names += [f"tools/p09/synthetic{i}.py" for i in range(19)]
    return dict(state=build.base.PASS,exit_code=0,cleanup_confirmed=True,owned_tree_empty=True,
        current_CLI_library_typecheck_qualified=True,source_input_bytes_checked_before_after=True,
        current_test_executable_built=False,runtime_tests_executed=False,full249_current_qualified=False,
        source_epoch_audit_pin=build.base.AUDIT_PIN,
        selected_target_directory=build.TARGET.relative_to(build.c.ROOT).as_posix(),policy=build.c.POLICY,
        owned_limits_readback=dict(verified=True),prior_queue_cases=105,next_case=112,accepted_count_delta=0,
        whole_workspace_Rust_input_count=787,
        source_freeze=[dict(path=name,bytes=1,sha256="a"*64) for name in names])


class BuildContracts(unittest.TestCase):
    def test_recipe_retains_exact_optimized_profile_and_no_runtime(self):
        recipe=build.recipe(1)
        self.assertEqual(len(build.profile.CONFIG),81)
        self.assertEqual(recipe.count("--config"),81)
        self.assertNotIn("run",recipe);self.assertNotIn("--list",recipe)
        self.assertEqual(recipe[-3:],["--","-C","extra-filename=-p361-case112-r001"])
        self.assertEqual(build.ARGS,["rustc","-p","hwpx-agent-cli","--test","form_stored_provider","--profile","test"])
    def test_closed_generation_and_fresh_suffix_scope(self):
        for value in (0,1000,True,"1"):
            with self.subTest(value=value),self.assertRaises(ValueError):build.task_for(value)
        self.assertEqual(build.run_for(build.task_for(3)),3)
        self.assertNotEqual(build.executable_name(1),build.executable_name(2))
        self.assertNotIn(build.executable_name(1),[build.base.epoch.LIBRARY])
        with self.assertRaises(ValueError):build.run_for("stored-tests")
    def test_assertions_overflow_and_catalog_test_are_mandatory(self):
        for key in ("debug_assertions","overflow_checks","test"):
            for value in (False,1):
                row=dict(build.EXPECTED_PROFILE);row[key]=value
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):build.profile_scope(row)
    def test_all_raw_records_are_hashed_and_complete_stream_is_bound(self):
        dep=dict(reason="compiler-artifact",target=dict(name="dependency"))
        output,raw=proof_payload(dep,artifact(),dict(reason="build-finished",success=True))
        row=build.parse_build(output,1,require_file=False)
        self.assertEqual(row["validated_stream"]["raw_stdout_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(row["validated_stream"]["messages"],3)
        self.assertEqual(row["executable_path"],build.executable_name(1))
    def test_stream_rejects_warning_error_and_malformed_record(self):
        for raw in (b'{bad}\n',raw_payload(dict(reason="compiler-message",message=dict(level="warning"))),
                    raw_payload(dict(reason="compiler-message",message=dict(level="error"))),
                    b'{"reason":"build-finished","reason":"build-finished","success":true}\n'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):build.CargoStream().feed(raw)
    def test_original_record_and_total_memory_budgets_are_retained(self):
        with self.assertRaises(ValueError):build.CargoStream().feed(b"x"*4097)
        stream=build.CargoStream()
        for _ in range(8):stream.feed(b"x"*4096)
        with self.assertRaises(ValueError):stream.feed(b"x")
        stream=build.CargoStream();stream.bytes=build.stream.TOTAL_JSON_BYTES
        with self.assertRaises(ValueError):stream.feed(b"x")
    def test_fresh_catalog_target_source_and_kind_are_exact(self):
        for row in (artifact(fresh=True),artifact(target=dict(name="form_stored_provider",kind=["bin"])),
                    artifact(target=dict(name="form_stored_provider",kind=["test"],src_path="foreign.rs")),
                    artifact(target=dict(name="formula_issuer_product_postgres_probe"))):
            with self.subTest(row=row),self.assertRaises(ValueError):build.CargoStream().feed(raw_payload(row))
    def test_duplicate_target_and_finish_or_missing_finish_are_rejected(self):
        for items in ((artifact(),artifact()),(artifact(),dict(reason="build-finished",success=False)),
                      (artifact(),dict(reason="build-finished",success=True),dict(reason="build-finished",success=True)),
                      (artifact(),)):
            with self.subTest(items=items),self.assertRaises(ValueError):proof_payload(*items)
    def test_announcement_cannot_escape_exact_cache_or_bind_old_executable(self):
        for name in (str(build.c.ROOT/"target/old/form_stored_provider-0123456789abcdef.exe"),
                     str(build.TARGET/"debug/deps/form_stored_provider-p361-case112-r002.exe"),
                     "form_stored_provider-0123456789abcdef.exe"):
            output,_=proof_payload(artifact(executable=name),dict(reason="build-finished",success=True))
            with self.subTest(name=name),self.assertRaises(ValueError):build.parse_build(output,1,require_file=False)
    def test_closed_stream_proof_cannot_truncate_skip_or_exceed_bounds(self):
        output,_=proof_payload(artifact(),dict(reason="build-finished",success=True))
        rows=[json.loads(line) for line in output.splitlines()]
        for change in (dict(raw_output_truncated=True),dict(all_records_validated=False),dict(raw_logs_included=True),
                       dict(messages=True),dict(raw_stdout_bytes=build.stream.TOTAL_JSON_BYTES+1),dict(raw_stdout_sha256="invalid")):
            altered=copy.deepcopy(rows);altered[-1].update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):
                build.parse_build("\n".join(json.dumps(row) for row in altered),1,require_file=False)
    def test_parent_preserves_qualified_whole_current_inputs(self):
        expected,rust=build.parent_scope(parent())
        self.assertEqual(len(expected),806);self.assertEqual(len(rust),787)
        self.assertIn(build.base.epoch.MODULE,rust)
    def test_parent_flags_and_input_inventory_cannot_be_promoted_or_rebased(self):
        for change in (dict(state="PASS_OTHER"),dict(current_CLI_library_typecheck_qualified=False),
                       dict(full249_current_qualified=True),dict(runtime_tests_executed=True),
                       dict(whole_workspace_Rust_input_count=True),dict(accepted_count_delta=1),dict(next_case=111)):
            row=parent();row.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):build.parent_scope(row)
        row=parent();row["source_freeze"].append(row["source_freeze"][0])
        with self.assertRaises(ValueError):build.parent_scope(row)
    def test_worker_reuses_original_go_job_dispatch_without_launching_child(self):
        with patch.object(build,"direct_path"),patch.object(build.Path,"exists",return_value=False), \
             patch.object(build.Path,"is_dir",return_value=True),patch.object(build.c,"worker",return_value=0) as original:
            self.assertEqual(build.worker(build.task_for(997)),0)
        original.assert_called_once_with(build.task_for(997))
    def test_original_job_hard_caps_are_not_weakened(self):
        self.assertEqual(build.c.POLICY["logical_cpu_limit"],1)
        self.assertEqual(build.c.POLICY["cargo_jobs"],1)
        self.assertEqual(build.c.POLICY["emergency_cpu_percent"],98)
        self.assertEqual(build.c.POLICY["stop_ram_min_percent"],8)
        self.assertEqual(build.c.POLICY["job_memory_stop_percent"],7)
        self.assertEqual(build.c.POLICY["job_memory_limit_percent"],8)


if __name__=="__main__":unittest.main()
