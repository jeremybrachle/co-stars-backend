# S3 Snapshot Deployment

This repository can publish static frontend data files instead of running the FastAPI app in AWS.

The static deployment flow exports two JSON files:

- `frontend-manifest.json`
- `frontend-snapshot.json`

The manifest includes a `snapshot_endpoint` that points at the deployed snapshot object, so the frontend can fetch the manifest first and then fetch the snapshot only when needed.

## GitHub Workflow

The workflow lives at `.github/workflows/snapshot-deploy.yml`.

It does the following:

1. checks out the repo
2. installs Python dependencies
3. seeds a deterministic SQLite fixture with `ci_seed_db.py`
4. exports static JSON assets
5. uploads the JSON files as a GitHub Actions artifact
6. deploys assets from pull requests in the same repository
7. deploys assets when code lands on `main`

Current deploy path for both pull requests and `main`:

```text
s3://<bucket>/<main-prefix>/frontend-manifest.json
s3://<bucket>/<main-prefix>/frontend-snapshot.json
```

This means a same-repo pull request can publish directly to the production snapshot location for testing. Later, you can split previews back out into a separate prefix if you want safer isolation.

## Required GitHub Repository Variables

Set these as repository or organization variables in GitHub:

- `AWS_REGION`
- `AWS_ROLE_ARN`
- `SNAPSHOT_S3_BUCKET`

Recommended optional variables:

- `SNAPSHOT_MAIN_PREFIX`
  - example: `co-stars/prod`
- `SNAPSHOT_BASE_URL`
  - example: `https://d111111abcdef8.cloudfront.net`
  - only needed if you want the workflow summary and manifest to contain absolute public URLs
- `CLOUDFRONT_DISTRIBUTION_ID`
  - optional; if set, the workflow invalidates `frontend-manifest.json` and `frontend-snapshot.json` after deploy

If `SNAPSHOT_BASE_URL` is not set, the manifest uses a relative `snapshot_endpoint` value of `frontend-snapshot.json`. That works well when the frontend fetches the manifest from the same deployed directory.

Example:

```text
AWS_REGION=us-east-1
AWS_ROLE_ARN=arn:aws:iam::123456789012:role/github-co-stars-snapshot-deploy
SNAPSHOT_S3_BUCKET=my-frontend-bucket
SNAPSHOT_MAIN_PREFIX=co-stars/prod
SNAPSHOT_BASE_URL=https://d111111abcdef8.cloudfront.net
```

With that configuration, pull requests and `main` both publish:

```text
https://d111111abcdef8.cloudfront.net/co-stars/prod/frontend-manifest.json
https://d111111abcdef8.cloudfront.net/co-stars/prod/frontend-snapshot.json
```

## AWS IAM Setup

Use GitHub Actions OIDC rather than static AWS keys.

The IAM role referenced by `AWS_ROLE_ARN` should trust GitHub's OIDC provider and allow:

- `s3:PutObject`
- `s3:DeleteObject`
- `s3:ListBucket`
- `cloudfront:CreateInvalidation` if you want invalidations

Scope S3 permissions to the bucket and key prefixes used by this workflow.

Typical trust policy conditions should restrict access to this repository. Because you want both pull requests and `main` to deploy, the easiest trust condition is repository-wide rather than branch-specific.

## Pull Request Behavior

The workflow deploys to S3 only for pull requests whose source branch lives in the same repository.

Forked pull requests still build the export and upload the artifact, but they do not assume AWS credentials or push to S3.

## Frontend Integration

Point the frontend manifest fetch at one of the deployed manifest URLs.

The exported manifest already contains the correct static `snapshot_endpoint`, so the frontend can use the same manifest-first logic described in `FRONTEND_DATA_SYNC.md`.

## Manual Local Export

You can generate the same static files locally with:

```bash
python ci_seed_db.py
python export_frontend_snapshot.py \
  --output dist/frontend-snapshot.json \
  --manifest-output dist/frontend-manifest.json
```

If you want the manifest to reference an absolute public URL instead, add `--snapshot-endpoint https://example.com/co-stars/frontend-snapshot.json`.

## Minimum AWS Inputs You Need

If you already have the frontend deploying from GitHub to AWS, you likely need only these pieces for the backend snapshot flow:

- an S3 bucket that the snapshot JSON should be written to
- the AWS region for that bucket
- an IAM role assumable by GitHub Actions through OIDC
- optional CloudFront distribution ID if you want cache invalidation

In the simplest case, you can reuse the same AWS account, the same GitHub OIDC provider, and often the same CloudFront distribution the frontend already uses.

The one extra decision is where the files should live in the bucket, for example:

```text
co-stars/prod/frontend-manifest.json
co-stars/prod/frontend-snapshot.json
```

If you want the snapshot workflow to match the frontend workflow's variable names exactly, you can set:

- `SNAPSHOT_S3_BUCKET` to the same value as the frontend's bucket
- `CLOUDFRONT_DISTRIBUTION_ID` to the same distribution ID the frontend already invalidates
- `AWS_ROLE_ARN` and `AWS_REGION` to the same values already used by the frontend deploy