FROM mcr.microsoft.com/devcontainers/cpp:ubuntu-22.04

WORKDIR /opt
COPY nvmefs/third-party/xnvme/toolbox ./toolbox
RUN bash -e ./toolbox/pkgs/ubuntu-jammy.sh

RUN mkdir -p /home/vscode/.tools/python && cd /home/vscode/.tools/python \
        && wget https://www.python.org/ftp/python/3.13.2/Python-3.13.2.tgz \ 
        && tar zxf Python-3.13.2.tgz \
        && cd Python-3.13.2 \
        && ./configure && make && make install

RUN rm -rf /usr/local/vcpkg

CMD ["bash"]