# Lifesign — User Status & Health Telemetry Server

轻量 HTTP 服务：接收手机端上报的**设备状态 + 健康数据**，并以
**MCP（Model Context Protocol）** 暴露给 AI Agent 读取。单进程、单端口。

## ✨ 特性

- 📱 **手机上报**：iOS 快捷指令 `POST /ingest` 推送电量/位置/网络/健康快照
- 🤖 **MCP 网关**：同一进程挂载 `/mcp`，Hermes 等 AI Agent 直接读取
- 🏗️ **单端口单进程**：上传 + 查询 + MCP 全部复用 8764，无二次 HTTP hop
- 🐳 **Docker 就绪**：GitHub Actions 自动构建镜像，1Panel 一键 Compose 部署

## 🏗️ 架构

```
手机 (iOS 快捷指令)
   │ POST https://<your-domain>/user-status/ingest   ← 仅上传经反代
   ▼
1Panel OpenResty (反向代理)
   │ proxy_pass → <host-ip>:8764/ingest
   ▼
┌──────────────────────────────┐
│ FastAPI + FastMCP 同一进程    │
│  (单端口 8764)               │
│                              │
│  POST /ingest   手机上传      │
│  GET  /query_all  agent读取  │
│  /mcp  MCP 网关 (同进程)      │
└──────┬───────────────────────┘
       │ 本机回环 http://127.0.0.1:8764/mcp
       ▼
   Hermes Agent (AI)
```

- **手机上传**：公网 HTTPS 经反代 → `8764/ingest`
- **AI 读取**：本机回环直连 `8764/mcp`（不经过公网）
- **共享内存**：MCP 工具直接读 `app.store`，无需序列化/二次请求

## 🔌 端点

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| `POST` | `/ingest` | Bearer 手机 key | 手机上报最新状态 |
| `GET` | `/query_all` | Bearer agent key | 返回完整快照 |
| `GET` | `/health` | 无 | 健康检查（Docker HEALTHCHECK 用） |
| `POST` | `/mcp` | 无（本机回环） | MCP streamable-http 端点 |

## 🔑 身份与配置

仅两个共享密钥做身份识别（身份标识，非字段级授权），均可用环境变量覆盖：

| 用途 | 环境变量 | 默认值（仅开发） | 端点 |
|------|----------|------------------|------|
| 手机 key | `USER_STATUS_PHONE_KEY` | `phone-secret-key-001` | `POST /ingest` |
| agent key | `USER_STATUS_AGENT_KEY` | `agent-read-secret-key-001` | `GET /query_all` |
| 监听端口 | `USER_STATUS_PORT` | `8764` | —（run.sh 使用） |

> ⚠️ **生产部署必须通过环境变量覆盖默认密钥**，勿使用仓库内默认值。

## 🚀 快速开始

### 本机运行

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
./run.sh start      # 后台启动 :8764
./run.sh status
./run.sh stop
```

### Docker 运行

```bash
# 本地构建
docker build -t lifesign:local .
docker run -d --name lifesign -p 8764:8764 \
  -e USER_STATUS_PHONE_KEY='<phone-key>' \
  -e USER_STATUS_AGENT_KEY='<agent-key>' \
  lifesign:local
```

### 1Panel Compose 部署（推荐）

1. 在 1Panel → 容器 → 编排 中新建编排，粘贴 `docker-compose.yml`；
2. 镜像由 GitHub Actions 自动构建推送到 GHCR，部署时直接拉取；
3. 仅需开放 1 个端口 `8764`，其余由反向代理处理。

### 手机发送数据

```bash
# 经公网反代（手机端快捷指令用这个）
curl -s -X POST https://<your-domain>/user-status/ingest \
  -H "Authorization: Bearer <phone-key>" \
  -H "Content-Type: application/json" \
  -d '{"deviceStage":{"battery":{"percentage":87,"is_charging":true}}}'

# 或内网直连
curl -s -X POST http://<host-ip>:8764/ingest \
  -H "Authorization: Bearer <phone-key>" \
  -H "Content-Type: application/json" \
  -d '{"deviceStage":{"battery":{"percentage":87,"is_charging":true}}}'
```

### Hermes MCP 配置（config.yaml）

```yaml
mcp_servers:
  user-status:
    type: streamable-http
    url: http://127.0.0.1:8764/mcp   # 本机回环，不走公网
    connect_timeout: 10
    timeout: 30
```

验证：`hermes mcp test user-status`；重启 Hermes 后工具注册为 `mcp_user_status_*`。

## 🐳 Docker 镜像构建（GitHub Actions）

仓库内置 `.github/workflows/docker-build.yml`：

- **触发**：push 到 `main` / 手动 `workflow_dispatch` / 打 tag
- **产物**：`ghcr.io/<owner>/lifesign:latest` 与 `:<git-sha>` 双 tag
- **平台**：`linux/amd64`、`linux/arm64`
- **说明**：镜像为私有（仓库私有 → GHCR 包私有），1Panel 部署时需在
  Docker 配置中添加 GHCR 登录凭据（`ghcr.io` 用户名 + PAT）。

## ✅ 测试

```bash
. .venv/bin/activate
python -m pytest tests/ -v
```

## 🗂️ 项目结构

```
lifesign/
├── app/
│   ├── main.py            # FastAPI 入口（挂载 MCP 网关）
│   ├── mcp_server.py      # FastMCP 工具定义（get_status/get_battery/...）
│   ├── store.py           # 线程安全内存存储
│   ├── models/status.py   # Pydantic 数据模型
│   └── routers/           # /ingest 与 /query_all 路由
├── config/clients.example.yaml   # 身份配置模板（真实文件勿提交）
├── panel_api.py           # 1Panel API 签名请求辅助脚本
├── docker-compose.yml     # 1Panel Compose 部署编排
├── Dockerfile
├── run.sh                 # 本机后台启停
└── tests/
```

## 📜 许可证

MIT
