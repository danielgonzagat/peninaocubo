#!/bin/bash
# PENIN-Ω Deployment Script
# Deploys the complete PENIN-Ω system with secure metrics exposure

set -e

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
DOMAIN="metrics.penin.local"
SSL_DIR="nginx/ssl"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if OpenSSL is installed
    if ! command -v openssl &> /dev/null; then
        log_error "OpenSSL is not installed. Please install OpenSSL first."
        exit 1
    fi
    
    log_success "All prerequisites are met"
}

# Create environment file
create_env_file() {
    log_info "Creating environment file..."
    
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << EOF
# PENIN-Ω Environment Configuration
PENIN_METRICS_TOKEN=$(openssl rand -hex 32)
PENIN_CACHE_HMAC_KEY=$(openssl rand -hex 32)
REDIS_PASSWORD=$(openssl rand -hex 16)
GRAFANA_PASSWORD=$(openssl rand -hex 16)

# Domain configuration
DOMAIN=$DOMAIN
EOF
        log_success "Environment file created: $ENV_FILE"
    else
        log_info "Environment file already exists: $ENV_FILE"
    fi
}

# Setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    if [ ! -d "$SSL_DIR" ]; then
        mkdir -p "$SSL_DIR"
    fi
    
    if [ ! -f "$SSL_DIR/penin-metrics.crt" ]; then
        log_info "Generating SSL certificates..."
        ./nginx/ssl-setup.sh
        log_success "SSL certificates generated"
    else
        log_info "SSL certificates already exist"
    fi
}

# Create authentication file
create_auth() {
    log_info "Creating authentication file..."
    
    AUTH_FILE="nginx/.htpasswd"
    if [ ! -f "$AUTH_FILE" ]; then
        # Create default user (password: penin123)
        echo "penin:\$2y\$10\$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi" > "$AUTH_FILE"
        log_success "Authentication file created: $AUTH_FILE"
        log_warning "Default credentials: penin/penin123"
        log_warning "Please change the password in production!"
    else
        log_info "Authentication file already exists: $AUTH_FILE"
    fi
}

# Create Grafana configuration
create_grafana_config() {
    log_info "Creating Grafana configuration..."
    
    # Create datasources directory
    mkdir -p grafana/datasources
    
    # Create Prometheus datasource
    cat > grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
    
    # Create dashboards directory
    mkdir -p grafana/dashboards
    
    # Create dashboard configuration
    cat > grafana/dashboards/dashboard.yml << EOF
apiVersion: 1

providers:
  - name: 'PENIN-Ω Dashboards'
    orgId: 1
    folder: 'PENIN-Ω'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
    
    log_success "Grafana configuration created"
}

# Deploy services
deploy_services() {
    log_info "Deploying PENIN-Ω services..."
    
    # Build and start services
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    
    log_success "Services deployed successfully"
}

# Wait for services to be ready
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for PENIN-Ω core
    log_info "Waiting for PENIN-Ω core..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "PENIN-Ω core is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "PENIN-Ω core failed to start"
        return 1
    fi
    
    # Wait for Prometheus
    log_info "Waiting for Prometheus..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:9090/-/healthy &> /dev/null; then
            log_success "Prometheus is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "Prometheus failed to start"
        return 1
    fi
    
    # Wait for Grafana
    log_info "Waiting for Grafana..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:3000/api/health &> /dev/null; then
            log_success "Grafana is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "Grafana failed to start"
        return 1
    fi
}

# Display deployment information
show_deployment_info() {
    log_success "PENIN-Ω deployment completed successfully!"
    echo ""
    echo "🌐 Service URLs:"
    echo "  PENIN-Ω Core:     http://localhost:8000"
    echo "  Metrics (HTTP):   http://localhost/metrics"
    echo "  Metrics (HTTPS):  https://$DOMAIN/metrics"
    echo "  Prometheus:       http://localhost:9090"
    echo "  Grafana:          http://localhost:3000"
    echo ""
    echo "🔐 Authentication:"
    echo "  Username: penin"
    echo "  Password: penin123"
    echo ""
    echo "📊 Grafana Login:"
    echo "  Username: admin"
    echo "  Password: $(grep GRAFANA_PASSWORD $ENV_FILE | cut -d'=' -f2)"
    echo ""
    echo "🔧 Management Commands:"
    echo "  View logs:        docker-compose logs -f"
    echo "  Stop services:    docker-compose down"
    echo "  Restart:          docker-compose restart"
    echo "  Update:           docker-compose pull && docker-compose up -d"
    echo ""
    echo "⚠️  Important Notes:"
    echo "  1. Add '$DOMAIN' to your /etc/hosts file:"
    echo "     127.0.0.1 $DOMAIN"
    echo ""
    echo "  2. Change default passwords in production!"
    echo ""
    echo "  3. SSL certificates are self-signed for development."
    echo "     Use trusted certificates in production."
    echo ""
    echo "  4. Check logs if services fail to start:"
    echo "     docker-compose logs [service-name]"
}

# Main deployment function
main() {
    echo "🚀 PENIN-Ω Deployment Script"
    echo "=============================="
    echo ""
    
    check_prerequisites
    create_env_file
    setup_ssl
    create_auth
    create_grafana_config
    deploy_services
    wait_for_services
    show_deployment_info
}

# Handle script arguments
case "${1:-}" in
    "stop")
        log_info "Stopping PENIN-Ω services..."
        docker-compose -f "$COMPOSE_FILE" down
        log_success "Services stopped"
        ;;
    "restart")
        log_info "Restarting PENIN-Ω services..."
        docker-compose -f "$COMPOSE_FILE" restart
        log_success "Services restarted"
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" logs -f "${2:-}"
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    "update")
        log_info "Updating PENIN-Ω services..."
        docker-compose -f "$COMPOSE_FILE" pull
        docker-compose -f "$COMPOSE_FILE" up -d
        log_success "Services updated"
        ;;
    *)
        main
        ;;
esac