"""New admission-order/newline contracts; compiler and product bodies never run."""
import io
from types import SimpleNamespace as NS
import unittest
import native011_current_cohort_build as build


class StartContracts(unittest.TestCase):
    def test_exact_lf_and_windows_crlf_are_consumed_without_read_ahead(self):
        for token in (build.START,build.START.replace(b'\n',b'\r\n')):
            data=io.BytesIO(token+b'untouched');build.read_build_start(data.read)
            self.assertEqual(data.read(),b'untouched')

    def test_eof_wrong_and_overlong_token_rejected(self):
        for token in (b'',build.START[:-1],b'X'+build.START,b'X'*100):
            with self.assertRaisesRegex(ValueError,'WORKER_BUILD_TOKEN_REQUIRED'):
                build.read_build_start(io.BytesIO(token).read)

    def test_membership_resource_write_flush_then_original_eof_capture(self):
        events=[];payload=[]
        class Input:
            def write(self,text):events.append('write');payload.append(text);return len(text)
            def flush(self):events.append('flush')
            def close(self):events.append('eof')
        owned=NS(stdin=Input(),observe=lambda:events.append('membership'))
        guard=NS(check=lambda **kwargs:events.append(('resource',kwargs)))
        def capture(process,**kwargs):
            self.assertEqual(kwargs,dict(output_limit=32768,parse_markers=False))
            self.assertEqual(payload,[build.START.decode('ascii')]);process.stdin.close();return 'captured'
        self.assertEqual(build.start_capture(owned,guard,capture),'captured')
        self.assertEqual(events,['membership',('resource',{'force':True}),'write','flush','eof'])

    def test_resource_failure_cannot_write_token_or_start_capture(self):
        def fail(**kwargs):raise ValueError('RESOURCE_STOP')
        owned=NS(stdin=NS(write=lambda _:self.fail('token leaked')),observe=lambda:None)
        with self.assertRaisesRegex(ValueError,'RESOURCE_STOP'):
            build.start_capture(owned,NS(check=fail),lambda *args,**kwargs:self.fail('capture started'))


if __name__=='__main__':unittest.main()
