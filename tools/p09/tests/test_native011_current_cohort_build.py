"""New build-only parser, recipe inverse and environment contracts; no Cargo."""
import json
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_current_cohort_build as build
import native011_current_cohort_plan as plan
import accept_case112_current_epoch as a
import conservative_maintenance as c
import stored_test_profile81 as profile
import signed_durable_build_stream as stream


class BuildContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(c.ROOT/plan.BUILD).read_text(encoding='utf-8')
        cls.module=build.definitions(cls.raw,a,c,profile,stream,plan)

    def artifact(self):
        return dict(reason='compiler-artifact',target=dict(name='form_stored_provider',kind=['test'],
            src_path=str(c.ROOT/'crates/product-cli/tests/form_stored_provider.rs')),fresh=False,
            profile=dict(opt_level='1',debuginfo='line-tables-only',debug_assertions=True,
                overflow_checks=True,test=True),executable=str(c.ROOT/self.module.executable_name(1)))

    def test_original_recipe_profile81_and_parser_identities(self):
        raw=a.native.definitions(self.raw,('require','task_for','recipe'),dict(profile=profile,
            TARGET=c.ROOT/plan.OLD_TARGET,ARGS=['rustc','-p','hwpx-agent-cli','--test','form_stored_provider','--profile','test']))
        self.assertEqual(self.module.recipe(1),plan.project_recipe(raw.recipe(1),c.ROOT))
        self.assertEqual(len(profile.CONFIG),81)
        self.assertEqual(self.module.executable_name(1),
            plan.TARGET+'/debug/deps/form_stored_provider-p361-native011-g001.exe')

    def test_complete_original_stream_and_closed_parser(self):
        reader=self.module.CargoStream()
        for row in (self.artifact(),dict(reason='build-finished',success=True)):
            reader.feed((json.dumps(row)+'\n').encode())
        payload=reader.finish(0);result=self.module.parse_build(payload,1,require_file=False)
        self.assertTrue(result['validated_stream']['all_records_validated'])
        self.assertFalse(result['validated_stream']['raw_output_truncated'])

    def test_warning_and_duplicate_artifact_are_not_filtered(self):
        reader=self.module.CargoStream()
        with self.assertRaisesRegex(ValueError,'WARNING_OR_ERROR'):
            reader.accept(json.dumps(dict(reason='compiler-message',message=dict(level='warning'))).encode())
        reader=self.module.CargoStream();raw=json.dumps(self.artifact()).encode();reader.accept(raw)
        with self.assertRaisesRegex(ValueError,'EXACT_FRESH_TEST_TARGET'):reader.accept(raw)

    def test_original_assertions_profile_and_fresh_artifact_required(self):
        artifact=self.artifact();artifact['profile']['debug_assertions']=False
        with self.assertRaisesRegex(ValueError,'EXACT_ASSERTION_TEST_PROFILE'):
            self.module.CargoStream().accept(json.dumps(artifact).encode())
        artifact=self.artifact();artifact['fresh']=True
        with self.assertRaisesRegex(ValueError,'EXACT_FRESH_TEST_TARGET'):
            self.module.CargoStream().accept(json.dumps(artifact).encode())

    def test_environment_keeps_assertions_single_jobs_codegen16_and_no_incremental(self):
        original=dict(P150_BLOB_ROOT='not_a_value_to_retain')
        env=build.build_environment(original)
        self.assertNotIn('P150_BLOB_ROOT',env);self.assertIn('P150_BLOB_ROOT',original)
        self.assertEqual((env['CARGO_BUILD_JOBS'],env['RUST_TEST_THREADS'],env['CARGO_INCREMENTAL']),('1','1','0'))
        self.assertEqual(env['CARGO_PROFILE_TEST_CODEGEN_UNITS'],'16')
        self.assertEqual(env['CARGO_PROFILE_TEST_DEBUG_ASSERTIONS'],'true')
        self.assertEqual(env['CARGO_PROFILE_TEST_OVERFLOW_CHECKS'],'true')
        for name in build.OVERRIDES:
            with self.assertRaisesRegex(ValueError,'NO_AMBIENT_COMPILER_OVERRIDE'):
                build.build_environment({name:'untrusted'})

    def test_changed_identity_source_or_incomplete_stream_refused(self):
        with self.assertRaisesRegex(ValueError,'EXACT_TWO_IDENTITY_CONSTANTS'):
            build.definitions(self.raw.replace('extra-filename=-p361-case112-r','other-prefix'),a,c,profile,stream,plan)
        with self.assertRaisesRegex(ValueError,'COMPLETE_CLEAN_BUILD_REQUIRED'):
            self.module.CargoStream().finish(0)

    def test_named_plan_dependencies_use_actual_fresh_pins_and_reject_drift(self):
        pin=dict(path='Cargo.toml',bytes=1,sha256='a'*64);calls=[]
        def fresh(name):calls.append(name);return pin
        def exact(actual,expected,label):self.assertEqual(actual,expected,label)
        build.check_plan_dependencies({'Cargo.toml':pin},[pin],fresh,exact)
        self.assertEqual(calls,[])
        build.check_plan_dependencies({},[pin],fresh,exact);self.assertEqual(calls,['Cargo.toml'])
        with self.assertRaises(AssertionError):
            build.check_plan_dependencies({'Cargo.toml':dict(pin,bytes=2)},[pin],fresh,exact)


if __name__=='__main__':unittest.main()
