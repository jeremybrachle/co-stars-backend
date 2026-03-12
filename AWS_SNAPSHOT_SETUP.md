# AWS Snapshot Setup

This guide covers the one-time AWS and GitHub setup needed to publish `frontend-manifest.json` and `frontend-snapshot.json` to S3 from GitHub Actions.

It assumes you already have the snapshot workflow in `.github/workflows/snapshot-deploy.yml` and that you want snapshot publishing to run on git pushes for now, with manual workflow dispatch still available once GitHub exposes it in the Actions tab.

## What Gets Deployed

The workflow exports and uploads two files:

- `frontend-manifest.json`
- `frontend-snapshot.json`

Recommended S3 object layout:

```text
s3://<bucket>/co-stars/prod/frontend-manifest.json
s3://<bucket>/co-stars/prod/frontend-snapshot.json
```

If you serve the bucket through CloudFront, the public URLs would typically be:

```text
https://<cloudfront-domain>/co-stars/prod/frontend-manifest.json
https://<cloudfront-domain>/co-stars/prod/frontend-snapshot.json
```

## Step 1: Choose The S3 Location

Decide where these files should live.

You have two common options:

1. Use the same S3 bucket as the frontend build.
2. Use a separate S3 bucket just for snapshot data.

The simplest setup is usually the same bucket, with a separate prefix such as `co-stars/prod/`.

## Step 2: Confirm CloudFront Routing

If the frontend is already served through CloudFront, confirm that requests for the snapshot paths will reach the S3 bucket.

Examples:

```text
/co-stars/prod/frontend-manifest.json
/co-stars/prod/frontend-snapshot.json
```

If the same distribution already fronts the same S3 bucket, you may not need to change anything.

## Step 3: Confirm Or Create GitHub OIDC In AWS

GitHub Actions should assume an AWS IAM role using OIDC rather than static AWS access keys.

If your frontend deploy already uses this pattern, the OIDC provider may already exist.

In AWS IAM, confirm there is an identity provider for:

```text
token.actions.githubusercontent.com
```

If not, create it with:

- Provider URL: `https://token.actions.githubusercontent.com`
- Audience: `sts.amazonaws.com`

## Step 4: Create Or Reuse An IAM Role For GitHub Actions

You can either:

1. Reuse the same role the frontend deploy uses.
2. Create a dedicated role for snapshot publishing.

If you reuse the frontend role, make sure it has permission to write the snapshot files under your chosen prefix.

### Trust Policy

Use a trust policy like this, replacing `<ACCOUNT_ID>`, `<OWNER>`, and `<REPO>`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:<OWNER>/<REPO>:*"
        }
      }
    }
  ]
}
```

That allows workflows in this repository to assume the role.

### Permissions Policy

Attach a policy like this, replacing the bucket name and prefix:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListBucketForSnapshotPrefix",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::<bucket>",
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "co-stars/prod/*"
          ]
        }
      }
    },
    {
      "Sid": "WriteSnapshotObjects",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::<bucket>/co-stars/prod/*"
      ]
    },
    {
      "Sid": "InvalidateCloudFront",
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation"
      ],
      "Resource": "*"
    }
  ]
}
```

If you do not want CloudFront invalidation yet, remove the `InvalidateCloudFront` statement.

## Step 5: Collect The AWS Values You Need

After the IAM role and S3 destination exist, collect these values:

- AWS region
- IAM role ARN
- S3 bucket name
- CloudFront distribution ID if you want invalidation
- CloudFront public base URL if you want absolute URLs in the workflow summary and manifest

Example:

```text
AWS_REGION=us-east-1
AWS_ROLE_ARN=arn:aws:iam::123456789012:role/github-co-stars-snapshot-deploy
SNAPSHOT_S3_BUCKET=my-frontend-bucket
SNAPSHOT_MAIN_PREFIX=co-stars/prod
CLOUDFRONT_DISTRIBUTION_ID=E123ABC456XYZ
SNAPSHOT_BASE_URL=https://d111111abcdef8.cloudfront.net
```

## Step 6: Add GitHub Repository Variables

In GitHub, open:

```text
Settings -> Secrets and variables -> Actions -> Variables
```

Create these repository variables:

- `AWS_REGION`
- `AWS_ROLE_ARN`
- `SNAPSHOT_S3_BUCKET`

Recommended:

- `SNAPSHOT_MAIN_PREFIX`
- `CLOUDFRONT_DISTRIBUTION_ID`
- `SNAPSHOT_BASE_URL`

Suggested values:

```text
AWS_REGION=us-east-1
AWS_ROLE_ARN=arn:aws:iam::123456789012:role/github-co-stars-snapshot-deploy
SNAPSHOT_S3_BUCKET=my-frontend-bucket
SNAPSHOT_MAIN_PREFIX=co-stars/prod
CLOUDFRONT_DISTRIBUTION_ID=E123ABC456XYZ
SNAPSHOT_BASE_URL=https://d111111abcdef8.cloudfront.net
```

## Step 7: Commit And Push The Backend Changes

Commit the snapshot workflow and docs to your branch and push them to GitHub.

The workflow currently runs on:

- pushes to any branch
- manual `workflow_dispatch`

## Step 8: Trigger The First Deployment

Push a commit to your branch to trigger the workflow, or run `Snapshot Deploy` manually from the Actions tab when the manual trigger is available.

### Manual Workflow Inputs

The manual `workflow_dispatch` path now supports these inputs:

- `git_ref`
  - branch, tag, or ref to deploy
- `deploy_prefix`
  - optional override for the S3 key prefix
- `snapshot_base_url`
  - optional override for the public manifest and snapshot base URL
- `publish_to_s3`
  - if `false`, the workflow only exports files and uploads the GitHub artifact
- `invalidate_cloudfront`
  - if `true`, invalidates CloudFront after publish when a distribution ID is configured

Useful examples:

1. Export only from `main` without publishing to AWS.
2. Publish a branch to the normal production prefix.
3. Publish a branch to a temporary prefix such as `co-stars/test-run`.

Example manual run values:

```text
git_ref=main
deploy_prefix=co-stars/prod
snapshot_base_url=https://d111111abcdef8.cloudfront.net
publish_to_s3=true
invalidate_cloudfront=true
```

## Step 9: Verify The Files In S3

Check that these objects exist:

```text
s3://<bucket>/co-stars/prod/frontend-manifest.json
s3://<bucket>/co-stars/prod/frontend-snapshot.json
```

If you use CloudFront, verify the public URLs load successfully in a browser.

## Step 10: Point The Frontend At The Manifest URL

Once the files are live, configure the frontend to fetch the manifest from the deployed location.

Example:

```text
https://<cloudfront-domain>/co-stars/prod/frontend-manifest.json
```

The manifest then points the frontend at `frontend-snapshot.json`.

## Frontend Handoff

These are the concrete values and assumptions the frontend team needs from this backend setup.

### Stable API Snapshot Entry Point

The API snapshot manifest endpoint is:

```text
/api/export/frontend-manifest
```

That manifest includes:

- `version`
- `source_updated_at`
- `actor_count`
- `movie_count`
- `relationship_count`
- `level_count`
- `recommended_refresh_interval_hours`
- `snapshot_endpoint`

The API manifest's `snapshot_endpoint` may be relative. The frontend should resolve it relative to the API base URL.

### Stable Hosted Snapshot Entry Point

The hosted manifest URL should be treated as the frontend's build-time entry point.

Expected shape:

```text
https://<cloudfront-domain>/co-stars/prod/frontend-manifest.json
```

The hosted manifest's `snapshot_endpoint` may be either:

1. a relative path such as `frontend-snapshot.json`
2. an absolute URL

The frontend should support both.

### Build-Time Frontend Config

Once the public manifest URL is known, the frontend should set:

```text
VITE_SNAPSHOT_MANIFEST_URL=https://<cloudfront-domain>/co-stars/prod/frontend-manifest.json
```

If you later introduce per-environment prefixes, this value can vary by environment. Right now the backend workflow is configured for one stable published path.

### Runtime Behavior Assumptions

This backend setup is compatible with a frontend that:

- fetches the API manifest only when the user explicitly requests API snapshot refresh
- fetches the hosted manifest only when the user explicitly requests hosted snapshot refresh
- resolves `snapshot_endpoint` from the manifest rather than hardcoding the snapshot URL
- stores the loaded snapshot client-side and reuses it until manually replaced or cleared

### CORS Expectations

If the frontend fetches the hosted manifest and snapshot from the same CloudFront origin that serves the frontend, no browser CORS change is usually required.

If the hosted manifest or snapshot is served cross-origin, allow browser `GET` requests from the frontend origin.

For API manifest access, the FastAPI app already controls CORS via `ALLOWED_ORIGINS`.

### Final Values The Frontend Team Needs

Before the frontend can wire production hosted snapshot refresh, provide them with:

1. the exact public manifest URL
2. the API base URL
3. confirmation whether the hosted manifest uses a relative or absolute `snapshot_endpoint`
4. the intended refresh cadence represented by `recommended_refresh_interval_hours`

## Troubleshooting

### Access denied when configuring AWS credentials

Usually means one of these is wrong:

- the IAM role trust policy does not match the repo
- the GitHub variable `AWS_ROLE_ARN` is wrong
- the repository is not allowed by the OIDC trust condition

### Access denied when uploading to S3

Usually means the role is assumed correctly, but the policy does not allow the bucket or prefix.

Check:

- bucket name
- prefix path
- `s3:PutObject`
- `s3:ListBucket`

### CloudFront still serves stale files

Check:

- `CLOUDFRONT_DISTRIBUTION_ID` is correct
- the role allows `cloudfront:CreateInvalidation`
- the invalidation completed successfully in the workflow logs

### Pull request run does not deploy

This workflow no longer runs automatically on pull requests.

Use the manual Actions-tab run instead.