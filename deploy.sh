#!/bin/bash
# Deploy CDE Matcher to Google App Engine

set -e

echo "🚀 Deploying CDE Matcher to Google App Engine"
echo "============================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK first."
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 | grep -q "@"; then
    echo "❌ Not authenticated with gcloud. Please run:"
    echo "   gcloud auth login"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project set. Please run:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Project: $PROJECT_ID"

# Check if required APIs are enabled
echo "🔍 Checking required APIs..."
required_apis=(
    "appengine.googleapis.com"
    "storage-api.googleapis.com"
    "storage-component.googleapis.com"
)

for api in "${required_apis[@]}"; do
    if ! gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo "❌ API $api is not enabled. Enabling now..."
        gcloud services enable "$api"
    else
        echo "✅ $api is enabled"
    fi
done

# Check if App Engine app exists
if ! gcloud app describe &>/dev/null; then
    echo "❓ App Engine app doesn't exist. Creating one..."
    echo "   Choose a region close to your users:"
    gcloud app create
fi

# Verify bucket exists
BUCKET_NAME=${GCS_BUCKET_NAME:-pathnd_cdes}
if ! gsutil ls "gs://$BUCKET_NAME" &>/dev/null; then
    echo "❌ GCS bucket 'gs://$BUCKET_NAME' not found or not accessible."
    echo "   Please create the bucket or check permissions:"
    echo "   gsutil mb gs://$BUCKET_NAME"
    echo "   gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME"
    exit 1
fi

echo "✅ Bucket gs://$BUCKET_NAME is accessible"

# Check bucket structure
echo "🔍 Checking bucket structure..."
required_paths=(
    "clinical_data/"
    "cdes/"
)

for path in "${required_paths[@]}"; do
    if gsutil ls "gs://$BUCKET_NAME/$path" &>/dev/null; then
        echo "✅ Found $path"
    else
        echo "⚠️  Creating $path"
        echo | gsutil cp - "gs://$BUCKET_NAME/${path}.keep"
    fi
done

# Deploy the application
echo "🚀 Deploying to App Engine..."
gcloud app deploy app.yaml --quiet

# Get the app URL
APP_URL=$(gcloud app describe --format="value(defaultHostname)")
echo ""
echo "🎉 Deployment successful!"
echo "📱 App URL: https://$APP_URL"
echo ""
echo "📊 Monitor logs: gcloud app logs tail -s default"
echo "🔧 Manage versions: gcloud app versions list"
echo ""
echo "📁 Make sure your bucket has the required structure:"
echo "   gs://$BUCKET_NAME/clinical_data/ - Your CSV clinical data files"
echo "   gs://$BUCKET_NAME/cdes/digipath_cdes.csv - Target CDE definitions"
echo "   gs://$BUCKET_NAME/output/ - Generated results (auto-created)"