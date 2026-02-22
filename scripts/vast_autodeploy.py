"""
Deploy CAD Builder to Vast.ai as a self-configuring instance.
The instance clones from GitHub, installs deps, builds frontend, and starts serving.

Usage:
    set VAST_API_KEY=your_key
    python scripts/vast_autodeploy.py
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

API_KEY = os.getenv("VAST_API_KEY", "").strip()
if not API_KEY:
    print("Set VAST_API_KEY environment variable")
    sys.exit(1)

BASE = "https://console.vast.ai/api/v0"
REPO = "https://github.com/Robmikhan/cad-builder.git"

# Onstart script that runs when the instance boots.
# Installs everything and starts the CAD Builder API + worker.
ONSTART_SCRIPT = r"""#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

LOG=/var/log/cad-builder-setup.log
exec > >(tee -a $LOG) 2>&1
echo "=== CAD Builder setup starting at $(date) ==="

# Install system deps
apt-get update -qq
apt-get install -y -qq python3.11 python3.11-venv python3-pip \
    git curl wget nodejs npm ffmpeg libgl1-mesa-glx libglib2.0-0 2>/dev/null

ln -sf /usr/bin/python3.11 /usr/bin/python 2>/dev/null || true

# Clone repo
if [ ! -d /opt/cad-builder ]; then
    git clone REPO_URL /opt/cad-builder
fi
cd /opt/cad-builder

# Python deps
python -m pip install --no-cache-dir -U pip wheel 2>/dev/null
python -m pip install --no-cache-dir -e . 2>/dev/null

# Build frontend
cd /opt/cad-builder/frontend
npm install 2>/dev/null
npm run build 2>/dev/null
cd /opt/cad-builder

# Create .env if missing
if [ ! -f .env ]; then
    cp .env.production .env
    ADMIN_KEY="cad_admin_$(openssl rand -hex 16)"
    sed -i "s|^CAD_AGENT_API_KEYS=.*|CAD_AGENT_API_KEYS=${ADMIN_KEY}|" .env
    sed -i "s|^DOMAIN=.*|DOMAIN=:80|" .env
    sed -i "s|^OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://localhost:11434|" .env
    echo "ADMIN_KEY=${ADMIN_KEY}" >> /var/log/cad-builder-setup.log
fi

# Install and start Ollama
if ! command -v ollama &>/dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi
nohup ollama serve &>/var/log/ollama.log &
sleep 5
ollama pull qwen2.5-coder:7b &>/var/log/ollama-pull.log &

# Start API server
cd /opt/cad-builder
nohup python -m uvicorn services.api.main:app --host 0.0.0.0 --port 8080 \
    &>/var/log/cad-api.log &

# Start worker
nohup python -m services.workers.worker &>/var/log/cad-worker.log &

echo "=== CAD Builder setup complete at $(date) ==="
echo "=== API running on port 8080 ==="
""".replace("REPO_URL", REPO)


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
        err_body = e.read().decode()
        print(f"  API Error {e.code}: {err_body}")
        return {"error": e.code, "body": err_body}


def find_offer():
    """Find cheapest GPU with 12GB+ VRAM."""
    print("Searching for GPU offers...")
    query = {
        "gpu_ram": {"gte": 12},
        "rentable": {"eq": True},
        "order": [["dph_total", "asc"]],
        "limit": 10,
        "type": "on-demand",
    }
    data = api_req(f"/bundles?q={urllib.parse.quote(json.dumps(query))}")
    offers = data.get("offers", data) if isinstance(data, dict) else data
    if not offers:
        print("No GPU offers found!")
        sys.exit(1)

    for o in offers[:5]:
        print(f"  {o.get('gpu_name')} | {o.get('gpu_ram',0)/1024:.0f}GB | "
              f"${o.get('dph_total',0):.3f}/hr | ID: {o.get('id')}")

    best = offers[0]
    print(f"\nSelected: {best.get('gpu_name')} at ${best.get('dph_total',0):.3f}/hr")
    return best


def create_instance(offer_id):
    """Create a Vast.ai instance with auto-deploy onstart script."""
    print(f"\nCreating instance from offer {offer_id}...")

    config = {
        "client_id": "me",
        "image": "nvidia/cuda:12.1.0-runtime-ubuntu22.04",
        "disk": 50,
        "onstart": ONSTART_SCRIPT,
        "direct": True,
        "jupyter": False,
        "env": {
            "CAD_AGENT_PORT": "8080",
        },
    }

    result = api_req(f"/asks/{offer_id}/", method="PUT", data=config)
    instance_id = result.get("new_contract")
    if not instance_id:
        print(f"  Failed: {result}")
        sys.exit(1)
    print(f"  Instance ID: {instance_id}")
    return instance_id


def wait_for_instance(instance_id, timeout=600):
    """Wait for instance to be running."""
    print(f"\nWaiting for instance {instance_id}...")
    start = time.time()
    while time.time() - start < timeout:
        data = api_req("/instances?owner=me")
        instances = data.get("instances", data) if isinstance(data, dict) else data
        for i in (instances if isinstance(instances, list) else []):
            if str(i.get("id")) == str(instance_id):
                status = i.get("actual_status", "")
                ports = i.get("ports", {})
                ip = i.get("public_ipaddr", "")
                direct_port = None
                # Find mapped port for 8080
                for port_key, port_info in (ports or {}).items():
                    if "8080" in str(port_key):
                        if isinstance(port_info, list) and port_info:
                            direct_port = port_info[0].get("HostPort", "")
                        elif isinstance(port_info, dict):
                            direct_port = port_info.get("HostPort", "")

                print(f"  Status: {status} | IP: {ip} | Ports: {ports}")

                if status == "running":
                    return {
                        "id": instance_id,
                        "ip": ip,
                        "ports": ports,
                        "direct_port": direct_port,
                        "gpu": i.get("gpu_name"),
                        "cost": i.get("dph_total", 0),
                        "ssh_host": i.get("ssh_host"),
                        "ssh_port": i.get("ssh_port"),
                    }
        time.sleep(20)

    print("Timed out!")
    sys.exit(1)


def main():
    # Check for existing instances
    data = api_req("/instances?owner=me")
    instances = data.get("instances", data) if isinstance(data, dict) else data
    running = [i for i in (instances if isinstance(instances, list) else [])
               if i.get("actual_status") in ("running", "loading")]

    if running:
        inst = running[0]
        print(f"Existing instance found: {inst['id']} ({inst.get('gpu_name')})")
        print(f"  Status: {inst.get('actual_status')}")
        print(f"  IP: {inst.get('public_ipaddr')}")
        print(f"  Ports: {inst.get('ports')}")
        print(f"  SSH: {inst.get('ssh_host')}:{inst.get('ssh_port')}")
        info = {
            "id": inst["id"],
            "ip": inst.get("public_ipaddr", ""),
            "ports": inst.get("ports", {}),
            "gpu": inst.get("gpu_name"),
            "cost": inst.get("dph_total", 0),
            "ssh_host": inst.get("ssh_host"),
            "ssh_port": inst.get("ssh_port"),
        }
    else:
        offer = find_offer()
        instance_id = create_instance(offer["id"])
        info = wait_for_instance(instance_id)

    print("\n" + "=" * 55)
    print("  INSTANCE DEPLOYED")
    print("=" * 55)
    print(f"  GPU:   {info.get('gpu')}")
    print(f"  Cost:  ${info.get('cost', 0):.3f}/hr (${info.get('cost', 0)*730:.0f}/mo)")
    print(f"  IP:    {info.get('ip')}")
    print(f"  Ports: {info.get('ports')}")
    if info.get("ssh_host"):
        print(f"  SSH:   ssh -p {info.get('ssh_port')} root@{info.get('ssh_host')}")
    print()
    print("  The instance is now installing dependencies and building the app.")
    print("  This takes ~5-10 minutes on first boot.")
    print()
    ip = info.get("ip", "IP")
    print(f"  Once ready, access at: http://{ip}:8080")
    print()
    print("  Check setup progress via SSH:")
    print(f"    ssh -p {info.get('ssh_port')} root@{info.get('ssh_host')} tail -f /var/log/cad-builder-setup.log")
    print()


if __name__ == "__main__":
    main()
