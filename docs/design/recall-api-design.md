# Recall API 设计文档

## 1. 目标

`search.recall` 的目标不是直接回答用户问题，而是为 agent 返回一组高质量、可追溯、适合继续读原文件验证的候选上下文。

因此返回值必须结构化，且要明确来源与相关性理由。

## 2. API 范围

第一阶段定义三个接口：

- `POST /v1/index/upsert`
- `POST /v1/search/recall`
- `POST /v1/memory/store`

本文件重点定义 `search.recall`。

## 3. `search.recall` 请求结构

### 3.1 请求体

```json
{
  "project_id": "unity-sample",
  "query": "UI 面板统一打开入口在哪",
  "scopes": ["project:unity-sample"],
  "types": ["code_chunk", "doc_chunk", "task_summary"],
  "top_k": 8,
  "filters": {
    "verified_only": false,
    "source_kinds": ["code", "document", "task"],
    "paths_prefix": ["Assets/", "Docs/"]
  },
  "strategy": "hybrid"
}
```

### 3.2 字段说明

- `project_id`
  - 必填
  - 所有查询的默认过滤条件

- `query`
  - 必填
  - 用户问题或 agent 的任务子问题

- `scopes`
  - 可选
  - 第一阶段通常为 `project` 或 `project + session`

- `types`
  - 可选
  - 用于限制召回对象类型

- `top_k`
  - 可选
  - 默认建议为 `8`

- `filters`
  - 可选
  - 统一承载结构化约束

- `strategy`
  - 第一阶段只允许 `hybrid`
  - 预留 `keyword`、`vector` 作为调试选项

## 4. `search.recall` 返回结构

```json
{
  "query": "UI 面板统一打开入口在哪",
  "project_id": "unity-sample",
  "strategy": "hybrid",
  "results": [
    {
      "id": "ki_8d8c6d8f",
      "type": "code_chunk",
      "title": "UIRoot.cs",
      "summary": "UIRoot 负责统一打开和关闭 UI 面板。",
      "score": 0.93,
      "why_relevant": "命中 UI、打开入口和面板相关语义与关键词。",
      "source_kind": "code",
      "source_path": "Assets/Scripts/UI/UIRoot.cs",
      "citation": "Assets/Scripts/UI/UIRoot.cs:88",
      "line_hint": 88,
      "verified": true,
      "next_candidates": [
        "Assets/Scripts/UI/BasePanel.cs",
        "Assets/Scripts/UI/UIPanelRegistry.cs"
      ]
    }
  ]
}
```

## 5. 排序与处理链路

`search.recall` 建议固定遵循以下链路：

1. 按 `project_id`、`scope`、`type`、其他 metadata 做预过滤
2. 执行全文检索
3. 执行向量检索
4. 合并候选集
5. 做 rerank
6. 做去重
7. 做多样性控制
8. 生成结构化结果

这里的关键原则有两个：

- 召回优先于生成
- 多样性优先于重复相似片段堆积

## 6. 返回结果要求

每条结果至少必须包含：

- `summary`
- `score`
- `why_relevant`
- `source_path`
- `citation`

如果是代码记录，建议补充：

- `line_hint`
- `symbol_name`

如果是任务总结，建议补充：

- `task_id`
- `outcome`

## 7. 错误处理

建议最小错误类型如下：

- `400`
  - 请求参数缺失或非法

- `404`
  - `project_id` 不存在

- `422`
  - `types` 或 `scopes` 使用非法枚举值

- `500`
  - 内部索引或存储异常

即使无结果，也应返回空数组而不是报错。

## 8. 其他两个接口的最小合同

### 8.1 `POST /v1/index/upsert`

用途：

- 写入或更新 `doc_chunk` 与 `code_chunk`

最小请求：

```json
{
  "project_id": "unity-sample",
  "records": []
}
```

### 8.2 `POST /v1/memory/store`

用途：

- 写入 `task_summary`

最小请求：

```json
{
  "project_id": "unity-sample",
  "task_id": "task-20260318-001",
  "scope": "session:task-20260318-001",
  "summary": "确认 UIRoot 是 UI 打开统一入口。",
  "related_paths": [
    "Assets/Scripts/UI/UIRoot.cs"
  ],
  "verified": true
}
```

## 9. Agent 使用约束

agent 使用 `search.recall` 时应遵循以下约束：

- recall 结果只用于缩小范围
- 高分结果仍需读原文件验证
- 写回 `memory.store` 前应确保内容已验证
- 不允许把 recall 摘要直接当成最终事实

## 10. 第一阶段结论

第一阶段 API 的重点不是接口数量，而是把最小闭环做稳：

- 有索引入口
- 有 recall 出口
- 有任务总结写入口

只要这三点成立，就能支撑第一轮 MVP 验证。
