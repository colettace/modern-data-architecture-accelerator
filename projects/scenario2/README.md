# Scenario 2: Event-Driven Lakehouse Pipeline

This scenario provides an isolated project layout for a domain-specific ingestion and transformation pipeline using MDAA L3 constructs and Airflow orchestration.

## Architecture

Scenario 2 is designed as a modular lakehouse pattern:

- **Infra config** (`infra/`, `mdaa.yaml`, `roles.yaml`, `tags.yaml`, `config/environments/*.yaml`):
  - Defines reusable MDAA composition, IAM roles, and environment overlays.
  - Uses scenario-specific naming so resources remain isolated from other starter kits and blueprints.
- **Ingestion layer** (`src/ingestion/`):
  - Placeholder Python package for source extract/load logic.
- **Transformation layer** (`src/transformation/`):
  - Placeholder Python package for transformation and quality checks.
- **Orchestration** (`airflow/dags/`, `airflow/operators/`, `orchestration/`):
  - Airflow DAGs/operators coordinate ingest -> transform -> monitor workflow steps.
- **Monitoring** (`monitoring/`):
  - Dashboard/alarm definition placeholders for pipeline observability.

## Deploy Flow

1. **Set organization and account context**
   - Update `mdaa.yaml` and `config/environments/<env>.yaml` values.
2. **Validate composition**
   - Run MDAA list/synth from this directory to validate modules and config overlays.
3. **Deploy foundational modules**
   - Deploy IAM roles and project modules first.
4. **Deploy data processing modules**
   - Deploy ingestion and transformation modules.
5. **Enable orchestration and observability**
   - Register Airflow DAGs and apply monitoring assets.
6. **Smoke test**
   - Trigger a run and verify outputs in target catalog/buckets and dashboard metrics.

## Runbook

### Operational checks

- Confirm scheduler heartbeat and DAG status are healthy.
- Validate ingestion outputs landed in expected raw/staging path.
- Validate transformation outputs in curated path and row counts.
- Verify data quality / alarm thresholds are within expected bounds.

### Common incident actions

- **Ingestion failure**: inspect connector/auth configuration in `src/ingestion/` and Airflow task logs.
- **Transformation failure**: inspect Spark/Glue task output and transformation package behavior in `src/transformation/`.
- **Permission errors**: verify `roles.yaml` policy mappings and environment overlay principals.
- **Missing metrics/alerts**: validate assets in `monitoring/` and deployment status.

### Recovery pattern

1. Fix configuration/code.
2. Re-run failed Airflow task only.
3. If data is partially written, clean or quarantine intermediate outputs.
4. Backfill affected partitions/time window.
5. Confirm alarms return to normal.

## Directory Layout

```text
projects/scenario2/
├── README.md
├── mdaa.yaml
├── tags.yaml
├── roles.yaml
├── config/
│   └── environments/
│       ├── dev.yaml
│       ├── test.yaml
│       └── prod.yaml
├── infra/
├── orchestration/
├── airflow/
│   ├── dags/
│   └── operators/
├── src/
│   ├── ingestion/
│   └── transformation/
├── monitoring/
└── docs/
```
