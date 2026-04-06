# 05. 接口与数据模型草案

## 1. 数据模型

以下为首期建议的核心实体。

## 1.1 Project

字段建议：

- `id`
- `name`
- `bidder_name`
- `tender_title`
- `tender_no`
- `status`
- `current_step`
- `created_at`
- `updated_at`

说明：

- 一个项目对应一次标书编制过程。

## 1.2 TenderFile

字段建议：

- `id`
- `project_id`
- `file_name`
- `file_type`
- `file_size`
- `storage_path`
- `parsed_text_path`
- `parse_status`
- `parse_error_message`
- `uploaded_at`

## 1.3 OutlineNode

字段建议：

- `id`
- `project_id`
- `parent_id`
- `level`
- `title`
- `order_no`
- `node_type`
- `prompt_requirement`
- `knowledge_scope`
- `is_enabled`
- `created_at`
- `updated_at`

说明：

- `node_type` 可取 `chapter`、`section`。
- 首期生成粒度建议基于一级 `chapter`。

## 1.4 ChapterContent

字段建议：

- `id`
- `project_id`
- `outline_node_id`
- `current_version_no`
- `content`
- `content_format`
- `status`
- `last_generated_at`
- `last_edited_at`
- `updated_at`

## 1.5 ChapterContentVersion

字段建议：

- `id`
- `chapter_content_id`
- `version_no`
- `source_type`
- `source_task_id`
- `content`
- `created_at`

说明：

- `source_type` 可取 `ai_generated`、`manual_edit`、`regenerated`。

## 1.6 KnowledgeAsset

字段建议：

- `id`
- `name`
- `category`
- `file_name`
- `storage_path`
- `dify_dataset_id`
- `dify_document_id`
- `status`
- `created_at`

## 1.7 ProjectKnowledgeBinding

字段建议：

- `id`
- `project_id`
- `knowledge_asset_id`
- `scope_type`
- `scope_node_id`
- `created_at`

说明：

- `scope_type` 可取 `project`、`chapter`。

## 1.8 GenerationTask

字段建议：

- `id`
- `project_id`
- `outline_node_id`
- `task_type`
- `status`
- `request_payload`
- `result_summary`
- `error_message`
- `started_at`
- `finished_at`

## 1.9 BidCheckResult

字段建议：

- `id`
- `project_id`
- `check_version`
- `risk_level`
- `rule_type`
- `title`
- `description`
- `suggestion`
- `related_outline_node_id`
- `status`
- `created_at`

## 1.10 ExportTask

字段建议：

- `id`
- `project_id`
- `template_name`
- `status`
- `file_path`
- `error_message`
- `created_at`
- `finished_at`

## 2. 接口风格建议

建议使用 REST API + SSE。

- REST 用于增删改查
- SSE 用于章节生成流式输出

接口前缀建议：

- `/api/projects`
- `/api/knowledge`
- `/api/exports`

## 3. 核心接口清单

## 3.1 项目管理

### `POST /api/projects`

作用：

- 创建项目

请求体示例：

```json
{
  "name": "某某项目投标文件",
  "bidderName": "某某科技有限公司",
  "tenderTitle": "某项目建设招标",
  "tenderNo": "ABC-2026-001"
}
```

### `GET /api/projects`

作用：

- 查询项目列表

### `GET /api/projects/{projectId}`

作用：

- 查询项目详情

## 3.2 招标文件上传与解析

### `POST /api/projects/{projectId}/tender-file`

作用：

- 上传招标文件

表单字段：

- `file`

返回字段建议：

- `fileId`
- `parseStatus`

### `POST /api/projects/{projectId}/tender-file/parse`

作用：

- 手动触发解析

返回字段建议：

- `parseStatus`
- `outlineVersion`

### `GET /api/projects/{projectId}/tender-file`

作用：

- 获取招标文件信息与解析状态

## 3.3 目录树管理

### `GET /api/projects/{projectId}/outline`

作用：

- 获取目录树

返回示例：

```json
{
  "projectId": "p1",
  "nodes": [
    {
      "id": "n1",
      "parentId": null,
      "level": 1,
      "title": "第一章 项目概述",
      "orderNo": 1,
      "nodeType": "chapter",
      "promptRequirement": "突出项目背景、建设目标和总体认识"
    }
  ]
}
```

### `PUT /api/projects/{projectId}/outline`

作用：

- 整体保存目录树

请求体建议：

```json
{
  "nodes": [
    {
      "id": "n1",
      "parentId": null,
      "level": 1,
      "title": "第一章 项目概述",
      "orderNo": 1,
      "nodeType": "chapter",
      "promptRequirement": "突出项目背景、建设目标和总体认识",
      "knowledgeScope": ["企业案例库", "资质库"],
      "isEnabled": true
    }
  ]
}
```

## 3.4 章节内容管理

### `GET /api/projects/{projectId}/chapters/{nodeId}`

作用：

- 获取指定章节当前内容

返回字段建议：

- `nodeId`
- `title`
- `status`
- `currentVersionNo`
- `content`
- `versions`

### `PUT /api/projects/{projectId}/chapters/{nodeId}`

作用：

- 保存人工编辑内容

请求体示例：

```json
{
  "content": "这里是用户修改后的章节内容"
}
```

## 3.5 章节生成

### `POST /api/projects/{projectId}/chapters/{nodeId}/generate`

作用：

- 创建章节生成任务

请求体建议：

```json
{
  "mode": "replace",
  "useKnowledge": true,
  "includePreviousSummary": true
}
```

返回字段建议：

- `taskId`
- `streamUrl`

### `GET /api/projects/{projectId}/generation-tasks/{taskId}/stream`

作用：

- SSE 流式接收生成内容

事件建议：

```text
event: start
data: {"taskId":"t1","nodeId":"n1"}

event: delta
data: {"text":"第一段内容"}

event: progress
data: {"message":"正在整理本章小节"}

event: complete
data: {"versionNo":3}
```

### `POST /api/projects/{projectId}/chapters/{nodeId}/regenerate`

作用：

- 重新生成章节

说明：

- 本质上可复用生成接口，也可以单独暴露语义化接口。

## 3.6 知识库管理

### `POST /api/knowledge/assets`

作用：

- 上传知识文件

### `GET /api/knowledge/assets`

作用：

- 查询知识文件列表

### `POST /api/projects/{projectId}/knowledge-bindings`

作用：

- 绑定知识库到项目或章节

请求体示例：

```json
{
  "knowledgeAssetIds": ["k1", "k2"],
  "scopeType": "chapter",
  "scopeNodeId": "n1"
}
```

## 3.7 废标检查

### `POST /api/projects/{projectId}/bid-check`

作用：

- 发起废标检查

返回字段建议：

- `checkVersion`
- `summary`
- `results`

返回结果示例：

```json
{
  "checkVersion": 2,
  "summary": {
    "high": 1,
    "medium": 3,
    "low": 4
  },
  "results": [
    {
      "riskLevel": "high",
      "title": "缺少法定代表人授权响应",
      "description": "招标文件要求提供授权证明，当前正文未体现",
      "suggestion": "在商务响应章节补充法定代表人授权材料说明",
      "relatedOutlineNodeId": "n8"
    }
  ]
}
```

## 3.8 导出

### `POST /api/projects/{projectId}/exports`

作用：

- 发起 Word 导出

请求体示例：

```json
{
  "templateName": "standard-bid-v1",
  "coverFields": {
    "projectName": "某某项目投标文件",
    "bidderName": "某某科技有限公司"
  }
}
```

### `GET /api/projects/{projectId}/exports`

作用：

- 获取导出记录列表

### `GET /api/projects/{projectId}/exports/{exportId}/download`

作用：

- 下载 Word 文件

## 4. 与 Dify 的接口边界

后端对外暴露业务接口，对内调用 Dify 工作流。

后端需要向 Dify 组织以下上下文：

- 招标文件摘要
- 当前章节标题及层级结构
- 当前章节提示词
- 当前项目绑定的知识范围
- 必要的前文章节摘要

后端不应把数据库结构直接暴露给 Dify，而应转换为简洁的工作流输入对象。

## 5. 返回码与错误约定

建议统一返回格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

错误场景建议：

- `4001` 文件类型不支持
- `4002` 文件解析失败
- `4003` 目录树校验失败
- `4004` 生成任务创建失败
- `4005` Dify 调用失败
- `4006` 导出失败

## 6. 版本化建议

- 首期可不做复杂版本前缀，但需预留 `/api/v1`
- 章节内容必须保留内部版本号
- 废标检查结果建议保留检查版本号
