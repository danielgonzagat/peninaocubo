#!/bin/bash
# SSL Certificate Setup Script for PENIN-Ω Metrics
# Generates self-signed certificates for development/testing
# For production, use certificates from a trusted CA

set -e

SSL_DIR="/etc/nginx/ssl"
DOMAIN="metrics.penin.local"
COUNTRY="US"
STATE="California"
CITY="San Francisco"
ORG="PENIN-Ω"
EMAIL="admin@penin.local"

echo "🔐 Setting up SSL certificates for PENIN-Ω metrics..."

# Create SSL directory
sudo mkdir -p $SSL_DIR
cd $SSL_DIR

# Generate private key
echo "📝 Generating private key..."
sudo openssl genrsa -out penin-metrics.key 4096

# Generate certificate signing request
echo "📝 Generating certificate signing request..."
sudo openssl req -new -key penin-metrics.key -out penin-metrics.csr -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=IT/CN=$DOMAIN/emailAddress=$EMAIL"

# Generate self-signed certificate
echo "📝 Generating self-signed certificate..."
sudo openssl x509 -req -days 365 -in penin-metrics.csr -signkey penin-metrics.key -out penin-metrics.crt

# Set proper permissions
sudo chmod 600 penin-metrics.key
sudo chmod 644 penin-metrics.crt
sudo chmod 644 penin-metrics.csr

# Create certificate bundle
echo "📝 Creating certificate bundle..."
sudo cat penin-metrics.crt penin-metrics.key > penin-metrics.pem
sudo chmod 600 penin-metrics.pem

# Generate DH parameters for perfect forward secrecy
echo "📝 Generating DH parameters (this may take a while)..."
sudo openssl dhparam -out dhparam.pem 2048

echo "✅ SSL certificates generated successfully!"
echo ""
echo "📋 Certificate details:"
echo "  Domain: $DOMAIN"
echo "  Valid for: 365 days"
echo "  Key size: 4096 bits"
echo "  DH parameters: 2048 bits"
echo ""
echo "📁 Files created:"
echo "  $SSL_DIR/penin-metrics.key (private key)"
echo "  $SSL_DIR/penin-metrics.crt (certificate)"
echo "  $SSL_DIR/penin-metrics.csr (signing request)"
echo "  $SSL_DIR/penin-metrics.pem (bundle)"
echo "  $SSL_DIR/dhparam.pem (DH parameters)"
echo ""
echo "⚠️  Note: These are self-signed certificates for development/testing."
echo "   For production, use certificates from a trusted CA."
echo ""
echo "🔧 Next steps:"
echo "1. Add '$DOMAIN' to your /etc/hosts file:"
echo "   127.0.0.1 $DOMAIN"
echo ""
echo "2. Create authentication file:"
echo "   sudo htpasswd -c /etc/nginx/.htpasswd penin-user"
echo ""
echo "3. Test the configuration:"
echo "   sudo nginx -t"
echo ""
echo "4. Reload nginx:"
echo "   sudo systemctl reload nginx"