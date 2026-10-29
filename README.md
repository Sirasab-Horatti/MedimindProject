# MediMind — An Agentic AI-Based Intelligent Healthcare Decision Support System

MediMind is a full-stack, multi-role healthcare **decision-support** platform.
Patients describe symptoms in natural language — **typed, spoken, in 11
languages** — and receive a **preliminary AI assessment** produced by a
transparent multi-agent workflow, NLP symptom extraction and a trained
machine-learning model — with explainability, continuous monitoring, alerts,
doctor review, professional reports, analytics and a complete audit trail.

> ⚠️ **Medical disclaimer** — MediMind provides an AI-based preliminary health
> assessment for educational and decision-support purposes. It is **not** a
> substitute for professional medical diagnosis, treatment, or emergency care.
> If you may be experiencing an emergency, contact a qualified healthcare
> professional or your local emergency service immediately.

---

## 🫀 What's new in 6.0 — Specialized Medical Report Intelligence

- **Medical Reports** (`/medical-reports`) — upload specialist documents
  (PDF, text, images) with drag & drop, real processing states, secure
  storage outside the web root (opaque names, no public URLs), authorized
  download/preview and safe deletion.
- **Report type detection** — CARDIAC, DIABETES, RENAL, LIVER, CBC,
  GENERAL_LAB, OTHER via keyword classification with a strong-signal guard;
  CARDIAC and DIABETES have fully implemented specialized analysis — other
  types are stored/classified with an honest "not yet available"
  (never faked).
- **Cardiac analyzer** — extracts only what the document actually contains
  (ECG intervals, rhythm, ejection fraction, lipids, glucose, BP,
  troponin…), preserving original values/units/reference ranges, with absent
  fields explicitly "Not available in the uploaded report".
- **Evidence/rules engine** (`medical_rules/`) — configurable, source-
  attributed thresholds (AHA/ACC/HRS, AHA/ACC/HFSA, ACC/AHA, NHLBI ATP III,
  ADA, ESC, EHRA) rendered through the **Medical Evidence Library** with
  "Why am I seeing this?" attribution in the UI.
- **Specialized cardiac decision support** — Key Findings, Items for
  Professional Review, Follow-up Discussion, Monitoring Suggestions,
  Questions for a Doctor, Report Comparison and Emergency Warnings only when
  justified. Conservative flags ("requires professional review") — never a
  diagnosis, never medication instructions.
- **Physician impression kept separate** — the report's own Impression/
  Conclusion is shown as "Reported by the source document", apart from
  "MediMind explanation" (negation-aware: "No ST elevation" is not flagged).
- **Longitudinal comparison** — Previous / Current / Change for measurements
  that really exist in two consecutive reports (unit-mismatch safe; trends
  are never labelled improving/worsening on MediMind's authority).
- **Monitoring · Alerts · Timeline integration** — report-sourced vitals
  become clearly-labelled Monitoring Records reviewed by the existing
  Monitoring Agent; rule flags raise report-linked alerts; four new timeline
  events are computed from real reports.
- **Doctor review** (`/doctor/medical-reports`) — assigned doctors see the
  original document, AI EXTRACTION and AI EXPLANATION (clearly separated)
  and record their own DOCTOR REVIEW; patients see it on the report page.
- **Cardiac dashboard** (`/cardiac`) — reports, latest findings, trends only
  from real history ("No previous cardiac reports available for comparison"
  otherwise), open alerts and doctor reviews.
- **Controlled report Q&A + voice** — ask "Explain my cardiac report" or
  "What changed from my previous report?" in chat or by voice; answers are
  retrieved ONLY from the user's authorized reports with evidence citations
  and are readable aloud in the selected language (medical values are never
  translated).
- **Document + symptom fusion with explicit consent** — the assessment can
  show the latest cardiac report as labelled context only after an explicit
  YES; the ML model input itself never changes.

See **[docs/medical-reports.md](docs/medical-reports.md)** for the full 6.0
architecture, API surface and safety model.

---

## 🌍 What's new in 9.0 — Global Clinical Knowledge, Disease Database & Evidence-Grounded Decision Support

MediMind 9.0 adds a source-aware, versioned, structured, multilingual,
evidence-grounded healthcare decision-support layer — an **incremental**
upgrade with zero removals and no parallel medical system. Full details in
**[docs/clinical-knowledge.md](docs/clinical-knowledge.md)**:

- **Explicit source hierarchy (§1)** — Tier 1 WHO/national guidelines outrank
  Tier 2 specialty societies, Tier 3 peer-reviewed evidence and Tier 4
  academic-hospital education (supplementary only, never guideline-equivalent).
  21 curated sources seeded; every relationship provenanced.
- **Disease master + ICD-11 backbone (§4/§5)** — controlled seed of 10 canonical
  diseases (hypertension BA00, type 2 diabetes 5A11, ischaemic heart disease
  BA41, …) with 11-language aliases, plus provenanced symptom links (47),
  risk factors (41), findings, tests, complications, differentials, guidelines
  and red flags.
- **Recommendation engine (§13–§15)** — `POST /clinical/recommendations/assess`
  turns text/voice/canonical symptoms into POSSIBLE considerations with red-flag
  evaluation, safe recommendation categories only (no medication changes, no
  prescriptions), a full evidence chain and jurisdiction-aware guidance
  (default INDIA). Conflicting guidelines (ACC/AHA 130/80 vs ESH/ISH 140/90)
  are disclosed, never silently merged (§16).
- **WHO population-health layer (§3/§41)** — offline-safe GHO sync, stored with
  methodology notes, always labelled POPULATION STATISTICS, never used as
  personal risk.
- **Governance & ingestion (§18–§21)** — source freshness/versioning
  (history never deleted), approval chain NEW → QUALITY_CHECK → REVIEW_REQUIRED
  → APPROVED → ACTIVE (new guidance never auto-activates), transparent
  quality components instead of any fake "accuracy score".
- **Semantic retrieval + evaluation (§25/§43/§44)** — hashed-trigram hybrid
  retrieval over the existing keyword index; per-capability evaluation runs
  (red-flag detection, recommendation retrieval, keyword-vs-hybrid) stored
  separately — never one meaningless "AI accuracy" number.
- **Doctor review of AI recommendations (§35)** — AGREE/DISAGREE/MODIFY/ADD_NOTE
  verdicts on stored recommendations; feedback never triggers automatic
  production retraining (§36).
- **Admin Clinical Knowledge Center (§38/§39)** — `/admin/clinical-knowledge`:
  tiered source dashboard, diseases, rules, ranges, conflicts, pending
  ingestion reviews with approve/retire actions, outdated sources and
  knowledge-quality checks (§27: unprovenanced relationships, unmapped ICD,
  unsupported recommendations, …).
- **Multilingual provenance UI (§32–§34)** — "Why this recommendation?" and
  "Evidence used" cards with tier badges, source dates and jurisdiction;
  voice "why" questions answer from the SAME stored recommendation + evidence;
  localized labels keep codes/values/units unchanged.
- **71 new tests** (`tests/test_clinical_knowledge.py`) — disease DB, ICD
  mapping, tiers, red flags, engine, provenance, jurisdiction, conflicts, WHO
  layer, retrieval, ingestion approval, doctor review, RBAC, audit, quality.
  Full suite: **405 passed** (334 baseline + 71).

---

## 🩸 What's new in 8.5 — Diabetes Specialized Intelligence

Diabetes is the second fully implemented specialty, built on the exact
6.0/7.0/8.0 extension points — no new tables, no new paradigms, everything
labelled and source-attributed the same way as cardiac:

- **Diabetes analyzer** (`DiabetesReportAnalyzer`) — extracts only what the
  document contains: HbA1c (%), fasting/random/post-meal glucose, generic
  glucose (never silently promoted), descriptive urine glucose/ketones,
  fasting insulin, lipid panel and BP — with absent fields honestly "Not
  available in the uploaded report" and mmol/L values preserved verbatim
  (never compared to mg/dL thresholds).
- **Strong-signal classification** — a document becomes DIABETES only with a
  real diabetes-specific marker (HbA1c, named glucose variants, urine
  ketones, fasting insulin, diabetes panel); "diabetic" + one glucose value
  never classifies on its own.
- **ADA-attributed rules** (`medical_rules/diabetes_rules.py`, rule version
  `diabetes-rules-8.5`) — HbA1c/glucose/lipid/BP thresholds with per-finding
  source attribution; urine positives flagged in the report's own words;
  DKA/hyperosmolar/critical impressions get the fixed safe urgent wording.
- **Everywhere diabetes lives** — timeline says "Diabetes report", alerts
  carry diabetes rule provenance, monitoring records note "uploaded diabetes
  report", the list endpoint returns `diabetes_count`, prediction fusion
  shows "Values from your uploaded diabetes report" with explicit consent,
  and the assistant answers "What is my HbA1c?" from the real report with
  ADA citations.
- **Diabetes UX** — `/diabetes` dashboard, `/diabetes/knowledge` (cited ADA
  education topics), a Diabetes filter + dashboard tiles in Medical Reports,
  nav entries and a "show my diabetes dashboard" voice command.
- **38 new tests** (`tests/test_diabetes_reports.py`) — classification,
  extraction, rules, longitudinal comparison (HbA1c 5.8→8.2), medical-safety
  scans, timeline/monitoring/alerts/doctor-review/audit integration, Q&A,
  fusion consent and knowledge grounding. Full suite at 8.5: **334 passed**.

---

## 🗄️ What's new in 8.0 — Clinical Data Intelligence & Strong Database

The data layer is now structured, longitudinal and queryable — built for
AI/ML decision support without ever turning stored values into diagnoses:

- **Structured clinical layer** — uploaded reports are no longer just PDFs +
  JSON blobs: `report_sections` (queryable ECG/LABS/IMPRESSION sections) and
  `report_observations` (one verbatim row per extracted value with unit,
  the report's own reference text, extraction confidence and a rules-status
  LABEL — never an AI interpretation) are persisted at upload time.
- **Time-series measurements** — every value (report-extracted AND
  patient-entered vitals) flows into `clinical_measurements` with patient +
  parameter + observed_at + provenance. Latest/previous/history/trends are
  pure indexed queries; unit conversion happens ONLY along explicitly safe
  paths (mg/dL→mmol/L is blocked as analyte-dependent).
- **Full provenance** — every datum is PATIENT_ENTERED, REPORT_EXTRACTED,
  DOCTOR_ENTERED, MONITORING_DEVICE or AI_DERIVED. AI-derived data is never
  an original measurement; patient-entered is never doctor-confirmed.
- **Catalogs & ontology** — `specialties` (CARDIAC and DIABETES are ACTIVE —
  activation requires analyzer+rules+knowledge+tests), `clinical_parameters`
  (18 real parameters incl. diabetes-ready rows), `symptom_dictionary`
  (192 canonical symptoms with 11-language aliases), versioned
  `clinical_rules` with guideline sources.
- **Model & dataset lineage** — every prediction now links to the exact
  ACTIVE `model_versions` row (which itself references its `datasets`
  version), plus `prediction_evidence` and consent-preserving
  `prediction_context` rows.
- **Alert & knowledge provenance** — alerts carry `source_record_id` +
  `rule_code` + `rule_version`; knowledge gains `knowledge_documents` and
  `knowledge_chunks` (embedding-ready columns, no heavyweight vector DB).
- **Data quality engine** — `/admin/data-quality` aggregates extraction
  failures, content-hash duplicate reports, unmapped parameters, numeric
  mismatches and future-dated rows — flags for review, never silently fixes.
- **Clinical APIs & UX** — `/clinical/patient/{id}/measurements|trends|
  symptoms|timeline|history` (ownership/assignment/RBAC enforced), new
  patient **Clinical History** page with real-data trend graphs (shown only
  when ≥ 2 real observations exist) and an enriched doctor chart.
- **Non-destructive migration** — safe ADD COLUMN migrations + idempotent
  backfill (verified against the live DB; backup taken). PostgreSQL-ready
  engine with proper pooling; SQLite stays the dev fallback.

See **[docs/data-dictionary.md](docs/data-dictionary.md)** for the full
clinical data dictionary and **docs/architecture.md** for the data layer.

---

## 📚 What's new in 7.0 — Evidence-Grounded Medical Knowledge

MediMind now answers healthcare questions from clearly separated layers —
patient data, AI interpretation, medical evidence and doctor review — and
labels every response with its provenance:

- **Controlled knowledge layer** (`medical_knowledge/`) — 10 curated guideline
  sources (AHA/ACC, ESC, EHRA, NHLBI, ADA) with patient-education texts
  written from the cited documents and stored verbatim — never generated,
  never web-scraped. A groundedness guard refuses to present a topic as an
  answer when the retrieval signal is weak — "I could not find this topic"
  instead of an invented explanation.
- **Voice Q&A fixed at the gateway** — voice transcripts and typed questions
  now take the SAME unified evidence pipeline (`POST /knowledge/ask`):
  multilingual intent understanding (11 languages) → report-aware routing →
  evidence retrieval → provenance-labelled answer → TTS. Primary provider
  unavailable? Deterministic engines answer; the label says exactly what.
- **Report-aware Q&A** — "Explain my cardiac report" composes the caller's
  OWN authorized report values with cited guideline education ("your QTc is
  410 ms — QTc is…, EHRA 2020"). Cross-user access is impossible by
  construction, and patient data never leaves the controlled path.
- **Provenance labels on every answer** — AI Assistant / Structured MediMind
  Assistant / Medical Evidence Answer / Cardiac Report Analyzer / Patient
  Report Analysis / ML Assessment / Doctor Review, with "Evidence used"
  citations and a "Why am I seeing this?" explainer in the chat UI.
- **Admin knowledge registry** (`/admin/medical-knowledge`) — sources,
  specialties, versions, status, activate/deactivate, audited; patients can
  never modify sources (server-enforced).
- **Cardiac knowledge hub** (`/cardiac/knowledge`; plus the diabetes
  counterpart `/diabetes/knowledge` since 8.5) — education topics (ECG
  basics, echo, EF, rhythm, biomarkers, lipids, blood pressure; HbA1c,
  glucose, urine findings, insulin) fully separated from
  patient-specific interpretation.
- **Compare + summary enrichment** — report comparison now links each
  parameter to its evidence source (still never labelling changes as
  improved/worsened on its own), and the Health Summary gained real-data
  Recent Reports / Doctor Reviews sections.

See **[docs/medical-knowledge.md](docs/medical-knowledge.md)** for the
knowledge architecture, authorization model and provenance system.

---

## 🛡️ What's new in 6.5 — AI Availability, Fallback & Reliability

MediMind now survives AI-provider failures gracefully — and honestly reports
status instead of blaming "the AI" for unrelated errors:

- **Root cause fixed** — the generic error panel that showed "MediMind AI is
  temporarily unavailable" for *any* failed request (backend down, timeout,
  a 500 on alerts…) no longer mislabels non-AI failures; every page shows an
  accurate title, and AI status has dedicated components.
- **AI Gateway** (`backend/services/ai_gateway.py`) — one entry point for
  chat/report-Q&A/summary/explanation with an optional env-configured primary
  provider (OpenAI-compatible), bounded retries with exponential backoff, hard
  request timeouts, a CLOSED→OPEN→HALF_OPEN circuit breaker with automatic
  recovery, and 8-category error classification with safe user wording.
- **Deterministic fallback** — with no external provider configured (the
  default), the assistant runs on MediMind's own NLP + ML + controlled report
  Q&A. It never fakes an LLM, never fabricates medical advice, and patient
  report questions are answered by the controlled service even when a primary
  provider exists (data-leave-prevention).
- **Partial availability guarantee** — a chat outage never means MediMind is
  down: symptom extraction, ML prediction, cardiac analysis, report upload,
  monitoring, alerts, timeline, PDFs and every dashboard keep working. The
  sidebar, the assistant page and `/transparency` show honest status
  (Online / Limited Mode / temporarily unavailable) with recovery actions
  (Retry · Use Structured Assistant · Open Symptom Checker · Open Medical
  Reports).
- **Voice stays honest** — if the mic worked, the UI says "Voice input is
  working, but the conversational AI service is temporarily unavailable" —
  never "voice assistant unavailable" for an AI-layer problem.
- **Admin reliability dashboard** (`/admin/ai-health`) — availability,
  success/fallback/failure counts, timeouts, latencies, breaker state and
  error categories. Privacy-safe by construction: no message content, no
  patient data, no provider keys (`ai_operation_logs` stores metadata only).
- **Dev-only failure simulation** — double env-gated (`AI_ALLOW_FAILURE_
  SIMULATION` + mode), inert in production, health status always truthful.

See **[docs/ai-reliability.md](docs/ai-reliability.md)** for the gateway
architecture, health endpoint contract and reliability guarantees.

---

## 🎙️ What's new in 5.0 — Multilingual Voice AI & Accessibility

- **Voice-first assessment** — a guided hands-free flow (`/voice-assessment`):
  choose language → speak → confirm the transcript → the same five-agent
  pipeline and ML model produce the result, optionally read aloud.
- **11 languages** — English, हिन्दी, ಕನ್ನಡ, తెలుగు, தமிழ், മലയാളം, मराठी, বাংলা,
  ગુજરાતી, ਪੰਜਾਬੀ, اردو — selected globally, persisted per user, with native
  scripts mapped to canonical English symptoms by **local offline
  dictionaries** (no paid APIs, no bundled models).
- **Multilingual NLP bridge** (`nlp/language_service.py`) — native-language
  input (voice or typed) is canonicalized so the SAME extractor, agents and
  model assess it; negation, duration and severity are preserved across
  languages (e.g. "ನನಗೆ ಎರಡು ದಿನಗಳಿಂದ ಜ್ವರ ಇದೆ" → fever + "for 2 days").
- **Voice assistant chat** — mic conversations with voice-message bubbles
  (transcript, language, duration), Listen buttons on every reply and
  opt-in auto-speak.
- **Voice search & dictation** — symptom search by voice in any supported
  language; doctor note dictation (always review-before-save).
- **Voice settings & privacy by default** (`/settings/voice`) — voice mode,
  auto-speak, speech rate, mic/voice tests; **audio is never stored unless
  the user opts in**, stored audio is owner-scoped, and admin analytics are
  aggregate-only (no audio, no transcripts).
- **Transcript gate** — every recognition result is shown as "You said …"
  with Edit / Clear / Use This before it can affect an assessment; full text
  fallback everywhere (accessibility-first).

See **[docs/voice.md](docs/voice.md)** for the complete voice architecture.

---

## ✨ What's in the platform (4.0)

| Area | What it does |
|---|---|
| 🔐 RBAC | Three roles (PATIENT / DOCTOR / ADMIN) enforced **on the backend** — DB-truthed role checks, ownership guards, invite-gated doctor signup, one-time admin bootstrap |
| 🧠 Agentic AI | Six co-operating agents through a shared state graph: Interaction → Symptom Analysis → Preprocessing → Diagnosis → Recommendation, plus the **Monitoring Agent** feeding an alert engine |
| 💬 NLP | Multi-word symptoms, colloquial aliases, negation ("no cough"), duration and severity extraction over a dataset-derived vocabulary; **voice input in 11 languages** (Web Speech API + offline canonicalization) feeds the same pipeline |
| 🤖 Machine Learning | TF-IDF + five classifiers (LR, SVM, RF, NB, DT) trained and compared on the same split; Logistic Regression deployed — real metrics served from stored artifacts |
| 🔍 Explainable AI | Feature-based contributions from the real model: supporting evidence, contradicting evidence, per-alternative reasoning, with explicit limitations |
| 🩺 Doctor workflow | Assignment-scoped patient lists and charts, clinical review notes, follow-up recommendations, review status — AI outputs stay read-only |
| 🛡️ Admin console | Real system statistics, user/role management, doctor authorizations, audit-log viewer, feedback review, per-day analytics, Model Lab with version registry |
| ⏱️ Monitoring & alerts | Patient-entered observations (temp, HR, BP, glucose, notes) reviewed by the Monitoring Agent; deduplicated alerts (emergency / abnormal / follow-up / monitoring) with a full lifecycle |
| 📄 Advanced reports | Professional PDF with patient info, symptoms, prediction, alternatives, explainability, agent trail, monitoring, alerts, doctor review, model version, report ID |
| 🧾 Audit logging | Every security-relevant action recorded — never passwords or tokens; searchable admin viewer |
| ⭐ Feedback | "Was this assessment useful?" captured and reviewed by admins; never auto-retrains the model |
| 🧪 Testing | 153 automated tests (68 original + 85 added across 4.0/5.0) covering RBAC, ownership, monitoring, alerts, explainability, multilingual NLP, voice privacy and more |

**Trained model performance (computed on a held-out test set — not fabricated):**

| Model | Accuracy | Macro F1 | Status |
|---|---|---|---|
| Logistic Regression | 0.9802 | 0.9805 | **ACTIVE (deployed)** |
| Linear SVM | 0.9802 | 0.9804 | CANDIDATE |
| Random Forest | 0.9767 | 0.9769 | CANDIDATE |
| Naive Bayes | 0.9751 | 0.9738 | CANDIDATE |
| Decision Tree | 0.9095 | 0.9098 | CANDIDATE |

---

## 🏗️ Project structure

```
MediMind/
├── frontend/            # React + Vite SPA (role-based pages, components, services)
├── backend/             # FastAPI app (routes, models, database, utils incl. RBAC + audit)
├── agents/              # 6-agent workflow (state, graph, 5 assessment agents + monitoring)
├── nlp/                 # Text processing + symptom extraction (aliases, negation, metadata)
├── ml/                  # Dataset, preprocessing, train, evaluate, explain, artifacts
├── tests/               # 116 pytest tests (auth, RBAC, doctor, monitoring, agents, API)
├── docs/                # architecture, agents, api, database, security, ml, testing
└── README.md
```

Documentation:

* [docs/architecture.md](docs/architecture.md) — full system design & flow diagram
* [docs/agents.md](docs/agents.md) — the six agents and the alert engine
* [docs/ml.md](docs/ml.md) — dataset, models, metrics, explainability, versioning
* [docs/database.md](docs/database.md) — schema + safe migration policy
* [docs/api.md](docs/api.md) — complete endpoint reference with roles
* [docs/security.md](docs/security.md) — RBAC, ownership, audit, safety policies
* [docs/voice.md](docs/voice.md) — 5.0 voice & multilingual architecture, privacy model
* [docs/testing.md](docs/testing.md) — suite layout and manual checklist

---

## 🚀 Getting started

### Prerequisites
* Python 3.12+ (a virtual environment at `venv/` is used in this workspace)
* Node.js 18+

### 1. Backend

```bash
# from the project root
python -m venv venv
venv\Scripts\activate                 # Windows  (source venv/bin/activate on Linux/macOS)
pip install -r backend/requirements.txt

# configure secrets (backend/.env)
#   SECRET_KEY, DATABASE_URL, ALLOWED_ORIGINS
#   DOCTOR_INVITE_CODE=<code>   # required to register DOCTOR accounts

# train + evaluate the model (first run only)
python ml/train.py
python ml/evaluate.py

# start the API on http://127.0.0.1:8000
python -m uvicorn backend.main:app --port 8000
```

Interactive API docs: `http://127.0.0.1:8000/docs`

On startup the app creates any missing tables and runs **safe migrations**
(e.g. adding `users.role` to an existing 3.0 database — no data loss).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxies /api -> port 8000)
```

### 3. Run the tests

```bash
venv/Scripts/python -m pytest tests/ -q        # 116 passed
cd frontend && npm run build                   # production build check
```

### 4. First admin & doctor

1. Register a normal account, then call `POST /auth/bootstrap-admin` with that
   account's token — allowed only while the platform has no admin.
2. As admin, create a doctor via **Admin → Users** (or share the
   `DOCTOR_INVITE_CODE` for self-registration), then grant patient access via
   **Admin → Doctors**.

---

## 🧭 Demonstration workflow (viva-ready)

1. **Patient** registers (PATIENT) → dashboard shows live, real statistics.
2. **Symptom Checker**: type *"I have been having fever, headache and body pain
   for two days but no cough."* — or dictate it with **voice input** (editable
   transcript, same NLP pipeline).
3. **Identify symptoms** → NLP extracts `fever, headache, body ache`, excludes
   the negated `cough`, notes duration; submit → five agents run; the model
   returns condition, confidence and alternatives.
4. **"Why did the system produce this assessment?"** — feature-based
   explanation from the real model; rate the assessment with feedback.
5. **Monitoring**: record BP 185/115 → the Monitoring Agent flags it URGENT and
   creates critical alerts → **Alerts** page shows them with safe, non-diagnostic
   guidance; acknowledge/resolve.
6. **Health Timeline** shows every real event; **Health Summary** aggregates
   assessments, common symptoms, monitoring and alerts.
7. **Doctor** (assigned by admin) opens the patient chart, reviews the AI
   assessment, adds a follow-up note, marks it REVIEWED — the ML output itself
   stays read-only.
8. **Reports** → generate the advanced report and download the PDF
   (explainability, monitoring, alerts, doctor review, model version included).
9. **Admin** console: real overview stats, audit trail of everything that just
   happened, Model Lab with the five-model comparison and version registry,
   per-day analytics.

---

## 🔒 Security notes

* bcrypt password hashing; JWT bearer sessions; secrets in `backend/.env`.
* Role checks re-read the database on every request — frontend guards are UX only.
* Patient data is owner-scoped; doctors need explicit assignments; all clinical
  access is audited.
* Audit logs sanitize metadata against a secret blocklist; logs survive account deletion.
* Global exception handlers return human-readable errors, never stack traces.
* No fabricated data anywhere: monitoring values are patient-entered, metrics
  come from stored artifacts, empty platforms show honest empty states.

## ⚖️ License

MIT — see [LICENSE](LICENSE).
