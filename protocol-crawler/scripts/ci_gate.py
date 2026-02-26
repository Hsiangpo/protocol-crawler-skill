#!/usr/bin/env python3
"""
CI 门禁自动检查脚本

对应 SKILL.md 步骤 6 的检查项。
用法：python ci_gate.py <项目根目录>
返回：0 = 全部通过，1 = 存在不通过项
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

# ===== 配置 =====

MAX_FILE_LINES = 1000
MAX_FUNC_LINES = 200
BANNED_SUFFIXES = ["_v2", "_v3", "_v4", "_v5", "_new", "_old", "_bak", "_backup", "_copy"]
CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs"}
TEXT_LIKE_EXTENSIONS = {
    ".md", ".txt", ".rst", ".json", ".jsonl", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".conf", ".env", ".csv", ".tsv",
    ".xml", ".html", ".css", ".sql", ".sh", ".bat", ".ps1"
}
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico", ".svg",
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".zip", ".rar", ".7z", ".gz", ".tar", ".exe", ".dll", ".so",
    ".dylib", ".class", ".jar", ".pyc", ".pyd", ".bin"
}
IGNORE_DIRS = {
    "__pycache__", "node_modules", ".git", ".venv", "venv",
    "env", ".env", "dist", "build", ".next", ".cache",
    ".idea", ".vscode", "debug", "tmp"
}
TEMP_FILE_PATTERNS = {
    "test_output", "debug_response", "temp", "tmp_", "test_",
    "scratch", "playground", "draft"
}
TEMP_EXTENSIONS = {".tmp", ".bak", ".swp", ".log"}


def check_file_lines(filepath: Path) -> List[str]:
    """检查 1: 单文件行数 ≤ MAX_FILE_LINES"""
    errors = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            line_count = sum(1 for _ in f)
        if line_count > MAX_FILE_LINES:
            errors.append(
                f"  ❌ 文件超限：{line_count} 行（上限 {MAX_FILE_LINES}）→ 需拆分为多个模块"
            )
    except Exception as e:
        errors.append(f"  ⚠️ 无法读取：{e}")
    return errors


def check_function_lines(filepath: Path) -> List[str]:
    """检查 2: 单函数行数 ≤ MAX_FUNC_LINES（仅 Python）"""
    errors = []
    if filepath.suffix != ".py":
        return errors

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return errors

    func_name = None
    func_start = 0
    func_indent = 0

    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if not stripped:
            continue

        # 检测函数定义
        lstripped = stripped.lstrip()
        indent = len(stripped) - len(lstripped)

        if lstripped.startswith("def ") or lstripped.startswith("async def "):
            # 如果已有函数在追踪中，先结束它
            if func_name is not None:
                func_len = i - func_start
                if func_len > MAX_FUNC_LINES:
                    errors.append(
                        f"  ❌ 函数超限：{func_name}() 第{func_start + 1}-{i}行"
                        f"（{func_len}行，上限 {MAX_FUNC_LINES}）→ 需拆分"
                    )

            # 提取函数名
            name_part = lstripped.split("(")[0]
            func_name = name_part.replace("def ", "").replace("async ", "").strip()
            func_start = i
            func_indent = indent

        elif func_name is not None and indent <= func_indent and not lstripped.startswith("#"):
            # 函数结束（缩进回退到函数级别或更低）
            if not lstripped.startswith("@"):  # 装饰器不算结束
                func_len = i - func_start
                if func_len > MAX_FUNC_LINES:
                    errors.append(
                        f"  ❌ 函数超限：{func_name}() 第{func_start + 1}-{i}行"
                        f"（{func_len}行，上限 {MAX_FUNC_LINES}）→ 需拆分"
                    )
                func_name = None

    # 处理文件末尾的函数
    if func_name is not None:
        func_len = len(lines) - func_start
        if func_len > MAX_FUNC_LINES:
            errors.append(
                f"  ❌ 函数超限：{func_name}() 第{func_start + 1}-{len(lines)}行"
                f"（{func_len}行，上限 {MAX_FUNC_LINES}）→ 需拆分"
            )

    return errors


def check_filename(filepath: Path) -> List[str]:
    """检查 3: 禁止版本号后缀"""
    errors = []
    stem = filepath.stem.lower()
    for suffix in BANNED_SUFFIXES:
        if stem.endswith(suffix):
            errors.append(
                f"  ❌ 文件名含禁用后缀 '{suffix}'：{filepath.name} → 重命名，只保留一份"
            )
            break
    return errors


def check_encoding(filepath: Path) -> List[str]:
    """检查 6: 文件编码 UTF-8"""
    errors = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            f.read(4096)  # 只读前 4KB 检测
    except UnicodeDecodeError:
        errors.append(f"  ❌ 文件编码非 UTF-8 → 需转换为 UTF-8")
    except Exception:
        pass
    return errors


def check_gitignore(project_root: Path) -> List[str]:
    """检查 7: debug/、tmp/、.env 均已添加到 .gitignore"""
    errors = []
    gitignore = project_root / ".gitignore"

    if not gitignore.exists():
        needs_gitignore = (
            (project_root / "debug").exists() or
            (project_root / "tmp").exists() or
            (project_root / ".env").exists()
        )
        if needs_gitignore:
            errors.append("❌ 未创建 .gitignore → 需创建并添加 debug/、tmp/、.env 规则")
        return errors

    try:
        content = gitignore.read_text(encoding="utf-8", errors="replace")
        lines = [l.strip() for l in content.splitlines() if not l.strip().startswith("#")]

        # 检查 debug/
        if (project_root / "debug").exists():
            has_debug = any(l in ("debug/", "debug", "/debug", "/debug/") for l in lines)
            if not has_debug:
                errors.append("❌ debug/ 目录未添加到 .gitignore")

        # 检查 tmp/
        if (project_root / "tmp").exists():
            has_tmp = any(l in ("tmp/", "tmp", "/tmp", "/tmp/") for l in lines)
            if not has_tmp:
                errors.append("❌ tmp/ 目录未添加到 .gitignore")

        # 检查 .env
        if (project_root / ".env").exists():
            has_env = any(l in (".env", "/.env") for l in lines)
            if not has_env:
                errors.append("❌ .env 文件未添加到 .gitignore → 凭据泄露风险！")

    except Exception as e:
        errors.append(f"⚠️ 无法读取 .gitignore：{e}")

    return errors


def check_env_file(project_root: Path) -> List[str]:
    """检查 8: .env 凭据管理规范"""
    errors = []

    # 检查是否有 .env.example
    has_env = (project_root / ".env").exists()
    has_example = (project_root / ".env.example").exists()

    if has_env and not has_example:
        errors.append("⚠️ 有 .env 但缺少 .env.example → 建议创建 .env.example 列出所有环境变量")

    return errors


def check_root_temp_files(project_root: Path) -> List[str]:
    """检查: 根目录是否有遗留的临时文件"""
    errors = []
    temp_files_found = []

    for item in project_root.iterdir():
        if not item.is_file():
            continue

        stem_lower = item.stem.lower()
        suffix_lower = item.suffix.lower()

        # 检查临时文件名模式
        is_temp_name = any(stem_lower.startswith(p) for p in TEMP_FILE_PATTERNS)
        is_temp_ext = suffix_lower in TEMP_EXTENSIONS

        if is_temp_name or is_temp_ext:
            temp_files_found.append(item.name)

    if temp_files_found:
        files_str = ", ".join(temp_files_found[:5])
        if len(temp_files_found) > 5:
            files_str += f" 等{len(temp_files_found)}个"
        errors.append(
            f"❌ 根目录发现疑似临时文件：{files_str} → 删除或移入 tmp/ 目录"
        )

    return errors


def check_directory_structure(project_root: Path) -> List[str]:
    """检查 8: 基本目录结构（仅检查有无 src/ 或主代码目录）"""
    errors = []
    has_src = (project_root / "src").exists()
    has_docs = (project_root / "docs").exists()

    # 只在项目看起来已经在开发中时检查
    py_files = list(project_root.glob("*.py"))
    if len(py_files) > 3 and not has_src:
        errors.append(
            f"⚠️ 项目根目录有 {len(py_files)} 个 .py 文件但未使用 src/ 目录 → 建议按规范整理"
        )

    return errors


def is_likely_text_file(filepath: Path) -> bool:
    """判断文件是否可能是文本文件。"""
    suffix = filepath.suffix.lower()
    if suffix in BINARY_EXTENSIONS:
        return False

    # 对常见文本后缀快速放行，减少二进制探测开销
    if suffix in CODE_EXTENSIONS or suffix in TEXT_LIKE_EXTENSIONS:
        return True

    # 无后缀或未知后缀：按内容做轻量探测
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(4096)
    except OSError:
        return False

    if b"\x00" in chunk:
        return False
    return True


def should_check_file(filepath: Path, all_text_files: bool) -> bool:
    """判断当前文件是否应纳入检查范围。"""
    suffix = filepath.suffix.lower()
    if all_text_files:
        return is_likely_text_file(filepath)
    return suffix in CODE_EXTENSIONS


def scan_project(project_root: Path, all_text_files: bool = False) -> Tuple[int, int, int, List[str]]:
    """扫描项目，返回 (总文件数, 通过数, 失败数, 项目级错误列表)。"""
    total_files = 0
    pass_count = 0
    fail_count = 0
    all_errors = []

    # 项目级检查
    gitignore_errors = check_gitignore(project_root)
    if gitignore_errors:
        all_errors.extend(gitignore_errors)
        fail_count += 1
    else:
        pass_count += 1

    env_errors = check_env_file(project_root)
    if env_errors:
        all_errors.extend(env_errors)

    temp_errors = check_root_temp_files(project_root)
    if temp_errors:
        all_errors.extend(temp_errors)
        fail_count += 1
    else:
        pass_count += 1

    structure_errors = check_directory_structure(project_root)
    if structure_errors:
        all_errors.extend(structure_errors)

    # 文件级检查
    has_oversize = False
    for root, dirs, files in os.walk(project_root):
        # 过滤忽略目录
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

        for filename in files:
            filepath = Path(root) / filename

            if not should_check_file(filepath, all_text_files):
                continue

            total_files += 1
            rel_path = filepath.relative_to(project_root)

            file_errors = []
            file_errors.extend(check_file_lines(filepath))
            file_errors.extend(check_filename(filepath))
            file_errors.extend(check_encoding(filepath))
            if filepath.suffix.lower() == ".py":
                file_errors.extend(check_function_lines(filepath))

            if file_errors:
                fail_count += 1
                print(f"\n📄 {rel_path}")
                for err in file_errors:
                    print(err)
                    if "文件超限" in err or "函数超限" in err:
                        has_oversize = True
            else:
                pass_count += 1

    # 超限反作弊警告
    if has_oversize:
        print("\n" + "━" * 60)
        print("⛔ 反作弊警告：修复超限时只能通过合理拆分来解决！")
        print("   ❌ 严禁删除错误处理、重试、数据校验、日志等健壮性代码")
        print("   ❌ 严禁合并多个函数为一个巨型函数")
        print("   ❌ 严禁移除注释和文档字符串")
        print("   ✅ 正确做法：按职责拆分为多个模块/子函数")
        print("━" * 60)

    return total_files, pass_count, fail_count, all_errors


def main():
    parser = argparse.ArgumentParser(
        description="CI 门禁检查 — 对应 SKILL.md 步骤 6",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
检查项：
  1. 单文件行数 ≤ 1000 行
  2. 单函数行数 ≤ 200 行（仅 Python）
  3. 文件名禁止版本号后缀（_v2, _new, _old 等）
  4. 废弃代码检测（需人工判断）
  5. 注释语言检查（需人工判断）
  6. 文件编码 UTF-8
  7. debug/、tmp/、.env 已加入 .gitignore
  8. .env 凭据管理（有 .env.example）
  9. 根目录无临时文件
  10. 目录结构基本规范

默认仅检查代码文件（.py/.js/.ts/...）。
可加 --all-text-files 扩展到全部文本文件（.md/.json/.yaml/.toml/...）。
        """
    )
    parser.add_argument(
        "project_dir",
        type=str,
        help="项目根目录路径"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示所有文件的检查结果（包括通过的）"
    )
    parser.add_argument(
        "--all-text-files",
        action="store_true",
        help="检查全部文本文件（默认仅检查代码文件）"
    )

    args = parser.parse_args()
    project_root = Path(args.project_dir).resolve()

    if not project_root.exists():
        print(f"❌ 目录不存在：{project_root}")
        sys.exit(1)

    print(f"🔍 CI 门禁检查：{project_root}")
    print("=" * 60)
    print(f"📌 检查范围：{'全部文本文件' if args.all_text_files else '代码文件（默认）'}")

    total_files, pass_count, fail_count, project_errors = scan_project(
        project_root, all_text_files=args.all_text_files
    )

    # 项目级错误
    if project_errors:
        print("\n📁 项目级检查")
        for err in project_errors:
            print(f"  {err}")

    # 汇总
    print("\n" + "=" * 60)
    print(f"📊 检查完成")
    print(f"   扫描文件：{total_files}")
    print(f"   ✅ 通过：{pass_count}")
    print(f"   ❌ 失败：{fail_count}")

    # 提醒人工检查项
    print(f"\n⚠️ 以下检查项需要人工确认：")
    print(f"   4. 废弃代码：同功能是否只保留一份？")
    print(f"   5. 注释语言：是否使用中文、无人称？")

    if fail_count > 0:
        print(f"\n❌ 门禁未通过 — 请修复上述问题后重新运行")
        sys.exit(1)
    else:
        print(f"\n✅ 自动检查项全部通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
