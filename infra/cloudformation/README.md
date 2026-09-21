# AWS CloudFormation Deployment Guide

This directory contains the production AWS CloudFormation template for the **AI Due Diligence Copilot**.

## Architecture Overview
- **VPC & Networking**: Dedicated 2-AZ VPC with Public & Private Subnets, Internet Gateway, and NAT Gateway.
- **Application Load Balancer (ALB)**: Internet-facing load balancer with `/health` checks.
- **ECS Fargate Cluster**:
  - `diligence-api`: FastAPI backend serving the compiled React frontend, analytics APIs, and RAG retrieval.
  - `diligence-worker`: Asynchronous background worker executing long-running diligence workflows and canary runs.
- **RDS PostgreSQL**: Private Multi-AZ capable PostgreSQL 15 database instance with encrypted storage.
- **ECR Repositories**: Encrypted container registries for `diligence-api` and `diligence-worker`.
- **AWS Secrets Manager**: Encrypted secret store for database credentials, Gemini API key, and OpenAI API key.
- **CloudWatch Logs**: Centralized structured logging for API and Worker containers with 30-day retention.

---

## Method 1: Deploy via AWS Console (Zero CLI Setup Required)

1. Open the [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation).
2. Click **Create stack** -> **With new resources (standard)**.
3. Under **Template source**, select **Upload a template file**.
4. Choose `infra/cloudformation/template.yaml` and click **Next**.
5. Fill in the parameters:
   - **Stack name**: `diligence-copilot-prod`
   - **DBMasterPassword**: Set a strong database password (e.g. `Pr0dDiligence2026!`).
   - **GeminiApiKey**: Your Google Gemini API Key.
   - **OpenAiApiKey**: *(Optional)* Your OpenAI API Key for fallback model routing.
6. Click **Next** -> acknowledge IAM capabilities checkbox (`I acknowledge that AWS CloudFormation might create IAM resources with custom names`).
7. Click **Submit**. CloudFormation will provision all resources (~10-15 minutes).

---

## Method 2: Deploy via AWS CLI

### 1. Build and Push Container Images to ECR
First, create the ECR repositories or run the stack creation to output repository URIs:
```bash
# Set your AWS Account ID & Region
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Authenticate Docker with ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Build and push API container (includes frontend bundle)
docker build -f Dockerfile.api -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/production-diligence-api:latest .
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/production-diligence-api:latest

# Build and push Worker container
docker build -f Dockerfile.worker -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/production-diligence-worker:latest .
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/production-diligence-worker:latest
```

### 2. Deploy CloudFormation Stack
```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/template.yaml \
  --stack-name diligence-copilot-prod \
  --parameter-overrides \
      DBMasterPassword="YOUR_STRONG_PASSWORD" \
      GeminiApiKey="YOUR_GEMINI_API_KEY" \
      OpenAiApiKey="YOUR_OPENAI_API_KEY" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### 3. Retrieve Load Balancer URL
```bash
aws cloudformation describe-stacks \
  --stack-name diligence-copilot-prod \
  --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
  --output text
```
Open the returned URL in your browser to access the live copilot!
