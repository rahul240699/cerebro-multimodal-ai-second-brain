#!/bin/bash

# Resume AWS ECS Deployment (Scale back to normal)

set -e

REGION="us-east-1"
CLUSTER="cerebro-cluster"

echo "▶️  Resuming Cerebro deployment..."
echo ""

# Check if RDS is stopped
DB_STATUS=$(aws rds describe-db-instances --db-instance-identifier cerebro-db --region $REGION --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null || echo "unknown")

if [ "$DB_STATUS" == "stopped" ]; then
    echo "📊 Starting RDS database..."
    aws rds start-db-instance --db-instance-identifier cerebro-db --region $REGION
    echo "⏳ Waiting for database to start (this takes 3-5 minutes)..."
    aws rds wait db-instance-available --db-instance-identifier cerebro-db --region $REGION
    echo "✅ Database is running"
    echo ""
elif [ "$DB_STATUS" == "available" ]; then
    echo "✅ Database is already running"
    echo ""
else
    echo "⚠️  Database status: $DB_STATUS"
    echo ""
fi

echo "📊 Scaling up services..."

# Scale backend to 1
echo "  → Backend API: 1 task"
aws ecs update-service \
    --cluster $CLUSTER \
    --service cerebro-backend \
    --desired-count 1 \
    --region $REGION \
    --query 'service.serviceName' \
    --output text > /dev/null

# Scale frontend to 1
echo "  → Frontend: 1 task"
aws ecs update-service \
    --cluster $CLUSTER \
    --service cerebro-frontend \
    --desired-count 1 \
    --region $REGION \
    --query 'service.serviceName' \
    --output text > /dev/null

# Scale celery worker to 1
echo "  → Celery Worker: 1 task"
aws ecs update-service \
    --cluster $CLUSTER \
    --service cerebro-celery-worker \
    --desired-count 1 \
    --region $REGION \
    --query 'service.serviceName' \
    --output text > /dev/null

echo ""
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "✅ Services resumed!"
echo ""
echo "🌐 Your application is available at:"
echo "   https://dbu9oghut69dh.cloudfront.net"
echo ""
echo "📋 Check service status:"
echo "   aws ecs describe-services --cluster $CLUSTER --services cerebro-backend cerebro-frontend cerebro-celery-worker --region $REGION"
echo ""
echo "📊 View logs:"
echo "   aws logs tail /ecs/cerebro-backend --follow --region $REGION"
