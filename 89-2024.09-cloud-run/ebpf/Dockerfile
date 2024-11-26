FROM ubuntu:22.04

RUN echo uname -r
RUN echo uname -a

RUN apt-get update && apt-get install -y \
    clang \
    llvm \
    libelf-dev \
    gcc \
    make \
    iproute2 \
    bpfcc-tools \
    linux-headers-generic \
    python3 \
    python3-pip \
    linux-libc-dev

#RUN wget http://mirrors.kernel.org/ubuntu/pool/main/l/linux/linux-headers-$(uname -r)_all.deb && \
#    dpkg -i linux-headers-$(uname -r)_all.deb


# TODO - fix linux-headers
# linux-headers-$(uname -r) \

# sudo ln -s /usr/include/x86_64-linux-gnu/asm /usr/include/asm
# 
COPY hello_bpf.c /usr/src/hello_bpf.c
# RUN clang -O2 -target bpf -c /usr/src/hello_bpf.c -o /usr/src/hello_bpf.o
# 
# CMD ["bpftool", "prog", "load", "/usr/src/hello_bpf.o", "/sys/fs/bpf/hello"]
