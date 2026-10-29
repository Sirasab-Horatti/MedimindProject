"""
MediMind 6.0 - cardiac rules engine.

Conservative, source-attributed interpretation of extracted cardiac
report values. The engine ONLY evaluates values actually present in the
uploaded report (absent parameters produce NO finding - never a guess).

Every threshold here is configurable and attributed to a source in the
Medical Evidence Library (medical_rules/evidence.py). Thresholds are
general-adult screening references that depend on context (age, sex,
assay, symptoms, clinical history). The engine always frames results as
"requires professional review" - it NEVER diagnoses and NEVER suggests
starting or stopping medication.
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

CARDIAC_THRESHOLDS: dict = {
    "heart_rate": {
        "label": "Heart rate",
        "low_urgent": 40, "low": 50, "high": 100, "high_urgent": 130,
        "unit": "bpm",
        "source": "aha_acc_2007_ecg_standardization",
    },
    "pr_interval_ms": {
        "label": "PR interval",
        "high_urgent": 300, "high": 200, "low": 120,
        "unit": "ms",
        "source": "aha_acc_2007_ecg_standardization",
    },
    "qrs_duration_ms": {
        "label": "QRS duration",
        "high_urgent": 160, "high": 120,
        "unit": "ms",
        "source": "aha_acc_2007_ecg_standardization",
    },
    "qtc_ms": {
        "label": "QTc interval",
        "high_urgent": 500, "high": 460, "low_urgent": 340, "low": 350,
        "unit": "ms",
        "source": "ehra_2020_qtc_interpretation",
    },
    "ejection_fraction": {
        "label": "Ejection fraction",
        "low_urgent": 30, "low": 40, "normal_low": 50,
        "unit": "%",
        "source": "acc_aha_hfsa_2022_heart_failure",
    },
    "ldl_mg_dl": {
        "label": "LDL cholesterol",
        "high_urgent": 190, "high": 130,
        "unit": "mg/dL",
        "source": "nhlbi_atp3_lipids",
    },
    "total_cholesterol_mg_dl": {
        "label": "Total cholesterol",
        "high": 240,
        "unit": "mg/dL",
        "source": "nhlbi_atp3_lipids",
    },
    "hdl_mg_dl": {
        "label": "HDL cholesterol",
        "low": 40,
        "unit": "mg/dL",
        "source": "nhlbi_atp3_lipids",
    },
    "triglycerides_mg_dl": {
        "label": "Triglycerides",
        "high": 200, "high_urgent": 500,
        "unit": "mg/dL",
        "source": "nhlbi_atp3_lipids",
    },
    "glucose_mg_dl": {
        "label": "Glucose",
        "low_urgent": 54.0, "low": 70.0, "high": 140.0, "high_urgent": 250.0,
        "unit": "mg/dL",
        "source": "ada_standards_diabetes",
    },
    "systolic_bp": {
        "label": "Systolic blood pressure",
        "high": 130, "high_urgent": 180,
        "unit": "mmHg",
        "source": "acc_aha_2017_hypertension",
    },
    "diastolic_bp": {
        "label": "Diastolic blood pressure",
        "high": 80, "high_urgent": 120,
        "unit": "mmHg",
        "source": "acc_aha_2017_hypertension",
    },
}

# Words that, when present in the physician impression, constitute
# red-flag phrasing deserving an urgent-care prompt (still not a
# diagnosis - the IMPRESSION belongs to the reporting physician).
IMPRESSION_URGENT_TERMS = (
    "st elevation",
    "stemi",
    "depression suggestive of ischemia",
    "acute",
    "critical",
    "severe",
    "emergency",
)

# Descriptive rhythm/finding phrases that warrant professional review
IMPRESSION_REVIEW_TERMS = (
    "atrial fibrillation",
    "atrial flutter",
    "arrhythmia",
    "ectopic",
    "ischemia",
    "ischemic",
    "infarct",
    "block",
    "abnormal",
    "prolonged",
    "stenosis",
    "regurgitation",
    "hypokinesia",
    "hypokinesis",
    "akinesia",
    "dilation",
    "hypertrophy",
)

# Severity strings inside Finding rows
_ALT_NORMAL = SEVERITY_NORMAL


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


def evaluate_cardiac_value(row: dict, thresholds: dict | None = None) -> list[Finding]:
    """Evaluate ONE extracted parameter against the configured thresholds.

    ``row`` is a single cardiac extraction entry:
    ``{"parameter", "label", "value", "unit", "display_value", ...}``.
    Returns 0 findings when the value is absent or non-numeric
    (descriptive fields are handled by evaluate_cardiac_impression).
    """
    rules = thresholds or CARDIAC_THRESHOLDS
    parameter = row.get("parameter")
    rule = rules.get(parameter)
    if rule is None:
        return []
    value = _numeric(row)
    if value is None:
        return []

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


def source_attribution(source_key: str) -> str:
    """Short human-readable attribution string for a source key."""
    names = {
        "aha_acc_2007_ecg_standardization": "AHA/ACC/HRS ECG standardization recommendations",
        "acc_aha_hfsa_2022_heart_failure": "AHA/ACC/HFSA heart failure guideline",
        "acc_aha_2017_hypertension": "ACC/AHA blood pressure guideline",
        "nhlbi_atp3_lipids": "NHLBI ATP III cholesterol classification",
        "ada_standards_diabetes": "ADA Standards of Care (glucose criteria)",
        "esc_2023_acs_troponin": "ESC acute coronary syndrome guidelines (troponin)",
        "esc_2024_atrial_fibrillation": "ESC atrial fibrillation guideline",
        "esc_eacts_2021_valve_disease": "ESC/EACTS valvular heart disease guideline",
        "ehra_2020_qtc_interpretation": "EHRA QTc interpretation position paper",
        "aha_2022_ecg_axis": "AHA ECG axis standardization",
    }
    return names.get(source_key, source_key)


def evaluate_cardiac_value_with_troponin(rows_by_param: dict[str, dict],
                                         thresholds: dict | None = None) -> list[Finding]:
    """Evaluate numeric parameters INCLUDING troponin (assay-dependent).

    Troponin handling is deliberately conservative: assays differ, so any
    reported, elevated-above-the-report's-own-reference value produces a
    REVIEW finding that defers to the report and to professionals - the
    engine never decides "troponin is normal" for an unfamiliar assay.
    """
    findings: list[Finding] = []
    for parameter in ("troponin",):
        row = rows_by_param.get(parameter)
        if not row:
            continue
        numeric = _numeric(row)
        if numeric is None:
            # Descriptive troponin (e.g. "negative", "<0.01 ng/mL")
            findings.append(Finding(
                finding=f"Troponin: reported as {row.get('display_value', '')}".strip(),
                reason=(
                    "Cardiac troponin interpretation depends on the specific assay and "
                    "clinical context. The uploaded report documents this value; its "
                    "meaning should be reviewed by a healthcare professional."
                ),
                severity=SEVERITY_INFORMATION,
                source="esc_2023_acs_troponin",
                recommended_action=ACTION_DISCUSS,
                parameter=row.get("parameter"),
                confidence=row.get("confidence"),
            ))
            continue

        ref_text = row.get("reference_range") or ""
        # Try to read the report's OWN upper reference limit (e.g. "<0.04 ng/mL")
        upper_limit = None
        match = re.search(r"<\s*([0-9]*\.?[0-9]+)", ref_text)
        if match:
            try:
                upper_limit = float(match.group(1))
            except ValueError:
                upper_limit = None

        if upper_limit is not None and numeric > upper_limit:
            findings.append(Finding(
                finding=f"Troponin: reported value {row.get('display_value', '')} is above the "
                        "reference limit printed on the report",
                reason=(
                    f"The report lists {row.get('display_value', '')} against its own reference "
                    f"of {ref_text}. Values above the report's stated limit warrant prompt "
                    "professional review (ESC ACS guidance on high-sensitivity troponin)."
                ),
                severity=SEVERITY_IMPORTANT_REVIEW,
                source="esc_2023_acs_troponin",
                recommended_action=ACTION_TIMELY,
                parameter=row.get("parameter"),
                confidence=row.get("confidence"),
            ))
        else:
            findings.append(Finding(
                finding=f"Troponin: reported value {row.get('display_value', '')}",
                reason=(
                    "The uploaded report documents this troponin result. Interpretation "
                    "depends on the assay, timing and clinical context, so MediMind defers "
                    "the meaning to a healthcare professional."
                ),
                severity=SEVERITY_INFORMATION,
                source="esc_2023_acs_troponin",
                recommended_action=ACTION_DISCUSS,
                parameter=row.get("parameter"),
                confidence=row.get("confidence"),
            ))

    return []


def _term_negated(text: str, start: int) -> bool:
    """True when a term is preceded by a negation cue (e.g. 'No ST elevation')."""
    window = text[max(0, start - 60):start]
    return bool(re.search(
        r"\b(?:no|without|absent|negative\s+for|no\s+evidence\s+of|free\s+of|ruled\s+out)\b[^.]{0,40}$",
        window,
        re.IGNORECASE,
    ))


def _normality_statement(text: str) -> bool:
    """True when the impression itself declares normality."""
    return bool(re.search(
        r"\b(?:no\s+(?:significant|acute|relevant)?\s*abnormalit|normal\s+(?:ecg|ekg|study|report)"
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


def _value_with_unit(row: dict, unit: str) -> str:
    display = str(row.get("display_value", row.get("value", "")))
    if unit and not display.endswith(unit) and not unit.startswith("%"):  
        return f"{display} {unit}"
    return f"{display}{unit}" if unit else display


def evaluate_cardiac_impression(impression: str | None) -> list[Finding]:
    """Flag explicitly reported impression language (report's own words).

    The impression is quoted/attributed to the source document - MediMind
    NEVER rewrites it and NEVER confirms it. Negated phrases ("No ST
    elevation") and plain normality statements are NOT flagged.
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
                f"{', '.join(urgent_terms[:3])}. The uploaded report states this in its own "
                "conclusion section."
            ),
            severity=SEVERITY_URGENT,
            source="aha_acc_2007_ecg_standardization",
            recommended_action=ACTION_URGENT,
            parameter="impression",
        ))

    review_terms = _find_terms(impression, IMPRESSION_REVIEW_TERMS)
    if review_terms and not urgent_terms and not _normality_statement(impression):
        findings.append(Finding(
            finding="The report's impression mentions findings that commonly warrant professional review",
            reason=(
                "The uploaded report's impression includes: "
                f"{', '.join(review_terms[:4])}. The uploaded report states this in its own "
                "conclusion section."
            ),
            severity=SEVERITY_REVIEW,
            source="aha_acc_2007_ecg_standardization",
            recommended_action=ACTION_DISCUSS,
            parameter="impression",
        ))
    return findings


def evaluate_wall_motion(findings_text: str | None) -> list[Finding]:
    """Flag explicitly reported wall-motion descriptors (echo reports)."""
    if not findings_text:
        return []
    text = findings_text.lower()
    flagged = [term for term in ("hypokinesia", "hypokinesis", "akinesia", "dyskinesia", "aneurysm") if term in text]
    if flagged:
        return [Finding(
            finding="The echo report describes a wall-motion abnormality",
            reason=(
                f"The uploaded report states: '{findings_text.strip()}'. Wall-motion "
                "descriptions are interpreted together with the rest of the echo study by "
                "a cardiologist."
            ),
            severity=SEVERITY_IMPORTANT_REVIEW,
            source="acc_aha_hfsa_2022_heart_failure",
            recommended_action=ACTION_TIMELY,
            parameter="wall_motion",
        )]
    return []


def evaluate_valve(findings_text: str | None) -> list[Finding]:
    """Flag explicitly reported valve descriptors (echo reports)."""
    if not findings_text:
        return []
    text = findings_text.lower()
    flagged = [term for term in ("stenosis", "regurgitation", "prolapse", "prosthetic", "stenotic") if term in text]
    if flagged:
        return [Finding(
            finding="The echo report describes a valve finding",
            reason=(
                f"The uploaded report states: '{findings_text.strip()}'. Valve findings are "
                "graded and managed by a cardiologist based on severity and symptoms."
            ),
            severity=SEVERITY_REVIEW,
            source="esc_eacts_2021_valve_disease",
            recommended_action=ACTION_DISCUSS,
            parameter="valve_findings",
        )]
    return []


@dataclass
class CardiacRuleResult:
    """Aggregate outcome of evaluating one cardiac report."""

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


def evaluate_cardiac_report(extracted: dict, thresholds: dict | None = None) -> CardiacRuleResult:
    """Evaluate every extracted cardiac parameter present in the report.

    ``extracted`` is the cardiac extraction structure:
    ``{"parameters": [...], "impression": ...}``. Absent parameters yield
    no findings; findings are always source-attributed and conservatively
    worded.
    """
    result = CardiacRuleResult()
    parameters = extracted.get("parameters") or []
    rows_by_param = {row.get("parameter"): row for row in parameters if row.get("parameter")}

    for row in parameters:
        parameter = row.get("parameter")
        if parameter == "troponin":
            result.findings.extend(
                evaluate_cardiac_value_with_troponin({parameter: row}, thresholds)
            )
        else:
            result.findings.extend(evaluate_cardiac_value(row, thresholds))

    result.findings.extend(evaluate_cardiac_impression(extracted.get("impression")))
    result.findings.extend(evaluate_wall_motion(extracted.get("wall_motion_findings")))
    result.findings.extend(evaluate_valve(extracted.get("valve_findings")))
    result.compute_flag()
    return result
