# AI Resume Screening Assistant

An evidence-first recruiter assistant that compares resumes with job requirements, distinguishes claimed skills from demonstrated experience, exposes uncertainty, and generates targeted interview questions.

## Project status

This repository contains the shared foundation for the hackathon. Feature work should be completed on task-specific branches and merged through pull requests.

## Repository layout

```text
app/                 User interface and application entry points
src/models/          Domain and validation schemas
src/parsers/         Resume and job-description parsing
src/prompts/         Versioned LLM prompts
src/services/        Analysis, scoring, PII, and LLM services
src/database/        Persistence and repositories
src/utils/           Shared utilities
tests/               Unit and integration tests
sample_data/         Synthetic demonstration data
docs/                BRD, HLD, diagrams, and demo documentation
scripts/             Development and utility scripts
```

See [plan.md](plan.md) for the hackathon implementation plan and [CLAUDE.md](CLAUDE.md) for architecture and contribution rules.

See [docs/IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md) for the detailed backend architecture, libraries, analysis workflow, scoring model, database schema, API contracts, privacy controls, and agentic artificial intelligence assessment.

## Run the application

```bash
pip install -e '.[dev]'
uvicorn app.api:app --reload
```

In a second terminal:

```bash
streamlit run app/main.py
```

FastAPI serves the analysis and persistence API on port 8000. Streamlit serves
the recruiter dashboard on port 8501 and calls FastAPI through `BACKEND_URL`.

## Explainability

The language model only classifies each requirement and quotes evidence; the
score is a weighted sum calculated in `src/services/scoring_service.py`. That
makes every explanation below exact and reproducible, with no extra model calls.
Each one is a tab on the candidate report.

| Report feature | Question it answers | Explainable AI technique |
| --- | --- | --- |
| Why this score: per-requirement point chart | Why did this candidate get this number? | Local additive feature attribution. The score is linear, so the attribution is exact rather than approximated. |
| What-if simulator and fewest changes to the next fit band | What would have to be true for the result to change? | Counterfactual explanation. The suggested path is minimal in the number of changes. |
| Quote found / not found in resume | Can the model's cited evidence be trusted? | Faithfulness check. Each quote is matched against the resume text in code, independently of the model. |
| Compare: status heatmap and point differences | Why does one candidate rank above another? | Contrastive explanation. |
| How this score is calculated, and the JSON audit download | What rules does the system apply to everyone? | Global explanation and auditability. |

Limitations: the grounding check confirms that a quote appears in the resume,
not that the quote proves the requirement; ungrounded quotes are flagged for
review and do not change the score. Reports saved before this check was added
show no grounding badge.

## Contributing

Create a task-specific branch before editing, push only that branch, and open a pull request into `main`. Never commit API keys, real resumes, or candidate PII.
