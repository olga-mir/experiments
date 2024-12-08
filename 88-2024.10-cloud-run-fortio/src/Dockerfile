FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o /cloudrun-explorer

FROM alpine:3.18
RUN apk add --no-cache iproute2
COPY --from=builder /cloudrun-explorer /cloudrun-explorer
ENTRYPOINT ["/cloudrun-explorer"]
CMD ["--port=8080"]