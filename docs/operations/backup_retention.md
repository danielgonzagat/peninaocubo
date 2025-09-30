# Backup and Retention Policies

## Overview

This document outlines the backup and data retention policies for PENIN-Ω system, ensuring data integrity, compliance, and disaster recovery capabilities.

## Data Classification

### Critical Data (Retention: 7 years)
- **WORM Ledger**: All evolution events and audit trails
- **Ethics Metrics**: ECE, bias ratios, fairness scores
- **Policy Decisions**: Σ-Guard and IR→IC evaluations
- **Security Events**: Authentication, authorization logs

### Important Data (Retention: 3 years)
- **Performance Metrics**: Latency, throughput, success rates
- **Cost Data**: Budget tracking, provider costs
- **Evolution History**: Mutation strategies, fitness scores
- **Configuration Changes**: System configuration updates

### Operational Data (Retention: 1 year)
- **Application Logs**: Debug, info, warning logs
- **Cache Data**: L1/L2 cache contents
- **Temporary Files**: Intermediate processing data

### Transient Data (Retention: 30 days)
- **Session Data**: User sessions, temporary tokens
- **Cache Metadata**: Cache hit/miss statistics
- **Debug Traces**: Detailed execution traces

## Backup Strategy

### WORM Ledger Backup

#### Daily Incremental Backup
```bash
#!/bin/bash
# Daily WORM backup script

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/worm"
WORM_DB="/data/worm.db"

# Create backup directory
mkdir -p ${BACKUP_DIR}/${DATE}

# Create incremental backup
sqlite3 ${WORM_DB} ".backup ${BACKUP_DIR}/${DATE}/worm_incremental.db"

# Create checksum
sha256sum ${BACKUP_DIR}/${DATE}/worm_incremental.db > ${BACKUP_DIR}/${DATE}/worm_incremental.db.sha256

# Upload to S3
aws s3 cp ${BACKUP_DIR}/${DATE}/worm_incremental.db s3://penin-backups/worm/daily/
aws s3 cp ${BACKUP_DIR}/${DATE}/worm_incremental.db.sha256 s3://penin-backups/worm/daily/

# Cleanup local backup after 7 days
find ${BACKUP_DIR} -name "worm_incremental.db" -mtime +7 -delete
```

#### Weekly Full Backup
```bash
#!/bin/bash
# Weekly full WORM backup

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/worm"
WORM_DB="/data/worm.db"

# Create full backup
sqlite3 ${WORM_DB} ".backup ${BACKUP_DIR}/worm_full_${DATE}.db"

# Compress backup
gzip ${BACKUP_DIR}/worm_full_${DATE}.db

# Create checksum
sha256sum ${BACKUP_DIR}/worm_full_${DATE}.db.gz > ${BACKUP_DIR}/worm_full_${DATE}.db.gz.sha256

# Upload to S3 with lifecycle policy
aws s3 cp ${BACKUP_DIR}/worm_full_${DATE}.db.gz s3://penin-backups/worm/weekly/
aws s3 cp ${BACKUP_DIR}/worm_full_${DATE}.db.gz.sha256 s3://penin-backups/worm/weekly/

# Set lifecycle policy (move to IA after 30 days, Glacier after 90 days)
aws s3api put-bucket-lifecycle-configuration --bucket penin-backups --lifecycle-configuration '{
  "Rules": [
    {
      "ID": "WormBackupLifecycle",
      "Status": "Enabled",
      "Filter": {"Prefix": "worm/weekly/"},
      "Transitions": [
        {"Days": 30, "StorageClass": "STANDARD_IA"},
        {"Days": 90, "StorageClass": "GLACIER"}
      ]
    }
  ]
}'
```

### Cache Backup

#### Redis Persistence
```bash
#!/bin/bash
# Redis backup script

REDIS_HOST="redis-cluster"
REDIS_PORT="6379"
BACKUP_DIR="/backup/redis"
DATE=$(date +%Y%m%d)

# Create Redis dump
redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} --rdb ${BACKUP_DIR}/redis_${DATE}.rdb

# Compress dump
gzip ${BACKUP_DIR}/redis_${DATE}.rdb

# Upload to S3
aws s3 cp ${BACKUP_DIR}/redis_${DATE}.rdb.gz s3://penin-backups/redis/

# Cleanup local backup after 3 days
find ${BACKUP_DIR} -name "redis_*.rdb.gz" -mtime +3 -delete
```

### Configuration Backup

#### System Configuration
```bash
#!/bin/bash
# Configuration backup script

CONFIG_DIR="/etc/penin"
BACKUP_DIR="/backup/config"
DATE=$(date +%Y%m%d)

# Backup configuration files
tar -czf ${BACKUP_DIR}/penin_config_${DATE}.tar.gz ${CONFIG_DIR}

# Upload to S3
aws s3 cp ${BACKUP_DIR}/penin_config_${DATE}.tar.gz s3://penin-backups/config/

# Cleanup local backup after 30 days
find ${BACKUP_DIR} -name "penin_config_*.tar.gz" -mtime +30 -delete
```

## Retention Policies

### Automated Retention

#### WORM Ledger Retention
```python
class WormRetentionManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.retention_policies = {
            "critical": 7 * 365 * 24 * 3600,  # 7 years in seconds
            "important": 3 * 365 * 24 * 3600,  # 3 years in seconds
            "operational": 365 * 24 * 3600,  # 1 year in seconds
            "transient": 30 * 24 * 3600  # 30 days in seconds
        }
    
    def cleanup_expired_data(self):
        """Remove expired data based on retention policies."""
        cutoff_times = {
            category: time.time() - retention
            for category, retention in self.retention_policies.items()
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clean up transient data
            cursor.execute("""
                DELETE FROM events 
                WHERE event_type IN ('session_data', 'cache_metadata', 'debug_trace')
                AND timestamp < ?
            """, (cutoff_times["transient"],))
            
            # Clean up operational data
            cursor.execute("""
                DELETE FROM events 
                WHERE event_type IN ('app_log', 'cache_data', 'temp_file')
                AND timestamp < ?
            """, (cutoff_times["operational"],))
            
            conn.commit()
    
    def archive_old_data(self):
        """Archive old data to cold storage."""
        archive_cutoff = time.time() - (2 * 365 * 24 * 3600)  # 2 years
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get old data
            cursor.execute("""
                SELECT * FROM events 
                WHERE timestamp < ?
                ORDER BY timestamp
            """, (archive_cutoff,))
            
            old_data = cursor.fetchall()
            
            if old_data:
                # Create archive file
                archive_path = f"/archive/worm_archive_{int(time.time())}.jsonl"
                with open(archive_path, 'w') as f:
                    for row in old_data:
                        f.write(json.dumps(row) + '\n')
                
                # Upload to Glacier
                self.upload_to_glacier(archive_path)
                
                # Remove from main database
                cursor.execute("DELETE FROM events WHERE timestamp < ?", (archive_cutoff,))
                conn.commit()
    
    def upload_to_glacier(self, file_path: str):
        """Upload file to AWS Glacier."""
        import boto3
        
        glacier = boto3.client('glacier')
        
        with open(file_path, 'rb') as f:
            response = glacier.upload_archive(
                vaultName='penin-archive',
                archiveDescription=f'WORM archive {os.path.basename(file_path)}',
                body=f
            )
            
        logger.info(f"Uploaded {file_path} to Glacier: {response['archiveId']}")
```

#### Log Retention
```python
class LogRetentionManager:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        self.retention_days = {
            "debug": 7,
            "info": 30,
            "warning": 90,
            "error": 365
        }
    
    def cleanup_logs(self):
        """Clean up old log files."""
        for level, days in self.retention_days.items():
            pattern = f"{self.log_dir}/*{level}*.log"
            cutoff_time = time.time() - (days * 24 * 3600)
            
            for log_file in glob.glob(pattern):
                if os.path.getmtime(log_file) < cutoff_time:
                    # Compress before deletion
                    self.compress_log(log_file)
                    os.remove(log_file)
    
    def compress_log(self, log_file: str):
        """Compress log file."""
        compressed_file = f"{log_file}.gz"
        with open(log_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
```

### Compliance Retention

#### GDPR Compliance
```python
class GDPRRetentionManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def handle_data_subject_request(self, subject_id: str, request_type: str):
        """Handle GDPR data subject requests."""
        if request_type == "access":
            return self.export_subject_data(subject_id)
        elif request_type == "deletion":
            return self.delete_subject_data(subject_id)
        elif request_type == "portability":
            return self.export_portable_data(subject_id)
    
    def export_subject_data(self, subject_id: str):
        """Export all data for a specific subject."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM events 
                WHERE user_id = ? OR content LIKE ?
                ORDER BY timestamp
            """, (subject_id, f"%{subject_id}%"))
            
            data = cursor.fetchall()
            
            # Create export file
            export_file = f"/exports/subject_{subject_id}_{int(time.time())}.json"
            with open(export_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return export_file
    
    def delete_subject_data(self, subject_id: str):
        """Delete all data for a specific subject."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Log deletion for audit
            cursor.execute("""
                INSERT INTO events (event_type, user_id, content, timestamp)
                VALUES ('gdpr_deletion', ?, ?, ?)
            """, (subject_id, f"Data deletion request for subject {subject_id}", time.time()))
            
            # Delete subject data
            cursor.execute("DELETE FROM events WHERE user_id = ?", (subject_id,))
            cursor.execute("DELETE FROM events WHERE content LIKE ?", (f"%{subject_id}%",))
            
            conn.commit()
```

## Backup Verification

### Integrity Checks

#### WORM Integrity Verification
```python
class WormIntegrityChecker:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def verify_integrity(self):
        """Verify WORM ledger integrity."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check hash chain
            cursor.execute("SELECT id, hash, prev_hash FROM events ORDER BY timestamp")
            events = cursor.fetchall()
            
            prev_hash = None
            for event_id, hash_val, stored_prev_hash in events:
                # Verify previous hash
                if prev_hash and stored_prev_hash != prev_hash:
                    raise IntegrityError(f"Hash chain broken at event {event_id}")
                
                # Calculate current hash
                cursor.execute("SELECT content FROM events WHERE id = ?", (event_id,))
                content = cursor.fetchone()[0]
                calculated_hash = hashlib.sha256(content.encode()).hexdigest()
                
                if hash_val != calculated_hash:
                    raise IntegrityError(f"Hash mismatch at event {event_id}")
                
                prev_hash = hash_val
            
            return True
    
    def verify_backup_integrity(self, backup_path: str):
        """Verify backup file integrity."""
        # Check file exists and is readable
        if not os.path.exists(backup_path):
            raise IntegrityError(f"Backup file {backup_path} does not exist")
        
        # Check SQLite integrity
        result = subprocess.run([
            "sqlite3", backup_path, "PRAGMA integrity_check;"
        ], capture_output=True, text=True)
        
        if result.returncode != 0 or "ok" not in result.stdout:
            raise IntegrityError(f"SQLite integrity check failed: {result.stdout}")
        
        return True
```

### Automated Testing

#### Backup Restoration Test
```python
class BackupRestorationTest:
    def __init__(self, test_db_path: str):
        self.test_db_path = test_db_path
    
    def test_restoration(self, backup_path: str):
        """Test backup restoration."""
        # Create test database
        test_db = f"{self.test_db_path}/test_restore.db"
        
        # Restore from backup
        shutil.copy2(backup_path, test_db)
        
        # Verify restoration
        checker = WormIntegrityChecker(test_db)
        integrity_ok = checker.verify_integrity()
        
        # Test basic operations
        with sqlite3.connect(test_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            count = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM events")
            time_range = cursor.fetchone()
        
        # Cleanup
        os.remove(test_db)
        
        return {
            "integrity_ok": integrity_ok,
            "event_count": count,
            "time_range": time_range
        }
```

## Monitoring and Alerting

### Backup Monitoring

```yaml
# Prometheus alerts for backup monitoring
groups:
- name: backup-monitoring
  rules:
  - alert: BackupFailed
    expr: backup_success == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Backup failed"
      
  - alert: BackupSizeAnomaly
    expr: abs(backup_size_bytes - backup_size_bytes offset 1d) / backup_size_bytes offset 1d > 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Backup size changed significantly"
      
  - alert: RetentionPolicyViolation
    expr: data_age_seconds > retention_policy_seconds
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "Data retention policy violation"
```

### Backup Dashboard

```json
{
  "dashboard": {
    "title": "PENIN Backup Status",
    "panels": [
      {
        "title": "Backup Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(backup_success_total[24h])"
          }
        ]
      },
      {
        "title": "Backup Size Trend",
        "type": "graph",
        "targets": [
          {
            "expr": "backup_size_bytes"
          }
        ]
      },
      {
        "title": "Data Age Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "data_age_seconds by (category)"
          }
        ]
      }
    ]
  }
}
```

## Disaster Recovery Procedures

### Full System Recovery

```bash
#!/bin/bash
# Full system recovery script

# 1. Restore WORM database
aws s3 cp s3://penin-backups/worm/weekly/worm_full_20240107.db.gz /restore/
gunzip /restore/worm_full_20240107.db.gz
sqlite3 /data/worm.db < /restore/worm_full_20240107.db

# 2. Restore Redis cache
aws s3 cp s3://penin-backups/redis/redis_20240107.rdb.gz /restore/
gunzip /restore/redis_20240107.rdb.gz
redis-cli --rdb /restore/redis_20240107.rdb

# 3. Restore configuration
aws s3 cp s3://penin-backups/config/penin_config_20240107.tar.gz /restore/
tar -xzf /restore/penin_config_20240107.tar.gz -C /

# 4. Verify restoration
python -c "
from penin.omega.ledger import WORMLedger
ledger = WORMLedger('/data/worm.db')
print(f'Records restored: {ledger.count_records()}')
print(f'Integrity check: {ledger.verify_integrity()}')
"

# 5. Start services
systemctl start penin-core
systemctl start redis
systemctl start prometheus
```

### Partial Recovery

```bash
#!/bin/bash
# Partial recovery for specific data types

DATA_TYPE=$1
BACKUP_DATE=$2

case $DATA_TYPE in
  "worm")
    aws s3 cp s3://penin-backups/worm/daily/worm_incremental_${BACKUP_DATE}.db /restore/
    sqlite3 /data/worm.db < /restore/worm_incremental_${BACKUP_DATE}.db
    ;;
  "cache")
    aws s3 cp s3://penin-backups/redis/redis_${BACKUP_DATE}.rdb.gz /restore/
    gunzip /restore/redis_${BACKUP_DATE}.rdb.gz
    redis-cli --rdb /restore/redis_${BACKUP_DATE}.rdb
    ;;
  "config")
    aws s3 cp s3://penin-backups/config/penin_config_${BACKUP_DATE}.tar.gz /restore/
    tar -xzf /restore/penin_config_${BACKUP_DATE}.tar.gz -C /
    ;;
esac
```