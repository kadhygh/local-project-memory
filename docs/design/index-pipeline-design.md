# Index Pipeline 设计文档

## 1. 目标

第一阶段索引流水线的目标是把 Unity 项目中的文档、代码和任务总结，转换为统一 schema 下可检索、可过滤、可追溯的记录。

## 2. 输入来源

第一阶段只处理：

- `*.md`
- `Assets/**/*.cs`
- `ProjectSettings/**/*`
- `Packages/manifest.json`
- 明确纳入的 `*.json`、`*.yaml`

任务总结不走文件扫描流程，由 `memory.store` 单独写入。

## 3. 流水线阶段

建议流水线拆为以下阶段：

1. 文件发现
2. 文件分类
3. 内容读取与规范化
4. 切块
5. 元数据提取
6. 摘要生成
7. embedding 生成
8. upsert 入库
9. 删除失效记录

## 4. 文件发现

### 4.1 全量索引

全量索引从项目根目录扫描目标模式。

输出应是一个文件清单，每条至少包含：

- `path`
- `kind`
- `modified_at`
- `size`

### 4.2 增量索引

第一阶段推荐两种方式：

- 基于文件时间戳
- 基于 Git 变化清单

如果 Git 不可用，则退回时间戳策略。

## 5. 文件分类

建议把文件先分到以下类别：

- `document`
- `code`
- `config`

第一阶段 `config` 仍可统一落为 `doc_chunk` 或 `code_chunk` 风格文本块，只要来源可追溯即可。

## 6. 规范化

读取阶段应完成：

- UTF-8 读取
- 换行统一
- 去除明显无意义的空白噪声
- 保留原始路径

不应在这一层做过强清洗，否则会破坏引用和后续验证。

## 7. 切块策略

### 7.1 文档切块

对 `*.md` 建议按标题层级和段落切块。

推荐规则：

- 优先按一级和二级标题分段
- 若单段过长，再按段落数切块
- 保留 `doc_section` 和 `doc_order`

### 7.2 代码切块

对 `*.cs` 建议优先做符号级切块。

推荐优先级：

- class
- interface
- enum
- method

如果第一版无法稳定做 AST 级切块，可先退化为：

- 固定窗口切块
- 同时保留文件路径与起始行号

### 7.3 配置切块

对 `manifest.json`、项目配置等，建议按逻辑块切分。

第一阶段允许简单按文件或大段落切块，只要引用稳定。

## 8. 元数据提取

每个块至少提取：

- `project_id`
- `type`
- `scope`
- `source_kind`
- `source_path`
- `title`
- `line_hint`
- `citation`

代码块建议额外提取：

- `symbol_name`
- `class_name`
- `namespace`

## 9. 摘要生成

第一阶段允许使用简单策略：

- 文档块使用首句或标题加短摘要
- 代码块使用符号名加用途短句
- 配置块使用键名和用途短句

后续再接入 LLM 辅助摘要。

第一阶段的要求不是摘要文采，而是摘要可读且能帮助 recall 展示。

## 10. Embedding 策略

第一阶段要求统一 embedding 策略，保证：

- 查询向量化与文档向量化兼容
- 文档、代码、任务总结使用同一版本模型

如果初版先不上真实 embedding 服务，也应保留统一接口。

## 11. Upsert 规则

每次入库前应生成稳定 ID。

upsert 必须满足：

- 相同 ID 覆盖更新
- 新记录写入
- 失效文件对应记录可删除或标记失效

## 12. 首批样本建议

在真正接 Unity 项目前，可以先拿当前仓库已有文档做首批样本：

- `docs/research/lancedb-research.md`
- `docs/research/unity-core-needs.md`
- `docs/research/implementation-recommendations.md`
- `docs/validation/mvp-acceptance.md`
- `docs/design/phase1-boundary.md`
- `docs/design/schema-design.md`
- `docs/design/recall-api-design.md`

这样可以先验证：

- 文档切块
- upsert 流程
- recall 返回格式

## 13. 第一阶段失败点

流水线第一版最容易出问题的地方包括：

- 切块过大导致噪声高
- 切块过碎导致上下文丢失
- `source_path` 或 `citation` 不稳定
- 文档和代码摘要质量太差
- 增量更新无法正确覆盖旧记录

这些点应优先进入测试清单。

## 14. 第一阶段结论

索引流水线第一版不需要复杂，但必须保证三个基本质量：

- 数据能进来
- 结果能追溯
- 更新能稳定

只要这三点成立，就可以开始验证 recall 对真实开发任务的价值。

