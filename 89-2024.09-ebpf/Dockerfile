FROM ubuntu:24.10 AS builder

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    clang \
    llvm \
    linux-headers-generic \
    linux-libc-dev \
    libbpf-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY vmlinux.h /app/vmlinux.h
COPY hello.bpf.c .

RUN clang -O2 -g -target bpf \
    -D__TARGET_ARCH_x86 \
    -I. \
    -I/usr/include/x86_64-linux-gnu \
    -I/usr/include/bpf \
    -c hello.bpf.c -o hello.bpf.o

FROM ubuntu:24.10

WORKDIR /app
COPY --from=builder /app/hello.bpf.o .

CMD ["sleep", "infinity"]  # Replace with your actual command