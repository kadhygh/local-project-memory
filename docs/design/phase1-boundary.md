# 第一阶段边界定义

## 1. 目标

第一阶段只做最小可用的 `MemoryService`，目标是让外部 agent 对 Unity 项目完成基础索引、结构化 recall 和任务总结写入。

第一阶段验证的问题只有一个：

是否能减少定位成本并提升跨任务复用能力。

## 2. 第一阶段必须交付的能力

- 文档索引
- 代码索引
- 任务总结写入
- 带引用的 recall
- `project` 与 `session` 两层 scope

## 3. 第一阶段纳入的数据对象

只纳入三类对象：

- `doc_chunk`
- `code_chunk`
- `task_summary`

原因如下：

- `doc_chunk` 能提供稳定背景和约定
- `code_chunk` 是开发任务的主要定位入口
- `task_summary` 是长期记忆的最小闭环

## 4. 第一阶段索引来源

只处理以下来源：

- 项目文档
- `Assets/**/*.cs`
- `Packages/manifest.json`
- `ProjectSettings/**/*`
- 与开发有关的 `*.json`、`*.yaml`

第一阶段暂不处理：

- `scene_summary`
- `prefab_summary`
- `entity_relation`
- 多模态资源

## 5. 第一阶段 scope 规则

第一阶段只支持两个 scope：

- `project:<project-id>`
- `session:<task-id>`

写入原则：

- 静态索引默认写入 `project`
- 任务中产生的总结先写入 `session`
- 明确验证后的任务总结可同时写入 `project`

## 6. 第一阶段 API 范围

只做三个核心 API：

- `index.upsert`
- `search.recall`
- `memory.store`

第一阶段不做：

- `memory.promote`
- `memory.forget`
- `entity.link`
- 批量治理接口

## 7. 第一阶段检索策略

默认检索链路固定为：

1. 元数据过滤
2. 关键词检索
3. 向量检索
4. 混合合并
5. rerank
6. 去重与多样性控制

如果某一环在第一版暂未接入，服务仍应保持同样的接口合同，便于后续补齐。

## 8. 第一阶段写入策略

允许立即写入长期层的内容：

- 用户明确确认的项目规则
- 已验证的任务总结
- 已确认的问题根因

只允许写入 `session` 层的内容：

- 当前任务中的临时发现
- 未形成稳定结论的定位经验

不允许写入的内容：

- 原始对话
- 未验证推测
- 大段重复源码
- 工具噪声

## 9. 第一阶段非目标

第一阶段不追求：

- Unity 编辑器集成
- 实时文件监听
- 复杂记忆治理
- 关系图谱
- 资源深解析
- 完整多 agent 协作协议

## 10. 第一阶段成功标准

若满足以下条件，可认为第一阶段达标：

- 能为 Unity 项目建立可追溯的文档和代码索引
- 能通过 recall 缩小阅读范围
- 能写入并再次召回 `task_summary`
- 能在至少一组真实任务里带来可观测收益

## 11. 第一阶段交付物

第一阶段至少应交付：

- 基础 schema
- 最小 API
- 最小索引流水线
- 本地运行说明
- MVP 验收结果
