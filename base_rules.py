"""
MediMind 6.0 - shared building blocks for the medical rules engine.

Every finding produced by the rules engine is:

  * derived from a value ACTUALLY present in the uploaded report
  * attributed to a source in the Medical Evidence Library
  * worded conservatively ("requires professional review" - never a
    diagnosis, never treatment advice)
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------
# Conservative risk-flag vocabulary (11) - NOT diagnoses
# ---------------------------------------------------------------------

FLAG_NORMAL_INFORMATION = "NORMAL_INFORMATION"
FLAG_REVIEW = "REVIEW"
FLAG_IMPORTANT_REVIEW = "IMPORTANT_REVIEW"
FLAG_URGENT = "URGENT"

# Severity strings used inside findings
SEVERITY_NORMAL = "normal"
SEVERITY_INFORMATION = "information"
SEVERITY_REVIEW = "review"
SEVERITY_IMPORTANT_REVIEW = "important_review"
SEVERITY_URGENT = "urgent"

SEVERITY_ORDER = {
    SEVERITY_NORMAL: 0,
    SEVERITY_INFORMATION: 0,
    SEVERITY_REVIEW: 1,
    SEVERITY_IMPORTANT_REVIEW: 2,
    SEVERITY_URGENT: 3,
}


def highest_severity(severities: list[str]) -> str:
    """Return the most severe severity from a list (normal when empty)."""
    worst = SEVERITY_NORMAL
    for severity in severities:
        if SEVERITY_ORDER.get(severity, 0) > SEVERITY_ORDER.get(worst, 0):
            worst = severity
    return worst


# ---------------------------------------------------------------------
# Safe wording (medical-safety tests grep for these)
# ---------------------------------------------------------------------

DISCLAIMER_GENERAL = (
    "This information is generated from the uploaded report and general, "
    "source-attributed reference ranges. It is not a medical diagnosis. "
    "Please discuss it with a qualified healthcare professional."
)

EMERGENCY_WORDING = (
    "This information may require urgent medical attention. Please contact "
    "a qualified healthcare professional or local emergency service."
)

# Recommended actions are discussion prompts, never treatment instructions
ACTION_DISCUSS = "Discuss this finding with your healthcare professional."
ACTION_TIMELY = (
    "Share this report with a healthcare professional promptly and discuss "
    "the appropriate next steps."
)
ACTION_URGENT = (
    "This information may require urgent medical attention. Please contact "
    "a qualified healthcare professional or local emergency service."
)

NOT_AVAILABLE_TEXT = "Not available in the uploaded report."

FORBIDDEN_DIAGNOSTIC_PHRASES = (
    "you definitely have",
    "the report proves you have",
    "you have heart disease",
    "you should start",
    "you should stop",
    "start taking",
    "stop taking",
)


@dataclass
class Finding:
    """One rule-engine observation about an extracted report value."""

    finding: str
    reason: str
    severity: str  # SEVERITY_* constant
    source: str  # evidence source_key
    recommended_action: str
    parameter: str | None = None
    confidence: float | None = None  # extraction/interpretation confidence

    def to_dict(self) -> dict:
        return {
            "finding": self.finding,
            "reason": self.reason,
            "severity": self.severity,
            "source": self.source,
            "recommended_action": self.recommended_action,
            "parameter": self.parameter,
            "confidence": self.confidence,
        }


@dataclass
class SuggestionSet:
    """The seven specialized decision-support sections (spec section 8)."""

    key_findings: list[str] = field(default_factory=list)
    items_for_professional_review: list[str] = field(default_factory=list)
    follow_up_discussion: list[str] = field(default_factory=list)
    monitoring_suggestions: list[str] = field(default_factory=list)
    questions_to_ask: list[str] = field(default_factory=list)
    comparison_notes: list[str] = field(default_factory=list)
    emergency_warnings: list[str] = field(default_factory=list)
    # Comparative history used to build comparison_notes (never fabricated)
    comparison: dict | None = None

    def to_dict(self) -> dict:
        return {
            "key_findings": self.key_findings,
            "items_for_professional_review": self.items_for_professional_review,
            "follow_up_discussion": self.follow_up_discussion,
            "monitoring_suggestions": self.monitoring_suggestions,
            "questions_to_ask": self.questions_to_ask,
            "comparison_notes": self.comparison_notes,
            "emergency_warnings": self.emergency_warnings,
            "comparison": self.comparison,
        }
