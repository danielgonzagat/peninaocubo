# PENIN-Ω Kubernetes Operator - Quick Start Guide

This guide will help you deploy a PENIN-Ω cluster in Kubernetes in under 5 minutes.

## Prerequisites

- Kubernetes cluster (v1.20+) - you can use:
  - **minikube**: `minikube start`
  - **kind**: `kind create cluster`
  - **Docker Desktop**: Enable Kubernetes in settings
  - Cloud providers: GKE, EKS, AKS
- `kubectl` configured and working
- Cluster admin permissions

## Step 1: Quick Install (1 minute)

```bash
# Clone repository
git clone https://github.com/danielgonzagat/peninaocubo.git
cd peninaocubo/deploy/operator

# Install everything
make install
```

This installs:
- Custom Resource Definitions (CRDs)
- Operator in `penin-system` namespace
- RBAC permissions

## Step 2: Verify Installation (30 seconds)

```bash
# Check operator is running
kubectl get pods -n penin-system

# Expected output:
# NAME                              READY   STATUS    RESTARTS   AGE
# penin-operator-xxxxxxxxxx-xxxxx   1/1     Running   0          30s

# Verify CRD is installed
kubectl get crd peninaomegaclusters.penin.ai
```

## Step 3: Deploy Your First Cluster (1 minute)

```bash
# Deploy development cluster
make deploy-dev

# Check deployment status
kubectl get penin
# Or with full name:
kubectl get peninaomegaclusters

# Expected output:
# NAME        PHASE      VERSION   AGE
# penin-dev   Creating   0.9.0     10s
```

## Step 4: Watch It Come Up (2 minutes)

```bash
# Watch cluster status
watch kubectl get pods -l app=penin-omega,cluster=penin-dev

# Expected output (after ~2 minutes):
# NAME                                        READY   STATUS    RESTARTS   AGE
# penin-dev-acfa-league-xxxxxxxxxx-xxxxx      1/1     Running   0          2m
# penin-dev-omega-meta-xxxxxxxxxx-xxxxx       1/1     Running   0          2m
# penin-dev-redis-xxxxxxxxxx-xxxxx            1/1     Running   0          2m
# penin-dev-sigma-guard-xxxxxxxxxx-xxxxx      1/1     Running   0          2m
# penin-dev-sr-omega-infinity-xxx-xxxxx       1/1     Running   0          2m
```

## Step 5: Access the Cluster (30 seconds)

```bash
# Port-forward to services
make port-forward-dev

# In another terminal, test the services:
curl http://localhost:8010/health  # Ω-META
curl http://localhost:8011/health  # Σ-Guard
curl http://localhost:8012/health  # SR-Ω∞
curl http://localhost:8013/health  # ACFA League

# View metrics
curl http://localhost:8010/metrics
```

## Step 6: Check Cluster Details

```bash
# Get detailed status
kubectl describe penin penin-dev

# View logs from any service
kubectl logs -l app=penin-omega,service=omega-meta --tail=20

# Check all services
kubectl get svc -l app=penin-omega,cluster=penin-dev
```

## What You Just Created

Your cluster includes:

1. **Ω-META** - Master orchestrator (1 replica)
2. **Σ-Guard** - Fail-closed security gates (1 replica)
3. **SR-Ω∞** - Self-reflection service (1 replica)
4. **ACFA League** - Champion-challenger orchestration (1 replica)
5. **Redis** - Caching layer (1 replica)

All services are:
- ✅ Auto-configured with environment variables
- ✅ Health-checked with liveness/readiness probes
- ✅ Monitored with Prometheus metrics
- ✅ Logged with structured JSON
- ✅ Connected via Kubernetes services

## Next Steps

### Scale a Service

```bash
# Scale Σ-Guard to 3 replicas for high availability
kubectl patch penin penin-dev --type=merge -p '{"spec":{"replicas":{"sigmaGuard":3}}}'

# Watch the scaling
kubectl get pods -l service=sigma-guard -w
```

### Update Configuration

```bash
# Increase daily budget
kubectl patch penin penin-dev --type=merge -p '{"spec":{"config":{"budgetDailyUsd":10.0}}}'

# Change CAOS+ parameters
kubectl patch penin penin-dev --type=merge -p '{"spec":{"config":{"caosPlus":{"kappa":25.0}}}}'
```

### Deploy Production Cluster

```bash
# Create production namespace
kubectl create namespace penin-prod

# Deploy production cluster (HA configuration)
make deploy-prod

# Check status
kubectl get penin -n penin-prod
```

### Monitor Metrics

```bash
# Port-forward to Prometheus (if deployed)
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Or directly from service
kubectl port-forward svc/penin-dev-omega-meta 8010:8010
curl http://localhost:8010/metrics | grep penin_
```

### View Operator Logs

```bash
# Follow operator logs
make logs

# Or directly:
kubectl logs -n penin-system -l component=operator -f
```

## Clean Up

```bash
# Delete the cluster
make delete-dev

# Or manually:
kubectl delete penin penin-dev

# Uninstall operator (if desired)
make uninstall
```

## Common Issues

### Pods Stuck in Pending

Check events:
```bash
kubectl describe pod <pod-name>
kubectl get events --sort-by='.lastTimestamp'
```

Possible causes:
- Insufficient resources (increase cluster size)
- Missing storage class (check with `kubectl get sc`)
- Image pull issues (check image pull policy)

### Services Not Ready

Check logs:
```bash
kubectl logs -l service=omega-meta
```

Common issues:
- Configuration errors (check env vars)
- Network issues (check service connectivity)
- Resource limits too low (increase in spec)

### Operator Not Working

```bash
# Check operator status
kubectl get pods -n penin-system
kubectl logs -n penin-system -l component=operator

# Restart operator if needed
make restart-operator
```

## Architecture Overview

```
User
  │
  └──> kubectl apply -f cluster.yaml
         │
         ▼
  [Kubernetes API]
         │
         ▼
  [PENIN-Ω Operator]
         │
         ├──> Creates Deployments
         ├──> Creates Services
         ├──> Creates ConfigMaps
         ├──> Monitors Health
         └──> Updates Status
                │
                ▼
         [PENIN-Ω Cluster]
           ├── Ω-META
           ├── Σ-Guard
           ├── SR-Ω∞
           ├── ACFA League
           └── Redis
```

## Configuration Options

The operator supports extensive configuration through the CRD spec:

```yaml
spec:
  version: "0.9.0"              # PENIN-Ω version
  
  replicas:                     # Replica counts
    omegaMeta: 1
    sigmaGuard: 2
    srOmegaInfinity: 1
    acfaLeague: 1
  
  resources:                    # Resource limits
    omegaMeta:
      cpu: "500m"
      memory: "512Mi"
  
  config:                       # PENIN-Ω configuration
    budgetDailyUsd: 5.0
    caosPlus:
      maxBoost: 0.05
      kappa: 20.0
    sigmaGuard:
      eceThreshold: 0.01
      biasThreshold: 1.05
  
  observability:                # Monitoring settings
    metrics: true
    tracing: true
    logging:
      level: "INFO"
  
  storage:                      # Storage configuration
    cache:
      enabled: true
      type: "redis"
```

See the [full documentation](README.md) for all options.

## Further Reading

- [Complete Operator Documentation](README.md)
- [Architecture Guide](../../docs/architecture.md)
- [PENIN-Ω Documentation](../../README.md)
- [Kubernetes Operator Pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)

## Support

Need help?
- Check [Troubleshooting section](README.md#troubleshooting)
- View [GitHub Issues](https://github.com/danielgonzagat/peninaocubo/issues)
- Check operator logs: `make logs`

---

**Congratulations!** 🎉 You now have a fully functional PENIN-Ω cluster running in Kubernetes!
