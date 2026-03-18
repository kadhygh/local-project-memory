# LanceDB 调研报告

## 1. 调研目标

本文档的目标不是泛泛介绍向量数据库，而是判断 LanceDB 是否适合作为 Unity 开发期 LLM agent 的长期记忆与超级索引底座。

本次调研重点关注以下问题：

- LanceDB 当前的产品形态和运行方式是什么
- LanceDB 是否支持 Unity 开发场景需要的检索能力
- LanceDB 是否适合直接由 Unity/C# 调用
- LanceDB 在长期记忆方案中更适合扮演什么角色
- 在后续落地时需要规避哪些技术风险

## 2. 结论摘要

- LanceDB 适合作为长期记忆服务中的底层检索与存储引擎。
- LanceDB 不等于“完整长期记忆系统”，它解决的是表存储、向量检索、全文检索、混合检索、索引与多模态数据管理。
- 对 Unity 开发工作流而言，最合理的使用方式不是让 Unity 直接深度绑定 LanceDB，而是通过独立的 `MemoryService` 或 `IndexService` 访问 LanceDB。
- LanceDB 很适合支撑“先语义定位，再精确读源码”的工作流，因此非常适合 LLM 开发代理、项目级超级索引和长期记忆服务。
- LanceDB 目前官方重点 SDK 为 Python、TypeScript、Rust 和 REST；没有官方 C# SDK 作为一等接入方式，因此 Unity 侧更适合通过服务接口接入。

## 3. LanceDB 是什么

根据官方 README，LanceDB 的定位已经不再只是一个传统意义上的 vector database，而是一个面向 AI/ML 应用的 multimodal AI lakehouse。

从官方材料看，LanceDB 的核心特征包括：

- 支持向量检索
- 支持全文检索和 SQL 能力
- 支持多模态数据，包括文本、图片、视频、点云等
- 基于 Lance 列式格式构建
- 支持本地开源运行，也支持 Cloud / Enterprise
- 支持 Python、Node.js、Rust 和 REST API

对我们这类 Unity 开发场景来说，真正重要的不是它的宣传定位，而是它提供了足够完整的检索能力组合。

## 4. 运行方式与部署模型

LanceDB 的运行方式对后续架构设计很关键。

官方 Quickstart 明确说明：

- 开源版可以作为 embedded database 在进程内运行，使用方式类似 SQLite
- 可以连接本地文件路径
- 可以连接对象存储 URI，例如 `s3://`、`gs://`、`az://`
- Cloud / Enterprise 则使用 `db://...` URI 连接远程服务

这意味着 LanceDB 至少支持三种适合我们评估的运行模式：

- 本地文件模式
- 对象存储模式
- 托管或远程服务模式

对开发期 LLM 超级索引而言，最可行的通常是：

- 本地开发阶段使用本地文件模式
- 团队共享或远程部署阶段使用对象存储或托管方式

## 5. 与 Unity 开发相关的核心能力

### 5.1 向量检索

LanceDB 支持向量相似度检索，这一层是长期记忆和语义索引的基础。

向量检索适合这些 Unity 开发查询：

- “僵尸生成相关逻辑在哪”
- “和任务系统状态切换最相关的脚本有哪些”
- “这个场景切换问题以前在哪里修过”
- “和某个 prefab 功能相近的其他资源在哪”

单看向量检索还不够，但它是语义召回的入口能力。

### 5.2 全文检索

LanceDB 官方文档显示其支持基于 BM25 的 Full-Text Search。

这对 Unity 工程尤其重要，因为很多检索不是纯语义，而是强关键词驱动，例如：

- 脚本类名
- 组件名
- prefab 名
- scene 名
- 特定配置字段
- 枚举值
- 任务 ID

如果没有全文检索，很多工程检索会出现语义上相关、但工程上不精确的问题。

### 5.3 混合检索

官方提供了 Hybrid Search，将语义检索和全文检索结合，并使用 reranker 重新排序。

这一点对 Unity 开发期 LLM 是高价值能力，因为真实查询通常天然混合：

- 一部分是意图
- 一部分是术语
- 一部分是项目内部命名
- 一部分是上下文线索

因此对于代码、配置、文档、场景资源统一检索时，Hybrid Search 比纯向量检索更符合实际需求。

### 5.4 Reranking

LanceDB 支持对召回结果进行 rerank，官方文档列出内建的 Cohere、CrossEncoder 等方式。

这对工程问题尤其有价值，因为初召回只负责“找一批可能相关的东西”，而不是直接给最终答案。Rerank 可以显著提升前几条结果的可用性，降低噪声。

### 5.5 Embedding 管理

官方 Embeddings 文档说明 LanceDB 具有 embedding function registry，支持在写入时自动生成 embedding，并在 OSS 版本中支持查询时自动向量化。

这一点的意义是：

- 可以把 embedding 逻辑与表 schema 绑定
- 可以统一 source document 和 query 的 embedding 方式
- 可以接入多种模型提供方
- 可以在服务层控制 embedding 策略，而不是让 Unity 直接管理

### 5.6 Metadata 过滤与标量索引

官方文档显示 LanceDB 支持 scalar index，包括 BTREE、BITMAP、LABEL_LIST 等。

这对长期记忆系统非常关键，因为真正有用的检索通常不是“全库乱搜”，而是带 scope 的过滤，例如：

- 仅在某个 project 内检索
- 仅在某个 scene 或 system 内检索
- 仅看 doc
- 仅看 code
- 仅看已验证记忆
- 仅看最近一周任务结果

如果 metadata 过滤做得好，检索质量通常会比单纯增强 embedding 更稳定。

### 5.7 向量索引与性能调优

官方文档显示 LanceDB 支持多种向量索引与压缩方案，包括：

- IVF
- IVF_PQ
- IVF_RQ
- IVF_HNSW_SQ

并提供不同场景下的 recall / latency / compression 权衡建议。

这说明 LanceDB 适合从中小规模项目逐步扩展到更大规模数据集，而不需要一开始就切到另一套存储引擎。

## 6. LanceDB 对长期记忆系统的价值

LanceDB 适合扮演的是“长期记忆系统的底层引擎”，而不是完整记忆编排层。

更准确地说，它适合负责：

- 存储记忆片段、文档块、代码块、资源摘要和 metadata
- 建立向量索引
- 建立全文索引
- 提供混合检索和 rerank 基础能力
- 支持过滤、分 scope、分表或分 namespace 管理

它不天然负责这些内容：

- 哪些信息应该写入长期记忆
- 任务结束后如何抽取记忆摘要
- 记忆冲突如何合并
- 哪些记忆应该淘汰
- 哪些记忆应该晋升为稳定文档
- recall 结果如何注入到 agent prompt 中

这些能力需要由我们自己的 `MemoryService` 或 `Agent Orchestrator` 来补齐。

## 7. 对 Unity 工程的适配判断

### 7.1 适合的点

- 适合作为代码、文档、配置、资源摘要的统一检索底座
- 适合做 project-level 知识库
- 适合做长期记忆库和索引库的统一底层
- 适合做“先召回候选，再精读源码”的 LLM 工作流
- 适合同时服务单 agent 和多 agent

### 7.2 不适合直接做的点

- 不适合把 LanceDB 直接深嵌到 Unity runtime 里作为一等运行核心
- 不适合让 Unity/C# 直接承接复杂 embedding、rerank、memory consolidation 全流程
- 不适合把 LanceDB 误当成完整的 agent memory plugin

### 7.3 最推荐的接法

- 用 Python 或 TypeScript 做外部 `MemoryService`
- 让 `MemoryService` 封装 LanceDB 的表结构、索引策略、embedding 和 recall API
- Unity 或外部 coding agent 通过 HTTP / gRPC / MCP 风格接口访问

## 8. 主要优点

- 本地开源版启动门槛低
- 同时具备向量检索、全文检索、混合检索能力
- 支持多模态数据，后续可扩展到图片和资源预览信息
- 支持标量索引和 metadata filter，适合工程检索
- 支持多种索引类型，后续能做规模化优化
- 有 REST 和多语言 SDK，适合服务化封装

## 9. 主要限制与风险

### 9.1 不是完整长期记忆方案

如果没有额外的记忆抽取、去重、分层、淘汰、scope 管理与 prompt 注入逻辑，LanceDB 只能算检索底座，不会自动变成“长期记忆系统”。

### 9.2 Unity 直连不是最优路径

官方一等接入方式不是 C#。这意味着如果我们坚持让 Unity 直接与 LanceDB 深度耦合，开发和运维成本会高于“外部服务 + Unity 接口层”方案。

### 9.3 检索质量依赖上层设计

LanceDB 提供检索能力，但最终质量高度依赖：

- chunk 策略
- schema 设计
- metadata 完整度
- embedding 模型选择
- rerank 策略
- scope 设计
- memory write policy

### 9.4 不能替代 source of truth

长期记忆或索引命中的结果，仍然只是候选线索和候选上下文。涉及代码修改和结论确认时，最终仍应回到源码、配置和文档原文验证。

## 10. 对当前方向的判断

如果目标是下面这类能力，LanceDB 是合适的底层候选：

- 为 Unity 开发期 LLM 建立超级索引
- 让 LLM 更快定位相关源码、文档、scene、prefab、配置
- 为多轮任务提供跨任务长期记忆
- 为多 agent 系统提供共享 recall 底座

如果目标是“一个装上就能工作的完整 agent 记忆系统”，LanceDB 本身并不直接满足，需要外面再包一层服务和策略。

## 11. 最终建议

- 把 LanceDB 定位为长期记忆与项目索引系统的底层引擎。
- 不要把 LanceDB 直接等同于记忆系统本身。
- 第一阶段优先做面向开发期 LLM 的 `MemoryService`。
- 先服务代码、文档、配置和任务摘要，不要一开始就追求 Unity runtime 深度集成。
- 优先建设 hybrid retrieval、metadata filtering、scope 管理和引用溯源能力。

## 12. 参考资料

- LanceDB 官方 README: https://github.com/lancedb/lancedb
- LanceDB 官方文档首页: https://docs.lancedb.com/
- LanceDB Quickstart: https://docs.lancedb.com/quickstart
- LanceDB Embeddings: https://docs.lancedb.com/embedding
- LanceDB Full-Text Search: https://docs.lancedb.com/search/full-text-search
- LanceDB Hybrid Search: https://docs.lancedb.com/search/hybrid-search
- LanceDB Reranking: https://docs.lancedb.com/reranking
- LanceDB Vector Index: https://docs.lancedb.com/indexing/vector-index
- LanceDB Scalar Index: https://docs.lancedb.com/indexing/scalar-index
- LanceDB Storage: https://docs.lancedb.com/storage
