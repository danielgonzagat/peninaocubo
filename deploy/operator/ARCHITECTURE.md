# PENIN-Ω Kubernetes Operator Architecture

## Overview

The PENIN-Ω Kubernetes Operator is a cloud-native controller that automates the deployment and lifecycle management of PENIN-Ω clusters in Kubernetes environments.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                              │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                    penin-system namespace                     │    │
│  │                                                                │    │
│  │  ┌──────────────────────────────────────────────────────┐    │    │
│  │  │         PENIN-Ω Operator (Kopf-based)               │    │    │
│  │  │                                                       │    │    │
│  │  │  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │    │    │
│  │  │  │  Create    │  │   Update   │  │   Monitor    │  │    │    │
│  │  │  │  Handler   │  │   Handler  │  │   Timer      │  │    │    │
│  │  │  │  @on.create│  │  @on.update│  │  @timer(30s) │  │    │    │
│  │  │  └─────┬──────┘  └─────┬──────┘  └──────┬───────┘  │    │    │
│  │  │        │                │                │          │    │    │
│  │  │        └────────────────┴────────────────┘          │    │    │
│  │  │                         │                           │    │    │
│  │  └─────────────────────────┼───────────────────────────┘    │    │
│  │                            │                                │    │
│  └────────────────────────────┼────────────────────────────────┘    │
│                               │                                     │
│                               ▼                                     │
│                    ┌─────────────────────┐                          │
│                    │  Kubernetes API     │                          │
│                    │  Server             │                          │
│                    └──────────┬──────────┘                          │
│                               │                                     │
│        ┏━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━┓            │
│        ▼                      ▼                        ▼            │
│  ┌──────────┐         ┌──────────┐              ┌──────────┐       │
│  │   CRD    │         │ RBAC     │              │ Events   │       │
│  │ PeninOmeg│         │ Rules    │              │ Logging  │       │
│  │ aCluster │         │          │              │          │       │
│  └──────────┘         └──────────┘              └──────────┘       │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              User Namespace (e.g., default)                   │ │
│  │                                                                │ │
│  │  ┌────────────────────────────────────────────────────────┐  │ │
│  │  │  PeninOmegaCluster CR: penin-dev                       │  │ │
│  │  │  ├── spec.version: "0.9.0"                             │  │ │
│  │  │  ├── spec.replicas: {...}                              │  │ │
│  │  │  ├── spec.resources: {...}                             │  │ │
│  │  │  ├── spec.config: {...}                                │  │ │
│  │  │  └── status: {phase, services, metrics}                │  │ │
│  │  └────────────────────────────────────────────────────────┘  │ │
│  │                                                                │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │              Managed Resources                          │ │ │
│  │  │                                                          │ │ │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ │ │
│  │  │  │  Deployment  │  │  Deployment  │  │  Deployment  │ │ │ │
│  │  │  │  omega-meta  │  │  sigma-guard │  │  sr-omega-∞  │ │ │ │
│  │  │  │  Replicas: 1 │  │  Replicas: 2 │  │  Replicas: 1 │ │ │ │
│  │  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │ │ │
│  │  │         │                 │                  │         │ │ │
│  │  │  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐ │ │ │
│  │  │  │   Service    │  │   Service    │  │   Service    │ │ │ │
│  │  │  │   :8010      │  │   :8011      │  │   :8012      │ │ │ │
│  │  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │ │ │
│  │  │         │                 │                  │         │ │ │
│  │  │  ┌──────▼───────────────────────────────────▼───────┐ │ │ │
│  │  │  │                Pod Network                       │ │ │ │
│  │  │  │  • Pod: omega-meta-xxx (Ready 1/1)               │ │ │ │
│  │  │  │  • Pod: sigma-guard-xxx (Ready 1/1)              │ │ │ │
│  │  │  │  • Pod: sigma-guard-yyy (Ready 1/1)              │ │ │ │
│  │  │  │  • Pod: sr-omega-infinity-xxx (Ready 1/1)        │ │ │ │
│  │  │  │  • Pod: acfa-league-xxx (Ready 1/1)              │ │ │ │
│  │  │  │  • Pod: redis-xxx (Ready 1/1)                    │ │ │ │
│  │  │  └──────────────────────────────────────────────────┘ │ │ │
│  │  │                                                          │ │ │
│  │  │  ┌──────────────┐  ┌──────────────┐                    │ │ │
│  │  │  │  Deployment  │  │  Deployment  │                    │ │ │
│  │  │  │  acfa-league │  │  redis       │                    │ │ │
│  │  │  │  Replicas: 1 │  │  Replicas: 1 │                    │ │ │
│  │  │  └──────────────┘  └──────────────┘                    │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              Observability Stack (optional)                   │ │
│  │                                                                │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │ │
│  │  │ Prometheus  │  │  Grafana    │  │   Loki      │          │ │
│  │  │ (metrics)   │  │ (dashboards)│  │  (logs)     │          │ │
│  │  └──────┬──────┘  └─────────────┘  └─────────────┘          │ │
│  │         │                                                     │ │
│  │         │ Scrapes /metrics endpoint                          │ │
│  │         └──────────────────┐                                 │ │
│  │                            ▼                                 │ │
│  │                    Service Monitors                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

      User Interactions
      ─────────────────

   kubectl apply -f cluster.yaml  ──────┐
   kubectl get penin              ──────┤
   kubectl patch penin ...        ──────┼─> Kubernetes API
   kubectl delete penin ...       ──────┤
   kubectl logs ...               ──────┘
```

## Component Responsibilities

### 1. Operator Components

#### Create Handler (@on.create)
- **Triggered:** When a new PeninOmegaCluster is created
- **Actions:**
  - Creates Deployments for all 4 services
  - Creates Services for networking
  - Creates Redis deployment (if caching enabled)
  - Sets owner references for automatic cleanup
  - Initializes cluster status

#### Update Handler (@on.update)
- **Triggered:** When PeninOmegaCluster spec is modified
- **Actions:**
  - Detects changes in replicas
  - Scales deployments up/down
  - Updates resource limits
  - Rolls out configuration changes

#### Monitor Timer (@timer(30s))
- **Triggered:** Every 30 seconds for all clusters
- **Actions:**
  - Checks deployment health
  - Updates service readiness status
  - Updates cluster phase
  - Reports metrics

#### Delete Handler (@on.delete)
- **Triggered:** When PeninOmegaCluster is deleted
- **Actions:**
  - Kubernetes auto-cleanup via owner references
  - Logs deletion event

### 2. Managed Resources

#### Deployments
Each service gets its own Deployment:
- **omega-meta**: Orchestrator (configurable replicas)
- **sigma-guard**: Security gates (configurable replicas, recommended 2+)
- **sr-omega-infinity**: Self-reflection (configurable replicas)
- **acfa-league**: Champion-challenger (configurable replicas)
- **redis**: Cache (1 replica)

#### Services
Each Deployment has a corresponding Service:
- Type: ClusterIP
- Port mapping to container ports
- Selector: matches pod labels
- Enables inter-service communication

#### Pods
Created by Deployments with:
- Health probes (liveness + readiness)
- Resource requests/limits
- Environment variables from spec
- Prometheus annotations
- Structured logging to stdout

### 3. Custom Resource Definition (CRD)

```yaml
apiVersion: penin.ai/v1alpha1
kind: PeninOmegaCluster
metadata:
  name: my-cluster
spec:
  # User-defined configuration
  version: "0.9.0"
  replicas: {...}
  resources: {...}
  config: {...}
  
status:
  # Operator-managed status
  phase: "Running"
  services:
    omegaMeta: {ready: true, replicas: 1}
    sigmaGuard: {ready: true, replicas: 2}
    # ...
  metrics:
    alpha: 0.7828
    deltaLinf: 0.0500
    # ...
```

## Data Flow

### 1. Cluster Creation Flow

```
User
  │
  └─> kubectl apply -f cluster-dev.yaml
        │
        ▼
    Kubernetes API
        │
        ▼
    Operator (Create Handler)
        │
        ├─> Create omega-meta Deployment + Service
        ├─> Create sigma-guard Deployment + Service
        ├─> Create sr-omega-infinity Deployment + Service
        ├─> Create acfa-league Deployment + Service
        └─> Create redis Deployment + Service
              │
              ▼
          Pods start
              │
              ├─> Health checks
              ├─> Load configuration
              └─> Report metrics
                    │
                    ▼
              Operator (Monitor Timer)
                    │
                    └─> Update status
```

### 2. Configuration Update Flow

```
User
  │
  └─> kubectl patch penin penin-dev -p '{"spec":{"replicas":{"sigmaGuard":3}}}'
        │
        ▼
    Kubernetes API
        │
        ▼
    Operator (Update Handler)
        │
        └─> Patch sigma-guard Deployment
              │
              └─> replicas: 2 → 3
                    │
                    ▼
              New pod created
                    │
                    ├─> Health checks pass
                    └─> Joins service
                          │
                          ▼
                    Operator (Monitor Timer)
                          │
                          └─> Update status
                                readyReplicas: 2 → 3
```

### 3. Health Monitoring Flow

```
Operator (Monitor Timer - every 30s)
  │
  ├─> Query Deployment status
  │     │
  │     └─> deployment.status.readyReplicas
  │
  ├─> Update CR status
  │     │
  │     └─> status.services.{service}.ready
  │
  └─> Determine cluster phase
        │
        ├─> All ready → "Running"
        ├─> Some pending → "Updating"
        └─> All failed → "Failed"
```

## Owner References

The operator uses Kubernetes owner references to manage resource lifecycle:

```yaml
ownerReferences:
  - apiVersion: penin.ai/v1alpha1
    kind: PeninOmegaCluster
    name: penin-dev
    uid: <cluster-uid>
    controller: true
    blockOwnerDeletion: true
```

**Benefits:**
- Automatic cleanup when cluster is deleted
- Cascading deletion of all resources
- Prevents accidental resource leaks
- No manual cleanup required

## RBAC Permissions

The operator requires the following permissions:

### Cluster-wide:
- **penin.ai/peninaomegaclusters**: Full CRUD + status updates
- **apps/deployments**: Full CRUD for service deployments
- **core/services**: Full CRUD for networking
- **core/configmaps**: Full CRUD for configuration
- **core/pods**: Read for monitoring
- **core/events**: Create for status reporting

### Service Account:
- Name: `penin-operator`
- Namespace: `penin-system`
- Role: ClusterRole `penin-operator-role`
- Binding: ClusterRoleBinding `penin-operator-binding`

## Configuration Propagation

Configuration flows from CRD spec to pod environment:

```
PeninOmegaCluster.spec.config
  │
  ├─> budgetDailyUsd → PENIN_BUDGET_DAILY_USD
  │
  ├─> caosPlus.kappa → PENIN_CAOS_PLUS__KAPPA
  │
  ├─> sigmaGuard.eceThreshold → PENIN_SIGMA_GUARD__ECE_THRESHOLD
  │
  └─> evolution.seed → PENIN_EVOLUTION__SEED
        │
        ▼
    Pod Environment Variables
        │
        └─> PENIN services read on startup
```

## Self-Architecting (Phase 3)

The operator enables future self-architecting capabilities:

```
SR-Ω∞ Service
  │
  └─> Detects performance bottleneck
        │
        └─> Requests infrastructure change
              │
              ▼
          Operator API (future)
              │
              ├─> Validates request
              ├─> Checks policies
              └─> Updates cluster spec
                    │
                    ▼
              Update Handler triggered
                    │
                    └─> Scales service
                          │
                          └─> Monitors impact
                                │
                                ├─> Performance improved → Keep
                                └─> Performance degraded → Rollback
```

## Scaling Patterns

### Horizontal Scaling
```
kubectl patch penin penin-dev -p '{"spec":{"replicas":{"sigmaGuard":5}}}'
  │
  └─> Operator scales sigma-guard: 2 → 5 pods
        │
        └─> Load balanced across all pods
```

### Vertical Scaling
```
kubectl patch penin penin-dev -p '{"spec":{"resources":{"omegaMeta":{"cpu":"2000m"}}}}'
  │
  └─> Operator updates deployment resources
        │
        └─> Rolling restart with new limits
```

## High Availability

Production deployments use multiple replicas:

```yaml
spec:
  replicas:
    omegaMeta: 2        # Active-active
    sigmaGuard: 3       # Majority quorum
    srOmegaInfinity: 2  # Active-active
    acfaLeague: 2       # Active-active
```

**Benefits:**
- No single point of failure
- Rolling updates without downtime
- Automatic failover
- Load distribution

## Monitoring Integration

### Prometheus Scraping

Pods are automatically annotated:
```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8010"
  prometheus.io/path: "/metrics"
```

Prometheus auto-discovers and scrapes metrics.

### Grafana Dashboards

Pre-configured dashboards visualize:
- L∞ evolution over time
- CAOS+ component breakdown
- SR-Ω∞ 4D radar chart
- Gate pass/fail rates
- Resource utilization

## Future Enhancements

### v1.1
- [ ] HorizontalPodAutoscaler integration
- [ ] PersistentVolume for WORM ledger
- [ ] Secret management
- [ ] Custom metrics from SR-Ω∞

### v1.2
- [ ] Self-architecting API
- [ ] Multi-cluster federation
- [ ] A/B testing automation
- [ ] GitOps integration (Flux/ArgoCD)

### v2.0 (Phase 3)
- [ ] Full auto-evolution loop
- [ ] Protocol mutation support
- [ ] Swarm intelligence
- [ ] Proto-consciousness integration

---

**Note:** This operator implements the foundation for Phase 1 (production readiness) and Phase 3 (self-architecting) of the PENIN-Ω roadmap.
