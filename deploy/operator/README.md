# PENIN-Ω Kubernetes Operator

## Overview

The PENIN-Ω Kubernetes Operator automates the deployment and lifecycle management of PENIN-Ω clusters in Kubernetes. It transforms PENIN-Ω into a true cloud-native system with self-healing, auto-scaling, and self-architecting capabilities.

## Features

### 🎯 Core Capabilities

- **Automated Deployment**: One-command cluster creation with all microservices
- **Lifecycle Management**: Automated upgrades, scaling, and configuration updates
- **Health Monitoring**: Continuous health checks with automatic recovery
- **Self-Healing**: Automatic pod restarts and service recovery
- **Configuration Management**: Centralized configuration through CRDs
- **Observability**: Built-in Prometheus metrics and logging

### 🏗️ Managed Services

The operator manages the complete PENIN-Ω microservices architecture:

1. **Ω-META** (port 8010): Master orchestrator and coordination service
2. **Σ-Guard** (port 8011): Fail-closed security gates with ethical validation
3. **SR-Ω∞** (port 8012): Self-reflection and continuous assessment service
4. **ACFA League** (port 8013): Champion-challenger evolution and deployment orchestration

### 🔄 Auto-Evolution Support

The operator enables Phase 3 (Transcendência) capabilities:

- **Real-Time Self-Architecting**: Operator can modify service replicas based on SR-Ω∞ feedback
- **Dynamic Resource Allocation**: Automatic scaling based on system metrics
- **A/B Testing**: Support for champion-challenger deployments through ACFA League

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PENIN-Ω Operator                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Create     │  │   Update     │  │   Monitor    │          │
│  │   Handler    │  │   Handler    │  │   Timer      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                  │
│         └─────────────────┴──────────────────┘                  │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │  Kubernetes API      │
                 └──────────────────────┘
                            │
        ┏━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━┓
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Ω-META      │    │  Σ-Guard     │    │  SR-Ω∞       │
│  Deployment  │    │  Deployment  │    │  Deployment  │
│  + Service   │    │  + Service   │    │  + Service   │
└──────────────┘    └──────────────┘    └──────────────┘
        
        ▼
┌──────────────┐    ┌──────────────┐
│  ACFA League │    │  Redis       │
│  Deployment  │    │  (Cache)     │
│  + Service   │    └──────────────┘
└──────────────┘
```

## Installation

### Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- Cluster admin permissions

### Step 1: Install CRDs

```bash
kubectl apply -f deploy/operator/crds/peninaomegacluster-crd.yaml
```

### Step 2: Deploy the Operator

```bash
kubectl apply -f deploy/operator/manifests/operator.yaml
```

This creates:
- `penin-system` namespace
- ServiceAccount with RBAC permissions
- Operator Deployment

### Step 3: Verify Installation

```bash
# Check operator is running
kubectl get pods -n penin-system

# Check CRD is installed
kubectl get crd peninaomegaclusters.penin.ai
```

## Usage

### Creating a Cluster

#### Development Cluster

```bash
kubectl apply -f deploy/operator/examples/cluster-dev.yaml
```

This creates a minimal PENIN-Ω cluster suitable for development:
- 1 replica of each service
- Minimal resource allocation
- DEBUG logging
- Local storage

#### Production Cluster

```bash
# Create production namespace
kubectl create namespace penin-prod

# Deploy cluster
kubectl apply -f deploy/operator/examples/cluster-production.yaml
```

This creates a production-ready cluster with:
- High availability (multiple replicas)
- Production resource limits
- INFO logging
- SSD storage
- Redis caching

### Checking Cluster Status

```bash
# List clusters
kubectl get peninaomegaclusters
# Or use shorthand
kubectl get penin

# Get detailed status
kubectl describe penin penin-dev

# Check service pods
kubectl get pods -l app=penin-omega,cluster=penin-dev

# Check services
kubectl get svc -l app=penin-omega,cluster=penin-dev
```

### Scaling Services

Edit the cluster resource:

```bash
kubectl edit penin penin-dev
```

Update the replicas section:

```yaml
spec:
  replicas:
    sigmaGuard: 3  # Scale to 3 replicas
```

The operator will automatically update the deployment.

Or use kubectl patch:

```bash
kubectl patch penin penin-dev --type=merge -p '{"spec":{"replicas":{"sigmaGuard":3}}}'
```

### Updating Configuration

Update the configuration section:

```bash
kubectl patch penin penin-dev --type=merge -p '{
  "spec": {
    "config": {
      "budgetDailyUsd": 10.0,
      "caosPlus": {
        "kappa": 25.0
      }
    }
  }
}'
```

The operator will roll out the changes to all affected services.

### Upgrading Version

```bash
kubectl patch penin penin-dev --type=merge -p '{"spec":{"version":"1.0.0"}}'
```

The operator will perform a rolling update of all services.

### Deleting a Cluster

```bash
kubectl delete penin penin-dev
```

This automatically removes all resources (Deployments, Services, ConfigMaps).

## Custom Resource Specification

### PeninOmegaCluster

```yaml
apiVersion: penin.ai/v1alpha1
kind: PeninOmegaCluster
metadata:
  name: my-cluster
  namespace: default
spec:
  # Version of PENIN-Ω
  version: "0.9.0"
  
  # Replica counts
  replicas:
    omegaMeta: 1
    sigmaGuard: 2
    srOmegaInfinity: 1
    acfaLeague: 1
  
  # Resource limits
  resources:
    omegaMeta:
      cpu: "500m"
      memory: "512Mi"
    # ... other services
  
  # Configuration
  config:
    budgetDailyUsd: 5.0
    
    caosPlus:
      maxBoost: 0.05
      kappa: 20.0
    
    sigmaGuard:
      eceThreshold: 0.01
      biasThreshold: 1.05
    
    evolution:
      seed: 12345
  
  # Observability
  observability:
    metrics: true
    tracing: true
    logging:
      level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  
  # Storage
  storage:
    wormLedger:
      enabled: true
      storageClass: "standard"
      size: "10Gi"
    
    cache:
      enabled: true
      type: "redis"  # redis or memory
```

### Status Fields

The operator updates the status with real-time information:

```yaml
status:
  # Overall cluster phase
  phase: "Running"  # Pending, Creating, Running, Updating, Failed, Terminating
  
  # Service health
  services:
    omegaMeta:
      ready: true
      replicas: 1
      readyReplicas: 1
    sigmaGuard:
      ready: true
      replicas: 2
      readyReplicas: 2
    # ... other services
  
  # System metrics
  metrics:
    alpha: 0.7828
    deltaLinf: 0.0500
    caosPlus: 3.9045
    srScore: 0.8668
  
  # Conditions
  conditions:
    - type: "Ready"
      status: "True"
      lastTransitionTime: "2025-01-15T10:30:00Z"
      reason: "AllServicesHealthy"
      message: "All services are running and healthy"
  
  lastUpdateTime: "2025-01-15T10:30:00Z"
```

## Monitoring

### Accessing Metrics

Each service exposes Prometheus metrics:

```bash
# Port-forward to Ω-META
kubectl port-forward -n default svc/penin-dev-omega-meta 8010:8010

# Access metrics
curl http://localhost:8010/metrics
```

### Key Metrics

- `penin_alpha`: Current α_t^Ω value
- `penin_delta_linf`: Change in L∞ score
- `penin_caos_plus`: CAOS+ amplification factor
- `penin_sr_score`: Self-reflection score
- `penin_gate_fail_total`: Gate failure counters
- `penin_cycle_duration_seconds`: Evolution cycle duration

### Health Checks

```bash
# Check service health
kubectl port-forward -n default svc/penin-dev-omega-meta 8010:8010
curl http://localhost:8010/health
```

## Troubleshooting

### Cluster Not Starting

Check operator logs:

```bash
kubectl logs -n penin-system deployment/penin-operator
```

Check pod status:

```bash
kubectl get pods -l app=penin-omega,cluster=penin-dev
kubectl describe pod <pod-name>
```

### Services Not Ready

Check pod logs:

```bash
kubectl logs -l app=penin-omega,service=omega-meta
```

Check events:

```bash
kubectl get events --sort-by='.lastTimestamp' | grep penin
```

### Configuration Issues

Validate cluster spec:

```bash
kubectl get penin penin-dev -o yaml
```

Check for validation errors:

```bash
kubectl describe penin penin-dev
```

### Resource Issues

Check resource usage:

```bash
kubectl top pods -l app=penin-omega,cluster=penin-dev
```

Adjust resource limits if needed:

```bash
kubectl patch penin penin-dev --type=merge -p '{
  "spec": {
    "resources": {
      "omegaMeta": {
        "cpu": "1000m",
        "memory": "1Gi"
      }
    }
  }
}'
```

## Advanced Usage

### Multi-Cluster Deployments

Deploy to multiple namespaces:

```bash
# Development
kubectl apply -f examples/cluster-dev.yaml -n dev

# Staging
kubectl apply -f examples/cluster-staging.yaml -n staging

# Production
kubectl apply -f examples/cluster-production.yaml -n prod
```

### Custom Storage Classes

Use specific storage classes:

```yaml
spec:
  storage:
    wormLedger:
      storageClass: "fast-ssd"
      size: "100Gi"
```

### Integration with Observability Stack

The operator integrates with standard Kubernetes observability:

- **Prometheus**: Automatic service discovery via annotations
- **Grafana**: Import dashboards from `deploy/grafana/`
- **Logging**: Structured JSON logs to stdout

### Auto-Scaling (Future)

The operator will support HPA integration:

```yaml
spec:
  autoScaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPU: 70
    targetMemory: 80
```

### Self-Architecting (Phase 3)

The operator enables the SR-Ω∞ service to request infrastructure changes:

1. SR-Ω∞ detects performance bottleneck
2. Sends scaling request to operator
3. Operator evaluates request against policies
4. Updates cluster configuration
5. Monitors impact
6. Rolls back if performance degrades

## Security

### RBAC

The operator requires cluster-wide permissions to:
- Manage CRDs and custom resources
- Create/update/delete Deployments and Services
- Read pod status for monitoring

See `manifests/operator.yaml` for full RBAC configuration.

### Network Policies

Apply network policies to restrict traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: penin-network-policy
spec:
  podSelector:
    matchLabels:
      app: penin-omega
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: penin-omega
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: penin-omega
```

### Secrets Management

Store sensitive configuration in Secrets:

```bash
kubectl create secret generic penin-secrets \
  --from-literal=openai-api-key=sk-... \
  --from-literal=redis-password=...
```

Reference in cluster spec (future feature).

## Development

### Building the Operator

```bash
# Build Docker image
docker build -t ghcr.io/danielgonzagat/penin-operator:latest \
  -f deploy/operator/Dockerfile .

# Push to registry
docker push ghcr.io/danielgonzagat/penin-operator:latest
```

### Testing Locally

```bash
# Install kopf
pip install kopf kubernetes

# Run operator locally (out-of-cluster)
cd deploy/operator
python penin_operator.py
```

### Running Tests

```bash
pytest tests/operator/
```

## Roadmap

### v1.0 (Current)
- [x] Basic cluster lifecycle management
- [x] Health monitoring
- [x] Configuration management
- [x] Multiple replica support

### v1.1 (Next)
- [ ] Horizontal Pod Autoscaling
- [ ] PersistentVolume management for WORM ledger
- [ ] Secret management integration
- [ ] Custom metrics from SR-Ω∞

### v1.2 (Future)
- [ ] Self-architecting capabilities
- [ ] A/B testing automation
- [ ] Multi-cluster federation
- [ ] GitOps integration

### v2.0 (Phase 3)
- [ ] Full auto-evolution loop
- [ ] Protocol mutation support
- [ ] Swarm intelligence orchestration
- [ ] Proto-consciousness integration

## References

- [Kopf Documentation](https://kopf.readthedocs.io/)
- [Kubernetes Operator Pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
- [PENIN-Ω Architecture](../../docs/architecture.md)
- [Custom Resource Definitions](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/)

## Support

For issues and questions:
- GitHub Issues: https://github.com/danielgonzagat/peninaocubo/issues
- Documentation: `docs/`
- Operator Logs: `kubectl logs -n penin-system deployment/penin-operator`

---

**PENIN-Ω Kubernetes Operator** - Cloud-Native IA³ Orchestration
