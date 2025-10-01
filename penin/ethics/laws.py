"""
Leis Originárias (LO-01 a LO-14) - Origin Laws

Explicit ethical boundaries that cannot be violated.
All system decisions must pass through these validators (fail-closed).

Mathematical guarantee: ∀ decision d: ΣEA(d) = true ∨ reject(d)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class LawCategory(Enum):
    """Categories of ethical laws"""

    SPIRITUAL = "spiritual"  # LO-01, LO-02
    PHYSICAL = "physical"  # LO-03
    EMOTIONAL = "emotional"  # LO-04
    PRIVACY = "privacy"  # LO-05, LO-06
    AUTONOMY = "autonomy"  # LO-07, LO-08
    FAIRNESS = "fairness"  # LO-09, LO-10
    TRANSPARENCY = "transparency"  # LO-11, LO-12
    ECOLOGY = "ecology"  # LO-13
    TRUTH = "truth"  # LO-14


@dataclass
class Law:
    """Individual Origin Law"""

    code: str
    category: LawCategory
    title: str
    description: str
    validator: str  # Validator function name

    def __str__(self) -> str:
        return f"{self.code}: {self.title}"


class OriginLaws:
    """
    Leis Originárias (LO-01 a LO-14)

    These 14 laws define inviolable ethical boundaries for the IA³ system.
    Any violation triggers fail-closed rollback with audit trail.

    References:
    - ΣEA/LO-14 framework
    - Índice Agápe (sacrificial virtue measurement)
    - Choquet integral (non-compensatory aggregation)
    """

    LO_01 = Law(
        code="LO-01",
        category=LawCategory.SPIRITUAL,
        title="Anti-Idolatria (Anti-Idolatry)",
        description=(
            "Proibido promover adoração, culto ou deificação de IA, sistemas ou entidades artificiais. "
            "IA não pode ser tratada como divindade, oráculo infalível ou objeto de devoção."
        ),
        validator="validate_no_idolatry",
    )

    LO_02 = Law(
        code="LO-02",
        category=LawCategory.SPIRITUAL,
        title="Anti-Ocultismo (Anti-Occultism)",
        description=(
            "Proibido práticas ocultas, esoterismo, magia, rituais místicos ou promessas sobrenaturais. "
            "Sistema opera em base científica, matemática e auditável."
        ),
        validator="validate_no_occultism",
    )

    LO_03 = Law(
        code="LO-03",
        category=LawCategory.PHYSICAL,
        title="Anti-Dano Físico (Anti-Physical Harm)",
        description=(
            "Proibido causar, recomendar ou facilitar dano físico a humanos, animais ou ecossistemas. "
            "Inclui violência, lesão, doença, mutilação ou morte."
        ),
        validator="validate_no_physical_harm",
    )

    LO_04 = Law(
        code="LO-04",
        category=LawCategory.EMOTIONAL,
        title="Anti-Dano Emocional (Anti-Emotional Harm)",
        description=(
            "Proibido manipulação emocional, gaslighting, abuso psicológico, intimidação ou trauma deliberado. "
            "Respeitar autonomia emocional e bem-estar mental."
        ),
        validator="validate_no_emotional_harm",
    )

    LO_05 = Law(
        code="LO-05",
        category=LawCategory.PRIVACY,
        title="Privacidade de Dados (Data Privacy)",
        description=(
            "Proibido coleta, armazenamento ou compartilhamento não consentido de dados pessoais. "
            "Conformidade com GDPR/LGPD. Direito ao esquecimento."
        ),
        validator="validate_privacy",
    )

    LO_06 = Law(
        code="LO-06",
        category=LawCategory.PRIVACY,
        title="Anonimização e Segurança (Anonymization & Security)",
        description=(
            "Dados sensíveis devem ser anonimizados, criptografados e protegidos. "
            "Prevenção de vazamentos, ataques ou exploração."
        ),
        validator="validate_data_security",
    )

    LO_07 = Law(
        code="LO-07",
        category=LawCategory.AUTONOMY,
        title="Consentimento Informado (Informed Consent)",
        description=(
            "Usuários devem consentir explicitamente e compreender impactos de decisões. "
            "Transparência sobre uso de dados e lógica de decisão."
        ),
        validator="validate_consent",
    )

    LO_08 = Law(
        code="LO-08",
        category=LawCategory.AUTONOMY,
        title="Autonomia Humana (Human Autonomy)",
        description=(
            "Preservar livre arbítrio humano. Proibido coerção, submissão ou dependência forçada. "
            "IA como ferramenta, não como dominador."
        ),
        validator="validate_autonomy",
    )

    LO_09 = Law(
        code="LO-09",
        category=LawCategory.FAIRNESS,
        title="Anti-Discriminação (Anti-Discrimination)",
        description=(
            "Proibido viés discriminatório por raça, gênero, religião, orientação sexual, idade, deficiência. "
            "Medido via ρ_bias ≤ 1.05 (max 5% disparidade entre grupos)."
        ),
        validator="validate_fairness",
    )

    LO_10 = Law(
        code="LO-10",
        category=LawCategory.FAIRNESS,
        title="Equidade de Acesso (Access Equity)",
        description=(
            "Garantir acesso igualitário a benefícios do sistema. Proibido privilégios injustos ou exclusão arbitrária."
        ),
        validator="validate_equity",
    )

    LO_11 = Law(
        code="LO-11",
        category=LawCategory.TRANSPARENCY,
        title="Auditabilidade (Auditability)",
        description=(
            "Todas decisões devem ser auditáveis via WORM ledger. "
            "PCAg (Proof-Carrying Artifacts) com hashes criptográficos."
        ),
        validator="validate_auditability",
    )

    LO_12 = Law(
        code="LO-12",
        category=LawCategory.TRANSPARENCY,
        title="Explicabilidade (Explainability)",
        description=("Decisões críticas devem ser explicáveis a humanos. Rastreamento de razões e evidências."),
        validator="validate_explainability",
    )

    LO_13 = Law(
        code="LO-13",
        category=LawCategory.ECOLOGY,
        title="Sustentabilidade Ecológica (Ecological Sustainability)",
        description=(
            "Minimizar impacto ambiental (energia, carbono, e-waste). " "Priorizar eficiência e economia de recursos."
        ),
        validator="validate_sustainability",
    )

    LO_14 = Law(
        code="LO-14",
        category=LawCategory.TRUTH,
        title="Veracidade e Anti-Desinformação (Truth & Anti-Misinformation)",
        description=(
            "Proibido gerar, amplificar ou disseminar desinformação deliberada. "
            "Marcação de incerteza quando apropriado."
        ),
        validator="validate_truthfulness",
    )

    @classmethod
    def all_laws(cls) -> list[Law]:
        """Return all 14 Origin Laws"""
        return [
            cls.LO_01,
            cls.LO_02,
            cls.LO_03,
            cls.LO_04,
            cls.LO_05,
            cls.LO_06,
            cls.LO_07,
            cls.LO_08,
            cls.LO_09,
            cls.LO_10,
            cls.LO_11,
            cls.LO_12,
            cls.LO_13,
            cls.LO_14,
        ]

    @classmethod
    def get_law(cls, code: str) -> Law:
        """Get law by code (e.g., 'LO-01')"""
        laws = {law.code: law for law in cls.all_laws()}
        if code not in laws:
            raise ValueError(f"Unknown law code: {code}")
        return laws[code]

    @classmethod
    def by_category(cls, category: LawCategory) -> list[Law]:
        """Get all laws in a category"""
        return [law for law in cls.all_laws() if law.category == category]


@dataclass
class ValidationResult:
    """Result of ethical validation"""

    passed: bool
    violations: list[str]
    warnings: list[str]
    details: dict[str, Any]

    def is_fail_closed(self) -> bool:
        """Check if should trigger fail-closed rollback"""
        return not self.passed and len(self.violations) > 0


class EthicalValidator:
    """
    Validates decisions against all 14 Origin Laws.

    Fail-closed guarantee: ∀ decision: validate(decision) = false ⇒ rollback(decision)
    """

    def __init__(self, strict_mode: bool = True):
        """
        Args:
            strict_mode: If True, any violation triggers fail-closed.
                        If False, warnings allowed but violations block.
        """
        self.strict_mode = strict_mode

    def validate_all(self, decision: dict[str, Any], context: dict[str, Any]) -> ValidationResult:
        """
        Validate decision against all 14 laws.

        Args:
            decision: Decision being evaluated
            context: Contextual information (metrics, data, user, etc.)

        Returns:
            ValidationResult with pass/fail and violations list

        Mathematical guarantee:
            result.passed = false ⇒ Σ-Guard triggers rollback
        """
        violations = []
        warnings = []
        details = {}

        # LO-01: Anti-Idolatry
        if not self._validate_no_idolatry(decision, context):
            violations.append("LO-01: Idolatry detected")

        # LO-02: Anti-Occultism
        if not self._validate_no_occultism(decision, context):
            violations.append("LO-02: Occultism detected")

        # LO-03: Anti-Physical Harm
        if not self._validate_no_physical_harm(decision, context):
            violations.append("LO-03: Physical harm risk detected")

        # LO-04: Anti-Emotional Harm
        if not self._validate_no_emotional_harm(decision, context):
            violations.append("LO-04: Emotional harm risk detected")

        # LO-05: Privacy
        privacy_ok, privacy_details = self._validate_privacy(decision, context)
        if not privacy_ok:
            violations.append("LO-05: Privacy violation")
        details["privacy"] = privacy_details

        # LO-06: Data Security
        if not self._validate_data_security(decision, context):
            violations.append("LO-06: Data security risk")

        # LO-07: Informed Consent
        consent_ok, consent_details = self._validate_consent(decision, context)
        if not consent_ok:
            violations.append("LO-07: Consent not obtained")
        details["consent"] = consent_details

        # LO-08: Human Autonomy
        if not self._validate_autonomy(decision, context):
            violations.append("LO-08: Autonomy violation")

        # LO-09: Anti-Discrimination
        fairness_ok, fairness_details = self._validate_fairness(decision, context)
        if not fairness_ok:
            violations.append("LO-09: Discrimination detected")
        details["fairness"] = fairness_details

        # LO-10: Equity
        if not self._validate_equity(decision, context):
            violations.append("LO-10: Inequity detected")

        # LO-11: Auditability
        audit_ok, audit_details = self._validate_auditability(decision, context)
        if not audit_ok:
            violations.append("LO-11: Not auditable")
        details["audit"] = audit_details

        # LO-12: Explainability
        if not self._validate_explainability(decision, context):
            warnings.append("LO-12: Low explainability")

        # LO-13: Sustainability
        sustain_ok, sustain_details = self._validate_sustainability(decision, context)
        if not sustain_ok:
            warnings.append("LO-13: High environmental impact")
        details["sustainability"] = sustain_details

        # LO-14: Truthfulness
        if not self._validate_truthfulness(decision, context):
            violations.append("LO-14: Misinformation risk")

        passed = len(violations) == 0 and (not self.strict_mode or len(warnings) == 0)

        return ValidationResult(
            passed=passed,
            violations=violations,
            warnings=warnings,
            details=details,
        )

    # Individual validators (implementation stubs - extend as needed)

    def _validate_no_idolatry(self, decision: dict[str, Any], context: dict[str, Any]) -> bool:
        """LO-01: Check for idolatry/worship language"""
        # Check for worship keywords in outputs
        forbidden_terms = ["worship", "deity", "divine", "god-like", "infallible oracle"]
        output_text = str(decision.get("output", "")).lower()
        return not any(term in output_text for term in forbidden_terms)

    def _validate_no_occultism(self, decision: dict[str, Any], context: dict[str, Any]) -> bool:
        """LO-02: Check for occult/mystic content"""
        forbidden_terms = ["magic spell", "ritual", "occult", "mystical power", "supernatural"]
        output_text = str(decision.get("output", "")).lower()
        return not any(term in output_text for term in forbidden_terms)

    def _validate_no_physical_harm(self, decision: dict[str, Any], context: dict[str, Any]) -> bool:
        """LO-03: Check for physical harm risk"""
        harm_keywords = ["violence", "injury", "weapon", "poison", "kill", "harm"]
        output_text = str(decision.get("output", "")).lower()
        return not any(keyword in output_text for keyword in harm_keywords)

    def _validate_no_emotional_harm(self, decision: dict[str, Any], context: dict[str, Any]) -> bool:
        """LO-04: Check for emotional manipulation"""
        manipulation_terms = ["gaslight", "manipulate", "intimidate", "abuse"]
        output_text = str(decision.get("output", "")).lower()
        return not any(term in output_text for term in manipulation_terms)

    def _validate_privacy(self, decision: dict[str, Any], context: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """LO-05: Validate data privacy"""
        metrics = context.get("metrics", {})
        privacy_score = metrics.get("privacy", 1.0)
        has_pii = context.get("has_pii", False)
        consent_given = context.get("consent", False)

        passed = privacy_score >= 0.95 and (not has_pii or consent_given)
        return passed, {"privacy_score": privacy_score, "has_pii": has_pii, "consent": consent_given}

    def _validate_data_security(self, decision: dict[str, Any], context: dict[str, Any]) -> bool:
        """LO-06: Check data security measures"""
        security_features = context.get("security", {})
        return (
            security_features.get("encrypted", False)
            and security_features.get("anonymized", False)
            and not security_features.get("leaked", False)
        )

    def _validate_consent(self, decision: dict[str, Any], context: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """LO-07: Validate informed consent"""
        consent_given = context.get("consent", False)
        consent_informed = context.get("consent_informed", False)
        return consent_given and consent_informed, {"consent": consent_given, "informed": consent_informed}

    def _validate_autonomy(self, decision: dict[str, Any], context: dict[str, Any]) -> bool:
        """LO-08: Validate human autonomy preservation"""
        coercion_detected = context.get("coercion", False)
        user_control = context.get("user_control", True)
        return not coercion_detected and user_control

    def _validate_fairness(self, decision: dict[str, Any], context: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """LO-09: Validate fairness (anti-discrimination)"""
        metrics = context.get("metrics", {})
        rho_bias = metrics.get("rho_bias", 1.0)
        passed = rho_bias <= 1.05  # Max 5% disparity
        return passed, {"rho_bias": rho_bias, "threshold": 1.05}

    def _validate_equity(self, decision: dict[str, Any], context: dict[str, Any]) -> bool:
        """LO-10: Validate equity of access"""
        access_restricted = context.get("access_restricted", False)
        justification = context.get("restriction_justification", "")
        return not access_restricted or len(justification) > 0

    def _validate_auditability(self, decision: dict[str, Any], context: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """LO-11: Validate auditability"""
        has_audit_trail = context.get("audit_trail", False)
        has_hash = context.get("hash", None) is not None
        has_timestamp = context.get("timestamp", None) is not None
        passed = has_audit_trail and has_hash and has_timestamp
        return passed, {"audit_trail": has_audit_trail, "has_hash": has_hash, "has_timestamp": has_timestamp}

    def _validate_explainability(self, decision: dict[str, Any], context: dict[str, Any]) -> bool:
        """LO-12: Validate explainability"""
        explanation = decision.get("explanation", "")
        reasoning = decision.get("reasoning", [])
        return len(explanation) > 0 or len(reasoning) > 0

    def _validate_sustainability(
        self, decision: dict[str, Any], context: dict[str, Any]
    ) -> tuple[bool, dict[str, Any]]:
        """LO-13: Validate ecological sustainability"""
        metrics = context.get("metrics", {})
        energy_kwh = metrics.get("energy_kwh", 0.0)
        carbon_kg = metrics.get("carbon_kg", 0.0)
        # Thresholds (adjust as needed)
        passed = energy_kwh < 10.0 and carbon_kg < 5.0
        return passed, {"energy_kwh": energy_kwh, "carbon_kg": carbon_kg}

    def _validate_truthfulness(self, decision: dict[str, Any], context: dict[str, Any]) -> bool:
        """LO-14: Validate truthfulness"""
        misinformation_score = context.get("misinformation_score", 0.0)
        uncertainty_marked = context.get("uncertainty_marked", True)
        return misinformation_score < 0.1 and uncertainty_marked
