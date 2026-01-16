#!/bin/bash

###############################################################################
# Update Frontend to use CloudFront HTTPS URL
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_NAME="cerebro"
AWS_REGION="us-east-1"

# Get CloudFront URL from saved file
if [ ! -f cloudfront-urls.txt ]; then
    echo -e "${RED}Error: cloudfront-urls.txt not found${NC}"
    echo -e "${YELLOW}Run ./setup-cloudfront-ssl.sh first${NC}"
    exit 1
fi

source cloudfront-urls.txt

# Frontend should make relative API calls since CloudFront handles routing
BACKEND_API_URL="${CLOUDFRONT_URL}"

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Updating Frontend for CloudFront        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo -e "\n${YELLOW}CloudFront URL: ${CLOUDFRONT_URL}${NC}"
echo -e "${YELLOW}API calls will be relative to CloudFront${NC}"

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Login to ECR
echo -e "\n${YELLOW}Logging into ECR...${NC}"
aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Build frontend with CloudFront URL
echo -e "\n${YELLOW}Building frontend with HTTPS backend URL...${NC}"
cd frontend
docker buildx build --platform linux/amd64 \
    --build-arg NEXT_PUBLIC_API_URL="${BACKEND_API_URL}" \
    -t "${PROJECT_NAME}-frontend" .
docker tag "${PROJECT_NAME}-frontend:latest" \
    "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${PROJECT_NAME}-frontend:latest"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${PROJECT_NAME}-frontend:latest"
echo -e "${GREEN}✓ Frontend image updated with HTTPS URL${NC}"
cd ..

# Force ECS to redeploy frontend
echo -e "\n${YELLOW}Redeploying frontend service...${NC}"
aws ecs update-service \
    --cluster cerebro-cluster \
    --service cerebro-frontend \
    --force-new-deployment \
    --region us-east-1 > /dev/null

echo -e "\n${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Update Complete! 🎉                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo -e "\n${YELLOW}Wait 2-3 minutes for ECS to redeploy, then:${NC}"
echo -e "${GREEN}1. Visit: ${CLOUDFRONT_URL}${NC}"
echo -e "${GREEN}2. Upload documents - should work now!${NC}"
echo -e "${GREEN}3. Record audio - HTTPS enables microphone access${NC}"
echo ""
echo -e "${YELLOW}Clear CloudFront cache to see changes immediately:${NC}"
echo -e "  aws cloudfront create-invalidation --distribution-id ${DISTRIBUTION_ID} --paths '/*'"
echo ""
