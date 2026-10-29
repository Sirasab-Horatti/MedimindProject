"""
MediMind 6.0 - medical_rules package.

A configurable, attributable rules layer for specialized report analysis.

  * ``evidence.py``     - the Medical Evidence Library (source metadata)
  * ``base_rules.py``   - shared vocabulary (Finding, severities, wording)
  * ``cardiac_rules.py``- cardiac parameter thresholds + interpretation
  * ``diabetes_rules.py``- diabetes parameter thresholds + interpretation (8.5)

Rules NEVER diagnose. They compare a value against a documented,
source-attributed reference and produce a finding that recommends
PROFESSIONAL review. Thresholds are intentionally conservative and every
finding carries its evidence source key.
"""
