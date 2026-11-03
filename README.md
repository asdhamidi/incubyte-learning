# Incubyte Learning

Welcome to my **Incubyte Centre of Excellence (CoE) learning plan**. This repository is a structured, day-by-day vault of my learning, notes, and submissions.

## Curriculum

| Day | Day Topic | Starting File |
| --- | --- | --- |
| 1 | Incubyte Culture, Ways of Working & Setting Up to Build | [Day 1](./part1/day-1-dora-pods-values.md) |
| 2 | SQL Precision for Pipelines | [Day 2](./part1/day-2-sql-with-precision.md) |
| 3 | Azure Data Services | [Day 3](./part1/day-3-azure-data-services.md) |
| 4 | Azure Data Factory In Depth | [Day 4](./part1/day-4-azure-data-factory-in-depth.md) |
| 5 | Testing Data Pipelines | [Day 5](./part1/day-5-testing-data-pipelines.md) |
| 6 | Modelling Layers, Single Source of Truth & Data Quality | [Day 6](./part1/day-6-modelling-layers-single-source-of-truth-and-data-quality.md) |
| 7 | CI/CD & Git for Data | [Day 7](./part1/day-7-ci-cd-git-for-data.md) |

## Repository Structure

```text
.
├── README.md                              # You are here
├── ci.py                                  # CI entry point, same checks locally and on GitHub
├── requirements.txt                       # Pinned versions used by CI
├── .github/workflows/ci.yml               # GitHub Actions workflow
├── part1/                                 # Part 1 learning material (notes)
│   ├── day-1-dora-pods-values.md
│   ├── day-2-sql-with-precision.md
│   ├── day-3-azure-data-services.md
│   ├── day-4-azure-data-factory-in-depth.md
│   ├── day-5-testing-data-pipelines.md
│   ├── day-6-modelling-layers-single-source-of-truth-and-data-quality.md
│   └── day-7-ci-cd-git-for-data.md
├── assets/                                # Screenshots used in the notes
│   ├── day4/
│   └── day7/
└── code/                                  # Hands-on exercises
    └── part1/
        ├── day1/                          # Record cleaner (Python)
        │   ├── README.md
        │   ├── main.py
        │   ├── pyproject.toml
        │   ├── reflection.md
        │   └── tests/
        │       └── test_record_cleaner.py
        ├── day2/                          # Incremental MERGE in DuckDB (SQL + Python)
        │   ├── README.md
        │   ├── pipeline.py
        │   ├── merge_and_idempotency.py
        │   ├── union.py
        │   ├── pyproject.toml
        │   ├── reflection.md
        │   ├── sql/
        │   │   ├── 01_setup.sql
        │   │   ├── 02_merge.sql
        │   │   ├── 03_idempotency_check.sql
        │   │   └── 04_union_vs_union_all.sql
        │   └── tests/
        │       ├── conftest.py
        │       ├── test_orders_data.py
        │       └── test_pipeline.py
        ├── day5/                          # Testing a data pipeline (Python)
        │   ├── README.md
        │   ├── data_checks.py
        │   ├── flatten_orders.py
        │   ├── exercise1.py
        │   ├── demonstration.py
        │   ├── pyproject.toml
        │   ├── sample_orders/             # 10 sample order JSON files
        │   └── tests/
        │       ├── test_data.py
        │       ├── test_exercise1.py
        │       └── test_validator.py
        ├── day6/                          # Layers, one source of truth, incident trace (DuckDB)
        │   ├── README.md
        │   ├── pyproject.toml
        │   ├── practice/
        │   │   └── practice.py
        │   └── exercise/
        │       ├── incident_setup.py
        │       ├── explore.py
        │       ├── message_to_client.md
        │       └── postmortem.md
        └── day7/                          # Review exercise
            ├── README.md
            └── exercise-1/
                ├── pr-to-review.md
                └── review.md
```
