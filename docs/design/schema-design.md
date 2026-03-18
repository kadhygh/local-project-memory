# Schema 设计文档

## 1. 设计目标

第一阶段 schema 的目标不是覆盖所有未来对象，而是为 `doc_chunk`、`code_chunk`、`task_summary` 提供统一、稳定、可检索的记录结构。

第一阶段采用统一记录模型，后续再扩展专用表或关系表。

## 2. 统一记录模型

建议第一阶段使用单一主表，例如 `knowledge_items`。

每条记录共享以下核心字段：

- `id`
- `project_id`
- `scope`
- `type`
- `text`
- `summary`
- `title`
- `source_kind`
- `source_path`
- `source_id`
- `tags`
- `vector`
- `importance`
- `confidence`
- `verified`
- `created_at`
- `updated_at`
- `last_accessed_at`
- `access_count`
- `line_hint`
- `citation`

## 3. 字段定义

### 3.1 主键与身份字段

- `id`
  - 全局唯一字符串
  - 建议由 `project_id + type + source_path + chunk_key` 生成稳定 ID

- `project_id`
  - Unity 项目标识
  - 所有第一阶段查询默认必须带该字段

- `scope`
  - 第一阶段仅允许 `project:<project-id>` 或 `session:<task-id>`

- `type`
  - 枚举值仅允许 `doc_chunk`、`code_chunk`、`task_summary`

### 3.2 内容字段

- `text`
  - 原始可检索文本
  - 用于全文检索、向量化和后续摘要参考

- `summary`
  - 面向 recall 结果展示的短摘要
  - 控制在 1 到 3 句

- `title`
  - 结果标题
  - 例如文档标题、文件名、任务标题

- `tags`
  - 字符串列表
  - 用于弱分类与后续过滤

### 3.3 来源字段

- `source_kind`
  - 记录原始来源类型
  - 第一阶段建议允许 `document`、`code`、`config`、`task`

- `source_path`
  - 原始文件路径或逻辑路径
  - 必须可回到真实文件

- `source_id`
  - 来源系统内的稳定标识
  - 文档可用文档相对路径
  - 代码可用文件路径加符号名
  - 任务可用任务 ID

- `line_hint`
  - 用于帮助定位代码块的大致行号

- `citation`
  - 面向 agent 的引用字符串
  - 例如 `Assets/Scripts/UI/UIRoot.cs:88`

### 3.4 检索字段

- `vector`
  - 向量字段
  - 由统一 embedding 策略生成

- `importance`
  - 0 到 1 的浮点值
  - 表示该记录在排序中的业务权重

- `confidence`
  - 0 到 1 的浮点值
  - 表示该记录内容可靠度

- `verified`
  - 布尔值
  - 用于区分已验证与未验证内容

### 3.5 生命周期字段

- `created_at`
- `updated_at`
- `last_accessed_at`
- `access_count`

这些字段用于后续治理，但第一阶段先保证能写入。

## 4. 类型特化字段

虽然第一阶段使用统一模型，仍建议保留一组可选字段。

### 4.1 `doc_chunk`

建议补充：

- `doc_section`
- `doc_order`

### 4.2 `code_chunk`

建议补充：

- `language`
- `symbol_name`
- `symbol_kind`
- `class_name`
- `namespace`

### 4.3 `task_summary`

建议补充：

- `task_id`
- `task_kind`
- `outcome`
- `related_paths`

## 5. 字段约束

第一阶段建议遵循以下硬约束：

- `project_id` 必填
- `scope` 必填
- `type` 必填
- `text` 必填
- `summary` 必填
- `source_kind` 必填
- `source_path` 必填
- `citation` 必填

建议的软约束：

- `importance` 默认 `0.5`
- `confidence` 默认 `0.5`
- `verified` 默认 `false`
- `access_count` 默认 `0`

## 6. ID 生成规则

第一阶段需要稳定 ID，避免全量重建时产生重复记录。

建议规则：

- 文档块：`hash(project_id + type + source_path + doc_order)`
- 代码块：`hash(project_id + type + source_path + symbol_name + line_hint)`
- 任务总结：`hash(project_id + type + task_id + outcome)`

## 7. JSON 示例

```json
{
  "id": "ki_8d8c6d8f",
  "project_id": "unity-sample",
  "scope": "project:unity-sample",
  "type": "code_chunk",
  "text": "public class UIRoot : MonoBehaviour { ... }",
  "summary": "UIRoot 负责统一打开和关闭 UI 面板。",
  "title": "UIRoot.cs",
  "source_kind": "code",
  "source_path": "Assets/Scripts/UI/UIRoot.cs",
  "source_id": "Assets/Scripts/UI/UIRoot.cs:UIRoot",
  "tags": ["ui", "panel", "entrypoint"],
  "vector": [],
  "importance": 0.7,
  "confidence": 0.8,
  "verified": true,
  "created_at": "2026-03-18T00:00:00Z",
  "updated_at": "2026-03-18T00:00:00Z",
  "last_accessed_at": null,
  "access_count": 0,
  "line_hint": 88,
  "citation": "Assets/Scripts/UI/UIRoot.cs:88",
  "language": "csharp",
  "symbol_name": "UIRoot",
  "symbol_kind": "class",
  "class_name": "UIRoot",
  "namespace": "Game.UI"
}
```

## 8. 表拆分建议

第一阶段先使用单表，理由如下：

- 实现简单
- 查询路径清晰
- 便于统一 recall

后续当 `scene_summary`、`prefab_summary`、`entity_relation` 纳入后，再考虑拆表。

## 9. 第一阶段索引建议

第一阶段建议至少准备：

- `project_id` 的标量过滤能力
- `scope` 的标量过滤能力
- `type` 的标量过滤能力
- `source_path` 的可追溯字段
- `text` 的全文检索能力
- `vector` 的向量检索能力

## 10. 设计结论

第一阶段 schema 的核心不是“字段够多”，而是保证每条记录：

- 能被检索
- 能被过滤
- 能被追溯
- 能被后续治理

只要这四件事成立，MVP 就有可持续演进的基础。
