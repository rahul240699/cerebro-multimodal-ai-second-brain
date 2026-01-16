#!/bin/bash

###############################################################################
# Initialize PostgreSQL Database
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Initializing PostgreSQL database...${NC}"

# Get RDS endpoint and password from CloudFormation
RDS_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name cerebro-stack \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
    --output text)

echo -e "${YELLOW}RDS Endpoint: ${RDS_ENDPOINT}${NC}"

# The database password is in the CloudFormation parameters (default: CerebroPass123!)
DB_PASSWORD="CerebroPass123!"

echo -e "\n${YELLOW}Creating 'cerebro' database...${NC}"

# We need to connect from an EC2 instance or use the backend container
# Let's use the backend ECS task to run the command

TASK_ARN=$(aws ecs list-tasks \
    --cluster cerebro-cluster \
    --service-name cerebro-backend \
    --region us-east-1 \
    --query 'taskArns[0]' \
    --output text)

if [ "$TASK_ARN" == "None" ] || [ -z "$TASK_ARN" ]; then
    echo -e "${RED}No running backend tasks found. Wait for backend to start.${NC}"
    exit 1
fi

echo -e "${YELLOW}Using backend task: ${TASK_ARN}${NC}"

# Execute command in the backend container to create database
echo -e "${YELLOW}Creating database via backend container...${NC}"

aws ecs execute-command \
    --cluster cerebro-cluster \
    --task "${TASK_ARN}" \
    --container backend \
    --command "PGPASSWORD=${DB_PASSWORD} psql -h ${RDS_ENDPOINT} -U postgres -d postgres -c 'CREATE DATABASE cerebro;'" \
    --interactive \
    --region us-east-1 2>/dev/null || echo "Database might already exist or command failed"

# Alternative: Run Python script to initialize
echo -e "\n${YELLOW}Running database initialization from backend...${NC}"

aws ecs execute-command \
    --cluster cerebro-cluster \
    --task "${TASK_ARN}" \
    --container backend \
    --command "python -c \"from app.core.database import init_db; init_db(); print('Database initialized')\"" \
    --interactive \
    --region us-east-1

echo -e "\n${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Database Initialized! ✓                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo -e "\n${YELLOW}Restarting backend service...${NC}"

aws ecs update-service \
    --cluster cerebro-cluster \
    --service cerebro-backend \
    --force-new-deployment \
    --region us-east-1 > /dev/null

echo -e "${GREEN}✓ Backend restarting${NC}"
echo -e "${YELLOW}Wait 2 minutes then try uploading again${NC}"
