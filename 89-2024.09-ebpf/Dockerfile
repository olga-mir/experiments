FROM ubuntu:24.10 as builder

# Add build argument for kernel version
ARG KERNEL_VERSION

# Install build dependencies with specific kernel headers
RUN apt-get update && apt-get install -y \
    clang \
    llvm \
    libelf-dev \
    linux-headers-generic \
    linux-tools-generic \
    build-essential \
    bpftool \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY hello.bpf.c .

# Build the eBPF program with correct includes
RUN clang -O2 -g -target bpf \
    -I/usr/include/$(uname -m)-linux-gnu \
    -I/usr/include \
    -I/usr/src/linux-headers-${KERNEL_VERSION}/include \
    -I/usr/src/linux-headers-${KERNEL_VERSION}/arch/x86/include \
    -c hello.bpf.c -o hello.bpf.o

FROM ubuntu:24.10

RUN apt-get update && apt-get install -y \
    bpftool \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/hello.bpf.o .

RUN echo '#!/bin/sh\nbpftool prog load hello.bpf.o /sys/fs/bpf/hello\ntail -f /sys/kernel/debug/tracing/trace_pipe' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]