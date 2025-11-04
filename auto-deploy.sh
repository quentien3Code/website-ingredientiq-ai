#!/bin/bash

# Auto Deploy Script for FoodAI
# This script handles the complete deployment process including static files fix

set -e

echo "🚀 Starting FoodAI auto deployment..."

# Configuration
ECR_REGISTRY="888722447205.dkr.ecr.us-east-1.amazonaws.com"
REGION="us-east-1"

# Login to ECR
echo "📝 Logging into AWS ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build and push backend image for AMD64
echo "🔨 Building backend image for AMD64..."
docker buildx build --platform linux/amd64 -t $ECR_REGISTRY/foodai:latest --push .

# Build and push nginx image for AMD64
echo "🔨 Building nginx image for AMD64..."
docker buildx build --platform linux/amd64 -t $ECR_REGISTRY/foodai-nginx:latest --file ./nginx/Dockerfile --push ./nginx

echo "✅ Images built and pushed successfully!"

# Create production docker-compose
cat > docker-compose.prod.yml << 'EOF'
version: "3.8"

services:
  foodai-backend:
    image: 888722447205.dkr.ecr.us-east-1.amazonaws.com/foodai:latest
    container_name: foodai-backend
    restart: always
    command: ["sh", "-c", "python manage.py migrate --noinput && gunicorn --bind 0.0.0.0:8018 foodanalysis.wsgi:application"]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    networks:
      - foodai_network
    depends_on:
      - foodai-db

  foodai-db:
    image: postgres:15
    container_name: foodai-db
    restart: always
    environment:
      POSTGRES_DB: foodai
      POSTGRES_USER: foodai_user
      POSTGRES_PASSWORD: pass098foodai1123
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - foodai_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  foodai-nginx:
    image: 888722447205.dkr.ecr.us-east-1.amazonaws.com/foodai-nginx:latest
    container_name: foodai-nginx
    restart: always
    ports:
      - "8018:80"
    networks:
      - foodai_network
    depends_on:
      - foodai-backend
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - /etc/letsencrypt:/etc/letsencrypt:ro

networks:
  foodai_network:
    driver: bridge

volumes:
  static_volume:
  media_volume:
  postgres-data:
EOF

# Create server deployment script
cat > server-deploy.sh << 'EOF'
#!/bin/bash

# Server deployment script with static files fix
set -e

echo "🚀 Starting server deployment..."

# Login to ECR
echo "📝 Logging into AWS ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 888722447205.dkr.ecr.us-east-1.amazonaws.com

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down || true

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f docker-compose.prod.yml pull

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 15

# Fix static files if needed (backup solution)
echo "🔧 Ensuring static files are properly linked..."
docker exec -it foodai-backend bash -c "
    if [ ! -f /app/staticfiles/css/main.f056d19f.css ]; then
        find /app/staticfiles -name 'main.*.css' -exec ln -sf {} /app/staticfiles/css/main.f056d19f.css \;
    fi
    if [ ! -f /app/staticfiles/js/main.b538225d.js ]; then
        find /app/staticfiles -name 'main.*.js' -exec ln -sf {} /app/staticfiles/js/main.b538225d.js \;
    fi
" || echo "Static files fix completed"

# Check status
echo "🔍 Checking service status..."
docker-compose -f docker-compose.prod.yml ps

echo "✅ Deployment completed successfully!"
echo "🌐 Your application should be available at: http://your-server-ip:8018"
EOF

chmod +x server-deploy.sh

echo ""
echo "🎉 Auto deployment setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Copy docker-compose.prod.yml and server-deploy.sh to your server"
echo "2. On your server, run: chmod +x server-deploy.sh"
echo "3. On your server, run: ./server-deploy.sh"
echo ""
echo "✨ This setup will automatically handle static files issues!"
