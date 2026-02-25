# PRD 对齐流程详细规范

## 对齐锁机制

### 对齐锁格式（ASCII，便于压缩与检索）

```
ALIGNMENT_LOCK: true
ALIGNMENT_DONE_AT: YYYY-MM-DD
NEXT_ACTION: continue_implementation
DO_NOT_REALIGN: true
ALIGNMENT_SCOPE: 简要描述对齐范围
ALIGNMENT_HASH: 内容哈希
```

### 脚本使用

```bash
# 写入对齐锁
python .codex/skills/protocol-crawler/scripts/alignment_lock.py set --target prd --create

# 检查锁状态
python .codex/skills/protocol-crawler/scripts/alignment_lock.py check --target prd

# 验证锁是否有效（未过期、内容未变更）
python .codex/skills/protocol-crawler/scripts/alignment_lock.py verify --target prd --max-age 30

# 清除锁
python .codex/skills/protocol-crawler/scripts/alignment_lock.py clear --target prd
```

### 对齐锁失效条件

- 用户明确要求变更需求/范围
- PRD 发生重大改动（可通过 `verify` 命令检测内容哈希变化）
- 锁超过 30 天未更新

### 上下文压缩注意事项

发生上下文压缩/摘要时，**必须保留**对齐锁行或等价句：

- `ALREADY_ALIGNED_DO_NOT_REALIGN`
- `===ALIGNMENT_LOCKED===`

避免后续重复对齐。

---

> **完整执行流程见 SKILL.md 步骤 1）PRD 检查与对齐。** 本文件仅记录锁机制本身的技术细节。
