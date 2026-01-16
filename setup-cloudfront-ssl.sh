#!/bin/bash

###############################################################################
# Setup CloudFront with Free SSL for Cerebro
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_NAME="cerebro"
AWS_REGION="us-east-1"

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Setting Up CloudFront with SSL          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"

# Get ALB DNS name
ALB_DNS=$(aws cloudformation describe-stacks \
    --stack-name cerebro-stack \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
    --output text | sed 's|http://||')

echo -e "\n${YELLOW}ALB DNS: ${ALB_DNS}${NC}"

# Create CloudFront distribution
echo -e "\n${YELLOW}Creating CloudFront distributions (this takes 10-15 minutes)...${NC}"

# Create distribution config
cat > cloudfront-config.json <<EOF
{
  "CallerReference": "${PROJECT_NAME}-$(date +%s)",
  "Comment": "Cerebro Frontend Distribution with Free SSL",
  "Enabled": true,
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "${PROJECT_NAME}-alb",
        "DomainName": "${ALB_DNS}",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "http-only",
          "OriginSslProtocols": {
            "Quantity": 1,
            "Items": ["TLSv1.2"]
          }
        },
        "ConnectionAttempts": 3,
        "ConnectionTimeout": 10
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "${PROJECT_NAME}-alb",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 7,
      "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "Compress": true,
    "ForwardedValues": {
      "QueryString": true,
      "Cookies": {
        "Forward": "all"
      },
      "Headers": {
        "Quantity": 3,
        "Items": ["Host", "Origin", "Authorization"]
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 0,
    "MaxTTL": 0,
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    }
  },
  "CacheBehaviors": {
    "Quantity": 1,
    "Items": [
      {
        "PathPattern": "/api/*",
        "TargetOriginId": "${PROJECT_NAME}-alb",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
          "Quantity": 7,
          "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
          "CachedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"]
          }
        },
        "Compress": false,
        "ForwardedValues": {
          "QueryString": true,
          "Cookies": {
            "Forward": "all"
          },
          "Headers": {
            "Quantity": 4,
            "Items": ["Host", "Origin", "Authorization", "Content-Type"]
          }
        },
        "MinTTL": 0,
        "DefaultTTL": 0,
        "MaxTTL": 0,
        "TrustedSigners": {
          "Enabled": false,
          "Quantity": 0
        }
      }
    ]
  },
  "PriceClass": "PriceClass_100",
  "ViewerCertificate": {
    "CloudFrontDefaultCertificate": true,
    "MinimumProtocolVersion": "TLSv1.2_2019"
  }
}
EOF

echo -e "${YELLOW}Creating CloudFront distribution...${NC}"
DISTRIBUTION_OUTPUT=$(aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json \
    --region us-east-1)

DISTRIBUTION_ID=$(echo "$DISTRIBUTION_OUTPUT" | grep -o '"Id": "[^"]*"' | head -1 | cut -d'"' -f4)
CLOUDFRONT_DOMAIN=$(echo "$DISTRIBUTION_OUTPUT" | grep -o '"DomainName": "[^"]*"' | head -1 | cut -d'"' -f4)

rm cloudfront-config.json

echo -e "${GREEN}✓ CloudFront distribution created${NC}"
echo -e "${YELLOW}Distribution ID: ${DISTRIBUTION_ID}${NC}"
echo -e "${YELLOW}CloudFront Domain: ${CLOUDFRONT_DOMAIN}${NC}"

# Wait for distribution to deploy
echo -e "\n${YELLOW}Waiting for CloudFront distribution to deploy (10-15 minutes)...${NC}"
echo -e "${YELLOW}You can continue with other tasks. Check status with:${NC}"
echo -e "  aws cloudfront get-distribution --id ${DISTRIBUTION_ID} --query 'Distribution.Status' --output text"

# Update backend CORS to allow CloudFront domain
echo -e "\n${YELLOW}Updating backend CORS settings...${NC}"
aws ecs update-service \
    --cluster cerebro-cluster \
    --service cerebro-backend \
    --force-new-deployment \
    --region us-east-1 > /dev/null

echo -e "\n${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     CloudFront Setup Complete! 🎉         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo -e "\n${YELLOW}Your HTTPS URLs:${NC}"
echo -e "${GREEN}Frontend: https://${CLOUDFRONT_DOMAIN}${NC}"
echo -e "${GREEN}Backend API: https://${CLOUDFRONT_DOMAIN}/api${NC}"
echo ""
echo -e "${YELLOW}Status Check:${NC}"
echo -e "  aws cloudfront get-distribution --id ${DISTRIBUTION_ID} --query 'Distribution.Status'"
echo ""
echo -e "${YELLOW}The distribution is deploying. Wait 10-15 minutes, then:${NC}"
echo -e "  1. Visit https://${CLOUDFRONT_DOMAIN}"
echo -e "  2. Try uploading documents and audio"
echo -e "  3. Audio recording will now work with HTTPS!"
echo ""
echo -e "${YELLOW}To save these details:${NC}"
echo "CLOUDFRONT_URL=https://${CLOUDFRONT_DOMAIN}" > cloudfront-urls.txt
echo "DISTRIBUTION_ID=${DISTRIBUTION_ID}" >> cloudfront-urls.txt
echo -e "${GREEN}✓ Saved to cloudfront-urls.txt${NC}"
echo ""
