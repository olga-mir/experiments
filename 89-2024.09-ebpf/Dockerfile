FROM golang:1.23 AS builder

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    clang \
    llvm \
    linux-headers-amd64 \
    linux-libc-dev \
    libbpf-dev \
    gcc-multilib \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for asm/types.h
RUN ln -s /usr/include/x86_64-linux-gnu/asm /usr/include/asm

WORKDIR /app

COPY go.* ./
COPY *.go ./
COPY hello.bpf.c ./

# Download dependencies and generate eBPF code
RUN go mod download && \
    go generate ./...

# Build the Go binary
RUN go build -o loader

FROM debian:bookworm-slim

WORKDIR /app
COPY --from=builder /app/loader .

ENTRYPOINT ["/app/loader"]