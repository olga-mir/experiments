# Authentication Setup for Cloud Run Service-to-Service Communication

## Overview

This document explains the authentication requirements for the Cloud Run Fortio load testing architecture.

## Two Types of Authentication

### 1. User → Cloud Run (Bastion → src-fortio)

**How it works:**
- You authenticate using your personal GCP account credentials
- Generate token: `task get-auth-token` (or `gcloud auth print-identity-token`)
- This works because you're logged in via `gcloud auth login`
- The token proves YOUR identity to Cloud Run's IAM invoker check

**No special setup needed** - just be logged into gcloud.

### 2. Cloud Run → Cloud Run (src-fortio → dest-fortio)

**How it works:**
- The src-fortio service runs as the `fortio@PROJECT.iam` service account
- It needs to prove its identity to dest-fortio to pass IAM invoker check
- This requires generating a JWT token signed by the service account
- To generate this token, you need the service account's private key

**Special setup required** - this is what `GOOGLE_APPLICATION_CREDENTIALS` is for.

## Why GOOGLE_APPLICATION_CREDENTIALS is Needed

The `idtoken` utility (in `idtoken/main.go`) uses the Google Cloud SDK to:
1. Read the service account key file from `GOOGLE_APPLICATION_CREDENTIALS`
2. Sign a JWT token with the service account's private key
3. Set the audience to the target Cloud Run service URL
4. This JWT proves the service account's identity to Cloud Run

**Without this key file**, the utility cannot impersonate the service account and generate valid tokens.

## Setup Steps

### Recommended Approach: Application Default Credentials (ADC)

**This is the secure, modern approach** that doesn't require service account keys:

```bash
# Step 1: Login with Application Default Credentials
gcloud auth application-default login

# Step 2: Make sure GOOGLE_APPLICATION_CREDENTIALS is NOT set
unset GOOGLE_APPLICATION_CREDENTIALS

# Step 3: Run the task
task print-authed-load-test-request
```

This approach:
- ✅ Uses your user credentials (no service account keys)
- ✅ More secure (credentials are managed by gcloud)
- ✅ Automatic token refresh
- ✅ No key files to manage or lose

### Alternative: Service Account Key (Less Secure)

⚠️ **Only use this if you specifically need to test service account impersonation:**

```bash
# Step 1: Create the Service Account Key
task setup-fortio-sa-key

# Step 2: Set the Environment Variable
export GOOGLE_APPLICATION_CREDENTIALS=~/fortio-sa-key.json

# Step 3: Run the task
task print-authed-load-test-request
```

**Security Note:** Service account keys are a security risk. Google recommends avoiding them when possible.

## How the Token Generation Works

When you run `task print-authed-load-test-request`:

1. The task runs: `cd idtoken && TARGET_CLOUD_RUN_SERVICE=<dest-url> go run main.go`
2. The Go program:
   - Reads `GOOGLE_APPLICATION_CREDENTIALS` to find the key file
   - Uses `google.golang.org/api/idtoken.NewTokenSource()` to create a token source
   - Generates a JWT with audience=dest-fortio URL
   - Outputs: `Authorization: Bearer <JWT_TOKEN>`
3. This header is substituted into the template and saved to `rendered.json`
4. The rendered config is copied to the bastion host

## Security Considerations

⚠️ **Service Account Keys are Sensitive**

- The key file contains the private key for the service account
- Anyone with this file can impersonate the service account
- In production, use Workload Identity Federation instead
- For this exploration/testing project, keys are acceptable
- Keep the key file secure and never commit it to git

## Troubleshooting

### Error: "idtoken: unsupported credentials type"

**Cause:** `GOOGLE_APPLICATION_CREDENTIALS` is either:
- Not set
- Points to a non-existent file
- Points to the wrong type of credentials (e.g., user credentials instead of SA key)

**Fix:** Run `task setup-fortio-sa-key` and set the environment variable.

### Error: "File not found"

**Cause:** The path in `GOOGLE_APPLICATION_CREDENTIALS` doesn't exist.

**Fix:**
```bash
ls -la $GOOGLE_APPLICATION_CREDENTIALS  # Check if file exists
task setup-fortio-sa-key                # Recreate if needed
```

### Key Already Exists

If you run `task setup-fortio-sa-key` and the key already exists, it will skip creation. To recreate:

```bash
rm ~/fortio-sa-key.json
task setup-fortio-sa-key
```

## Alternative: Runtime Token Generation

In production environments, Cloud Run services can generate their own tokens at runtime using:
- The metadata server
- Application Default Credentials (ADC)
- Workload Identity Federation

This avoids needing to manage service account key files. For this exploration project, we use key files for simplicity.

## Flow Diagram

```
You (laptop)
    |
    | gcloud auth login
    | (User credentials)
    |
    v
Bastion VM
    |
    | curl -H "Authorization: Bearer $USER_TOKEN"
    |
    v
src-fortio (Cloud Run)
    |
    | Generate JWT using fortio SA key
    | curl -H "Authorization: Bearer $SA_JWT_TOKEN"
    |
    v
dest-fortio (Cloud Run)
    |
    | IAM Invoker Check validates fortio SA
    |
    v
Load test execution
```
