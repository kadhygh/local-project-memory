# 基于 LanceDB 的落地建议

## 1. 落地目标

落地目标不是把 LanceDB 直接装进 Unity，而是基于 LanceDB 建立一个能服务 LLM 开发工作流的长期记忆与超级索引服务。

第一阶段目标应非常明确：

- 为 Unity 开发任务提供高质量 recall
- 降低大范围 `grep` 的使用频率
- 建立跨任务可复用的工作记忆
- 为后续多 agent 协作打基础

## 2. 推荐总体架构

建议使用分层结构，而不是让 Unity 直接处理所有记忆逻辑。

推荐架构如下：

- `LLM Agent / Orchestrator`
- `MemoryService`
- `LanceDB`
- `Embedding Provider`
- `Rerank Provider`
- `Indexer Pipeline`

各层职责如下。

### 2.1 LLM Agent / Orchestrator

负责：

- 接收任务
- 发起 recall 请求
- 决定何时读取原文件验证
- 在任务结束时提交摘要写入

### 2.2 MemoryService

负责：

- 封装 LanceDB 表和索引
- 提供统一 API
- 管理 schema、scope、metadata
- 实现 recall、store、update、forget
- 做 basic dedup 和 consolidation
- 处理引用溯源和排序策略

### 2.3 LanceDB

负责：

- 存储数据
- 向量索引
- 全文索引
- 混合检索
- metadata filter

### 2.4 Embedding Provider

负责：

- 为文档、代码块、任务摘要生成 embedding
- 保证 query 与 document 使用兼容策略

### 2.5 Rerank Provider

负责：

- 对初召回结果进行精排
- 提升 top-k 的工程可用性

### 2.6 Indexer Pipeline

负责：

- 全量或增量索引
- 文件切块
- 资源摘要提取
- 任务摘要入库
- 关系边生成

## 3. 推荐接入方式

### 3.1 第一阶段

第一阶段建议让外部 LLM agent 直接使用 `MemoryService`。

也就是说：

- Unity 工程本身不需要先改
- 不需要先做 Unity 插件
- 不需要先做编辑器可视化工具

只要你的开发 agent 能调用 `MemoryService`，就已经能开始获得收益。

### 3.2 第二阶段

第二阶段再考虑：

- Unity 编辑器工具接入
- 项目内面板接入
- 多 agent 共用记忆服务

### 3.3 不推荐的方式

不建议一开始就做下面这些事情：

- 让 Unity/C# 直接承接 LanceDB 主逻辑
- 把 embedding、rerank、索引编排全部做在 Unity 进程内
- 将长期记忆系统与 Unity runtime 强耦合

## 4. 推荐的数据层设计

建议从第一天就按层管理数据。

### 4.1 文档层

对象示例：

- 架构文档
- 开发规范
- 功能设计
- 模块说明
- 操作手册

特征：

- 稳定
- 权威
- 应优先保留引用来源

### 4.2 项目索引层

对象示例：

- 代码 chunk
- 类和方法摘要
- scene 摘要
- prefab 摘要
- 配置块
- 资源依赖信息

特征：

- 变动频繁
- 是主要检索入口

### 4.3 工作记忆层

对象示例：

- 任务完成摘要
- 历史问题根因
- 某次修复的关键入口
- 任务中验证过的重要发现

特征：

- 更动态
- 需要治理
- 不能无节制写入

### 4.4 稳定知识层

对象示例：

- 多次验证后的项目规则
- 重复任务中反复出现的稳定结论
- 可以回写到 doc 的项目知识

特征：

- 来源于 working memory 的 consolidation
- 应有更高置信度

## 5. 推荐的 schema 字段

每条记录建议至少包含以下字段：

- `id`
- `type`
- `scope`
- `text`
- `summary`
- `vector`
- `source_kind`
- `source_path`
- `source_id`
- `title`
- `tags`
- `importance`
- `confidence`
- `created_at`
- `updated_at`
- `last_accessed_at`
- `access_count`
- `verified`
- `related_ids`

如果是代码对象，建议补充：

- `symbol_name`
- `symbol_kind`
- `class_name`
- `namespace`
- `line_hint`

如果是 Unity 资源对象，建议补充：

- `asset_guid`
- `asset_type`
- `scene_name`
- `prefab_name`
- `component_types`

## 6. 推荐的 scope 设计

建议至少支持以下 scope：

- `global`
- `project:<project-id>`
- `module:<module-name>`
- `scene:<scene-name>`
- `asset:<guid>`
- `agent:<role>`
- `session:<task-id>`

推荐原则如下：

- 查询默认带 `project` scope
- 任务运行中可叠加 `session` scope
- 跨任务稳定知识进入 `project` 或 `global`
- 临时发现先落在 `session`

## 7. 推荐的索引对象优先级

第一阶段先索引最有价值的内容，不要贪全。

推荐优先级如下：

1. 项目 doc
2. 代码与配置
3. 任务摘要
4. scene / prefab 摘要
5. 关系边与稳定知识

这个顺序的原因是：

- doc 与代码能最快形成可用 recall
- 任务摘要能最快带来跨任务收益
- scene 与 prefab 摘要适合第二步补强 Unity 特性

## 8. 推荐的检索策略

### 8.1 默认策略

默认采用：

- metadata filter
- full-text retrieval
- vector retrieval
- hybrid merge
- rerank
- diversity control

### 8.2 为什么不建议纯向量

纯向量在 Unity 工程里容易丢失：

- 类名
- 字段名
- prefab 名
- scene 名
- 配置 key
- 特定枚举或状态名

### 8.3 为什么不建议纯关键词

纯关键词又容易丢失：

- 同义表达
- 历史任务摘要
- 未命名但语义相关的模块
- 设计文档和代码之间的弱关联

### 8.4 推荐的 recall 输出

一次 recall 返回结果建议是结构化的。

建议包含：

- `summary`
- `source_type`
- `source_path`
- `score`
- `why_relevant`
- `citation`
- `next_candidates`

如果 recall 只返回大段原文，不利于 agent 高效消费。

## 9. 推荐的写入策略

### 9.1 写入原则

写入应以“提炼后写入”为原则，而不是“原样存档”。

### 9.2 建议立即写入的内容

- 已完成任务摘要
- 已确认 bug 根因
- 稳定入口映射
- 用户明确确认的开发约定

### 9.3 建议延后 consolidation 的内容

- 多次重复出现的经验
- 高频命中的检索路径
- 多条相近结论的合并版本

### 9.4 不建议写入长期层的内容

- 全量聊天记录
- 未验证推测
- 重复源码片段
- 短期噪声日志

## 10. 推荐的 API 最小集合

第一阶段建议只做最小可用 API。

推荐如下：

- `index.upsert`
- `index.delete`
- `search.recall`
- `memory.store`
- `memory.promote`
- `memory.forget`
- `entity.link`

其中最关键的是：

- `search.recall`
- `memory.store`
- `index.upsert`

这三个 API 足以启动第一阶段闭环。

## 11. 推荐的执行阶段

### 第一阶段：基础索引

目标：

- 建立 LanceDB 表结构
- 打通文档与代码索引
- 建立全文检索和向量检索
- 输出结构化 recall 结果

交付：

- 可检索的项目 doc 与 code index
- 基础 recall API

### 第二阶段：工作记忆

目标：

- 支持任务完成后写入摘要
- 引入 scope 和 importance
- 建立 verified 与 unverified 区分

交付：

- 任务记忆入库
- recall 结果混入历史经验

### 第三阶段：治理与 consolidation

目标：

- 去重
- 合并
- 提升稳定知识
- 回写项目文档候选

交付：

- 更稳的长期记忆层
- 更少的噪声积累

### 第四阶段：多 agent 与 Unity 工具接入

目标：

- 多 agent 共用知识层
- 接 Unity 编辑器工具
- 为后续项目内工具留接口

交付：

- 统一的项目知识总线

## 12. 技术路线建议

在没有特殊约束的情况下，建议如下：

- `MemoryService` 用 Python 或 TypeScript 实现
- LanceDB 作为底层存储与检索引擎
- Embedding 和 rerank 使用外部模型提供方
- Unity 暂时只作为未来客户端之一

这样做的好处是：

- 开发速度快
- 可替换性强
- 生态成熟
- 后续扩展到多 agent 更自然

## 13. 应避免的做法

- 一开始就追求 Unity 深度集成
- 一开始就把所有资源都做重度多模态索引
- 一开始就把全部对话写入长期记忆
- 没有 scope 就做全项目共享大库
- 没有引用溯源就让 agent 直接使用 recall 结果
- 没有源码验证步骤就信任长期记忆输出

## 14. 推荐的首个里程碑

建议首个里程碑定义为：

构建一个仅服务开发期 LLM 的 `MemoryService`，能对项目 doc、代码和任务摘要完成索引与 recall，并返回结构化引用结果，支持在任务中缩小阅读范围而不是替代源码验证。

如果这个里程碑做成，后续无论是多 agent 还是 Unity 编辑器接入，都会简单很多。

## 15. 推荐的后续文档

在本文件之后，建议继续补充以下设计文档：

- schema 设计文档
- recall API 设计文档
- index pipeline 设计文档
- memory write policy 文档
- evaluation 指标文档
