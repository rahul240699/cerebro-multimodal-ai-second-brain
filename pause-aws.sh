#!/bin/bash

# Pause AWS ECS Deployment (Scale to 0 to save costs)
# This keeps all infrastructure but stops running tasks

set -e

REGION="us-east-1"
CLUSTER="cerebro-cluster"

echo "🛑 Pausing Cerebro deployment to save costs..."
echo ""
echo "This will:"
echo "  - Scale all ECS services to 0 tasks"
echo "  - Keep RDS database (you can stop it manually for 7 days)"
echo "  - Keep ElastiCache Redis running (minimal cost)"
echo "  - Keep CloudFront, ALB, and VPC (no additional cost when idle)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

echo ""
echo "📊 Scaling down services..."

# Scale backend to 0
echo "  → Backend API: 0 tasks"
aws ecs update-service \
    --cluster $CLUSTER \
    --service cerebro-backend \
    --desired-count 0 \
    --region $REGION \
    --query 'service.serviceName' \
    --output text > /dev/null

# Scale frontend to 0
echo "  → Frontend: 0 tasks"
aws ecs update-service \
    --cluster $CLUSTER \
    --service cerebro-frontend \
    --desired-count 0 \
    --region $REGION \
    --query 'service.serviceName' \
    --output text > /dev/null

# Scale celery worker to 0
echo "  → Celery Worker: 0 tasks"
aws ecs update-service \
    --cluster $CLUSTER \
    --service cerebro-celery-worker \
    --desired-count 0 \
    --region $REGION \
    --query 'service.serviceName' \
    --output text > /dev/null

echo ""
echo "✅ All ECS services scaled to 0"

echo ""
echo "💰 Additional cost savings (optional):"
echo ""
echo "1. Stop RDS database (saves ~\$13/month, auto-starts after 7 days):"
echo "   aws rds stop-db-instance --db-instance-identifier cerebro-db --region $REGION"
echo ""
echo "2. Delete NAT Gateway (saves ~\$32/month, need to recreate on resume):"
echo "   - This is complex, only do if pausing for >1 month"
echo ""
echo "Current state:"
echo "  • ECS services: STOPPED (saves ~\$20-30/month)"
echo "  • RDS: RUNNING (~\$13/month)"
echo "  • ElastiCache: RUNNING (~\$13/month)"
echo "  • ALB: RUNNING (~\$16/month) - needed for CloudFront"
echo "  • NAT Gateway: RUNNING (~\$32/month)"
echo ""
echo "Total cost while paused: ~\$74/month"
echo "To save more, stop RDS: ~\$61/month"
echo ""
echo "🔄 To resume, run: ./resume-aws.sh"
