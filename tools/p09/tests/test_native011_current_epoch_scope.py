"""New lossless archive/union contracts; no file/Frame/process is created."""
import unittest
import current_stored_runtime_scope as scope
import native011_current_epoch_scope as epoch


def pin(name,value='a'):return dict(path=name,bytes=1,sha256=value*64)


class ScopeContracts(unittest.TestCase):
    def test_archive_preserves_every_other_pin_count_and_bytes_without_mutating_input(self):
        before=pin('crates/x.rs');other=pin('crates/y.rs','b')
        after=dict(before,path='archive/crates/x.rs');original={p['path']:p for p in (before,other)}
        result=epoch.archive_rows(original,[(before,after)],scope)
        self.assertEqual(result,{'archive/crates/x.rs':after,'crates/y.rs':other})
        self.assertEqual(original['crates/x.rs'],before)

    def test_wrong_preimage_or_changed_payload_cannot_be_archived(self):
        before=pin('crates/x.rs');after=dict(before,path='archive/x.rs')
        for original,translation in (({'crates/x.rs':dict(before,bytes=2)},(before,after)),
            ({'crates/x.rs':before},(before,dict(after,sha256='b'*64)))):
            with self.assertRaisesRegex(ValueError,'LOSSLESS_DISJOINT_ARCHIVE_MAPPING'):
                epoch.archive_rows(original,[translation],scope)

    def test_existing_archive_or_duplicate_translation_is_rejected(self):
        before=pin('crates/x.rs');after=dict(before,path='archive/x.rs')
        with self.assertRaisesRegex(ValueError,'LOSSLESS_DISJOINT_ARCHIVE_MAPPING'):
            epoch.archive_rows({before['path']:before,after['path']:after},[(before,after)],scope)
        with self.assertRaisesRegex(ValueError,'LOSSLESS_DISJOINT_ARCHIVE_MAPPING'):
            epoch.archive_rows({before['path']:before},[(before,after),(before,after)],scope)

    def test_digest_is_order_independent_and_payload_sensitive(self):
        one=pin('crates/a.rs');two=pin('crates/b.rs','b')
        a={one['path']:one,two['path']:two};b=dict(reversed(list(a.items())))
        self.assertEqual(epoch.digest(a),epoch.digest(b))
        b[one['path']]=dict(one,bytes=2);self.assertNotEqual(epoch.digest(a),epoch.digest(b))


if __name__=='__main__':unittest.main()
