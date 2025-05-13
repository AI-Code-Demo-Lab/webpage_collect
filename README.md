# 微信客服回调服务

这是一个专为企业微信客服打造的回调服务，用于处理客服消息并将文章保存到飞书多维表格中。本服务可以自动提取文章链接中的内容，使用 AI 技术生成合适的分类标签，并将整理好的信息保存到飞书表格中。

## 功能特点

- 接收并处理微信客服链接消息
- 自动抓取链接网页内容
- 使用 OpenAI API 自动生成分类标签
- 支持飞书多维表格存储和管理文章
- 提供 Docker 容器化部署方案

## 技术栈

- **后端框架**：FastAPI
- **服务器**：Uvicorn
- **AI 模型**：OpenAI API (GPT-4.1)
- **内容解析**：BeautifulSoup4
- **容器化**：Docker & Docker Compose
- **数据存储**：飞书多维表格

## 配置说明

本项目支持通过环境变量或.env 文件进行配置，主要配置项包括：

### 微信客服配置

```
WECHAT_TOKEN=你的微信Token
WECHAT_APP_ID=你的微信AppID
WECHAT_ENCODING_AES_KEY=你的微信消息加密密钥
WECHAT_SECRET=你的企业微信应用凭证密钥
```

### 飞书配置

```
FEISHU_APP_ID=你的飞书应用ID
FEISHU_APP_SECRET=你的飞书应用密钥
```

### OpenAI 配置

```
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=你的OpenAI API密钥
```

### 服务器配置

```
HOST=0.0.0.0
PORT=8080
```

## 部署指南

### 前置条件

- Docker 和 Docker Compose
- 企业微信客服账号和相关配置
- 飞书账号和已创建的多维表格
- OpenAI API 密钥

### 使用 Docker 部署

1. 克隆代码仓库

```bash
git clone <仓库地址>
cd webpage_collect
```

2. 配置环境变量

创建`.env`文件并填入必要的配置信息，或者直接在`docker-compose.yml`中修改。

3. 构建并启动服务

```bash
docker-compose up -d
```

4. 服务将在`http://你的服务器IP:3005`上运行

5. 在企业微信客服管理后台配置回调地址：`http://你的服务器IP:3005/wechat`

### 停止服务

```bash
docker-compose down
```

## 使用流程

1. 客户通过企业微信客服渠道发送文章链接
2. 系统自动接收并处理链接消息
3. 系统抓取链接内容并使用 AI 生成分类标签
4. 系统将标题、链接、描述、图片链接和分类标签存储到飞书多维表格
5. 系统回复客户"文章保存成功"的消息

## 本地开发

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 创建.env 文件并配置环境变量

3. 启动开发服务器

```bash
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8080
```

## 注意事项

- 目前仅支持处理链接类型的消息
- 飞书多维表格需要预先创建并设置好相应的字段
- OpenAI API 调用可能会产生费用，请注意控制用量
