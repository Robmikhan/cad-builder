"""
Golden-set evaluation harness.
Place a few known test cases in services/eval/golden_set/.
Each case can include:
- part_spec.json
- expected.json (dimensions, etc.)
This is a scaffold; wire in your mesh/cad steps as they mature.
"""
from pathlib import Path
import json

def main():
    golden = Path("services/eval/golden_set")
    cases = [p for p in golden.iterdir() if p.is_dir()]
    results = []
    for c in cases:
        spec = json.loads((c / "part_spec.json").read_text(encoding="utf-8"))
        results.append({"case": c.name, "status": "TODO", "note": "Wire pipeline eval here."})
    print(json.dumps({"results": results}, indent=2))

if __name__ == "__main__":
    main()
