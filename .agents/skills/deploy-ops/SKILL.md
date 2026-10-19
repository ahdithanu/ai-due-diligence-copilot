---
name: deploy-ops
description: Operational guidance for local testing tunnels, Docker container builds, Render 24/7 cloud hosting, and AWS CloudFormation deployments.
---

# Deploy Ops Skill

Use this skill when deploying the application, updating cloud configurations, or exposing live endpoints for testing.

## Local Tunnel (Ephemeral Demos)

To expose the local development server temporarily without cloud infrastructure:

1. Ensure the backend server is running:
   ```bash
   .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
2. Launch a public tunnel via Cloudflare:
   ```bash
   cloudflared tunnel --url http://127.0.0.1:8000 --logfile /tmp/cloudflared.log
   ```
3. Extract the active URL:
   ```bash
   grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' /tmp/cloudflared.log | head -1
   ```
*Note*: Ephemeral tunnels disconnect when the host machine sleeps or changes networks.

## Permanent 24/7 Cloud Hosting (Render Free Tier)

The repository includes a `render.yaml` blueprint:
1. Push changes to GitHub (`git push origin main`).
2. In [dashboard.render.com](https://dashboard.render.com), create a new **Blueprint** service pointing to this repository.
3. Render builds `Dockerfile.api` using dynamic port binding (`${PORT:-8000}`) and provisions a permanent HTTPS URL.

## Enterprise AWS Deployment (CloudFormation)

For enterprise customer environments requiring isolated VPCs and SOC 2 alignment:
1. Verify AWS authentication: `aws sts get-caller-identity` (requires unsandboxed execution).
2. Execute the deployment script:
   ```bash
   ./scripts/deploy.sh
   ```
   *Provisions VPC, NAT Gateway, Application Load Balancer, ECS Fargate, and RDS PostgreSQL.*
