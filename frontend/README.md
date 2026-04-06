# 前端 — Vue 3 + Vite

## 环境要求

- Node.js ≥ 20.19 或 ≥ 22.12

## 主要依赖

| 包 | 用途 |
|---|---|
| Vue 3 | UI 框架 |
| Vue Router 5 | 路由 |
| Pinia | 状态管理 |
| Element Plus | UI 组件库 |
| Axios | HTTP 请求 |
| Vite 7 | 构建工具 |
| TypeScript | 类型检查 |

## 快速启动

```bash
cd frontend

# 复制并填写环境变量
cp .env.example .env

# 安装依赖
npm install

# 开发模式
npm run dev
```

前端默认运行在 `http://localhost:5173`。

## 常用脚本

```bash
npm run dev          # 开发服务器（热更新）
npm run build        # 生产构建
npm run type-check   # TypeScript 类型检查
npm run preview      # 预览构建产物
```

## 环境变量

复制 `.env.example` 为 `.env`：

```dotenv
VITE_API_BASE_URL=http://localhost:5000   # 后端接口地址
```

## 目录结构

```
frontend/src/
├── api/            # Axios 接口封装
├── components/
│   └── workspace/  # 工作台核心组件（GenerationPanel、KnowledgePanel 等）
├── views/          # 页面（WorkspacePage 等）
├── stores/         # Pinia 状态
├── router/         # 路由配置
└── assets/         # 静态资源
```
