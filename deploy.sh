gcloud artifacts repositories create cde-matcher-repo \
  --repository-format=docker \
  --location=europe-west4 \
  --description="Container images for CDE Matcher"

gcloud builds submit --tag europe-west4-docker.pkg.dev/path-nd-main/cde-matcher-repo/cde-matcher:latest .

gcloud run deploy cde-matcher \
  --image=europe-west4-docker.pkg.dev/path-nd-main/cde-matcher-repo/cde-matcher:latest \
  --platform=managed \
  --region=europe-west4 \
  --allow-unauthenticated \
  --set-env-vars CDE_PASSWORD_HASH=<hash>