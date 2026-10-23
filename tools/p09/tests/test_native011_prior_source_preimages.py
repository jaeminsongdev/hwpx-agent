"""Exact inverse models only; original and current source files are never edited."""
import hashlib
import unittest
import native011_prior_source_preimages as pre


def pin(name,data):return dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


class PreimageContracts(unittest.TestCase):
    def test_all_four_closed_module_inverse_recipes(self):
        for name,addition in pre.ADDITIONS.items():
            old=b'// original\nuse original;\n';new=addition+old
            self.assertEqual(pre.restore(name,new,pin(name,old)),old)
            self.assertTrue(new.startswith(addition))

    def test_cli_inverse_preserves_every_other_byte(self):
        old=b'use original;\nfn main() {\n    original();\n}\n\n'+pre.FUNCTION_END+b'    old();\n}\n'
        new=old.replace(b'    original();',pre.BRANCH+b'    original();')
        new=new.replace(pre.FUNCTION_END,pre.FUNCTION_START+b'    extension();\n}\n\n'+pre.FUNCTION_END)
        self.assertEqual(pre.restore(pre.MAIN,new,pin(pre.MAIN,old)),old)

    def test_same_shape_but_changed_original_or_wrong_expected_hash_is_not_recovery(self):
        name=next(iter(pre.ADDITIONS));old=b'original\n';new=pre.ADDITIONS[name]+b'tampered\n'
        with self.assertRaisesRegex(ValueError,'EXACT_PRIOR_BYTES_AND_SHA256'):pre.restore(name,new,pin(name,old))
        expected=pin(name,old);expected['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'EXACT_PRIOR_BYTES_AND_SHA256'):
            pre.restore(name,pre.ADDITIONS[name]+old,expected)

    def test_duplicates_missing_unknown_source_and_wrong_order_rejected(self):
        name=next(iter(pre.ADDITIONS));old=b'original\n'
        for raw in (old,pre.ADDITIONS[name]*2+old):
            with self.assertRaisesRegex(ValueError,'ONE_EXACT_MODULE_ADDITION'):pre.restore(name,raw,pin(name,old))
        with self.assertRaisesRegex(ValueError,'ONLY_FIVE_PRIOR_SOURCES'):
            pre.restore('crates/other.rs',old,pin('crates/other.rs',old))
        raw=pre.FUNCTION_END+pre.FUNCTION_START+pre.BRANCH
        with self.assertRaisesRegex(ValueError,'EXACT_CLI_EXTENSION_ORDER'):pre.restore(pre.MAIN,raw,pin(pre.MAIN,old))


if __name__=='__main__':unittest.main()
