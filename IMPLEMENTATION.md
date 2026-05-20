# MCP 测试调试工具 - 实施文档

## 1. 项目概述

### 1.1 产品定位

面向 MCP Server 开发者的全功能可视化测试调试平台，基于 Python + Streamlit 构建，支持 STDIO 和 Streamable HTTP 双传输协议，提供从基础调试到自动化测试、性能分析、协议验证的一站式能力。

### 1.2 核心目标

- **降低 MCP Server 开发调试成本**：可视化操作替代手动 JSON-RPC 通信
- **保障 Server 质量**：提供自动化测试和协议合规性验证
- **提升开发效率**：录制回放、Mock、性能测试加速开发迭代

### 1.3 与现有工具的差异化

| 特性 | MCP Inspector | 本工具 |
|------|--------------|--------|
| 技术栈 | Node.js | Python（AI 开发者友好） |
| 传输协议 | STDIO + SSE | STDIO + Streamable HTTP |
| 自动化测试 | 无 | 录制回放 + 断言框架 |
| 性能测试 | 无 | 延迟 / 并发 / 吞吐量 |
| Mock 能力 | 无 | Mock Server + 响应模拟 |
| 协议验证 | 无 | MCP 规范合规性检查 |
| 测试报告 | 无 | HTML / JSON 格式报告 |

---

## 2. 技术架构

### 2.1 技术选型

| 层级 | 技术 | 版本要求 | 说明 |
|------|------|----------|------|
| 运行时 | Python | >= 3.11 | 原生 async/await 支持 |
| Web UI | Streamlit | >= 1.40.0 | 快速构建数据应用，纯 Python |
| MCP SDK | mcp | >= 1.0.0 | 官方 Tier 1 Python SDK |
| 数据模型 | Pydantic | >= 2.0 | 类型安全的数据验证 |
| HTTP 客户端 | httpx | >= 0.27 | 异步 HTTP，用于 Streamable HTTP 传输 |
| 数据库 | aiosqlite | >= 0.20 | 异步 SQLite，存储配置和测试数据 |
| 图表 | Plotly | >= 5.0 | 性能测试可视化 |
| Schema 验证 | jsonschema | >= 4.0 | JSON Schema 校验 |
| 包管理 | uv | >= 0.4.0 | 快速依赖管理 |

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Web UI                        │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │
│  │ 连接管理 │ │ 原语调试  │ │ 消息日志  │ │ 自动化测试     │  │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └───────┬────────┘  │
│       │           │            │                │            │
│  ┌────┴───────────┴────────────┴────────────────┴────────┐  │
│  │                   Service 层                           │  │
│  │  ToolService │ ResourceService │ PromptService         │  │
│  │  TestRunner  │ MockService    │ ProtocolValidator      │  │
│  │  PerformanceTester            │ MessageLogger          │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                          │                                   │
│  ┌───────────────────────┴─────────────────────────────────┐ │
│  │               Client / Transport 层                     │ │
│  │  ConnectionManager → SessionWrapper                     │ │
│  │  TransportFactory (STDIO | StreamableHTTP)              │ │
│  └───────────────────────┬─────────────────────────────────┘ │
└──────────────────────────┼──────────────────────────────────┘
                           │ MCP Protocol (JSON-RPC 2.0)
           ┌───────────────┴───────────────┐
           │                               │
    ┌──────┴──────┐                ┌───────┴───────┐
    │ MCP Server  │                │ MCP Server    │
    │ (STDIO)     │                │ (HTTP Remote) │
    └─────────────┘                └───────────────┘
```

### 2.3 数据流

```
用户操作 → Streamlit UI → Service 层 → ConnectionManager → MCP ClientSession → MCP Server
                                      ↓
                              MessageLogger（拦截记录）
                                      ↓
                              ProtocolValidator（验证）
```

---

## 3. 项目结构

```
mcp-test/
├── pyproject.toml                      # 项目配置和依赖
├── .env.example                        # 环境变量模板
├── .gitignore
├── app.py                              # Streamlit 应用入口
│
├── src/
│   ├── __init__.py
│   │
│   ├── client/                         # MCP 客户端层
│   │   ├── __init__.py
│   │   ├── connection_manager.py       # 连接生命周期管理
│   │   ├── session_wrapper.py          # ClientSession 增强
│   │   └── transport_factory.py        # 传输层工厂
│   │
│   ├── models/                         # 数据模型
│   │   ├── __init__.py
│   │   ├── server_config.py            # Server 配置模型
│   │   ├── test_case.py                # 测试用例模型
│   │   ├── test_result.py              # 测试执行结果模型
│   │   └── message_log.py              # 消息日志模型
│   │
│   ├── services/                       # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── tool_service.py             # 工具调试服务
│   │   ├── resource_service.py         # 资源调试服务
│   │   ├── prompt_service.py           # 提示词调试服务
│   │   ├── test_runner.py              # 自动化测试运行器
│   │   ├── mock_service.py             # Mock 服务
│   │   ├── protocol_validator.py       # 协议合规性验证
│   │   ├── performance_tester.py       # 性能测试
│   │   └── message_logger.py           # 消息日志记录器
│   │
│   ├── ui/                             # UI 层
│   │   ├── __init__.py
│   │   ├── pages/                      # 页面模块
│   │   │   ├── __init__.py
│   │   │   ├── connection_page.py      # 连接管理页
│   │   │   ├── tools_page.py           # 工具调试页
│   │   │   ├── resources_page.py       # 资源浏览页
│   │   │   ├── prompts_page.py         # 提示词页
│   │   │   ├── messages_page.py        # 消息日志页
│   │   │   ├── test_runner_page.py     # 自动化测试页
│   │   │   ├── mock_page.py            # Mock 管理页
│   │   │   ├── validator_page.py       # 协议验证页
│   │   │   └── performance_page.py     # 性能测试页
│   │   ├── components/                 # 可复用组件
│   │   │   ├── __init__.py
│   │   │   ├── sidebar.py              # 侧边栏
│   │   │   ├── json_editor.py          # JSON 编辑器
│   │   │   ├── message_viewer.py       # 消息查看器
│   │   │   └── status_indicator.py     # 状态指示器
│   │   └── layout.py                   # 全局布局
│   │
│   └── utils/                          # 工具函数
│       ├── __init__.py
│       ├── logger.py                   # 日志配置
│       ├── json_utils.py               # JSON 格式化/验证
│       └── config.py                   # 全局配置管理
│
├── tests/                              # 测试用例存储目录
│   └── examples/
│       └── sample_test.json
│
├── data/                               # 运行时数据
│   └── history/                        # 历史记录
│
└── docs/                               # 文档
    └── test_case_format.md             # 测试用例格式说明
```

---

## 4. 模块详细设计

### 4.1 Client 层 — `src/client/`

#### 4.1.1 `transport_factory.py` — 传输层工厂

```python
# transport_factory.py
"""
负责创建 MCP 传输层实例。
根据配置创建 STDIO 或 Streamable HTTP 传输。
"""
```

**核心接口：**

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `create_stdio_transport(config)` | `StdioConfig` | `StdioServerParameters` | 创建 STDIO 传输参数 |
| `create_http_transport(config)` | `HttpConfig` | `StreamableHTTPTransport` | 创建 HTTP 传输实例 |

**STDIO 配置模型：**

```python
class StdioConfig(BaseModel):
    command: str                    # 执行命令，如 "python", "node", "uvx"
    args: list[str] = []           # 命令参数
    env: dict[str, str] | None     # 环境变量
    cwd: str | None                # 工作目录
```

**HTTP 配置模型：**

```python
class HttpConfig(BaseModel):
    url: str                        # Server URL
    headers: dict[str, str] = {}   # 请求头（含认证信息）
    timeout: float = 30.0          # 超时时间（秒）
```

#### 4.1.2 `connection_manager.py` — 连接管理器

```python
# connection_manager.py
"""
管理 MCP 连接的完整生命周期：
创建 → 初始化 → 能力协商 → 通信 → 断开 → 重连
"""
```

**核心接口：**

| 方法 | 说明 |
|------|------|
| `async connect(config: ServerConfig)` | 建立连接并完成初始化握手 |
| `async disconnect()` | 优雅断开连接 |
| `async reconnect()` | 重新连接 |
| `get_session() → SessionWrapper` | 获取当前会话 |
| `get_server_info() → ServerInfo` | 获取 Server 身份和能力信息 |
| `get_connection_state() → ConnectionState` | 获取连接状态 |
| `on_state_change(callback)` | 注册状态变更回调 |

**连接状态机：**

```
DISCONNECTED → CONNECTING → INITIALIZING → CONNECTED → DISCONNECTING → DISCONNECTED
                                    ↓                           ↑
                                  ERROR ────────────────────────┘
```

**初始化握手流程：**

```
Client                                    Server
  │                                         │
  │──── initialize (protocolVersion,        │
  │      capabilities, clientInfo) ────────→│
  │                                         │
  │←─── initialize result (protocolVersion, │
  │      capabilities, serverInfo) ─────────│
  │                                         │
  │──── notifications/initialized ─────────→│
  │                                         │
  │         [READY FOR COMMUNICATION]       │
```

#### 4.1.3 `session_wrapper.py` — 会话封装

```python
# session_wrapper.py
"""
在 MCP ClientSession 基础上增加：
- 消息拦截和记录
- 错误处理增强
- 超时控制
- 请求/响应的 Schema 缓存
"""
```

**增强功能：**

| 功能 | 说明 |
|------|------|
| 消息拦截 | 所有请求/响应自动记录到 MessageLogger |
| 超时控制 | 可配置每个操作的独立超时 |
| 错误包装 | 将 MCP 错误转换为友好的异常信息 |
| Schema 缓存 | 缓存 tools/list, resources/list 等结果，减少重复请求 |
| 事件通知 | 连接状态变更、消息收发事件通知 |

### 4.2 Models 层 — `src/models/`

#### 4.2.1 `server_config.py`

```python
class ServerConfig(BaseModel):
    """Server 连接配置"""
    id: str                              # 唯一标识 (UUID)
    name: str                            # 显示名称
    transport_type: Literal["stdio", "http"]
    stdio_config: StdioConfig | None     # STDIO 配置
    http_config: HttpConfig | None       # HTTP 配置
    created_at: datetime
    updated_at: datetime

class ServerInfo(BaseModel):
    """Server 信息（初始化后获取）"""
    name: str
    version: str
    protocol_version: str
    capabilities: ServerCapabilities

class ServerCapabilities(BaseModel):
    """Server 能力声明"""
    tools: ToolCapabilities | None
    resources: ResourceCapabilities | None
    prompts: PromptCapabilities | None
    logging: LoggingCapabilities | None
```

#### 4.2.2 `test_case.py`

```python
class TestCase(BaseModel):
    """测试用例"""
    id: str
    name: str
    description: str | None
    server_config_id: str                # 关联的 Server 配置
    steps: list[TestStep]                # 测试步骤列表
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime

class TestStep(BaseModel):
    """单个测试步骤"""
    id: str
    type: Literal["tool_call", "resource_read", "prompt_get", "assertion", "wait"]
    # tool_call 步骤
    tool_name: str | None
    arguments: dict | None
    # resource_read 步骤
    resource_uri: str | None
    # prompt_get 步骤
    prompt_name: str | None
    prompt_arguments: dict | None
    # assertion 步骤
    assertion: Assertion | None
    # wait 步骤
    wait_seconds: float | None

class Assertion(BaseModel):
    """断言定义"""
    type: Literal[
        "status_success",          # 结果状态为成功
        "content_contains",        # 内容包含指定文本
        "content_matches",         # 内容匹配正则
        "content_schema_valid",    # 内容符合 JSON Schema
        "response_time_lt",        # 响应时间小于阈值
        "content_not_empty",       # 内容非空
        "json_field_equals",       # JSON 字段值相等
    ]
    expected: Any                    # 期望值
    path: str | None                 # JSON 路径 (用于 json_field_equals)

class TestSuite(BaseModel):
    """测试套件"""
    id: str
    name: str
    description: str | None
    test_case_ids: list[str]
    tags: list[str] = []
```

#### 4.2.3 `test_result.py`

```python
class TestRunResult(BaseModel):
    """测试执行结果"""
    id: str
    test_case_id: str
    status: Literal["passed", "failed", "error", "skipped"]
    started_at: datetime
    finished_at: datetime
    duration_ms: float
    step_results: list[StepResult]
    error_message: str | None

class StepResult(BaseModel):
    """步骤执行结果"""
    step_id: str
    status: Literal["passed", "failed", "error", "skipped"]
    duration_ms: float
    request: dict | None              # 发送的请求
    response: dict | None             # 收到的响应
    assertion_results: list[AssertionResult] | None
    error_message: str | None

class AssertionResult(BaseModel):
    """断言结果"""
    assertion_type: str
    passed: bool
    expected: Any
    actual: Any
    message: str
```

#### 4.2.4 `message_log.py`

```python
class MessageLog(BaseModel):
    """消息日志记录"""
    id: str
    session_id: str                    # 关联的连接会话
    direction: Literal["request", "response", "notification"]
    timestamp: datetime
    method: str | None                 # JSON-RPC 方法名
    request_id: int | str | None       # JSON-RPC ID
    data: dict                         # 完整消息内容
    duration_ms: float | None          # 响应耗时（仅 response）
    error: dict | None                 # 错误信息（仅 error response）
```

### 4.3 Services 层 — `src/services/`

#### 4.3.1 `tool_service.py` — 工具调试服务

| 方法 | 说明 |
|------|------|
| `async list_tools()` | 获取工具列表（带缓存） |
| `async get_tool(name)` | 获取单个工具详情 |
| `async call_tool(name, arguments)` | 调用工具并记录日志 |
| `async call_tool_raw(name, arguments)` | 调用工具返回原始响应 |
| `get_call_history(name)` | 获取指定工具的调用历史 |
| `generate_form_schema(tool)` | 从 inputSchema 生成表单描述 |

#### 4.3.2 `resource_service.py` — 资源调试服务

| 方法 | 说明 |
|------|------|
| `async list_resources()` | 获取资源列表 |
| `async read_resource(uri)` | 读取资源内容 |
| `async subscribe_resource(uri)` | 订阅资源变更 |
| `async unsubscribe_resource(uri)` | 取消订阅 |
| `detect_content_type(content)` | 自动检测内容类型 |

#### 4.3.3 `prompt_service.py` — 提示词调试服务

| 方法 | 说明 |
|------|------|
| `async list_prompts()` | 获取提示词列表 |
| `async get_prompt(name, arguments)` | 获取提示词内容 |
| `generate_form_schema(prompt)` | 从参数定义生成表单描述 |

#### 4.3.4 `message_logger.py` — 消息日志服务

| 方法 | 说明 |
|------|------|
| `log_request(session_id, method, data)` | 记录请求 |
| `log_response(session_id, request_id, data, duration)` | 记录响应 |
| `log_notification(session_id, method, data)` | 记录通知 |
| `query(filters)` | 按条件查询日志 |
| `export(format)` | 导出日志（JSON/CSV） |
| `clear(session_id)` | 清除指定会话日志 |

#### 4.3.5 `test_runner.py` — 自动化测试运行器

**核心流程：**

```
加载测试用例
    │
    ▼
建立 MCP 连接
    │
    ▼
┌──→ 执行 TestStep
│       │
│       ├── tool_call → 调用工具 → 收集响应
│       ├── resource_read → 读取资源 → 收集响应
│       ├── prompt_get → 获取提示词 → 收集响应
│       ├── assertion → 比对期望值 → 记录结果
│       └── wait → 等待指定时间
│       │
│       ├── 成功 → 记录 StepResult(passed)
│       └── 失败 → 记录 StepResult(failed) + 中断/继续
│       │
│   还有下一个步骤？──是──┘
│       │ 否
│       ▼
   生成 TestRunResult
       │
       ▼
   断开连接
```

**断言执行逻辑：**

| 断言类型 | 执行方式 |
|----------|----------|
| `status_success` | 检查 `result.isError != true` |
| `content_contains` | 检查响应文本包含 `expected` 子串 |
| `content_matches` | 正则匹配响应文本 |
| `content_schema_valid` | 用 `jsonschema` 验证响应内容 |
| `response_time_lt` | 检查 `duration_ms < expected` |
| `content_not_empty` | 检查 `content` 数组非空 |
| `json_field_equals` | 用 JSON Path 提取字段值比较 |

#### 4.3.6 `mock_service.py` — Mock 服务

**Mock 配置模型：**

```python
class MockConfig(BaseModel):
    """Mock Server 配置"""
    id: str
    name: str
    server_info: MockServerInfo
    tools: list[MockTool]
    resources: list[MockResource]
    prompts: list[MockPrompt]
    behavior: MockBehavior

class MockTool(BaseModel):
    """Mock 工具定义"""
    name: str
    description: str
    input_schema: dict
    response: MockResponse            # 固定响应

class MockResponse(BaseModel):
    """Mock 响应"""
    content: list[dict]               # 返回内容
    is_error: bool = False
    delay_ms: int = 0                 # 模拟延迟

class MockBehavior(BaseModel):
    """Mock 行为配置"""
    record_requests: bool = True      # 记录收到的请求
    allow_unexpected: bool = True     # 允许未定义的调用
    default_error: dict | None        # 未定义调用的默认响应
```

**Mock 工作原理：**

```
Mock Service 启动一个 MCP Server 进程
    │
    ├── 收到 tools/list → 返回预定义的工具列表
    ├── 收到 tools/call → 返回预定义的响应（可配延迟）
    ├── 收到 resources/list → 返回预定义的资源列表
    ├── 收到 resources/read → 返回预定义的资源内容
    ├── 收到 prompts/list → 返回预定义的提示词列表
    └── 收到 prompts/get → 返回预定义的提示词内容
```

#### 4.3.7 `protocol_validator.py` — 协议合规性验证

**验证项目清单：**

| 检查项 | 验证内容 |
|--------|----------|
| **初始化流程** | |
| `init_request_format` | initialize 请求格式正确 |
| `init_response_format` | initialize 响应格式正确 |
| `init_notification` | initialized 通知已发送 |
| `protocol_version` | 协议版本为支持的版本 |
| `capability_declaration` | 能力声明格式正确 |
| **消息格式** | |
| `jsonrpc_version` | jsonrpc 字段为 "2.0" |
| `request_id_type` | 请求 ID 为 number 或 string |
| `response_id_match` | 响应 ID 与请求 ID 匹配 |
| `notification_no_id` | 通知消息不包含 id 字段 |
| **原语规范** | |
| `tool_name_format` | 工具名符合命名规范 |
| `tool_input_schema` | 工具 inputSchema 为有效 JSON Schema |
| `tool_response_format` | 工具调用响应包含 content 数组 |
| `resource_uri_format` | 资源 URI 格式正确 |
| `prompt_name_format` | 提示词名称非空 |
| **错误处理** | |
| `error_response_format` | 错误响应包含 code 和 message |
| `unknown_method_error` | 未知方法返回 -32601 |
| `invalid_params_error` | 无效参数返回 -32602 |

**验证结果输出：**

```python
class ValidationReport(BaseModel):
    """验证报告"""
    server_name: str
    server_version: str
    protocol_version: str
    timestamp: datetime
    total_checks: int
    passed: int
    failed: int
    warnings: int
    results: list[ValidationCheckResult]
    overall_status: Literal["compliant", "partial", "non_compliant"]

class ValidationCheckResult(BaseModel):
    """单项检查结果"""
    check_id: str
    category: str
    description: str
    status: Literal["passed", "failed", "warning", "skipped"]
    details: str | None
    request: dict | None
    response: dict | None
```

#### 4.3.8 `performance_tester.py` — 性能测试

**测试类型：**

| 类型 | 配置 | 输出指标 |
|------|------|----------|
| 延迟测试 | 单次调用 N 次，统计每次耗时 | min/max/avg/p50/p95/p99 |
| 并发测试 | M 个并发客户端同时调用 | QPS、错误率、P95 延迟 |
| 吞吐量测试 | 逐步增加并发直到性能下降 | 最大 QPS、饱和点 |
| 稳定性测试 | 持续运行 N 分钟 | 错误率趋势、内存泄漏检测 |

**性能测试配置：**

```python
class PerformanceConfig(BaseModel):
    """性能测试配置"""
    test_type: Literal["latency", "concurrency", "throughput", "stability"]
    tool_name: str
    arguments: dict
    iterations: int = 100             # 延迟测试调用次数
    concurrency: int = 10             # 并发数
    ramp_up_seconds: float = 10       # 吞吐量测试爬坡时间
    duration_seconds: int = 300       # 稳定性测试持续时间
    warmup_iterations: int = 5        # 预热次数（不计入结果）
```

**性能报告：**

```python
class PerformanceReport(BaseModel):
    """性能报告"""
    config: PerformanceConfig
    started_at: datetime
    finished_at: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    latency_stats: LatencyStats
    qps: float | None
    errors: list[str]

class LatencyStats(BaseModel):
    min_ms: float
    max_ms: float
    avg_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
```

### 4.4 UI 层 — `src/ui/`

#### 4.4.1 全局布局 `layout.py`

```
┌─────────────────────────────────────────────────────────┐
│  MCP Test Tool v1.0.0                    [状态指示器]    │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│  侧边栏  │              主内容区                         │
│          │                                              │
│ ┌──────┐ │  ┌──────────────────────────────────────┐   │
│ │连接管理│ │  │                                      │   │
│ ├──────┤ │  │         当前页面内容                   │   │
│ │工具   │ │  │                                      │   │
│ ├──────┤ │  │                                      │   │
│ │资源   │ │  │                                      │   │
│ ├──────┤ │  │                                      │   │
│ │提示词 │ │  │                                      │   │
│ ├──────┤ │  │                                      │   │
│ │消息日志│ │  │                                      │   │
│ ├──────┤ │  │                                      │   │
│ │自动化  │ │  │                                      │   │
│ ├──────┤ │  │                                      │   │
│ │Mock   │ │  │                                      │   │
│ ├──────┤ │  │                                      │   │
│ │验证   │ │  │                                      │   │
│ ├──────┤ │  │                                      │   │
│ │性能   │ │  │                                      │   │
│ └──────┘ │  └──────────────────────────────────────┘   │
│          │                                              │
│ Server:  │                                              │
│ [选择框] │                                              │
│ 状态: ●  │                                              │
└──────────┴──────────────────────────────────────────────┘
```

#### 4.4.2 页面设计

**连接管理页 (`connection_page.py`)**

```
┌─ 连接管理 ──────────────────────────────────────────────┐
│                                                         │
│  ┌─ 新建连接 ──────────────────────────────────────┐    │
│  │ 连接名称: [________________________]            │    │
│  │ 传输类型: ○ STDIO  ○ Streamable HTTP            │    │
│  │                                                  │    │
│  │ [STDIO 配置]                                     │    │
│  │ 命令: [python_______]                            │    │
│  │ 参数: [server.py________________]                │    │
│  │ 环境变量: [+ 添加]                               │    │
│  │                                                  │    │
│  │ [连接]  [保存配置]                               │    │
│  └──────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─ 已保存的连接 ──────────────────────────────────┐    │
│  │ 📗 My Server (STDIO) - python server.py    [连接]│    │
│  │ 📗 Remote API (HTTP) - http://...          [连接]│    │
│  │ 📗 DB Server (STDIO) - uvx mcp-sqlite     [连接]│    │
│  └──────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─ Server 信息 ───────────────────────────────────┐    │
│  │ 名称: example-server                            │    │
│  │ 版本: 1.0.0                                     │    │
│  │ 协议版本: 2025-06-18                            │    │
│  │ 能力: tools ✓ resources ✓ prompts ✗ logging ✓   │    │
│  └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**工具调试页 (`tools_page.py`)**

```
┌─ 工具调试 ──────────────────────────────────────────────┐
│                                                         │
│  ┌─ 工具列表 ───────────────┐ ┌─ 工具详情 ────────────┐│
│  │ 🔍 calculator_arithmetic ││ 名称: weather_current  ││
│  │ ☁️ weather_current   [✓] ││ 标题: Weather Info     ││
│  │ 📁 file_read             ││                        ││
│  │ 📁 file_write            ││ 描述: Get current      ││
│  │                          ││ weather for any loc... ││
│  │                          ││                        ││
│  │                          ││ ── 输入参数 ──         ││
│  │                          ││ location*: [________]  ││
│  │                          ││ units: [metric ▼]      ││
│  │                          ││                        ││
│  │                          ││ [执行] [保存为测试步骤] ││
│  └──────────────────────────┘└────────────────────────┘│
│                                                         │
│  ┌─ 执行结果 ───────────────────────────────────────┐   │
│  │ 状态: ✅ 成功  耗时: 342ms                       │   │
│  │                                                  │   │
│  │ Content:                                         │   │
│  │ {                                                │   │
│  │   "type": "text",                                │   │
│  │   "text": "Current weather: 68°F..."            │   │
│  │ }                                                │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─ 调用历史 ───────────────────────────────────────┐   │
│  │ #1  2025-05-18 14:30:22  ✅ 342ms  [查看] [重放] │   │
│  │ #2  2025-05-18 14:28:10  ✅ 289ms  [查看] [重放] │   │
│  │ #3  2025-05-18 14:25:01  ❌ 5000ms [查看] [重放] │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**消息日志页 (`messages_page.py`)**

```
┌─ 消息日志 ──────────────────────────────────────────────┐
│                                                         │
│  过滤: [全部类型 ▼] [全部方法 ▼] [搜索___________] [导出]│
│                                                         │
│  ┌─ 消息列表 ──────────────────────────────────────┐    │
│  │ → 14:30:22.100 tools/call          id:3  REQ   │    │
│  │ ← 14:30:22.442 tools/call response id:3  RES   │    │
│  │ → 14:30:20.050 tools/list          id:2  REQ   │    │
│  │ ← 14:30:20.120 tools/list response id:2  RES   │    │
│  │ → 14:30:18.000 initialize          id:1  REQ   │    │
│  │ ← 14:30:18.850 initialize response id:1  RES   │    │
│  │ → 14:30:18.860 notifications/init       NOTIF  │    │
│  └──────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─ 消息详情 ───────────────────────────────────────┐   │
│  │ 方向: Request →                                  │   │
│  │ 时间: 2025-05-18 14:30:22.100                    │   │
│  │ 方法: tools/call                                 │   │
│  │                                                  │   │
│  │ {                                                │   │
│  │   "jsonrpc": "2.0",                              │   │
│  │   "id": 3,                                       │   │
│  │   "method": "tools/call",                        │   │
│  │   "params": {                                    │   │
│  │     "name": "weather_current",                   │   │
│  │     "arguments": { "location": "Beijing" }       │   │
│  │   }                                              │   │
│  │ }                                                │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**自动化测试页 (`test_runner_page.py`)**

```
┌─ 自动化测试 ────────────────────────────────────────────┐
│                                                         │
│  [新建用例] [导入] [导出] [录制]                         │
│                                                         │
│  ┌─ 测试用例 ───────────────────────────────────────┐   │
│  │ □ 基础工具调用测试 (3 步骤)               [编辑][▶] │   │
│  │ ☑ 天气 API 完整流程 (5 步骤)              [编辑][▶] │   │
│  │ □ 错误处理测试 (4 步骤)                   [编辑][▶] │   │
│  │                                                  │   │
│  │ [全选] [批量执行] [批量删除]                      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─ 执行结果 ───────────────────────────────────────┐   │
│  │ 天气 API 完整流程     ✅ PASSED    1.2s           │   │
│  │   ✅ Step 1: list_tools          120ms           │   │
│  │   ✅ Step 2: call weather         342ms           │   │
│  │   ✅ Step 3: assert contains      0ms            │   │
│  │   ✅ Step 4: call with params     289ms           │   │
│  │   ✅ Step 5: assert schema_valid  2ms            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**性能测试页 (`performance_page.py`)**

```
┌─ 性能测试 ──────────────────────────────────────────────┐
│                                                         │
│  ┌─ 测试配置 ───────────────────────────────────────┐   │
│  │ 测试类型: [延迟测试 ▼]                           │   │
│  │ 目标工具: [weather_current ▼]                    │   │
│  │ 调用次数: [100___]                               │   │
│  │ 预热次数: [5____]                                │   │
│  │ 参数: { "location": "Beijing" }                  │   │
│  │ [开始测试]                                       │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─ 测试结果 ───────────────────────────────────────┐   │
│  │ 总请求数: 100  成功: 98  失败: 2                 │   │
│  │                                                  │   │
│  │ ┌── 延迟分布 ──────────────────────────────┐     │   │
│  │ │  Min:  156ms   Max: 1,234ms              │     │   │
│  │ │  Avg:  342ms   StdDev: 89ms              │     │   │
│  │ │  P50:  310ms   P95: 567ms   P99: 987ms  │     │   │
│  │ │                                          │     │   │
│  │ │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░                  │     │   │
│  │ │  [直方图 / 时序图]                         │     │   │
│  │ └──────────────────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 5. 测试用例格式规范

### 5.1 文件格式

测试用例以 JSON 文件存储在 `tests/` 目录下。

### 5.2 示例测试用例

```json
{
  "id": "tc-001",
  "name": "天气工具基础测试",
  "description": "验证天气查询工具的基本功能",
  "tags": ["weather", "smoke"],
  "steps": [
    {
      "id": "step-1",
      "type": "tool_call",
      "tool_name": "weather_current",
      "arguments": {
        "location": "Beijing",
        "units": "metric"
      }
    },
    {
      "id": "step-2",
      "type": "assertion",
      "assertion": {
        "type": "status_success"
      }
    },
    {
      "id": "step-3",
      "type": "assertion",
      "assertion": {
        "type": "content_contains",
        "expected": "Beijing"
      }
    },
    {
      "id": "step-4",
      "type": "assertion",
      "assertion": {
        "type": "response_time_lt",
        "expected": 5000
      }
    },
    {
      "id": "step-5",
      "type": "tool_call",
      "tool_name": "weather_current",
      "arguments": {
        "location": ""
      }
    },
    {
      "id": "step-6",
      "type": "assertion",
      "assertion": {
        "type": "status_success",
        "expected": false
      }
    }
  ]
}
```

---

## 6. 分期实施计划

### Phase 1: 基础框架 + 连接管理 ✅ 已完成

**目标**：能连接 MCP Server 并查看 Server 信息

| 任务 | 优先级 | 预计工时 | 状态 |
|------|--------|----------|------|
| 初始化项目结构，配置 pyproject.toml | P0 | 0.5h | ✅ 完成 |
| 实现 `transport_factory.py` | P0 | 2h | ✅ 完成 |
| 实现 `connection_manager.py` | P0 | 4h | ✅ 完成 |
| 实现 `session_wrapper.py` | P0 | 3h | ✅ 完成 |
| 实现 `server_config.py` 模型 | P0 | 1h | ✅ 完成 |
| 实现 `message_log.py` 模型 | P0 | 1h | ✅ 完成 |
| 实现 `config.py` 配置管理 | P0 | 1h | ✅ 完成 |
| 实现 `logger.py` 日志工具 | P1 | 1h | ✅ 完成 |
| 实现 Streamlit 入口和全局布局 | P0 | 2h | ✅ 完成 |
| 实现侧边栏和状态指示器组件 | P0 | 1.5h | ✅ 完成 |
| 实现连接管理页 | P0 | 3h | ✅ 完成 |
| 实现工具调试页 (Phase 2 前置) | P0 | — | ✅ 已提前实现 |
| 实现资源浏览页 (Phase 2 前置) | P0 | — | ✅ 已提前实现 |
| 实现提示词页 (Phase 2 前置) | P1 | — | ✅ 已提前实现 |
| 实现消息日志页 (Phase 2 前置) | P0 | — | ✅ 已提前实现 |
| **合计** | | **20h** | |

**验收标准：**
- [x] 能通过 STDIO 连接本地 MCP Server
- [x] 能通过 HTTP 连接远程 MCP Server
- [x] 初始化握手成功，展示 Server 信息和能力
- [x] 连接状态正确显示和切换
- [x] 已保存的连接配置持久化
- [x] 工具列表浏览和调用 (提前实现)
- [x] 资源浏览和读取 (提前实现)
- [x] 提示词测试 (提前实现)
- [x] 消息日志记录和查看 (提前实现)

**已实现文件清单：**

```
src/
├── client/
│   ├── __init__.py
│   ├── connection_manager.py    # 连接生命周期管理 (状态机)
│   ├── session_wrapper.py       # ClientSession 封装 (缓存+消息拦截)
│   └── transport_factory.py     # STDIO/HTTP 传输层工厂
├── models/
│   ├── __init__.py
│   ├── server_config.py         # Server 配置、连接状态、能力模型
│   └── message_log.py           # 消息日志模型
├── ui/
│   ├── __init__.py
│   ├── components/
│   │   ├── sidebar.py           # 侧边栏导航 + 连接选择
│   │   ├── status_indicator.py  # 连接状态渲染
│   │   ├── json_editor.py       # JSON 编辑器组件
│   │   └── message_viewer.py    # 消息查看器组件
│   └── pages/
│       ├── connection_page.py   # 连接管理页 (新建/保存/连接/断开)
│       ├── tools_page.py        # 工具调试页 (列表/Schema/调用)
│       ├── resources_page.py    # 资源浏览页 (列表/读取/模板)
│       ├── prompts_page.py      # 提示词页 (列表/测试)
│       └── messages_page.py     # 消息日志页 (过滤/查看)
└── utils/
    ├── __init__.py
    ├── async_utils.py           # asyncio 与 Streamlit 桥接
    ├── config.py                # 连接配置持久化
    ├── json_utils.py            # JSON 格式化/验证
    └── logger.py                # 日志工具
app.py                           # Streamlit 入口
```

### Phase 2: Primitives 调试 ✅ 已完成

**目标**：能浏览和测试工具、资源、提示词，增强消息日志

| 任务 | 优先级 | 预计工时 | 状态 |
|------|--------|----------|------|
| 实现 `tool_service.py` | P0 | 3h | ✅ 完成 |
| 实现 `resource_service.py` | P0 | 2h | ✅ 完成 |
| 实现 `prompt_service.py` | P0 | 2h | ✅ 完成 |
| 实现 `message_logger.py` | P0 | 3h | ✅ 完成 |
| 增强工具调试页 (调用历史+耗时+JSON解析) | P0 | 4h | ✅ 完成 |
| 增强资源浏览页 (订阅+内容渲染+计数) | P0 | 3h | ✅ 完成 |
| 增强提示词页 (消息格式化+计数) | P1 | 2.5h | ✅ 完成 |
| 增强消息日志页 (统计面板+导出+方法过滤) | P0 | 3h | ✅ 完成 |
| 增强消息查看器 (颜色图标+详情) | P1 | 1.5h | ✅ 完成 |
| 线程安全消息缓冲区 (deque+Lock) | P0 | 1h | ✅ 完成 |
| 连接参数编辑/修改功能 | P1 | 1.5h | ✅ 完成 |
| **合计** | | **26.5h** | |

**验收标准：**
- [x] 能列出所有工具并展示 Schema
- [x] 能通过表单填写参数调用工具
- [x] 能直接编辑 JSON 调用工具
- [x] 工具调用历史记录和查看
- [x] 调用结果自动 JSON 解析和格式化
- [x] 能列出和读取资源（含内容类型检测）
- [x] 资源订阅支持
- [x] 能列出和测试提示词
- [x] 提示词消息格式化展示 (chat_message 样式)
- [x] 消息日志统计面板 (总消息/请求/响应/错误/耗时)
- [x] 消息日志方法下拉过滤 + 文本搜索
- [x] 消息日志 JSON/CSV 导出
- [x] 消息颜色图标 (🔵请求/🟢响应/🟡通知)
- [x] 连接参数在线编辑修改

**已实现文件清单 (Phase 2 新增/修改)：**

```
src/
├── services/                         # Phase 2 新增 Service 层
│   ├── __init__.py
│   ├── tool_service.py               # 工具调试 (调用历史+表单生成)
│   ├── resource_service.py           # 资源调试 (内容检测+渲染)
│   ├── prompt_service.py             # 提示词调试 (消息格式化)
│   └── message_logger.py             # 消息日志 (统计+查询+导出)
├── ui/
│   ├── components/
│   │   └── message_viewer.py         # 增强: 颜色图标+详情展开
│   └── pages/
│       ├── connection_page.py        # 增强: 编辑连接参数+取消编辑
│       ├── tools_page.py             # 增强: ToolService+调用历史+JSON解析
│       ├── resources_page.py         # 增强: ResourceService+订阅+内容渲染
│       ├── prompts_page.py           # 增强: PromptService+消息格式化
│       └── messages_page.py          # 增强: 统计面板+方法过滤+导出
├── client/
│   └── session_wrapper.py            # 增强: 线程安全消息缓冲区 (deque+Lock)
app.py                                # 增强: MessageLogger 集成
```

### Phase 3: 自动化测试 ✅ 已完成

**目标**：支持创建测试用例、执行自动化测试、断言验证、录制回放

| 任务 | 优先级 | 预计工时 | 状态 |
|------|--------|----------|------|
| 实现 `test_case.py` 和 `test_result.py` 模型 | P0 | 2h | ✅ 完成 |
| 实现 `test_runner.py` 测试执行器 | P0 | 4h | ✅ 完成 |
| 实现断言引擎 (7种断言类型) | P0 | 3h | ✅ 完成 |
| 实现测试用例持久化 `test_config.py` | P0 | 1.5h | ✅ 完成 |
| 实现自动化测试页 (CRUD+执行+结果展示) | P0 | 4h | ✅ 完成 |
| 实现录制功能 (从调用历史生成测试步骤) | P1 | 2h | ✅ 完成 |
| 测试用例 JSON 导出 | P1 | 1h | ✅ 完成 |
| **合计** | | **17.5h** | |

**验收标准：**
- [x] 能创建、编辑、保存测试用例
- [x] 能执行测试用例并生成报告
- [x] 断言类型覆盖 7 种 (status_success, content_contains, content_matches, content_schema_valid, response_time_lt, content_not_empty, json_field_equals)
- [x] 录制功能能从工具调用历史生成测试步骤
- [x] 测试结果可视化展示 (通过/失败/耗时/断言详情)
- [x] 测试用例 JSON 导出

**已实现文件清单 (Phase 3 新增)：**

```
src/
├── models/
│   ├── test_case.py                  # 测试用例、步骤、断言模型
│   └── test_result.py                # 测试执行结果、步骤结果、断言结果
├── services/
│   └── test_runner.py                # 测试执行器 + 断言引擎
├── ui/
│   └── pages/
│       └── test_runner_page.py       # 自动化测试页 (CRUD+执行+结果)
├── utils/
│   └── test_config.py                # 测试用例 JSON 持久化
```

### Phase 4: 协议验证 + 性能测试 ✅ 已完成

**目标**：完整的质量保障工具链

| 任务 | 优先级 | 预计工时 | 状态 |
|------|--------|----------|------|
| 实现 `protocol_validator.py` | P1 | 5h | ✅ 完成 |
| 实现协议验证页 | P1 | 3h | ✅ 完成 |
| 实现 `performance_tester.py` | P1 | 4h | ✅ 完成 |
| 实现性能测试页（含 Plotly 图表） | P1 | 3h | ✅ 完成 |
| **合计** | | **15h** | |

**验收标准：**
- [x] 协议验证覆盖 16 个检查项（6大类）
- [x] 生成合规性报告（通过/失败/警告 + 总体状态）
- [x] 延迟测试统计 min/max/avg/p50/p95/p99/stddev
- [x] 并发测试可配置并发数
- [x] 性能图表使用 Plotly 渲染（时序图 + 直方图）
- [x] QPS 计算

**已实现文件清单 (Phase 4 新增)：**

```
src/
├── services/
│   ├── protocol_validator.py         # 协议验证 (6类16项检查)
│   └── performance_tester.py         # 性能测试 (延迟+并发)
├── ui/
│   └── pages/
│       ├── validator_page.py         # 协议验证页 (分类展示+统计)
│       └── performance_page.py       # 性能测试页 (Plotly图表)
```

### Phase 5: 打磨 + 发布

| 任务 | 优先级 | 预计工时 |
|------|--------|----------|
| UI 主题美化和一致性调整 | P2 | 4h |
| 错误处理和边界情况 | P1 | 3h |
| 多 Server 连接对比功能 | P2 | 4h |
| 历史会话回放 | P2 | 3h |
| 通知监听和展示 | P1 | 2h |
| 编写 README 和使用文档 | P1 | 3h |
| 编写示例测试用例 | P2 | 2h |
| **合计** | | **21h** |

---

## 7. 关键实现要点

### 7.1 Streamlit 与 asyncio 的集成

Streamlit 运行在同步上下文中，MCP SDK 使用 asyncio。需要通过以下方式桥接：

```python
import asyncio
from streamlit.runtime.scriptrunner import add_script_run_ctx

def get_or_create_event_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

def run_async(coro):
    loop = get_or_create_event_loop()
    return loop.run_until_complete(coro)
```

### 7.2 MCP Session 状态管理

使用 Streamlit 的 `st.session_state` 管理 MCP 连接状态：

```python
# 在 session_state 中保存的关键对象
session_state_keys = {
    "connection_manager": ConnectionManager,     # 连接管理器实例
    "active_session_id": str | None,             # 当前活跃的连接 ID
    "server_configs": dict[str, ServerConfig],   # 所有保存的 Server 配置
    "server_infos": dict[str, ServerInfo],        # 已连接的 Server 信息
    "message_logs": list[MessageLog],             # 消息日志缓存
    "tool_cache": dict[str, list],                # 工具列表缓存
    "resource_cache": dict[str, list],            # 资源列表缓存
    "prompt_cache": dict[str, list],              # 提示词列表缓存
}
```

### 7.3 消息拦截机制

通过继承或包装 `ClientSession` 来拦截所有 JSON-RPC 消息：

```python
class InterceptingSession(ClientSession):
    def __init__(self, *args, message_logger=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._message_logger = message_logger

    async def _send_request(self, request):
        self._message_logger.log_request(request)
        start = time.monotonic()
        response = await super()._send_request(request)
        duration = (time.monotonic() - start) * 1000
        self._message_logger.log_response(response, duration)
        return response
```

### 7.4 JSON Schema 到表单的自动转换

将工具的 `inputSchema` 自动转换为 Streamlit 表单组件：

```python
def schema_to_form(schema: dict) -> list[FormField]:
    """
    JSON Schema 类型 → Streamlit 组件映射：
    - string (no enum) → st.text_input
    - string (with enum) → st.selectbox
    - number/integer → st.number_input
    - boolean → st.checkbox
    - array → st.text_area (JSON 编辑)
    - object → st.text_area (JSON 编辑)
    """
```

---

## 8. 质量保障

### 8.1 测试策略

| 测试类型 | 范围 | 工具 |
|----------|------|------|
| 单元测试 | Services 层业务逻辑 | pytest + pytest-asyncio |
| 集成测试 | MCP 连接和通信 | pytest + Mock MCP Server |
| UI 测试 | 关键用户流程 | 手动测试 |

### 8.2 代码规范

- 类型注解：所有函数必须有类型注解
- 文档字符串：所有 public 方法必须有 docstring
- Lint：使用 ruff 进行代码检查
- 格式化：使用 black + isort

---

## 9. 启动命令

```bash
# 安装依赖
uv sync

# 启动开发服务器
uv run streamlit run app.py --server.port 8501

# 运行测试
uv run pytest tests/ -v

# 代码检查
uv run ruff check src/
```

---

## 10. 附录

### 10.1 MCP 协议方法速查

| 方法 | 方向 | 说明 |
|------|------|------|
| `initialize` | C→S | 初始化连接 |
| `notifications/initialized` | C→S | 初始化完成通知 |
| `ping` | 双向 | 心跳检测 |
| `tools/list` | C→S | 列出可用工具 |
| `tools/call` | C→S | 调用工具 |
| `notifications/tools/list_changed` | S→C | 工具列表变更通知 |
| `resources/list` | C→S | 列出可用资源 |
| `resources/read` | C→S | 读取资源内容 |
| `resources/subscribe` | C→S | 订阅资源 |
| `resources/unsubscribe` | C→S | 取消订阅 |
| `notifications/resources/updated` | S→C | 资源更新通知 |
| `notifications/resources/list_changed` | S→C | 资源列表变更通知 |
| `prompts/list` | C→S | 列出可用提示词 |
| `prompts/get` | C→S | 获取提示词 |
| `notifications/prompts/list_changed` | S→C | 提示词列表变更通知 |
| `logging/setLevel` | C→S | 设置日志级别 |
| `notifications/message` | S→C | 日志消息通知 |
| `completion/complete` | C→S | 自动补全 |
| `sampling/createMessage` | S→C | 请求 LLM 采样 |
| `elicitation/create` | S→C | 请求用户输入 |

> C→S = Client 到 Server, S→C = Server 到 Client

### 10.2 JSON-RPC 2.0 错误码

| 错误码 | 含义 |
|--------|------|
| -32700 | Parse error（解析错误） |
| -32600 | Invalid Request（无效请求） |
| -32601 | Method not found（方法不存在） |
| -32602 | Invalid params（无效参数） |
| -32603 | Internal error（内部错误） |
| -32001 | Request timed out（请求超时） |
| -32002 | Server not initialized（Server 未初始化） |
| -32003 | Connection closed（连接已关闭） |
