# Deployment Planning

This document captures all deployment decisions, rationale, and alternatives considered for Kibitzer.

## Scale & Constraints

- **Target audience:** Personal use + friends. ~100 users max.
- **Traffic pattern:** Low and bursty. A few concurrent users at most.
- **Budget priority:** Minimize ongoing cost. Free/cheap tiers preferred.
- **Ops priority:** Minimize maintenance burden. This is a side project, not a job.
- **Implication:** We can use simpler infrastructure that would not scale to thousands
  of users but is perfectly fine for our needs. No need for load balancers, auto-scaling,
  multi-region, or high-availability setups.

---

## Current State (as of 2026-03-09)

### What we have

| Asset | Status | Notes |
|-------|--------|-------|
| **Dockerfile** | Done | Multi-stage build (Node 22 → Python 3.12), health check, single-worker uvicorn |
| **docker-compose.yml** | Done | Single service, volume mount for SQLite, port 8000 |
| **.env.example** | Done | SECRET_KEY, ANTHROPIC_API_KEY, DATABASE_URL, LOG_LEVEL, CORS_ORIGINS |
| **.dockerignore** | Done | Properly excludes .git, venv, node_modules, tests, .env |
| **Health endpoint** | Done | `GET /api/health` returns 200 |

### What we don't have

| Gap | Impact |
|-----|--------|
| **CI/CD pipeline** | No automated tests, lint, or deploy on push |
| **Hosting target** | No cloud platform chosen or configured |
| **Infrastructure-as-code** | No Terraform, CDK, or platform config (fly.toml, etc.) |
| **HTTPS / TLS** | Cookies set with `secure=False`; no reverse proxy or cert management |
| **Database for production** | SQLite limits to single worker, no concurrent writes, no horizontal scaling |
| **Secret management** | Env vars only; no vault or managed secrets |
| **Monitoring / logging** | Local stdout only; no centralized logs or metrics |
| **Domain / DNS** | No custom domain configured |
| **Backup strategy** | No database or volume backup plan |

### Architecture summary

```
Browser ──► FastAPI (uvicorn, port 8000)
              ├── /api/*          Python backend (auth, practice, analyze)
              ├── /static/*       Vite-built React assets
              └── /*              SPA catch-all → index.html
                    │
                    ▼
              SQLite (file: /app/data/bridge.db)
              Anthropic API (optional, for LLM explanations)
```

Single container serves both frontend and API. Database is an embedded SQLite file.

---

## Decisions

> Each section below records a decision, why we chose it, and what else we considered.
> Format: **Decision**, then *Why*, then *Alternatives considered*.

### 1. Hosting Platform

**Decision: Home machine + Cloudflare Tunnel**

*Why:* Cheapest "always on" option (~$10/yr for domain). Home internet is reliable.
Full control over the machine. No port forwarding needed -- cloudflared makes outbound
connections to Cloudflare's edge. Free TLS, DDoS protection, and CDN from Cloudflare.
Future iPhone app just hits the same domain.

*Alternatives considered:*

| Platform | Cost (est.) | Why not |
|----------|-------------|---------|
| Fly.io | ~$0-5/mo | Free tier terms have shifted; paying monthly for something we can host for free |
| Railway | ~$5/mo | Ongoing cost with no upside over self-hosting at our scale |
| Render free | $0 | Sleeps after 15min inactivity -- 30-60s cold starts unacceptable for mobile app |
| Render paid | $7/mo | $84/yr vs $10/yr for a domain |
| DigitalOcean / Hetzner VPS | $4-6/mo | Paying for a server when we have one at home |

### 2. Database (Production)

**Decision: Keep SQLite**

*Why:* Already works. ~100 users with low concurrency means the single-writer
limitation is a non-issue. Running on our own hardware means no "persistent volume"
concern -- the DB file lives on disk. Zero ops, no extra service, backup = copy a file.

*Alternatives considered:*
- PostgreSQL (managed) -- extra cost and migration effort for no benefit at our scale
- SQLite + Litestream -- could add later if we want continuous backups, not needed now

### 3. CI/CD Pipeline

**Decision: Skip for now -- manual deploy**

*Why:* Pre-commit hooks already run ruff + mypy locally. Deploy is just
`git pull && docker compose up -d --build` on the home machine. Not worth the
setup overhead of GitHub Actions for a solo/small project. Can revisit if it
becomes painful.

### 4. Domain & DNS

**Decision: Custom domain via Cloudflare Registrar**

*Why:* Required for Cloudflare Tunnel. Cloudflare Registrar sells domains at cost
(no markup). DNS is managed in the same Cloudflare dashboard as the tunnel. ~$10/yr.

*No alternatives -- Cloudflare Tunnel requires a domain with Cloudflare DNS.*

### 5. TLS / HTTPS

**Decision: Cloudflare-managed TLS (automatic)**

*Why:* Comes free with Cloudflare Tunnel. Cloudflare terminates TLS at their edge.
Auto-renewing certs, zero config. No need for Caddy, Let's Encrypt, or certbot.

*Need to update:* Set `secure=True` on auth cookies once HTTPS is live.

### 6. Secret Management

**Decision: .env file on home machine**

*Why:* We have 2 secrets (SECRET_KEY, ANTHROPIC_API_KEY). Docker compose reads from
`.env` file. The machine is on our home network. This is the simplest option and
perfectly adequate at our scale.

*Alternative considered:* Docker secrets -- adds complexity for no real benefit with 2 values.

### 7. Monitoring & Logging

**Decision: Skip for now -- Docker logs + health endpoint**

*Why:* `docker compose logs` is good enough to debug issues when they come up.
Health endpoint exists at `/api/health`. Can add UptimeRobot (free, pings every
5min and alerts on downtime) later if we want to know about outages proactively.

### 8. Backup Strategy

**Decision: Accept the risk for now**

*Why:* Only real data is user accounts (~10-100 rows). Practice sessions are ephemeral.
Worst case = friends re-register. Can add a cron job to copy the SQLite file later
if the data becomes more valuable.

---

## Setup Checklist

All decisions made. Steps to get live:

- [ ] Buy domain via Cloudflare Registrar
- [ ] Set up Cloudflare account + DNS
- [ ] Set up home machine (install Docker, clone repo)
- [ ] Create `.env` with SECRET_KEY and ANTHROPIC_API_KEY
- [ ] `docker compose up -d --build`
- [ ] Install `cloudflared`, create tunnel, point domain at localhost:8000
- [ ] Run `cloudflared` as systemd service (auto-start on boot)
- [ ] Set `secure=True` on auth cookies
- [ ] Test from outside network
- [ ] Share URL with friends

---

## Notes

*Space for ongoing observations and learnings as we deploy.*
