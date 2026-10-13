"""Preserve first failed document-placement receipt; same verification, new run."""
from unittest.mock import patch
import verify_observed_writer_progress as prior
def main():
    raw=prior.build.s.scoped_path
    old='implementation/p09/evidence/p09-172-observed-writer.progress-sync-run01.v1.json'
    new='implementation/p09/evidence/p09-172-observed-writer.progress-sync-run02.v1.json'
    def destination(name,**kw):return raw(new if name==old else name,**kw)
    with patch.object(prior.build.s,'scoped_path',destination):return prior.main()
if __name__=='__main__':raise SystemExit(main())
