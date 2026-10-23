"""New key-delivery branch only; no database, OS credential or prior model execution."""
import ast,types,unittest
from pathlib import Path
PATH=Path(__file__).resolve().parents[1]/'native_postgres_storage.py'

class Models(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def require(ok,code):
            if not ok:raise ValueError(code)
        tree=ast.parse(PATH.read_text(encoding='utf-8'));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='artifact_probe_environment')
        namespace={'cluster':types.SimpleNamespace(require=require),'secrets':types.SimpleNamespace(token_hex=lambda n:'synthetic-wrong-key'if n==32 else None)}
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(PATH),'exec'),namespace)
        cls.make=staticmethod(namespace['artifact_probe_environment'])
        cls.env={'P09_SQL23_ADMIN_PASSWORD':'synthetic-admin','P09_SQL23_REVISION_PASSWORD':'synthetic-stale-role',
            'P09_STORAGE_AES_HEX':'synthetic-stale-aes','P09_STORAGE_HMAC_HEX':'synthetic-stale-hmac','P09_OWNED_ARTIFACT_CUSTODY_NONCE':'public-nonce','SystemRoot':'synthetic-system'}
    def test_owned_installer_receives_nonce_without_database_or_crypto_keys(self):
        out=self.make(self.env,1234,'role-r','role-a','--custody-install-keys',True,None,None)
        self.assertTrue(out=={'P09_OWNED_ARTIFACT_CUSTODY_NONCE':'public-nonce','SystemRoot':'synthetic-system'})
    def test_owned_application_receives_only_explicit_roles_and_never_crypto_or_admin(self):
        for mode in('--execute','--restart-registered','--wrong-key'):
            out=self.make(self.env,1234,'role-r','role-a',mode,True,None,None)
            self.assertTrue(all(k not in out for k in('P09_SQL23_ADMIN_PASSWORD','P09_STORAGE_AES_HEX','P09_STORAGE_HMAC_HEX')))
            self.assertTrue(out['P09_SQL23_REVISION_PASSWORD']=='role-r'and out['P09_SQL23_ARTIFACT_PASSWORD']=='role-a'and out['P09_SQL23_PORT']=='1234')
    def test_original_parent_key_modes_preserve_normal_and_wrong_key_branches(self):
        normal=self.make({},1234,'r','a','--execute',False,'original-aes','original-hmac')
        wrong=self.make({},1234,'r','a','--wrong-key',False,'original-aes','original-hmac')
        self.assertTrue(normal['P09_STORAGE_AES_HEX']=='original-aes'and normal['P09_STORAGE_HMAC_HEX']=='original-hmac')
        self.assertTrue(wrong['P09_STORAGE_AES_HEX']=='synthetic-wrong-key'and wrong['P09_STORAGE_HMAC_HEX']=='original-hmac')
    def test_installer_is_not_available_in_legacy_parent_key_mode(self):
        with self.assertRaisesRegex(ValueError,'PG_STORAGE_INSTALLER_ONLY_FOR_OWNED_WINDOWS_KEYS'):
            self.make({},1234,'r','a','--custody-install-keys',False,'a','h')
