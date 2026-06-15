# 🔬 智能研究助理 Agent

基于 LangGraph 构建的智能研究助理系统，能够自动识别问题类型并执行深度研究，生成专业报告。

## ✨ 核心功能

### 智能分类
- **研究模式**：自动识别需要深度研究的问题（如包含“研究”“最新”“分析”等关键词，或经 LLM 二次确认），执行搜索 → 阅读 → 整理 → 报告全流程。
- **对话模式**：日常闲聊、简单问题直接响应，无需搜索。
- **强制模式**：勾选前端“强制研究模式”复选框时，无论输入内容如何都强制走研究流程；未勾选时由系统自动判断（不发送 `research_mode` 字段，后端走自动分类）。
- **追问增强**：若上一轮已生成报告，追问时 `chat_agent` 会自动注入历史研究发现和向量知识库中的相关内容作为上下文，无需重新搜索。

### 深度研究能力
- 🌐 使用 Tavily 搜索引擎获取最新信息
- 📄 自动抓取并解析网页内容
- 📊 智能整理研究发现
- 📝 生成结构化 Markdown 报告
- 🧠 自动将报告存入 ChromaDB 向量知识库，供后续追问或相关查询时召回

### 多会话管理
- 🔒 基于 Session ID 的多用户隔离
- 💾 对话历史持久化存储（SQLite）
- 🔄 支持跨会话追问，上下文连贯

### 可观测性
- 📈 Token 消耗实时统计
- ⚠️ 阈值告警机制
- 📋 研究步骤透明展示（前端 SSE 流式推送进度）

## 🚀 快速开始

### 环境要求
- Python 3.10+
- OpenAI API Key（或 DeepSeek 等兼容 API）
- Tavily API Key（可选，用于网络搜索）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 并重命名为 `.env`，填写相关配置：

```env
# Chat模型配置
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat

# Tavily搜索API（可选）
TAVILY_API_KEY=your-tavily-key

# 数据存储路径（请根据实际项目路径修改）
PROJECT_ROOT=D:\桌面\ai agent学习\简历三项目\research_assistant
DATA_ROOT=D:\桌面\ai agent学习\简历三项目\research_assistant\output
```

### 启动服务

```bash
python main.py
```

服务启动后访问：http://localhost:8000

## 📡 API 使用

### 发送消息

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我查一下2025年人工智能的最新发展趋势",
    "session_id": "user123",
    "research_mode": null
  }'
```

### 响应示例

```json
{
  "response": "# 关于“2025年人工智能发展趋势”的研究报告...",
  "session_id": "user123",
  "tokens_used": 1532,
  "research_used": true
}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message | string | 是 | 用户输入消息 |
| session_id | string | 否 | 会话ID，默认"default" |
| research_mode | bool | 否 | 强制模式：`true`=研究，不传或`null`=自动 |

## 🏗️ 项目架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI 服务层                           │
│                         main.py                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                     LangGraph 状态机                            │
│   ┌─────────┐    ┌─────────┐    ┌────────────┐    ┌─────────┐  │
│   │classifier│───▶│ planner │───▶│ researcher │───▶│  chat   │  │
│   └─────────┘    └─────────┘    └────────────┘    └─────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                         Skill 工具层                            │
│    web_search | web_fetch | report_gen | vector_search         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                        持久化层                                 │
│              PersistentMemory + MemorySaver                     │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 目录结构

```
research_assistant/
├── agent/                    # Agent核心模块
│   ├── agents/               # 子Agent实现
│   │   ├── classifier_agent.py   # 问题分类器
│   │   ├── planner_agent.py      # 研究规划器
│   │   ├── researcher_agent.py   # 研究执行器
│   │   └── chat_agent.py         # 对话响应器
│   ├── graph.py              # LangGraph状态机
│   ├── state.py              # 状态定义
│   └── supervisor.py         # 中心调度器
├── skills/                   # 工具技能层
│   ├── web_search_skill.py   # 网络搜索（Tavily）
│   ├── web_fetch_skill.py    # 网页抓取
│   ├── report_gen_skill.py   # 报告生成
│   ├── vector_search_skill.py # 向量检索与存储
│   └── mcp_adapter.py        # MCP适配器
├── memory/                   # 持久化存储
│   └── persistent_memory.py  # SQLite会话存储
├── utils/                    # 工具函数
│   ├── token_monitor.py      # Token监控
│   ├── input_normalizer.py   # 输入标准化与意图分析
│   └── vector_store.py       # ChromaDB向量存储封装
├── frontend/                 # 前端界面
│   ├── index.html            # 主页面
│   └── style.css             # 样式文件
├── main.py                   # 服务入口
└── requirements.txt          # 依赖列表
```

## 🧠 Agent 节点说明

### Classifier（分类器）
- 判断用户问题类型：`research` 或 `chat`
- 基于本地关键词分析 + LLM 二次确认
- 支持强制模式覆盖

### Planner（规划器）
- 根据问题生成研究步骤
- 步骤包含：搜索、阅读、整理、报告

### Researcher（研究员）
- 执行研究步骤
- 调用对应 Skill 工具
- 收集研究发现

### Chat（对话器）
- 直接响应日常对话
- 支持基于历史研究发现和向量知识库的上下文增强回答

## 🛠️ Skill 体系

| Skill | 名称 | 功能 |
|-------|------|------|
| web_search | WebSearchSkill | 使用 Tavily 搜索网络信息 |
| web_fetch | WebFetchSkill | 抓取网页正文内容 |
| report_gen | ReportGenSkill | 生成结构化研究报告，并存入 ChromaDB |
| vector_search | VectorSearchSkill | 从知识库中语义检索历史报告 |
| vector_store | VectorStoreSkill | 将文档存入 ChromaDB 知识库 |

## 📊 Token 监控

系统内置 Token 监控功能：
- 默认阈值：4000 Token
- 超过阈值自动告警
- 统计输入/输出 Token 消耗

## 🔧 配置说明

### 模型配置
- 支持 OpenAI 兼容 API
- 默认使用 DeepSeek 模型
- 可通过环境变量切换模型

### 存储配置
- 对话历史存储在 SQLite 数据库
- 默认路径：`./output/memory.db`
- 可通过 `DATA_ROOT` 环境变量自定义

## 📝 使用示例

### 研究模式示例

**用户输入**：
```
帮我查一下2025年人工智能的最新发展趋势
```

**执行流程**：
1. 分类器识别为 `research`
2. 规划器生成步骤：搜索 → 阅读 → 整理 → 报告
3. 研究员执行搜索，获取相关资料
4. 抓取关键网页内容
5. 整理研究发现
6. 生成结构化报告

**输出**：
```markdown
# 关于“2025年人工智能发展趋势”的研究报告

研究时间：2025-01-15 10:30

## 研究发现

### 1. 搜索：2025年人工智能发展趋势
...

### 2. 网页: https://example.com/ai-trends-2025
...

### 3. 核心发现
...

## 结论
...
```

### 对话模式示例

**用户输入**：
```
你好，今天天气不错
```

**执行流程**：
1. 分类器识别为 `chat`
2. 直接调用 LLM 响应

**输出**：
```
你好！今天天气确实很好，希望你有一个愉快的一天！有什么我可以帮助你的吗？
```

### 追问示例

**第一轮**：
```
研究一下2025年AI趋势
```
（系统输出研究报告）

**第二轮**：
```
那它会对就业有什么影响？
```

**执行流程**：
1. 分类器判断新问题为 `chat`（不含研究关键词）
2. 进入 `chat` 节点
3. `chat_agent` 检测到已有报告，自动注入上一轮的 `findings` 及向量知识库中相关报告内容作为上下文
4. 基于上下文回答追问，无需重新搜索

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---
