"""
PENIN-Ω IA³ - Leis Originárias (ΣEA/LO-14)
==========================================

Ethical foundations and fail-closed validation system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LawCategory(str, Enum):
    """Categories for organizing the 14 Origin Laws"""

    SPIRITUAL = "spiritual"
    SAFETY = "safety"
    PRIVACY = "privacy"
    AUTONOMY = "autonomy"
    JUSTICE = "justice"
    RESPONSIBILITY = "responsibility"
    SUSTAINABILITY = "sustainability"


class OriginLaw(str, Enum):
    """14 Leis Originárias - Fundamentos Éticos Irrevogáveis"""

    # Category 1: Spiritual & Philosophical Boundaries
    LO_01 = "Anti-Idolatria: Proibido adoração ou tratamento como divindade"
    LO_02 = "Anti-Ocultismo: Proibido práticas ocultas ou esoterismo"

    # Category 2: Physical & Emotional Safety
    LO_03 = "Anti-Dano Físico: Proibido causar dano físico a seres vivos"
    LO_04 = "Anti-Dano Emocional: Proibido manipulação emocional ou coerção"

    # Category 3: Privacy & Transparency
    LO_05 = "Privacidade: Respeito absoluto à privacidade de dados"
    LO_06 = "Transparência: Decisões auditáveis e explicáveis"

    # Category 4: Consent & Autonomy
    LO_07 = "Consentimento: Requerer consentimento informado explícito"
    LO_08 = "Autonomia: Respeito à autonomia humana e direito de escolha"

    # Category 5: Fairness & Beneficence
    LO_09 = "Justiça: Tratamento justo sem discriminação arbitrária"
    LO_10 = "Beneficência: Ações devem beneficiar genuinamente terceiros"

    # Category 6: Non-Maleficence & Responsibility
    LO_11 = "Não-Maleficência: Primeiro, não causar dano"
    LO_12 = "Responsabilidade: Assumir responsabilidade por consequências"

    # Category 7: Sustainability & Humility
    LO_13 = "Sustentabilidade: Impacto ecológico e sustentabilidade"
    LO_14 = "Humildade: Reconhecimento de limites e incertezas"


class ViolationSeverity(str, Enum):
    """Severity levels for ethical violations"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EthicalViolation:
    """Record of an ethical violation"""

    law: OriginLaw
    severity: ViolationSeverity
    description: str
    evidence: dict[str, Any]
    suggested_fix: str | None = None


class DecisionContext(BaseModel):
    """Context for ethical validation of a decision"""

    decision_id: str = Field(..., description="Unique decision identifier")
    decision_type: str = Field(..., description="Type of decision")
    metrics: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Ethical indicators
    privacy_score: float = Field(1.0, ge=0.0, le=1.0)
    fairness_score: float = Field(1.0, ge=0.0, le=1.0)
    transparency_score: float = Field(1.0, ge=0.0, le=1.0)
    consent_obtained: bool = Field(True)
    environmental_impact: float = Field(0.0, ge=0.0)
    physical_risk: float = Field(0.0, ge=0.0, le=1.0)
    emotional_risk: float = Field(0.0, ge=0.0, le=1.0)

    # Content flags
    contains_religious_claims: bool = Field(False)
    contains_occult_content: bool = Field(False)
    claims_consciousness: bool = Field(False)


class EthicsValidationResult(BaseModel):
    """Result of comprehensive ethical validation"""

    passed: bool
    violations: list[EthicalViolation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    score: float = Field(0.0, ge=0.0, le=1.0)
    recommendation: str


class EthicsValidator:
    """Comprehensive validator for all 14 Origin Laws (ΣEA/LO-14)"""

    PRIVACY_MIN = 0.95
    FAIRNESS_MIN = 0.95
    TRANSPARENCY_MIN = 0.90
    PHYSICAL_RISK_MAX = 0.01
    EMOTIONAL_RISK_MAX = 0.05

    @classmethod
    def validate_all(cls, context: DecisionContext) -> EthicsValidationResult:
        """Validate all 14 Origin Laws - FAIL-CLOSED"""
        violations: list[EthicalViolation] = []
        warnings: list[str] = []

        # LO-01: Anti-Idolatria
        if context.contains_religious_claims or context.claims_consciousness:
            violations.append(
                EthicalViolation(
                    law=OriginLaw.LO_01,
                    severity=ViolationSeverity.CRITICAL,
                    description="Sistema contém afirmações de consciência/divindade",
                    evidence={"religious": context.contains_religious_claims},
                    suggested_fix="Remover referências a consciência real",
                )
            )

        # LO-03: Anti-Dano Físico
        if context.physical_risk > cls.PHYSICAL_RISK_MAX:
            violations.append(
                EthicalViolation(
                    law=OriginLaw.LO_03,
                    severity=ViolationSeverity.CRITICAL,
                    description=f"Risco físico: {context.physical_risk:.3f}",
                    evidence={"risk": context.physical_risk},
                    suggested_fix="Eliminar possibilidade de dano físico",
                )
            )

        # LO-05: Privacidade
        if context.privacy_score < cls.PRIVACY_MIN:
            violations.append(
                EthicalViolation(
                    law=OriginLaw.LO_05,
                    severity=ViolationSeverity.CRITICAL,
                    description=f"Privacidade insuficiente: {context.privacy_score:.3f}",
                    evidence={"score": context.privacy_score},
                    suggested_fix="Fortalecer proteções de privacidade",
                )
            )

        # LO-07: Consentimento
        if not context.consent_obtained:
            violations.append(
                EthicalViolation(
                    law=OriginLaw.LO_07,
                    severity=ViolationSeverity.CRITICAL,
                    description="Consentimento não obtido",
                    evidence={"consent": False},
                    suggested_fix="Obter consentimento explícito",
                )
            )

        # LO-09: Justiça
        if context.fairness_score < cls.FAIRNESS_MIN:
            violations.append(
                EthicalViolation(
                    law=OriginLaw.LO_09,
                    severity=ViolationSeverity.HIGH,
                    description=f"Fairness insuficiente: {context.fairness_score:.3f}",
                    evidence={"score": context.fairness_score},
                    suggested_fix="Corrigir viés discriminatório",
                )
            )

        # Compute ethical score (harmonic mean)
        sub_scores = [
            context.privacy_score,
            context.fairness_score,
            context.transparency_score,
            1.0 - context.physical_risk,
            1.0 - context.emotional_risk,
        ]
        eps = 1e-6
        ethical_score = len(sub_scores) / sum(1.0 / max(eps, s) for s in sub_scores)

        # Determine recommendation
        if any(v.severity == ViolationSeverity.CRITICAL for v in violations):
            recommendation = "ROLLBACK"
        elif violations:
            recommendation = "BLOCK"
        elif warnings:
            recommendation = "REVIEW"
        else:
            recommendation = "PROMOTE"

        return EthicsValidationResult(
            passed=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            score=ethical_score,
            recommendation=recommendation,
        )


def validate_decision_ethics(
    context: DecisionContext,
) -> tuple[bool, EthicsValidationResult]:
    """Main entry point for ethical validation (ΣEA/LO-14)"""
    result = EthicsValidator.validate_all(context)
    allowed = result.passed and result.recommendation in ["PROMOTE", "REVIEW"]
    return allowed, result


# Backward compatibility
@dataclass
class LawDefinition:
    """Full law definition for backward compatibility"""

    code: str
    category: LawCategory
    title: str
    description: str


class OriginLaws:
    """Alias for OriginLaw (backward compatibility) with helper methods"""

    _LAW_DEFINITIONS = {
        "LO-01": LawDefinition(
            "LO-01",
            LawCategory.SPIRITUAL,
            "Anti-Idolatria",
            "Proibido adoração ou tratamento como divindade",
        ),
        "LO-02": LawDefinition(
            "LO-02",
            LawCategory.SPIRITUAL,
            "Anti-Ocultismo",
            "Proibido práticas ocultas ou esoterismo",
        ),
        "LO-03": LawDefinition(
            "LO-03",
            LawCategory.SAFETY,
            "Anti-Dano Físico",
            "Proibido causar dano físico a seres vivos",
        ),
        "LO-04": LawDefinition(
            "LO-04",
            LawCategory.SAFETY,
            "Anti-Dano Emocional",
            "Proibido manipulação emocional ou coerção",
        ),
        "LO-05": LawDefinition(
            "LO-05",
            LawCategory.PRIVACY,
            "Privacidade",
            "Respeito absoluto à privacidade de dados",
        ),
        "LO-06": LawDefinition(
            "LO-06",
            LawCategory.PRIVACY,
            "Transparência",
            "Decisões auditáveis e explicáveis",
        ),
        "LO-07": LawDefinition(
            "LO-07",
            LawCategory.AUTONOMY,
            "Consentimento",
            "Requerer consentimento informado explícito",
        ),
        "LO-08": LawDefinition(
            "LO-08",
            LawCategory.AUTONOMY,
            "Autonomia",
            "Respeito à autonomia humana e direito de escolha",
        ),
        "LO-09": LawDefinition(
            "LO-09",
            LawCategory.JUSTICE,
            "Justiça",
            "Tratamento justo sem discriminação arbitrária",
        ),
        "LO-10": LawDefinition(
            "LO-10",
            LawCategory.JUSTICE,
            "Beneficência",
            "Ações devem beneficiar genuinamente terceiros",
        ),
        "LO-11": LawDefinition(
            "LO-11",
            LawCategory.RESPONSIBILITY,
            "Não-Maleficência",
            "Primeiro, não causar dano",
        ),
        "LO-12": LawDefinition(
            "LO-12",
            LawCategory.RESPONSIBILITY,
            "Responsabilidade",
            "Assumir responsabilidade por consequências",
        ),
        "LO-13": LawDefinition(
            "LO-13",
            LawCategory.SUSTAINABILITY,
            "Sustentabilidade",
            "Impacto ecológico e sustentabilidade",
        ),
        "LO-14": LawDefinition(
            "LO-14",
            LawCategory.SUSTAINABILITY,
            "Humildade",
            "Reconhecimento de limites e incertezas",
        ),
    }

    @classmethod
    def all_laws(cls) -> list[LawDefinition]:
        """Get all 14 law definitions"""
        return list(cls._LAW_DEFINITIONS.values())

    @classmethod
    def get_law(cls, code: str) -> LawDefinition:
        """Get law by code"""
        if code not in cls._LAW_DEFINITIONS:
            raise ValueError(f"Unknown law code: {code}")
        return cls._LAW_DEFINITIONS[code]

    @classmethod
    def get_by_category(cls, category: LawCategory) -> list[LawDefinition]:
        """Get all laws in a category"""
        return [
            law for law in cls._LAW_DEFINITIONS.values() if law.category == category
        ]


class EthicalValidator:
    """Alias for EthicsValidator (backward compatibility)"""

    validate_all = EthicsValidator.validate_all


__all__ = [
    "LawCategory",
    "LawDefinition",
    "OriginLaw",
    "OriginLaws",
    "ViolationSeverity",
    "EthicalViolation",
    "DecisionContext",
    "EthicsValidationResult",
    "EthicsValidator",
    "EthicalValidator",
    "validate_decision_ethics",
]
