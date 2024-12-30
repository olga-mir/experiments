FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o /cloudrun-explorer
RUN CGO_ENABLED=0 GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH} go build -a -o info-utility -ldflags "${LDFLAGS}" main.go

FROM alpine:3.18
RUN apk add --no-cache iproute2
COPY --from=builder /cloudrun-explorer /cloudrun-explorer
ENTRYPOINT ["/cloudrun-explorer"]
CMD ["--port=8080"]