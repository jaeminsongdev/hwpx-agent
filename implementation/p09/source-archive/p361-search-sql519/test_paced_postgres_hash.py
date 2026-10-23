"""Four deterministic pacing/hash models, no DB/network/subprocess or user originals."""
import hashlib,tempfile,unittest
from pathlib import Path
from paced_postgres_hash import PacedPostgresHasher
ROOT=Path(__file__).resolve().parents[3]
class Time:
    def __init__(self):self.now=0.0
    def clock(self):return self.now
    def sleep(self,delay):self.now+=delay
class Models(unittest.TestCase):
    def test_full_multichunk_and_empty_hash_match_original(self):
        with tempfile.TemporaryDirectory(prefix='p09-pg-hash-',dir=ROOT/'target')as root:
            t=Time();h=PacedPostgresHasher(t.clock,t.sleep)
            for name,data in [('large.dll',b'abcd'*100_000),('empty.dat',b'')]:
                p=Path(root)/name;p.write_bytes(data);self.assertEqual(h.sha_file(p),hashlib.sha256(data).hexdigest())
            self.assertEqual((h.read_passes,h.opens,h.bytes_read),(2,2,400_000))
    def test_second_pass_is_fresh_not_a_name_or_digest_cache(self):
        with tempfile.TemporaryDirectory(prefix='p09-pg-hash-',dir=ROOT/'target')as root:
            t=Time();h=PacedPostgresHasher(t.clock,t.sleep);p=Path(root)/'file.dll';p.write_bytes(b'first');a=h.sha_file(p)
            p.write_bytes(b'changed');b=h.sha_file(p);self.assertNotEqual(a,b);self.assertEqual(b,hashlib.sha256(b'changed').hexdigest());self.assertEqual(h.read_passes,2)
    def test_idle_cannot_accumulate_multiple_file_open_credits(self):
        with tempfile.TemporaryDirectory(prefix='p09-pg-hash-',dir=ROOT/'target')as root:
            t=Time();h=PacedPostgresHasher(t.clock,t.sleep);p=Path(root)/'file.dll';p.write_bytes(b'x')
            h.sha_file(p);h.sha_file(p);self.assertGreaterEqual(t.now,.05);t.now+=10;before=t.now
            # Byte pacing can independently sleep (including float-rounding at a token boundary).
            # Test the open limiter itself: idle grants no accumulated open credits.
            open_wait=h.open_sleep;h.sha_file(p);self.assertEqual(h.open_sleep,open_wait);after_idle=t.now
            deadline=h.next_open;expected_open_wait=max(0.0,deadline-after_idle)
            h.sha_file(p);self.assertGreaterEqual(t.now,deadline)
            self.assertAlmostEqual(h.open_sleep-open_wait,expected_open_wait,places=9);self.assertGreater(expected_open_wait,0.0);self.assertEqual(h.opens,4)
    def test_weighted_binary_byte_rate_and_one_chunk_burst_are_preserved(self):
        with tempfile.TemporaryDirectory(prefix='p09-pg-hash-',dir=ROOT/'target')as root:
            t=Time();h=PacedPostgresHasher(t.clock,t.sleep);p=Path(root)/'probe.exe';data=b'x'*(2*1024*1024);p.write_bytes(data)
            self.assertEqual(h.sha_file(p),hashlib.sha256(data).hexdigest());self.assertGreaterEqual(t.now,(len(data)-65536)/(5*1024*1024//2))
            self.assertEqual(h.pacer.bytes_by_kind['binary'],len(data));self.assertFalse(h.profile()['raw_or_parsed_content_cached'])
