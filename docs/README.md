# 文档总览

这是 `local-project-memory` 的统一文档入口。

如果你第一次进入这个仓库，建议按下面顺序阅读：

1. 项目说明
2. 设计文档
3. 验收文档
4. 推进进度

## 目录结构

```text
docs/
  README.md
  design/
  research/
  roadmap/
  validation/
```

## 建议阅读顺序

### 1. 项目理解

- [仓库 README](/D:/Projects/memory-lancedb-pro/README.md)
  - 了解项目定位、当前状态和主要目标

### 2. 研究与背景

位于 `docs/research/`：

- [lancedb-research.md](/D:/Projects/memory-lancedb-pro/docs/research/lancedb-research.md)
  - 解释为什么选择 LanceDB 作为候选底层引擎
- [unity-core-needs.md](/D:/Projects/memory-lancedb-pro/docs/research/unity-core-needs.md)
  - 定义 Unity 开发场景中的核心需求
- [implementation-recommendations.md](/D:/Projects/memory-lancedb-pro/docs/research/implementation-recommendations.md)
  - 说明推荐架构和落地方向

### 3. 核心设计

位于 `docs/design/`：

- [phase1-boundary.md](/D:/Projects/memory-lancedb-pro/docs/design/phase1-boundary.md)
  - 第一阶段范围和非目标
- [schema-design.md](/D:/Projects/memory-lancedb-pro/docs/design/schema-design.md)
  - 统一记录模型与字段设计
- [recall-api-design.md](/D:/Projects/memory-lancedb-pro/docs/design/recall-api-design.md)
  - recall 和最小 API 合同
- [index-pipeline-design.md](/D:/Projects/memory-lancedb-pro/docs/design/index-pipeline-design.md)
  - 文档、代码、配置、任务总结如何进入索引
- [memory-governance-and-human-interface.md](/D:/Projects/memory-lancedb-pro/docs/design/memory-governance-and-human-interface.md)
  - 人类知识层、机器 memory 层和治理接口边界
- [project-memory-workflow.md](/D:/Projects/memory-lancedb-pro/docs/design/project-memory-workflow.md)
  - 项目初始化、执行、收尾、治理四步闭环

### 4. 验收与验证

位于 `docs/validation/`：

- [mvp-acceptance.md](/D:/Projects/memory-lancedb-pro/docs/validation/mvp-acceptance.md)
  - MVP 如何在真实项目里验证价值

### 5. 推进与现状

位于 `docs/roadmap/`：

- [progress.md](/D:/Projects/memory-lancedb-pro/docs/roadmap/progress.md)
  - 当前完成了什么、接下来做什么、真实项目验证结果如何

## 按角色阅读

如果你是第一次参与这个项目，可以按角色选择入口：

- 产品或架构视角：
  - 先看 [仓库 README](/D:/Projects/memory-lancedb-pro/README.md)
  - 再看 [project-memory-workflow.md](/D:/Projects/memory-lancedb-pro/docs/design/project-memory-workflow.md)
  - 再看 [memory-governance-and-human-interface.md](/D:/Projects/memory-lancedb-pro/docs/design/memory-governance-and-human-interface.md)

- 实现视角：
  - 先看 [phase1-boundary.md](/D:/Projects/memory-lancedb-pro/docs/design/phase1-boundary.md)
  - 再看 [schema-design.md](/D:/Projects/memory-lancedb-pro/docs/design/schema-design.md)
  - 再看 [index-pipeline-design.md](/D:/Projects/memory-lancedb-pro/docs/design/index-pipeline-design.md)
  - 再看 [recall-api-design.md](/D:/Projects/memory-lancedb-pro/docs/design/recall-api-design.md)

- 验收视角：
  - 先看 [mvp-acceptance.md](/D:/Projects/memory-lancedb-pro/docs/validation/mvp-acceptance.md)
  - 再看 [progress.md](/D:/Projects/memory-lancedb-pro/docs/roadmap/progress.md)

## 当前推荐入口

如果只想从一个地方开始，我建议从：

- [docs/README.md](/D:/Projects/memory-lancedb-pro/docs/README.md)

然后依次阅读：

1. [README.md](/D:/Projects/memory-lancedb-pro/README.md)
2. [project-memory-workflow.md](/D:/Projects/memory-lancedb-pro/docs/design/project-memory-workflow.md)
3. [memory-governance-and-human-interface.md](/D:/Projects/memory-lancedb-pro/docs/design/memory-governance-and-human-interface.md)
4. [progress.md](/D:/Projects/memory-lancedb-pro/docs/roadmap/progress.md)