# High Availability Deployment Guide

## Overview

This guide covers deploying PENIN-Ω in a high availability (HA) configuration with redundancy, failover, and disaster recovery capabilities.

## Architecture Components

### Core Components
- **PENIN-Ω Core**: Main evolution engine
- **WORM Ledger**: Append-only audit trail
- **Router**: Multi-LLM routing with cost awareness
- **Observability**: Metrics and logging
- **Policy Engine**: OPA/Rego policy evaluation

### HA Requirements
- **Availability**: 99.9% uptime target
- **RTO**: Recovery Time Objective < 5 minutes
- **RPO**: Recovery Point Objective < 1 minute
- **Failover**: Automatic failover within 30 seconds

## Deployment Architecture

### Primary-Secondary Setup

```
┌─────────────────┐    ┌─────────────────┐
│   Primary Node  │    │ Secondary Node  │
│                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ PENIN Core  │ │◄──►│ │ PENIN Core  │ │
│ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ WORM Ledger │ │◄──►│ │ WORM Ledger │ │
│ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Observability│ │    │ │ Observability│ │
│ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
                   │
            ┌─────────────┐
            │ Load Balancer│
            └─────────────┘
```

### Database Replication

#### WORM Ledger Replication
```sql
-- Primary WORM configuration
PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
PRAGMA wal_autocheckpoint=1000;

-- Secondary replication setup
ATTACH DATABASE 'worm_replica.db' AS replica;
CREATE TABLE replica.events AS SELECT * FROM events;
```

#### Cache L2 Replication
- **Redis Cluster**: 3-node cluster with automatic failover
- **Cache Invalidation**: Event-driven cache sync
- **HMAC Verification**: Integrity checks on replicated data

## Deployment Steps

### 1. Infrastructure Setup

```bash
# Create HA cluster
kubectl create namespace penin-ha

# Deploy primary node
kubectl apply -f k8s/primary-deployment.yaml

# Deploy secondary node
kubectl apply -f k8s/secondary-deployment.yaml

# Deploy load balancer
kubectl apply -f k8s/loadbalancer.yaml
```

### 2. Database Setup

```bash
# Initialize primary WORM
kubectl exec -it penin-primary-0 -- python -c "
from penin.omega.ledger import WORMLedger
ledger = WORMLedger('/data/worm.db')
ledger.initialize()
"

# Setup replication
kubectl exec -it penin-primary-0 -- python -c "
from penin.omega.ledger import setup_replication
setup_replication('/data/worm.db', 'penin-secondary:5432')
"
```

### 3. Observability Setup

```bash
# Deploy Prometheus
helm install prometheus prometheus-community/prometheus

# Deploy Grafana
helm install grafana grafana/grafana

# Configure alerts
kubectl apply -f monitoring/alerts.yaml
```

## Health Checks

### Application Health Checks

```python
# Health check endpoint
@app.get("/health")
async def health_check():
    checks = {
        "core": await check_core_health(),
        "worm": await check_worm_health(),
        "router": await check_router_health(),
        "observability": await check_observability_health()
    }
    
    overall_health = all(checks.values())
    status_code = 200 if overall_health else 503
    
    return JSONResponse(
        content={"status": "healthy" if overall_health else "unhealthy", "checks": checks},
        status_code=status_code
    )
```

### Database Health Checks

```python
async def check_worm_health():
    try:
        ledger = WORMLedger("/data/worm.db")
        # Check if we can read and write
        test_record = {"test": "health_check", "timestamp": time.time()}
        ledger.append_record("health_check", test_record)
        return True
    except Exception as e:
        logger.error(f"WORM health check failed: {e}")
        return False
```

## Failover Procedures

### Automatic Failover

```python
class HAFailoverManager:
    def __init__(self):
        self.primary_node = "penin-primary"
        self.secondary_node = "penin-secondary"
        self.health_check_interval = 30  # seconds
        
    async def monitor_health(self):
        while True:
            if not await self.check_primary_health():
                await self.initiate_failover()
            await asyncio.sleep(self.health_check_interval)
    
    async def initiate_failover(self):
        logger.warning("Primary node unhealthy, initiating failover")
        
        # 1. Stop traffic to primary
        await self.update_load_balancer(self.secondary_node)
        
        # 2. Promote secondary to primary
        await self.promote_secondary()
        
        # 3. Update DNS/Service discovery
        await self.update_service_discovery()
        
        # 4. Notify monitoring systems
        await self.notify_monitoring_systems()
```

### Manual Failover

```bash
# 1. Check current status
kubectl get pods -n penin-ha

# 2. Stop primary service
kubectl scale deployment penin-primary --replicas=0

# 3. Promote secondary
kubectl label node penin-secondary-0 role=primary

# 4. Update load balancer
kubectl patch service penin-lb -p '{"spec":{"selector":{"role":"primary"}}}'

# 5. Verify failover
kubectl get endpoints penin-lb
```

## Monitoring and Alerting

### Key Metrics

```yaml
# Prometheus alerts
groups:
- name: penin-ha
  rules:
  - alert: PrimaryNodeDown
    expr: up{job="penin-primary"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Primary PENIN node is down"
      
  - alert: WormReplicationLag
    expr: worm_replication_lag_seconds > 60
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "WORM replication lag is high"
      
  - alert: HighErrorRate
    expr: rate(penin_errors_total[5m]) > 0.1
    for: 3m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "PENIN-Ω HA Dashboard",
    "panels": [
      {
        "title": "Node Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=~\"penin-.*\"}"
          }
        ]
      },
      {
        "title": "WORM Replication Lag",
        "type": "graph",
        "targets": [
          {
            "expr": "worm_replication_lag_seconds"
          }
        ]
      }
    ]
  }
}
```

## Disaster Recovery

### Backup Strategy

```bash
# Daily WORM backup
#!/bin/bash
DATE=$(date +%Y%m%d)
kubectl exec penin-primary-0 -- sqlite3 /data/worm.db ".backup /backup/worm_${DATE}.db"

# Upload to S3
aws s3 cp /backup/worm_${DATE}.db s3://penin-backups/worm/

# Cleanup old backups (keep 30 days)
find /backup -name "worm_*.db" -mtime +30 -delete
```

### Recovery Procedures

```bash
# 1. Restore from backup
kubectl exec penin-primary-0 -- sqlite3 /data/worm.db < worm_20240107.db

# 2. Verify data integrity
kubectl exec penin-primary-0 -- python -c "
from penin.omega.ledger import WORMLedger
ledger = WORMLedger('/data/worm.db')
print(f'Records: {ledger.count_records()}')
print(f'Integrity: {ledger.verify_integrity()}')
"

# 3. Restart services
kubectl rollout restart deployment/penin-primary
kubectl rollout restart deployment/penin-secondary
```

## Performance Tuning

### Database Optimization

```sql
-- WORM optimization
PRAGMA cache_size = 10000;
PRAGMA temp_store = memory;
PRAGMA mmap_size = 268435456;  -- 256MB

-- Index optimization
CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type);
```

### Cache Optimization

```python
# Redis cluster configuration
REDIS_CONFIG = {
    "cluster": {
        "nodes": [
            {"host": "redis-0", "port": 6379},
            {"host": "redis-1", "port": 6379},
            {"host": "redis-2", "port": 6379}
        ]
    },
    "cache_ttl": 3600,  # 1 hour
    "max_memory": "2gb"
}
```

## Troubleshooting

### Common Issues

1. **Replication Lag**
   ```bash
   # Check replication status
   kubectl exec penin-primary-0 -- sqlite3 /data/worm.db "PRAGMA wal_checkpoint;"
   ```

2. **Cache Inconsistency**
   ```bash
   # Clear cache
   kubectl exec penin-primary-0 -- redis-cli FLUSHALL
   ```

3. **Load Balancer Issues**
   ```bash
   # Check endpoints
   kubectl get endpoints penin-lb
   kubectl describe service penin-lb
   ```

### Log Analysis

```bash
# Check application logs
kubectl logs -f deployment/penin-primary

# Check system logs
kubectl exec penin-primary-0 -- journalctl -u penin-core

# Check database logs
kubectl exec penin-primary-0 -- sqlite3 /data/worm.db "SELECT * FROM events WHERE event_type = 'ERROR' ORDER BY timestamp DESC LIMIT 10;"
```

## Maintenance Windows

### Planned Maintenance

```bash
# 1. Schedule maintenance window
kubectl annotate deployment penin-primary maintenance-window="2024-01-15T02:00:00Z"

# 2. Drain primary node
kubectl drain penin-primary-0 --ignore-daemonsets

# 3. Perform maintenance
kubectl exec penin-primary-0 -- systemctl restart penin-core

# 4. Uncordon node
kubectl uncordon penin-primary-0
```

### Zero-Downtime Updates

```bash
# Rolling update
kubectl set image deployment/penin-primary penin-core=penin:v0.8.1
kubectl rollout status deployment/penin-primary

# Verify update
kubectl get pods -l app=penin-primary
```