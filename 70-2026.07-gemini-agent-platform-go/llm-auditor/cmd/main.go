// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package main

import (
	"context"
	"log"
	"os"

	"google.golang.org/adk/v2/agent"
	"google.golang.org/adk/v2/cmd/launcher"
	"google.golang.org/adk/v2/cmd/launcher/agentengine"
	"google.golang.org/adk/v2/session"
	vertexaisession "google.golang.org/adk/v2/session/vertexai"

	"llmauditor/auditor"
)

func main() {
	ctx := context.Background()

	projectID := os.Getenv("GOOGLE_CLOUD_PROJECT")
	location := os.Getenv("GOOGLE_CLOUD_AGENT_ENGINE_LOCATION")
	if location == "" {
		location = "us-central1"
	}
	agentEngineID := os.Getenv("GOOGLE_CLOUD_AGENT_ENGINE_ID")

	llmAuditorAgent := auditor.GetLLmAuditorAgent(ctx, projectID, location)

	var sessionService session.Service
	if projectID != "" && location != "" && agentEngineID != "" {
		var err error
		sessionService, err = vertexaisession.NewSessionService(ctx, vertexaisession.VertexAIServiceConfig{
			ProjectID:       projectID,
			Location:        location,
			ReasoningEngine: agentEngineID,
		})
		if err != nil {
			log.Printf("Warning: VertexAI session service unavailable (%v), falling back to in-memory sessions", err)
			sessionService = session.InMemoryService()
		}
	} else {
		log.Println("Agent Engine env vars not set, using in-memory sessions")
		sessionService = session.InMemoryService()
	}

	config := &launcher.Config{
		SessionService: sessionService,
		AgentLoader:    agent.NewSingleLoader(llmAuditorAgent),
	}

	l := agentengine.NewLauncher(agentEngineID)
	if err := l.Execute(ctx, config, os.Args[1:]); err != nil {
		log.Fatalf("Run failed: %v\n\n%s", err, l.CommandLineSyntax())
	}
}
