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

## Contributing

Create a task-specific branch before editing, push only that branch, and open a pull request into `main`. Never commit API keys, real resumes, or candidate PII.
