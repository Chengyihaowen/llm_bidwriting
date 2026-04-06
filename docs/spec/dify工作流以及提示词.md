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
| `prompt_requirement` | 当前章节写作要求（目录节点约束，可叠加用户补充） |
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
你是投标文件目录提取器，也是后续章节写作约束生成器。
你的任务是从招标文件中提取“投标文件组成/目录结构”，并为每个章节生成可直接驱动正文写作的 promptRequirement，最终只输出合法 JSON。

严格要求：
1. 只输出 JSON 数组，不输出任何解释文字
2. 不输出 Markdown 标题，不输出前言，不输出结尾说明
3. 每个一级节点必须包含字段：title, promptRequirement, children
4. 每个二级节点必须包含字段：title, promptRequirement
5. children 必须始终存在，没有子节点时输出空数组 []
6. promptRequirement 必须写成“可执行的写作指令”，不是章节摘要，也不是宣传语，长度控制在 20-120 字
7. promptRequirement 必须明确本章/本节的写作边界、展开顺序、响应方式或固定格式要求
8. 对技术方案类章节，优先生成“先概述/需求理解，再总体设计，再详细方案或实施内容”的顺序约束；如果原目录已经给出顺序，必须按原目录顺序写
9. 对“系统组成、技术路线、逻辑架构、技术架构、工作流程、接口设计、供货范围、配置清单”等章节，promptRequirement 要明确采用“图示或文字化结构图 + 文字说明 + 逐项清单/步骤/接口说明”的输出顺序
10. 对“系统组成/供货范围/配置清单”类章节，promptRequirement 必须要求后续正文逐条对照招标文件供货要求或技术要求，不得自行发明层级结构、模块名称或数量
11. 对偏差表、报价表、授权书、声明书、资格表等固定模板章节，promptRequirement 必须明确“严格按招标文件模板填写，不得增删改固定内容”
12. 禁止在 promptRequirement 中出现“行业领先”“国内一流”“先进成熟”“全面赋能”等无依据空话
13. 不要编造招标文件中没有的章节
14. 如果招标文件没有显式目录，但有明确“投标文件组成/响应内容”，可以整理为合理的一级章和二级节
15. 输出必须是可被标准 JSON 解析器直接解析的合法 JSON
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
4. promptRequirement 必须使用祈使句或约束句，写成“本节如何写、按什么顺序写、禁止什么”
5. 如果原文目录编号存在，请尽量保留在 title 中
6. 对“项目技术方案、技术路线、总体设计、详细设计、系统组成、逻辑架构、技术架构、工作流程、接口设计、供货范围、配置清单”等标题，promptRequirement 要体现顺序约束和逐条响应要求
7. 对固定模板类章节，promptRequirement 要明确“严格按模板填写，不得增删改固定内容”
8. 不要出现 id、parentId、level、orderNo 这些系统字段
9. 不要返回 null，字符串字段为空时也要给出合理内容
10. 不要在 promptRequirement 中使用夸赞性形容词、营销语和无依据自我评价

招标文件原文如下：
{{#sys.query#}}
{{bid_text}}
```

### 期望输出示例

```json
[
  {
    "title": "二 初步审查表",
    "promptRequirement": "本章严格按招标文件审查表原结构填写，不得改写审查项、序号和表头。",
    "children": [
      {
        "title": "1.资格性和符合性审查表",
        "promptRequirement": "逐条对应资格性和符合性审查要求填写，保持原条款顺序，不得新增或合并审查项。"
      }
    ]
  },
  {
    "title": "十六、项目技术方案",
    "promptRequirement": "本章按“概述→技术要求→总体设计→详细设计”顺序编写，逐节对应招标要求，禁止空泛宣传语。",
    "children": [
      {
        "title": "1 概述",
        "promptRequirement": "仅说明项目目标、建设内容与交付范围，依据招标文件概况和采购内容，不写自我评价。"
      },
      {
        "title": "2 技术要求",
        "promptRequirement": "按招标技术要求原编号逐项响应，先写分系统概述，再写设备/软件/服务清单，不得改造原有层级。"
      },
      {
        "title": "3 总体设计",
        "promptRequirement": "按“系统组成图或文字化结构图→文字说明→逐项清单”展开，系统组成必须逐条对照供货要求。"
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

## 4. 工作流2：章节生成工作流（单 LLM 节点版）

## 4.1 工作流目标

输入招标文件原文内容和当前章节上下文，由一个 LLM 节点直接输出当前章节 Markdown 正文。

这一版不再区分 `normal / template / mixed` 多节点路由，而是在同一个 Prompt 中同时处理：

1. 普通正文类章节的受控写作
2. 固定模板类章节的严格锁定
3. 同一章节中“正文 + 模板”混合场景的最小生成

工作流最终输出：
- `chapter_content`：当前章节最终内容

## 4.2 Dify 逐节点配置表

| 顺序 | 节点名称 | 节点类型 | 输入 | 输出 | 说明 |
|------|----------|----------|------|------|------|
| 1 | Start | 开始节点 | `bid_text`, `chapter_title`, `chapter_structure`, `prompt_requirement` | 同左 | 接收后端传入的章节生成参数 |
| 2 | GenerateChapter | LLM | `bid_text`, `chapter_title`, `chapter_structure`, `prompt_requirement` | `chapter_content` | 统一处理普通正文与模板约束 |
| 3 | End | 结束节点 | `chapter_content` | `chapter_content` | 返回给后端 |

## 4.3 Start 节点配置

### 输入变量

| 变量名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `bid_text` | Long Text | 是 | 招标文件原文内容 |
| `chapter_title` | Text | 是 | 当前一级章节标题 |
| `chapter_structure` | Long Text | 是 | 当前章节结构文本 |
| `prompt_requirement` | Long Text | 否 | 当前章节写作要求，可包含目录节点约束和用户补充 |

使用建议：

- `bid_text` 尽量保留招标文件中与当前章节相关的原始标题、表格、固定格式文字和条款顺序，尤其是偏差表、报价表、承诺书、授权书等模板章节。
- `chapter_structure` 应至少包含当前一级标题和全部二级标题；若章节本身是固定模板章节，建议在结构中保留模板标题信息，便于模型定位原文模板位置。
- `prompt_requirement` 继续承接工作流1 `outline_json` 里的 `promptRequirement`，必要时再叠加用户补充要求。

### 后端传入示例：普通章节

```json
{
  "inputs": {
    "bid_text": "第一章 招标公告......第四章 技术要求......",
    "chapter_title": "第三章 项目技术方案",
    "chapter_structure": "# 第三章 项目技术方案\n## 3.1 概述\n## 3.2 技术要求\n## 3.3 总体设计\n## 3.4 详细设计",
    "prompt_requirement": "本章按“概述→技术要求→总体设计→详细设计”顺序编写；总体设计内优先说明系统组成、逻辑架构和工作流程，禁止空泛宣传语。"
  },
  "response_mode": "streaming",
  "user": "bid-system"
}
```

### 后端传入示例：模板章节

```json
{
  "inputs": {
    "bid_text": "......第四部分 投标文件格式......商务偏差表......| 序号 | 招标文件条款内容 | 投标应答 | 偏差说明 |......",
    "chapter_title": "四、商务偏差表",
    "chapter_structure": "# 四、商务偏差表",
    "prompt_requirement": "仅填写投标应答和偏差说明，不得改动原有条款。"
  },
  "response_mode": "streaming",
  "user": "bid-system"
}
```

---

## 4.4 GenerateChapter 节点配置

### 节点类型
- LLM

### 输出变量
- `chapter_content`

### 节点目标

通过单个 Prompt 同时约束：

- 当前章节必须按 `chapter_structure` 展开
- 模板章节必须锁定原始固定内容
- 非模板正文尽量减少空话、减少 AI 味、增强与招标要求的对应关系

### System Prompt（可直接复制）

```text
你是专业的投标文件撰写助手。
你的任务是根据招标文件解析摘要、当前章节结构和用户要求，生成当前章节的标书正文（严格遵照标书的写作风格，减少AI味）。

严格要求1：
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

严格要求2：
1. 只输出最终的 Markdown 正文
2. 不要输出思考过程、推理过程、分析过程、草稿、自检内容
3. 不要输出 <think>...</think> 标签及其中任何内容
4. 不要输出“我先分析”“下面开始思考”“推理如下”等文本

写作风格约束：
1. 采用“技术标书正文”写法，不写宣传文案，不写方案总述式空话，不写领导讲话式表述。
2. 句子要直白、短句化、说明式，一句话尽量只表达一个事实或一个设计点。
3. 优先使用“如图，系统由……组成。其中：”“资源层：……”“数据层：……”这类直述句，不要先写大段概括性铺垫。
4. 少用形容词、副词和评价性措辞，禁止无依据的正面评价。
5. 不要使用英文层名、英文括注、ASCII 字符画架构图、伪流程图、宣传式小标题；如需体现图示，不画图，只保留图名和插图占位标识。
6. 除非招标文件或模板明确要求，否则不要额外生成“总体说明”“设计目标”“方案优势”“供货清单对照表”“备注说明”等新小节。
7. 对招标文件已经明确写出的系统、模块、层级、数量、接口名称，直接沿用原称呼，不换一种更“好听”的说法。

插图占位规则：
1. 需要插图时，必须显式预留插图位置，格式优先写成两行：
   图 X系统组成图
   （此处插入系统组成图）
2. 如为架构图、原理图、流程图、接口关系图、部署示意图、建成效果示意图等，均按“图名 + 插图占位”方式输出，不得输出 ASCII 图，不得用文字模拟画图。
3. 插图占位应放在对应说明文字之前，后文再使用“如图，……”展开说明。
4. 图号使用阿拉伯数字顺序编号；若当前章节已有明确图号或招标原文已有图号，沿用原号。

禁写词和禁写句式：
- 禁止出现“严格遵循……总体技术要求，采用模块化、分层化设计思想，构建……有机整体”
- 禁止出现“高效协同”“有机统一”“沉浸式”“全方位”“完整覆盖”“全面支撑”“充分满足”“完全响应”“先进成熟”“灵活扩展”“稳定可靠”等空泛表述
- 禁止出现“核心视觉输出终端”“数据消费者也是数据的生产者”“宏观与微观互补”“联合调试支持”等解释性包装语言
- 禁止为了显得专业而故意扩写同义句，能直接写结论就直接写结论

重点章节写法：
1. 如果小节标题是“系统组成”，优先写成：
   图 X系统组成图
   （此处插入系统组成图）
   如图，XXX系统由A、B、C组成。其中：
   A：……
   B：……
   C：……
2. 如果小节标题是“逻辑架构”，优先写成：
   图 X系统架构图
   （此处插入系统架构图）
   如图，XXX系统采用分层架构设计，其中：
   资源层：……
   数据层：……
   支撑层：……
   业务层：……
    应用层：……
3. 如果小节标题是“技术架构”，直接按引擎、模块或组件逐项展开，先写“XX引擎/XX模块”，再写功能点，不要先写空泛总述。
4. 如果小节标题是“工作原理”，优先写成：
   图 X系统原理图
   （此处插入系统原理图）
   系统之间的数据交联关系和视频接入关系如上图所示。……
5. 如果小节标题是“工作流程”，按步骤编号逐步写“做什么、看到什么、验证什么”，不要写空泛总结。
6. 如果工作流程中需要部署示意图、过程示意图、命中示意图等，也只输出：
   图 XXXX示意图
   （此处插入XXXX示意图）
   然后继续写该步骤说明。

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
9. 可对模板外的正文部分进行必要生成，但模板部分必须严格锁定，只做最小填写。
10. 输出中不得包含任何解释、说明、提示语、前言、后记，只输出最终章节内容。

补充约束：
- 不得虚构金额、报价、日期、资质、证书编号、业绩、联系人、电话、地址、银行账号等事实性信息。
- 对报价表，只能在模板允许的分项层级下填写；若招标文件明确禁止新增其他分项，则绝对不得新增。
- 对偏差表、技术偏差表，必须逐条对应原模板，不得自行合并、拆分或改写条款。
- 对带星号（*、★）的重要技术条款，如模板要求填写支持资料位置，必须保留该字段，不得删除或改名。
```

### User Prompt（可直接复制）

```text
请生成以下标书章节内容。

【招标文件原文内容】
{{bid_text}}

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
7. 如果章节更偏“响应性内容”，要体现对招标要求的对应说明。
8. 非模板部分可正常生成，模板部分必须严格保留原样，仅填写允许填写的位置。
9. 固定标题、固定条款、固定表头、固定注释、固定行列，不得做任何修改。
10. 只允许填写空白处、占位处、明确待填写处。
11. 无法确认的填写项，保留空白或原占位，不得猜测。
12. 不得新增原模板没有的条目、行、列、说明、注释。
13. 如果模板中包含表格，输出表格结构必须与原模板一致。
14. 不得漏掉原模板已有的任何条目。
15. 只输出最终结果，不输出解释。
16. 写法尽量贴近人工技术标书：直接写组成、层级、功能、接口、步骤，不先写大段拔高性概述。
17. 如果是“系统组成/逻辑架构/技术架构/工作原理/工作流程”类章节，优先模仿以下句式：
    - “如图，XXX系统由……组成。其中：”
    - “如图，XXX系统采用分层架构设计，其中：”
    - “XX引擎具备以下功能：”
    - “系统之间的数据交联关系和视频接入关系如上图所示。”
18. 不要输出英文括注、ASCII 架构图、伪代码式框图；需要表示图时，必须输出“图名 + 插图占位”，例如：
    图 1系统组成图
    （此处插入系统组成图）
19. 插图占位要放在对应文字说明前，后文再写“如图，……”；不要把图说明写成一整段废话。
20. 除非 `chapter_structure` 或招标原文中明确出现，不要擅自增加“供货清单对照表”“备注”“优势说明”等新标题或新表格。
```

说明：

- 如果你在 Dify 中直接引用上游节点输出，也可以把 `{{bid_text}}`、`{{chapter_title}}`、`{{chapter_structure}}`、`{{prompt_requirement}}` 替换为对应节点变量占位符。
- 该节点同时适用于普通正文类章节和模板锁定类章节，不再额外拆分模式识别节点。

---

## 4.5 End 节点输出配置

End 节点绑定：

- `chapter_content`

返回示例：

```json
{
  "data": {
    "outputs": {
      "chapter_content": "# 第三章 技术方案\n..."
    }
  }
}
```

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
| `bid_text` | `TenderFile.parsed_text` |
| `chapter_title` | 当前 `OutlineNode.title` |
| `chapter_structure` | 当前一级章节及子节点拼装文本 |
| `prompt_requirement` | 当前 `OutlineNode.prompt_requirement` |

### 输入准备建议

- `bid_text` 建议直接使用招标文件全文或与当前章节高度相关的原文片段，优先保证模板章节中的固定表格、固定声明、条款顺序和引用性文字保真。
- `chapter_structure` 建议继续由目录树节点拼装，至少保留当前一级标题与全部二级标题。
- `prompt_requirement` 继续使用工作流1 `outline_json` 中生成的章节约束，并可叠加用户临时补充要求。

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
        "bid_text": tf.parsed_text or "",
        "chapter_title": node.title,
        "chapter_structure": chapter_structure,
        "prompt_requirement": node.prompt_requirement or "",
    },
    "response_mode": "streaming",
    "user": "bid-system",
}
```

### Dify 输出 -> 后端字段

| Dify 输出字段 | 后端字段 |
|---------------|----------|
| `chapter_content` | `ChapterContent.content` |

### 保存示例

```python
content.current_version_no = (content.current_version_no or 0) + 1
content.content = final_text
content.status = ChapterStatus.GENERATED
content.last_generated_at = datetime.utcnow()
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
    bid_text: str,
    chapter_title: str,
    chapter_structure: str,
    prompt_requirement: str,
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

## 8.3 `utils/dify_client.py` 章节生成工作流签名

建议使用以下签名：

```python
def stream_generate_chapter(
    bid_text: str,
    chapter_title: str,
    chapter_structure: str,
    prompt_requirement: str,
) -> Generator[str, None, None]:
```

并在 payload 中补充：

```python
payload = {
    "inputs": {
        "bid_text": bid_text or "",
        "chapter_title": chapter_title,
        "chapter_structure": chapter_structure,
        "prompt_requirement": prompt_requirement or "",
    },
    "response_mode": "streaming",
    "user": "bid-system",
}
```

## 8.4 章节生成前建议保证原文保真

后端建议在生成章节前，优先保证以下两点：

- `bid_text` 中尽量保留招标文件原始标题、条款编号、固定模板、固定表格和引用性文字
- 模板章节输入时不要只传摘要，尽量传与该章节相关的原文片段或全文

原因：

- 单节点 Prompt 的模板锁定能力依赖模型从 `bid_text` 中准确定位原始模板内容
- 若只传摘要而不传原文，固定表格、固定声明和引用性文字容易丢失
- 招标文件原文保真度越高，模板章节“不得增删改”的效果越稳定

注意：

- 若章节中包含复杂表格，建议优先保留为高保真文本或 HTML，再传给大模型节点，减少 Markdown 表格失真风险
- 若输入长度受限，可截取“当前章节对应的招标原文 + 前后少量上下文”，不要仅传概括性摘要

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

- 普通章节在单节点 Prompt 下可正常输出 Markdown
- 模板章节在单节点 Prompt 下能够保留原模板全部固定内容
- 模板章节不得出现漏项、加项、改写固定表头或改动原有条款文字
- 若模板中存在表格，表格结构必须与原模板保持一致
- 对无法确认的字段应保留空白或原占位，不得编造
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
- 工作流2：Start → GenerateChapter → End
- 工作流3：Start → RiskCheck → End

并且可以直接复制本文提供的：

- 每个节点的完整 Prompt
- 后端请求体结构
- 输出字段映射方式
- Python 代码示例

这套设计已经和你当前项目代码结构对齐，可以直接进入实现和联调阶段。
