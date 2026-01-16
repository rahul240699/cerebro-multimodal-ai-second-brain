# 🧠 Cerebro AWS ECS Deployment - Complete

## 🎉 Your Application is Live!

**URL:** https://dbu9oghut69dh.cloudfront.net

All services are running successfully on AWS ECS with:
- ✅ Free SSL/HTTPS via CloudFront
- ✅ PostgreSQL database with pgvector support
- ✅ Redis for Celery task queue
- ✅ Backend API (FastAPI)
- ✅ Frontend (Next.js)
- ✅ Celery worker with 2GB memory (upgraded from 512MB on Render)

---

## 📋 Deployment Details

### Infrastructure
- **AWS Region:** us-east-1 (US East - N. Virginia)
- **CloudFormation Stack:** cerebro-stack
- **ECS Cluster:** cerebro-cluster
- **CloudFront Distribution:** E1SK024906FH8L

### Services
1. **Backend API**
   - Task Definition: cerebro-backend:3
   - CPU: 512, Memory: 1GB
   - Auto-scaling: 1-3 tasks
   - Health Check: https://dbu9oghut69dh.cloudfront.net/api/health

2. **Frontend**
   - Task Definition: cerebro-frontend:2
   - CPU: 256, Memory: 512MB
   - Auto-scaling: 1-3 tasks

3. **Celery Worker**
   - Task Definition: cerebro-celery-worker:3
   - CPU: 1024, Memory: 2GB
   - Tasks: 4 registered (audio, document, image, web)
   - Connected to ElastiCache Redis

### Database
- **RDS PostgreSQL:** 16.3
- **Instance:** db.t3.micro
- **Storage:** 20GB gp3
- **Database:** cerebro (auto-created on startup)
- **Extensions:** pgvector (for semantic search)

### Cache/Queue
- **ElastiCache Redis:** 7.x
- **Instance:** cache.t3.micro
- **Purpose:** Celery broker and result backend

---

## 🚀 Features Enabled

### ✅ Document Processing
- Upload PDFs, Word docs, text files
- Automatic chunking and embedding generation
- Vector similarity search
- Multi-modal content extraction

### ✅ Audio Recording
- **HTTPS Required:** ✅ (CloudFront provides SSL)
- Record voice messages via browser
- Whisper transcription
- Embedding generation
- Semantic search across transcripts

### ✅ Image Analysis
- Upload images
- GPT-4 Vision analysis
- Text extraction and indexing

### ✅ Web Scraping
- URL-based content extraction
- Automatic chunking
- Vector embeddings

---

## 🛠️ Management Commands

### View Logs
```bash
# Backend API logs
aws logs tail /ecs/cerebro-backend --follow --region us-east-1

# Celery worker logs
aws logs tail /ecs/cerebro-celery --follow --region us-east-1

# Frontend logs
aws logs tail /ecs/cerebro-frontend --follow --region us-east-1
```

### Force Service Restart
```bash
# Restart backend
aws ecs update-service --cluster cerebro-cluster --service cerebro-backend --force-new-deployment --region us-east-1

# Restart celery worker
aws ecs update-service --cluster cerebro-cluster --service cerebro-celery-worker --force-new-deployment --region us-east-1

# Restart frontend
aws ecs update-service --cluster cerebro-cluster --service cerebro-frontend --force-new-deployment --region us-east-1
```

### Update Environment Variables
```bash
# Example: Update OPENAI_API_KEY
./fix-cors.sh  # Modify this script to update any environment variable
```

### Invalidate CloudFront Cache
```bash
aws cloudfront create-invalidation --distribution-id E1SK024906FH8L --paths "/*" --region us-east-1
```

---

## 🔧 Deployment Scripts

### Main Deployment
- **deploy-aws.sh** - Full infrastructure deployment
  - Creates ECR repositories
  - Builds Docker images for linux/amd64
  - Generates CloudFormation template
  - Deploys entire stack
  - Returns CloudFront HTTPS URL

### SSL/HTTPS Setup
- **setup-cloudfront-ssl.sh** - Creates CloudFront distribution with free SSL

### Updates
- **update-to-cloudfront.sh** - Rebuild frontend with CloudFront URL
- **fix-cors.sh** - Update CORS policy in backend
- **fix-database.sh** - Initialize database if needed

### Cleanup
- **cleanup-aws.sh** - Delete all AWS resources

---

## 📊 Cost Estimate

### Current Configuration (Free Tier / Low Traffic)
- **ECS Fargate:** ~$20-30/month (3 services always running)
- **RDS PostgreSQL:** ~$13/month (db.t3.micro)
- **ElastiCache Redis:** ~$13/month (cache.t3.micro)
- **CloudFront:** First 1TB free, then $0.085/GB
- **ALB:** ~$16/month
- **NAT Gateway:** ~$32/month
- **Data Transfer:** Varies by usage

**Total Estimated:** ~$95-105/month

### Cost Optimization Tips
1. Use AWS Free Tier for first 12 months
2. Consider stopping non-production environments
3. Use Spot instances for dev/test (not recommended for prod)
4. Monitor CloudWatch logs retention (set to 7 days)
5. Set up AWS Budgets alerts

---

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check RDS endpoint
aws cloudformation describe-stacks --stack-name cerebro-stack --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' --output text

# Check backend logs for connection errors
aws logs tail /ecs/cerebro-backend --since 5m --region us-east-1
```

### Celery Tasks Not Processing
```bash
# Check celery worker logs
aws logs tail /ecs/cerebro-celery --since 5m --region us-east-1

# Verify Redis connection
aws elasticache describe-cache-clusters --show-cache-node-info --region us-east-1
```

### Frontend 404 Errors
```bash
# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id E1SK024906FH8L --paths "/*" --region us-east-1

# Check frontend logs
aws logs tail /ecs/cerebro-frontend --since 5m --region us-east-1
```

### CORS Errors
```bash
# Update CORS policy to allow all origins
./fix-cors.sh
```

---

## 🔐 Security Notes

### Current Configuration
- ✅ VPC with private subnets for RDS/Redis
- ✅ Security groups restricting access
- ✅ SSL/HTTPS via CloudFront
- ⚠️ CORS set to "*" (allow all origins)
- ⚠️ Database password in CloudFormation (default: CerebroPass123!)

### Production Recommendations
1. **Change database password** - Use AWS Secrets Manager
2. **Restrict CORS** - Set specific frontend domain
3. **Enable RDS encryption** - Add at-rest encryption
4. **Add WAF** - CloudFront Web Application Firewall
5. **Enable CloudTrail** - Audit AWS API calls
6. **Set up GuardDuty** - Threat detection
7. **Use IAM roles** - Instead of hardcoded credentials

---

## 📈 Monitoring

### CloudWatch Metrics
- CPU/Memory utilization per service
- Request count and latency
- Error rates
- Database connections

### Recommended Alarms
```bash
# High CPU (>80%)
# High Memory (>90%)
# Error rate (>1%)
# Database connection failures
```

### Access CloudWatch Dashboard
```bash
aws cloudwatch get-dashboard --dashboard-name cerebro-dashboard --region us-east-1
```

---

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to AWS ECS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and push Docker images
        run: |
          ./deploy-aws.sh
```

---

## 🎯 Next Steps

### Immediate
1. ✅ Test document upload at https://dbu9oghut69dh.cloudfront.net
2. ✅ Test audio recording (requires HTTPS)
3. ✅ Verify semantic search works
4. ⚠️ Change default database password
5. ⚠️ Add custom domain (optional)

### Optional Enhancements
- [ ] Set up custom domain with Route 53
- [ ] Add WAF rules for security
- [ ] Enable RDS automated backups
- [ ] Set up CloudWatch alarms
- [ ] Add Redis persistence
- [ ] Enable ECS Exec for debugging
- [ ] Set up multi-region deployment

---

## 📞 Support Resources

### AWS Services Used
- [ECS Fargate Documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [RDS PostgreSQL Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/)
- [ElastiCache Redis Documentation](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/)

### Useful AWS CLI Commands
```bash
# List all ECS services
aws ecs list-services --cluster cerebro-cluster --region us-east-1

# Describe stack resources
aws cloudformation describe-stack-resources --stack-name cerebro-stack --region us-east-1

# List CloudFront distributions
aws cloudfront list-distributions --region us-east-1
```

---

## ✅ Deployment Checklist

- [x] Created ECR repositories
- [x] Built Docker images for linux/amd64 platform
- [x] Pushed images to ECR
- [x] Created CloudFormation stack
- [x] Deployed VPC and networking
- [x] Deployed RDS PostgreSQL with pgvector
- [x] Deployed ElastiCache Redis
- [x] Deployed ECS cluster and services
- [x] Created Application Load Balancer
- [x] Set up CloudFront with free SSL
- [x] Configured CORS policy
- [x] Fixed API routing
- [x] Auto-created database on startup
- [x] Fixed Celery SSL configuration
- [x] Verified all services running
- [x] Tested API health endpoint

**🎉 ALL SYSTEMS OPERATIONAL 🎉**

---

*Generated: 2025-01-16*
*Deployed by: deploy-aws.sh*
*Region: us-east-1*
