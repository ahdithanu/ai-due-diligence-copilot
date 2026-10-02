#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# AI Due Diligence Copilot — AWS Deployment Script
# Deploys: ECS Fargate (API + Worker) + RDS PostgreSQL + ALB
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --------------- Configuration ---------------
STACK_NAME="${STACK_NAME:-diligence-copilot-prod}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-production}"
DB_MASTER_PASSWORD="${DB_MASTER_PASSWORD:-}"
GEMINI_API_KEY="${GEMINI_API_KEY:-}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# --------------- Colors ---------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[deploy]${NC} $1"; }
ok()   { echo -e "${GREEN}  ✓${NC} $1"; }
warn() { echo -e "${YELLOW}  ⚠${NC} $1"; }
err()  { echo -e "${RED}  ✗${NC} $1"; exit 1; }

# --------------- Pre-flight checks ---------------
log "Running pre-flight checks..."

command -v aws >/dev/null 2>&1  || err "AWS CLI not found. Install: brew install awscli"
command -v docker >/dev/null 2>&1 || err "Docker not found. Install Docker Desktop first."

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null) \
  || err "AWS not authenticated. Run: aws configure"
ok "AWS Account: $AWS_ACCOUNT_ID (Region: $AWS_REGION)"

# Check Docker daemon
docker info >/dev/null 2>&1 || err "Docker daemon not running. Start Docker Desktop."
ok "Docker daemon running"

# --------------- Prompt for secrets if not set ---------------
if [ -z "$DB_MASTER_PASSWORD" ]; then
  echo -en "${YELLOW}  Enter RDS database password (min 8 chars): ${NC}"
  read -rs DB_MASTER_PASSWORD
  echo ""
  if [ ${#DB_MASTER_PASSWORD} -lt 8 ]; then
    err "Password must be at least 8 characters"
  fi
fi

if [ -z "$GEMINI_API_KEY" ]; then
  echo -en "${YELLOW}  Enter Gemini API Key (or press Enter to skip): ${NC}"
  read -rs GEMINI_API_KEY
  echo ""
fi

if [ -z "$OPENAI_API_KEY" ]; then
  echo -en "${YELLOW}  Enter OpenAI API Key (or press Enter to skip): ${NC}"
  read -rs OPENAI_API_KEY
  echo ""
fi

# --------------- Derived values ---------------
API_REPO="${ENVIRONMENT}-diligence-api"
WORKER_REPO="${ENVIRONMENT}-diligence-worker"
API_IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${API_REPO}:${IMAGE_TAG}"
WORKER_IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${WORKER_REPO}:${IMAGE_TAG}"

# ============================================================
# STEP 1: Deploy CloudFormation stack (creates ECR repos + infra)
# ============================================================
log "Step 1/4 — Deploying CloudFormation stack '${STACK_NAME}'..."

cd "$PROJECT_ROOT"

aws cloudformation deploy \
  --template-file infra/cloudformation/template.yaml \
  --stack-name "$STACK_NAME" \
  --parameter-overrides \
      EnvironmentName="$ENVIRONMENT" \
      DBMasterPassword="$DB_MASTER_PASSWORD" \
      GeminiApiKey="${GEMINI_API_KEY:-placeholder}" \
      OpenAiApiKey="${OPENAI_API_KEY:-placeholder}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --no-fail-on-empty-changeset \
  2>&1 | while IFS= read -r line; do echo "    $line"; done

ok "CloudFormation stack deployed/updated"

# ============================================================
# STEP 2: Authenticate Docker with ECR
# ============================================================
log "Step 2/4 — Authenticating Docker with ECR..."

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin \
    "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com" \
  2>&1 | while IFS= read -r line; do echo "    $line"; done

ok "Docker authenticated with ECR"

# ============================================================
# STEP 3: Build and push container images
# ============================================================
log "Step 3/4 — Building and pushing container images..."

log "  Building API image (includes frontend bundle)..."
docker build \
  --platform linux/amd64 \
  -f Dockerfile.api \
  -t "$API_IMAGE_URI" \
  . 2>&1 | tail -5 | while IFS= read -r line; do echo "    $line"; done
ok "API image built"

log "  Pushing API image to ECR..."
docker push "$API_IMAGE_URI" 2>&1 | tail -3 | while IFS= read -r line; do echo "    $line"; done
ok "API image pushed: $API_IMAGE_URI"

log "  Building Worker image..."
docker build \
  --platform linux/amd64 \
  -f Dockerfile.worker \
  -t "$WORKER_IMAGE_URI" \
  . 2>&1 | tail -5 | while IFS= read -r line; do echo "    $line"; done
ok "Worker image built"

log "  Pushing Worker image to ECR..."
docker push "$WORKER_IMAGE_URI" 2>&1 | tail -3 | while IFS= read -r line; do echo "    $line"; done
ok "Worker image pushed: $WORKER_IMAGE_URI"

# ============================================================
# STEP 4: Force ECS service update (pull new images)
# ============================================================
log "Step 4/4 — Forcing ECS service redeployment..."

CLUSTER_NAME="${ENVIRONMENT}-diligence-cluster"
API_SERVICE="${ENVIRONMENT}-diligence-api"
WORKER_SERVICE="${ENVIRONMENT}-diligence-worker"

aws ecs update-service \
  --cluster "$CLUSTER_NAME" \
  --service "$API_SERVICE" \
  --force-new-deployment \
  --region "$AWS_REGION" \
  --query 'service.serviceName' \
  --output text 2>&1 | while IFS= read -r line; do echo "    $line"; done
ok "API service redeployment triggered"

aws ecs update-service \
  --cluster "$CLUSTER_NAME" \
  --service "$WORKER_SERVICE" \
  --force-new-deployment \
  --region "$AWS_REGION" \
  --query 'service.serviceName' \
  --output text 2>&1 | while IFS= read -r line; do echo "    $line"; done
ok "Worker service redeployment triggered"

# ============================================================
# OUTPUT: Live URL
# ============================================================
echo ""
log "============================================"
log "  🚀 DEPLOYMENT COMPLETE"
log "============================================"

LIVE_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
  --output text \
  --region "$AWS_REGION" 2>/dev/null || echo "pending...")

echo ""
echo -e "  ${GREEN}🌐 Live URL:${NC}  ${LIVE_URL}"
echo -e "  ${GREEN}📊 Stack:${NC}     ${STACK_NAME}"
echo -e "  ${GREEN}🏗️  Region:${NC}    ${AWS_REGION}"
echo -e "  ${GREEN}🐳 API:${NC}       ${API_IMAGE_URI}"
echo -e "  ${GREEN}⚙️  Worker:${NC}    ${WORKER_IMAGE_URI}"
echo ""
echo -e "  ${CYAN}Monitor deployment:${NC}"
echo -e "    aws ecs describe-services --cluster ${CLUSTER_NAME} --services ${API_SERVICE} --region ${AWS_REGION} --query 'services[0].deployments'"
echo ""
echo -e "  ${CYAN}View logs:${NC}"
echo -e "    aws logs tail /ecs/${ENVIRONMENT}-diligence-api --region ${AWS_REGION} --follow"
echo ""
