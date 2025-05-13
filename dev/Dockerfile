FROM python:3.12

# 安装必要的工具和SSH服务
RUN apt-get update && apt-get install -y \
    openssh-server \
    vim \
    git \
    curl \
    wget \
    iputils-ping \
    net-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 配置SSH服务
RUN mkdir /var/run/sshd
RUN echo 'root:password' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH登录修复
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

# 创建工作目录
RUN mkdir -p /workspace
WORKDIR /workspace

# 安装Python开发工具
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ \
    ipython \
    pytest \
    flake8 \
    black \
    mypy \
    isort \
    pylint

# 暴露SSH端口
EXPOSE 22

# 启动SSH服务
CMD ["/usr/sbin/sshd", "-D"] 