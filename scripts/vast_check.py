"""Check Vast.ai instances and available GPU offers."""
import urllib.request
import json
import sys
import os

API_KEY = os.getenv("VAST_API_KEY", "").strip()
if not API_KEY:
    print("Set VAST_API_KEY environment variable")
    sys.exit(1)

BASE = "https://console.vast.ai/api/v0"

def api_get(path):
    req = urllib.request.Request(
        f"{BASE}{path}",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

# Check existing instances
print("=== Existing Instances ===")
data = api_get("/instances?owner=me")
instances = data.get("instances", data) if isinstance(data, dict) else data
if not instances:
    print("  No running instances found.")
else:
    for i in instances:
        print(f"  ID: {i.get('id')}")
        print(f"  GPU: {i.get('gpu_name')} x{i.get('num_gpus', 1)}")
        print(f"  Status: {i.get('actual_status')}")
        print(f"  SSH: {i.get('ssh_host')}:{i.get('ssh_port')}")
        print(f"  Cost: ${i.get('dph_total', 0):.3f}/hr")
        print(f"  Image: {i.get('image_uuid', 'N/A')}")
        print()

# Show cheap GPU offers
print("\n=== Cheapest GPU Offers (RTX 3060+, 12GB+ VRAM) ===")
try:
    search = api_get("/bundles?q={\"gpu_ram\":{\"gte\":12},\"rentable\":{\"eq\":true},\"order\":[[\"dph_total\",\"asc\"]],\"limit\":5,\"type\":\"on-demand\"}")
    offers = search.get("offers", search) if isinstance(search, dict) else search
    if not offers:
        print("  No offers found.")
    else:
        for o in offers[:5]:
            print(f"  GPU: {o.get('gpu_name')} x{o.get('num_gpus',1)} | "
                  f"VRAM: {o.get('gpu_ram',0):.0f}GB | "
                  f"${o.get('dph_total',0):.3f}/hr (${o.get('dph_total',0)*730:.0f}/mo) | "
                  f"ID: {o.get('id')}")
except Exception as e:
    print(f"  Error fetching offers: {e}")
