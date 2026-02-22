# CAD Builder — Production Deployment Guide

## Quick Start (5 minutes)

### 1. Rent a GPU Server

**Vast.ai** (cheapest, ~$17-25/mo for RTX 3060 12GB):

```bash
# From your local machine:
export VAST_API_KEY="your_vastai_api_key"
python scripts/vast_deploy.py
```

This finds the cheapest GPU and rents it. You'll get SSH credentials.

**Alternatives:**
| Provider | GPU | Price | Notes |
|----------|-----|-------|-------|
| [Vast.ai](https://vast.ai) | RTX 3060 12GB | ~$0.024/hr ($17/mo) | Cheapest |
| [RunPod](https://runpod.io) | RTX 3090 24GB | ~$0.22/hr ($160/mo) | Reliable |
| [Lambda](https://lambdalabs.com) | A10 24GB | ~$0.60/hr ($438/mo) | Enterprise |
| [AWS](https://aws.amazon.com) | T4 16GB (g4dn.xlarge) | ~$0.526/hr ($384/mo) | Corporate |

### 2. SSH In and Deploy

```bash
ssh -p PORT root@HOST

# Clone the repository
git clone https://github.com/YOUR_USERNAME/cad-builder.git /opt/cad-builder
cd /opt/cad-builder

# One-command deploy
bash scripts/deploy.sh yourdomain.com
```

The script will:
- Install Docker + NVIDIA Container Toolkit
- Build all Docker images (API, Worker, Ollama, Caddy)
- Generate an admin API key
- Download the AI model (~4.7GB)
- Start everything with auto-SSL

### 3. Point Your Domain

Add a DNS **A record** pointing your domain to the server's IP address:

```
Type: A
Name: @ (or subdomain like "cad")
Value: SERVER_IP_ADDRESS
TTL: 300
```

Caddy automatically provisions SSL via Let's Encrypt once DNS propagates (~2-5 minutes).

### 4. Verify

```bash
curl https://yourdomain.com/api/health
# {"status":"ok","version":"0.2.0","uptime_sec":...}
```

Visit `https://yourdomain.com` in your browser — you should see the landing page.

---

## Architecture

```
Internet → Caddy (:443 SSL) → FastAPI API (:8080) → Ollama (:11434)
                                    ↓
                               Worker (background)
                                    ↓
                            GPU (TripoSR, rembg)
```

All services run as Docker containers with GPU passthrough.

## Configuration

Edit `.env` on the server:

| Variable | Default | Description |
|----------|---------|-------------|
| `DOMAIN` | `localhost` | Your domain for auto-SSL |
| `CAD_AGENT_API_KEYS` | (generated) | Comma-separated admin API keys |
| `STRIPE_LINK_STARTER` | | Stripe payment link for $19/mo tier |
| `STRIPE_LINK_PRO` | | Stripe payment link for $49/mo tier |
| `STRIPE_LINK_BUSINESS` | | Stripe payment link for $149/mo tier |
| `CAD_AGENT_RATE_LIMIT` | `60` | Requests per window per IP |
| `CAD_AGENT_RATE_WINDOW_SEC` | `60` | Rate limit window (seconds) |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | LLM model name |

## Operations

```bash
cd /opt/cad-builder

# View logs
docker compose -f docker/docker-compose.prod.yml logs -f

# View specific service
docker compose -f docker/docker-compose.prod.yml logs -f api

# Restart everything
docker compose -f docker/docker-compose.prod.yml restart

# Stop
docker compose -f docker/docker-compose.prod.yml down

# Update (pull latest code + rebuild)
git pull
docker compose -f docker/docker-compose.prod.yml up -d --build

# Check GPU usage
nvidia-smi
```

## Stripe Setup (Monetization)

1. Go to [Stripe Dashboard](https://dashboard.stripe.com) → Products
2. Create three products:
   - **Starter** — $19/month (recurring)
   - **Pro** — $49/month (recurring)
   - **Business** — $149/month (recurring)
3. For each product, click "Create payment link"
4. Copy each link into `.env`:
   ```
   STRIPE_LINK_STARTER=https://buy.stripe.com/xxx
   STRIPE_LINK_PRO=https://buy.stripe.com/yyy
   STRIPE_LINK_BUSINESS=https://buy.stripe.com/zzz
   ```
5. Restart: `docker compose -f docker/docker-compose.prod.yml restart api`

When a customer pays, manually generate their API key:
```bash
docker compose -f docker/docker-compose.prod.yml exec api \
  python -c "from services.api.quotas import create_paid_key; print(create_paid_key('starter', 'customer@email.com'))"
```

## No Domain? (IP-only access)

If you don't have a domain yet, the deploy script serves on port 80:

```bash
bash scripts/deploy.sh
# Access at: http://SERVER_IP
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `nvidia-smi` not found | GPU drivers not installed. Use a Vast.ai/RunPod template with CUDA pre-installed |
| Health check fails | `docker compose logs api` — check for startup errors |
| Ollama model not found | `docker compose exec ollama ollama pull qwen2.5-coder:7b` |
| SSL not working | Check DNS propagation: `dig yourdomain.com` should show server IP |
| Out of GPU memory | Use a machine with 12GB+ VRAM, or reduce batch size |

## Cost Summary

| Component | Monthly Cost |
|-----------|-------------|
| Vast.ai RTX 3060 | ~$17-25 |
| Domain (.com) | ~$1 |
| **Total** | **~$18-26/mo** |

Break-even: **2 Starter customers** ($38/mo revenue vs $25/mo cost).
