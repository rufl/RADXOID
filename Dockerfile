FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    bc bison build-essential ccache cpio curl device-tree-compiler \
    dosfstools flex g++-multilib gcc-multilib git gnupg gperf htop \
    lib32ncurses5-dev \
    lib32z-dev libgl1-mesa-dev liblz4-tool libssl-dev libxml2-utils \
    lzop mtools openjdk-8-jdk parted pigz python2 python3 python-is-python2 \
    rsync swig unzip u-boot-tools udev vim-common xsltproc zip zlib1g-dev \
    ca-certificates && rm -rf /var/lib/apt/lists/*

# The RK Android-11 BSP ships clang-3289846, linked against the NCurses 5 ABI.
# Ubuntu 20.04 only offers NCurses 6; install the buster compatibility libs.
RUN mkdir -p /tmp/ncurses5 && cd /tmp/ncurses5 && \
    base=http://archive.debian.org/debian/pool/main/n/ncurses && \
    debs="libtinfo5_6.1+20181013-2+deb10u2_amd64.deb libncurses5_6.1+20181013-2+deb10u2_amd64.deb" && \
    for deb in $debs; do curl -fsSL "$base/$deb" -o "$deb"; done && \
    echo "f9d7df1e86b5376c1ae102739d04a5605386b331c8bc47ea471facaec0f63ae2  libtinfo5_6.1+20181013-2+deb10u2_amd64.deb" | sha256sum -c && \
    echo "2bea6e3579991f70c47401a5d70e131b83c34c4c6eee4af478e9232042b1d288  libncurses5_6.1+20181013-2+deb10u2_amd64.deb" | sha256sum -c && \
    dpkg -i $debs && rm -rf /tmp/ncurses5

RUN mkdir -p /opt/bin && curl -fsSL \
    https://storage.googleapis.com/git-repo-downloads/repo \
    -o /opt/bin/repo && chmod 0755 /opt/bin/repo
ENV PATH=/opt/bin:${PATH}

WORKDIR /work
ENTRYPOINT ["/bin/bash"]
