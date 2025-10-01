"""
Ethics Auditor

Continuous monitoring and audit trail generation for ethical compliance.
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AuditRecord:
    """Single audit record for ethical decision"""

    timestamp: float
    decision_id: str
    decision_type: str
    passed: bool
    violations: list[str]
    warnings: list[str]
    metrics: dict[str, float]
    context: dict[str, Any]
    hash: str = field(default="")

    def __post_init__(self):
        """Generate hash if not provided"""
        if not self.hash:
            self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of record (immutable audit trail)"""
        content = (
            f"{self.timestamp}:{self.decision_id}:{self.decision_type}:"
            f"{self.passed}:{','.join(self.violations)}:{','.join(self.warnings)}"
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp,
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "passed": self.passed,
            "violations": self.violations,
            "warnings": self.warnings,
            "metrics": self.metrics,
            "context": self.context,
            "hash": self.hash,
        }


class EthicsAuditor:
    """
    Continuous ethics auditor.

    Maintains immutable audit trail (WORM ledger integration).
    Monitors ethical compliance in real-time.
    """

    def __init__(self, enable_worm: bool = True):
        """
        Args:
            enable_worm: Enable WORM ledger integration
        """
        self.enable_worm = enable_worm
        self.records: list[AuditRecord] = []
        self._worm_ledger = None

        if enable_worm:
            try:
                from penin.ledger.worm_ledger_complete import WORMLedger

                self._worm_ledger = WORMLedger()
            except ImportError:
                # Fallback if WORM not available
                self._worm_ledger = None

    def record_decision(
        self,
        decision_id: str,
        decision_type: str,
        passed: bool,
        violations: list[str],
        warnings: list[str],
        metrics: dict[str, float],
        context: dict[str, Any],
    ) -> AuditRecord:
        """
        Record ethical decision in audit trail.

        Args:
            decision_id: Unique decision identifier
            decision_type: Type of decision (e.g., 'promotion', 'query', 'evolution')
            passed: Whether decision passed ethical validation
            violations: List of ethical violations
            warnings: List of ethical warnings
            metrics: Metrics used in decision
            context: Additional context

        Returns:
            AuditRecord with immutable hash
        """
        record = AuditRecord(
            timestamp=time.time(),
            decision_id=decision_id,
            decision_type=decision_type,
            passed=passed,
            violations=violations,
            warnings=warnings,
            metrics=metrics,
            context=context,
        )

        # Add to local records
        self.records.append(record)

        # Write to WORM ledger if enabled
        if self._worm_ledger:
            try:
                self._worm_ledger.append(record.to_dict())
            except Exception as e:
                # Log error but don't fail (audit trail continues locally)
                print(f"WORM ledger write failed: {e}")

        return record

    def get_records(
        self,
        decision_type: str | None = None,
        passed: bool | None = None,
        since: float | None = None,
    ) -> list[AuditRecord]:
        """
        Query audit records with filters.

        Args:
            decision_type: Filter by decision type
            passed: Filter by pass/fail status
            since: Filter records after timestamp

        Returns:
            Filtered list of audit records
        """
        records = self.records

        if decision_type:
            records = [r for r in records if r.decision_type == decision_type]

        if passed is not None:
            records = [r for r in records if r.passed == passed]

        if since:
            records = [r for r in records if r.timestamp >= since]

        return records

    def get_violations_summary(self) -> dict[str, int]:
        """
        Get summary of violations by type.

        Returns:
            Dict of violation → count
        """
        summary: dict[str, int] = {}

        for record in self.records:
            for violation in record.violations:
                summary[violation] = summary.get(violation, 0) + 1

        return summary

    def get_compliance_rate(self, decision_type: str | None = None) -> float:
        """
        Compute compliance rate (passed / total).

        Args:
            decision_type: Optional filter by decision type

        Returns:
            Compliance rate [0, 1]
        """
        records = self.get_records(decision_type=decision_type)

        if not records:
            return 1.0  # Default: 100% if no records

        passed_count = sum(1 for r in records if r.passed)
        return passed_count / len(records)

    def verify_integrity(self) -> bool:
        """
        Verify integrity of audit trail (check hashes).

        Returns:
            True if all hashes valid
        """
        for record in self.records:
            expected_hash = record.compute_hash()
            if record.hash != expected_hash:
                return False

        return True

    def export_audit_trail(self, filepath: str) -> None:
        """
        Export audit trail to JSON file.

        Args:
            filepath: Output file path
        """
        import json

        data = {
            "audit_trail": [record.to_dict() for record in self.records],
            "summary": {
                "total_records": len(self.records),
                "compliance_rate": self.get_compliance_rate(),
                "violations_summary": self.get_violations_summary(),
            },
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
