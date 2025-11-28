#!/bin/bash

# Restaurant POS - One Command Docker Setup
# Uses local MySQL server on host machine

echo "==========================================="
echo "Restaurant POS - Docker Setup"
echo "==========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose V2 is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker is installed"
echo "✓ Docker Compose is available"
echo ""

# Check if local MySQL is running
echo "Checking local MySQL connection..."
if mysql -h localhost -u root -proot -e "SELECT 1;" &> /dev/null; then
    echo "✓ Local MySQL is accessible"
else
    echo "❌ Cannot connect to local MySQL"
    echo "   Please ensure MySQL is running on localhost:3306"
    echo "   Username: root, Password: root"
    exit 1
fi

# Check if database exists
echo "Checking database..."
if mysql -h localhost -u root -proot -e "USE restaurant_pos;" &> /dev/null; then
    echo "✓ Database 'restaurant_pos' exists"
else
    echo "⚠️  Database 'restaurant_pos' not found"
    echo "   Please run: python init_db.py first"
    exit 1
fi

echo ""
# Check if user can run docker without sudo
if ! docker ps &> /dev/null; then
    echo "⚠️  Docker requires sudo. You may need to add your user to the docker group:"
    echo "   sudo usermod -aG docker $USER"
    echo "   Then log out and back in."
    echo ""
    echo "Using sudo for Docker commands..."
    DOCKER_CMD="sudo docker"
    COMPOSE_CMD="sudo docker compose"
else
    DOCKER_CMD="docker"
    COMPOSE_CMD="docker compose"
fi

# Stop any existing containers
echo "Stopping existing containers (if any)..."
$COMPOSE_CMD down 2>/dev/null

echo ""
echo "Building Docker image..."
$COMPOSE_CMD build

if [ $? -eq 0 ]; then
    echo "✓ Docker image built successfully"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi

echo ""
echo "Starting application..."
$COMPOSE_CMD up -d

# Wait for service to be ready
echo "Waiting for application to start..."
sleep 10

# Check if service is running
if $COMPOSE_CMD ps | grep -q "Up"; then
    echo ""
    echo "==========================================="
    echo "✅ Restaurant POS is now running!"
    echo "==========================================="
    echo ""
    echo "Access Points:"
    echo "  API Server:       http://localhost:8000"
    echo "  API Docs:         http://localhost:8000/docs"
    echo "  ReDoc:            http://localhost:8000/redoc"
    echo "  Health Check:     http://localhost:8000/health"
    echo ""
    echo "Database:"
    echo "  Host: localhost (from host) / host.docker.internal (from container)"
    echo "  Port: 3306"
    echo "  Database: restaurant_pos"
    echo "  Username: root"
    echo "  Password: root"
    echo ""
    echo "Admin Credentials:"
    echo "  Email: admin@restaurant.com"
    echo "  Password: Admin123!"
    echo ""
    echo "Useful Commands:"
    echo "  View logs:        docker compose logs -f"
    echo "  Stop app:         docker compose stop"
    echo "  Start app:        docker compose start"
    echo "  Restart app:      docker compose restart"
    echo "  Stop & remove:    docker compose down"
    echo "  View status:      docker compose ps"
    echo "==========================================="
    echo ""
    
    # Test the API
    echo "Testing API connection..."
    sleep 3
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is responding"
        echo ""
        echo "Setup complete! Your application is ready to use."
    else
        echo "⚠️  API is still starting... Check logs with: docker compose logs -f"
    fi
else
    echo ""
    echo "❌ Failed to start application"
    echo "   Check logs with: docker compose logs"
    exit 1
fi
