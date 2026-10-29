"""
MediMind 6.0 - Medical Evidence Library.

Attribution metadata for every specialized interpretation MediMind makes.
Entries are curated from publicly available clinical guidelines of
reputable organizations. They are stored as METADATA (organization,
title, version, section, URL) and referenced by ``source_key`` from the
rules engine; they are seeded into the ``evidence_sources`` table so the
UI can show "Evidence source" and "Why am I seeing this?".

NOTE: the thresholds in cardiac_rules.py are CONSERVATIVE,
general-adult screening references attributed to these sources. They
depend on context (age, sex, assay, clinical history) and MediMind
always presents them as general reference information requiring
professional review - never as universal rules or a diagnosis.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.database.tables import EvidenceSource

EVIDENCE_LIBRARY: list[dict] = [
    {
        "source_key": "aha_acc_2007_ecg_standardization",
        "source_name": "AHA/ACC/HRS Recommendations for the Standardization and Interpretation of the Electrocardiogram",
        "organization": "American Heart Association / American College of Cardiology / Heart Rhythm Society",
        "document_title": "Recommendations for the Standardization and Interpretation of the Electrocardiogram, Part II: Electrocardiogram Diagnostic Statement List and Interval Interpretation",
        "version": "2007",
        "section": "Interval and waveform measurement",
        "url": "https://www.ahajournals.org/doi/10.1161/circulationaha.106.180200",
        "specialty": "CARDIAC",
    },
    {
        "source_key": "acc_aha_hfsa_2022_heart_failure",
        "source_name": "AHA/ACC/HFSA Guideline for the Management of Heart Failure",
        "organization": "American Heart Association / American College of Cardiology / Heart Failure Society of America",
        "document_title": "2022 AHA/ACC/HFSA Guideline for the Management of Heart Failure",
        "version": "2022",
        "section": "Classification of left ventricular ejection fraction",
        "url": "https://www.ahajournals.org/doi/10.1161/CIR.0000000000001063",
        "specialty": "CARDIAC",
    },
    {
        "source_key": "acc_aha_2017_hypertension",
        "source_name": "ACC/AHA Guideline for High Blood Pressure in Adults",
        "organization": "American College of Cardiology / American Heart Association",
        "document_title": "2017 Guideline for the Prevention, Detection, Evaluation, and Management of High Blood Pressure in Adults",
        "version": "2017",
        "section": "Blood pressure categories",
        "url": "https://www.ahajournals.org/doi/10.1161/HYP.0000000000000065",
        "specialty": "CARDIAC",
    },
    {
        "source_key": "nhlbi_atp3_lipids",
        "source_name": "NHLBI ATP III Cholesterol Classification",
        "organization": "National Heart, Lung, and Blood Institute (National Cholesterol Education Program)",
        "document_title": "Third Report of the Expert Panel on Detection, Evaluation, and Treatment of High Blood Cholesterol in Adults (Adult Treatment Panel III)",
        "version": "2002 (update 2004)",
        "section": "LDL, total cholesterol, HDL and triglyceride classification",
        "url": "https://www.nhlbi.nih.gov/files/docs/resources/heart/atp-3-cholesterol-full-report.pdf",
        "specialty": "CARDIAC",
    },
    {
        "source_key": "ada_standards_diabetes",
        "source_name": "ADA Standards of Care in Diabetes - Diagnostic Criteria",
        "organization": "American Diabetes Association",
        "document_title": "Standards of Care in Diabetes (current edition)",
        "version": "annual edition",
        "section": "Classification and diagnosis of diabetes: glucose criteria",
        "url": "https://diabetesjournals.org/care",
        "specialty": "DIABETES",
    },
    {
        "source_key": "ada_2023_comorbidities_lipids",
        "source_name": "ADA Standards of Care - Comprehensive Medical Evaluation and Assessment of Comorbidities (lipid management)",
        "organization": "American Diabetes Association",
        "document_title": "Standards of Care in Diabetes (current edition)",
        "version": "annual edition",
        "section": "Lipid-lowering management in diabetes",
        "url": "https://diabetesjournals.org/care",
        "specialty": "DIABETES",
    },
    {
        "source_key": "esc_2023_acs_troponin",
        "source_name": "ESC Guidelines for the Management of Acute Coronary Syndromes",
        "organization": "European Society of Cardiology",
        "document_title": "2023 ESC Guidelines for the management of acute coronary syndromes",
        "version": "2023",
        "section": "High-sensitivity cardiac troponin assays",
        "url": "https://academic.oup.com/eurheartj/article/44/38/3720/7259740",
        "specialty": "CARDIAC",
    },
    {
        "source_key": "esc_2024_atrial_fibrillation",
        "source_name": "ESC Guidelines for the Management of Atrial Fibrillation",
        "organization": "European Society of Cardiology",
        "document_title": "2024 ESC Guidelines for the management of atrial fibrillation",
        "version": "2024",
        "section": "Detection and diagnosis",
        "url": "https://academic.oup.com/eurheartj/article/45/36/3314/7741372",
        "specialty": "CARDIAC",
    },
    {
        "source_key": "esc_eacts_2021_valve_disease",
        "source_name": "ESC/EACTS Guidelines for the Management of Valvular Heart Disease",
        "organization": "European Society of Cardiology / European Association for Cardio-Thoracic Surgery",
        "document_title": "2021 ESC/EACTS Guidelines for the management of valvular heart disease",
        "version": "2021",
        "section": "Assessment of stenotic and regurgitant lesions",
        "url": "https://academic.oup.com/eurheartj/article/43/7/561/6273580",
        "specialty": "CARDIAC",
    },
    {
        "source_key": "ehra_2020_qtc_interpretation",
        "source_name": "EHRA Position Paper - QTc Interval Interpretation",
        "organization": "European Heart Rhythm Association",
        "document_title": "QTc interval prolongation: thresholds and interpretation (position paper)",
        "version": "2020",
        "section": "QTc thresholds",
        "url": "https://www.escardio.org/working-groups/ehra",
        "specialty": "CARDIAC",
    },
    {
        "source_key": "aha_2022_ecg_axis",
        "source_name": "AHA ECG Interpretation - Cardiac Axis",
        "organization": "American Heart Association",
        "document_title": "Standardization and interpretation of the electrocardiogram: axis determination",
        "version": "2007 (reaffirmed)",
        "section": "Mean electrical axis",
        "url": "https://www.ahajournals.org/doi/10.1161/circulationaha.106.180200",
        "specialty": "CARDIAC",
    },
]


def evidence_by_key(source_key: str) -> dict | None:
    """Look up one library entry (used when building citations in rules)."""
    for entry in EVIDENCE_LIBRARY:
        if entry["source_key"] == source_key:
            return dict(entry)
    return None


def seed_evidence_sources(db: Session) -> int:
    """Upsert the library into evidence_sources (idempotent). Returns added count."""
    added = 0
    for entry in EVIDENCE_LIBRARY:
        existing = (
            db.query(EvidenceSource)
            .filter(EvidenceSource.source_key == entry["source_key"])
            .first()
        )
        if existing is not None:
            continue
        db.add(
            EvidenceSource(
                source_key=entry["source_key"],
                source_name=entry["source_name"],
                organization=entry["organization"],
                document_title=entry["document_title"],
                version=entry.get("version"),
                section=entry.get("section"),
                url=entry.get("url"),
                specialty=entry.get("specialty", "GENERAL"),
            )
        )
        added += 1
    if added:
        db.commit()
    return added
