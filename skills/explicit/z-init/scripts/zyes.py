#!/usr/bin/env python3
"""Zyes 协议工具。支持只读检查和受控任务状态转换。"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any


TASK_STATUSES = (
    "planning",
    "ready",
    "in-progress",
    "verifying",
    "completed",
    "cancelled",
    "superseded",
)
TICKET_STATUSES = ("ready", "in-progress", "completed")
TERMINAL_TASK_STATUSES = {"completed", "cancelled", "superseded"}
STATUS_ORDER = {
    "in-progress": 0,
    "ready": 1,
    "planning": 2,
    "verifying": 3,
    "completed": 4,
    "cancelled": 5,
    "superseded": 6,
}
ENTRY_STATUSES = {
    "z-brainstorm": {"planning"},
    "z-implement": {"ready", "in-progress", "verifying", "completed"},
    "z-finish-task": set(TASK_STATUSES),
    "z-list-tasks": set(TASK_STATUSES),
}
ACTION_INSTRUCTIONS = {
    "resolve-errors": (
        ("Resolve every listed blocking error before continuing.",),
        ("Do not mutate task state while the context is invalid.",),
    ),
    "select-task": (
        ("Select exactly one listed task and rerun context with --task.",),
        ("Do not infer the user's task when multiple candidates remain.",),
    ),
    "create-planning-task": (
        (
            "Create or select one planning task before writing product code.",
            "Investigate repository evidence before asking user questions.",
            "Use z-grilling for every substantive user decision.",
        ),
        (
            "Do not modify product code or start implementation.",
            "Do not choose user-owned product decisions.",
        ),
    ),
    "refine-plan": (
        (
            "Investigate repository evidence and update the current planning revision.",
            "Use z-grilling for every unresolved substantive user decision.",
            "Keep acceptance, scope and risks explicit in the planning artifacts.",
        ),
        ("Do not modify product code or start implementation.",),
    ),
    "approve-or-revise-plan": (
        (
            "Review the latest spec and ticket plan against confirmed decisions.",
            "Present the final planning summary and wait for fresh implementation approval.",
        ),
        ("Do not start implementation in the planning approval turn.",),
    ),
    "start-ticket": (
        (
            "Choose and start exactly one frontier ticket with the controlled command.",
            "Rerun this context after the state transition.",
        ),
        ("Do not implement before the current ticket pointer is valid.",),
    ),
    "implement-ticket": (
        (
            "Implement the current ticket only.",
            "Record actual Result and Verification evidence before completion.",
            "Review the actual diff on both Standards and Spec axes.",
        ),
        (
            "Do not start another ticket.",
            "Do not archive the task or perform Git delivery.",
        ),
    ),
    "verify-task": (
        (
            "Verify the completed tickets on independent Standards and Spec axes.",
            "Write result evidence or create a controlled rework ticket for blocking findings.",
        ),
        ("Do not fix product code during the verification action.",),
    ),
    "reverify-or-finish": (
        ("Reverify only when requested; otherwise continue with z-finish-task.",),
        ("Do not archive without explicit user authorization.",),
    ),
    "cancel-or-supersede-task": (
        (
            "Require an explicit cancel or supersede decision and use the controlled command.",
        ),
        ("Do not interpret an ordinary finish request as cancellation.",),
    ),
    "archive-task": (
        ("Archive the terminal task only after explicit user authorization.",),
        ("Do not perform Git delivery or start another task.",),
    ),
    "list-tasks": (
        ("Report task status, ticket progress and the next valid action.",),
        ("Do not mutate task state.",),
    ),
    "use-entry-for-status": (
        ("Use the workflow entry that owns the selected task status.",),
        ("Do not force an incompatible state transition.",),
    ),
    "no-matching-task": (
        ("Report that no task matches this entry and suggest the valid next entry.",),
        ("Do not create or mutate a task implicitly.",),
    ),
}
SPEC_REQUIRED_HEADINGS = (
    "Problem Statement",
    "Solution",
    "User Stories",
    "Acceptance Criteria",
    "Implementation Decisions",
    "Testing Decisions",
    "Risks and Deferred Items",
    "Out of Scope",
)
SPEC_V2_REQUIRED_HEADINGS = tuple(
    "Decisions" if heading == "Implementation Decisions" else heading
    for heading in SPEC_REQUIRED_HEADINGS
)
SPEC_PLACEHOLDERS = (
    "<Task title>",
    "<actor>",
    "<feature>",
    "<benefit>",
    "<要解决的问题>",
    "<解决方案>",
    "<用户故事>",
    "<可观察的验收条件>",
    "<已确认的实现决定>",
    "<测试 seam 与策略>",
)
TICKET_PLACEHOLDERS = (
    "<这个切片交付的端到端行为>",
    "<可观察的验收条件>",
    "<完成后记录实际实现；开始前保持为空>",
    "<完成后记录实际执行的检查及结果；未执行项写明原因>",
)
RESULT_PLACEHOLDERS = (
    "<对照 spec 和 tickets 总结实际交付>",
    "<命令、手工检查及结果；未执行项写明原因>",
    "<规格符合性和工程质量发现；没有则写 none>",
    "<未完成或后续事项；没有则写 none>",
)

PROJECT_BLOCK_RE = re.compile(r"<!-- zyes:start -->(.*?)<!-- zyes:end -->", re.DOTALL)
HOME_BLOCK_RE = re.compile(r"<!-- zyes-home:start -->(.*?)<!-- zyes-home:end -->", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
TASK_STATUS_RE = re.compile(r"^Status:\s*`([^`]+)`\s*$", re.MULTILINE)
CREATED_RE = re.compile(r"^Created:\s*`([^`]+)`\s*$", re.MULTILINE)
PLANNING_REVISION_RE = re.compile(r"^Planning revision:\s*`(\d+)`\s*$", re.MULTILINE)
BLOCKED_RE = re.compile(r"^Blocked by:\s*`([^`]+)`\s*$", re.MULTILINE)
CANCEL_REASON_RE = re.compile(r"^Reason:\s*(.+?)\s*$", re.MULTILINE)
SUPERSEDED_BY_RE = re.compile(r"^Superseded by:\s*`([^`]+)`\s*$", re.MULTILINE)
FORMAT_VERSION_RE = re.compile(r"^Format version:\s*`(\d+)`\s*$", re.MULTILINE)
SPEC_REFS_RE = re.compile(r"^Spec refs:\s*(.+?)\s*$", re.MULTILINE)
STABLE_REF_RE = re.compile(r"`((?:D|AC)-\d{3})`")
TASK_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
TICKET_FILE_RE = re.compile(r"^(\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ZyesError(Exception):
    pass


def ensure_directory(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ZyesError(f"无法创建目录 {path}: {exc}") from exc


def atomic_write_bytes(path: Path, content: bytes, mode: int | None = None) -> None:
    if path.is_symlink():
        raise ZyesError(f"拒绝覆盖符号链接: {path}")
    ensure_directory(path.parent)
    fd: int | None = None
    temp_name: str | None = None
    try:
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        os.fchmod(fd, mode if mode is not None else 0o644)
        with os.fdopen(fd, "wb") as handle:
            fd = None
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        temp_name = None
    except OSError as exc:
        raise ZyesError(f"无法原子写入 {path}: {exc}") from exc
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if temp_name is not None:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass


def file_snapshot(path: Path) -> tuple[bytes | None, int | None]:
    if not path.exists() and not path.is_symlink():
        return None, None
    if path.is_symlink():
        raise ZyesError(f"拒绝修改符号链接: {path}")
    try:
        return path.read_bytes(), path.stat().st_mode & 0o777
    except OSError as exc:
        raise ZyesError(f"无法读取待修改文件 {path}: {exc}") from exc


class StateTransaction:
    """为一次状态迁移保留回滚信息，并对单文件使用原子替换。"""

    def __init__(self) -> None:
        self.actions: list[tuple[Any, ...]] = []
        self.recorded_files: set[Path] = set()
        self.recorded_directories: set[Path] = set()
        self.committed = False

    def __enter__(self) -> "StateTransaction":
        return self

    def __exit__(self, exc_type: Any, exc: BaseException | None, traceback: Any) -> bool:
        if self.committed:
            return False
        try:
            self.rollback()
        except ZyesError as rollback_error:
            if exc is not None:
                raise ZyesError(f"状态迁移失败且回滚失败：{exc}；{rollback_error}") from exc
            raise
        return False

    def record_file(self, path: Path) -> None:
        resolved = path.resolve(strict=False)
        if resolved in self.recorded_files:
            return
        content, mode = file_snapshot(path)
        self.recorded_files.add(resolved)
        self.actions.append(("file", path, content, mode))

    def record_parent_directories(self, path: Path) -> None:
        missing: list[Path] = []
        current = path
        while not current.exists():
            missing.append(current)
            if current == current.parent:
                break
            current = current.parent
        new_items = [item for item in reversed(missing) if item not in self.recorded_directories]
        if new_items:
            self.recorded_directories.update(new_items)
            self.actions.append(("directories", tuple(new_items)))

    def write_text(self, path: Path, content: str) -> None:
        self.record_parent_directories(path.parent)
        self.record_file(path)
        mode = None
        if path.exists() and not path.is_symlink():
            try:
                mode = path.stat().st_mode & 0o777
            except OSError as exc:
                raise ZyesError(f"无法读取文件权限 {path}: {exc}") from exc
        atomic_write_bytes(path, content.encode("utf-8"), mode)

    def unlink(self, path: Path) -> None:
        self.record_file(path)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise ZyesError(f"无法删除 {path}: {exc}") from exc

    def move(self, source: Path, destination: Path) -> None:
        if destination.exists() or destination.is_symlink():
            raise ZyesError(f"移动目标已存在: {destination}")
        self.record_parent_directories(destination.parent)
        ensure_directory(destination.parent)
        try:
            shutil.move(str(source), str(destination))
        except OSError as exc:
            raise ZyesError(f"无法移动 {source} 到 {destination}: {exc}") from exc
        self.actions.append(("move", source, destination))

    def commit(self) -> None:
        self.committed = True
        self.actions.clear()
        self.recorded_files.clear()
        self.recorded_directories.clear()

    def rollback(self) -> None:
        errors: list[str] = []
        for action in reversed(self.actions):
            try:
                if action[0] == "file":
                    _, path, content, mode = action
                    if content is None:
                        path.unlink(missing_ok=True)
                    else:
                        atomic_write_bytes(path, content, mode)
                elif action[0] == "move":
                    _, source, destination = action
                    if destination.exists() or destination.is_symlink():
                        ensure_directory(source.parent)
                        shutil.move(str(destination), str(source))
                else:
                    _, directories = action
                    for directory in reversed(directories):
                        try:
                            directory.rmdir()
                        except FileNotFoundError:
                            pass
            except (OSError, ZyesError) as exc:
                errors.append(str(exc))
        self.actions.clear()
        self.recorded_files.clear()
        self.recorded_directories.clear()
        if errors:
            raise ZyesError("回滚失败：" + "；".join(errors))


@contextlib.contextmanager
def project_write_lock(project_root: Path):
    """使用操作系统文件锁串行化同一 Zyes 项目的写命令。"""

    if not project_root.is_dir():
        raise ZyesError(f"Zyes 项目根目录不存在或不可访问: {project_root}")
    runtime_dir = project_root / "runtime"
    if runtime_dir.exists() and (not runtime_dir.is_dir() or not is_within(runtime_dir, project_root)):
        raise ZyesError("runtime 必须是 Zyes 项目根目录内的目录")
    ensure_directory(runtime_dir)
    lock_path = runtime_dir / ".write.lock"
    if lock_path.is_symlink():
        raise ZyesError(f"状态写锁不能是符号链接: {lock_path}")
    try:
        handle = lock_path.open("a+b")
    except OSError as exc:
        raise ZyesError(f"无法打开状态写锁 {lock_path}: {exc}") from exc

    locked = False
    try:
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except OSError as exc:
            raise ZyesError("另一个 Zyes 写命令正在运行，请等待后重试") from exc
        yield
    finally:
        if locked:
            try:
                if os.name == "nt":
                    import msvcrt

                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        handle.close()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise ZyesError(f"{path} 不是有效的 UTF-8 文本: {exc}") from exc
    except OSError as exc:
        raise ZyesError(f"无法读取 {path}: {exc}") from exc


def mask_fenced_code(text: str) -> str:
    """遮蔽 fenced code 内容但保留字符位置与换行，供 Markdown 结构解析使用。"""

    output: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        newline = line[len(content) :]
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", content)
        if fence_character is None and opening:
            marker = opening.group(1)
            fence_character = marker[0]
            fence_length = len(marker)
            output.append(" " * len(content) + newline)
            continue
        if fence_character is not None:
            closing = re.match(
                rf"^ {{0,3}}{re.escape(fence_character)}{{{fence_length},}}\s*$",
                content,
            )
            output.append(" " * len(content) + newline)
            if closing:
                fence_character = None
                fence_length = 0
            continue
        output.append(line)
    return "".join(output)


def single_match(pattern: re.Pattern[str], text: str, label: str, errors: list[str]) -> str | None:
    matches = pattern.findall(text)
    if len(matches) != 1:
        errors.append(f"{label} 必须且只能出现一次，实际为 {len(matches)} 次")
        return None
    value = matches[0]
    return value.strip() if isinstance(value, str) else value


def is_within(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((str(path.resolve()), str(root.resolve()))) == str(root.resolve())
    except (OSError, ValueError):
        return False


def contained_relative_path(
    path: Path,
    root: Path,
    label: str,
    errors: list[str],
) -> str | None:
    if not is_within(path, root):
        errors.append(f"{label} 通过符号链接解析到 Zyes 项目根目录之外")
        return None
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError) as exc:
        errors.append(f"无法计算 {label} 的项目内相对路径: {exc}")
        return None


def posix_relative_path(value: str, label: str, errors: list[str]) -> PurePosixPath | None:
    if "\\" in value:
        errors.append(f"{label} 必须使用 POSIX 相对路径")
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        errors.append(f"{label} 必须是 Zyes 项目根目录内的规范相对路径")
        return None
    if path.as_posix() != value:
        errors.append(f"{label} 必须是规范相对路径: {path.as_posix()}")
        return None
    return path


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise ZyesError(f"无法从 {start} 向上找到 Git 仓库根目录")


def project_instruction_file(repo_root: Path) -> Path:
    agents = repo_root / "AGENTS.md"
    claude = repo_root / "CLAUDE.md"
    if agents.is_file():
        return agents
    if claude.is_file():
        return claude
    raise ZyesError("仓库根目录不存在 AGENTS.md 或 CLAUDE.md")


def one_controlled_block(path: Path, pattern: re.Pattern[str], name: str) -> str:
    blocks = pattern.findall(read_text(path))
    if len(blocks) != 1:
        raise ZyesError(f"{path} 中必须且只能存在一个 {name} 受控块，实际为 {len(blocks)} 个")
    return blocks[0]


def block_value(block: str, key: str) -> str:
    matches = re.findall(rf"^- {re.escape(key)}:\s*`([^`]+)`\s*$", block, re.MULTILINE)
    if len(matches) != 1:
        raise ZyesError(f"Zyes workflow 受控块中的 {key} 必须且只能出现一次，实际为 {len(matches)} 次")
    return matches[0].strip()


def home_from_instructions(path: Path) -> Path:
    block = one_controlled_block(path.resolve(), HOME_BLOCK_RE, "Zyes home")
    match = re.search(r"Zyes 外置工作流根目录：\s*`([^`]+)`", block)
    if not match:
        raise ZyesError(f"{path} 的 Zyes home 受控块缺少绝对路径")
    home = Path(match.group(1))
    if not home.is_absolute():
        raise ZyesError(f"{path} 中的 Zyes home 必须是绝对路径")
    return home.resolve()


def resolve_project_root(
    repo: Path,
    zyes_home: Path | None = None,
    global_instructions: Path | None = None,
) -> dict[str, str]:
    repo_root = find_repo_root(repo)
    instruction_file = project_instruction_file(repo_root)
    block = one_controlled_block(instruction_file, PROJECT_BLOCK_RE, "Zyes workflow")
    mode = block_value(block, "Mode")
    if mode == "shared":
        root_value = block_value(block, "Root")
        if root_value != ".zyes":
            raise ZyesError("shared 模式的 Root 必须为 `.zyes`")
        project_root = (repo_root / ".zyes").resolve()
        project_name = ""
    elif mode == "external":
        project_name = block_value(block, "Project")
        if not SLUG_RE.fullmatch(project_name):
            raise ZyesError("external 模式的 Project 必须是小写 kebab-case")
        if zyes_home and global_instructions:
            raise ZyesError("--zyes-home 与 --global-instructions 只能使用一个")
        if global_instructions:
            resolved_home = home_from_instructions(global_instructions)
        elif zyes_home:
            if not zyes_home.is_absolute():
                raise ZyesError("--zyes-home 必须是绝对路径")
            resolved_home = zyes_home.resolve()
        else:
            raise ZyesError("external 模式需要 --zyes-home 或 --global-instructions")
        project_root = (resolved_home / project_name).resolve()
    else:
        raise ZyesError("Zyes workflow 受控块中的 Mode 必须是 `shared` 或 `external`")

    if not project_root.is_dir():
        raise ZyesError(f"Zyes 项目根目录不存在或不可访问: {project_root}")
    return {
        "mode": mode,
        "repo_root": str(repo_root),
        "instruction_file": str(instruction_file),
        "project": project_name,
        "project_root": str(project_root),
    }


def parse_current(project_root: Path) -> dict[str, Any]:
    current_path = project_root / "runtime/current.yaml"
    result: dict[str, Any] = {"path": "runtime/current.yaml", "task": None, "ticket": None, "errors": []}
    if not current_path.exists():
        if current_path.is_symlink():
            result["errors"].append("current.yaml 是失效的符号链接")
        result["path"] = None
        return result
    if not is_within(current_path, project_root):
        result["errors"].append("runtime/current.yaml 通过符号链接解析到 Zyes 项目根目录之外")
        return result
    text = read_text(current_path)
    task_matches = re.findall(r"^task:\s*(.+?)\s*$", text, re.MULTILINE)
    ticket_matches = re.findall(r"^ticket:\s*(.+?)\s*$", text, re.MULTILINE)
    if len(task_matches) != 1:
        result["errors"].append(f"current.yaml 的 task 必须且只能出现一次，实际为 {len(task_matches)} 次")
    if len(ticket_matches) != 1:
        result["errors"].append(f"current.yaml 的 ticket 必须且只能出现一次，实际为 {len(ticket_matches)} 次")
    if len(task_matches) == 1:
        value = task_matches[0].strip()
        parsed = posix_relative_path(value, "current task", result["errors"])
        if parsed:
            result["task"] = parsed.as_posix()
    if len(ticket_matches) == 1:
        value = ticket_matches[0].strip()
        if value != "null":
            parsed = posix_relative_path(value, "current ticket", result["errors"])
            if parsed:
                result["ticket"] = parsed.as_posix()
    if result["task"]:
        task_path = PurePosixPath(result["task"])
        if len(task_path.parts) != 2 or task_path.parts[0] != "tasks" or not TASK_DIR_RE.fullmatch(task_path.name):
            result["errors"].append("current task 必须指向 `tasks/YYYY-MM-DD-<slug>`")
    if result["ticket"]:
        ticket_path = PurePosixPath(result["ticket"])
        if (
            len(ticket_path.parts) != 4
            or ticket_path.parts[0] != "tasks"
            or ticket_path.parts[2] != "tickets"
            or not TASK_DIR_RE.fullmatch(ticket_path.parts[1])
            or not TICKET_FILE_RE.fullmatch(ticket_path.name)
        ):
            result["errors"].append("current ticket 必须指向 `tasks/<task>/tickets/<NN>-<slug>.md`")
        elif result["task"] and ticket_path.parent.parent != PurePosixPath(result["task"]):
            result["errors"].append("current ticket 不属于 current task")
    for key in ("task", "ticket"):
        if result[key]:
            target = project_root.joinpath(*PurePosixPath(result[key]).parts)
            if not is_within(target, project_root):
                result["errors"].append(f"current {key} 解析到 Zyes 项目根目录之外")
            elif not target.exists():
                result["errors"].append(f"current {key} 指向不存在的路径: {result[key]}")
    return result


def section_body(text: str, heading: str) -> str | None:
    structure = mask_fenced_code(text)
    heading_match = re.search(rf"^## {re.escape(heading)}\s*$", structure, re.MULTILINE)
    if not heading_match:
        return None
    body_start = structure.find("\n", heading_match.end())
    if body_start == -1:
        return ""
    body_start += 1
    next_heading = re.search(r"^##\s+", structure[body_start:], re.MULTILINE)
    body_end = body_start + next_heading.start() if next_heading else len(text)
    return text[body_start:body_end].strip()


def meaningful_section(body: str | None) -> bool:
    if not body:
        return False
    return not bool(re.fullmatch(r"<[^>]+>", body.strip(), re.DOTALL))


def contains_placeholder(text: str, placeholders: tuple[str, ...]) -> bool:
    return any(placeholder in text for placeholder in placeholders)


def stable_spec_items(
    body: str | None,
    prefix: str,
    strict: bool,
    errors: list[str],
) -> dict[str, str]:
    if body is None:
        return {}
    matches = re.findall(
        rf"^- ({re.escape(prefix)}-\d{{3}}):\s*(.+?)\s*$",
        mask_fenced_code(body),
        re.MULTILINE,
    )
    items: dict[str, str] = {}
    for item_id, value in matches:
        if item_id in items:
            if strict:
                errors.append(f"spec.md 稳定 ID 重复: {item_id}")
        elif not value.strip() or value.strip().startswith("<"):
            if strict:
                errors.append(f"spec.md {item_id} 缺少有效内容")
        else:
            items[item_id] = value.strip()
    if strict and meaningful_section(body) and body.strip() != "none" and not matches:
        errors.append(f"spec.md 中的 {prefix} 条目必须使用 `{prefix}-NNN` 稳定 ID")
    return items


def validate_spec(spec_path: Path, task_status: str | None, errors: list[str]) -> dict[str, Any]:
    text = read_text(spec_path)
    structure = mask_fenced_code(text)
    version_matches = FORMAT_VERSION_RE.findall(structure)
    if len(version_matches) > 1:
        errors.append(f"spec Format version 必须且只能出现一次，实际为 {len(version_matches)} 次")
    format_version = int(version_matches[0]) if version_matches else 1
    if format_version not in {1, 2}:
        errors.append(f"不支持的 spec Format version: {format_version}")
    strict = task_status in {"ready", "in-progress", "verifying", "completed"}
    headings = SPEC_V2_REQUIRED_HEADINGS if format_version == 2 else SPEC_REQUIRED_HEADINGS
    if strict:
        single_match(H1_RE, structure, "spec 一级标题", errors)
    for heading in headings:
        if not strict:
            break
        if not meaningful_section(section_body(text, heading)):
            errors.append(f"spec.md 缺少有效的 `## {heading}` 内容")
    if strict and contains_placeholder(text, SPEC_PLACEHOLDERS):
        errors.append("spec.md 仍含模板占位文本")
    decisions: dict[str, str] = {}
    acceptance: dict[str, str] = {}
    if format_version == 2:
        decisions = stable_spec_items(section_body(text, "Decisions"), "D", strict, errors)
        acceptance = stable_spec_items(
            section_body(text, "Acceptance Criteria"),
            "AC",
            strict,
            errors,
        )
        if strict and not acceptance:
            errors.append("Format version 2 spec 必须至少包含一个 AC-NNN")
    return {
        "format_version": format_version,
        "decisions": decisions,
        "acceptance": acceptance,
        "refs": {**decisions, **acceptance},
    }


def parse_ticket(
    ticket_path: Path,
    project_root: Path,
    spec_format_version: int = 1,
    known_spec_refs: set[str] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    relative = contained_relative_path(ticket_path, project_root, "ticket", errors)
    filename_match = TICKET_FILE_RE.fullmatch(ticket_path.name)
    if not filename_match:
        errors.append("ticket 文件名必须是 `<NN>-<slug>.md`")
    if relative is None:
        return {
            "id": ticket_path.stem,
            "path": relative,
            "title": None,
            "status": None,
            "blocked_by": [],
            "spec_refs": [],
            "errors": errors,
            "warnings": warnings,
        }
    text = read_text(ticket_path)
    structure = mask_fenced_code(text)
    title = single_match(H1_RE, structure, "ticket 一级标题", errors)
    status = single_match(TASK_STATUS_RE, structure, "ticket Status", errors)
    blocked_value = single_match(BLOCKED_RE, structure, "Blocked by", errors)
    spec_ref_lines = SPEC_REFS_RE.findall(structure)
    spec_refs: list[str] = []
    if len(spec_ref_lines) > 1:
        errors.append(f"ticket Spec refs 必须且只能出现一次，实际为 {len(spec_ref_lines)} 次")
    elif spec_ref_lines:
        spec_refs = STABLE_REF_RE.findall(spec_ref_lines[0])
        residue = STABLE_REF_RE.sub("", spec_ref_lines[0])
        if re.sub(r"[\s,]+", "", residue):
            errors.append("ticket Spec refs 只能包含反引号包裹的 D-NNN 或 AC-NNN")
        if len(spec_refs) != len(set(spec_refs)):
            errors.append("ticket Spec refs 不得重复")
        if not spec_refs:
            errors.append("ticket Spec refs 必须包含反引号包裹的 D-NNN 或 AC-NNN")
    elif spec_format_version == 2:
        errors.append("Format version 2 ticket 缺少 Spec refs")
    if spec_format_version == 2 and spec_refs and not any(ref.startswith("AC-") for ref in spec_refs):
        errors.append("Format version 2 ticket 必须至少引用一个 AC-NNN")
    if known_spec_refs is not None:
        unknown_refs = [ref for ref in spec_refs if ref not in known_spec_refs]
        if unknown_refs:
            errors.append(f"ticket Spec refs 不存在: {', '.join(unknown_refs)}")
    if status and status not in TICKET_STATUSES:
        errors.append(f"未知 ticket 状态: {status}")
    blockers: list[str] = []
    if blocked_value:
        if blocked_value != "none":
            blockers = [item.strip() for item in blocked_value.split(",") if item.strip()]
            if not blockers:
                errors.append("Blocked by 必须使用 `none` 或逗号分隔的 ticket 名称")
            for blocker in blockers:
                if not re.fullmatch(r"\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*", blocker):
                    errors.append(f"非法 blocker: {blocker}")
    result_body = section_body(text, "Result")
    verification_body = section_body(text, "Verification")
    what_to_build = section_body(text, "What to build")
    acceptance = section_body(text, "Acceptance Criteria")
    if not meaningful_section(what_to_build):
        errors.append("缺少有效的 `## What to build` 内容")
    if not meaningful_section(acceptance):
        errors.append("缺少有效的 `## Acceptance Criteria` 内容")
    elif not re.search(r"^- \[[ xX]\] ", acceptance, re.MULTILINE):
        errors.append("Acceptance Criteria 必须使用 Markdown checkbox")
    if result_body is None:
        errors.append("缺少 `## Result` 章节")
    if verification_body is None:
        errors.append("缺少 `## Verification` 章节")
    if status == "completed":
        if not meaningful_section(result_body):
            errors.append("completed ticket 的 Result 未填写")
        if not meaningful_section(verification_body):
            errors.append("completed ticket 的 Verification 未填写")
        if acceptance and re.search(r"^- \[ \] ", acceptance, re.MULTILINE):
            errors.append("completed ticket 仍有未勾选的 Acceptance Criteria")
        if contains_placeholder(text, TICKET_PLACEHOLDERS):
            errors.append("completed ticket 仍含模板占位文本")
    return {
        "id": ticket_path.stem,
        "path": relative,
        "title": title,
        "status": status,
        "blocked_by": blockers,
        "spec_refs": spec_refs,
        "errors": errors,
        "warnings": warnings,
    }


def blocker_cycles(tickets: dict[str, dict[str, Any]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(ticket_id: str) -> None:
        if ticket_id in visiting:
            index = visiting.index(ticket_id)
            cycle = visiting[index:] + [ticket_id]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if ticket_id in visited:
            return
        visiting.append(ticket_id)
        for blocker in tickets[ticket_id]["blocked_by"]:
            if blocker in tickets:
                visit(blocker)
        visiting.pop()
        visited.add(ticket_id)

    for ticket_id in tickets:
        visit(ticket_id)
    return cycles


def parse_result(task_dir: Path, project_root: Path, task_status: str | None) -> dict[str, Any] | None:
    result_path = task_dir / "result.md"
    if not result_path.exists() and not result_path.is_symlink():
        return None
    errors: list[str] = []
    relative = contained_relative_path(result_path, project_root, "result.md", errors)
    if relative is None:
        return {
            "path": None,
            "errors": errors,
        }
    text = read_text(result_path)
    if task_status not in {"cancelled", "superseded"}:
        for heading in ("Delivered", "Verification", "Review Findings", "Remaining Work"):
            if not meaningful_section(section_body(text, heading)):
                errors.append(f"result.md 缺少有效的 `## {heading}` 内容")
        if contains_placeholder(text, RESULT_PLACEHOLDERS):
            errors.append("result.md 仍含模板占位文本")
    return {
        "path": relative,
        "errors": errors,
    }


def parse_task(task_dir: Path, project_root: Path, archived: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    relative = contained_relative_path(task_dir, project_root, "任务目录", errors)
    if relative is None:
        return {
            "path": None,
            "title": None,
            "status": None,
            "created": None,
            "planning_revision": None,
            "format_version": 1,
            "spec_ref_ids": [],
            "reason": None,
            "superseded_by": None,
            "current": False,
            "current_ticket": None,
            "tickets": {**{state: 0 for state in TICKET_STATUSES}, "total": 0},
            "frontier": [],
            "result_exists": False,
            "errors": errors,
            "warnings": warnings,
        }
    if not TASK_DIR_RE.fullmatch(task_dir.name):
        errors.append("任务目录名必须是 `YYYY-MM-DD-<slug>`")
    task_path = task_dir / "task.md"
    spec_path = task_dir / "spec.md"
    title: str | None = None
    status: str | None = None
    created: str | None = None
    planning_revision: int | None = None
    cancel_reason: str | None = None
    superseded_by: str | None = None
    spec_metadata: dict[str, Any] = {
        "format_version": 1,
        "decisions": {},
        "acceptance": {},
        "refs": {},
    }
    if not task_path.is_file():
        errors.append("缺少 task.md")
    elif not is_within(task_path, project_root):
        errors.append("task.md 通过符号链接解析到 Zyes 项目根目录之外")
    else:
        text = read_text(task_path)
        structure = mask_fenced_code(text)
        title = single_match(H1_RE, structure, "task 一级标题", errors)
        status = single_match(TASK_STATUS_RE, structure, "task Status", errors)
        created = single_match(CREATED_RE, structure, "Created", errors)
        revision = single_match(PLANNING_REVISION_RE, structure, "Planning revision", errors)
        reason_matches = CANCEL_REASON_RE.findall(structure)
        superseded_matches = SUPERSEDED_BY_RE.findall(structure)
        if revision:
            planning_revision = int(revision)
            if planning_revision < 1:
                errors.append("Planning revision 必须大于 0")
        if len(reason_matches) > 1:
            errors.append(f"task Reason 最多出现一次，实际为 {len(reason_matches)} 次")
        elif reason_matches:
            cancel_reason = reason_matches[0].strip()
        if len(superseded_matches) > 1:
            errors.append(f"Superseded by 最多出现一次，实际为 {len(superseded_matches)} 次")
        elif superseded_matches:
            superseded_by = superseded_matches[0].strip()
        if status and status not in TASK_STATUSES:
            errors.append(f"未知 task 状态: {status}")
        if created:
            try:
                date.fromisoformat(created)
            except ValueError:
                errors.append(f"Created 不是有效的 YYYY-MM-DD 日期: {created}")
            else:
                if TASK_DIR_RE.fullmatch(task_dir.name) and created != task_dir.name[:10]:
                    errors.append("Created 必须与任务目录日期一致")
    tickets_dir = task_dir / "tickets"
    spec_validation_status = status
    if (
        status == "planning"
        and tickets_dir.is_dir()
        and is_within(tickets_dir, project_root)
        and any(tickets_dir.glob("*.md"))
    ):
        spec_validation_status = "ready"
    if not spec_path.is_file():
        errors.append("缺少 spec.md")
    elif not is_within(spec_path, project_root):
        errors.append("spec.md 通过符号链接解析到 Zyes 项目根目录之外")
    else:
        spec_metadata = validate_spec(spec_path, spec_validation_status, errors)

    ticket_items: list[dict[str, Any]] = []
    if tickets_dir.exists() and not tickets_dir.is_dir():
        errors.append("tickets 必须是目录")
    elif tickets_dir.is_dir() and not is_within(tickets_dir, project_root):
        errors.append("tickets 目录通过符号链接解析到 Zyes 项目根目录之外")
    elif tickets_dir.is_dir():
        for ticket_path in sorted(tickets_dir.glob("*.md")):
            ticket_items.append(
                parse_ticket(
                    ticket_path,
                    project_root,
                    spec_metadata["format_version"],
                    set(spec_metadata["refs"]),
                )
            )
    tickets = {item["id"]: item for item in ticket_items}
    numbers: dict[str, list[str]] = {}
    for ticket_id in tickets:
        number = ticket_id.split("-", 1)[0]
        numbers.setdefault(number, []).append(ticket_id)
    for number, ids in numbers.items():
        if len(ids) > 1:
            errors.append(f"ticket 编号重复 {number}: {', '.join(ids)}")
    for ticket_id, ticket in tickets.items():
        for blocker in ticket["blocked_by"]:
            if blocker == ticket_id:
                ticket["errors"].append("ticket 不能阻塞自身")
            elif blocker not in tickets:
                ticket["errors"].append(f"blocker 不存在: {blocker}")
        if ticket["status"] == "in-progress":
            incomplete = [
                blocker
                for blocker in ticket["blocked_by"]
                if blocker in tickets and tickets[blocker]["status"] != "completed"
            ]
            if incomplete:
                ticket["errors"].append(
                    f"in-progress ticket 仍被未完成 blocker 阻塞: {', '.join(incomplete)}"
                )
    for cycle in blocker_cycles(tickets):
        errors.append(f"ticket 依赖图存在环: {' -> '.join(cycle)}")

    frontier = [
        ticket_id
        for ticket_id, ticket in tickets.items()
        if ticket["status"] == "ready"
        and not ticket["errors"]
        and all(tickets[blocker]["status"] == "completed" for blocker in ticket["blocked_by"] if blocker in tickets)
    ]
    counts = {state: sum(1 for ticket in tickets.values() if ticket["status"] == state) for state in TICKET_STATUSES}
    counts["total"] = len(tickets)
    in_progress = [ticket_id for ticket_id, ticket in tickets.items() if ticket["status"] == "in-progress"]
    if len(in_progress) > 1:
        errors.append(f"同一任务存在多个 in-progress tickets: {', '.join(in_progress)}")
    if status == "planning" and any(ticket["status"] != "ready" for ticket in tickets.values()):
        errors.append("planning task 中已有 tickets 时，它们必须全部为 ready")
    if status == "ready":
        if not tickets:
            errors.append("ready task 必须至少包含一个 ticket")
        if any(ticket["status"] != "ready" for ticket in tickets.values()):
            errors.append("ready task 的 tickets 必须全部为 ready")
    if status == "in-progress" and tickets and all(ticket["status"] == "completed" for ticket in tickets.values()):
        errors.append("所有 tickets 已完成时 task 应进入 verifying")
    if status == "in-progress" and not tickets:
        errors.append("in-progress task 必须至少包含一个 ticket")
    if status in {"verifying", "completed"}:
        if not tickets or any(ticket["status"] != "completed" for ticket in tickets.values()):
            errors.append(f"{status} task 的 tickets 必须全部为 completed")
    if status in {"cancelled", "superseded"} and in_progress:
        errors.append(f"{status} task 不得包含 in-progress ticket")

    if status == "cancelled":
        if not cancel_reason or cancel_reason.startswith("<"):
            errors.append("cancelled task 必须包含有效的 Reason")
        if superseded_by:
            errors.append("cancelled task 不应包含 Superseded by")
    elif status == "superseded":
        if cancel_reason:
            errors.append("superseded task 不应包含 Reason")
        if not superseded_by:
            errors.append("superseded task 必须包含 Superseded by")
        else:
            if not TASK_DIR_RE.fullmatch(superseded_by):
                errors.append("Superseded by 必须是 `YYYY-MM-DD-<slug>` task 标识")
            elif superseded_by == task_dir.name:
                errors.append("task 不能 supersede 自身")
            else:
                active_target = project_root / "tasks" / superseded_by
                archived_targets = [
                    target
                    for target in (project_root / "archive").glob(f"*/{superseded_by}")
                    if re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", target.parent.name)
                ]
                matches = [target for target in (active_target, *archived_targets) if target.is_dir()]
                if any(not is_within(target, project_root) for target in matches):
                    errors.append("Superseded by 目标通过符号链接解析到 Zyes 项目根目录之外")
                elif len(matches) != 1:
                    errors.append(
                        f"Superseded by 必须唯一指向 active 或 archived task: {superseded_by}"
                    )
                else:
                    replacement_task = matches[0] / "task.md"
                    if not replacement_task.is_file() or not is_within(replacement_task, project_root):
                        errors.append(f"Superseded by 目标缺少可访问的 task.md: {superseded_by}")
    elif cancel_reason or superseded_by:
        errors.append("只有 cancelled 或 superseded task 可以包含终态说明")

    result = parse_result(task_dir, project_root, status)
    if archived and status not in TERMINAL_TASK_STATUSES:
        errors.append("归档任务必须处于 completed、cancelled 或 superseded")
    if status == "completed" and result is None:
        errors.append("completed task 缺少 result.md")
    if result:
        errors.extend(result["errors"])
    for ticket in tickets.values():
        if ticket["errors"]:
            errors.extend(f"{ticket['id']}: {message}" for message in ticket["errors"])
    return {
        "path": relative,
        "title": title,
        "status": status,
        "created": created,
        "planning_revision": planning_revision,
        "format_version": spec_metadata["format_version"],
        "spec_ref_ids": sorted(spec_metadata["refs"]),
        "reason": cancel_reason,
        "superseded_by": superseded_by,
        "current": False,
        "current_ticket": None,
        "tickets": counts,
        "frontier": sorted(frontier),
        "result_exists": result is not None,
        "errors": errors,
        "warnings": warnings,
    }


def active_task_dirs(project_root: Path) -> tuple[list[Path], list[str]]:
    tasks_root = project_root / "tasks"
    if not tasks_root.exists():
        return [], []
    if not tasks_root.is_dir():
        return [], ["tasks 必须是目录"]
    if not is_within(tasks_root, project_root):
        return [], ["tasks 目录通过符号链接解析到 Zyes 项目根目录之外"]
    dirs: list[Path] = []
    errors: list[str] = []
    for item in sorted(tasks_root.iterdir()):
        if not item.is_dir():
            continue
        if not is_within(item, project_root):
            errors.append(f"任务目录越界: tasks/{item.name}")
            continue
        dirs.append(item)
    return dirs, errors


def archived_task_dirs(project_root: Path) -> tuple[list[Path], list[str]]:
    archive_root = project_root / "archive"
    if not archive_root.exists():
        return [], []
    if not archive_root.is_dir():
        return [], ["archive 必须是目录"]
    if not is_within(archive_root, project_root):
        return [], ["archive 目录通过符号链接解析到 Zyes 项目根目录之外"]
    dirs: list[Path] = []
    errors: list[str] = []
    for month in sorted(archive_root.iterdir()):
        if not month.is_dir():
            continue
        if not is_within(month, archive_root):
            errors.append(f"归档月份目录越界: archive/{month.name}")
            continue
        if not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", month.name):
            errors.append(f"非法归档月份目录: archive/{month.name}")
        for task_dir in sorted(month.iterdir()):
            if not task_dir.is_dir():
                continue
            if not is_within(task_dir, month):
                errors.append(f"归档任务目录越界: archive/{month.name}/{task_dir.name}")
                continue
            dirs.append(task_dir)
    return dirs, errors


def select_task_dir(project_root: Path, selector: str) -> Path:
    tasks_root = (project_root / "tasks").resolve()
    if not is_within(tasks_root, project_root):
        raise ZyesError("tasks 目录通过符号链接解析到 Zyes 项目根目录之外")
    candidate = Path(selector)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    elif selector.startswith("tasks/"):
        resolved = project_root.joinpath(*PurePosixPath(selector).parts).resolve()
    else:
        resolved = (tasks_root / selector).resolve()
    if not is_within(resolved, tasks_root) or resolved.parent != tasks_root:
        raise ZyesError("--task 必须指向 tasks/ 的直接子目录")
    if not resolved.is_dir():
        raise ZyesError(f"任务目录不存在: {resolved}")
    return resolved


def snapshot(project_root: Path, task_selector: str | None = None, include_archive: bool = False) -> dict[str, Any]:
    project_root = project_root.expanduser().resolve()
    if not project_root.is_dir():
        raise ZyesError(f"Zyes 项目根目录不存在或不可访问: {project_root}")
    current = parse_current(project_root)
    if task_selector:
        task_dirs = [select_task_dir(project_root, task_selector)]
        global_errors: list[str] = []
    else:
        task_dirs, global_errors = active_task_dirs(project_root)
    tasks = [parse_task(task_dir, project_root) for task_dir in task_dirs]
    task_map = {task["path"]: task for task in tasks}
    global_errors.extend(current["errors"])

    if current["task"]:
        current_task = task_map.get(current["task"])
        if current_task:
            current_task["current"] = True
            current_task["current_ticket"] = current["ticket"]
            if current["ticket"]:
                current_ticket_path = PurePosixPath(current["ticket"])
                expected_ticket_dir = PurePosixPath(current_task["path"]) / "tickets"
                if current_ticket_path.parent != expected_ticket_dir:
                    current_task["errors"].append("current ticket 不属于 current task")
                else:
                    ticket_id = Path(current["ticket"]).stem
                    ticket_path = project_root / current["ticket"]
                    if not TICKET_FILE_RE.fullmatch(ticket_path.name):
                        current_task["errors"].append("current ticket 文件名不符合 `<NN>-<slug>.md`")
                    elif ticket_path.exists():
                        ticket = parse_ticket(ticket_path, project_root)
                        if ticket["status"] != "in-progress":
                            current_task["errors"].append(f"current ticket {ticket_id} 不是 in-progress")
                        if current_task["status"] != "in-progress":
                            current_task["errors"].append("只有 in-progress task 可以设置 current ticket")
            elif current_task["tickets"]["in-progress"]:
                current_task["errors"].append("task 存在 in-progress ticket，但 current ticket 为 null")
        elif not task_selector:
            global_errors.append(f"current task 未出现在 active tasks 中: {current['task']}")
    for task in tasks:
        if task["tickets"]["in-progress"] and not task["current"]:
            task["warnings"].append("任务存在 in-progress ticket，但不是 current task")

    archived: list[dict[str, Any]] = []
    if include_archive:
        archive_dirs, archive_errors = archived_task_dirs(project_root)
        global_errors.extend(archive_errors)
        archived = [parse_task(task_dir, project_root, archived=True) for task_dir in archive_dirs]
        archived.sort(key=lambda item: item["created"] or "", reverse=True)

    tasks.sort(key=lambda item: item["created"] or "", reverse=True)
    tasks.sort(key=lambda item: STATUS_ORDER.get(item["status"], 99))
    tasks.sort(key=lambda item: not item["current"])
    valid = not global_errors and all(not task["errors"] for task in tasks) and all(not task["errors"] for task in archived)
    return {
        "project_root": str(project_root),
        "valid": valid,
        "current": current,
        "errors": global_errors,
        "tasks": tasks,
        "archive": archived,
    }


def context_files(
    project_root: Path,
    task: dict[str, Any] | None,
    phase: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    knowledge_context = project_root / "knowledge" / "CONTEXT.md"
    adr_dir = project_root / "knowledge" / "adr"
    files: dict[str, Any] = {
        "knowledge_context": "knowledge/CONTEXT.md"
        if knowledge_context.is_file() and is_within(knowledge_context, project_root)
        else None,
        "adr_dir": "knowledge/adr"
        if adr_dir.is_dir() and is_within(adr_dir, project_root)
        else None,
    }
    if task is None or not isinstance(task.get("path"), str):
        return files

    task_root = project_root / task["path"]
    tickets_root = task_root / "tickets"
    ticket_paths = (
        [
            ticket.resolve().relative_to(project_root.resolve()).as_posix()
            for ticket in sorted(tickets_root.glob("*.md"))
            if is_within(ticket, project_root)
        ]
        if tickets_root.is_dir() and is_within(tickets_root, project_root)
        else []
    )
    if phase == "implement" and not verbose:
        ticket_paths = []
        current_ticket = task.get("current_ticket")
        if isinstance(current_ticket, str):
            current_path = PurePosixPath(current_ticket)
            expected_parent = PurePosixPath(task["path"]) / "tickets"
            resolved = project_root.joinpath(*current_path.parts)
            if (
                current_path.parent == expected_parent
                and TICKET_FILE_RE.fullmatch(current_path.name)
                and resolved.is_file()
                and is_within(resolved, project_root)
            ):
                ticket_paths = [current_path.as_posix()]
    files.update(
        {
            "task": f"{task['path']}/task.md",
            "spec": f"{task['path']}/spec.md",
            "tickets": ticket_paths,
            "result": f"{task['path']}/result.md" if (task_root / "result.md").is_file() else None,
        }
    )
    return files


def task_context_summary(task: dict[str, Any], verbose: bool = False) -> dict[str, Any]:
    summary = {
        "path": task["path"],
        "title": task["title"],
        "status": task["status"],
        "planning_revision": task["planning_revision"],
        "format_version": task["format_version"],
        "current": task["current"],
        "current_ticket": task["current_ticket"],
        "tickets": task["tickets"],
        "frontier": task["frontier"],
        "result_exists": task["result_exists"],
        "errors": task["errors"],
    }
    if verbose:
        summary["warnings"] = task["warnings"]
    return summary


def candidate_context_summary(task: dict[str, Any], verbose: bool = False) -> dict[str, Any]:
    if verbose:
        return task_context_summary(task, verbose=True)
    return {
        "path": task["path"],
        "title": task["title"],
        "status": task["status"],
    }


def estimate_context_tokens(text: str) -> int:
    ascii_characters = sum(ord(character) < 128 for character in text)
    non_ascii_characters = len(text) - ascii_characters
    return (ascii_characters + 3) // 4 + non_ascii_characters


def snapshot_errors(data: dict[str, Any]) -> list[str]:
    return [
        *data["errors"],
        *(
            f"{task['path']}: {message}"
            for task in data["tasks"]
            for message in task["errors"]
        ),
    ]


def select_entry_task(
    data: dict[str, Any],
    allowed_statuses: set[str],
    task_selector: str | None,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str | None]:
    candidates = [task for task in data["tasks"] if task["status"] in allowed_statuses]
    selected: dict[str, Any] | None = None
    selection: str | None = None
    if task_selector:
        selected = data["tasks"][0] if data["tasks"] else None
        selection = "explicit"
    elif data["current"]["task"]:
        selected = next(
            (task for task in data["tasks"] if task["path"] == data["current"]["task"]),
            None,
        )
        if selected:
            selection = "current"
    if selected is None and len(candidates) == 1:
        selected = candidates[0]
        selection = "unique-candidate"
    return selected, candidates, selection


def route_entry_action(
    entry: str,
    selected: dict[str, Any] | None,
    candidates: list[dict[str, Any]],
    valid: bool,
) -> str:
    if not valid:
        return "resolve-errors"
    if selected is None and len(candidates) > 1:
        return "select-task"
    if selected is None:
        return "create-planning-task" if entry == "z-brainstorm" else "no-matching-task"
    if selected["status"] not in ENTRY_STATUSES[entry]:
        return "use-entry-for-status"
    if entry == "z-brainstorm":
        return "approve-or-revise-plan" if selected["tickets"]["total"] else "refine-plan"
    if entry == "z-implement":
        if selected["status"] == "ready":
            return "start-ticket"
        if selected["status"] == "in-progress":
            return "implement-ticket" if selected["current_ticket"] else "start-ticket"
        if selected["status"] == "verifying":
            return "verify-task"
        return "reverify-or-finish"
    if selected["status"] in TERMINAL_TASK_STATUSES:
        return "archive-task"
    return "cancel-or-supersede-task"


def task_state(task: dict[str, Any] | None, selection: str | None) -> dict[str, Any] | None:
    if task is None:
        return None
    state: dict[str, Any] = {
        "task": task["path"],
        "title": task["title"],
        "status": task["status"],
        "revision": task["planning_revision"],
        "format_version": task["format_version"],
        "selection": selection,
    }
    if task["current_ticket"]:
        state["ticket"] = task["current_ticket"]
    return state


def compact_task_list(task: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "path": task["path"],
        "title": task["title"],
        "status": task["status"],
        "current": task["current"],
        "tickets": task["tickets"],
        "frontier": task["frontier"],
    }
    if task["current_ticket"]:
        summary["current_ticket"] = task["current_ticket"]
    if task["reason"]:
        summary["reason"] = task["reason"]
    if task["superseded_by"]:
        summary["superseded_by"] = task["superseded_by"]
    return summary


def entry_input_paths(
    project_root: Path,
    entry: str,
    action: str,
    selected: dict[str, Any] | None,
    verbose: bool,
) -> tuple[list[str], dict[str, Any]]:
    if selected is None or entry == "z-list-tasks":
        return [], {}
    if entry == "z-finish-task":
        full = context_files(project_root, selected, phase="finish", verbose=verbose)
        names = ("task", "result")
    else:
        phase = "plan"
        if entry == "z-implement":
            phase = "verify" if selected["status"] in {"verifying", "completed"} else "implement"
        full = context_files(project_root, selected, phase=phase, verbose=verbose)
        if selected["format_version"] == 2 and action == "implement-ticket":
            names = ("task", "tickets", "knowledge_context", "adr_dir")
        elif selected["format_version"] == 2 and action == "verify-task":
            names = ("task", "result", "knowledge_context", "adr_dir")
        else:
            names = ("task", "spec", "tickets", "result", "knowledge_context", "adr_dir")
    inputs: list[str] = []
    for name in names:
        value = full.get(name)
        if isinstance(value, str):
            inputs.append(value)
        elif isinstance(value, list):
            inputs.extend(item for item in value if isinstance(item, str))
    return inputs, full


def spec_artifact_metadata(project_root: Path, task: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    spec_path = project_root / task["path"] / "spec.md"
    text = read_text(spec_path)
    metadata = validate_spec(spec_path, task["status"], [])
    return text, metadata


def ticket_evidence(
    ticket_path: Path,
    project_root: Path,
    task: dict[str, Any],
) -> dict[str, Any]:
    parsed = parse_ticket(
        ticket_path,
        project_root,
        task["format_version"],
        set(task["spec_ref_ids"]),
    )
    text = read_text(ticket_path)
    result = section_body(text, "Result")
    verification = section_body(text, "Verification")
    return {
        "ticket": parsed["id"],
        "path": parsed["path"],
        "status": parsed["status"],
        "spec_refs": parsed["spec_refs"],
        "result": result if meaningful_section(result) else None,
        "verification": verification if meaningful_section(verification) else None,
    }


def entry_artifact_context(
    project_root: Path,
    selected: dict[str, Any] | None,
    action: str,
) -> tuple[dict[str, Any], list[str]]:
    if selected is None or selected["format_version"] != 2:
        return {}, []
    if action not in {"implement-ticket", "verify-task"}:
        return {}, []
    spec_text, metadata = spec_artifact_metadata(project_root, selected)
    context: dict[str, Any] = {
        "goal": section_body(spec_text, "Problem Statement"),
        "out_of_scope": section_body(spec_text, "Out of Scope"),
    }
    expand: list[str] = []
    if action == "implement-ticket":
        current_ticket = selected["current_ticket"]
        if not current_ticket:
            return context, expand
        ticket_path = project_root.joinpath(*PurePosixPath(current_ticket).parts)
        evidence = ticket_evidence(ticket_path, project_root, selected)
        context["spec_refs"] = [
            {"id": ref, "text": metadata["refs"][ref]}
            for ref in evidence["spec_refs"]
            if ref in metadata["refs"]
        ]
        return context, expand

    tickets_root = project_root / selected["path"] / "tickets"
    evidence_items = [
        ticket_evidence(path, project_root, selected)
        for path in sorted(tickets_root.glob("*.md"))
        if is_within(path, project_root)
    ]
    matrix: list[dict[str, Any]] = []
    for acceptance_id, acceptance_text in metadata["acceptance"].items():
        covered = [item for item in evidence_items if acceptance_id in item["spec_refs"]]
        blocking: list[str] = []
        if not covered:
            blocking.append("no covering ticket")
        for item in covered:
            if item["status"] != "completed":
                blocking.append(f"{item['ticket']} is not completed")
                if item["path"]:
                    expand.append(item["path"])
            if item["result"] is None or item["verification"] is None:
                blocking.append(f"{item['ticket']} lacks result or verification evidence")
                if item["path"]:
                    expand.append(item["path"])
        matrix.append(
            {
                "acceptance_id": acceptance_id,
                "text": acceptance_text,
                "tickets": covered,
                "blocking": blocking,
            }
        )
    context["evidence_matrix"] = matrix
    return context, sorted(set(expand))


def append_prompt_block(
    lines: list[str],
    label: str,
    value: str | None,
    content_indent: str = "",
) -> None:
    if value is None:
        return
    lines.append(f"{label}:")
    lines.extend(f"{content_indent}{line}" for line in (value.splitlines() or ["none"]))


def render_entry_prompt(contract: dict[str, Any]) -> str:
    lines = [
        "<zyes-context>",
        f"Project: {contract['project_root']}",
        f"Entry: {contract['entry']}",
        f"Action: {contract['action']}",
    ]
    state = contract["state"]
    if state is None:
        lines.append("State: none")
    else:
        state_parts = [
            f"task={state['task']}",
            f"status={state['status']}",
            f"revision={state['revision']}",
        ]
        if state.get("ticket"):
            state_parts.append(f"ticket={state['ticket']}")
        lines.append("State: " + ", ".join(state_parts))
    if contract["frontier"]:
        lines.append("Frontier: " + ", ".join(contract["frontier"]))
    if contract["choices"]:
        lines.append("Choices:")
        for choice in contract["choices"]:
            lines.append(f"- {choice['path']} | {choice['status']} | {choice['title']}")
    if contract["tasks"]:
        lines.append("Tasks:")
        for task in contract["tasks"]:
            tickets = task["tickets"]
            marker = "current" if task["current"] else "active"
            lines.append(
                f"- {task['path']} | {task['status']} | {marker} | "
                f"tickets={tickets['completed']}/{tickets['total']}"
            )
            details: list[str] = []
            if task.get("current_ticket"):
                details.append(f"ticket={task['current_ticket']}")
            if task["frontier"]:
                details.append("frontier=" + ",".join(task["frontier"]))
            if task.get("reason"):
                details.append(f"reason={task['reason']}")
            if task.get("superseded_by"):
                details.append(f"superseded_by={task['superseded_by']}")
            if details:
                lines.append("  " + "; ".join(details))
    if contract["inputs"]:
        lines.append("Inputs:")
        lines.extend(f"- {path}" for path in contract["inputs"])
    artifact_context = contract["context"]
    if artifact_context:
        lines.append("Context:")
        append_prompt_block(lines, "Goal", artifact_context.get("goal"))
        append_prompt_block(lines, "Out of scope", artifact_context.get("out_of_scope"))
        if artifact_context.get("spec_refs"):
            lines.append("Spec refs:")
            lines.extend(
                f"- {item['id']}: {item['text']}"
                for item in artifact_context["spec_refs"]
            )
        if artifact_context.get("evidence_matrix"):
            lines.append("Evidence matrix:")
            for item in artifact_context["evidence_matrix"]:
                lines.append(f"- {item['acceptance_id']}: {item['text']}")
                if item["tickets"]:
                    for ticket in item["tickets"]:
                        lines.append(f"  - {ticket['ticket']} | {ticket['status']}")
                        append_prompt_block(
                            lines,
                            "    Result",
                            ticket["result"],
                            content_indent="      ",
                        )
                        append_prompt_block(
                            lines,
                            "    Verification",
                            ticket["verification"],
                            content_indent="      ",
                        )
                if item["blocking"]:
                    lines.extend(f"  - BLOCKING: {message}" for message in item["blocking"])
    if contract["required"]:
        lines.append("Required:")
        lines.extend(f"- {instruction}" for instruction in contract["required"])
    if contract["stop"]:
        lines.append("Stop:")
        lines.extend(f"- {instruction}" for instruction in contract["stop"])
    if contract["errors"]:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in contract["errors"])
    budget = contract.get("budget")
    if budget and budget["oversize"]:
        lines.append(
            f"Oversize: true; estimated={budget['estimated_tokens']}; limit={budget['limit']}"
        )
        lines.append("Expand:")
        expand_paths = contract["expand"] or contract["inputs"]
        if expand_paths:
            lines.extend(f"- {path}" for path in expand_paths)
        else:
            lines.append("- Rerun context with --verbose for targeted diagnostics.")
    lines.append("</zyes-context>")
    return "\n".join(lines)


def entry_context(
    project_root: Path,
    entry: str,
    task_selector: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    if entry not in ENTRY_STATUSES:
        raise ZyesError(f"未知入口: {entry}")
    data = snapshot(project_root, task_selector)
    errors = snapshot_errors(data)

    if entry == "z-list-tasks":
        action = "resolve-errors" if not data["valid"] else "list-tasks"
        required, stop = ACTION_INSTRUCTIONS[action]
        current_task = next((task for task in data["tasks"] if task["current"]), None)
        contract: dict[str, Any] = {
            "project_root": data["project_root"],
            "entry": entry,
            "action": action,
            "valid": data["valid"],
            "state": task_state(current_task, "current" if current_task else None),
            "choices": [],
            "tasks": [compact_task_list(task) for task in data["tasks"]],
            "inputs": [],
            "context": {},
            "expand": [],
            "frontier": [],
            "required": list(required),
            "stop": list(stop),
            "errors": errors,
        }
        if verbose:
            contract["diagnostics"] = data
    else:
        selected, candidates, selection = select_entry_task(
            data,
            ENTRY_STATUSES[entry],
            task_selector,
        )
        action = route_entry_action(entry, selected, candidates, data["valid"])
        required, stop = ACTION_INSTRUCTIONS[action]
        if data["valid"]:
            inputs, full_files = entry_input_paths(
                project_root,
                entry,
                action,
                selected,
                verbose,
            )
            artifact_context, expand = entry_artifact_context(project_root, selected, action)
        else:
            inputs, full_files = [], {}
            artifact_context, expand = {}, []
        contract = {
            "project_root": data["project_root"],
            "entry": entry,
            "action": action,
            "valid": data["valid"],
            "state": task_state(selected, selection),
            "choices": (
                [candidate_context_summary(task) for task in candidates]
                if action == "select-task"
                else []
            ),
            "tasks": [],
            "inputs": inputs,
            "context": artifact_context,
            "expand": expand,
            "frontier": selected["frontier"] if selected and action == "start-ticket" else [],
            "required": list(required),
            "stop": list(stop),
            "errors": errors,
        }
        if verbose:
            contract["diagnostics"] = {
                "selected_task": task_context_summary(selected, verbose=True) if selected else None,
                "candidates": [candidate_context_summary(task, verbose=True) for task in candidates],
                "files": full_files,
            }

    prompt = render_entry_prompt(contract)
    limit = 700 if contract["choices"] else 450
    estimated_tokens = estimate_context_tokens(prompt)
    contract["budget"] = {
        "limit": limit,
        "estimated_tokens": estimated_tokens,
        "oversize": estimated_tokens > limit,
    }
    return contract


def project_root_from_args(args: argparse.Namespace) -> Path:
    if args.project_root:
        return Path(args.project_root).expanduser().resolve()
    config = resolve_project_root(
        Path(args.repo),
        Path(args.zyes_home) if args.zyes_home else None,
        Path(args.global_instructions) if args.global_instructions else None,
    )
    return Path(config["project_root"])


def ensure_valid_selected_task(project_root: Path, task_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    data = snapshot(project_root, task_dir.name)
    if not data["tasks"]:
        raise ZyesError(f"未找到任务: {task_dir.name}")
    task = data["tasks"][0]
    errors = [*data["errors"], *task["errors"]]
    if errors:
        raise ZyesError("；".join(errors))
    return data, task


def write_text_state(path: Path, content: str, transaction: StateTransaction) -> None:
    transaction.write_text(path, content)


def replace_single_status(
    path: Path,
    status: str,
    transaction: StateTransaction,
) -> None:
    text = read_text(path)
    matches = list(TASK_STATUS_RE.finditer(mask_fenced_code(text)))
    if len(matches) != 1:
        raise ZyesError(f"{path} 的 Status 必须且只能出现一次，实际为 {len(matches)} 次")
    start, end = matches[0].span()
    updated = f"{text[:start]}Status: `{status}`{text[end:]}"
    write_text_state(path, updated, transaction)


def set_task_line(
    task_path: Path,
    pattern: re.Pattern[str],
    line: str,
    label: str,
    transaction: StateTransaction,
) -> None:
    text = read_text(task_path)
    matches = list(pattern.finditer(mask_fenced_code(text)))
    if len(matches) > 1:
        raise ZyesError(f"{task_path} 的 {label} 最多出现一次，实际为 {len(matches)} 次")
    if matches:
        start, end = matches[0].span()
        updated = f"{text[:start]}{line}{text[end:]}"
    else:
        separator = "" if text.endswith("\n") else "\n"
        updated = f"{text}{separator}{line}\n"
    write_text_state(task_path, updated, transaction)


def bump_planning_revision(task_path: Path, transaction: StateTransaction) -> int:
    text = read_text(task_path)
    matches = list(PLANNING_REVISION_RE.finditer(mask_fenced_code(text)))
    if len(matches) != 1:
        raise ZyesError(f"{task_path} 的 Planning revision 必须且只能出现一次，实际为 {len(matches)} 次")
    next_revision = int(matches[0].group(1)) + 1
    start, end = matches[0].span()
    updated = f"{text[:start]}Planning revision: `{next_revision}`{text[end:]}"
    write_text_state(task_path, updated, transaction)
    return next_revision


def task_relative_path(task_dir: Path, project_root: Path) -> str:
    return task_dir.resolve().relative_to(project_root.resolve()).as_posix()


def ticket_relative_path(ticket_path: Path, project_root: Path) -> str:
    return ticket_path.resolve().relative_to(project_root.resolve()).as_posix()


def write_current(
    project_root: Path,
    task_rel: str | None,
    ticket_rel: str | None,
    transaction: StateTransaction,
) -> None:
    current_path = project_root / "runtime/current.yaml"
    if task_rel is None:
        if current_path.exists() or current_path.is_symlink():
            if not is_within(current_path, project_root):
                raise ZyesError("runtime/current.yaml 通过符号链接解析到 Zyes 项目根目录之外")
            transaction.unlink(current_path)
        return
    task_parsed = posix_relative_path(task_rel, "current task", [])
    ticket_parsed = None if ticket_rel is None else posix_relative_path(ticket_rel, "current ticket", [])
    if task_parsed is None or (ticket_rel is not None and ticket_parsed is None):
        raise ZyesError("current 路径必须是 Zyes 项目根目录内的规范相对路径")
    if current_path.exists() and current_path.is_symlink():
        raise ZyesError("runtime/current.yaml 是符号链接，拒绝覆盖")
    text = f"task: {task_rel}\nticket: {ticket_rel or 'null'}\n"
    write_text_state(current_path, text, transaction)


def select_ticket_path(project_root: Path, task_dir: Path, selector: str) -> Path:
    if "\\" in selector:
        raise ZyesError("ticket 必须使用 POSIX 路径或 ticket 标识")
    raw = PurePosixPath(selector)
    if raw.is_absolute() or ".." in raw.parts:
        raise ZyesError("ticket 必须是当前任务内的相对路径或 ticket 标识")
    if len(raw.parts) == 4 and raw.parts[0] == "tasks" and raw.parts[2] == "tickets":
        if raw.parts[1] != task_dir.name:
            raise ZyesError("ticket 不属于指定 task")
        filename = raw.name
    elif len(raw.parts) == 2 and raw.parts[0] == "tickets":
        filename = raw.name
    elif len(raw.parts) == 1:
        filename = raw.name if raw.name.endswith(".md") else f"{raw.name}.md"
    else:
        raise ZyesError("ticket 必须是 ticket 标识、文件名或 `tickets/<file>.md`")
    if not TICKET_FILE_RE.fullmatch(filename):
        raise ZyesError("ticket 文件名必须是 `<NN>-<slug>.md`")
    ticket_path = (task_dir / "tickets" / filename).resolve()
    tickets_dir = (task_dir / "tickets").resolve()
    if not is_within(ticket_path, project_root) or ticket_path.parent != tickets_dir:
        raise ZyesError("ticket 路径解析到指定 task 的 tickets 目录之外")
    if not ticket_path.is_file():
        raise ZyesError(f"ticket 不存在: {ticket_path}")
    return ticket_path


def parsed_tickets(task_dir: Path, project_root: Path) -> dict[str, dict[str, Any]]:
    tickets_dir = task_dir / "tickets"
    if not tickets_dir.is_dir():
        return {}
    return {ticket_path.stem: parse_ticket(ticket_path, project_root) for ticket_path in sorted(tickets_dir.glob("*.md"))}


def ticket_completion_errors(ticket_path: Path) -> list[str]:
    text = read_text(ticket_path)
    errors: list[str] = []
    result_body = section_body(text, "Result")
    verification_body = section_body(text, "Verification")
    acceptance = section_body(text, "Acceptance Criteria")
    if not meaningful_section(result_body):
        errors.append("ticket 的 Result 未填写")
    if not meaningful_section(verification_body):
        errors.append("ticket 的 Verification 未填写")
    if not meaningful_section(acceptance):
        errors.append("ticket 缺少有效的 Acceptance Criteria")
    elif re.search(r"^- \[ \] ", acceptance, re.MULTILINE):
        errors.append("ticket 仍有未勾选的 Acceptance Criteria")
    if contains_placeholder(text, TICKET_PLACEHOLDERS):
        errors.append("ticket 仍含模板占位文本")
    return errors


def command_payload(project_root: Path, task_dir: Path, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    data = snapshot(project_root, task_dir.name)
    payload: dict[str, Any] = {
        "valid": data["valid"],
        "current": data["current"],
        "task": data["tasks"][0] if data["tasks"] else None,
        "errors": data["errors"],
    }
    if extra:
        payload.update(extra)
    return payload


def ensure_command_payload_valid(command: str, payload: dict[str, Any]) -> None:
    if payload["valid"]:
        return
    errors = list(payload["errors"])
    task = payload.get("task")
    if task:
        errors.extend(task["errors"])
    detail = "；".join(errors) if errors else "未知状态错误"
    raise ZyesError(f"{command} 后状态校验失败：{detail}")


def ensure_no_other_current_ticket(current: dict[str, Any], task_rel: str) -> None:
    if current["ticket"] and current["task"] != task_rel:
        raise ZyesError(f"current 指向另一个正在执行的 ticket: {current['ticket']}")


def validated_date(value: str | None, label: str = "--date") -> date:
    if value is None:
        return date.today()
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ZyesError(f"{label} 必须是有效的 YYYY-MM-DD 日期: {value}") from exc
    if parsed.isoformat() != value:
        raise ZyesError(f"{label} 必须是有效的 YYYY-MM-DD 日期: {value}")
    return parsed


def create_task(
    project_root: Path,
    title: str,
    slug: str,
    created: str | None = None,
) -> dict[str, Any]:
    clean_title = title.strip()
    if not clean_title or "\n" in clean_title or "\r" in clean_title:
        raise ZyesError("task title 必须是非空单行文本")
    if not SLUG_RE.fullmatch(slug):
        raise ZyesError("slug 必须是小写 kebab-case")
    created_date = validated_date(created)
    task_name = f"{created_date.isoformat()}-{slug}"

    with project_write_lock(project_root):
        data = snapshot(project_root)
        if not data["valid"]:
            errors = [*data["errors"]]
            errors.extend(
                f"{task['path']}: {message}"
                for task in data["tasks"]
                for message in task["errors"]
            )
            raise ZyesError("；".join(errors))
        if data["current"]["ticket"]:
            raise ZyesError(f"current 指向正在执行的 ticket: {data['current']['ticket']}")

        tasks_root = project_root / "tasks"
        if tasks_root.exists() and (not tasks_root.is_dir() or not is_within(tasks_root, project_root)):
            raise ZyesError("tasks 必须是 Zyes 项目根目录内的目录")
        task_dir = tasks_root / task_name
        if task_dir.exists() or task_dir.is_symlink():
            raise ZyesError(f"任务目录已存在: {task_dir}")
        task_rel = f"tasks/{task_name}"
        task_text = (
            f"# {clean_title}\n\n"
            "Status: `planning`\n"
            f"Created: `{created_date.isoformat()}`\n"
            "Planning revision: `1`\n"
        )
        spec_text = (
            f"# {clean_title}\n\n"
            "Format version: `2`\n\n"
            "## Problem Statement\n\n<要解决的问题>\n\n"
            "## Solution\n\n<解决方案>\n\n"
            "## User Stories\n\n<用户故事>\n\n"
            "## Acceptance Criteria\n\n- AC-001: <可观察的验收条件>\n\n"
            "## Decisions\n\n- D-001: <已确认的实现决定>\n\n"
            "## Testing Decisions\n\n<测试 seam 与策略>\n\n"
            "## Risks and Deferred Items\n\nnone\n\n"
            "## Out of Scope\n\nnone\n\n"
            "## Further Notes\n\nnone\n"
        )

        with StateTransaction() as transaction:
            transaction.write_text(task_dir / "task.md", task_text)
            transaction.write_text(task_dir / "spec.md", spec_text)
            write_current(project_root, task_rel, None, transaction)
            payload = command_payload(project_root, task_dir, {"created": task_name})
            ensure_command_payload_valid("create-task", payload)
            transaction.commit()
            return payload


def ready_task(project_root: Path, task_selector: str) -> dict[str, Any]:
    with project_write_lock(project_root):
        task_dir = select_task_dir(project_root, task_selector)
        data, task = ensure_valid_selected_task(project_root, task_dir)
        if task["status"] != "planning":
            raise ZyesError("只有 planning task 可以发布为 ready")
        if not task["tickets"]["total"] or not task["frontier"]:
            raise ZyesError("task 必须包含有效 tickets 和至少一个 frontier 才能发布")
        task_rel = task_relative_path(task_dir, project_root)
        ensure_no_other_current_ticket(data["current"], task_rel)
        with StateTransaction() as transaction:
            replace_single_status(task_dir / "task.md", "ready", transaction)
            write_current(project_root, task_rel, None, transaction)
            payload = command_payload(project_root, task_dir, {"task_status": "ready"})
            ensure_command_payload_valid("ready-task", payload)
            transaction.commit()
            return payload


def reopen_planning(project_root: Path, task_selector: str) -> dict[str, Any]:
    with project_write_lock(project_root):
        task_dir = select_task_dir(project_root, task_selector)
        data, task = ensure_valid_selected_task(project_root, task_dir)
        if task["status"] != "ready":
            raise ZyesError("只有尚未开始实现的 ready task 可以退回 planning")
        task_rel = task_relative_path(task_dir, project_root)
        ensure_no_other_current_ticket(data["current"], task_rel)
        with StateTransaction() as transaction:
            replace_single_status(task_dir / "task.md", "planning", transaction)
            write_current(project_root, task_rel, None, transaction)
            payload = command_payload(project_root, task_dir, {"task_status": "planning"})
            ensure_command_payload_valid("reopen-planning", payload)
            transaction.commit()
            return payload


def start_ticket(project_root: Path, task_selector: str, ticket_selector: str | None) -> dict[str, Any]:
    with project_write_lock(project_root):
        task_dir = select_task_dir(project_root, task_selector)
        data, task = ensure_valid_selected_task(project_root, task_dir)
        current = data["current"]
        task_rel = task_relative_path(task_dir, project_root)
        tickets = parsed_tickets(task_dir, project_root)
        if task["status"] not in {"ready", "in-progress"}:
            raise ZyesError("只有 ready 或 in-progress task 可以开始 ticket")
        ensure_no_other_current_ticket(current, task_rel)
        if current["ticket"] and current["task"] == task_rel:
            active_ticket = Path(current["ticket"]).stem
            if ticket_selector and select_ticket_path(project_root, task_dir, ticket_selector).stem != active_ticket:
                raise ZyesError(f"current 已指向另一个 in-progress ticket: {active_ticket}")
            return command_payload(project_root, task_dir, {"started": active_ticket, "changed": False})

        in_progress = [ticket_id for ticket_id, ticket in tickets.items() if ticket["status"] == "in-progress"]
        if in_progress:
            raise ZyesError(f"存在未被 current 指向的 in-progress ticket: {', '.join(in_progress)}")
        if not task["frontier"]:
            raise ZyesError("当前没有可开始的 frontier ticket")

        if ticket_selector:
            ticket_path = select_ticket_path(project_root, task_dir, ticket_selector)
            target = ticket_path.stem
            if target not in task["frontier"]:
                raise ZyesError(f"指定 ticket 不是 frontier: {target}")
        else:
            target = task["frontier"][0]
            ticket_path = select_ticket_path(project_root, task_dir, target)

        with StateTransaction() as transaction:
            replace_single_status(ticket_path, "in-progress", transaction)
            replace_single_status(task_dir / "task.md", "in-progress", transaction)
            write_current(
                project_root,
                task_rel,
                ticket_relative_path(ticket_path, project_root),
                transaction,
            )
            payload = command_payload(project_root, task_dir, {"started": target, "changed": True})
            ensure_command_payload_valid("start-ticket", payload)
            transaction.commit()
            return payload


def complete_ticket(project_root: Path, task_selector: str, ticket_selector: str) -> dict[str, Any]:
    with project_write_lock(project_root):
        task_dir = select_task_dir(project_root, task_selector)
        data, task = ensure_valid_selected_task(project_root, task_dir)
        current = data["current"]
        task_rel = task_relative_path(task_dir, project_root)
        ticket_path = select_ticket_path(project_root, task_dir, ticket_selector)
        ticket = parse_ticket(ticket_path, project_root)
        if task["status"] != "in-progress" or ticket["status"] != "in-progress":
            raise ZyesError("只能完成 in-progress task 中的 in-progress ticket")
        expected_ticket_rel = ticket_relative_path(ticket_path, project_root)
        if current["task"] != task_rel or current["ticket"] != expected_ticket_rel:
            raise ZyesError("current 必须指向待完成的 in-progress ticket")
        completion_errors = ticket_completion_errors(ticket_path)
        if completion_errors:
            raise ZyesError("；".join(completion_errors))

        with StateTransaction() as transaction:
            replace_single_status(ticket_path, "completed", transaction)
            tickets_after = parsed_tickets(task_dir, project_root)
            all_completed = bool(tickets_after) and all(
                item["status"] == "completed" for item in tickets_after.values()
            )
            replace_single_status(
                task_dir / "task.md",
                "verifying" if all_completed else "in-progress",
                transaction,
            )
            write_current(project_root, task_rel, None, transaction)
            payload = command_payload(
                project_root,
                task_dir,
                {
                    "completed": ticket_path.stem,
                    "task_status": "verifying" if all_completed else "in-progress",
                },
            )
            ensure_command_payload_valid("complete-ticket", payload)
            transaction.commit()
            return payload


def release_task_ticket(
    project_root: Path,
    task_dir: Path,
    current: dict[str, Any],
    transaction: StateTransaction,
) -> str | None:
    task_rel = task_relative_path(task_dir, project_root)
    tickets = parsed_tickets(task_dir, project_root)
    in_progress = [ticket_id for ticket_id, ticket in tickets.items() if ticket["status"] == "in-progress"]
    released: str | None = None
    if in_progress:
        if len(in_progress) != 1:
            raise ZyesError("任务必须最多包含一个 in-progress ticket")
        released = in_progress[0]
        ticket_path = select_ticket_path(project_root, task_dir, released)
        replace_single_status(ticket_path, "ready", transaction)
    if current["task"] == task_rel:
        write_current(project_root, task_rel, None, transaction)
    return released


def validate_replacement_target(project_root: Path, task_dir: Path, replacement: str) -> None:
    if not TASK_DIR_RE.fullmatch(replacement):
        raise ZyesError("replacement 必须是 `YYYY-MM-DD-<slug>` task 标识")
    if replacement == task_dir.name:
        raise ZyesError("task 不能 supersede 自身")
    active_target = project_root / "tasks" / replacement
    archived_targets = [
        target
        for target in (project_root / "archive").glob(f"*/{replacement}")
        if re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", target.parent.name)
    ]
    matches = [target for target in (active_target, *archived_targets) if target.is_dir()]
    if any(not is_within(target, project_root) for target in matches):
        raise ZyesError("Superseded by 目标通过符号链接解析到 Zyes 项目根目录之外")
    if len(matches) != 1:
        raise ZyesError(f"Superseded by 必须唯一指向 active 或 archived task: {replacement}")
    replacement_task = matches[0] / "task.md"
    if not replacement_task.is_file() or not is_within(replacement_task, project_root):
        raise ZyesError(f"Superseded by 目标缺少可访问的 task.md: {replacement}")


def cancel_task(project_root: Path, task_selector: str, reason: str) -> dict[str, Any]:
    clean_reason = reason.strip()
    if not clean_reason or "\n" in clean_reason or "\r" in clean_reason or clean_reason.startswith("<"):
        raise ZyesError("取消任务必须提供非空单行 reason")
    with project_write_lock(project_root):
        task_dir = select_task_dir(project_root, task_selector)
        data, task = ensure_valid_selected_task(project_root, task_dir)
        if task["status"] in TERMINAL_TASK_STATUSES and task["status"] != "cancelled":
            raise ZyesError(f"不能取消已经处于 {task['status']} 的任务")
        with StateTransaction() as transaction:
            released = release_task_ticket(project_root, task_dir, data["current"], transaction)
            replace_single_status(task_dir / "task.md", "cancelled", transaction)
            set_task_line(
                task_dir / "task.md",
                CANCEL_REASON_RE,
                f"Reason: {clean_reason}",
                "Reason",
                transaction,
            )
            payload = command_payload(
                project_root,
                task_dir,
                {"cancelled": task_dir.name, "released": released},
            )
            ensure_command_payload_valid("cancel-task", payload)
            transaction.commit()
            return payload


def supersede_task(project_root: Path, task_selector: str, replacement: str) -> dict[str, Any]:
    with project_write_lock(project_root):
        task_dir = select_task_dir(project_root, task_selector)
        data, task = ensure_valid_selected_task(project_root, task_dir)
        if task["status"] in TERMINAL_TASK_STATUSES and task["status"] != "superseded":
            raise ZyesError(f"不能替代已经处于 {task['status']} 的任务")
        validate_replacement_target(project_root, task_dir, replacement)
        with StateTransaction() as transaction:
            released = release_task_ticket(project_root, task_dir, data["current"], transaction)
            replace_single_status(task_dir / "task.md", "superseded", transaction)
            set_task_line(
                task_dir / "task.md",
                SUPERSEDED_BY_RE,
                f"Superseded by: `{replacement}`",
                "Superseded by",
                transaction,
            )
            payload = command_payload(
                project_root,
                task_dir,
                {
                    "superseded": task_dir.name,
                    "superseded_by": replacement,
                    "released": released,
                },
            )
            ensure_command_payload_valid("supersede-task", payload)
            transaction.commit()
            return payload


def resolve_rework_draft(project_root: Path, selector: str) -> Path:
    if "\\" in selector:
        raise ZyesError("ticket draft 必须使用 POSIX 路径")
    raw = PurePosixPath(selector)
    if ".." in raw.parts:
        raise ZyesError("ticket draft 路径不能包含 ..")
    scratch_dir = project_root / "scratch"
    if (
        not scratch_dir.is_dir()
        or scratch_dir.is_symlink()
        or not is_within(scratch_dir, project_root)
    ):
        raise ZyesError("scratch 必须是 Zyes 项目根目录内的普通目录")
    candidate = Path(selector) if Path(selector).is_absolute() else project_root.joinpath(*raw.parts)
    if candidate.is_symlink():
        raise ZyesError(f"ticket draft 不能是符号链接: {candidate}")
    draft = candidate.resolve()
    scratch_root = scratch_dir.resolve()
    if not is_within(draft, scratch_root):
        raise ZyesError("ticket draft 必须位于 <ZYES_PROJECT_ROOT>/scratch/ 内")
    if not draft.is_file() or draft.is_symlink():
        raise ZyesError(f"ticket draft 不存在、不是普通文件或是符号链接: {draft}")
    if not TICKET_FILE_RE.fullmatch(draft.name):
        raise ZyesError("ticket draft 文件名必须是 `<NN>-<slug>.md`")
    return draft


def request_changes(project_root: Path, task_selector: str, draft_selector: str) -> dict[str, Any]:
    with project_write_lock(project_root):
        task_dir = select_task_dir(project_root, task_selector)
        data, task = ensure_valid_selected_task(project_root, task_dir)
        if task["status"] != "verifying" or not task["result_exists"]:
            raise ZyesError("只有已经写入 result.md 的 verifying task 可以创建返工 ticket")
        draft = resolve_rework_draft(project_root, draft_selector)
        parsed_draft = parse_ticket(
            draft,
            project_root,
            task["format_version"],
            set(task["spec_ref_ids"]),
        )
        if parsed_draft["errors"] or parsed_draft["status"] != "ready":
            details = parsed_draft["errors"] or ["ticket draft 的 Status 必须是 ready"]
            raise ZyesError("；".join(details))
        destination = task_dir / "tickets" / draft.name
        if destination.exists() or destination.is_symlink():
            raise ZyesError(f"返工 ticket 已存在: {destination}")
        task_rel = task_relative_path(task_dir, project_root)
        ensure_no_other_current_ticket(data["current"], task_rel)
        with StateTransaction() as transaction:
            transaction.move(draft, destination)
            replace_single_status(task_dir / "task.md", "in-progress", transaction)
            write_current(project_root, task_rel, None, transaction)
            payload = command_payload(
                project_root,
                task_dir,
                {"task_status": "in-progress", "rework_ticket": destination.stem},
            )
            ensure_command_payload_valid("request-changes", payload)
            transaction.commit()
            return payload


def reverify_task(project_root: Path, task_selector: str) -> dict[str, Any]:
    with project_write_lock(project_root):
        task_dir = select_task_dir(project_root, task_selector)
        _, task = ensure_valid_selected_task(project_root, task_dir)
        if task["status"] != "completed" or not task["result_exists"]:
            raise ZyesError("只有具有 result.md 的 completed task 可以重新验收")
        with StateTransaction() as transaction:
            replace_single_status(task_dir / "task.md", "verifying", transaction)
            payload = command_payload(project_root, task_dir, {"task_status": "verifying"})
            ensure_command_payload_valid("reverify-task", payload)
            transaction.commit()
            return payload


def accept_task(project_root: Path, task_selector: str) -> dict[str, Any]:
    with project_write_lock(project_root):
        task_dir = select_task_dir(project_root, task_selector)
        _, task = ensure_valid_selected_task(project_root, task_dir)
        if task["status"] != "verifying" or not task["result_exists"]:
            raise ZyesError("只有已经写入完整 result.md 的 verifying task 可以接受")
        with StateTransaction() as transaction:
            replace_single_status(task_dir / "task.md", "completed", transaction)
            payload = command_payload(project_root, task_dir, {"task_status": "completed"})
            ensure_command_payload_valid("accept-task", payload)
            transaction.commit()
            return payload


def archive_task(project_root: Path, task_selector: str, archive_date: str | None = None) -> dict[str, Any]:
    with project_write_lock(project_root):
        task_dir = select_task_dir(project_root, task_selector)
        data, task = ensure_valid_selected_task(project_root, task_dir)
        if task["status"] not in TERMINAL_TASK_STATUSES:
            raise ZyesError("只有 completed、cancelled 或 superseded task 可以归档")
        month_source = validated_date(archive_date)
        archive_rel = PurePosixPath("archive") / month_source.strftime("%Y-%m") / task_dir.name
        archive_dir = project_root.joinpath(*archive_rel.parts)
        if task_dir.parent != (project_root / "tasks").resolve():
            raise ZyesError("归档源必须是 tasks/ 的直接子目录")
        if archive_dir.exists() or archive_dir.is_symlink():
            raise ZyesError(f"归档目标已存在: {archive_dir}")
        if not is_within(archive_dir.parent, project_root):
            raise ZyesError("归档目标解析到 Zyes 项目根目录之外")
        current = data["current"]
        task_rel = task_relative_path(task_dir, project_root)
        with StateTransaction() as transaction:
            transaction.move(task_dir, archive_dir)
            if current["task"] == task_rel:
                write_current(project_root, None, None, transaction)
            archived_task = parse_task(archive_dir, project_root, archived=True)
            current_after = parse_current(project_root)
            errors = [*archived_task["errors"], *current_after["errors"]]
            if current_after["task"] == task_rel:
                errors.append("current 指针仍指向已归档任务")
            if errors:
                raise ZyesError("archive-task 后状态校验失败：" + "；".join(errors))
            transaction.commit()
            return {
                "valid": True,
                "archived": archive_rel.as_posix(),
                "task": archived_task,
                "current": current_after,
                "errors": [],
            }


def bump_revision(project_root: Path, task_selector: str) -> dict[str, Any]:
    with project_write_lock(project_root):
        task_dir = select_task_dir(project_root, task_selector)
        _, task = ensure_valid_selected_task(project_root, task_dir)
        if task["status"] != "planning":
            raise ZyesError("只有 planning task 可以递增 Planning revision")
        with StateTransaction() as transaction:
            revision = bump_planning_revision(task_dir / "task.md", transaction)
            payload = command_payload(project_root, task_dir, {"planning_revision": revision})
            ensure_command_payload_valid("bump-revision", payload)
            transaction.commit()
            return payload


def emit_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def print_task_table(tasks: list[dict[str, Any]]) -> None:
    print("CURRENT\tSTATUS\tTICKETS\tFRONTIER\tTASK\tPATH")
    for task in tasks:
        tickets = task["tickets"]
        progress = f"{tickets['completed']}/{tickets['total']}"
        print(
            "\t".join(
                (
                    "yes" if task["current"] else "",
                    task["status"] or "invalid",
                    progress,
                    ",".join(task["frontier"]) or "none",
                    task["title"] or "<invalid>",
                    task["path"],
                )
            )
        )
        for error in task["errors"]:
            print(f"ERROR\t{task['path']}\t{error}")
        for warning in task["warnings"]:
            print(f"WARN\t{task['path']}\t{warning}")


def print_list(data: dict[str, Any]) -> None:
    if data["errors"]:
        for error in data["errors"]:
            print(f"ERROR\t{error}")
    if data["tasks"]:
        print_task_table(data["tasks"])
    else:
        print("当前没有未归档任务")
    if data["archive"]:
        print("\nARCHIVE")
        print_task_table(data["archive"])


def print_validation(data: dict[str, Any], verbose: bool = False) -> None:
    if data["valid"]:
        print("Zyes 状态有效")
    else:
        for error in data["errors"]:
            print(f"ERROR\t{error}")
    for task in data["tasks"]:
        for error in task["errors"]:
            print(f"ERROR\t{task['path']}\t{error}")
        if verbose:
            for warning in task["warnings"]:
                print(f"WARN\t{task['path']}\t{warning}")


def validation_output(data: dict[str, Any], verbose: bool = False) -> dict[str, Any]:
    if verbose:
        return data
    compact = dict(data)
    compact["tasks"] = [
        {key: value for key, value in task.items() if key != "warnings"}
        for task in data["tasks"]
    ]
    compact["archive"] = [
        {key: value for key, value in task.items() if key != "warnings"}
        for task in data["archive"]
    ]
    return compact


def add_resolution_args(parser: argparse.ArgumentParser, include_json: bool = True) -> None:
    parser.add_argument("--project-root", help="直接指定已解析的 Zyes 项目根目录")
    parser.add_argument("--repo", default=".", help="用于解析 Zyes 配置的仓库路径")
    parser.add_argument("--zyes-home", help="external 模式的 Zyes home 绝对路径")
    parser.add_argument("--global-instructions", help="包含 Zyes home 受控块的全局 AGENTS.md 或 CLAUDE.md")
    if include_json:
        parser.add_argument("--json", action="store_true", help="以 JSON 输出")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    root_parser = subparsers.add_parser("root", help="解析唯一的 Zyes 项目根目录")
    root_parser.add_argument("--repo", default=".")
    root_parser.add_argument("--zyes-home")
    root_parser.add_argument("--global-instructions")
    root_parser.add_argument("--json", action="store_true")

    context_parser = subparsers.add_parser("context", help="输出入口当前 action 的最小任务上下文")
    add_resolution_args(context_parser, include_json=False)
    context_parser.add_argument("--entry", required=True, choices=tuple(ENTRY_STATUSES))
    context_parser.add_argument("--task", help="指定 active task 的目录名或相对路径")
    context_parser.add_argument("--verbose", action="store_true", help="包含完整候选、文件和 warning 诊断")
    context_parser.add_argument(
        "--format",
        choices=("json", "prompt"),
        default="json",
        help="action contract 输出格式",
    )

    validate_parser = subparsers.add_parser("validate", help="校验任务、ticket、result 和 current 状态")
    add_resolution_args(validate_parser)
    validate_parser.add_argument("--task", help="只校验一个 active task 的目录名或相对路径")
    validate_parser.add_argument("--verbose", action="store_true", help="包含非阻塞 warning 诊断")

    frontier_parser = subparsers.add_parser("frontier", help="计算指定任务当前可执行的 tickets")
    add_resolution_args(frontier_parser)
    frontier_parser.add_argument("--task", required=True, help="active task 的目录名或相对路径")

    list_parser = subparsers.add_parser("list", help="列出 active tasks 和状态摘要")
    add_resolution_args(list_parser)
    list_parser.add_argument("--archive", action="store_true", help="同时读取归档任务")

    create_parser = subparsers.add_parser("create-task", help="创建 planning task 和初始 spec")
    add_resolution_args(create_parser)
    create_parser.add_argument("--title", required=True, help="task 标题")
    create_parser.add_argument("--slug", required=True, help="小写 kebab-case task slug")
    create_parser.add_argument("--date", dest="created", help="创建日期 YYYY-MM-DD；默认今天")

    ready_parser = subparsers.add_parser("ready-task", help="校验并发布 planning task")
    add_resolution_args(ready_parser)
    ready_parser.add_argument("--task", required=True, help="planning task 的目录名或相对路径")

    reopen_parser = subparsers.add_parser("reopen-planning", help="将未开始的 ready task 退回 planning")
    add_resolution_args(reopen_parser)
    reopen_parser.add_argument("--task", required=True, help="ready task 的目录名或相对路径")

    start_parser = subparsers.add_parser("start-ticket", help="开始一个 frontier ticket")
    add_resolution_args(start_parser)
    start_parser.add_argument("--task", required=True, help="active task 的目录名或相对路径")
    start_parser.add_argument("--ticket", help="要开始的 ticket 标识或路径；省略则选 frontier 最小项")

    complete_parser = subparsers.add_parser("complete-ticket", help="完成一个 in-progress ticket")
    add_resolution_args(complete_parser)
    complete_parser.add_argument("--task", required=True, help="active task 的目录名或相对路径")
    complete_parser.add_argument("--ticket", required=True, help="要完成的 ticket 标识或路径")

    changes_parser = subparsers.add_parser("request-changes", help="从 scratch 导入返工 ticket")
    add_resolution_args(changes_parser)
    changes_parser.add_argument("--task", required=True, help="verifying task 的目录名或相对路径")
    changes_parser.add_argument(
        "--ticket-draft",
        required=True,
        help="位于 <ZYES_PROJECT_ROOT>/scratch/ 内的完整 ready ticket 文件",
    )

    reverify_parser = subparsers.add_parser("reverify-task", help="重新验收 completed task")
    add_resolution_args(reverify_parser)
    reverify_parser.add_argument("--task", required=True, help="completed task 的目录名或相对路径")

    accept_parser = subparsers.add_parser("accept-task", help="接受已经完成验收的 task")
    add_resolution_args(accept_parser)
    accept_parser.add_argument("--task", required=True, help="verifying task 的目录名或相对路径")

    cancel_parser = subparsers.add_parser("cancel-task", help="取消一个任务")
    add_resolution_args(cancel_parser)
    cancel_parser.add_argument("--task", required=True, help="active task 的目录名或相对路径")
    cancel_parser.add_argument("--reason", required=True, help="取消原因")

    supersede_parser = subparsers.add_parser("supersede-task", help="将一个任务标记为 superseded")
    add_resolution_args(supersede_parser)
    supersede_parser.add_argument("--task", required=True, help="active task 的目录名或相对路径")
    supersede_parser.add_argument("--replacement", required=True, help="承接该需求的新 task 标识")

    archive_parser = subparsers.add_parser("archive-task", help="归档一个终态任务")
    add_resolution_args(archive_parser)
    archive_parser.add_argument("--task", required=True, help="active task 的目录名或相对路径")
    archive_parser.add_argument("--date", dest="archive_date", help="归档日期 YYYY-MM-DD；默认今天")

    revision_parser = subparsers.add_parser("bump-revision", help="递增 planning revision")
    add_resolution_args(revision_parser)
    revision_parser.add_argument("--task", required=True, help="planning task 的目录名或相对路径")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "root":
            config = resolve_project_root(
                Path(args.repo),
                Path(args.zyes_home) if args.zyes_home else None,
                Path(args.global_instructions) if args.global_instructions else None,
            )
            if args.json:
                emit_json(config)
            else:
                print(config["project_root"])
            return 0

        project_root = project_root_from_args(args)
        if args.command == "context":
            data = entry_context(project_root, args.entry, args.task, verbose=args.verbose)
            if args.format == "prompt":
                print(render_entry_prompt(data))
            else:
                emit_json(data)
            return 0 if data["valid"] else 1
        if args.command == "validate":
            data = snapshot(project_root, args.task)
            output = validation_output(data, verbose=args.verbose)
            emit_json(output) if args.json else print_validation(data, verbose=args.verbose)
            return 0 if data["valid"] else 1
        if args.command == "frontier":
            data = snapshot(project_root, args.task)
            task = data["tasks"][0]
            if args.json:
                emit_json(
                    {
                        "task": task["path"],
                        "frontier": task["frontier"],
                        "errors": [*data["errors"], *task["errors"]],
                        "warnings": task["warnings"],
                    }
                )
            elif not data["valid"]:
                print_validation(data)
            else:
                print("\n".join(task["frontier"]) if task["frontier"] else "none")
            return 0 if data["valid"] else 1
        if args.command == "list":
            data = snapshot(project_root, include_archive=args.archive)
            emit_json(data) if args.json else print_list(data)
            return 0 if data["valid"] else 1
        if args.command == "create-task":
            data = create_task(project_root, args.title, args.slug, args.created)
            emit_json(data) if args.json else print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "ready-task":
            data = ready_task(project_root, args.task)
            emit_json(data) if args.json else print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "reopen-planning":
            data = reopen_planning(project_root, args.task)
            emit_json(data) if args.json else print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "start-ticket":
            data = start_ticket(project_root, args.task, args.ticket)
            emit_json(data) if args.json else print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "complete-ticket":
            data = complete_ticket(project_root, args.task, args.ticket)
            emit_json(data) if args.json else print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "request-changes":
            data = request_changes(project_root, args.task, args.ticket_draft)
            emit_json(data) if args.json else print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "reverify-task":
            data = reverify_task(project_root, args.task)
            emit_json(data) if args.json else print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "accept-task":
            data = accept_task(project_root, args.task)
            emit_json(data) if args.json else print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "cancel-task":
            data = cancel_task(project_root, args.task, args.reason)
            emit_json(data) if args.json else print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "supersede-task":
            data = supersede_task(project_root, args.task, args.replacement)
            emit_json(data) if args.json else print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "archive-task":
            data = archive_task(project_root, args.task, args.archive_date)
            emit_json(data) if args.json else print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "bump-revision":
            data = bump_revision(project_root, args.task)
            emit_json(data) if args.json else print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        raise ZyesError(f"未知命令: {args.command}")
    except ZyesError as exc:
        wants_json = getattr(args, "json", False) or (
            args.command == "context" and getattr(args, "format", None) == "json"
        )
        if wants_json:
            emit_json({"valid": False, "errors": [str(exc)]})
        else:
            print(f"ERROR\t{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
