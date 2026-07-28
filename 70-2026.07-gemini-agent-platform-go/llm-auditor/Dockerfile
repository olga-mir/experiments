FROM --platform=linux/amd64 golang:1.26-alpine AS builder
WORKDIR /app
COPY . .
RUN go mod tidy && \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o server ./cmd/

FROM --platform=linux/amd64 gcr.io/distroless/static-debian12
COPY --from=builder /app/server /server
EXPOSE 8080
CMD ["/server", "web", "agentengine"]
