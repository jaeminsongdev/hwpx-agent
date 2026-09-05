from __future__ import annotations
import json
import plan_review

def main() -> int:
    bundles, errors = plan_review.validate_all()
    if errors:
        print(json.dumps({"decision": "FAIL", "errors": errors}, ensure_ascii=True, sort_keys=True)); return 1
    print(json.dumps({"decision": "PASS", "resource_bytes": bundles["resource"]["bytes"], "calls": 5}, ensure_ascii=True, sort_keys=True)); return 0
if __name__ == "__main__":
    raise SystemExit(main())
