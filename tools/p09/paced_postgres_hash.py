"""Task-local fresh full-file hashing: original SHA256, original weighted chunks, bounded open rate."""
import hashlib,math,time
from pathlib import Path
from weighted_audit_io import WeightedPacer,original

class PacedPostgresHasher:
    def __init__(self,clock=time.perf_counter,sleeper=time.sleep):
        self.clock,self.sleeper=clock,sleeper;self.next_open=clock();self.pacer=WeightedPacer(clock,sleeper)
        self.opens=0;self.read_passes=0;self.bytes_read=0;self.open_sleep=0.0
    def sha_file(self,path):
        path=Path(path)
        if not path.is_file()or path.is_symlink()or path.is_junction():raise ValueError('PG_HASH_REGULAR_FILE_REQUIRED')
        now=self.clock()
        if not math.isfinite(now):raise ValueError('PG_HASH_CLOCK_INVALID')
        while now<self.next_open:
            # Windows counters need not observe a sub-microsecond sleep. Round the
            # remaining wait up, never down: no extra open credit or busy spin.
            delay=min(.05,max(.001,self.next_open-now));self.sleeper(delay);self.open_sleep+=delay
            later=self.clock()
            if not math.isfinite(later)or later<=now:raise ValueError('PG_HASH_CLOCK_NOT_ADVANCING')
            now=later
        self.next_open=now+.05;self.opens+=1;self.pacer.select(path.name)
        sha=hashlib.sha256()
        with path.open('rb')as stream:
            self.read_passes+=1
            while True:
                # Parent OwnedSQLJobProcess still samples CPU/RAM/job pressure throughout this wait/read.
                self.pacer.reserve(lambda:None);chunk=stream.read(original.CHUNK_BYTES);self.pacer.refund(len(chunk))
                if not chunk:break
                self.bytes_read+=len(chunk);sha.update(chunk)
        return sha.hexdigest()
    def profile(self):
        return dict(read_passes=self.read_passes,file_opens=self.opens,bytes_read=self.bytes_read,max_file_opens_per_second=20,
            binary_bytes_per_second=5*1024*1024//2,other_bytes_per_second=4*1024*1024,chunk_bytes=original.CHUNK_BYTES,
            open_requested_sleep_seconds=round(self.open_sleep,6),byte_requested_sleep_seconds=round(self.pacer.requested_sleep_seconds,6),
            raw_or_parsed_content_cached=False,full_fresh_hash_preserved=True)
