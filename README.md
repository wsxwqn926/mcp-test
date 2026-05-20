# MCP Test Tool

MCP Server 全功能可视化测试调试平台，基于 Python FastAPI + Vue 3 构建。

## 功能特性

- **连接管理** — 支持 STDIO / HTTP / SSE 三种传输协议，配置持久化保存
- **工具调试** — 浏览工具列表、Schema 表单调用、JSON 编辑器、调用历史
- **资源浏览** — 资源列表、内容读取、资源订阅、模板展示
- **提示词测试** — 提示词列表、参数填充、消息格式化展示
- **消息日志** — 实时消息记录、过滤搜索、统计面板、JSON/CSV 导出
- **自动化测试** — 测试用例 CRUD、7 种断言类型、录制回放、批量执行
- **协议验证** — MCP 规范合规性检查（6 大类 16 项检查）
- **性能测试** — 延迟测试 / 并发测试，ECharts 可视化
- **实时通知** — WebSocket 推送连接状态、消息日志、服务端通知

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11+ / FastAPI / uvicorn |
| 前端 | Vue 3 / TypeScript / Vite / Element Plus |
| 状态管理 | Pinia |
| 图表 | ECharts |
| 实时通信 | WebSocket |
| MCP SDK | mcp >= 1.0.0 (官方 Python SDK) |

## 快速开始

### 环境要求

- Python >= 3.11
- Node.js >= 18
- npm >= 9

### 安装依赖

```bash
# 后端
pip install -e backend/

# 前端
cd frontend
npm install
```

### 启动服务

```bash
# 启动后端 (在项目根目录)
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# 启动前端 (在 frontend 目录)
cd frontend
npm run dev
```

访问 http://localhost:5173 即可使用。

### 端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | 8000 | FastAPI REST + WebSocket |
| 前端 Dev | 5173 | Vite 开发服务器（自动代理 API） |

## 项目结构

```
mcp-test/
├── backend/                    # Python 后端
│   ├── main.py                 # FastAPI 入口
│   ├── api/                    # REST API 路由 + WebSocket
│   ├── client/                 # MCP 客户端层
│   ├── models/                 # 数据模型 (Pydantic)
│   ├── services/               # 业务逻辑层
│   └── utils/                  # 工具函数
├── frontend/                   # Vue 3 前端
│   └── src/
│       ├── api/                # API 调用封装
│       ├── stores/             # Pinia 状态管理
│       ├── composables/        # 组合式函数
│       ├── views/              # 页面视图
│       └── components/         # 可复用组件
├── data/                       # 运行时数据
│   ├── server_configs.json     # 连接配置
│   ├── test_cases.json         # 测试用例
│   └── history/                # 消息历史
├── tests/examples/             # 示例测试用例
├── IMPLEMENTATION.md           # 详细实施文档
└── README.md
```

## 使用说明

### 1. 连接 MCP Server

1. 打开「连接管理」页面
2. 填写连接信息（STDIO 命令或 HTTP 地址）
3. 点击「保存并连接」

### 2. 调试工具

1. 连接成功后，进入「工具」页面
2. 选择工具，填写参数（表单或 JSON）
3. 点击「执行」查看结果

### 3. 运行自动化测试

1. 在「自动化测试」页面创建测试用例
2. 添加步骤：工具调用、断言、等待等
3. 点击「执行」查看测试报告
4. 也可使用「从历史录制」自动生成测试步骤

### 4. 协议验证

进入「协议验证」页面，点击「开始验证」，自动检测 MCP 协议合规性。

### 5. 性能测试

进入「性能测试」页面，选择延迟测试或并发测试，配置参数后执行。

## API 文档

启动后端后访问 http://localhost:8000/docs 查看 Swagger API 文档。

## License

MIT
