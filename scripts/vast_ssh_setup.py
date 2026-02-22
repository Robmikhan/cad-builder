"""Register local SSH key with Vast.ai account."""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

API_KEY = os.getenv("VAST_API_KEY", "").strip()
if not API_KEY:
    print("Set VAST_API_KEY environment variable")
    sys.exit(1)

# Find SSH public key
ssh_dir = Path.home() / ".ssh"
for name in ["id_ed25519.pub", "id_rsa.pub"]:
    pub = ssh_dir / name
    if pub.exists():
        ssh_key = pub.read_text().strip()
        print(f"Found SSH key: {pub}")
        print(f"  {ssh_key[:60]}...")
        break
else:
    print("No SSH public key found in ~/.ssh/")
    sys.exit(1)

# Upload to Vast.ai
print("\nRegistering SSH key with Vast.ai...")
body = json.dumps({"ssh_key": ssh_key}).encode()
req = urllib.request.Request(
    "https://console.vast.ai/api/v0/users/current/",
    data=body,
    method="PUT",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
)
try:
    r = urllib.request.urlopen(req)
    result = json.loads(r.read())
    print(f"  Response: {result}")
    print("  SSH key registered successfully!")
    print("\nYou may need to restart your Vast.ai instance for the key to take effect.")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"  Error {e.code}: {body}")
    # Try alternate endpoint format
    print("\nTrying alternate method...")
    try:
        body2 = json.dumps({"ssh_key": ssh_key}).encode()
        req2 = urllib.request.Request(
            "https://console.vast.ai/api/v0/ssh/",
            data=body2,
            method="PUT",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
        )
        r2 = urllib.request.urlopen(req2)
        print(f"  Response: {json.loads(r2.read())}")
        print("  SSH key registered!")
    except urllib.error.HTTPError as e2:
        print(f"  Error {e2.code}: {e2.read().decode()}")
        print("\n  Manual step: Go to https://cloud.vast.ai/account/")
        print(f"  Paste this SSH key in the 'SSH Key' field:")
        print(f"\n  {ssh_key}\n")
