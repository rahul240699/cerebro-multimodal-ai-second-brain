#!/bin/bash

# Cerebro EC2 Deployment Script
# This script sets up Cerebro on a fresh Ubuntu EC2 instance

set -e

echo "🚀 Starting Cerebro deployment on EC2..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
echo "📦 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add current user to docker group
sudo usermod -aG docker $USER

# Install Git
echo "📚 Installing Git..."
sudo apt-get install -y git

# Clone repository (update with your repo)
echo "📥 Cloning Cerebro repository..."
cd /home/ubuntu
if [ ! -d "cerebro" ]; then
    git clone https://github.com/rahul240699/cerebro-multimodal-ai-second-brain.git cerebro
fi
cd cerebro

# Create .env file
echo "🔐 Creating environment configuration..."
cat > backend/.env << 'EOF'
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/cerebro

# Redis Configuration  
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Model Configuration
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# API Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://your-ec2-public-ip:3000
EOF

echo ""
echo "⚠️  IMPORTANT: Edit backend/.env and add your OpenAI API key!"
echo "   sudo nano /home/ubuntu/cerebro/backend/.env"
echo ""
read -p "Press Enter after you've updated the .env file with your API key..."

# Update frontend API URL to use EC2 public IP
echo "🌐 Configuring frontend API URL..."
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "NEXT_PUBLIC_API_URL=http://$PUBLIC_IP:8000" > frontend/.env.local

# Update allowed origins in backend .env
sed -i "s/your-ec2-public-ip/$PUBLIC_IP/g" backend/.env

# Start services
echo "🚢 Starting Docker containers..."
sudo docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check if services are running
echo "✅ Checking service status..."
sudo docker-compose ps

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📡 Access your application at:"
echo "   Frontend: http://$PUBLIC_IP:3000"
echo "   Backend API: http://$PUBLIC_IP:8000"
echo "   API Docs: http://$PUBLIC_IP:8000/docs"
echo ""
echo "📋 Useful commands:"
echo "   View logs: cd /home/ubuntu/cerebro && sudo docker-compose logs -f"
echo "   Restart: cd /home/ubuntu/cerebro && sudo docker-compose restart"
echo "   Stop: cd /home/ubuntu/cerebro && sudo docker-compose down"
echo "   Update: cd /home/ubuntu/cerebro && git pull && sudo docker-compose up -d --build"
echo ""
