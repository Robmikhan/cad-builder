"""
Vast.ai deployment script for CAD Builder.
Rents a GPU instance and sets up the application.

Usage:
    python scripts/vast_deploy.py [--offer-id ID]

Environment:
    VAST_API_KEY — Your Vast.ai API key
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

API_KEY = os.getenv("VAST_API_KEY", "").strip()
if not API_KEY:
    print("ERROR: Set VAST_API_KEY environment variable")
    sys.exit(1)

BASE = "https://console.vast.ai/api/v0"

def api_get(path):
    req = urllib.request.Request(f"{BASE}{path}", headers={"Authorization": f"Bearer {API_KEY}"})
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def api_put(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=body, method="PUT",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def api_post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=body, method="POST",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())


def find_best_offer():
    """Find cheapest RTX 3060+ with 12GB+ VRAM."""
    print("Searching for GPU offers...")
    query = {
        "gpu_ram": {"gte": 12},
        "rentable": {"eq": True},
        "order": [["dph_total", "asc"]],
        "limit": 10,
        "type": "on-demand",
    }
    data = api_get(f"/bundles?q={json.dumps(query)}")
    offers = data.get("offers", data) if isinstance(data, dict) else data

    if not offers:
        print("No GPU offers available!")
        sys.exit(1)

    # Prefer RTX 3060 or better with good value
    for o in offers:
        gpu = o.get("gpu_name", "")
        vram = o.get("gpu_ram", 0)
        cost = o.get("dph_total", 0)
        oid = o.get("id")
        print(f"  {gpu} | {vram/1024:.0f}GB VRAM | ${cost:.3f}/hr (${cost*730:.0f}/mo) | ID: {oid}")

    best = offers[0]
    print(f"\nSelected: {best.get('gpu_name')} at ${best.get('dph_total', 0):.3f}/hr")
    return best


def rent_instance(offer_id):
    """Rent a Vast.ai instance with Docker + CUDA."""
    print(f"\nRenting instance (offer {offer_id})...")

    config = {
        "client_id": "me",
        "image": "nvidia/cuda:12.1.0-devel-ubuntu22.04",
        "disk": 40,  # GB
        "onstart": (
            "apt-get update -qq && "
            "apt-get install -y -qq git curl docker.io docker-compose-plugin openssh-server > /dev/null 2>&1 && "
            "mkdir -p /run/sshd && /usr/sbin/sshd && "
            "echo 'Instance ready'"
        ),
    }

    try:
        result = api_put(f"/asks/{offer_id}/", config)
        instance_id = result.get("new_contract")
        if not instance_id:
            print(f"  Response: {result}")
            print("ERROR: Could not rent instance. Check your Vast.ai balance.")
            sys.exit(1)
        print(f"  Instance ID: {instance_id}")
        return instance_id
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"ERROR: {e.code} — {body}")
        sys.exit(1)


def wait_for_instance(instance_id, timeout=300):
    """Wait for instance to be running and SSH-ready."""
    print(f"\nWaiting for instance {instance_id} to start...")
    start = time.time()
    while time.time() - start < timeout:
        data = api_get("/instances?owner=me")
        instances = data.get("instances", data) if isinstance(data, dict) else data
        for i in (instances if isinstance(instances, list) else []):
            if str(i.get("id")) == str(instance_id):
                status = i.get("actual_status", "")
                ssh_host = i.get("ssh_host", "")
                ssh_port = i.get("ssh_port", "")
                print(f"  Status: {status} | SSH: {ssh_host}:{ssh_port}")
                if status == "running" and ssh_host and ssh_port:
                    return {
                        "id": instance_id,
                        "ssh_host": ssh_host,
                        "ssh_port": ssh_port,
                        "gpu": i.get("gpu_name", "unknown"),
                        "cost": i.get("dph_total", 0),
                    }
        time.sleep(15)

    print("ERROR: Instance did not start within timeout")
    sys.exit(1)


def main():
    offer_id = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--offer-id" and i < len(sys.argv) - 1:
            offer_id = sys.argv[i + 1]

    # Check for existing instances first
    print("=== Checking existing instances ===")
    data = api_get("/instances?owner=me")
    instances = data.get("instances", data) if isinstance(data, dict) else data
    running = [i for i in (instances if isinstance(instances, list) else [])
               if i.get("actual_status") == "running"]

    if running:
        inst = running[0]
        print(f"Found running instance: ID {inst['id']}")
        print(f"  GPU: {inst.get('gpu_name')}")
        print(f"  SSH: {inst.get('ssh_host')}:{inst.get('ssh_port')}")
        print(f"  Cost: ${inst.get('dph_total', 0):.3f}/hr")
        info = {
            "id": inst["id"],
            "ssh_host": inst.get("ssh_host"),
            "ssh_port": inst.get("ssh_port"),
            "gpu": inst.get("gpu_name"),
            "cost": inst.get("dph_total", 0),
        }
    else:
        print("No running instances. Renting one...\n")
        if offer_id is None:
            offer = find_best_offer()
            offer_id = offer["id"]
        instance_id = rent_instance(offer_id)
        info = wait_for_instance(instance_id)

    print("\n" + "=" * 50)
    print("INSTANCE READY")
    print("=" * 50)
    print(f"  GPU:  {info['gpu']}")
    print(f"  Cost: ${info['cost']:.3f}/hr (${info['cost']*730:.0f}/mo)")
    print(f"  SSH:  ssh -p {info['ssh_port']} root@{info['ssh_host']}")
    print()
    print("Next steps:")
    print(f"  1. SSH in:  ssh -p {info['ssh_port']} root@{info['ssh_host']}")
    print("  2. Clone:   git clone <your-repo-url> /opt/cad-builder && cd /opt/cad-builder")
    print("  3. Deploy:  bash scripts/deploy.sh yourdomain.com")
    print()


if __name__ == "__main__":
    main()
