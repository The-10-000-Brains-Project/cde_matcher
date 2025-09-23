# CDE Matcher - App Engine Deployment Guide

This guide walks you through deploying the CDE Matcher to Google App Engine.

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **gcloud CLI** installed and configured
3. **GCS bucket** `pathnd_cdes` with your data

## Quick Deployment

### 1. Set up Google Cloud

```bash
# Install gcloud CLI (if not already installed)
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Prepare your data in GCS

Your bucket should have this structure:
```
gs://pathnd_cdes/
├── clinical_data/           # Your CSV clinical data files
├── cdes/                   # Target CDE definitions
│   └── digipath_cdes.csv   # Required CDE file
└── output/                 # Generated results (auto-created)
```

Upload your files:
```bash
# Upload clinical data
gsutil cp your-clinical-data.csv gs://pathnd_cdes/clinical_data/

# Upload CDE definitions
gsutil cp digipath_cdes.csv gs://pathnd_cdes/cdes/
```

### 3. Deploy the application

```bash
# Run the deployment script
./deploy.sh
```

Or deploy manually:
```bash
# Enable required APIs
gcloud services enable appengine.googleapis.com storage-api.googleapis.com

# Create App Engine app (if needed)
gcloud app create

# Deploy
gcloud app deploy
```

## Configuration

### Environment Variables (app.yaml)

- `GCS_BUCKET_NAME`: Your GCS bucket name (default: `pathnd_cdes`)
- `STREAMLIT_*`: Streamlit server configuration

### Custom Bucket

To use a different bucket, edit `app.yaml`:
```yaml
env_variables:
  GCS_BUCKET_NAME: "your-custom-bucket"
```

## Monitoring

### View logs
```bash
gcloud app logs tail -s default
```

### Manage versions
```bash
gcloud app versions list
gcloud app versions delete OLD_VERSION
```

### Check status
```bash
gcloud app describe
```

## Troubleshooting

### Common Issues

1. **"Bucket not found"**
   - Verify bucket exists: `gsutil ls gs://pathnd_cdes`
   - Check permissions: Your App Engine service account needs Storage Object Viewer access

2. **"Permission denied"**
   - Enable required APIs: `gcloud services enable storage-api.googleapis.com`
   - Check IAM permissions for App Engine default service account

3. **"App won't start"**
   - Check logs: `gcloud app logs tail -s default`
   - Verify `digipath_cdes.csv` exists in `gs://pathnd_cdes/cdes/`

### Service Account Permissions

The App Engine default service account needs these roles:
- Storage Object Viewer (to read from GCS)
- Storage Object Creator (to write results)

```bash
# Get the service account email
PROJECT_ID=$(gcloud config get-value project)
SA_EMAIL="$PROJECT_ID@appspot.gserviceaccount.com"

# Grant necessary permissions
gsutil iam ch serviceAccount:$SA_EMAIL:objectViewer gs://pathnd_cdes
gsutil iam ch serviceAccount:$SA_EMAIL:objectCreator gs://pathnd_cdes
```

## Scaling & Performance

### Instance Configuration

Edit `app.yaml` to adjust resources:
```yaml
instance_class: F4  # F1, F2, F4, F4_1G
automatic_scaling:
  min_instances: 1
  max_instances: 20
```

### Cost Optimization

- Use `min_instances: 0` for low-traffic applications
- Monitor usage with Cloud Monitoring
- Set up billing alerts

## Security

### Data Access
- Files in GCS bucket are accessible to the application only
- No public access to uploaded data
- HTTPS enforced for all connections

### Updates
```bash
# Deploy new version
gcloud app deploy

# Route traffic gradually
gcloud app services set-traffic default --splits=v1=50,v2=50
```

## Next Steps

1. **Custom Domain**: Configure a custom domain in App Engine settings
2. **Monitoring**: Set up Cloud Monitoring alerts
3. **Backup**: Implement automated GCS bucket backups
4. **CI/CD**: Set up automated deployments with Cloud Build

For issues, check the [troubleshooting section](#troubleshooting) or review App Engine logs.