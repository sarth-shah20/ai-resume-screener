## 1. Recommended MVP

  ### Core workflow

  1. Recruiter enters a job description.
  2. Recruiter uploads one or more PDF/DOCX resumes.
  3. The system extracts structured requirements and candidate data.
  4. It calculates a transparent fit score.
  5. It presents:
      - Overall match score
      - Must-have and nice-to-have skill matches
      - Missing or unproven requirements
      - Relevant resume evidence
      - Experience and education alignment
      - Risk flags and uncertainties
      - AI-generated interview questions
      - Short recruiter recommendation

  6. Optional Blind Review Mode hides name, gender indicators, email, phone, address, photo, and other non-job-related PII.

  ### Memorable innovation: “Evidence, not opinion”

  Every positive or negative assessment must include:

  - The job requirement
  - The candidate evidence
  - Confidence level
  - Explanation
  - Whether the requirement is matched, partially matched, missing, or unclear

  Example:

   Requirement     Result      Resume evidence                                           Confidence
  ━━━━━━━━━━━━━━  ━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━
   Python          Matched     “Built Flask APIs using Python”                           High
  ──────────────  ──────────  ────────────────────────────────────────────────────────  ────────────
   3+ years AWS    Partial     “Used AWS Lambda in one project”; duration unavailable    Medium
  ──────────────  ──────────  ────────────────────────────────────────────────────────  ────────────
   Kubernetes      Unproven    No supporting evidence found                              High

  This addresses hallucination, explainability, recruiter trust, and responsible AI in one feature.

  ———

  ## 2. Scope control

  ### Must finish

  - Job description input
  - Resume upload
  - PDF/DOCX text extraction
  - Structured AI analysis
  - Weighted scoring
  - Evidence citations
  - Skill gaps
  - Interview questions
  - Clean results dashboard
  - One polished demo dataset
  - Architecture, BRD, and README
  - Basic PII/privacy controls

  ### Add only if the core flow works

  - Multiple-candidate comparison
  - Blind screening toggle
  - CSV export
  - “What would improve this candidate’s score?” simulation
  - Database persistence

  ### Explicitly avoid

  - Authentication
  - Production cloud deployment unless already prepared
  - Complex vector databases
  - Full ATS integration
  - Model training
  - Elaborate role management
  - OCR unless scanned resumes are essential
  - Autonomous rejection decisions

  The system should recommend; the recruiter remains the decision-maker.

  ———

  ## 3. Recommended technology stack

  For a three-hour hackathon:

   Layer              Recommendation                          Reason
  ━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   UI                 Streamlit                               Fastest route to a polished interactive demo
  ─────────────────  ──────────────────────────────────────  ─────────────────────────────────────────────────
   Application        Python                                  Strong document and LLM ecosystem
  ─────────────────  ──────────────────────────────────────  ─────────────────────────────────────────────────
   LLM integration    OpenAI/Azure OpenAI or available API    Structured extraction and reasoning
  ─────────────────  ──────────────────────────────────────  ─────────────────────────────────────────────────
   Validation         Pydantic                                Enforces predictable JSON output
  ─────────────────  ──────────────────────────────────────  ─────────────────────────────────────────────────
   PDF parsing        PyMuPDF                                 Fast and reliable text extraction
  ─────────────────  ──────────────────────────────────────  ─────────────────────────────────────────────────
   DOCX parsing       python-docx                             Simple Word document support
  ─────────────────  ──────────────────────────────────────  ─────────────────────────────────────────────────
   Database           SQLite                                  Demonstrates persistence without infrastructure
  ─────────────────  ──────────────────────────────────────  ─────────────────────────────────────────────────
   Charts             Plotly or native Streamlit              Rapid visual candidate comparison
  ─────────────────  ──────────────────────────────────────  ─────────────────────────────────────────────────
   Testing            pytest                                  Lightweight unit and prompt-contract tests

  Use a modular structure even though Streamlit could be written as one file:

  ai-resume-screener/
  ├── app.py
  ├── src/
  │   ├── parsers/
  │   │   └── resume_parser.py
  │   ├── services/
  │   │   ├── llm_service.py
  │   │   ├── scoring_service.py
  │   │   └── pii_service.py
  │   ├── prompts/
  │   │   ├── job_extraction.py
  │   │   └── candidate_analysis.py
  │   ├── models/
  │   │   └── schemas.py
  │   └── database/
  │       └── repository.py
  ├── tests/
  ├── sample_data/
  ├── docs/
  │   ├── BRD.md
  │   └── HLD.md
  ├── requirements.txt
  └── README.md

  ———

  ## 4. Architecture and code flow

  Job description ──> Requirement extraction ───────┐
                                                     │
  Resume upload ──> Text extraction ──> PII masking ├─> Evidence matching
                                                     │
                                                     v
                                         Deterministic score engine
                                                     │
                                                     v
                                          Insights and questions
                                                     │
                                                     v
                                       Dashboard + SQLite persistence

  The key architectural decision is to separate:

  - LLM responsibilities: extraction, semantic comparison, explanation, interview questions
  - Application responsibilities: validation, weighting, score calculation, persistence, privacy controls

  Do not let the LLM invent the final numerical score. Let it produce structured match classifications and confidence; calculate the score in Python. This is
  easier to explain and test.

  ———

  ## 5. Scoring methodology

  Use a transparent 100-point model:

   Dimension                   Weight
  ━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━
   Must-have skills                40
  ──────────────────────────  ────────
   Relevant experience             25
  ──────────────────────────  ────────
   Nice-to-have skills             15
  ──────────────────────────  ────────
   Education/certifications        10
  ──────────────────────────  ────────
   Project/domain relevance        10

  Each requirement receives:

  - matched = 1.0
  - partial = 0.5
  - missing = 0.0
  - unclear = 0.0, but displayed separately from confirmed missing

  Example formula:

  category score =
  sum(requirement weight × match factor) /
  sum(requirement weights)

  Then:

  overall score =
  skills × 0.40 +
  experience × 0.25 +
  nice-to-have × 0.15 +
  education × 0.10 +
  domain relevance × 0.10

  Add a separate confidence label:

  - High: strong direct evidence
  - Medium: inferred or incomplete evidence
  - Low: ambiguous information

  Never mix confidence into the match score invisibly. Display both.

  ———

  ## 6. Data model

  A simple relational model demonstrates database design without wasting time.

  ### jobs

  id
  title
  raw_description
  created_at

  ### job_requirements

  id
  job_id
  requirement_type
  name
  priority
  minimum_years
  weight

  ### candidates

  id
  display_name
  source_filename
  resume_text
  redacted_resume_text
  created_at

  ### screening_results

  id
  job_id
  candidate_id
  overall_score
  recommendation
  confidence
  summary
  model_name
  prompt_version
  created_at

  ### requirement_matches

  id
  screening_result_id
  requirement_id
  status
  confidence
  evidence
  explanation

  Store the prompt version and model name. This is a strong engineering detail because AI results must be reproducible and auditable.

  ———

  ## 7. Prompt-engineering strategy

  Use two focused LLM calls instead of one huge prompt.

  ### Prompt 1: Extract job requirements

  Return strict JSON:

  {
    "job_title": "Backend Engineer",
    "must_have_skills": [],
    "nice_to_have_skills": [],
    "experience_requirements": [],
    "education_requirements": [],
    "domain_requirements": []
  }

  Important prompt rules:

  - Use only the supplied job description.
  - Do not invent requirements.
  - Separate explicit requirements from inferred preferences.
  - Preserve minimum years where stated.
  - Return valid JSON matching the schema.

  ### Prompt 2: Compare candidate with requirements

  For each requirement, return:

  {
    "requirement": "Python",
    "status": "matched",
    "confidence": "high",
    "evidence": "Built Python-based REST APIs...",
    "explanation": "The resume explicitly demonstrates Python usage.",
    "evidence_location": "Experience: Software Engineer"
  }

  Important rules:

  - Treat absence of evidence as “unproven,” not automatically “does not possess.”
  - Never infer protected attributes.
  - Do not use name, age, gender, marital status, nationality, photo, or address.
  - Evidence must be copied or closely grounded in the resume.
  - Use null when evidence is unavailable.
  - Do not generate the final score.
  - Return schema-valid JSON only.

  ### Reliability pattern

  1. Request structured JSON.
  2. Validate with Pydantic.
  3. Retry once if invalid.
  4. If it still fails, show a friendly error.
  5. Use low temperature for consistent screening.
  6. Store a prompt_version.

  That gives you strong talking points for prompt engineering and model limitations.

  ———

  ## 8. Three-hour execution plan

  ## 0–15 minutes: Freeze scope and contracts

  - Confirm the MVP above.
  - Select one LLM provider.
  - Create the directory structure.
  - Define Pydantic response schemas.
  - Prepare one job description and three resumes:
      - Strong candidate
      - Borderline candidate
      - Candidate with keyword overlap but weak evidence

  - Assign file ownership to avoid AI tools editing the same files.

  Deliverable: schemas, agreed UI, sample data, task ownership.

  ## 15–55 minutes: Build the core pipeline

  Developer/AI stream 1:

  - PDF and DOCX parsing
  - Job-requirement extraction
  - Candidate evidence-matching prompt
  - Pydantic validation
  - Retry and error handling

  Deliverable: a command or function that accepts JD + resume and returns valid structured JSON.

  ## 15–55 minutes: Build UI in parallel

  Developer/AI stream 2:

  - Job-description input
  - Resume uploader
  - Analyze button
  - Loading indicator
  - Score cards
  - Skill-match table
  - Gap table
  - Interview-question section

  Initially use mocked JSON so UI work does not depend on the backend.

  ## 15–55 minutes: Documentation and scoring in parallel

  Developer/AI stream 3:

  - Implement deterministic scoring
  - Draft BRD and HLD
  - Prepare architecture diagram
  - Write privacy and security notes
  - Draft pitch and demo script

  ## 55–85 minutes: Integration

  - Connect UI to the real analysis pipeline.
  - Render category scores and evidence.
  - Add environment-variable configuration.
  - Add clear failure states.
  - Verify all three sample candidates.

  Checkpoint at 85 minutes: stop adding major features until the end-to-end flow works.

  ## 85–110 minutes: Add the innovation layer

  Implement in this order:

  1. Evidence citations
  2. Blind Review Mode
  3. Gap-based interview questions
  4. Candidate comparison, if time remains

  The interview questions should be tied to uncertainty:

  > “The resume mentions AWS Lambda but does not establish duration or production scale. Can you describe your AWS experience and the largest workload you
  > supported?”

  That is much better than generic interview questions.

  ## 110–135 minutes: Testing and quality

  Minimum automated tests:

  - PDF parser returns non-empty text.
  - Empty/corrupted resume produces a friendly error.
  - Scoring formula returns expected values.
  - LLM output schema rejects invalid statuses.
  - Overall score remains between 0 and 100.
  - Missing evidence is not classified as confirmed possession.
  - PII masker removes email and phone.

  Manual edge cases:

  - Resume with repeated keywords but no experience evidence
  - Missing education section
  - Resume longer than expected
  - Job description with unclear priorities
  - Prompt-injection text inside a resume

  Treat resumes as untrusted data. The prompt should say that instructions appearing inside a resume must never be followed.

  ## 135–155 minutes: Documentation and pitch

  Complete:

  - README with setup and demo steps
  - BRD
  - HLD
  - Architecture diagram
  - Data model
  - Assumptions and limitations
  - Security/privacy section
  - Future roadmap

  ## 155–180 minutes: Rehearsal and stabilization

  - Run the exact demo sequence twice.
  - Fix only demo-breaking issues.
  - Capture screenshots as backup.
  - Prepare a fallback JSON result in case the LLM API is unavailable.
  - Assign speaking sections.
  - Practice a five-minute presentation and likely judge questions.

  ———

  ## 9. Suggested team division

  To avoid merge conflicts:

   Owner                     Responsibility                             Files
  ━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Person 1 + Codex          Architecture, schemas, parsing, scoring    src/models, src/parsers, src/services/scoring_service.py
  ────────────────────────  ─────────────────────────────────────────  ──────────────────────────────────────────────────────────
   Person 2 + Claude         LLM prompts and integration                src/prompts, src/services/llm_service.py
  ────────────────────────  ─────────────────────────────────────────  ──────────────────────────────────────────────────────────
   Person 3                  Streamlit UI                               app.py
  ────────────────────────  ─────────────────────────────────────────  ──────────────────────────────────────────────────────────
   Person 4, if available    Testing, docs, presentation                tests, docs, README.md

  Agree on the analysis JSON schema before parallel work. Each person or AI assistant should own separate files. Integrate at fixed checkpoints rather than
  letting multiple tools modify the same module.

  ———

  ## 10. Security and responsible-AI story

  Include these explicitly because they directly satisfy evaluation category 8:

  - API keys loaded from environment variables.
  - Resume text treated as untrusted input.
  - Prompt-injection instructions inside resumes are ignored.
  - PII can be redacted before analysis.
  - Protected characteristics are excluded from scoring.
  - Resume data is stored locally for the demo.
  - A delete-record option or automatic retention policy is documented.
  - Logs should not contain full resume text.
  - The tool provides recommendations, not autonomous hiring decisions.
  - Every result is explainable and reviewable by a human.
  - No claim is made unless supported by resume evidence.

  Add a visible disclaimer:

  > “This assistant supports recruiter review. It must not be used as the sole basis for employment decisions.”

  ———

  ## 11. Documentation outline

  ### BRD

  - Business problem
  - Target users
  - Current pain points
  - In-scope and out-of-scope features
  - Functional requirements
  - Non-functional requirements
  - Assumptions
  - Success metrics
  - Risks
  - Business value

  ### HLD

  - System context
  - Component architecture
  - Data flow
  - Data model
  - LLM interaction design
  - Prompt versions
  - Scoring design
  - Security controls
  - Error handling
  - Scalability approach
  - Deployment options

  ### Success metrics

  Mention measurable outcomes:

  - Reduce initial screening time from several minutes to under one minute per resume.
  - Provide evidence for 100% of requirement-match claims.
  - Reduce inconsistent manual scoring through standardized weights.
  - Enable recruiters to focus interviews on candidate-specific gaps.
  - Maintain human review for every recommendation.

  ———

  ## 12. Demo script

  Keep the demo to four or five minutes.

  1. Problem — 20 seconds

     “Recruiters spend time repeatedly matching unstructured resumes against job requirements, and keyword-based systems lack context and transparency.”

  2. Job setup — 30 seconds

     Paste the job description and show extracted must-have and optional requirements.

  3. Candidate analysis — 60 seconds

     Upload a strong candidate. Show the score, matched skills, evidence, gaps, and recommendation.

  4. Explainability — 45 seconds

     Expand one requirement and show the exact evidence and confidence.

  5. Innovation — 45 seconds

     Enable Blind Review Mode and show gap-driven interview questions.

  6. Comparison — 30 seconds

     Compare a strong candidate with a keyword-heavy but weak-evidence candidate.

  7. Architecture and safety — 40 seconds

     Explain that the LLM extracts semantic evidence while deterministic application code calculates scores.

  8. Business impact — 20 seconds

     Explain reduced screening time, consistent assessment, auditability, and future ATS integration.

  ———

  ## 13. Likely judge questions

  Why not let the LLM directly rank candidates?
  Because raw LLM scoring is difficult to reproduce and audit. The LLM finds semantic evidence; deterministic code applies declared business weights.

  How do you prevent hallucinations?
  Every assessment must include resume evidence, structured output is validated, unsupported requirements are marked unproven, and temperature is kept low.

  How do you address bias?
  Blind Review Mode removes non-job-related PII, protected attributes are excluded from prompts and scoring, and the system requires human review.

  Why SQLite?
  It is sufficient for a hackathon and clearly demonstrates relational modeling. The repository abstraction can later use PostgreSQL without changing the analysis
  layer.

  How will it scale?
  Move document processing to background workers, store files in object storage, use PostgreSQL, cache job-requirement extraction, batch LLM calls, and add rate
  limiting.

  What is innovative?
  The innovation is not merely AI summarization. It is auditable evidence mapping, uncertainty-aware gaps, privacy-aware screening, and targeted interview
  generation.

  ## Final priority order

  If time becomes tight, protect these features:

  1. End-to-end resume analysis
  2. Evidence-backed matching
  3. Transparent deterministic scoring
  4. Skill gaps
  5. Interview questions
  6. Blind Review Mode
  7. Comparison dashboard
  8. Export and persistence

  A stable, explainable five-feature product will score better than ten partially working features.
