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

COPY bpf/* ./bpf/
COPY go.* ./
COPY *.go ./

# First install bpf2go tool
RUN go install github.com/cilium/ebpf/cmd/bpf2go@latest

# Download dependencies and generate eBPF code with verbose output
RUN go mod download && \
    go generate -v ./... && \
    ls -la && \
    find . -name "*.go"

RUN CGO_ENABLED=0 go build -o loader

FROM ubuntu:24.10

WORKDIR /app
COPY --from=builder /app/loader .

ENTRYPOINT ["/app/loader"]