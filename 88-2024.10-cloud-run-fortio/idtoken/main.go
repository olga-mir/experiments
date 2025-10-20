package main

import (
	"context"
	"fmt"
	"io"
	"os"

	"google.golang.org/api/idtoken"
)

func main() {
	audience := os.Getenv("TARGET_CLOUD_RUN_SERVICE")

	err := printAuthHeader(os.Stdout, audience)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	}
}

func printAuthHeader(w io.Writer, audience string) error {
	ctx := context.Background()

	// idtoken.NewTokenSource will use credentials in this order:
	// 1. GOOGLE_APPLICATION_CREDENTIALS (service account key file) - if set
	// 2. Application Default Credentials (ADC) - user credentials from gcloud auth application-default login
	// 3. Compute Engine metadata server - if running on GCE/Cloud Run
	tokenSource, err := idtoken.NewTokenSource(ctx, audience)
	if err != nil {
		return fmt.Errorf("idtoken.NewTokenSource: %w\n\nTo fix this, run one of:\n  1. gcloud auth application-default login (recommended for local dev)\n  2. export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa-key.json (less secure)", err)
	}
	token, err := tokenSource.Token()
	if err != nil {
		return fmt.Errorf("tokenSource.Token: %w", err)
	}
	fmt.Printf("Authorization: Bearer %s\n", token.AccessToken)

	return nil
}
