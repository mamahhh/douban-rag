# 豆瓣 RAG 系统 📚

一个基于 RAG（检索增强生成）技术的豆瓣历史查询系统，支持电影、书籍、音乐和游戏记录。

## 功能特性

- 📤 **上传豆瓣导出数据** - 支持[豆伴](https://chromewebstore.google.com/detail/%E8%B1%86%E4%BC%B4%EF%BC%9A%E8%B1%86%E7%93%A3%E8%B4%A6%E5%8F%B7%E5%A4%87%E4%BB%BD%E5%B7%A5%E5%85%B7/ghppfgfeoafdcaebjoglabppkfmbcjdd)等工具导出的 CSV 和 XLSX 文件
- 🔍 **语义搜索** - 基于语义理解查找内容，而非简单关键词匹配
- 💬 **自然语言问答** - 用中文询问你的观影/阅读历史
- 🔄 **MCP 集成** - 连接 Claude、Gemini、ChatGPT 等 AI 助手
- 📊 **数据统计** - 查看媒体类型、评分分布等统计信息

## 技术栈

- **后端**: FastAPI + LlamaIndex + ChromaDB
- **前端**: Streamlit
- **向量模型**: BGE-M3 (BAAI/bge-m3)
- **重排序模型**: BGE-Reranker-v2-m3
- **大语言模型**: Google Gemini

## 快速开始

### 1. 环境配置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r backend/requirements.txt
pip install streamlit requests
```

### 2. 配置 API 密钥

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 GOOGLE_API_KEY
```

### 3. 启动应用

```bash
# 终端 1: 启动后端
cd backend
uvicorn app.main:app --reload --port 8000

# 终端 2: 启动前端
cd frontend
streamlit run app.py --server.port 8501
```

### 4. 上传数据

1. 打开 http://localhost:8501
2. 上传你的豆瓣导出文件（[豆伴](https://chromewebstore.google.com/detail/%E8%B1%86%E4%BC%B4%EF%BC%9A%E8%B1%86%E7%93%A3%E8%B4%A6%E5%8F%B7%E5%A4%87%E4%BB%BD%E5%B7%A5%E5%85%B7/ghppfgfeoafdcaebjoglabppkfmbcjdd)导出的 Excel 文件）
3. 开始与你的数据对话！

## MCP 集成

将豆瓣 RAG 系统连接到 AI 助手：

```json
{
  "mcpServers": {
    "douban-rag": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/douban-rag"
    }
  }
}
```

### 可用的 MCP 工具

| 工具 | 描述 |
|------|------|
| `search_douban` | 语义搜索豆瓣历史记录 |
| `ask_douban` | 用自然语言提问 |
| `get_stats` | 获取统计概览 |

## 项目结构

```
douban-rag/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI 接口
│   │   ├── core/         # 配置文件
│   │   └── rag/          # RAG 逻辑（数据处理、检索、引擎）
│   └── requirements.txt
├── frontend/
│   └── app.py            # Streamlit 界面
├── mcp_server.py         # MCP 服务器
└── data/                 # 数据目录（已忽略）
```

## 许可证

MIT
