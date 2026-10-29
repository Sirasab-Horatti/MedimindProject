"""
MediMind 8.5 - diabetes rules engine.

Conservative, source-attributed interpretation of extracted diabetes
report values. Structurally parallel to ``cardiac_rules.py`` (same
Finding vocabulary, same severity ladder, same "evaluate only what the
report actually contains" contract).

Every threshold is configurable and attributed to a source in the
Medical Evidence Library. Thresholds are general-adult screening
references that depend on context (age, pregnancy, assay, symptoms,
clinical history, whether the sample was truly fasting). The engine
always frames results as "requires professional review" - it NEVER
diagnoses diabetes and NEVER suggests starting, stopping or changing
medication.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from medical_rules.base_rules import (
    ACTION_DISCUSS,
    ACTION_TIMELY,
    ACTION_URGENT,
    Finding,
    FLAG_IMPORTANT_REVIEW,
    FLAG_NORMAL_INFORMATION,
    FLAG_REVIEW,
    FLAG_URGENT,
    SEVERITY_IMPORTANT_REVIEW,
    SEVERITY_INFORMATION,
    SEVERITY_NORMAL,
    SEVERITY_REVIEW,
    SEVERITY_URGENT,
    highest_severity,
)

# ---------------------------------------------------------------------
# Configurable, source-attributed thresholds (general adult screening
# references - context dependent, always framed for professional review)
# ---------------------------------------------------------------------

DIABETES_THRESHOLDS: dict = {
    "hba1c": {
        "label": "HbA1c",
        "high_urgent": 10.0, "high": 6.5, "low": 4.0,
        "unit": "%",
        "source": "ada_standards_diabetes",
    },
    "fasting_glucose": {
        "label": "Fasting glucose",
        "high_urgent": 300.0, "high": 126.0, "low_urgent": 54.0, "low": 70.0,
        "unit": "mg/dL",
        "source": "ada_standards_diabetes",
    },
    "random_glucose": {
        "label": "Random glucose",
        "high_urgent": 350.0, "high": 200.0, "low_urgent": 54.0, "low": 70.0,
        "unit": "mg/dL",
        "source": "ada_standards_diabetes",
    },
    "post_meal_glucose": {
        "label": "Post-meal glucose",
        "high_urgent": 350.0, "high": 180.0,
        "unit": "mg/dL",
        "source": "ada_standards_diabetes",
    },
    "ldl_mg_dl": {
        "label": "LDL cholesterol",
        "high_urgent": 190.0, "high": 100.0,
        "unit": "mg/dL",
        "source": "nhlbi_atp3_lipids",
    },
    "hdl_mg_dl": {
        "label": "HDL cholesterol",
        "low": 40.0,
        "unit": "mg/dL",
        "source": "nhlbi_atp3_lipids",
    },
    "total_cholesterol_mg_dl": {
        "label": "Total cholesterol",
        "high": 200.0,
        "unit": "mg/dL",
        "source": "nhlbi_atp3_lipids",
    },
    "triglycerides_mg_dl": {
        "label": "Triglycerides",
        "high": 150.0, "high_urgent": 500.0,
        "unit": "mg/dL",
        "source": "nhlbi_atp3_lipids",
    },
    "systolic_bp": {
        "label": "Systolic blood pressure",
        "high": 130.0, "high_urgent": 180.0,
        "unit": "mmHg",
        "source": "acc_aha_2017_hypertension",
    },
    "diastolic_bp": {
        "label": "Diastolic blood pressure",
        "high": 80.0, "high_urgent": 120.0,
        "unit": "mmHg",
        "source": "acc_aha_2017_hypertension",
    },
}

# Terms in the physician impression that warrant urgent-care wording
IMPRESSION_URGENT_TERMS = (
    "diabetic ketoacidosis",
    "ketoacidosis",
    "hyperosmolar",
    "critical",
    "severe",
    "emergency",
)

# Impression phrases that warrant professional review (report's own words)
IMPRESSION_REVIEW_TERMS = (
    "diabetes",
    "diabetic",
    "impaired fasting glucose",
    "impaired glucose tolerance",
    "prediabetes",
    "insulin",
    "hyperglycemia",
    "hyperglycaemia",
    "hypoglycemia",
    "hypoglycaemia",
    "retinopathy",
    "neuropathy",
    "nephropathy",
    "ketones",
)

# Explicitly-named glucose measurement types (§5: extract only what the
# report actually names; a bare "glucose" line never becomes a fasting value)
FASTING_MARKERS = (
    "fasting blood sugar", "fasting plasma glucose", "fasting glucose",
    "fbs", "fpg", "fasting",
)
RANDOM_MARKERS = ("random blood sugar", "random glucose", "rbs", "random")
POST_MEAL_MARKERS = (
    "post prandial", "postprandial", "post meal", "post-meal", "ppbs", "pp glucose", "pp",
)

URINE_GLUCOSE_MARKERS = ("urine glucose", "urinary glucose", "glucose (urine)", "urine sugar")
URINE_KETONE_MARKERS = ("urine ketones", "urinary ketones", "ketone bodies", "ketones (urine)", "ketones")
INSULIN_MARKERS = ("insulin (fasting)", "fasting insulin", "serum insulin", "insulin level", "insulin:")


def _finding(value_row: dict, label: str, severity: str, reason: str, source: str,
             action: str) -> Finding:
    return Finding(
        finding=f"{label}: reported value {value_row.get('display_value', '')}".strip(),
        reason=reason,
        severity=severity,
        source=source,
        recommended_action=action,
        parameter=value_row.get("parameter"),
        confidence=value_row.get("confidence"),
    )


def _numeric(row: dict) -> float | None:
    value = row.get("value")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _value_with_unit(row: dict, unit: str) -> str:
    display = str(row.get("display_value", row.get("value", "")))
    if unit and not display.endswith(unit) and not unit.startswith("%"):
        return f"{display} {unit}"
    return f"{display}{unit}" if unit else display


def source_attribution(source_key: str) -> str:
    """Short human-readable attribution string for a source key."""
    names = {
        "ada_standards_diabetes": "ADA Standards of Care (glucose criteria)",
        "nhlbi_atp3_lipids": "NHLBI ATP III cholesterol classification",
        "acc_aha_2017_hypertension": "ACC/AHA blood pressure guideline",
    }
    return names.get(source_key, source_key)


def evaluate_diabetes_value(row: dict, thresholds: dict | None = None) -> list[Finding]:
    """Evaluate ONE extracted parameter against the configured thresholds.

    ``row`` is a single diabetes extraction entry. Unit safety (§27): a
    value recorded in mmol/L is NEVER compared against mg/dL thresholds -
    it produces an information finding deferring to professionals.
    """
    rules = thresholds or DIABETES_THRESHOLDS
    parameter = row.get("parameter")
    rule = rules.get(parameter)
    if rule is None:
        return []
    value = _numeric(row)
    if value is None:
        # Descriptive entries (e.g. urine glucose "present") are documented
        # honestly without numeric interpretation.
        return [_descriptive_finding(row, rule)]
    if _is_mmol(row):
        return [_mmol_information_finding(row, rule)]

    label = rule["label"]
    source = rule["source"]
    findings: list[Finding] = []

    if "high_urgent" in rule and value >= rule["high_urgent"]:
        findings.append(_finding(
            row, label, SEVERITY_URGENT,
            f"The reported {label.lower()} of {_value_with_unit(row, rule['unit'])} is "
            f"markedly above the common reference range ({source_attribution(source)}).",
            source, ACTION_URGENT,
        ))
    elif "low_urgent" in rule and value <= rule["low_urgent"]:
        findings.append(_finding(
            row, label, SEVERITY_URGENT,
            f"The reported {label.lower()} of {_value_with_unit(row, rule['unit'])} is "
            f"markedly below the common reference range ({source_attribution(source)}).",
            source, ACTION_URGENT,
        ))
    elif value > rule.get("high", float("inf")):
        findings.append(_finding(
            row, label, SEVERITY_REVIEW,
            f"The reported {label.lower()} of {_value_with_unit(row, rule['unit'])} is "
            f"above the common reference range ({source_attribution(source)}).",
            source, ACTION_DISCUSS,
        ))
    elif value < rule.get("low", float("-inf")):
        findings.append(_finding(
            row, label, SEVERITY_REVIEW,
            f"The reported {label.lower()} of {_value_with_unit(row, rule['unit'])} is "
            f"below the common reference range ({source_attribution(source)}).",
            source, ACTION_DISCUSS,
        ))
    else:
        findings.append(_finding(
            row, label, SEVERITY_NORMAL,
            f"The reported {label.lower()} is within the common reference range "
            f"({source_attribution(source)}).",
            source, ACTION_DISCUSS,
        ))
    return findings


def _is_mmol(row: dict) -> bool:
    unit = (row.get("unit") or "").lower()
    return "mmol" in unit


def _mmol_information_finding(row: dict, rule: dict) -> Finding:
    """mmol/L values are recorded verbatim and NOT thresholded (§27)."""
    return Finding(
        finding=f"{rule['label']}: reported value {row.get('display_value', '')} "
                f"{(row.get('unit') or '').strip()}",
        reason=(
            f"This laboratory uses mmol/L units, which MediMind does not convert "
            f"to mg/dL. The value is preserved exactly as reported "
            f"({source_attribution(rule['source'])}); its meaning should be "
            "reviewed by a healthcare professional."
        ),
        severity=SEVERITY_INFORMATION,
        source=rule["source"],
        recommended_action=ACTION_DISCUSS,
        parameter=row.get("parameter"),
        confidence=row.get("confidence"),
    )


def _descriptive_finding(row: dict, rule: dict) -> Finding:
    return Finding(
        finding=f"{rule['label']}: reported as {row.get('display_value', '')}",
        reason=(
            "The uploaded report documents this result descriptively. Its "
            "meaning depends on the laboratory method and clinical context, so "
            "MediMind defers interpretation to a healthcare professional."
        ),
        severity=SEVERITY_INFORMATION,
        source=rule["source"],
        recommended_action=ACTION_DISCUSS,
        parameter=row.get("parameter"),
        confidence=row.get("confidence"),
    )


def evaluate_diabetes_urine(row: dict) -> list[Finding]:
    """Urine glucose / ketones: flag explicit positives (report's own words)."""
    parameter = row.get("parameter")
    if parameter not in ("urine_glucose", "urine_ketones"):
        return []
    display = str(row.get("display_value") or "").lower()
    source = "ada_standards_diabetes"
    if any(term in display for term in ("present", "positive", "trace", "moderate", "large", "detected")):
        label = "Urine glucose" if parameter == "urine_glucose" else "Urine ketones"
        return [Finding(
            finding=f"{label}: report notes '{row.get('display_value', '').strip()}'",
            reason=(
                "The uploaded report documents this urine finding. Its significance "
                "depends on blood-glucose levels, hydration and clinical context, so "
                "it should be reviewed by a healthcare professional."
            ),
            severity=SEVERITY_IMPORTANT_REVIEW if parameter == "urine_ketones" else SEVERITY_REVIEW,
            source=source,
            recommended_action=ACTION_TIMELY if parameter == "urine_ketones" else ACTION_DISCUSS,
            parameter=parameter,
            confidence=row.get("confidence"),
        )]
    return []


def evaluate_diabetes_insulin(row: dict) -> list[Finding]:
    """Insulin levels: assay-dependent; always informational, never judged."""
    if row.get("parameter") != "insulin":
        return []
    return [Finding(
        finding=f"Insulin: reported value {row.get('display_value', '')}".strip(),
        reason=(
            "Insulin assay results vary widely between laboratories and depend on "
            "timing and clinical context. The uploaded report documents this value; "
            "its meaning should be reviewed by a healthcare professional."
        ),
        severity=SEVERITY_INFORMATION,
        source="ada_standards_diabetes",
        recommended_action=ACTION_DISCUSS,
        parameter=row.get("parameter"),
        confidence=row.get("confidence"),
    )]


def _term_negated(text: str, start: int) -> bool:
    """True when a term is preceded by a negation cue (e.g. 'no ketones')."""
    window = text[max(0, start - 60):start]
    return bool(re.search(
        r"\b(?:no|without|absent|negative\s+for|no\s+evidence\s+of|free\s+of|ruled\s+out)\b[^.]{0,40}$",
        window,
        re.IGNORECASE,
    ))


def _normality_statement(text: str) -> bool:
    """True when the impression itself declares normality."""
    return bool(re.search(
        r"\b(?:no\s+(?:significant|acute|relevant)?\s*abnormalit|normal\s+(?:report|study|result)"
        r"|unremarkable|within\s+normal\s+limits|no\s+abnormality)\b",
        text,
        re.IGNORECASE,
    ))


def _find_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    """Find non-negated, word-boundary term hits in the impression."""
    found: list[str] = []
    for term in terms:
        match = re.search(rf"\b{re.escape(term)}", text, re.IGNORECASE)
        if match and not _term_negated(text, match.start()):
            found.append(term)
    return found


def evaluate_diabetes_impression(impression: str | None) -> list[Finding]:
    """Flag explicitly reported impression language (report's own words).

    The impression is quoted/attributed to the source document - MediMind
    NEVER rewrites it and NEVER confirms a diagnosis from it. Negated
    phrases ("no ketonuria") and normality statements are NOT flagged.
    """
    if not impression:
        return []
    findings: list[Finding] = []

    urgent_terms = _find_terms(impression, IMPRESSION_URGENT_TERMS)
    if urgent_terms:
        findings.append(Finding(
            finding="The report's impression contains urgent-sounding terminology",
            reason=(
                "The uploaded report's impression includes: "
                f"{', '.join(urgent_terms[:3])}. The uploaded report states this in its "
                "own conclusion section."
            ),
            severity=SEVERITY_URGENT,
            source="ada_standards_diabetes",
            recommended_action=ACTION_URGENT,
            parameter="impression",
        ))
        return findings

    review_terms = _find_terms(impression, IMPRESSION_REVIEW_TERMS)
    if review_terms and not _normality_statement(impression):
        findings.append(Finding(
            finding="The report's impression mentions diabetes-related findings that commonly warrant professional review",
            reason=(
                "The uploaded report's impression includes: "
                f"{', '.join(review_terms[:4])}. The uploaded report states this in its "
                "own conclusion section."
            ),
            severity=SEVERITY_REVIEW,
            source="ada_standards_diabetes",
            recommended_action=ACTION_DISCUSS,
            parameter="impression",
        ))
    return findings


@dataclass
class DiabetesRuleResult:
    """Aggregate outcome of evaluating one diabetes report."""

    findings: list[Finding] = field(default_factory=list)
    overall_flag: str = FLAG_NORMAL_INFORMATION

    def compute_flag(self) -> str:
        severities = [f.severity for f in self.findings]
        worst = highest_severity(severities)
        if worst == SEVERITY_URGENT:
            self.overall_flag = FLAG_URGENT
        elif worst == SEVERITY_IMPORTANT_REVIEW:
            self.overall_flag = FLAG_IMPORTANT_REVIEW
        elif worst == SEVERITY_REVIEW:
            self.overall_flag = FLAG_REVIEW
        else:
            self.overall_flag = FLAG_NORMAL_INFORMATION
        return self.overall_flag


def evaluate_diabetes_report(extracted: dict, thresholds: dict | None = None) -> DiabetesRuleResult:
    """Evaluate every extracted diabetes parameter present in the report.

    ``extracted`` is the diabetes extraction structure
    ``{"parameters": [...], "impression": ...}``. Absent parameters yield
    no findings; findings are always source-attributed and conservatively
    worded. The engine NEVER produces a diagnosis.
    """
    result = DiabetesRuleResult()
    parameters = extracted.get("parameters") or []

    for row in parameters:
        parameter = row.get("parameter")
        if parameter in ("urine_glucose", "urine_ketones"):
            result.findings.extend(evaluate_diabetes_urine(row))
        elif parameter == "insulin":
            result.findings.extend(evaluate_diabetes_insulin(row))
        else:
            result.findings.extend(evaluate_diabetes_value(row, thresholds))

    result.findings.extend(evaluate_diabetes_impression(extracted.get("impression")))
    result.compute_flag()
    return result


__all__ = [
    "DIABETES_THRESHOLDS",
    "DiabetesRuleResult",
    "FASTING_MARKERS",
    "RANDOM_MARKERS",
    "POST_MEAL_MARKERS",
    "URINE_GLUCOSE_MARKERS",
    "URINE_KETONE_MARKERS",
    "INSULIN_MARKERS",
    "evaluate_diabetes_report",
    "evaluate_diabetes_value",
    "evaluate_diabetes_impression",
    "source_attribution",
    "FLAG_IMPORTANT_REVIEW",
    "FLAG_NORMAL_INFORMATION",
    "FLAG_REVIEW",
    "FLAG_URGENT",
    "Finding",
]
