# Dokcerfile version: 250404 , Author: cddc
# 本Dockerfile框架适用于python项目，使用uv管理python环境

ARG BASE_IMAGE=cddc/app:latest
FROM ${BASE_IMAGE}

LABEL maintainer="cddc cddc@126.com"

# 更新系统软件包本地数据库和缓存，安装必要系统软件包，最后清除缓存
COPY packages.txt ./
RUN apt-get update && apt-get upgrade -y \
 && cat packages.txt | xargs apt-get install -y \
 && apt-get clean && rm -rf /var/lib/apt/lists/* 

# 安装uv环境管理工具
ENV XDG_BIN_HOME="/opt/uv"
ENV PATH="$XDG_BIN_HOME:$PATH"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

USER ubuntu

# 构建项目目录
ENV APP_DIR="/app" 
WORKDIR ${APP_DIR}

# 提前复制uv依赖关系文件（以ubuntu为文件属主）
COPY --chown=ubuntu:ubuntu ./pyproject.toml ./uv.lock ./
# 用uv恢复项目环境依赖包
RUN uv sync && uv clean

# 最佳实践：由.dockerignore文件指定排除项后，复制整个项目下的所有文件
COPY --chown=ubuntu:ubuntu . ./

CMD ["uv", "run", "bash", "./startup.sh"]
#CMD ["sleep", "infinity"]
