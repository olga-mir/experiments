BUCKET=llm-models-369
KSA_NAME=default
NAMESPACE=ai-apps

gcloud storage buckets add-iam-policy-binding gs://$BUCKET \
    --role=roles/storage.objectViewer \
    --member=principal://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/${PROJECT_ID}.svc.id.goog/subject/ns/$NAMESPACE/sa/$KSA_NAME \
    --condition=None
