FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    clang \
    llvm \
    libelf-dev \
    gcc \
    make \
    iproute2 \
    bpfcc-tools \
    linux-headers-$(uname -r) \
    python3 \
    python3-pip

COPY hello_bpf.c /usr/src/hello_bpf.c
RUN clang -O2 -target bpf -c /usr/src/hello_bpf.c -o /usr/src/hello_bpf.o

CMD ["bpftool", "prog", "load", "/usr/src/hello_bpf.o", "/sys/fs/bpf/hello"]
