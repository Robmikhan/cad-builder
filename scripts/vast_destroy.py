"""Stop and destroy Vast.ai instances."""
import json, os, sys, urllib.request, urllib.error

API_KEY = os.getenv("VAST_API_KEY", "").strip()
BASE = "https://console.vast.ai/api/v0"

def api_req(path, method="GET", data=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        f"{BASE}{path}", data=body, method=method,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    )
    try:
        r = urllib.request.urlopen(req)
        return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()}

data = api_req("/instances?owner=me")
instances = data.get("instances", data) if isinstance(data, dict) else data
if not instances:
    print("No instances to destroy")
    sys.exit(0)

for i in (instances if isinstance(instances, list) else []):
    iid = i.get("id")
    print(f"Destroying instance {iid} ({i.get('gpu_name')}, ${i.get('dph_total',0):.3f}/hr)...")
    result = api_req(f"/instances/{iid}/", method="DELETE")
    print(f"  Result: {result}")
print("Done — billing stopped.")
