import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import current_stored_listing_catalog as catalog


class CatalogContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[3]
        raw=(root/catalog.PARSER_PIN["path"]).read_bytes()
        assert len(raw)==catalog.PARSER_PIN["bytes"] and hashlib.sha256(raw).hexdigest()==catalog.PARSER_PIN["sha256"]
        cls.text=raw.decode("utf-8");cls.parser=catalog.Catalog(cls.text)
    def texts(self,count=249):
        root="\n".join(f"#[test] fn case{i}() {{}}" for i in range(count))
        root+="\n"+"\n".join(f'#[path="fixtures/item{i}.rs"]\nmod module{i};' for i in range(58))
        texts={catalog.ROOT:root}
        texts.update({f"crates/product-cli/tests/fixtures/item{i}.rs":"" for i in range(58)})
        return texts
    def test_exact_original_function_bodies_without_top_level_runner_execution(self):
        parser=catalog.Catalog(self.text+"\nraise AssertionError('top-level runner must not execute')\n")
        names,modules=parser.names(self.texts().__getitem__)
        self.assertEqual(len(names),249);self.assertEqual(len(modules),59)
        self.assertTrue(parser.validate("".join(name+": test\n" for name in names),names))
    def test_full_names_and_modules_are_mandatory(self):
        for count in (248,250):
            with self.subTest(count=count),self.assertRaises(ValueError):self.parser.names(self.texts(count).__getitem__)
        texts=self.texts();texts[catalog.ROOT]=texts[catalog.ROOT].replace('mod module57;','mod module56;')
        with self.assertRaises(ValueError):self.parser.names(texts.__getitem__)
    def test_ignored_and_unsupported_test_attributes_remain_rejected(self):
        for change in ("#[ignore]\n", "#[test] async fn unsupported() {}\n"):
            texts=self.texts();texts[catalog.ROOT]=change+texts[catalog.ROOT]
            with self.subTest(change=change),self.assertRaises(ValueError):self.parser.names(texts.__getitem__)
    def test_modules_without_explicit_paths_or_cycles_are_rejected(self):
        texts=self.texts();texts[catalog.ROOT]+="\nmod unsupported;"
        with self.assertRaises(ValueError):self.parser.names(texts.__getitem__)
        texts=self.texts();texts["crates/product-cli/tests/fixtures/item0.rs"]='#[path="../form_stored_provider.rs"]\nmod cycle;'
        with self.assertRaisesRegex(ValueError,"MODULE_CYCLE"):self.parser.names(texts.__getitem__)
    def test_listing_rejects_omission_duplicate_extra_and_failure_output(self):
        names,_=self.parser.names(self.texts().__getitem__)
        outputs=("".join(name+": test\n" for name in names[:-1]),
                 "".join(name+": test\n" for name in names[:-1]+[names[0]]),
                 "".join(name+": test\n" for name in names)+"extra: test\n",
                 "test result: ok. 249 passed; 0 failed\n")
        for output in outputs:
            with self.subTest(output=output[:40]),self.assertRaises(ValueError):self.parser.validate(output,names)
    def test_original_output_limit_and_optional_summary_are_retained(self):
        names,_=self.parser.names(self.texts().__getitem__)
        output="".join(name+": test\r\n" for name in names)
        self.assertTrue(self.parser.validate(output+"249 tests, 0 benchmarks\r\n",names))
        with self.assertRaises(ValueError):self.parser.validate(output+"249 tests, 0 benchmarks\n"*2,names)
        with self.assertRaises(ValueError):self.parser.validate(output+"\n"*32768,names)
    def test_missing_duplicate_or_dynamic_import_parser_function_fails_closed(self):
        texts=(self.text.replace("def module_path(","def omitted_module_path(",1),
               self.text+"\ndef module_path(parent,relative):return relative\n",
               self.text.replace("def module_path(parent, relative):","def module_path(parent, relative):\n    import os",1))
        for text in texts:
            with self.subTest(text=text[-60:]),self.assertRaises(ValueError):catalog.Catalog(text)


if __name__=="__main__":unittest.main()
