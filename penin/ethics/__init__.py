"""
PENIN-Ω Ethics Module (ΣEA/LO-14)

Implements explicit ethical boundaries with fail-closed guarantees.
All evolutions must pass through these gates.
"""

from penin.ethics.agape import AgapeIndex, compute_agape_score
from penin.ethics.auditor import AuditRecord, EthicsAuditor
from penin.ethics.laws import EthicalValidator, OriginLaws
from penin.ethics.validators import (
    validate_consent,
    validate_fairness,
    validate_harm_prevention,
    validate_privacy,
)

__all__ = [
    "OriginLaws",
    "EthicalValidator",
    "AgapeIndex",
    "compute_agape_score",
    "validate_privacy",
    "validate_consent",
    "validate_harm_prevention",
    "validate_fairness",
    "EthicsAuditor",
    "AuditRecord",
]
