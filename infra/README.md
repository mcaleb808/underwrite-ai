# infra

Terraform stack for the api on Google Cloud Run, fronted by Vercel.

## What this provisions

- **Artifact Registry** — Docker repo for the api image, with a cleanup policy that keeps the last 3 tagged versions and deletes untagged images after 7 days.
- **Cloud Run service** — `min=0` / `max=3`, 1 vCPU / 2 GB, scale-to-zero. Pulls `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, and `SENDGRID_API_KEY` from Secret Manager.
- **Secret Manager** — three secrets, accessible only to the runtime service account.
- **Runtime service account** — least-privilege: `secretAccessor` on each secret, `logging.logWriter` on the project. Nothing else.
- **Workload Identity Federation** — lets a specific GitHub repo's workflow impersonate a deploy service account without a JSON key in the repo.

The Vercel side is configured manually (one-time): connect the repo on the Vercel dashboard and set `NEXT_PUBLIC_API_URL` to the Cloud Run URL printed by `terraform output api_url`.

## One-time bootstrap

The Terraform state lives in a GCS bucket that has to exist before `terraform init` can use it.

```bash
export PROJECT_ID=your-gcp-project-id
export REGION=us-central1
export STATE_BUCKET=underwrite-tf-state-${PROJECT_ID}

gcloud auth login
gcloud config set project ${PROJECT_ID}
gcloud services enable storage.googleapis.com cloudresourcemanager.googleapis.com

gcloud storage buckets create gs://${STATE_BUCKET} \
  --location=${REGION} \
  --uniform-bucket-level-access

gcloud storage buckets update gs://${STATE_BUCKET} --versioning

cp terraform.tfvars.example terraform.tfvars   # then edit project_id / github_owner / github_repo
echo "state_bucket = \"${STATE_BUCKET}\"" > .backend-config
```

## Apply

```bash
make init      # consumes .backend-config
make plan      # review
make apply
make output    # api_url, artifact_repository, workload_identity_provider, ...
```

After the first apply, populate the secret values once (Terraform creates the secrets but never writes their contents):

```bash
echo -n "${OPENROUTER_API_KEY}" | gcloud secrets versions add OPENROUTER_API_KEY_demo --data-file=-
echo -n "${OPENAI_API_KEY}"     | gcloud secrets versions add OPENAI_API_KEY_demo     --data-file=-
echo -n "${SENDGRID_API_KEY}"   | gcloud secrets versions add SENDGRID_API_KEY_demo   --data-file=-
```

## GitHub Actions setup

`terraform output` prints `workload_identity_provider` and `deploy_service_account`. Add them to the repo as secrets:

| Secret | Source |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `terraform output workload_identity_provider` |
| `GCP_DEPLOY_SERVICE_ACCOUNT` | `terraform output deploy_service_account` |
| `GCP_PROJECT_ID` | your project id |
| `GCP_REGION` | `us-central1` |
| `GCP_ARTIFACT_REPO` | `terraform output artifact_repository` |
| `GCP_CLOUD_RUN_SERVICE` | `underwrite-api-demo` |

Pushes to `main` then build, push to Artifact Registry, and roll a new Cloud Run revision.

## Tear down

`make destroy` removes everything except the state bucket (which is free at this scale). Cloud Run scaled to zero is already $0/day, so you only need to destroy if you want to wipe completely.

## Cost guardrails

- Cloud Run scaled to zero between requests = $0
- Artifact Registry: cleanup policy keeps 3 images (~30 MB each), well under the free tier
- Secret Manager: 3 secrets, free tier covers all access
- Logs: Cloud Logging free tier covers our volume
- Idle target: under $1/month
