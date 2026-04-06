# 后端 — Flask + Dify

## 环境要求

- Python ≥ 3.11
- [uv](https://github.com/astral-sh/uv)（推荐）或 pip

## 主要依赖

| 包 | 用途 |
|---|---|
| Flask 3 | Web 框架 |
| Flask-SQLAlchemy | ORM |
| python-docx | Word 文件生成 |
| pdfplumber / PyPDF2 | PDF 解析 |
| requests | 调用 Dify API |
| python-dotenv | 读取 .env |

## 快速启动

```bash
cd backend

# 复制并填写环境变量
cp .env.example .env

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 安装依赖（推荐 uv）
pip install uv
uv sync

# 启动开发服务器
python app.py
```

服务默认运行在 `http://localhost:5000`。

## 目录结构

```
backend/
├── app.py            # 应用入口，注册蓝图
├── config.py         # 从 .env 读取配置
├── models.py         # SQLAlchemy 数据模型
├── extensions.py     # db / 扩展初始化
├── routes/
│   ├── projects.py   # 项目 CRUD
│   ├── generation.py # AI 章节生成（流式）
│   ├── export.py     # Word 导出
│   └── knowledge.py  # 知识库管理
└── utils/
    ├── dify_client.py     # Dify API 封装
    └── knowledge_client.py
```

## 环境变量

复制 `.env.example` 为 `.env` 并填写：

```dotenv
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=<自定义随机字符串>

DATABASE_URL=sqlite:///bid_system.db
UPLOAD_FOLDER=./uploads
MAX_CONTENT_LENGTH=52428800   # 50 MB

# Dify（必填）
DIFY_BASE_URL=http://<your-dify-host>/v1
DIFY_API_KEY_PARSE=app-xxxx
DIFY_API_KEY_GENERATE=app-xxxx
DIFY_API_KEY_CHECK=app-xxxx
```

## 数据库

首次启动自动创建 SQLite 数据库（`backend/instance/bid_system.db`）。
该文件已加入 `.gitignore`，不会提交到版本库。
