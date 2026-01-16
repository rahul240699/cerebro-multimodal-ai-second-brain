#!/bin/bash

###############################################################################
# Cerebro AWS Cleanup Script
# Removes all AWS resources created by deploy-aws.sh
###############################################################################

set -e

PROJECT_NAME="cerebro"
AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${PROJECT_NAME}-stack"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
echo -e "${RED}║     Cerebro AWS Cleanup Script            ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}This will DELETE all Cerebro resources from AWS!${NC}"
echo -e "${YELLOW}Stack:${NC} ${STACK_NAME}"
echo -e "${YELLOW}Region:${NC} ${AWS_REGION}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo -e "${GREEN}Cleanup cancelled${NC}"
    exit 0
fi

# Delete CloudFormation stack
echo -e "\n${YELLOW}Deleting CloudFormation stack...${NC}"
aws cloudformation delete-stack \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION"

echo -e "${YELLOW}Waiting for stack deletion to complete (this may take 10-15 minutes)...${NC}"
aws cloudformation wait stack-delete-complete \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION"

# Delete ECR repositories
echo -e "\n${YELLOW}Deleting ECR repositories...${NC}"
for repo in "${PROJECT_NAME}-backend" "${PROJECT_NAME}-frontend"; do
    aws ecr delete-repository \
        --repository-name "$repo" \
        --region "$AWS_REGION" \
        --force 2>/dev/null || echo "Repository $repo not found"
done

echo -e "\n${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       CLEANUP COMPLETED! ✓                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
