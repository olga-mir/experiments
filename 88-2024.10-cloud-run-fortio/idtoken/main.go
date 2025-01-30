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

	tokenSource, err := idtoken.NewTokenSource(ctx, audience)
	if err != nil {
		return fmt.Errorf("idtoken.NewTokenSource: %w", err)
	}
	token, err := tokenSource.Token()
	if err != nil {
		return fmt.Errorf("tokenSource.Token: %w", err)
	}
	fmt.Printf("Authorization: Bearer %s\n", token.AccessToken)

	return nil
}
