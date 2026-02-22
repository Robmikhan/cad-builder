#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# CAD Builder — One-Command Cloud Deployment
# Usage: ./scripts/deploy.sh [DOMAIN]
# Example: ./scripts/deploy.sh cadbuilder.io
#          ./scripts/deploy.sh        (uses IP, no SSL)
# ============================================================

DOMAIN="${1:-}"
REPO_URL="https://github.com/YOUR_USERNAME/cad-builder.git"
INSTALL_DIR="/opt/cad-builder"

echo "╔══════════════════════════════════════╗"
echo "║   CAD Builder — Production Deploy    ║"
echo "╚══════════════════════════════════════╝"

# ── 1. System prerequisites ──
echo ""
echo "▶ [1/7] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq git curl docker.io docker-compose-plugin > /dev/null 2>&1

# NVIDIA Container Toolkit (for GPU inside Docker)
if ! command -v nvidia-container-cli &> /dev/null; then
    echo "  Installing NVIDIA Container Toolkit..."
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
        gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null
    apt-get update -qq
    apt-get install -y -qq nvidia-container-toolkit > /dev/null 2>&1
    nvidia-ctk runtime configure --runtime=docker
    systemctl restart docker
fi

# ── 2. Clone or update repo ──
echo ""
echo "▶ [2/7] Setting up application..."
if [ -d "$INSTALL_DIR" ]; then
    echo "  Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull --ff-only 2>/dev/null || true
else
    echo "  Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR" 2>/dev/null || {
        echo "  ⚠ Could not clone from git. Assuming files are already in place."
        mkdir -p "$INSTALL_DIR"
    }
    cd "$INSTALL_DIR"
fi

# ── 3. Configure environment ──
echo ""
echo "▶ [3/7] Configuring environment..."
if [ ! -f .env ]; then
    cp .env.production .env
    # Generate a random admin API key
    ADMIN_KEY="cad_admin_$(openssl rand -hex 16)"
    sed -i "s|^CAD_AGENT_API_KEYS=.*|CAD_AGENT_API_KEYS=${ADMIN_KEY}|" .env
    echo "  ✅ Generated admin API key: ${ADMIN_KEY}"
    echo "  ⚠  SAVE THIS KEY — you'll need it to access the API"
fi

# Set domain
if [ -n "$DOMAIN" ]; then
    sed -i "s|^DOMAIN=.*|DOMAIN=${DOMAIN}|" .env
    echo "  Domain: ${DOMAIN} (SSL will auto-provision via Let's Encrypt)"
else
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
    sed -i "s|^DOMAIN=.*|DOMAIN=:80|" .env
    echo "  No domain specified — serving on http://${SERVER_IP}"
fi

# ── 4. Build Docker images ──
echo ""
echo "▶ [4/7] Building Docker images (this takes 5-10 minutes on first run)..."
docker compose -f docker/docker-compose.prod.yml build

# ── 5. Start services ──
echo ""
echo "▶ [5/7] Starting services..."
docker compose -f docker/docker-compose.prod.yml up -d

# ── 6. Pull Ollama model ──
echo ""
echo "▶ [6/7] Downloading AI model (qwen2.5-coder:7b, ~4.7GB)..."
echo "  Waiting for Ollama to start..."
sleep 10
docker compose -f docker/docker-compose.prod.yml exec ollama ollama pull qwen2.5-coder:7b

# ── 7. Verify ──
echo ""
echo "▶ [7/7] Verifying deployment..."
sleep 5
HEALTH=$(curl -sf http://localhost:8080/api/health 2>/dev/null || echo "FAILED")

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        Deployment Complete!          ║"
echo "╚══════════════════════════════════════╝"
echo ""

if echo "$HEALTH" | grep -q '"ok"'; then
    echo "✅ Health check: PASSED"
else
    echo "⚠  Health check: PENDING (may still be starting up)"
    echo "   Check with: curl http://localhost:8080/api/health"
fi

echo ""
if [ -n "$DOMAIN" ]; then
    echo "🌐 Your app: https://${DOMAIN}"
else
    echo "🌐 Your app: http://${SERVER_IP:-localhost}"
fi
echo ""
echo "📋 Admin API key is in .env (CAD_AGENT_API_KEYS)"
echo ""
echo "Useful commands:"
echo "  docker compose -f docker/docker-compose.prod.yml logs -f    # View logs"
echo "  docker compose -f docker/docker-compose.prod.yml restart    # Restart"
echo "  docker compose -f docker/docker-compose.prod.yml down       # Stop"
echo ""
