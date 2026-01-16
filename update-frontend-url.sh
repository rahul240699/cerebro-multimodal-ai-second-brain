#!/bin/bash

###############################################################################
# Update Frontend with Correct Backend URL
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_NAME="cerebro"
AWS_REGION="us-east-1"

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get the ALB URL from CloudFormation
ALB_URL=$(aws cloudformation describe-stacks \
    --stack-name cerebro-stack \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
    --output text)

BACKEND_API_URL="${ALB_URL}/api"

echo -e "${YELLOW}Current ALB URL: ${ALB_URL}${NC}"
echo -e "${YELLOW}Backend API URL: ${BACKEND_API_URL}${NC}"

# Login to ECR
echo -e "\n${YELLOW}Logging into ECR...${NC}"
aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Build frontend with correct API URL
echo -e "\n${YELLOW}Building frontend with correct backend URL...${NC}"
cd frontend
docker buildx build --platform linux/amd64 \
    --build-arg NEXT_PUBLIC_API_URL="${BACKEND_API_URL}" \
    -t "${PROJECT_NAME}-frontend" .
docker tag "${PROJECT_NAME}-frontend:latest" \
    "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${PROJECT_NAME}-frontend:latest"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${PROJECT_NAME}-frontend:latest"
echo -e "${GREEN}✓ Frontend image updated${NC}"
cd ..

# Force ECS to redeploy frontend service
echo -e "\n${YELLOW}Forcing ECS service to redeploy...${NC}"
aws ecs update-service \
    --cluster cerebro-cluster \
    --service cerebro-frontend \
    --force-new-deployment \
    --region us-east-1 > /dev/null

echo -e "\n${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Frontend Updated Successfully! ✓      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo -e "\n${YELLOW}Wait 2-3 minutes for the service to redeploy.${NC}"
echo -e "${YELLOW}Frontend URL: ${ALB_URL}${NC}"
echo ""
echo -e "${RED}NOTE: For HTTPS and audio recording support, you need:${NC}"
echo -e "${YELLOW}1. A custom domain (e.g., cerebro.yourdomain.com)${NC}"
echo -e "${YELLOW}2. SSL certificate from AWS Certificate Manager${NC}"
echo -e "${YELLOW}3. Update ALB listener to use HTTPS${NC}"
echo ""
