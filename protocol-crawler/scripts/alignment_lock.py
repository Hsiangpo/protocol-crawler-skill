"""
对齐锁管理器 (Alignment Lock Manager)

增强版对齐锁脚本，支持：
- 写入对齐锁
- 读取/验证对齐锁状态
- 锁过期检测
- 锁清理

使用方式：
  # 写入锁
  python alignment_lock.py set --target prd --create
  
  # 读取锁状态
  python alignment_lock.py check --target prd
  
  # 清除锁
  python alignment_lock.py clear --target prd
  
  # 验证锁是否有效（未过期）
  python alignment_lock.py verify --target prd --max-age 30
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional


# ============ 常量定义 ============

LOCK_KEYS = (
    "ALIGNMENT_LOCK:",
    "ALIGNMENT_DONE_AT:",
    "NEXT_ACTION:",
    "DO_NOT_REALIGN:",
    "ALIGNMENT_SCOPE:",  # 新增：对齐范围摘要
    "ALIGNMENT_HASH:",   # 新增：对齐内容哈希（用于检测变更）
)

# 用于上下文压缩时保留的标记（AI 必须识别）
COMPRESSION_MARKERS = [
    "ALIGNMENT_LOCK: true",
    "DO_NOT_REALIGN: true",
    "ALREADY_ALIGNED_DO_NOT_REALIGN",
    "===ALIGNMENT_LOCKED===",
]


# ============ 数据结构 ============

@dataclass
class AlignmentLock:
    """对齐锁数据结构。"""
    is_locked: bool
    done_at: Optional[str] = None
    next_action: Optional[str] = None
    scope: Optional[str] = None
    content_hash: Optional[str] = None
    
    def is_expired(self, max_age_days: int = 30) -> bool:
        """检查锁是否过期。"""
        if not self.done_at:
            return True
        try:
            lock_date = datetime.fromisoformat(self.done_at)
            age = datetime.now() - lock_date
            return age > timedelta(days=max_age_days)
        except ValueError:
            return True
    
    def to_block(self) -> str:
        """生成锁文本块。"""
        lines = [
            "ALIGNMENT_LOCK: true",
            f"ALIGNMENT_DONE_AT: {self.done_at or date.today().isoformat()}",
            f"NEXT_ACTION: {self.next_action or 'continue_implementation'}",
            "DO_NOT_REALIGN: true",
        ]
        if self.scope:
            lines.append(f"ALIGNMENT_SCOPE: {self.scope}")
        if self.content_hash:
            lines.append(f"ALIGNMENT_HASH: {self.content_hash}")
        return "\n".join(lines)
    
    def __str__(self) -> str:
        status = "🔒 LOCKED" if self.is_locked else "🔓 UNLOCKED"
        parts = [status]
        if self.done_at:
            parts.append(f"  Done at: {self.done_at}")
        if self.next_action:
            parts.append(f"  Next action: {self.next_action}")
        if self.scope:
            parts.append(f"  Scope: {self.scope}")
        return "\n".join(parts)


# ============ 核心功能 ============

def compute_content_hash(content: str) -> str:
    """计算内容哈希（用于检测 PRD 变更）。"""
    import hashlib
    # 移除锁相关行后计算哈希
    lines = []
    for line in content.splitlines():
        if not any(line.startswith(key) for key in LOCK_KEYS):
            lines.append(line)
    clean_content = "\n".join(lines).strip()
    return hashlib.md5(clean_content.encode("utf-8")).hexdigest()[:8]


def parse_lock(content: str) -> AlignmentLock:
    """从文件内容解析对齐锁。"""
    lock = AlignmentLock(is_locked=False)
    
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("ALIGNMENT_LOCK:"):
            lock.is_locked = "true" in line.lower()
        elif line.startswith("ALIGNMENT_DONE_AT:"):
            lock.done_at = line.split(":", 1)[1].strip()
        elif line.startswith("NEXT_ACTION:"):
            lock.next_action = line.split(":", 1)[1].strip()
        elif line.startswith("ALIGNMENT_SCOPE:"):
            lock.scope = line.split(":", 1)[1].strip()
        elif line.startswith("ALIGNMENT_HASH:"):
            lock.content_hash = line.split(":", 1)[1].strip()
        # 兼容简写标记
        elif line == "ALREADY_ALIGNED_DO_NOT_REALIGN":
            lock.is_locked = True
        elif line == "===ALIGNMENT_LOCKED===":
            lock.is_locked = True
            
    return lock


def remove_lock_lines(content: str) -> str:
    """移除现有的锁相关行。"""
    lines = []
    for line in content.splitlines():
        if any(line.strip().startswith(key) for key in LOCK_KEYS):
            continue
        if line.strip() in ("ALREADY_ALIGNED_DO_NOT_REALIGN", "===ALIGNMENT_LOCKED==="):
            continue
        lines.append(line)
    return "\n".join(lines)


def write_lock(path: Path, lock: AlignmentLock, create: bool = False) -> bool:
    """写入对齐锁到文件。"""
    if not path.exists() and not create:
        return False
    
    content = ""
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = remove_lock_lines(content).rstrip()
        # 计算内容哈希
        lock.content_hash = compute_content_hash(content)
    
    # 拼接新内容
    if content:
        new_content = content + "\n\n" + lock.to_block() + "\n"
    else:
        new_content = lock.to_block() + "\n"
    
    # 原子写入
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new_content, encoding="utf-8")
    tmp.replace(path)
    
    return True


def read_lock(path: Path) -> Optional[AlignmentLock]:
    """读取对齐锁状态。"""
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    return parse_lock(content)


def clear_lock(path: Path) -> bool:
    """清除对齐锁。"""
    if not path.exists():
        return False
    
    content = path.read_text(encoding="utf-8")
    new_content = remove_lock_lines(content).rstrip() + "\n"
    
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new_content, encoding="utf-8")
    tmp.replace(path)
    
    return True


def verify_lock(path: Path, max_age_days: int = 30) -> tuple[bool, str]:
    """
    验证对齐锁是否有效。
    
    返回: (is_valid, message)
    """
    lock = read_lock(path)
    
    if lock is None:
        return False, "文件不存在"
    
    if not lock.is_locked:
        return False, "未发现对齐锁"
    
    if lock.is_expired(max_age_days):
        return False, f"对齐锁已过期（超过 {max_age_days} 天）"
    
    # 可选：检查内容是否变更
    if lock.content_hash and path.exists():
        current_content = path.read_text(encoding="utf-8")
        current_hash = compute_content_hash(current_content)
        if current_hash != lock.content_hash:
            return False, f"内容已变更（hash: {lock.content_hash} -> {current_hash}）"
    
    return True, "对齐锁有效"


# ============ CLI ============

def get_paths(root: Path, target: str) -> list[Path]:
    """获取目标文件路径列表。"""
    prd_path = root / "docs" / "PRD.md"
    state_path = root / "docs" / "STATE.md"
    
    if target == "prd":
        return [prd_path]
    elif target == "state":
        return [state_path]
    elif target == "both":
        return [prd_path, state_path]
    else:
        return []


def cmd_set(args) -> int:
    """写入对齐锁。"""
    root = args.root.resolve()
    paths = get_paths(root, args.target)
    
    lock = AlignmentLock(
        is_locked=True,
        done_at=args.date or date.today().isoformat(),
        next_action=args.action or "continue_implementation",
        scope=args.scope,
    )
    
    updated = False
    for path in paths:
        if write_lock(path, lock, args.create):
            print(f"✅ 已写入对齐锁: {path}")
            updated = True
        else:
            print(f"⚠️ 文件不存在（使用 --create 创建）: {path}")
    
    return 0 if updated else 1


def cmd_check(args) -> int:
    """检查对齐锁状态。"""
    root = args.root.resolve()
    paths = get_paths(root, args.target)
    
    for path in paths:
        print(f"\n📄 {path}")
        lock = read_lock(path)
        if lock:
            print(str(lock))
        else:
            print("  (文件不存在)")
    
    return 0


def cmd_verify(args) -> int:
    """验证对齐锁有效性。"""
    root = args.root.resolve()
    paths = get_paths(root, args.target)
    
    all_valid = True
    for path in paths:
        is_valid, message = verify_lock(path, args.max_age)
        status = "✅" if is_valid else "❌"
        print(f"{status} {path}: {message}")
        if not is_valid:
            all_valid = False
    
    return 0 if all_valid else 1


def cmd_clear(args) -> int:
    """清除对齐锁。"""
    root = args.root.resolve()
    paths = get_paths(root, args.target)
    
    cleared = False
    for path in paths:
        if clear_lock(path):
            print(f"🗑️ 已清除对齐锁: {path}")
            cleared = True
        else:
            print(f"⚠️ 文件不存在: {path}")
    
    return 0 if cleared else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Alignment Lock Manager - 对齐锁管理器"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="项目根目录（默认：当前目录）",
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # set 命令
    set_parser = subparsers.add_parser("set", help="写入对齐锁")
    set_parser.add_argument("--target", choices=["prd", "state", "both"], default="prd")
    set_parser.add_argument("--date", help="对齐完成日期（YYYY-MM-DD）")
    set_parser.add_argument("--action", help="下一步动作")
    set_parser.add_argument("--scope", help="对齐范围摘要")
    set_parser.add_argument("--create", action="store_true", help="如果文件不存在则创建")
    set_parser.set_defaults(func=cmd_set)
    
    # check 命令
    check_parser = subparsers.add_parser("check", help="检查对齐锁状态")
    check_parser.add_argument("--target", choices=["prd", "state", "both"], default="prd")
    check_parser.set_defaults(func=cmd_check)
    
    # verify 命令
    verify_parser = subparsers.add_parser("verify", help="验证对齐锁有效性")
    verify_parser.add_argument("--target", choices=["prd", "state", "both"], default="prd")
    verify_parser.add_argument("--max-age", type=int, default=30, help="最大有效天数（默认30天）")
    verify_parser.set_defaults(func=cmd_verify)
    
    # clear 命令
    clear_parser = subparsers.add_parser("clear", help="清除对齐锁")
    clear_parser.add_argument("--target", choices=["prd", "state", "both"], default="prd")
    clear_parser.set_defaults(func=cmd_clear)
    
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
