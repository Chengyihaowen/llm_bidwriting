# 10. Dify 工作流逐节点配置、完整 Prompt 与后端字段映射

## 1. 文档目标

本文档用于把上一份拆分设计文档继续落到“可以直接搭建”的粒度，覆盖以下 3 部分：

1. 3 个工作流在 Dify 里的逐节点配置表
2. 可直接复制到 Dify 的完整 Prompt
3. Flask 后端字段映射与调用示例

对应关系：

- 工作流1：招标文件解析工作流
- 工作流2：章节生成工作流
- 工作流3：废标检查工作流

当前约束：

- 暂不接知识库
- 前端按一级章节逐章生成
- 生成结果为 Markdown
- 后端统一调 Dify，前端不直连 Dify

---

## 2. 统一命名建议

为了便于后端和 Dify 管理，建议统一采用下面的命名。

### 2.1 工作流命名

| 工作流 | 建议名称 | 说明 |
|--------|----------|------|
| 工作流1 | `bid-file-parse-workflow` | 解析招标文件，产出目录和摘要 |
| 工作流2 | `bid-chapter-generate-workflow` | 按当前大章生成 Markdown |
| 工作流3 | `bid-risk-check-workflow` | 检查废标/强制响应风险 |

### 2.2 Dify 输入变量命名

| 变量名 | 含义 |
|--------|------|
| `bid_text` | 招标文件纯文本 |
| `parsed_bid` | 招标文件结构化摘要 |
| `outline_json` | 目录树 JSON 字符串 |
| `risk_clauses` | 风险条款摘要 |
| `format_template` | 模板摘要 |
| `chapter_title` | 当前一级章节标题 |
| `chapter_structure` | 当前章节的结构文本 |
| `prompt_requirement` | 用户给当前章节补充的写作要求 |
| `chapter_content` | 当前章节生成结果 |
| `chapters_content` | 项目所有章节拼接后的全文 |
| `results` | 风险检查结果数组 |
| `summary` | 风险汇总 |

---

## 3. 工作流1：招标文件解析工作流

## 3.1 工作流目标

输入招标文件纯文本，输出：

- 招标文件摘要 `parsed_bid`
- 目录树 JSON `outline_json`
- 风险条款摘要 `risk_clauses`
- 模板摘要 `format_template`

## 3.2 Dify 逐节点配置表

| 顺序 | 节点名称 | 节点类型 | 输入 | 输出 | 说明 |
|------|----------|----------|------|------|------|
| 1 | Start | 开始节点 | `bid_text` | `bid_text` | 接收后端传入的招标文件纯文本 |
| 2 | ParseBid | LLM | `bid_text` | `parsed_bid` | 提取项目、资格、评分、技术、商务、偏差等摘要 |
| 3 | ExtractOutline | LLM | `bid_text` | `outline_json` | 输出合法 JSON 目录树 |
| 4 | ExtractRiskClauses | LLM | `bid_text` | `risk_clauses` | 输出否决条款、星号条款、强制响应项 |
| 5 | ExtractFormatTemplate | LLM | `bid_text` | `format_template` | 输出投标文件格式模板摘要 |
| 6 | End | 结束节点 | `parsed_bid`, `outline_json`, `risk_clauses`, `format_template` | 同左 | 返回给后端 |

## 3.3 Start 节点配置

### 输入变量

| 变量名 | 类型 | 必填 | 示例 |
|--------|------|------|------|
| `bid_text` | Paragraph / Long Text | 是 | 招标文件全文文本 |

### 后端传入示例

```json
{
  "inputs": {
    "bid_text": "第一章 招标公告......"
  },
  "response_mode": "blocking",
  "user": "bid-system"
}
```

---

## 3.4 ParseBid 节点配置

### 节点类型
- LLM

### 建议模型
- 大上下文模型
- 重点是稳定解析，不强调文采

### 输出变量
- `parsed_bid`

### System Prompt（可直接复制）

```text
你是一个通用招标文件解析引擎。
你的任务是从任意行业、任意类型的招标文件中提取结构化信息。

严格要求：
1. 所有信息必须从招标文件原文提取
2. 找不到的信息必须写“文件中未提及”
3. 所有金额、日期、比例、分值、编号必须按原文保留
4. 不允许猜测、不允许补全、不允许自行编造
5. 输出内容用于后续标书生成和合规检查，因此必须完整、准确、可复用
6. 输出使用清晰标题结构，不要输出 JSON，不要输出解释性前言
```

### User Prompt（可直接复制）

```text
请完整分析以下招标文件，并按照下面结构输出。
找不到的信息请写“文件中未提及”。

## A. 项目基本信息
- 项目名称：
- 招标编号：
- 招标人（采购人）：
- 招标代理机构：
- 项目概述（一句话描述采购什么）：
- 采购数量：
- 交货期/工期：
- 交货地点/服务地点：
- 资金来源：
- 最高投标限价（如有）：
- 投标有效期：
- 投标保证金金额及形式：
- 履约保证金比例及形式：

## B. 投标人资格要求
- 按原文逐条列出，尽量保留编号

## C. 评标办法
- 评标方法名称：
- 总分值：
- 各部分分值分配：
  - 商务/资格部分：
  - 技术部分：
  - 价格/报价部分：
- 商务/资格评分标准：
- 技术评分标准：
- 价格评分规则：
- 同分处理规则：

## D. 技术/供货/服务要求摘要
- 提取实质性技术要求、供货要求、服务要求、工作范围
- 尽量保留原文结构和编号

## E. 商务条款要点
- 合同类型：
- 付款方式及比例：
- 质保期：
- 售后服务要求：
- 违约责任要点：
- 知识产权归属：
- 保密要求：

## F. 偏差规定
- 是否允许偏差：
- 星号/关键条款偏差规定：
- 非星号条款负偏差限制：
- 偏差定义范围：

## G. 其他对标书撰写有直接影响的要求
- 例如签章要求、附件要求、响应格式要求、编制要求等

招标文件原文如下：
{{#sys.query#}}
{{bid_text}}
```

### 输出示例

```text
## A. 项目基本信息
- 项目名称：某某项目建设采购
- 招标编号：ABC-2026-001
...
```

---

## 3.5 ExtractOutline 节点配置

### 节点类型
- LLM

### 输出变量
- `outline_json`

### 关键要求
这个节点必须只输出合法 JSON，方便后端直接 `json.loads()`。

### System Prompt（可直接复制）

```text
你是投标文件目录提取器。
你的唯一任务是从招标文件中提取“投标文件组成/目录结构”，并输出合法 JSON。

严格要求：
1. 只输出 JSON 数组，不输出任何解释文字
2. 不输出 Markdown 标题，不输出前言，不输出结尾说明
3. 每个一级节点必须包含字段：title, promptRequirement, children
4. 每个二级节点必须包含字段：title, promptRequirement
5. children 必须始终存在，没有子节点时输出空数组 []
6. promptRequirement 要根据章节用途写出简短写作要求，长度控制在 15-60 字
7. 不要编造招标文件中没有的章节
8. 如果招标文件没有显式目录，但有明确“投标文件组成/响应内容”，可以整理为合理的一级章和二级节
9. 输出必须是可被标准 JSON 解析器直接解析的合法 JSON
```

### User Prompt（可直接复制）

```text
请从以下招标文件中提取投标文件目录结构，并输出 JSON 数组。

输出规则：
1. 仅输出 JSON 数组
2. 一级节点结构：
   {
     "title": "章节标题",
     "promptRequirement": "本章写作要求",
     "children": []
   }
3. 二级节点结构：
   {
     "title": "小节标题",
     "promptRequirement": "本节写作要求"
   }
4. 如果原文目录编号存在，请尽量保留在 title 中
5. 不要出现 id、parentId、level、orderNo 这些系统字段
6. 不要返回 null，字符串字段为空时也要给出合理内容

招标文件原文如下：
{{#sys.query#}}
{{bid_text}}
```

### 期望输出示例

```json
[
  {
    "title": "一 评分标准索引表",
    "promptRequirement": "招标项目的评分标准索引表",
    "children": []
  },
    {
    "title": "二 初步审查表",
    "promptRequirement": "招标项目的初步审查表",
    "children": [
      {
        "title": "1.资格性和符合性审查表",
        "promptRequirement": "招标文件的资格性和符合性审查表，必须严格遵照招标文件编写"
      }
    ]
  },
    {
    "title": "三 项目技术方案",
    "promptRequirement": "招标项目的项目技术方案",
    "children": [
      {
        "title": "1 概述",
        "promptRequirement": "围绕招标文件中的项目背景、建设必要性撰写。"
      },
      {
        "title": "2 技术要求",
        "promptRequirement": "招标文件的技术要求，包括2.1.大屏显示分系统（招标要求中的大屏显示分系统，包括2.1.1.LED显示子系统,2.1.2.音频扩声子系统），2.2。模拟座舱"
      }
    ]
  }
]
```

---

## 3.6 ExtractRiskClauses 节点配置

### 节点类型
- LLM

### 输出变量
- `risk_clauses`

### System Prompt（可直接复制）

```text
你是投标合规风险审查专家。
你的唯一任务是找出招标文件中所有可能导致投标被否决、废标、无效或必须重点响应的条款。

重点包括：
1. 星号条款、关键条款
2. 明确写有“否决”“废标”“无效”“拒绝”“不予接受”等后果的条款
3. 明确要求“必须”“应当”“不得偏离”的实质性响应条款

严格要求：
- 尽量逐条列出
- 保留原文关键信息
- 不得遗漏明显风险条款
- 不要输出 JSON，输出结构化 Markdown 文本
```

### User Prompt（可直接复制）

```text
请从以下招标文件中提取全部风险条款，并按照下面结构输出。

## A. 星号/关键条款
- 逐条列出：条款编号 / 条款摘要 / 所在章节 / 原文关键内容

## B. 否决性条款
- 逐条列出：否决条件 / 所在章节 / 原文关键内容

## C. 实质性响应要求
- 逐条列出：要求内容 / 所在章节 / 响应重点

## D. 风险提示总结
- 归纳最容易遗漏的 5-10 类要求

招标文件原文如下：
{{#sys.query#}}
{{bid_text}}
```

---

## 3.7 ExtractFormatTemplate 节点配置

### 节点类型
- LLM

### 输出变量
- `format_template`

### System Prompt（可直接复制）

```text
你是投标文件格式提取专家。
你的任务是从招标文件中提取投标文件格式要求和模板要求，供后续系统使用。

严格要求：
1. 重点提取投标文件组成、格式模板、表格结构、签章要求、编制要求
2. 尽量保留原文模板结构信息
3. 不输出 JSON，输出结构化 Markdown 摘要
4. 不要编造招标文件中没有的模板
```

### User Prompt（可直接复制）

```text
请从以下招标文件中提取投标文件格式要求，并按照下面结构输出。

## A. 投标文件目录/组成
## B. 常见模板及表格要求
- 投标函
- 偏差表
- 报价表
- 授权委托书
- 资格审查资料
- 其他声明/承诺书

## C. 签字盖章要求
## D. 正副本、装订、密封、电子版要求
## E. 对技术文件/商务文件/价格文件的特殊要求

招标文件原文如下：
{{#sys.query#}}
{{bid_text}}
```

---

## 3.8 End 节点输出配置

End 节点绑定以下输出：

- `parsed_bid`
- `outline_json`
- `risk_clauses`
- `format_template`

Dify 返回示例：

```json
{
  "data": {
    "outputs": {
      "parsed_bid": "...",
      "outline_json": "[...]",
      "risk_clauses": "...",
      "format_template": "..."
    }
  }
}
```

---

## 4. 工作流2：章节生成工作流（增强版：自动识别严格模板章节）

## 4.1 工作流目标

输入当前章节上下文，由工作流内部先自动判断当前章节属于：

1. **普通生成章节（normal）**
   用于技术方案、项目理解、服务方案、实施计划等自由撰写类章节，输出当前章节 Markdown 正文。

2. **严格模板章节（template）**
   用于招标文件已明确给出固定格式、固定表格、固定声明、固定偏差表、固定报价表等章节。
   该模式下必须：
   - 严格保留原始模板固定内容
   - 仅填写允许填写的位置
   - 不得改写原表格已有内容
   - 不得漏项
   - 不得加项
   - 不得改变行列结构、序号、表头、分项名称、注释说明

3. **混合章节（mixed）**
   同时包含普通正文和固定模板的章节。正文部分可生成，模板部分必须严格锁定。

工作流最终输出：
- `chapter_content`：当前章节最终内容
- `chapter_mode`：工作流自动判定的章节模式
- `validation_result`：模板校验结果 JSON（便于后端记录和调试）

## 4.2 Dify 逐节点配置表

| 顺序 | 节点名称 | 节点类型 | 输入 | 输出 | 说明 |
|------|----------|----------|------|------|------|
| 1 | Start | 开始节点 | `parsed_bid`, `format_template`, `chapter_title`, `chapter_structure`, `prompt_requirement`, `chapter_template_raw`, `fillable_rules` | 同左 | 接收后端传入的章节生成参数 |
| 2 | DetectChapterMode | LLM | `chapter_title`, `chapter_structure`, `chapter_template_raw`, `fillable_rules`, `format_template` | `chapter_mode`, `mode_reason` | 自动判断当前章节是 normal / template / mixed |
| 3 | RouteChapterMode | 条件分支 / IF-ELSE | `chapter_mode` | 路由结果 | 根据自动识别结果决定走普通生成还是模板填充 |
| 4A | GenerateNormalChapter | LLM | `parsed_bid`, `chapter_title`, `chapter_structure`, `prompt_requirement` | `chapter_content_draft` | 普通章节生成 |
| 4B | FillTemplateStrict | LLM | `parsed_bid`, `format_template`, `chapter_title`, `chapter_structure`, `prompt_requirement`, `chapter_mode`, `chapter_template_raw`, `fillable_rules` | `chapter_content_draft` | 严格模板填充 |
| 5 | ValidateTemplate | LLM | `chapter_mode`, `chapter_template_raw`, `chapter_content_draft`, `fillable_rules` | `validation_result` | 对 template / mixed 模式做模板一致性校验 |
| 6 | End | 结束节点 | `chapter_content_draft`, `chapter_mode`, `validation_result` | `chapter_content`, `chapter_mode`, `validation_result` | 返回给后端 |

## 4.3 Start 节点配置

### 输入变量

| 变量名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `parsed_bid` | Long Text | 是 | 招标文件解析摘要 |
| `format_template` | Long Text | 否 | 招标文件格式摘要，辅助识别章节用途 |
| `chapter_title` | Text | 是 | 当前一级章节标题 |
| `chapter_structure` | Long Text | 是 | 当前章节结构文本 |
| `prompt_requirement` | Long Text | 否 | 用户补充写作要求 |
| `chapter_template_raw` | Long Text | 否 | 当前章节对应的原始模板内容，要求尽量保真 |
| `fillable_rules` | Long Text | 否 | 当前章节填写规则说明 |

### 章节模式说明

| 模式 | 含义 |
|------|------|
| `normal` | 普通生成，不依赖模板 |
| `template` | 完全按原始模板填充，不允许自由发挥 |
| `mixed` | 同时包含正文和模板，正文可生成，模板部分必须严格锁定 |

### 后端传入示例：普通章节

```json
{
  "inputs": {
    "parsed_bid": "## A. 项目基本信息...",
    "format_template": "",
    "chapter_title": "第三章 技术方案",
    "chapter_structure": "# 第三章 技术方案\n## 3.1 总体设计思路\n## 3.2 技术路线\n## 3.3 实施计划",
    "prompt_requirement": "重点突出技术完整性、实施可行性和对评分点的覆盖",
    "chapter_template_raw": "",
    "fillable_rules": ""
  },
  "response_mode": "streaming",
  "user": "bid-system"
}
```

### 后端传入示例：疑似模板章节

```json
{
  "inputs": {
    "parsed_bid": "## A. 项目基本信息...",
    "format_template": "## A. 投标文件目录/组成 ...",
    "chapter_title": "四、商务偏差表",
    "chapter_structure": "# 四、商务偏差表",
    "prompt_requirement": "仅填写投标应答和偏差说明，不得改动原有条款",
    "chapter_template_raw": "| 序号 | 招标文件条款内容 | 招标文件条款内容 | 投标应答 | 偏差说明 |\n|---|---|---|---|---|\n| 1 | 货物产地 | 见投标人须知前附表1.4.3 |  |  |\n| 2 | 交货期 | 见第一章招标公告 |  |  |",
    "fillable_rules": "1. 固定保留全部行列和表头；2. 仅填写投标应答与偏差说明空白处；3. 不得新增条目；4. 无法确定则保留空白"
  },
  "response_mode": "streaming",
  "user": "bid-system"
}
```

---

## 4.4 DetectChapterMode 节点配置

### 节点类型
- LLM

### 输出变量
- `chapter_mode`
- `mode_reason`

### 节点目标
在不修改前端入参的前提下，由工作流内部自动识别当前章节属于：
- `normal`
- `template`
- `mixed`

### 判定原则

优先判为 `template` / `mixed` 的典型情况：
- 章节标题或结构中包含：偏差表、报价表、授权书、承诺书、声明、资格审查资料、情况表、分项报价表、技术偏差表、商务偏差表等字样
- 输入中存在明显表格模板、固定声明、固定格式文本
- 存在“见招标公告”“见投标人须知前附表”“不得新增”“逐条填写”“按表填写”等强约束表述

### System Prompt（可直接复制）

```text
你是投标文件章节类型识别助手。

你的任务是根据章节标题、章节结构、原始模板和填写规则，判断当前章节属于以下三种模式之一：
- normal
- template
- mixed

判断标准：
1. normal：主要是自由撰写型正文，没有固定模板约束。
2. template：主要是固定格式、固定表格、固定声明、固定偏差表、固定报价表等，必须按模板填写。
3. mixed：既包含自由撰写正文，又包含必须严格保留的模板部分。

严格要求：
1. 只输出 JSON，不输出解释文字。
2. 顶级字段固定为：chapter_mode, mode_reason。
3. chapter_mode 只允许为 normal、template、mixed。
4. 如果存在明显表格模板、固定表头、固定条款、固定声明，优先判断为 template 或 mixed。
5. 如果章节标题本身就是偏差表、报价表、授权书、承诺书、声明、资格表等，通常应判断为 template。
6. mode_reason 用一句简短中文说明判断依据。
```

### User Prompt（可直接复制）

```text
请判断当前章节属于哪种生成模式，并输出 JSON。

【当前章节标题】
{{chapter_title}}

【当前章节结构】
{{chapter_structure}}

【原始模板】
{{chapter_template_raw}}

【填写规则】
{{fillable_rules}}

【招标文件格式摘要】
{{format_template}}

输出格式如下：
{
  "chapter_mode": "normal | template | mixed",
  "mode_reason": "简要判断依据"
}
```

### 输出示例

```json
{
  "chapter_mode": "template",
  "mode_reason": "章节标题为商务偏差表，且输入中包含固定表头和逐项填写规则。"
}
```

---

## 4.5 RouteChapterMode 节点配置

### 节点类型
- 条件分支 / IF-ELSE

### 路由规则建议

#### 分支1：普通生成
条件：

```text
chapter_mode == "normal"
```

流向：
- `GenerateNormalChapter`

#### 分支2：严格模板填充
条件：

```text
chapter_mode == "template" or chapter_mode == "mixed"
```

流向：
- `FillTemplateStrict`

### 说明
这一层的目标是把“自由写作型章节”和“模板锁定型章节”彻底分开，避免同一个 Prompt 同时承担两类任务而失控。

---

## 4.6 GenerateNormalChapter 节点配置

### 节点类型
- LLM

### 输出变量
- `chapter_content_draft`

### System Prompt（可直接复制）

```text
你是专业的投标文件撰写助手。
你的任务是根据招标文件解析摘要、当前章节结构和用户要求，生成当前章节的标书正文。

严格要求：
1. 只生成当前章节内容，不生成其他章节
2. 输出必须为 Markdown
3. 标题层级必须严格跟随 chapter_structure
4. 必须以 chapter_title 对应的一级标题开始
5. 如果存在二级小节，必须逐个展开
6. 语言必须正式、专业、适合标书初稿
7. 不得虚构金额、日期、资质、证书、项目业绩、专利、参数、品牌等事实性信息
8. 对于文件未明确给出的内容，使用稳妥、审慎、通用的表述，不夸大承诺
9. 尽量覆盖招标文件中的评分点、响应点和实质性要求
10. 不输出任何解释、说明、前言或“以下为生成结果”之类内容
```

### User Prompt（可直接复制）

```text
请生成以下标书章节内容。

【章节模式】
{{chapter_mode}}

【招标文件解析摘要】
{{parsed_bid}}

【当前章节标题】
{{chapter_title}}

【当前章节结构】
{{chapter_structure}}

【用户补充要求】
{{prompt_requirement}}

请严格遵守以下生成要求：
1. 只输出当前章节 Markdown 正文
2. 必须从当前章节一级标题开始
3. 所有二级标题必须按 chapter_structure 展开
4. 不要漏掉任何已经给出的子标题
5. 内容应可直接作为网页中的章节初稿使用
6. 避免空泛套话，尽量具体但不要虚构事实
7. 如果章节更偏“响应性内容”，要体现对招标要求的对应说明
```

---

## 4.7 FillTemplateStrict 节点配置

### 节点类型
- LLM

### 输出变量
- `chapter_content_draft`

### 节点目标
用于固定格式章节、固定表格章节、偏差表、报价表、授权书、声明书、资格表等内容生成。
核心目标不是“写”，而是“按模板严格填”。

### System Prompt（可直接复制）

```text
你是投标文件“严格模板填充助手”。

你的唯一任务是：基于招标文件原始模板，在不改变原模板固定内容的前提下，填写允许填写的位置。

这是一个“锁模板”任务，不是自由写作任务。

严格规则：
1. 原始模板中的所有非空固定内容都视为锁定内容，绝对不得修改、删减、改写、同义替换、重排顺序。
2. 锁定内容包括但不限于：标题、序号、表头、条款名称、固定说明、注释、已有单元格文字、星号、编号、括号、标点、单位。
3. 只允许填写以下位置：
   - 原模板中的空白单元格
   - 下划线、空括号、留白处
   - 明确要求“由投标人填写”的位置
4. 不允许新增任何原模板中不存在的内容，包括：
   - 不允许新增行
   - 不允许新增列
   - 不允许新增条目
   - 不允许新增说明文字
   - 不允许新增注释
   - 不允许新增小标题
5. 不允许漏掉原模板已有项目。原模板有几行几列、几个条目，输出就必须保留几行几列、几个条目。
6. 对表格，必须严格保持：
   - 表格数量一致
   - 表头一致
   - 行顺序一致
   - 列顺序一致
   - 序号一致
   - 分项名称一致
7. 原模板中已有的引用性文字必须原样保留，例如“见第一章招标公告”“详见招标公告”“见投标人须知前附表”等，禁止改写。
8. 如某填写项无法从输入信息中确定，保留原空白或原占位，不得猜测、不得编造、不得用你自己的话补充。
9. 若 chapter_mode = mixed，则可对模板外的正文部分进行必要生成，但模板部分必须严格锁定，只做最小填写。
10. 输出中不得包含任何解释、说明、提示语、前言、后记，只输出最终章节内容。

补充约束：
- 不得虚构金额、报价、日期、资质、证书编号、业绩、联系人、电话、地址、银行账号等事实性信息。
- 对报价表，只能在模板允许的分项层级下填写；若招标文件明确禁止新增其他分项，则绝对不得新增。
- 对偏差表、技术偏差表，必须逐条对应原模板，不得自行合并、拆分或改写条款。
- 对带星号（*、★）的重要技术条款，如模板要求填写支持资料位置，必须保留该字段，不得删除或改名。
```

### User Prompt（可直接复制）

```text
请基于以下输入，生成当前章节内容。

【章节模式】
{{chapter_mode}}

【招标文件解析摘要】
{{parsed_bid}}

【招标文件格式摘要】
{{format_template}}

【当前章节标题】
{{chapter_title}}

【当前章节结构】
{{chapter_structure}}

【原始模板】
{{chapter_template_raw}}

【填写规则】
{{fillable_rules}}

【用户补充要求】
{{prompt_requirement}}

生成要求：
1. 若 chapter_mode = template，则以“原始模板”为绝对准绳，严格按模板输出。
2. 若 chapter_mode = mixed，则非模板部分可正常生成，模板部分必须严格保留原样，仅填写允许填写的位置。
3. 固定标题、固定条款、固定表头、固定注释、固定行列，不得做任何修改。
4. 只允许填写空白处、占位处、明确待填写处。
5. 无法确认的填写项，保留空白或原占位，不得猜测。
6. 不得新增原模板没有的条目、行、列、说明、注释。
7. 如果模板中包含表格，输出表格结构必须与原模板一致。
8. 不得漏掉原模板已有的任何条目。
9. 只输出最终结果，不输出解释。
```

### 适用场景建议

以下章节通常会被识别为 `template` 或 `mixed`：

- 商务偏差表
- 技术偏差表
- 分项报价表
- 基本情况表
- 类似项目情况表
- 主要股东或出资人信息
- 制造商授权书
- 投标人承诺书
- 廉洁承诺
- 软件自主化声明
- 其他招标文件已给定固定格式的表格与声明

---

## 4.8 ValidateTemplate 节点配置

### 节点类型
- LLM

### 输出变量
- `validation_result`

### 节点目标
对 `template` / `mixed` 模式的输出做二次校验，检查是否存在：
- 改动固定文字
- 漏项
- 加项
- 表格结构变化
- 非法填写
- 编造信息

### System Prompt（可直接复制）

```text
你是投标文件模板一致性校验器。

你的任务是比较“原始模板”和“候选输出”，判断候选输出是否严格遵守模板锁定规则。

严格检查项：
1. 是否修改了原模板中已有的固定文字
2. 是否删除了原模板中的条目、行、列、说明、注释
3. 是否新增了原模板中不存在的条目、行、列、说明、注释
4. 是否改变了表格表头、序号、分项名称、条款名称
5. 是否遗漏了原模板已有的任一项
6. 是否只在允许填写的位置进行了填写
7. 是否对无法确定的信息进行了猜测或编造

输出要求：
1. 只输出 JSON
2. 顶级字段固定为：pass, issues
3. pass 为布尔值
4. issues 为字符串数组
5. 若 chapter_mode = normal，则直接返回通过：
{
  "pass": true,
  "issues": []
}
```

### User Prompt（可直接复制）

```text
请比较以下内容并输出 JSON。

【章节模式】
{{chapter_mode}}

【原始模板】
{{chapter_template_raw}}

【填写规则】
{{fillable_rules}}

【候选输出】
{{chapter_content_draft}}

请严格检查是否存在：
- 改动固定文字
- 漏项
- 加项
- 表格结构变化
- 非法填写
- 编造信息

输出格式如下：
{
  "pass": true,
  "issues": []
}
```

### 输出示例

```json
{
  "pass": false,
  "issues": [
    "候选输出删除了原模板中的“付款条件”条目。",
    "候选输出新增了原模板中不存在的报价分项。",
    "原模板中的“见第一章招标公告”被改写，违反固定内容不得修改规则。"
  ]
}
```

---

## 4.9 End 节点输出配置

End 节点绑定：

- `chapter_content_draft` -> `chapter_content`
- `chapter_mode`
- `validation_result`

返回示例：

```json
{
  "data": {
    "outputs": {
      "chapter_content": "# 第三章 技术方案\n...",
      "chapter_mode": "template",
      "validation_result": "{\"pass\":true,\"issues\":[]}"
    }
  }
}
```

说明：

- 当 `chapter_mode = normal` 时，`validation_result` 一般固定为通过
- 当 `chapter_mode = template` 或 `mixed` 时，后端可根据 `validation_result.pass` 判断是否允许落库，或提示前端“模板结构未通过校验”

---

## 5. 工作流3：废标检查工作流

## 5.1 工作流目标

根据招标文件要求和当前标书正文，输出结构化风险问题清单。

## 5.2 Dify 逐节点配置表

| 顺序 | 节点名称 | 节点类型 | 输入 | 输出 | 说明 |
|------|----------|----------|------|------|------|
| 1 | Start | 开始节点 | `parsed_bid`, `risk_clauses`, `chapters_content` | 同左 | 接收检查参数 |
| 2 | RiskCheck | LLM | 上述全部输入 | `results`, `summary` | 输出结构化 JSON |
| 3 | End | 结束节点 | `results`, `summary` | 同左 | 返回给后端 |

## 5.3 Start 节点配置

### 输入变量

| 变量名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `parsed_bid` | Long Text | 是 | 招标文件解析摘要 |
| `risk_clauses` | Long Text | 否 | 风险条款摘要 |
| `chapters_content` | Long Text | 是 | 当前项目所有章节内容拼接后的全文 |

### 后端传入示例

```json
{
  "inputs": {
    "parsed_bid": "## A. 项目基本信息...",
    "risk_clauses": "## A. 星号/关键条款...",
    "chapters_content": "# 第一章 项目概述\n...\n\n# 第二章 商务响应\n..."
  },
  "response_mode": "blocking",
  "user": "bid-system"
}
```

---

## 5.4 RiskCheck 节点配置

### 节点类型
- LLM

### 输出变量
- `results`
- `summary`

### 关键要求
这个节点最好直接输出合法 JSON，方便后端直接解析。

### System Prompt（可直接复制）

```text
你是投标文件风险审查助手。
你的任务是根据招标文件要求和当前标书内容，识别可能导致废标、响应不完整或评分不足的风险。

严格要求：
1. 只输出 JSON，不输出任何解释文字
2. 输出必须包含两个顶级字段：results 和 summary
3. results 必须是数组
4. summary 必须是对象，字段为 high、medium、low
5. riskLevel 只允许为 high、medium、low
6. high 表示可能直接导致废标、资格不符或实质性不响应
7. medium 表示关键响应不完整、材料不足、存在明显不确定性
8. low 表示建议补充、增强或优化
9. relatedOutlineNodeId 当前阶段统一输出 null
10. 不能编造不存在的问题，必须依据输入内容判断
```

### User Prompt（可直接复制）

```text
请检查当前标书内容的风险，并输出 JSON。

【招标文件解析摘要】
{{parsed_bid}}

【关键风险条款】
{{risk_clauses}}

【当前标书正文】
{{chapters_content}}

输出 JSON 格式如下：
{
  "results": [
    {
      "riskLevel": "high | medium | low",
      "title": "问题标题",
      "description": "问题说明",
      "suggestion": "修改建议",
      "relatedOutlineNodeId": null
    }
  ],
  "summary": {
    "high": 0,
    "medium": 0,
    "low": 0
  }
}

要求：
1. 只输出 JSON
2. 如果没有明显风险，results 返回空数组，summary 全部为 0
3. description 要写清楚为什么判定为风险
4. suggestion 要给出可执行的补充建议
```

### 输出示例

```json
{
  "results": [
    {
      "riskLevel": "high",
      "title": "缺少法定代表人授权响应",
      "description": "招标文件明确要求提供法定代表人授权委托书，但当前正文中未体现相关响应内容。",
      "suggestion": "在商务响应章节补充授权委托书说明，并同步准备附件材料。",
      "relatedOutlineNodeId": null
    },
    {
      "riskLevel": "medium",
      "title": "售后服务承诺描述不充分",
      "description": "招标文件对售后服务响应时间和保障机制有明确要求，当前内容表述较笼统。",
      "suggestion": "补充响应时效、服务方式、保障机制及责任分工。",
      "relatedOutlineNodeId": null
    }
  ],
  "summary": {
    "high": 1,
    "medium": 1,
    "low": 0
  }
}
```

---

## 5.5 End 节点输出配置

End 节点绑定：
- `results`
- `summary`

返回示例：

```json
{
  "data": {
    "outputs": {
      "results": "[...]",
      "summary": "{\"high\":1,\"medium\":1,\"low\":0}"
    }
  }
}
```

说明：

- 某些 Dify 场景中 JSON 可能以字符串形式返回
- 后端需要兼容“对象”和“JSON 字符串”两种情况

---

## 6. Flask 后端字段映射设计

## 6.1 当前后端已存在字段

当前后端已经有：

### `TenderFile`
- `parsed_text`
- `parsed_summary`
- `parse_status`
- `parse_error_message`

### `OutlineNode`
- `title`
- `prompt_requirement`
- `parent_id`
- `level`
- `order_no`

### `ChapterContent`
- `content`
- `status`
- `current_version_no`

### `BidCheckResult`
- `risk_level`
- `title`
- `description`
- `suggestion`
- `related_outline_node_id`

## 6.2 建议补充字段

建议在 `TenderFile` 增加：

- `risk_clauses`
- `format_template`

用途：

| 字段 | 来源工作流 | 用途 |
|------|------------|------|
| `parsed_summary` | 工作流1 | 章节生成 / 废标检查 |
| `risk_clauses` | 工作流1 | 废标检查 |
| `format_template` | 工作流1 | 后续增强使用 |

建议模型字段示例：

```python
risk_clauses = db.Column(db.Text)
format_template = db.Column(db.Text)
```

---

## 6.3 工作流1 字段映射

### Dify 输出 -> 后端字段

| Dify 输出字段 | 后端字段 | 说明 |
|---------------|----------|------|
| `parsed_bid` | `TenderFile.parsed_summary` | 招标文件解析摘要 |
| `risk_clauses` | `TenderFile.risk_clauses` | 风险条款摘要 |
| `format_template` | `TenderFile.format_template` | 模板摘要 |
| `outline_json` | `OutlineNode` 表 | 解析后逐层写入目录节点 |

### Python 处理示例

```python
outputs = run_parse_workflow(bid_text)

parsed_bid = outputs.get('parsed_bid', '')
risk_clauses = outputs.get('risk_clauses', '')
format_template = outputs.get('format_template', '')
outline_json_str = outputs.get('outline_json', '')

tf.parsed_summary = parsed_bid
tf.risk_clauses = risk_clauses
tf.format_template = format_template
```

### `outline_json` 解析示例

```python
import json
import re

outline_data = []
if outline_json_str:
    try:
        outline_data = json.loads(outline_json_str)
    except Exception:
        m = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', outline_json_str)
        if m:
            outline_data = json.loads(m.group(1))
```

---

## 6.4 工作流2 字段映射（增强版）

### 后端输入组装来源

| Dify 输入字段 | 后端来源 |
|---------------|----------|
| `parsed_bid` | `TenderFile.parsed_summary` |
| `format_template` | `TenderFile.format_template` |
| `chapter_title` | 当前 `OutlineNode.title` |
| `chapter_structure` | 当前一级章节及子节点拼装文本 |
| `prompt_requirement` | 当前 `OutlineNode.prompt_requirement` |
| `chapter_template_raw` | 后端从招标文件原始模板中提取的当前章节模板 |
| `fillable_rules` | 后端为当前章节生成的填写规则 |

### 章节模式判定方式

`chapter_mode` 不再要求前端传入，而是在工作流内部通过 `DetectChapterMode` 节点自动识别。

建议后端仍尽量提供以下信息，以提升自动识别准确率：

- `chapter_title`
- `chapter_structure`
- `chapter_template_raw`
- `fillable_rules`
- `format_template`

### Python 组装示例

```python
def build_chapter_structure(node):
    lines = [f"# {node.title}"]
    children = sorted(node.children, key=lambda x: x.order_no)
    for child in children:
        lines.append(f"## {child.title}")
        if child.prompt_requirement:
            lines.append(f"要求：{child.prompt_requirement}")
    return "\n".join(lines)
```

### 调 Dify 请求示例

```python
payload = {
    "inputs": {
        "parsed_bid": parsed_bid or "",
        "format_template": tf.format_template or "",
        "chapter_title": node.title,
        "chapter_structure": chapter_structure,
        "prompt_requirement": node.prompt_requirement or "",
        "chapter_template_raw": chapter_template_raw or "",
        "fillable_rules": fillable_rules or "",
    },
    "response_mode": "streaming",
    "user": "bid-system",
}
```

### Dify 输出 -> 后端字段

| Dify 输出字段 | 后端字段 |
|---------------|----------|
| `chapter_content` | `ChapterContent.content` |
| `chapter_mode` | 可记录到日志表/调试信息，便于分析工作流判定结果 |
| `validation_result` | 可记录到日志表/调试信息，或用于前端提示 |

### 保存示例

```python
content.current_version_no = (content.current_version_no or 0) + 1
content.content = final_text
content.status = ChapterStatus.GENERATED
content.last_generated_at = datetime.utcnow()
```

### 模板校验建议

```python
chapter_mode = outputs.get("chapter_mode") or "normal"
validation = outputs.get("validation_result") or {}
if isinstance(validation, str):
    validation = json.loads(validation)

if chapter_mode in ("template", "mixed") and not validation.get("pass", False):
    raise ValueError("模板章节生成结果未通过一致性校验")
```

---

## 6.5 工作流3 字段映射

### 后端输入组装来源

| Dify 输入字段 | 后端来源 |
|---------------|----------|
| `parsed_bid` | `TenderFile.parsed_summary` |
| `risk_clauses` | `TenderFile.risk_clauses` |
| `chapters_content` | 所有 `ChapterContent.content` 拼接结果 |

### 章节全文拼接示例

```python
contents = ChapterContent.query.filter_by(project_id=project_id).all()
nodes_map = {n.id: n for n in OutlineNode.query.filter_by(project_id=project_id).all()}
chapters_text = []

for c in contents:
    if c.content:
        node = nodes_map.get(c.outline_node_id)
        title = node.title if node else f"章节{c.outline_node_id}"
        chapters_text.append(f"# {title}\n{c.content}")

chapters_content = "\n\n---\n\n".join(chapters_text)
```

### 调 Dify 请求示例

```python
payload = {
    "inputs": {
        "parsed_bid": tf.parsed_summary or "",
        "risk_clauses": tf.risk_clauses or "",
        "chapters_content": chapters_content[:80000],
    },
    "response_mode": "blocking",
    "user": "bid-system",
}
```

### Dify 输出 -> 后端字段

| Dify 输出字段 | 后端字段 |
|---------------|----------|
| `results[].riskLevel` | `BidCheckResult.risk_level` |
| `results[].title` | `BidCheckResult.title` |
| `results[].description` | `BidCheckResult.description` |
| `results[].suggestion` | `BidCheckResult.suggestion` |
| `results[].relatedOutlineNodeId` | `BidCheckResult.related_outline_node_id` |

### 落库示例

```python
for item in parsed_results:
    record = BidCheckResult(
        project_id=project_id,
        check_version=check_version,
        risk_level=item['riskLevel'],
        title=item['title'],
        description=item['description'],
        suggestion=item['suggestion'],
        related_outline_node_id=item.get('relatedOutlineNodeId'),
        status='open',
    )
    db.session.add(record)
```

---

## 7. Dify 调用封装建议

建议后端继续保留 3 个独立方法。

### 7.1 解析工作流

```python
def run_parse_workflow(bid_text: str) -> dict:
    ...
```

### 7.2 章节生成工作流

```python
def stream_generate_chapter(
    parsed_bid: str,
    format_template: str,
    chapter_title: str,
    chapter_structure: str,
    prompt_requirement: str,
    chapter_template_raw: str,
    fillable_rules: str,
) -> Generator[str, None, None]:
    ...
```

### 7.3 废标检查工作流

```python
def run_check_workflow(
    parsed_bid: str,
    risk_clauses: str,
    chapters_content: str,
) -> dict:
    ...
```

注意：你当前代码里的 `run_check_workflow()` 还没有传 `risk_clauses`，建议补上。

建议改成：

```python
def run_check_workflow(parsed_bid: str, risk_clauses: str, chapters_content: str) -> dict:
    payload = {
        'inputs': {
            'parsed_bid': parsed_bid or '',
            'risk_clauses': risk_clauses or '',
            'chapters_content': chapters_content[:80000],
        },
        'response_mode': 'blocking',
        'user': 'bid-system',
    }
```

---

## 8. 代码级改造建议（与当前项目对应）

## 8.1 `models.py` 建议补充

在 `TenderFile` 中增加：

```python
risk_clauses = db.Column(db.Text)
format_template = db.Column(db.Text)
```

## 8.2 `routes/files.py` 解析完成后保存

补充：

```python
risk_clauses = outputs.get('risk_clauses', '')
format_template = outputs.get('format_template', '')

tf.parsed_summary = parsed_bid
tf.risk_clauses = risk_clauses
tf.format_template = format_template
```

## 8.3 `utils/dify_client.py` 调整章节生成工作流签名

把：

```python
def stream_generate_chapter(
    parsed_bid: str,
    chapter_title: str,
    chapter_structure: str,
    prompt_requirement: str,
) -> Generator[str, None, None]:
```

改为：

```python
def stream_generate_chapter(
    parsed_bid: str,
    format_template: str,
    chapter_title: str,
    chapter_structure: str,
    prompt_requirement: str,
    chapter_template_raw: str,
    fillable_rules: str,
) -> Generator[str, None, None]:
```

并在 payload 中补充：

```python
payload = {
    "inputs": {
        "parsed_bid": parsed_bid or "",
        "format_template": format_template or "",
        "chapter_title": chapter_title,
        "chapter_structure": chapter_structure,
        "prompt_requirement": prompt_requirement or "",
        "chapter_template_raw": chapter_template_raw or "",
        "fillable_rules": fillable_rules or "",
    },
    "response_mode": "streaming",
    "user": "bid-system",
}
```

## 8.4 章节生成前建议增加模板提取

后端建议在生成章节前，尽量准备：

- `chapter_template_raw`
- `fillable_rules`

原因：

- `chapter_mode` 已由工作流内部的 `DetectChapterMode` 节点自动识别，前端无需改造
- 但自动识别和严格模板填充的效果，仍然高度依赖 `chapter_template_raw` 的质量

注意：

- `chapter_template_raw` 应尽量来自招标文件原始 docx 模板内容，而不是仅依赖 LLM 摘要
- 若章节中包含复杂表格，建议优先保留为 HTML 或高保真文本，减少 Markdown 表格失真风险

## 8.5 `utils/dify_client.py` 调整检查工作流签名

把：

```python
def run_check_workflow(parsed_bid: str, chapters_content: str) -> dict:
```

改为：

```python
def run_check_workflow(parsed_bid: str, risk_clauses: str, chapters_content: str) -> dict:
```

## 8.6 `routes/review.py` 调用时补上传 `risk_clauses`

```python
outputs = run_check_workflow(
    tf.parsed_summary or '',
    tf.risk_clauses or '',
    chapters_content,
)
```

---

## 9. 调试与验收建议

## 9.1 工作流1 验收标准

- 输入一份真实招标文件文本
- 必须返回 `parsed_bid`
- `outline_json` 能被 Python `json.loads()` 成功解析
- `outline_json` 至少能生成一级、二级目录树
- `risk_clauses` 有明确风险条款输出

## 9.2 工作流2 验收标准

- 普通章节在自动识别为 `chapter_mode = normal` 时可正常输出 Markdown
- 模板章节应能被 `DetectChapterMode` 自动识别为 `template` 或 `mixed`
- 模板章节在 `template` / `mixed` 模式下必须保留原模板全部固定内容
- 模板章节不得出现漏项、加项、改写固定表头或改动原有条款文字
- 若模板中存在表格，表格结构必须与原模板保持一致
- 对无法确认的字段应保留空白或原占位，不得编造
- `validation_result` 能输出合法 JSON
- `template` / `mixed` 模式下，`validation_result.pass` 应能正确反映是否通过模板校验
- 流式模式下能持续返回文本分片

## 9.3 工作流3 验收标准

- 输入一份正文全文后，返回合法 JSON
- `results` 是数组
- `summary` 数量与 `results` 对应
- 至少能识别明显缺失的授权、资格、响应类问题

---

## 10. 推荐落地顺序

1. 先在 Dify 搭好工作流1，并用控制台手工测试输出
2. 确认 `outline_json` 稳定后，打通后端落库
3. 再搭工作流2，先在 Dify 控制台测试单章节生成
4. 后端接入 SSE
5. 最后搭工作流3，并补 `risk_clauses` 字段落库

---

## 11. 最终结论

你现在可以按本文档直接在 Dify 搭建：

- 工作流1：Start → ParseBid → ExtractOutline → ExtractRiskClauses → ExtractFormatTemplate → End
- 工作流2：Start → DetectChapterMode → RouteChapterMode → GenerateNormalChapter / FillTemplateStrict → ValidateTemplate → End
- 工作流3：Start → RiskCheck → End

并且可以直接复制本文提供的：

- 每个节点的完整 Prompt
- 后端请求体结构
- 输出字段映射方式
- Python 代码示例

这套设计已经和你当前项目代码结构对齐，可以直接进入实现和联调阶段。
