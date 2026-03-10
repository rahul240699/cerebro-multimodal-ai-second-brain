#!/bin/bash

# Pause AWS ECS Deployment + Stop RDS (Maximum Cost Savings)
# RDS will auto-start after 7 days

set -e

REGION="us-east-1"
CLUSTER="cerebro-cluster"

echo "🛑 Pausing Cerebro deployment (including RDS) to maximize savings..."
echo ""
echo "⚠️  WARNING: RDS will automatically start after 7 days"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

echo ""
echo "📊 Scaling down ECS services..."

# Scale all services to 0
aws ecs update-service --cluster $CLUSTER --service cerebro-backend --desired-count 0 --region $REGION --output text > /dev/null
aws ecs update-service --cluster $CLUSTER --service cerebro-frontend --desired-count 0 --region $REGION --output text > /dev/null
aws ecs update-service --cluster $CLUSTER --service cerebro-celery-worker --desired-count 0 --region $REGION --output text > /dev/null

echo "✅ ECS services scaled to 0"

echo ""
echo "📊 Stopping RDS database..."
aws rds stop-db-instance --db-instance-identifier cerebro-db --region $REGION

echo "✅ RDS stop initiated (takes 1-2 minutes)"

echo ""
echo "💰 Cost while paused:"
echo "  • ECS services: \$0 (stopped)"
echo "  • RDS: \$0 (stopped, auto-starts in 7 days)"
echo "  • ElastiCache: ~\$13/month"
echo "  • ALB: ~\$16/month"
echo "  • NAT Gateway: ~\$32/month"
echo ""
echo "Total: ~\$61/month (vs ~\$105/month when running)"
echo "Savings: ~\$44/month (42% reduction)"
echo ""
echo "⚠️  Remember: RDS auto-starts after 7 days"
echo ""
echo "🔄 To resume, run: ./resume-aws.sh"
