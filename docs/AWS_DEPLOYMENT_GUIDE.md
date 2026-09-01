# AWS Enterprise Deployment Guide - AI Investment Due Diligence Copilot

This guide provides step-by-step instructions for deploying the **AI Investment Due Diligence Copilot** to **Amazon Web Services (AWS)** using enterprise best practices.

---

## 🏗️ AWS Cloud Architecture

```mermaid
flowchart TD
    subgraph AWS Cloud Infrastructure (us-east-1)
        subgraph Networking & Edge
            CloudFront["Amazon CloudFront CDN\n(Frontend SPA Delivery)"]
            ALB["Application Load Balancer (ALB)\n(HTTPS SSL Endpoint)"]
        end

        subgraph Container Compute (AWS ECS Fargate)
            ECS_API["AWS ECS Fargate: API Container\n(Dockerfile.api - FastAPI Server)"]
            ECS_Worker["AWS ECS Fargate: Worker Container\n(Dockerfile.worker - Background Queue Worker)"]
        end

        subgraph Database & Document Storage
            RDS["Amazon RDS PostgreSQL\n(Persistent Investment & Checkpoint Data)"]
            S3["Amazon S3 Bucket\n(Pitch Deck & Diligence Document Storage)"]
        end

        subgraph Security & Observability
            SecretsManager["AWS Secrets Manager / SSM\n(GEMINI_API_KEY, OPENAI_API_KEY)"]
            CloudWatch["Amazon CloudWatch\n(Container Logs & SLA Telemetry)"]
        end
    end

    User["User Browser"] --> CloudFront & ALB
    ALB --> ECS_API
    ECS_API <--> RDS & S3
    ECS_Worker <--> RDS & S3
    ECS_API & ECS_Worker -.-> SecretsManager & CloudWatch
```

---

## 🚀 Deployment Option 1: AWS App Runner (Fastest & Simplest - 5 Mins)

AWS App Runner provides fully managed container deployment directly from your GitHub repository.

### Steps:
1. Open the [AWS App Runner Console](https://console.aws.amazon.com/apprunner/home).
2. Click **Create an App Runner service**.
3. Select **Source code repository** $\rightarrow$ Connect your GitHub account **`ahdithanu`**.
4. Select repository **`ahdithanu/ai-due-diligence-copilot`** and branch **`main`**.
5. Set deployment settings:
   - **Build Provider**: Use configuration file or set `Dockerfile.api`.
   - **Port**: `8000`.
6. Add Environment Variables:
   - `LLM_PROVIDER`: `gemini` (or `openai`)
   - `GEMINI_API_KEY`: Your Gemini API key
   - `OPENAI_API_KEY`: Your OpenAI API key
7. Click **Create & Deploy**.
8. App Runner will output a live HTTPS URL (e.g. `https://xxxxxx.us-east-1.awsapprunner.com`).

---

## 🛡️ Deployment Option 2: AWS Copilot CLI (Enterprise ECS Fargate + RDS)

AWS Copilot is the official AWS CLI tool for launching production microservices on ECS Fargate.

### Step 1: Install AWS Copilot CLI
```bash
# macOS via Homebrew
brew install aws-copilot-cli
```

### Step 2: Initialize Application
```bash
cd "/Users/ahdithebomb/Documents/AI Due Diligence Copilot "

# Initialize Copilot app
copilot app init diligence-copilot
```

### Step 3: Launch API Service
```bash
copilot svc init \
  --name api \
  --svc-type "Load Balanced Web Service" \
  --dockerfile "./Dockerfile.api" \
  --port 8000
```

### Step 4: Launch Background Graph Worker
```bash
copilot svc init \
  --name worker \
  --svc-type "Backend Service" \
  --dockerfile "./Dockerfile.worker"
```

### Step 5: Deploy Environments
```bash
# Deploy Staging Environment
copilot env init --name staging --profile default --default
copilot deploy --env staging

# Deploy Production Environment
copilot env init --name production --profile default
copilot deploy --env production
```

---

## ⚙️ Environment Variables Required on AWS

| Variable Name | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | Primary LLM Provider | `gemini` or `openai` |
| `GEMINI_API_KEY` | Google Gemini API Key | `AIzaSy...` |
| `OPENAI_API_KEY` | OpenAI API Key | `sk-proj-...` |
| `DATABASE_URL` | RDS PostgreSQL Connection String | `postgresql+asyncpg://user:pass@rds-endpoint:5432/diligence_db` |
| `ENVIRONMENT` | Environment Name | `production` |
