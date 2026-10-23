"""Fixed non-Native pipe probe. No document API, process creation or runtime permit."""
import json,sys
if sys.argv[1:]!=['--io-only']:raise SystemExit(2)
print(json.dumps(dict(schema_version='hwpx-agent.private.python-pipe-probe/v1',sequence=113,
    case_index=6,operation='checkpoint',step='reopen_session_close')),flush=True)
# A failed controller must close the real input pipe to unblock this read.
value=sys.stdin.readline()
raise SystemExit(0 if value==''else 3)
