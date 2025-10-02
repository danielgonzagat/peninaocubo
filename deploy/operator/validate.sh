#!/bin/bash
# PENIN-Ω Operator Validation Script
# This script validates that the operator is properly installed and working

set -e

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   PENIN-Ω Kubernetes Operator Validation                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Function to check command existence
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1 not found${NC}"
        echo "  Please install $1 to continue"
        exit 1
    else
        echo -e "${GREEN}✓ $1 is installed${NC}"
    fi
}

# Function to check Kubernetes resource
check_resource() {
    local resource=$1
    local name=$2
    local namespace=${3:-""}
    
    if [ -n "$namespace" ]; then
        if kubectl get $resource $name -n $namespace &> /dev/null; then
            echo -e "${GREEN}✓ $resource/$name exists in namespace $namespace${NC}"
            return 0
        else
            echo -e "${RED}✗ $resource/$name not found in namespace $namespace${NC}"
            return 1
        fi
    else
        if kubectl get $resource $name &> /dev/null; then
            echo -e "${GREEN}✓ $resource/$name exists${NC}"
            return 0
        else
            echo -e "${RED}✗ $resource/$name not found${NC}"
            return 1
        fi
    fi
}

echo "Phase 1: Prerequisites"
echo "─────────────────────────────────────────────────"
check_command "kubectl"
check_command "make"

echo ""
echo "Phase 2: Kubernetes Cluster Access"
echo "─────────────────────────────────────────────────"

if kubectl cluster-info &> /dev/null; then
    echo -e "${GREEN}✓ Kubernetes cluster is accessible${NC}"
    echo "  Cluster: $(kubectl config current-context)"
else
    echo -e "${RED}✗ Cannot access Kubernetes cluster${NC}"
    echo "  Please check your kubeconfig"
    exit 1
fi

echo ""
echo "Phase 3: CRD Installation"
echo "─────────────────────────────────────────────────"

if check_resource "crd" "peninaomegaclusters.penin.ai"; then
    echo "  API Version: $(kubectl get crd peninaomegaclusters.penin.ai -o jsonpath='{.spec.versions[0].name}')"
    echo "  Scope: $(kubectl get crd peninaomegaclusters.penin.ai -o jsonpath='{.spec.scope}')"
else
    echo -e "${YELLOW}! CRD not installed${NC}"
    echo "  Run: kubectl apply -f deploy/operator/crds/peninaomegacluster-crd.yaml"
fi

echo ""
echo "Phase 4: Operator Deployment"
echo "─────────────────────────────────────────────────"

# Check namespace
if check_resource "namespace" "penin-system"; then
    # Check ServiceAccount
    check_resource "serviceaccount" "penin-operator" "penin-system"
    
    # Check ClusterRole
    check_resource "clusterrole" "penin-operator-role"
    
    # Check ClusterRoleBinding
    check_resource "clusterrolebinding" "penin-operator-binding"
    
    # Check Deployment
    if check_resource "deployment" "penin-operator" "penin-system"; then
        # Check if operator is running
        READY=$(kubectl get deployment penin-operator -n penin-system -o jsonpath='{.status.readyReplicas}')
        DESIRED=$(kubectl get deployment penin-operator -n penin-system -o jsonpath='{.spec.replicas}')
        
        if [ "$READY" == "$DESIRED" ] && [ "$READY" != "" ]; then
            echo -e "${GREEN}✓ Operator is running ($READY/$DESIRED pods ready)${NC}"
        else
            echo -e "${YELLOW}! Operator pods not ready ($READY/$DESIRED)${NC}"
            echo "  Check with: kubectl get pods -n penin-system"
        fi
    fi
else
    echo -e "${YELLOW}! Operator not installed${NC}"
    echo "  Run: kubectl apply -f deploy/operator/manifests/operator.yaml"
fi

echo ""
echo "Phase 5: Operator Logs (last 10 lines)"
echo "─────────────────────────────────────────────────"

if kubectl get pods -n penin-system -l component=operator &> /dev/null; then
    POD=$(kubectl get pods -n penin-system -l component=operator -o jsonpath='{.items[0].metadata.name}')
    if [ -n "$POD" ]; then
        echo "  Pod: $POD"
        echo ""
        kubectl logs -n penin-system $POD --tail=10 2>/dev/null || echo "  (No logs available yet)"
    fi
else
    echo "  (Operator not running)"
fi

echo ""
echo "Phase 6: Test Clusters"
echo "─────────────────────────────────────────────────"

# Check for any PeninOmegaCluster resources
CLUSTERS=$(kubectl get penin --all-namespaces --no-headers 2>/dev/null | wc -l)

if [ "$CLUSTERS" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $CLUSTERS PENIN-Ω cluster(s)${NC}"
    echo ""
    kubectl get penin --all-namespaces
    
    echo ""
    echo "Phase 7: Cluster Services"
    echo "─────────────────────────────────────────────────"
    
    # Show pods for all clusters
    kubectl get pods --all-namespaces -l app=penin-omega 2>/dev/null || echo "  (No pods found)"
    
else
    echo -e "${YELLOW}! No PENIN-Ω clusters deployed${NC}"
    echo "  To deploy a development cluster:"
    echo "    kubectl apply -f deploy/operator/examples/cluster-dev.yaml"
    echo ""
    echo "  To deploy a production cluster:"
    echo "    kubectl apply -f deploy/operator/examples/cluster-production.yaml"
fi

echo ""
echo "═════════════════════════════════════════════════"
echo "Validation Summary"
echo "═════════════════════════════════════════════════"

# Count checks
TOTAL_CHECKS=8
PASSED_CHECKS=0

kubectl cluster-info &> /dev/null && ((PASSED_CHECKS++))
kubectl get crd peninaomegaclusters.penin.ai &> /dev/null && ((PASSED_CHECKS++))
kubectl get namespace penin-system &> /dev/null && ((PASSED_CHECKS++))
kubectl get serviceaccount penin-operator -n penin-system &> /dev/null && ((PASSED_CHECKS++))
kubectl get clusterrole penin-operator-role &> /dev/null && ((PASSED_CHECKS++))
kubectl get clusterrolebinding penin-operator-binding &> /dev/null && ((PASSED_CHECKS++))
kubectl get deployment penin-operator -n penin-system &> /dev/null && ((PASSED_CHECKS++))

READY=$(kubectl get deployment penin-operator -n penin-system -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
DESIRED=$(kubectl get deployment penin-operator -n penin-system -o jsonpath='{.spec.replicas}' 2>/dev/null)
[ "$READY" == "$DESIRED" ] && [ "$READY" != "" ] && ((PASSED_CHECKS++))

if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
    echo -e "${GREEN}✓ All checks passed ($PASSED_CHECKS/$TOTAL_CHECKS)${NC}"
    echo ""
    echo "The PENIN-Ω operator is properly installed and running!"
    echo ""
    echo "Next steps:"
    echo "  1. Deploy a cluster: make deploy-dev"
    echo "  2. Check status: kubectl get penin"
    echo "  3. View logs: make logs"
    echo "  4. Read docs: deploy/operator/README.md"
    exit 0
else
    echo -e "${YELLOW}⚠ Some checks failed ($PASSED_CHECKS/$TOTAL_CHECKS passed)${NC}"
    echo ""
    echo "To install the operator:"
    echo "  cd deploy/operator"
    echo "  make install"
    echo ""
    echo "For help:"
    echo "  • Check docs: deploy/operator/README.md"
    echo "  • Quick start: deploy/operator/QUICKSTART.md"
    echo "  • View logs: kubectl logs -n penin-system -l component=operator"
    exit 1
fi
