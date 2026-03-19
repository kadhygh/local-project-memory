# 推进进度

## 当前阶段

- 阶段：Phase 1 MVP 实现
- 目标：跑通 `index.upsert -> search.recall -> memory.store` 的最小闭环
- 当前状态：MVP 闭环已打通，CLI 与 LanceDB 持久化适配已接入

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
- 新增 `ProjectIndexer`，支持对真实项目目录执行全量索引
- 新增代码文件与配置文件切块第一版
- 用 `project_mining` 完成首轮真实接入 smoke check
- 完成仓库工程化整理为 `local-project-memory`
- 文档迁移到 `docs/research`、`docs/design`、`docs/validation`、`docs/roadmap`
- Python 包名统一为 `local_project_memory`
- 补充根目录 `README.md`
- 新增 `docs/README.md` 作为统一文档入口
- 新增 `docs/design/memory-governance-and-human-interface.md`
- 新增 `docs/design/project-memory-workflow.md`
- 新增 CLI：`lpm index`、`lpm search`
- 新增 LanceDB 持久化适配：`src/local_project_memory/services/lancedb_store.py`
- 完成测试验证：`18 passed`

## 当前里程碑定义

- 能扫描项目文档
- 能将文档切块为 `KnowledgeRecord`
- 能完成 upsert
- 能通过 `search.recall` 返回带 citation 的结构化结果
- 能写入 `task_summary`
- 能对中文文档执行基础关键词 recall
- 能通过本地测试与 smoke check 验证最小闭环
- 能对真实 Unity 项目执行首轮 doc/code/config 索引
- 能通过 CLI 直接触发项目索引
- 能通过 LanceDB 持久化保存与复用项目索引

## 风险与阻塞

- 尚未接入真实 embedding，当前先用关键词与简单评分替代
- 代码切块仍是轻解析，不是 AST
- 配置切块仍是段落/锚点级，不是 schema-aware
- 当前排序仍是启发式规则，没有 hybrid merge / rerank / diversity control
- 尚未接入真实 Unity 项目做首轮正式 MVP 验收
- 当前 LanceDB 适配重点是持久化与兼容性，不是高性能混合检索

## 下一步

- 以一个本地 Unity 项目执行第一轮 MVP 验收
- 设计第一轮题库与真实开发任务清单
- 增加项目级 HTTP 索引接口
- 演进 recall，从关键词排序提升到 hybrid / vector / rerank
- 继续完善 memory 写回治理和架构师 agent 规则设计

## 本轮验证

- `python -m pytest -q tests/test_api.py tests/test_cli.py tests/test_indexer.py tests/test_lancedb_store.py tests/test_models.py tests/test_project_index.py tests/test_services.py -p no:cacheprovider`
- 结果：`18 passed`
- 文档索引 smoke check：当前仓库共生成 `486` 个 Markdown chunk
- 中文 recall smoke check：查询 `长期记忆 检索` 返回 `5` 条结构化结果
- LanceDB CLI smoke check：
  - `lpm index --storage-backend lancedb` 可持久化索引 `project_mining`
  - `lpm search --storage-backend lancedb --no-index` 可在新进程中复用已有索引

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

## 设计参考

- 知识层边界：`docs/design/memory-governance-and-human-interface.md`
- 工作流闭环：`docs/design/project-memory-workflow.md`
- 索引流水线：`docs/design/index-pipeline-design.md`
- Recall 接口：`docs/design/recall-api-design.md`
- Schema：`docs/design/schema-design.md`
- 验收标准：`docs/validation/mvp-acceptance.md`
- 统一文档入口：`docs/README.md`