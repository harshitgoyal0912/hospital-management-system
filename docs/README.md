# Documentation

Start here. Documents are grouped by what you are trying to do, not by when they
were written.

## If you want to understand the system

| Document | What it covers |
|---|---|
| [architecture/ARCHITECTURE_AUDIT.md](architecture/ARCHITECTURE_AUDIT.md) | What the codebase actually does, verified against source rather than against its own documentation. Includes the dispatch-path findings that motivated the guarded execution layer. |
| [architecture/PHASE20.md](architecture/PHASE20.md) | The responsibility split — which layer owns authorization, validation, state, retrieval and observability — with the known gaps listed rather than shaded in. |
| [architecture/LANGCHAIN_LANGGRAPH_FEATURES_GUIDE.md](architecture/LANGCHAIN_LANGGRAPH_FEATURES_GUIDE.md) | Pre-existing notes on the LangChain/LangGraph agents. Parts describe workflows that are declared but unimplemented; the audit says which. |

## If you are running or deploying it

| Document | What it covers |
|---|---|
| [operations/CUTOVER.md](operations/CUTOVER.md) | Migrating from the legacy unauthenticated path to guarded execution. Read before setting `TOOL_EXECUTION_MODE`. |
| [operations/STAGING.md](operations/STAGING.md) | The four validation gates and what counts as passing each. |
| [deployment/COMPLETE-DEPLOYMENT-GUIDE.md](deployment/COMPLETE-DEPLOYMENT-GUIDE.md) | Full AWS deployment walkthrough. |
| [deployment/QUICK-DEPLOY.md](deployment/QUICK-DEPLOY.md) | The short version. |
| [deployment/CI-CD-SETUP.md](deployment/CI-CD-SETUP.md) | GitHub Actions pipeline. |
| [deployment/GITHUB-SECRETS-SETUP.md](deployment/GITHUB-SECRETS-SETUP.md) | Which secrets CI needs. |
| [deployment/ENVIRONMENT_VARIABLES_DEPLOYMENT.md](deployment/ENVIRONMENT_VARIABLES_DEPLOYMENT.md) | Environment variables by environment. |
| [deployment/DEPLOYMENT_CHECKLIST.md](deployment/DEPLOYMENT_CHECKLIST.md) | Pre-flight checks. |
| [deployment/DEPLOYMENT_EMAIL_CONFIG.md](deployment/DEPLOYMENT_EMAIL_CONFIG.md) | SMTP configuration. |
| [deployment/README-DOCKER.md](deployment/README-DOCKER.md) | Local Docker usage. |

## If you want the measurements

| Document | What it covers |
|---|---|
| [evaluation/RESULTS.md](evaluation/RESULTS.md) | Every measured number, with its denominator, commit and date. Blank rows are work not done — not placeholders to fill in by guesswork. |
| [evaluation/EVAL_PLAYBOOK.md](evaluation/EVAL_PLAYBOOK.md) | How the evaluation work was sequenced. |

Runnable harnesses live in [`../evals/`](../evals/), not here:

```
evals/
  datasets/   labelled cases and their generators
  runners/    the scripts that produce numbers
  results/    raw output, committed so figures can be recomputed
  redteam/    adversarial suites
```

## Feature guides

Written for the existing application rather than the agent layer.

- [guides/DISCHARGE_WORKFLOW_GUIDE.md](guides/DISCHARGE_WORKFLOW_GUIDE.md)
- [guides/PATIENT_ADMISSION_FORM_GUIDE.md](guides/PATIENT_ADMISSION_FORM_GUIDE.md)
- [guides/POST_ADMISSION_WORKFLOW_GUIDE.md](guides/POST_ADMISSION_WORKFLOW_GUIDE.md)
- [guides/FRONTEND-AI-TOOL-GUIDE.md](guides/FRONTEND-AI-TOOL-GUIDE.md)
- [guides/FRONTEND_AI_SYSTEM_PROMPT.md](guides/FRONTEND_AI_SYSTEM_PROMPT.md)
- [guides/QUICK-REFERENCE.md](guides/QUICK-REFERENCE.md)

## A note on the older documents

The deployment and feature guides predate the guarded execution work and were
written against the original architecture. Where they disagree with
`architecture/ARCHITECTURE_AUDIT.md`, the audit is the one that was checked
against the source.
