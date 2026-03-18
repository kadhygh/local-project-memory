# 推进进度

## 当前阶段

- 阶段：Phase 1 MVP 实现
- 目标：跑通 `index.upsert -> search.recall -> memory.store` 的最小闭环
- 当前状态：本轮闭环已打通并完成基础验证

## 真实样本项目

- 知识库根目录：`D:\Projects\project_mining`
- Unity 项目根目录：`D:\Projects\project_mining\UnityProject`
- 文档入口：`D:\Projects\project_mining\Docs\readme.md`
- 当前观测：
  - `Docs/**/*.md` 约 `71` 个
  - `UnityProject/Assets/**/*.cs` 约 `2965` 个
  - 第一轮建议优先索引 `Docs/**/*.md`、`UnityProject/Assets/**/*.cs`、`UnityProject/ProjectSettings/*`、`UnityProject/Packages/manifest.json`

## 已完成

- 完成调研、需求、落地建议文档
- 补齐 MVP 验收文档
- 补齐第一阶段边界、schema、recall API、index pipeline 设计文档
- 建立 Python 最小工程骨架
- 建立 FastAPI 最小接口占位
- 实现内存版 `index.upsert`
- 实现内存版 `memory.store`
- 实现基于关键词和 metadata 过滤的基础 `search.recall`
- 实现 Markdown 文档发现与切块
- 增加服务层与 index pipeline 的基础测试
- 完成一次本地 smoke check，确认服务接口与最小闭环可导入运行
- 补齐 `ChunkCandidate -> KnowledgeRecord` 映射
- 修复 packaging 配置，使 `pip install -e .[dev]` 可用
- 修复 recall 的噪声问题，避免“零命中也有分”
- 修复中文 query 的基础 tokenization
- 修复测试环境对系统 Temp 的依赖，改为仓库内工作目录
- 完成测试验证：`14 passed`
- 完成中文 recall smoke check：基于当前仓库 486 个文档 chunk 命中 5 条结果
- 新增 `ProjectIndexer`，支持对真实项目目录执行全量索引
- 新增代码文件与配置文件切块第一版
- 用 `project_mining` 完成首轮真实接入 smoke check

## 本轮任务

- 建立统一推进进度文档
- 实现文档级索引与切块
- 实现最小存储层
- 实现基础 recall 排序与结果结构化
- 补 API 级集成测试
- 将 index pipeline 产物接到存储层
- 整理本轮验证结论与下一轮实现目标

## 当前拆分

- 主线任务：维护进度、整合结果、补运行链路
- 子任务 A：实现最小存储与 recall 闭环，已完成
- 子任务 B：实现 index pipeline 的文档切块与记录产出，已完成
- 子任务 C：补映射层、包结构与 API 级测试，已完成
- 子任务 D：修复 recall 噪声与中文 tokenization，已完成

## 当前里程碑定义

- 能扫描项目文档
- 能将文档切块为 `KnowledgeRecord`
- 能完成 upsert
- 能通过 `search.recall` 返回带 citation 的结构化结果
- 能写入 `task_summary`
- 能对中文文档执行基础关键词 recall
- 能通过本地测试与 smoke check 验证最小闭环
- 能对真实 Unity 项目执行首轮 doc/code/config 索引

## 风险与阻塞

- 尚未接入真实 LanceDB，当前先用内存存储替代
- 尚未接入真实 embedding，当前先用关键词与简单评分替代
- 代码切块仍是轻解析，不是 AST
- 配置切块仍是段落/锚点级，不是 schema-aware
- 当前排序仍是启发式规则，没有 hybrid merge / rerank / diversity control
- 尚未接入真实 Unity 项目做首轮验收
- 当前真实项目 smoke check 仍以内存库单进程运行，无法跨进程复用

## 下一步

- 接入真实 LanceDB 或至少抽象出存储适配层
- 以一个本地 Unity 项目执行第一轮 MVP 验收
- 设计第一轮题库与真实开发任务清单
- 增加用户可直接触发的索引命令或 API

## 本轮验证

- `python -m pytest -q tests/test_api.py tests/test_indexer.py tests/test_models.py tests/test_services.py -p no:cacheprovider`
- `python -m pytest -q tests/test_api.py tests/test_indexer.py tests/test_models.py tests/test_project_index.py tests/test_services.py -p no:cacheprovider`
- 结果：`14 passed`
- 文档索引 smoke check：当前仓库共生成 486 个 Markdown chunk
- 中文 recall smoke check：查询 `长期记忆 检索` 返回 5 条结构化结果

## 真实项目验证

- 真实项目：`D:\Projects\project_mining`
- Unity 根：`D:\Projects\project_mining\UnityProject`
- 文档入口：`D:\Projects\project_mining\Docs\readme.md`
- 真实索引 smoke check：
  - `docs_chunks = 2000`
  - `code_chunks = 34782`
  - `config_chunks = 35`
  - `upserted = 36817`
- 代表性 recall：
  - 查询 `UnityGatewayAgent`，命中 `Assets/Editor/LocalLLMGateway/UnityGatewayAgent.cs`
  - 查询 `PrefabHelperApi`，命中 `Assets/Editor/LocalLLMGateway/PrefabHelper/PrefabHelperApi.cs`
  - 查询 `长期记忆 检索`，能返回中文文档结果

## Repository Preparation

- 仓库工程化整理为 `local-project-memory`
- 文档迁移到 `docs/research`、`docs/design`、`docs/validation`、`docs/roadmap`
- Python 包名统一为 `local_project_memory`
- 补充根目录 `README.md`
- 下一步准备首个 git 提交并推送到空远端仓库
