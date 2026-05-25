# Comprehensive Repository Ingestion & Contextual Summarization Strategy

## Why the previous output was insufficient
The prior report was a **catalog + shallow heuristics** (type, counts, first-line hints). Your requirement is stronger:
1. Ingest **full content** of every non-ignored file.
2. Produce **substantive summaries** of each file (not first-line proxies).
3. Explain **repo context**: where each file fits, who references it, and operational role.

## Target output schema (two columns)
Use one row per directory and one row per file.

| Path | Deep Summary |
|---|---|
| `dir_or_file_path` | Rich, content-based summary plus structural context and references. |

For files, the `Deep Summary` should include these sections:
- **Purpose**: what the file does.
- **Key Contents**: important entities (classes/functions/models/tables/variables/targets).
- **Dependency/Reference Context**: who imports/references/calls/executes it.
- **Runtime/Workflow Role**: build, CI, orchestration, tests, docs, infra, seed data, etc.
- **Change Risk Notes** (optional): blast-radius hints.

For directories, the `Deep Summary` should include:
- **Role in architecture**.
- **Contained modules and conventions**.
- **How it interacts with sibling/top-level directories**.

## High-fidelity generation method

### 1) Enumerate scope respecting Git ignore
Use Git-native listing to define exact scope:
- `git ls-files`
- `git ls-files --others --exclude-standard`

This gives tracked + untracked, non-ignored files only.

### 2) Build repository context graph
Create a lightweight graph to attach usage context to each file:
- **Import graph** for Python/JS/TS (AST where possible, regex fallback).
- **SQL lineage hints** (model refs, source refs, includes).
- **Build/orchestration edges** from Makefiles, CI YAML, Dockerfiles, Terraform, dbt config, Airflow/Dagster/etc.
- **Cross-file mentions** via `rg` for file path/module names.

Output per file:
- inbound references (who uses this file)
- outbound dependencies (what this file uses)
- pipeline stage tags (test/build/deploy/runtime/docs)

### 3) Full-content ingestion with chunking
For each text file:
- Read full file.
- Chunk by semantic boundaries (headers/functions/classes/sections) with overlap.
- Produce chunk summaries, then synthesize a file-level summary.

For large/binary files:
- Extract available metadata + format-aware parsers where possible.
- If binary non-parseable, explicitly record limitation and usage context from references.

### 4) File-type-aware summarizers
Use specialized prompts/parsers by extension:
- **Code (`.py`, `.js`, `.ts`, `.go`, etc.)**: APIs, control flow, side effects, entrypoints.
- **SQL**: produced datasets/tables, joins, filters, grain.
- **YAML/JSON/TOML**: config semantics, toggles, environments.
- **Markdown/docs**: audience, procedures, operational relevance.
- **Infra (`.tf`, Docker, CI)**: resources, deployment paths, trust boundaries.

### 5) Directory synthesis pass
After file summaries exist, synthesize directory summaries using:
- child file summaries,
- graph centrality (important files),
- recurring themes (tests, ingestion, transforms, deployment).

### 6) Quality gates (to avoid shallow output)
Require checks before publishing:
- 100% file coverage against Git-derived inventory.
- Every file summary includes at least: Purpose + Key Contents + Context.
- No summary generated solely from first line.
- Spot-check depth thresholds (minimum token/section requirements per file type).

## Practical implementation blueprint

### Artifacts to generate
1. `docs/repo_inventory_deep_summary.md` (human-readable two-column output).
2. `artifacts/repo_inventory_deep_summary.json` (machine-readable structured data).
3. `artifacts/repo_context_graph.json` (references/dependency edges).
4. `artifacts/coverage_report.json` (proof all files were ingested).

### Recommended pipeline stages
1. **discover**: build inventory.
2. **index**: parse references/imports/links.
3. **summarize-files**: deep per-file summaries from full content.
4. **summarize-dirs**: directory-level role/context synthesis.
5. **validate**: enforce coverage + depth constraints.
6. **render**: output Markdown (Format B grouped by top-level directory).

## Performance and scale strategy
- Process files in parallel workers (bounded concurrency).
- Cache content hashes so unchanged files are not re-summarized.
- Persist chunk summaries and graph edges for incremental runs.
- Support `--changed-since <git-ref>` mode for fast updates.

## What this improves over prior report
- Moves from **heuristic hints** to **full-content grounded summaries**.
- Adds **architectural context** (who uses what, where, and why).
- Produces **auditable artifacts** proving complete ingestion and coverage.
- Enables both **human review** and **automation** with JSON outputs.

## Suggested acceptance criteria
- Every non-ignored file appears exactly once in file rows.
- Every directory implied by those paths appears in directory rows.
- Each file summary references actual content sections and context edges.
- Coverage report shows `ingested_files == discovered_files`.
- Random sample audit confirms summaries are materially accurate.
