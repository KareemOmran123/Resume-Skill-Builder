# CI/CD Guide

This repository uses GitHub Actions to keep pull requests testable, scan for common security issues, and provide an OIDC-ready staging deployment scaffold.

## Workflows

- `Pull Request CI` runs on pull requests to `main` and can be started manually with `workflow_dispatch`.
- `Staging Deployment` runs after pushes to `main` and can also be started manually.
- `Security Scanning` runs CodeQL and Trivy on pull requests, pushes to `main`, and manual runs.
- `AI Code Review` is a manual workflow for maintainers to run against a specific pull request.
- `Reusable Frontend CI`, `Reusable Backend CI`, and `Reusable Staging Deployment` are `workflow_call` workflows used by the top-level workflows.

## Pull Request Checks

Frontend CI uses Node.js 20 and 22:

- `npm ci`
- `npm run build`

Backend CI uses Python 3.10, 3.11, and 3.12:

- `python -m pip install -e backend`
- `python -m unittest discover -s backend/tests`

The live TheirStack integration test is skipped unless `THEIRSTACK_API_KEY` is present. Do not add that secret to default CI unless you intentionally want pull request checks to call the live API.

## Deployment Scaffold

The staging workflow gates deployment behind successful frontend and backend jobs with `needs`. The deploy job targets the `staging` GitHub Environment and requests `id-token: write`, so it is ready for cloud OIDC federation without long-lived cloud credentials.

The staging workflow uses path filters so documentation-only pushes to `main` do not trigger deployment. Pull request CI and security workflows intentionally run on every pull request to keep required branch protection checks predictable.

Replace the placeholder steps in `.github/workflows/reusable-staging-deploy.yml` with provider-specific deployment commands after the cloud identity is configured.

Recommended non-secret repository or environment variables:

- `CLOUD_PROVIDER`
- `CLOUD_REGION`
- `CLOUD_ROLE_TO_ASSUME`
- `CONTAINER_IMAGE`
- `STAGING_URL`

Use provider-native OIDC values instead of static cloud keys:

- AWS: role ARN for `AssumeRoleWithWebIdentity`
- Azure: client ID, tenant ID, subscription ID, and federated credential
- Google Cloud: workload identity provider and service account

## Required Secrets

No secrets are required for the default pull request CI, CodeQL, Trivy filesystem scan, or staging scaffold.

Set `CONTAINER_IMAGE` as a repository or environment variable to enable the optional Trivy container-image scan. If the image lives in a private registry, authenticate with OIDC or short-lived registry credentials in a dedicated step before the Trivy image scan.

Optional secrets:

- `OPENAI_API_KEY`: enables the manual `AI Code Review` workflow.
- `THEIRSTACK_API_KEY`: enables live TheirStack integration checks when deliberately supplied to a manual or scheduled backend workflow.
- `GEMINI_API_KEY`: reserve for a future Gemini review workflow.
- `ANTHROPIC_API_KEY`: reserve for a future Claude review workflow.

Never store secrets in repository files. Put sensitive values in GitHub repository or environment Secrets, and put non-sensitive deployment selectors in GitHub Variables.

## Branch Protection

Configure `main` with these branch protection rules:

- Require a pull request before merging.
- Require at least one approving review.
- Dismiss stale approvals when new commits are pushed.
- Require conversation resolution before merge.
- Require status checks to pass before merge.
- Require the `Pull Request CI` frontend, backend, and `CI complete` jobs.
- Require the `Security Scanning` CodeQL and Trivy filesystem jobs once the first successful run registers those checks.
- Block force pushes and branch deletion.
- Restrict who can push directly to `main`.

## Environments And Approvals

Create these GitHub Environments:

- `staging`: used by the current deployment scaffold. Add required reviewers if the team wants manual approval before deploys from `main`.
- `production`: reserve for a future production workflow. Require reviewers, deployment branches, and tighter secrets access before enabling it.

Environment-specific secrets should be scoped to the environment that needs them. Prefer OIDC federation for cloud access.

## AI Code Review

The safest first step is a manual AI review workflow rather than an automatic workflow on every pull request. Manual runs avoid exposing model-provider secrets to untrusted forked pull request code and keep the bot from creating noisy review traffic.

Current implementation:

1. Add `OPENAI_API_KEY` as a GitHub Actions secret.
2. Open Actions > AI Code Review > Run workflow.
3. Enter the pull request number.
4. The workflow checks out the PR merge commit, collects PR metadata and the patch, asks OpenAI Codex for an actionable review, and posts the result as a PR comment.

Gemini and Claude are good follow-up options once the team chooses a preferred provider. Keep them manual at first, pin their GitHub Actions to commit SHAs, and give them only the token permissions they need to read pull requests and write comments.

## Maintenance

Dependabot runs weekly for npm, pip, and GitHub Actions. Keep third-party Actions pinned to full commit SHAs; Dependabot can still propose updates while preserving reviewability.
