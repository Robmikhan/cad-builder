"""Restart a Vast.ai instance to pick up new SSH keys."""
import json
import os
import sys
import time
import urllib.request
import urllib.error

API_KEY = os.getenv("VAST_API_KEY", "").strip()
if not API_KEY:
    print("Set VAST_API_KEY environment variable")
    sys.exit(1)

BASE = "https://console.vast.ai/api/v0"

def api_put(path, data=None):
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=body, method="PUT",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def api_get(path):
    req = urllib.request.Request(f"{BASE}{path}", headers={"Authorization": f"Bearer {API_KEY}"})
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

# Get instance
data = api_get("/instances?owner=me")
instances = data.get("instances", data) if isinstance(data, dict) else data
if not instances:
    print("No instances found")
    sys.exit(1)

inst = instances[0]
iid = inst["id"]
print(f"Instance {iid}: {inst.get('gpu_name')} — status: {inst.get('actual_status')}")

# Try to stop then start
print(f"\nStopping instance {iid}...")
try:
    api_put(f"/instances/{iid}/", {"state": "stopped"})
    print("  Stop requested")
except urllib.error.HTTPError as e:
    print(f"  Stop error: {e.code} {e.read().decode()}")

print("Waiting 15s...")
time.sleep(15)

print(f"Starting instance {iid}...")
try:
    api_put(f"/instances/{iid}/", {"state": "running"})
    print("  Start requested")
except urllib.error.HTTPError as e:
    print(f"  Start error: {e.code} {e.read().decode()}")

print("Waiting for instance to come back...")
for attempt in range(20):
    time.sleep(15)
    data = api_get("/instances?owner=me")
    instances = data.get("instances", data) if isinstance(data, dict) else data
    for i in (instances if isinstance(instances, list) else []):
        if i.get("id") == iid:
            status = i.get("actual_status", "")
            ssh_host = i.get("ssh_host", "")
            ssh_port = i.get("ssh_port", "")
            print(f"  [{attempt+1}] Status: {status} | SSH: {ssh_host}:{ssh_port}")
            if status == "running" and ssh_host and ssh_port:
                print(f"\n✅ Instance ready! SSH: ssh -p {ssh_port} root@{ssh_host}")
                sys.exit(0)

print("Timed out waiting for instance")
