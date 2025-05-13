# Python 3.12 远程开发环境

这是一个用于 PyCharm 远程开发的 Docker 环境，预装了 Python 3.12 和常用开发工具。

## 使用方法

### 1. 构建并启动环境

```bash
# 创建workspace目录（如果不存在）
mkdir -p workspace

# 使用docker-compose启动环境
docker-compose up -d
```

### 2. 在 PyCharm 中配置远程解释器

1. 打开 PyCharm，转到 `File > Settings > Project > Python Interpreter`
2. 点击齿轮图标，选择 `Add...`
3. 选择 `SSH Interpreter`
4. 填写以下信息：
   - Host: 服务器 IP 地址
   - Port: 2222（在 docker-compose.yml 中配置的端口）
   - Username: root
   - Password: password（在 Dockerfile 中设置的密码）
5. 设置解释器路径: `/usr/local/bin/python`

### 3. 安全提示

默认设置了简单密码"password"，**仅供开发环境使用**。如需在生产环境使用，请修改 Dockerfile 中的密码设置并重新构建镜像。

### 4. 自定义

- 可以在 Dockerfile 中添加更多 Python 包或系统工具
- 可以修改 docker-compose.yml 中的端口映射和卷挂载配置

## 目录结构

- `Dockerfile`: 定义 Python 开发环境
- `docker-compose.yml`: 定义服务配置
- `workspace/`: 工作目录，会挂载到容器内的/workspace
