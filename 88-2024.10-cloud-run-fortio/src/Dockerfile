FROM golang:1.23-alpine AS builder

WORKDIR /app

# Only need LDFLAGS as build arg now
ARG LDFLAGS

# Copy only go.mod and go.sum first to leverage Docker cache
COPY go.mod go.sum ./
RUN go mod download

# Copy the rest of the source code
COPY . .

# Build using TARGETPLATFORM vars provided by buildx
RUN CGO_ENABLED=0 go build -a -o info-utility -ldflags "${LDFLAGS}" main.go

# Final stage
FROM alpine:3.18

WORKDIR /
COPY --from=builder /app/info-utility .
ENTRYPOINT ["/info-utility"]

# FROM alpine:3.18
# RUN apk add --no-cache iproute2
# COPY --from=builder /cloudrun-explorer /cloudrun-explorer
# ENTRYPOINT ["/cloudrun-explorer"]
# CMD ["--port=8080"]