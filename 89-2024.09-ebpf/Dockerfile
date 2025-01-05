FROM ubuntu:24.10 AS builder

# Install minimal build dependencies
RUN apt-get update && apt-get install -y \
    clang \
    llvm \
    && rm -rf /var/lib/apt/lists/*

#    libelf-dev \
#    build-essential \

WORKDIR /app

# Copy vmlinux.h - this should be generated in Lima and copied into Docker context
#bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
COPY vmlinux.h /app/vmlinux.h
COPY hello.bpf.c .

# Build the eBPF program using CO-RE
RUN clang -O2 -g -target bpf \
    -D__TARGET_ARCH_x86 \
    -I. \
    -c hello.bpf.c -o hello.bpf.o

FROM ubuntu:24.10


RUN apt-get update && apt-get install -y \
    linux-tools-common \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/hello.bpf.o .

RUN echo '#!/bin/sh\nbpftool prog load hello.bpf.o /sys/fs/bpf/hello\ntail -f /sys/kernel/debug/tracing/trace_pipe' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

