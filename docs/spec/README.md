# AI 智能标书系统 Spec 文档

## 1. 文档目标

本目录用于沉淀“AI 智能标书系统”的规格说明，目标是让后续开发可以直接依据文档进行：

- 页面与交互实现
- 后端接口设计
- Dify 工作流编排
- 数据库建模
- 测试与验收

本轮仅输出规格文档，不包含业务代码实现。

## 2. 项目范围

本项目面向“招标文件解析、标书目录编辑、分章生成、废标项检查、Word 导出”这条核心链路，技术栈固定为：

- 前端：Vue 3 + TypeScript
- 后端：Python + Flask + uv
- 大模型平台：Dify

## 3. 阅读顺序

建议按以下顺序阅读：

1. [01-product-overview.md](D:/code/标书系统最终版/docs/spec/01-product-overview.md)
2. [02-prd.md](D:/code/标书系统最终版/docs/spec/02-prd.md)
3. [03-functional-spec.md](D:/code/标书系统最终版/docs/spec/03-functional-spec.md)
4. [04-architecture.md](D:/code/标书系统最终版/docs/spec/04-architecture.md)
5. [05-api-data-model.md](D:/code/标书系统最终版/docs/spec/05-api-data-model.md)
6. [06-llm-workflow-and-prompts.md](D:/code/标书系统最终版/docs/spec/06-llm-workflow-and-prompts.md)
7. [07-word-export-spec.md](D:/code/标书系统最终版/docs/spec/07-word-export-spec.md)
8. [08-test-and-milestones.md](D:/code/标书系统最终版/docs/spec/08-test-and-milestones.md)

## 4. 本轮默认假设

为避免规格空转，本轮先采用以下默认假设：

- 当前阶段优先做单组织内部使用，不先设计复杂的多租户体系。
- 当前阶段不把登录、权限中心、审批流作为首期范围。
- 项目级数据需要持久化保存，支持后续继续编辑和重新导出。
- 招标文件可能是 PDF、Word 两类为主，后续可扩展其他格式。
- 知识库既要支持项目通用资料，也要支持企业通用资料。
- 废标项检查既需要大模型理解能力，也需要结构化规则兜底。
- Word 导出以“固定模板”方式实现，不做任意样式自由编排。

如果后面你希望把“用户权限、多人协作、审批、版本比对、历史追踪”也纳入范围，我们可以在这套 spec 上继续扩展。
