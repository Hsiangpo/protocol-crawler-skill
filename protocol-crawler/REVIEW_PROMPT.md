# Skill 专业评审提示词

> 将以下内容连同你的 skill 文件一起发给评审者（AI 或人类）。

---

## 📋 评审指令

你是一位 **AI Agent Skill 架构师**，精通 Codex/Claude Code/Cursor 等 AI 编码工具的 skill 系统设计。你的任务是对以下 skill 进行**多维度专业评审**并打分。

### 评审对象

**Skill 名称**：protocol-crawler（协议爬虫）

**请阅读以下文件**（按优先级）：

1. `SKILL.md` — 主文件（必读）
2. `references/core/_index.md` — core 参考导航
3. `references/humanization/_index.md` — 拟人化参考导航
4. `references/core/engineering-standards.md` — 工程规范
5. `references/humanization/network-layer.md` — 网络层拟人化
6. `references/core/error-checkpoint.md` — 错误处理与断点续跑
7. `references/yzm/captcha-solutions.md` — 验证码处理方案
8. `scripts/ci_gate.py` — CI 门禁自动检查脚本
9. `scripts/alignment_lock.py` — PRD 对齐锁脚本
10. `examples/README.md` — 端到端示例
11. `templates/nx-param-doc.md` — 逆向参数文档模板

### 评审维度（每项 1-10 分）

请从以下 **10 个维度**评分，每个维度给出分数 + 简要理由 + 具体改进建议：

| #       | 维度                          | 评分要点                                                                                                                                                 |
| ------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **D1**  | **触发精准度**                | Description 是否只包含触发条件（"Use when..."）？是否覆盖了足够的关键词让 Agent 能正确匹配到这个 skill？是否避免在 description 中总结工作流？            |
| **D2**  | **Agent 执行纪律**            | 流程中是否有足够的门禁（gate）机制防止 Agent 跳步骤？强制规则是否足够醒目（emoji/格式/位置）？是否有 Red Flags / 反合理化表防止 Agent 自我绕过？         |
| **D3**  | **Token 效率**                | SKILL.md 长度是否合理？关键信息是内联还是外放 reference？是否存在重复内容？决策树/表格是否比叙述性段落更节省 token？                                     |
| **D4**  | **技术完备性**                | 对于协议爬虫这个领域，核心技术点是否覆盖全面？（TLS 指纹、HTTP/2、Session 管理、限速、断点续跑、代理管理、验证码、错误处理、数据校验等）是否有明显遗漏？ |
| **D5**  | **防错设计**                  | 是否预判了 Agent 最容易犯的错误并提前堵死？（如裸用 requests、跳过抓包、静默空跑、硬编码凭据、屎山代码等）每个禁止项是否给了替代的正确做法？             |
| **D6**  | **可执行性**                  | 每个步骤是否足够具体让 Agent 能直接执行？是否有明确的输入/输出要求？代码示例是否可直接使用？脚本（ci_gate.py / alignment_lock.py）是否能正常运行？       |
| **D7**  | **用户可控性**                | 用户在流程中是否有足够的控制点？（如对齐检查、方案确认、异常报告等）Agent 是否会在关键节点主动停下来等待用户反馈，而不是默默推进？                       |
| **D8**  | **可维护性**                  | 文件结构是否清晰分层？references 是否有索引导航（\_index.md）？新增内容是否容易知道放在哪里？是否有版本/路径硬编码？                                     |
| **D9**  | **示例质量**                  | examples/ 是否提供了完整的端到端参考？代码示例是否展示了最佳实践（限速、断点续跑、异常处理、.env 管理等）？示例是否足够让 Agent 理解交付物标准？         |
| **D10** | **与 Superpowers 生态的集成** | 是否正确引用了 Superpowers 的 skills（TDD、systematic-debugging 等）？引用方式是否符合规范（skill name，非绝对路径）？是否有合理的降级策略（未安装时）？ |

### 输出格式

请按以下格式输出：

```
## 评审报告：protocol-crawler

### 总分：XX / 100

### 各维度评分

| 维度 | 分数 | 理由 |
|------|------|------|
| D1 触发精准度 | X/10 | ... |
| D2 Agent 执行纪律 | X/10 | ... |
| D3 Token 效率 | X/10 | ... |
| D4 技术完备性 | X/10 | ... |
| D5 防错设计 | X/10 | ... |
| D6 可执行性 | X/10 | ... |
| D7 用户可控性 | X/10 | ... |
| D8 可维护性 | X/10 | ... |
| D9 示例质量 | X/10 | ... |
| D10 Superpowers 集成 | X/10 | ... |

### 🏆 最大优势（Top 3）
1. ...
2. ...
3. ...

### ⚠️ 最大风险（Top 3）
1. ...（附具体改进建议）
2. ...
3. ...

### 🔧 具体改进建议（按优先级排序）
1. [P0] ...
2. [P1] ...
3. [P2] ...
...
```

### 评审标准参考

**满分标准（各维度 9-10 分）**：

- Superpowers 官方 skills 的设计水平（如 `systematic-debugging`、`test-driven-development`、`writing-plans`）
- 遵循 `writing-skills` 的所有规范（CSO、Token 效率、交叉引用、决策树使用规则等）
- Agent 执行覆盖率 > 95%（即 Agent 在 95% 以上的场景下都能按 skill 意图正确行动）

**合格标准（各维度 6-7 分）**：

- 核心流程完整，强制规则醒目
- 关键技术点覆盖，无致命遗漏
- Agent 能在大部分场景下正确执行

**不合格标准（各维度 < 5 分）**：

- 流程缺失或模糊，Agent 容易跑偏
- 技术点有明显遗漏
- 格式不规范，Token 浪费严重
