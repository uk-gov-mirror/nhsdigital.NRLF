#!/bin/bash
# User data script to configure the bastion host on launch
set -o errexit -o nounset -o pipefail

ASDF_VERSION="v0.18.0"

sudo apt update && \
    sudo apt upgrade -y && \
    sudo apt install -y \
        git \
        jq \
        wget \
        build-essential \
        unzip \
        gnupg \
        libbz2-dev \
        libffi-dev \
        liblzma-dev \
        libncurses-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        libxml2-dev \
        libxmlsec1-dev \
        llvm \
        lsb-release \
        python3 \
        tar \
        tk-dev \
        xz-utils \
        zip \
        zlib1g-dev && \
    sudo apt clean -y && rm -rf /var/lib/apt/lists/*

# Create nrlf_ops user
sudo adduser --disabled-password --gecos "" nrlf_ops
sudo -u nrlf_ops echo 'export PATH="${PATH}:${HOME}/.asdf/shims"' >> /home/nrlf_ops/.bashrc
sudo -u nrlf_ops sh -c 'mkdir /home/nrlf_ops/.aws && echo "
[default]
region = eu-west-2
output = json
" >> /home/nrlf_ops/.aws/config'

# Install ASDF
wget https://github.com/asdf-vm/asdf/releases/download/${ASDF_VERSION}/asdf-${ASDF_VERSION}-linux-amd64.tar.gz -O asdf.tar.gz && \
    tar -xzf asdf.tar.gz && \
    mv asdf /usr/bin/asdf && \
    chmod 755 /usr/bin/asdf && \
    rm asdf.tar.gz

# Clone NRLF into nrlf_ops home directory
sudo -u nrlf_ops git clone https://github.com/NHSDigital/NRLF.git /home/nrlf_ops/NRLF
