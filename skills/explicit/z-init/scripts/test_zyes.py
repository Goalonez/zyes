#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).with_name("zyes.py")
SPEC = importlib.util.spec_from_file_location("zyes_protocol", SCRIPT_PATH)
assert SPEC and SPEC.loader
zyes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(zyes)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def task_file(title: str, status: str, created: str = "2026-07-23") -> str:
    return f"# {title}\n\nStatus: `{status}`\nCreated: `{created}`\nPlanning revision: `1`\n"


def ticket_file(title: str, status: str, blocked_by: str, completed: bool = False) -> str:
    checked = "x" if completed else " "
    result = "已完成实现。" if completed else "<完成后记录实际实现；开始前保持为空>"
    verification = "测试通过。" if completed else "<完成后记录实际执行的检查及结果；未执行项写明原因>"
    return (
        f"# {title}\n\n"
        f"Status: `{status}`\n"
        f"Blocked by: `{blocked_by}`\n\n"
        "## What to build\n\n交付一个可观察结果。\n\n"
        f"## Acceptance Criteria\n\n- [{checked}] 行为可验证\n\n"
        f"## Result\n\n{result}\n\n"
        f"## Verification\n\n{verification}\n"
    )


def result_file() -> str:
    return (
        "# 验收结果\n\n"
        "## Delivered\n\n已交付。\n\n"
        "## Verification\n\n测试通过。\n\n"
        "## Review Findings\n\nnone\n\n"
        "## Remaining Work\n\nnone\n"
    )


def spec_file(title: str = "任务") -> str:
    return (
        f"# {title}\n\n"
        "## Problem Statement\n\n需要解决一个问题。\n\n"
        "## Solution\n\n交付一个可观察结果。\n\n"
        "## User Stories\n\n1. 用户可以完成目标行为。\n\n"
        "## Acceptance Criteria\n\n- 行为可验证。\n\n"
        "## Implementation Decisions\n\n遵循现有实现模式。\n\n"
        "## Testing Decisions\n\n通过公共 seam 验证。\n\n"
        "## Risks and Deferred Items\n\nnone\n\n"
        "## Out of Scope\n\nnone\n\n"
        "## Further Notes\n\nnone\n"
    )


def spec_file_v2(title: str = "任务", include_second_acceptance: bool = False) -> str:
    acceptance = "- AC-001: 用户可以完成目标行为。\n"
    if include_second_acceptance:
        acceptance += "- AC-002: 重新进入后行为仍然成立。\n"
    return (
        f"# {title}\n\n"
        "Format version: `2`\n\n"
        "## Problem Statement\n\n需要解决一个问题。\n\n"
        "## Solution\n\n交付一个可观察结果。\n\n"
        "## User Stories\n\n1. 用户可以完成目标行为。\n\n"
        f"## Acceptance Criteria\n\n{acceptance}\n"
        "## Decisions\n\n- D-001: 遵循现有实现模式。\n\n"
        "## Testing Decisions\n\n通过公共 seam 验证。\n\n"
        "## Risks and Deferred Items\n\nnone\n\n"
        "## Out of Scope\n\n不改变其他行为。\n\n"
        "## Further Notes\n\nnone\n"
    )


def ticket_file_v2(
    title: str,
    status: str,
    blocked_by: str,
    spec_refs: tuple[str, ...],
    completed: bool = False,
) -> str:
    refs = ", ".join(f"`{ref}`" for ref in spec_refs)
    return ticket_file(title, status, blocked_by, completed).replace(
        f"Status: `{status}`\n",
        f"Status: `{status}`\nSpec refs: {refs}\n",
        1,
    )


class ZyesProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.base = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def create_repo(self, block: str) -> Path:
        repo = self.base / "repo"
        (repo / ".git").mkdir(parents=True)
        write(repo / "AGENTS.md", block)
        return repo

    def create_valid_task(self, root: Path) -> Path:
        task = root / "tasks/2026-07-23-theme-switch"
        write(task / "task.md", task_file("主题切换", "in-progress"))
        write(task / "spec.md", spec_file("主题切换"))
        write(task / "tickets/01-add-state.md", ticket_file("01 — 添加状态", "completed", "none", True))
        write(task / "tickets/02-add-ui.md", ticket_file("02 — 添加界面", "ready", "01-add-state"))
        write(
            root / "runtime/current.yaml",
            "task: tasks/2026-07-23-theme-switch\nticket: null\n",
        )
        return task

    def test_resolve_shared_root(self) -> None:
        repo = self.create_repo(
            "<!-- zyes:start -->\n## Zyes workflow\n\n- Mode: `shared`\n- Root: `.zyes`\n<!-- zyes:end -->\n"
        )
        (repo / ".zyes").mkdir()
        result = zyes.resolve_project_root(repo)
        self.assertEqual(result["mode"], "shared")
        self.assertEqual(Path(result["project_root"]), (repo / ".zyes").resolve())
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = zyes.main(["root", "--repo", str(repo), "--json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(Path(json.loads(output.getvalue())["project_root"]), (repo / ".zyes").resolve())

    def test_resolve_external_root_from_global_instructions(self) -> None:
        repo = self.create_repo(
            "<!-- zyes:start -->\n## Zyes workflow\n\n- Mode: `external`\n- Project: `demo-project`\n<!-- zyes:end -->\n"
        )
        home = self.base / "zyes-home"
        (home / "demo-project").mkdir(parents=True)
        global_file = self.base / "AGENTS.md"
        write(
            global_file,
            f"<!-- zyes-home:start -->\n## Zyes home\n\nZyes 外置工作流根目录：`{home}`。\n<!-- zyes-home:end -->\n",
        )
        result = zyes.resolve_project_root(repo, global_instructions=global_file)
        self.assertEqual(Path(result["project_root"]), (home / "demo-project").resolve())
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = zyes.main(
                [
                    "root",
                    "--repo",
                    str(repo),
                    "--global-instructions",
                    str(global_file),
                    "--json",
                ]
            )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            Path(json.loads(output.getvalue())["project_root"]),
            (home / "demo-project").resolve(),
        )

    def test_resolve_external_root_from_zyes_home(self) -> None:
        repo = self.create_repo(
            "<!-- zyes:start -->\n## Zyes workflow\n\n- Mode: `external`\n- Project: `demo-project`\n<!-- zyes:end -->\n"
        )
        home = self.base / "zyes-home"
        (home / "demo-project").mkdir(parents=True)

        result = zyes.resolve_project_root(repo, zyes_home=home.resolve())

        self.assertEqual(Path(result["project_root"]), (home / "demo-project").resolve())
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = zyes.main(
                [
                    "root",
                    "--repo",
                    str(repo),
                    "--zyes-home",
                    str(home.resolve()),
                    "--json",
                ]
            )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            Path(json.loads(output.getvalue())["project_root"]),
            (home / "demo-project").resolve(),
        )

    def test_external_resolution_arguments_conflict(self) -> None:
        repo = self.create_repo(
            "<!-- zyes:start -->\n## Zyes workflow\n\n- Mode: `external`\n- Project: `demo-project`\n<!-- zyes:end -->\n"
        )
        home = self.base / "zyes-home"
        (home / "demo-project").mkdir(parents=True)
        global_file = self.base / "AGENTS.md"
        write(
            global_file,
            f"<!-- zyes-home:start -->\n## Zyes home\n\nZyes 外置工作流根目录：`{home}`。\n<!-- zyes-home:end -->\n",
        )

        with self.assertRaisesRegex(zyes.ZyesError, "只能使用一个"):
            zyes.resolve_project_root(
                repo,
                zyes_home=home.resolve(),
                global_instructions=global_file,
            )
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = zyes.main(
                [
                    "root",
                    "--repo",
                    str(repo),
                    "--zyes-home",
                    str(home.resolve()),
                    "--global-instructions",
                    str(global_file),
                    "--json",
                ]
            )
        self.assertEqual(exit_code, 2)
        self.assertIn("只能使用一个", json.loads(output.getvalue())["errors"][0])

    def test_external_home_must_be_absolute(self) -> None:
        repo = self.create_repo(
            "<!-- zyes:start -->\n## Zyes workflow\n\n- Mode: `external`\n- Project: `demo-project`\n<!-- zyes:end -->\n"
        )
        with self.assertRaisesRegex(zyes.ZyesError, "必须是绝对路径"):
            zyes.resolve_project_root(repo, zyes_home=Path("relative-home"))
        with self.assertRaisesRegex(zyes.ZyesError, "必须是绝对路径"):
            zyes.resolve_project_root(repo, zyes_home=Path("~/relative-home"))

    def test_workflow_keys_must_be_unique(self) -> None:
        repo = self.create_repo(
            "<!-- zyes:start -->\n## Zyes workflow\n\n"
            "- Mode: `shared`\n- Mode: `external`\n- Root: `.zyes`\n"
            "<!-- zyes:end -->\n"
        )
        (repo / ".zyes").mkdir()
        with self.assertRaisesRegex(zyes.ZyesError, "Mode 必须且只能出现一次"):
            zyes.resolve_project_root(repo)

    def test_valid_task_and_frontier(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        self.create_valid_task(root)
        result = zyes.snapshot(root)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["tasks"][0]["frontier"], ["02-add-ui"])
        self.assertEqual(result["tasks"][0]["tickets"]["completed"], 1)
        self.assertEqual(result["tasks"][0]["planning_revision"], 1)

    def test_task_requires_planning_revision(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-missing-revision"
        write(
            task / "task.md",
            "# 缺少 revision\n\nStatus: `planning`\nCreated: `2026-07-23`\n",
        )
        write(task / "spec.md", "# 缺少 revision\n")
        result = zyes.snapshot(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Planning revision" in error for error in result["tasks"][0]["errors"]))

    def test_bump_revision_updates_task(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-planning"
        write(task / "task.md", task_file("规划任务", "planning"))
        write(task / "spec.md", "# 规划任务\n")

        payload = zyes.bump_revision(root, task.name)

        self.assertTrue(payload["valid"], payload)
        self.assertEqual(payload["planning_revision"], 2)
        self.assertIn("Planning revision: `2`", (task / "task.md").read_text(encoding="utf-8"))

    def test_bump_revision_rejects_non_planning_task(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = self.create_valid_task(root)
        before = (task / "task.md").read_text(encoding="utf-8")

        with self.assertRaisesRegex(zyes.ZyesError, "只有 planning task"):
            zyes.bump_revision(root, task.name)

    def test_create_ready_and_reopen_planning_task(self) -> None:
        root = self.base / "zyes"
        root.mkdir()

        created = zyes.create_task(root, "主题切换", "theme-switch", "2026-07-23")
        task = root / "tasks/2026-07-23-theme-switch"
        self.assertTrue(created["valid"], created)
        self.assertEqual(
            (root / "runtime/current.yaml").read_text(encoding="utf-8"),
            "task: tasks/2026-07-23-theme-switch\nticket: null\n",
        )
        created_spec = (task / "spec.md").read_text(encoding="utf-8")
        self.assertIn("Format version: `2`", created_spec)
        self.assertIn("- AC-001:", created_spec)
        self.assertIn("- D-001:", created_spec)

        write(task / "spec.md", spec_file("主题切换"))
        write(task / "tickets/01-theme.md", ticket_file("01 — 主题", "ready", "none"))
        ready = zyes.ready_task(root, task.name)
        self.assertEqual(ready["task"]["status"], "ready")

        reopened = zyes.reopen_planning(root, task.name)
        self.assertEqual(reopened["task"]["status"], "planning")

    def test_create_task_rolls_back_new_directories_when_validation_fails(self) -> None:
        root = self.base / "zyes"
        root.mkdir()

        with mock.patch.object(
            zyes,
            "ensure_command_payload_valid",
            side_effect=zyes.ZyesError("模拟校验失败"),
        ):
            with self.assertRaisesRegex(zyes.ZyesError, "模拟校验失败"):
                zyes.create_task(root, "需要回滚", "rollback", "2026-07-23")

        self.assertFalse((root / "tasks").exists())
        self.assertFalse((root / "runtime/current.yaml").exists())

    def test_write_lock_rejects_concurrent_command(self) -> None:
        root = self.base / "zyes"
        root.mkdir()

        with zyes.project_write_lock(root):
            with self.assertRaisesRegex(zyes.ZyesError, "另一个 Zyes 写命令"):
                zyes.create_task(root, "锁冲突", "lock-conflict", "2026-07-23")

        self.assertFalse((root / "tasks").exists())

    def test_ready_task_rejects_incomplete_spec_and_missing_tickets(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        incomplete = root / "tasks/2026-07-23-incomplete"
        write(incomplete / "task.md", task_file("规格不完整", "planning"))
        write(incomplete / "spec.md", "# 规格不完整\n")
        write(incomplete / "tickets/01-work.md", ticket_file("01 — 工作", "ready", "none"))

        with self.assertRaisesRegex(zyes.ZyesError, "spec.md 缺少有效"):
            zyes.ready_task(root, incomplete.name)

        no_tickets = root / "tasks/2026-07-23-no-tickets"
        write(no_tickets / "task.md", task_file("没有 tickets", "planning"))
        write(no_tickets / "spec.md", spec_file("没有 tickets"))

        with self.assertRaisesRegex(zyes.ZyesError, "有效 tickets"):
            zyes.ready_task(root, no_tickets.name)

    def test_start_ticket_rolls_back_when_a_later_write_fails(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-rollback"
        write(task / "task.md", task_file("回滚", "ready"))
        write(task / "spec.md", spec_file("回滚"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "ready", "none"))
        write(root / "runtime/current.yaml", f"task: tasks/{task.name}\nticket: null\n")

        original = zyes.atomic_write_bytes
        calls = 0

        def fail_second_write(path: Path, content: bytes, mode: int | None = None) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise zyes.ZyesError("模拟写入失败")
            original(path, content, mode)

        with mock.patch.object(zyes, "atomic_write_bytes", side_effect=fail_second_write):
            with self.assertRaisesRegex(zyes.ZyesError, "模拟写入失败"):
                zyes.start_ticket(root, task.name, "01-work")

        self.assertIn("Status: `ready`", (task / "task.md").read_text(encoding="utf-8"))
        self.assertIn("Status: `ready`", (task / "tickets/01-work.md").read_text(encoding="utf-8"))
        self.assertEqual(
            (root / "runtime/current.yaml").read_text(encoding="utf-8"),
            f"task: tasks/{task.name}\nticket: null\n",
        )

    def test_malformed_status_returns_structured_business_error(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-bad-status"
        write(
            task / "task.md",
            "# 错误状态\n\nStatus: planning\nCreated: `2026-07-23`\nPlanning revision: `1`\n",
        )
        write(task / "spec.md", "# 错误状态\n")
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = zyes.main(
                [
                    "bump-revision",
                    "--project-root",
                    str(root),
                    "--task",
                    task.name,
                    "--json",
                ]
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertFalse(payload["valid"])
        self.assertIn("task Status 必须且只能出现一次", payload["errors"][0])

    def test_start_ticket_sets_task_ticket_and_current(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = self.create_valid_task(root)
        write(task / "task.md", task_file("主题切换", "in-progress"))
        write(task / "tickets/01-add-state.md", ticket_file("01 — 添加状态", "completed", "none", True))
        write(task / "tickets/02-add-ui.md", ticket_file("02 — 添加界面", "ready", "01-add-state"))

        payload = zyes.start_ticket(root, task.name, None)

        self.assertTrue(payload["valid"], payload)
        self.assertTrue(payload["changed"])
        self.assertEqual(payload["started"], "02-add-ui")
        self.assertIn("Status: `in-progress`", (task / "task.md").read_text(encoding="utf-8"))
        self.assertIn("Status: `in-progress`", (task / "tickets/02-add-ui.md").read_text(encoding="utf-8"))
        self.assertEqual(
            (root / "runtime/current.yaml").read_text(encoding="utf-8"),
            f"task: tasks/{task.name}\nticket: tasks/{task.name}/tickets/02-add-ui.md\n",
        )

    def test_complete_ticket_moves_to_verifying_when_last_ticket_done(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-one-ticket"
        write(task / "task.md", task_file("单 ticket", "in-progress"))
        write(task / "spec.md", spec_file("单 ticket"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "in-progress", "none", True))
        write(task / "result.md", result_file())
        write(
            root / "runtime/current.yaml",
            f"task: tasks/{task.name}\nticket: tasks/{task.name}/tickets/01-work.md\n",
        )

        payload = zyes.complete_ticket(root, task.name, "01-work")

        self.assertTrue(payload["valid"], payload)
        self.assertEqual(payload["task_status"], "verifying")
        self.assertIn("Status: `verifying`", (task / "task.md").read_text(encoding="utf-8"))
        self.assertIn("Status: `completed`", (task / "tickets/01-work.md").read_text(encoding="utf-8"))
        self.assertNotIn("Status:", (task / "result.md").read_text(encoding="utf-8"))
        self.assertEqual(
            (root / "runtime/current.yaml").read_text(encoding="utf-8"),
            f"task: tasks/{task.name}\nticket: null\n",
        )

    def test_complete_ticket_rejects_unfilled_result(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-unfilled"
        write(task / "task.md", task_file("未填结果", "in-progress"))
        write(task / "spec.md", spec_file("未填结果"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "in-progress", "none"))
        write(
            root / "runtime/current.yaml",
            f"task: tasks/{task.name}\nticket: tasks/{task.name}/tickets/01-work.md\n",
        )

        with self.assertRaisesRegex(zyes.ZyesError, "Result 未填写"):
            zyes.complete_ticket(root, task.name, "01-work")

    def test_cancel_task_releases_current_ticket(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-cancel-active"
        write(task / "task.md", task_file("取消执行中", "in-progress"))
        write(task / "spec.md", spec_file("取消执行中"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "in-progress", "none"))
        write(
            root / "runtime/current.yaml",
            f"task: tasks/{task.name}\nticket: tasks/{task.name}/tickets/01-work.md\n",
        )

        payload = zyes.cancel_task(root, task.name, "用户决定停止。")

        self.assertTrue(payload["valid"], payload)
        self.assertEqual(payload["released"], "01-work")
        self.assertIn("Status: `cancelled`", (task / "task.md").read_text(encoding="utf-8"))
        self.assertIn("Reason: 用户决定停止。", (task / "task.md").read_text(encoding="utf-8"))
        self.assertIn("Status: `ready`", (task / "tickets/01-work.md").read_text(encoding="utf-8"))
        self.assertEqual(
            (root / "runtime/current.yaml").read_text(encoding="utf-8"),
            f"task: tasks/{task.name}\nticket: null\n",
        )

    def test_cancel_task_releases_non_current_in_progress_ticket(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-non-current"
        write(task / "task.md", task_file("非 current", "in-progress"))
        write(task / "spec.md", spec_file("非 current"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "in-progress", "none"))

        before = zyes.snapshot(root, task.name)
        self.assertTrue(before["valid"], before)
        payload = zyes.cancel_task(root, task.name, "用户停止")

        self.assertTrue(payload["valid"], payload)
        self.assertEqual(payload["released"], "01-work")
        self.assertIn("Status: `cancelled`", (task / "task.md").read_text(encoding="utf-8"))
        self.assertIn("Status: `ready`", (task / "tickets/01-work.md").read_text(encoding="utf-8"))

    def test_supersede_task_validates_replacement_before_write(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-old"
        write(task / "task.md", task_file("旧任务", "in-progress"))
        write(task / "spec.md", spec_file("旧任务"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "in-progress", "none"))
        write(
            root / "runtime/current.yaml",
            f"task: tasks/{task.name}\nticket: tasks/{task.name}/tickets/01-work.md\n",
        )

        with self.assertRaisesRegex(zyes.ZyesError, "唯一指向"):
            zyes.supersede_task(root, task.name, "2026-07-23-missing")

        self.assertIn("Status: `in-progress`", (task / "task.md").read_text(encoding="utf-8"))
        self.assertIn("Status: `in-progress`", (task / "tickets/01-work.md").read_text(encoding="utf-8"))

    def test_supersede_task_releases_current_ticket(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        replacement = root / "tasks/2026-07-23-new"
        write(replacement / "task.md", task_file("新任务", "planning"))
        write(replacement / "spec.md", "# 新任务\n")
        old = root / "tasks/2026-07-23-old"
        write(old / "task.md", task_file("旧任务", "in-progress"))
        write(old / "spec.md", spec_file("旧任务"))
        write(old / "tickets/01-work.md", ticket_file("01 — 工作", "in-progress", "none"))
        write(
            root / "runtime/current.yaml",
            f"task: tasks/{old.name}\nticket: tasks/{old.name}/tickets/01-work.md\n",
        )

        payload = zyes.supersede_task(root, old.name, replacement.name)

        self.assertTrue(payload["valid"], payload)
        self.assertEqual(payload["released"], "01-work")
        self.assertIn("Status: `superseded`", (old / "task.md").read_text(encoding="utf-8"))
        self.assertIn(f"Superseded by: `{replacement.name}`", (old / "task.md").read_text(encoding="utf-8"))
        self.assertIn("Status: `ready`", (old / "tickets/01-work.md").read_text(encoding="utf-8"))

    def test_supersede_task_releases_non_current_in_progress_ticket(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        replacement = root / "tasks/2026-07-23-new-non-current"
        write(replacement / "task.md", task_file("新任务", "planning"))
        write(replacement / "spec.md", "# 新任务\n")
        old = root / "tasks/2026-07-23-old-non-current"
        write(old / "task.md", task_file("旧任务", "in-progress"))
        write(old / "spec.md", spec_file("旧任务"))
        write(old / "tickets/01-work.md", ticket_file("01 — 工作", "in-progress", "none"))

        payload = zyes.supersede_task(root, old.name, replacement.name)

        self.assertTrue(payload["valid"], payload)
        self.assertEqual(payload["released"], "01-work")
        self.assertIn("Status: `superseded`", (old / "task.md").read_text(encoding="utf-8"))
        self.assertIn("Status: `ready`", (old / "tickets/01-work.md").read_text(encoding="utf-8"))

    def test_archive_task_moves_terminal_task_and_clears_current(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-finished"
        write(task / "task.md", task_file("已完成", "completed"))
        write(task / "spec.md", spec_file("已完成"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(task / "result.md", result_file())
        write(root / "runtime/current.yaml", f"task: tasks/{task.name}\nticket: null\n")

        payload = zyes.archive_task(root, task.name, "2026-08-01")

        self.assertTrue(payload["valid"], payload)
        self.assertEqual(payload["archived"], "archive/2026-08/2026-07-23-finished")
        self.assertFalse(task.exists())
        self.assertTrue((root / "archive/2026-08/2026-07-23-finished/task.md").is_file())
        self.assertFalse((root / "runtime/current.yaml").exists())

    def test_archive_task_rejects_invalid_date_as_business_error(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-finished"
        write(task / "task.md", task_file("已完成", "completed"))
        write(task / "spec.md", spec_file("已完成"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(task / "result.md", result_file())
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = zyes.main(
                [
                    "archive-task",
                    "--project-root",
                    str(root),
                    "--task",
                    task.name,
                    "--date",
                    "2026-02-30",
                    "--json",
                ]
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertFalse(payload["valid"])
        self.assertIn("有效的 YYYY-MM-DD 日期", payload["errors"][0])
        self.assertTrue(task.exists())

    def test_archive_task_rolls_back_move_when_post_validation_fails(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-archive-rollback"
        write(task / "task.md", task_file("归档回滚", "completed"))
        write(task / "spec.md", spec_file("归档回滚"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(task / "result.md", result_file())
        write(root / "runtime/current.yaml", f"task: tasks/{task.name}\nticket: null\n")
        original = zyes.parse_current
        calls = 0

        def fail_after_move(project_root: Path) -> dict[str, object]:
            nonlocal calls
            calls += 1
            current = original(project_root)
            if calls == 2:
                current["errors"].append("模拟归档后校验失败")
            return current

        with mock.patch.object(zyes, "parse_current", side_effect=fail_after_move):
            with self.assertRaisesRegex(zyes.ZyesError, "模拟归档后校验失败"):
                zyes.archive_task(root, task.name, "2026-08-01")

        self.assertTrue(task.is_dir())
        self.assertFalse((root / "archive/2026-08/2026-07-23-archive-rollback").exists())
        self.assertEqual(
            (root / "runtime/current.yaml").read_text(encoding="utf-8"),
            f"task: tasks/{task.name}\nticket: null\n",
        )

    def test_verifying_task_can_create_result_lazily(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-ready-to-verify"
        write(task / "task.md", task_file("等待验收", "verifying"))
        write(task / "spec.md", spec_file("等待验收"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(root / "runtime/current.yaml", f"task: tasks/{task.name}\nticket: null\n")
        result = zyes.snapshot(root)
        self.assertTrue(result["valid"], result)

    def test_dangling_blocker_is_invalid(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-invalid-blocker"
        write(task / "task.md", task_file("非法阻塞", "ready"))
        write(task / "spec.md", spec_file("非法阻塞"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "ready", "99-missing"))
        result = zyes.snapshot(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("blocker 不存在" in error for error in result["tasks"][0]["errors"]))

    def test_cycle_is_invalid(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-cycle"
        write(task / "task.md", task_file("循环依赖", "ready"))
        write(task / "spec.md", spec_file("循环依赖"))
        write(task / "tickets/01-first.md", ticket_file("01 — First", "ready", "02-second"))
        write(task / "tickets/02-second.md", ticket_file("02 — Second", "ready", "01-first"))
        result = zyes.snapshot(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("依赖图存在环" in error for error in result["tasks"][0]["errors"]))

    def test_current_ticket_must_be_in_progress(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = self.create_valid_task(root)
        write(
            root / "runtime/current.yaml",
            f"task: tasks/{task.name}\nticket: tasks/{task.name}/tickets/02-add-ui.md\n",
        )
        result = zyes.snapshot(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("不是 in-progress" in error for error in result["tasks"][0]["errors"]))

    def test_completed_ticket_only_requires_acceptance_checkboxes(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-completed-ticket"
        write(task / "task.md", task_file("已完成 ticket", "verifying"))
        write(task / "spec.md", spec_file("已完成 ticket"))
        write(
            task / "tickets/01-work.md",
            ticket_file("01 — 工作", "completed", "none", True).replace(
                "## Verification\n\n测试通过。", "## Verification\n\n- [ ] 后续观察项\n测试通过。"
            ),
        )
        write(root / "runtime/current.yaml", f"task: tasks/{task.name}\nticket: null\n")
        result = zyes.snapshot(root)
        self.assertTrue(result["valid"], result)

    def test_planning_task_cannot_have_in_progress_ticket(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-planning-active"
        write(task / "task.md", task_file("规划异常", "planning"))
        write(task / "spec.md", "# 规划异常\n")
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "in-progress", "none"))
        write(
            root / "runtime/current.yaml",
            f"task: tasks/{task.name}\nticket: tasks/{task.name}/tickets/01-work.md\n",
        )
        result = zyes.snapshot(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("planning task" in error for error in result["tasks"][0]["errors"]))

    def test_in_progress_ticket_requires_completed_blockers(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-blocked-active"
        write(task / "task.md", task_file("阻塞异常", "in-progress"))
        write(task / "spec.md", spec_file("阻塞异常"))
        write(task / "tickets/01-gate.md", ticket_file("01 — 前置", "ready", "none"))
        write(task / "tickets/02-work.md", ticket_file("02 — 工作", "in-progress", "01-gate"))
        write(
            root / "runtime/current.yaml",
            f"task: tasks/{task.name}\nticket: tasks/{task.name}/tickets/02-work.md\n",
        )
        result = zyes.snapshot(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("未完成 blocker" in error for error in result["tasks"][0]["errors"]))

    def test_ready_task_requires_complete_spec(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-incomplete-spec"
        write(task / "task.md", task_file("缺少 spec", "ready"))
        write(task / "spec.md", "# 缺少 spec\n")
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "ready", "none"))
        result = zyes.snapshot(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("spec.md 缺少有效" in error for error in result["tasks"][0]["errors"]))

    def test_planning_task_with_tickets_requires_complete_spec(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-planning-with-tickets"
        write(task / "task.md", task_file("规划制品异常", "planning"))
        write(task / "spec.md", "# 规划制品异常\n")
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "ready", "none"))

        result = zyes.snapshot(root)

        self.assertFalse(result["valid"])
        self.assertTrue(any("spec.md 缺少有效" in error for error in result["tasks"][0]["errors"]))

    def test_completed_ticket_rejects_embedded_placeholder(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-placeholder"
        write(task / "task.md", task_file("占位文本", "completed"))
        write(task / "spec.md", spec_file("占位文本"))
        ticket = ticket_file("01 — 工作", "completed", "none", True).replace(
            "已完成实现。", "<完成后记录实际实现；开始前保持为空>\n已完成实现。"
        )
        write(task / "tickets/01-work.md", ticket)
        write(task / "result.md", result_file())
        result = zyes.snapshot(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("模板占位文本" in error for error in result["tasks"][0]["errors"]))

    def test_verifying_result_without_duplicate_status_is_valid(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-reverify"
        write(task / "task.md", task_file("重新验收", "verifying"))
        write(task / "spec.md", spec_file("重新验收"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(task / "result.md", result_file())
        write(root / "runtime/current.yaml", f"task: tasks/{task.name}\nticket: null\n")
        result = zyes.snapshot(root)
        self.assertTrue(result["valid"], result)

    def test_request_changes_imports_scratch_ticket_and_accepts_after_reverification(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-review"
        write(task / "task.md", task_file("验收", "verifying"))
        write(task / "spec.md", spec_file("验收"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(task / "result.md", result_file())
        draft = root / "scratch/rework/02-fix.md"
        write(draft, ticket_file("02 — 修复", "ready", "01-work"))
        write(root / "runtime/current.yaml", f"task: tasks/{task.name}\nticket: null\n")

        changes = zyes.request_changes(root, task.name, "scratch/rework/02-fix.md")
        self.assertTrue(changes["valid"], changes)
        self.assertFalse(draft.exists())
        self.assertTrue((task / "tickets/02-fix.md").is_file())
        self.assertEqual(changes["task"]["status"], "in-progress")
        self.assertEqual(changes["task"]["frontier"], ["02-fix"])

        write(task / "tickets/02-fix.md", ticket_file("02 — 修复", "completed", "01-work", True))
        write(task / "task.md", task_file("验收", "completed"))
        reverify = zyes.reverify_task(root, task.name)
        self.assertEqual(reverify["task"]["status"], "verifying")
        accepted = zyes.accept_task(root, task.name)
        self.assertEqual(accepted["task"]["status"], "completed")

    def test_request_changes_rolls_back_invalid_draft(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-invalid-rework"
        write(task / "task.md", task_file("无效返工", "verifying"))
        write(task / "spec.md", spec_file("无效返工"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(task / "result.md", result_file())
        draft = root / "scratch/rework/02-fix.md"
        write(draft, ticket_file("02 — 修复", "ready", "99-missing"))
        write(root / "runtime/current.yaml", f"task: tasks/{task.name}\nticket: null\n")

        with self.assertRaisesRegex(zyes.ZyesError, "blocker 不存在"):
            zyes.request_changes(root, task.name, "scratch/rework/02-fix.md")

        self.assertTrue(draft.is_file())
        self.assertFalse((task / "tickets/02-fix.md").exists())
        self.assertIn("Status: `verifying`", (task / "task.md").read_text(encoding="utf-8"))

    def test_request_changes_rejects_outside_symlink_and_duplicate_drafts(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-draft-boundaries"
        write(task / "task.md", task_file("草稿边界", "verifying"))
        write(task / "spec.md", spec_file("草稿边界"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(task / "tickets/04-existing.md", ticket_file("04 — 已存在", "completed", "01-work", True))
        write(task / "result.md", result_file())
        (root / "scratch").mkdir()

        outside = root / "outside/02-outside.md"
        write(outside, ticket_file("02 — 外部", "ready", "01-work"))
        with self.assertRaisesRegex(zyes.ZyesError, "必须位于"):
            zyes.request_changes(root, task.name, str(outside))

        real = root / "scratch/03-real.md"
        write(real, ticket_file("03 — 真实", "ready", "01-work"))
        link = root / "scratch/03-link.md"
        link.symlink_to(real.name)
        with self.assertRaisesRegex(zyes.ZyesError, "不能是符号链接"):
            zyes.request_changes(root, task.name, "scratch/03-link.md")

        duplicate = root / "scratch/04-existing.md"
        write(duplicate, ticket_file("04 — 重复", "ready", "01-work"))
        with self.assertRaisesRegex(zyes.ZyesError, "返工 ticket 已存在"):
            zyes.request_changes(root, task.name, "scratch/04-existing.md")

        self.assertTrue(outside.is_file())
        self.assertTrue(real.is_file())
        self.assertTrue(duplicate.is_file())

    def test_accept_task_requires_result(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-no-result"
        write(task / "task.md", task_file("缺少验收结果", "verifying"))
        write(task / "spec.md", spec_file("缺少验收结果"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))

        with self.assertRaisesRegex(zyes.ZyesError, "result.md"):
            zyes.accept_task(root, task.name)

        self.assertIn("Status: `verifying`", (task / "task.md").read_text(encoding="utf-8"))

    def test_fenced_code_does_not_change_markdown_structure(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-fenced-code"
        task_text = task_file("代码示例", "ready") + (
            "\n```text\n# 不是标题\nStatus: `planning`\n```\n"
        )
        spec_text = spec_file("代码示例").replace(
            "遵循现有实现模式。",
            "遵循现有实现模式。\n\n```text\n# 不是一级标题\n## 不是章节\nStatus: `ready`\n```",
        )
        write(task / "task.md", task_text)
        write(task / "spec.md", spec_text)
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "ready", "none"))

        result = zyes.snapshot(root)
        self.assertTrue(result["valid"], result)

    def test_fenced_result_heading_does_not_satisfy_ticket_structure(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-fenced-result"
        write(task / "task.md", task_file("围栏结果", "ready"))
        write(task / "spec.md", spec_file("围栏结果"))
        ticket = ticket_file("01 — 工作", "ready", "none").replace(
            "## Result\n\n<完成后记录实际实现；开始前保持为空>\n\n",
            "```text\n## Result\n伪造结果\n```\n\n",
        )
        write(task / "tickets/01-work.md", ticket)

        result = zyes.snapshot(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("缺少 `## Result`" in error for error in result["tasks"][0]["errors"]))

    def test_cancelled_task_requires_reason_and_no_active_ticket(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-cancelled"
        write(task / "task.md", task_file("已取消", "cancelled") + "Reason: 用户停止任务。\n")
        write(task / "spec.md", "# 已取消\n")
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "ready", "none"))
        write(root / "runtime/current.yaml", f"task: tasks/{task.name}\nticket: null\n")
        result = zyes.snapshot(root)
        self.assertTrue(result["valid"], result)

    def test_superseded_task_points_to_unique_replacement(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        replacement = root / "tasks/2026-07-23-new-scope"
        write(replacement / "task.md", task_file("新范围", "planning"))
        write(replacement / "spec.md", "# 新范围\n")
        old = root / "tasks/2026-07-23-old-scope"
        write(
            old / "task.md",
            task_file("旧范围", "superseded") + f"Superseded by: `{replacement.name}`\n",
        )
        write(old / "spec.md", "# 旧范围\n")
        write(old / "tickets/01-work.md", ticket_file("01 — 工作", "ready", "none"))
        result = zyes.snapshot(root)
        self.assertTrue(result["valid"], result)

    def test_superseded_target_cannot_escape_through_symlink(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        replacement_name = "2026-07-23-outside-replacement"
        outside = self.base / replacement_name
        write(outside / "task.md", task_file("外部替代任务", "planning"))
        write(outside / "spec.md", "# 外部替代任务\n")
        archived_link = root / "archive/2026-07" / replacement_name
        archived_link.parent.mkdir(parents=True)
        archived_link.symlink_to(outside, target_is_directory=True)
        old = root / "tasks/2026-07-23-old-scope"
        write(
            old / "task.md",
            task_file("旧范围", "superseded") + f"Superseded by: `{replacement_name}`\n",
        )
        write(old / "spec.md", "# 旧范围\n")

        result = zyes.snapshot(root)

        self.assertFalse(result["valid"])
        self.assertTrue(
            any("Superseded by 目标通过符号链接" in error for error in result["tasks"][0]["errors"])
        )

    def test_superseded_target_requires_task_file(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        replacement_name = "2026-07-23-empty-replacement"
        (root / "archive/2026-07" / replacement_name).mkdir(parents=True)
        old = root / "tasks/2026-07-23-old-scope"
        write(
            old / "task.md",
            task_file("旧范围", "superseded") + f"Superseded by: `{replacement_name}`\n",
        )
        write(old / "spec.md", "# 旧范围\n")

        result = zyes.snapshot(root)

        self.assertFalse(result["valid"])
        self.assertTrue(
            any("Superseded by 目标缺少可访问的 task.md" in error for error in result["tasks"][0]["errors"])
        )

    def test_superseded_target_rejects_invalid_archive_month(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        replacement_name = "2026-07-23-invalid-archive"
        replacement = root / "archive/not-a-month" / replacement_name
        write(replacement / "task.md", task_file("非法归档替代任务", "completed"))
        write(replacement / "spec.md", spec_file("非法归档替代任务"))
        write(replacement / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(replacement / "result.md", result_file())
        old = root / "tasks/2026-07-23-old-scope"
        write(
            old / "task.md",
            task_file("旧范围", "superseded") + f"Superseded by: `{replacement_name}`\n",
        )
        write(old / "spec.md", "# 旧范围\n")

        result = zyes.snapshot(root)

        self.assertFalse(result["valid"])
        self.assertTrue(
            any("Superseded by 必须唯一指向" in error for error in result["tasks"][0]["errors"])
        )

    def test_current_paths_must_be_canonical(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = self.create_valid_task(root)
        write(
            root / "runtime/current.yaml",
            f"task: tasks//{task.name}\nticket: null\n",
        )
        result = zyes.snapshot(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("规范相对路径" in error for error in result["errors"]))

    def test_current_task_must_be_an_active_task_path(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        self.create_valid_task(root)
        write(
            root / "runtime/current.yaml",
            "task: tasks/2026-07-23-theme-switch/tickets\nticket: null\n",
        )
        result = zyes.snapshot(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("current task 必须指向" in error for error in result["errors"]))

    def test_current_file_cannot_escape_through_symlink(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        self.create_valid_task(root)
        outside = self.base / "outside-current.yaml"
        write(outside, "task: tasks/2026-07-23-theme-switch\nticket: null\n")
        current = root / "runtime/current.yaml"
        current.unlink()
        current.symlink_to(outside)
        result = zyes.snapshot(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("符号链接" in error for error in result["errors"]))

    def test_task_validation_ignores_another_valid_current_task(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        self.create_valid_task(root)
        selected = root / "tasks/2026-07-23-second-task"
        write(selected / "task.md", task_file("第二个任务", "planning"))
        write(selected / "spec.md", "# 第二个任务\n")
        result = zyes.snapshot(root, selected.name)
        self.assertTrue(result["valid"], result)

    def test_task_selector_rejects_tasks_symlink_outside_project(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        outside = self.base / "outside-tasks"
        task = outside / "2026-07-23-outside-task"
        write(task / "task.md", task_file("越界任务", "planning"))
        write(task / "spec.md", "# 越界任务\n")
        (root / "tasks").symlink_to(outside, target_is_directory=True)
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = zyes.main(
                ["validate", "--project-root", str(root), "--task", task.name, "--json"]
            )
        self.assertEqual(exit_code, 2)
        self.assertIn("tasks 目录通过符号链接", output.getvalue())

    def test_parse_task_reports_out_of_bounds_path(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        outside = self.base / "2026-07-23-outside-task"
        write(outside / "task.md", task_file("越界任务", "planning"))
        write(outside / "spec.md", "# 越界任务\n")
        task_link = root / "tasks/2026-07-23-outside-task"
        task_link.parent.mkdir(parents=True)
        task_link.symlink_to(outside, target_is_directory=True)

        data = zyes.parse_task(task_link, root)

        self.assertIsNone(data["path"])
        self.assertTrue(any("任务目录 通过符号链接" in error for error in data["errors"]))

    def test_parse_ticket_reports_out_of_bounds_path(self) -> None:
        root = self.base / "zyes"
        ticket_dir = root / "tasks/2026-07-23-task/tickets"
        ticket_dir.mkdir(parents=True)
        outside = self.base / "01-outside.md"
        write(outside, ticket_file("01 — 越界", "ready", "none"))
        ticket_link = ticket_dir / "01-outside.md"
        ticket_link.symlink_to(outside)

        data = zyes.parse_ticket(ticket_link, root)

        self.assertIsNone(data["path"])
        self.assertTrue(any("ticket 通过符号链接" in error for error in data["errors"]))

    def test_parse_result_reports_out_of_bounds_path(self) -> None:
        root = self.base / "zyes"
        task = root / "tasks/2026-07-23-task"
        task.mkdir(parents=True)
        outside = self.base / "result.md"
        write(outside, result_file())
        (task / "result.md").symlink_to(outside)

        data = zyes.parse_result(task, root, "verifying")

        self.assertIsNotNone(data)
        assert data is not None
        self.assertIsNone(data["path"])
        self.assertTrue(any("result.md 通过符号链接" in error for error in data["errors"]))

    def test_invalid_utf8_returns_structured_business_error(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-invalid-utf8"
        task.mkdir(parents=True)
        (task / "task.md").write_bytes(b"\xff\xfe")
        write(task / "spec.md", "# 非法编码\n")
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = zyes.main(
                ["validate", "--project-root", str(root), "--task", task.name, "--json"]
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertFalse(payload["valid"])
        self.assertIn("不是有效的 UTF-8 文本", payload["errors"][0])

    def test_frontier_reports_global_current_errors(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = self.create_valid_task(root)
        write(root / "runtime/current.yaml", "task: ../../outside\nticket: null\n")
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = zyes.main(
                ["frontier", "--project-root", str(root), "--task", task.name, "--json"]
            )
        self.assertEqual(exit_code, 1)
        self.assertIn("current task 必须是", output.getvalue())

    def test_context_command_emits_json(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = self.create_valid_task(root)
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = zyes.main(
                [
                    "context",
                    "--entry",
                    "z-implement",
                    "--project-root",
                    str(root),
                    "--task",
                    task.name,
                    "--format",
                    "json",
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["state"]["task"], f"tasks/{task.name}")

    def test_context_command_verbose_preserves_diagnostics(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = self.create_valid_task(root)
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = zyes.main(
                [
                    "context",
                    "--entry",
                    "z-implement",
                    "--project-root",
                    str(root),
                    "--task",
                    task.name,
                    "--verbose",
                    "--format",
                    "json",
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(len(payload["diagnostics"]["files"]["tickets"]), 2)
        self.assertIn("warnings", payload["diagnostics"]["selected_task"])

    def test_validate_command_only_emits_warnings_with_verbose(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        self.create_valid_task(root)
        task = root / "tasks/2026-07-23-background-task"
        write(task / "task.md", task_file("后台任务", "in-progress"))
        write(task / "spec.md", spec_file("后台任务"))
        write(
            task / "tickets/01-background.md",
            ticket_file("01 — 后台工作", "in-progress", "none"),
        )

        def validate(*extra: str) -> dict[str, object]:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = zyes.main(
                    [
                        "validate",
                        "--project-root",
                        str(root),
                        "--task",
                        task.name,
                        *extra,
                        "--json",
                    ]
                )
            self.assertEqual(exit_code, 0)
            return json.loads(output.getvalue())

        compact = validate()
        verbose = validate("--verbose")

        self.assertNotIn("warnings", compact["tasks"][0])
        self.assertEqual(
            verbose["tasks"][0]["warnings"],
            ["任务存在 in-progress ticket，但不是 current task"],
        )

    def test_entry_context_routes_implement_actions(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-entry-routing"
        write(task / "task.md", task_file("入口路由", "ready"))
        write(task / "spec.md", spec_file("入口路由"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "ready", "none"))

        ready = zyes.entry_context(root, "z-implement", task.name)
        self.assertEqual(ready["action"], "start-ticket")
        self.assertEqual(ready["frontier"], ["01-work"])
        self.assertNotIn(f"tasks/{task.name}/tickets/01-work.md", ready["inputs"])

        write(task / "task.md", task_file("入口路由", "in-progress"))
        write(
            task / "tickets/01-work.md",
            ticket_file("01 — 工作", "in-progress", "none"),
        )
        current_ticket = f"tasks/{task.name}/tickets/01-work.md"
        write(
            root / "runtime/current.yaml",
            f"task: tasks/{task.name}\nticket: {current_ticket}\n",
        )
        implementing = zyes.entry_context(root, "z-implement")
        self.assertEqual(implementing["action"], "implement-ticket")
        self.assertEqual(implementing["state"]["ticket"], current_ticket)
        self.assertIn(current_ticket, implementing["inputs"])

        write(task / "task.md", task_file("入口路由", "verifying"))
        write(
            task / "tickets/01-work.md",
            ticket_file("01 — 工作", "completed", "none", True),
        )
        write(
            root / "runtime/current.yaml",
            f"task: tasks/{task.name}\nticket: null\n",
        )
        verifying = zyes.entry_context(root, "z-implement")
        self.assertEqual(verifying["action"], "verify-task")
        self.assertIn(current_ticket, verifying["inputs"])
        self.assertTrue(
            all(not contract["budget"]["oversize"] for contract in (ready, implementing, verifying))
        )

    def test_entry_context_keeps_ambiguous_choices_minimal(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        for name in ("2026-07-23-first-task", "2026-07-23-second-task"):
            task = root / "tasks" / name
            write(task / "task.md", task_file(name, "planning"))
            write(task / "spec.md", f"# {name}\n")

        contract = zyes.entry_context(root, "z-brainstorm")
        prompt = zyes.render_entry_prompt(contract)

        self.assertEqual(contract["action"], "select-task")
        self.assertEqual(len(contract["choices"]), 2)
        self.assertEqual(set(contract["choices"][0]), {"path", "title", "status"})
        self.assertLessEqual(contract["budget"]["estimated_tokens"], 700)
        self.assertIn("Choices:", prompt)

    def test_entry_prompt_matches_golden_empty_planning_contract(self) -> None:
        root = self.base / "zyes"
        root.mkdir()

        contract = zyes.entry_context(root, "z-brainstorm")
        prompt = zyes.render_entry_prompt(contract).replace(contract["project_root"], "<ROOT>")

        self.assertEqual(contract["action"], "create-planning-task")
        self.assertLessEqual(contract["budget"]["estimated_tokens"], 450)
        self.assertEqual(
            prompt,
            """<zyes-context>
Project: <ROOT>
Entry: z-brainstorm
Action: create-planning-task
State: none
Required:
- Create or select one planning task before writing product code.
- Investigate repository evidence before asking user questions.
- Use z-grilling for every substantive user decision.
Stop:
- Do not modify product code or start implementation.
- Do not choose user-owned product decisions.
</zyes-context>""",
        )

    def test_context_entry_prompt_and_json_share_contract(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = self.create_valid_task(root)

        json_output = io.StringIO()
        with redirect_stdout(json_output):
            json_exit = zyes.main(
                [
                    "context",
                    "--entry",
                    "z-implement",
                    "--project-root",
                    str(root),
                    "--task",
                    task.name,
                    "--format",
                    "json",
                ]
            )
        payload = json.loads(json_output.getvalue())

        prompt_output = io.StringIO()
        with redirect_stdout(prompt_output):
            prompt_exit = zyes.main(
                [
                    "context",
                    "--entry",
                    "z-implement",
                    "--project-root",
                    str(root),
                    "--task",
                    task.name,
                    "--format",
                    "prompt",
                ]
            )

        self.assertEqual(json_exit, 0)
        self.assertEqual(prompt_exit, 0)
        self.assertEqual(payload["action"], "start-ticket")
        self.assertIn(f"Action: {payload['action']}", prompt_output.getvalue())

    def test_entry_context_routes_planning_finish_list_and_mismatch(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-action-matrix"
        write(task / "task.md", task_file("动作矩阵", "planning"))
        write(task / "spec.md", "# 动作矩阵\n")

        refining = zyes.entry_context(root, "z-brainstorm", task.name)
        self.assertEqual(refining["action"], "refine-plan")

        write(task / "spec.md", spec_file("动作矩阵"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "ready", "none"))
        approval = zyes.entry_context(root, "z-brainstorm", task.name)
        self.assertEqual(approval["action"], "approve-or-revise-plan")

        write(task / "task.md", task_file("动作矩阵", "ready"))
        active_finish = zyes.entry_context(root, "z-finish-task", task.name)
        self.assertEqual(active_finish["action"], "cancel-or-supersede-task")

        write(task / "task.md", task_file("动作矩阵", "completed"))
        write(
            task / "tickets/01-work.md",
            ticket_file("01 — 工作", "completed", "none", True),
        )
        write(task / "result.md", result_file())
        terminal_finish = zyes.entry_context(root, "z-finish-task", task.name)
        self.assertEqual(terminal_finish["action"], "archive-task")
        self.assertEqual(
            terminal_finish["inputs"],
            [f"tasks/{task.name}/task.md", f"tasks/{task.name}/result.md"],
        )

        listing = zyes.entry_context(root, "z-list-tasks")
        self.assertEqual(listing["action"], "list-tasks")
        self.assertEqual(len(listing["tasks"]), 1)

        write(task / "task.md", task_file("动作矩阵", "in-progress"))
        write(
            task / "tickets/01-work.md",
            ticket_file("01 — 工作", "in-progress", "none"),
        )
        mismatch = zyes.entry_context(root, "z-brainstorm", task.name)
        self.assertEqual(mismatch["action"], "use-entry-for-status")
        self.assertTrue(
            all(
                not contract["budget"]["oversize"]
                for contract in (
                    refining,
                    approval,
                    active_finish,
                    terminal_finish,
                    listing,
                    mismatch,
                )
            )
        )

    def test_entry_context_reports_no_match_and_blocking_errors(self) -> None:
        root = self.base / "zyes"
        root.mkdir()

        no_match = zyes.entry_context(root, "z-implement")
        self.assertEqual(no_match["action"], "no-matching-task")

        write(root / "runtime/current.yaml", "task: ../../outside\nticket: null\n")
        invalid = zyes.entry_context(root, "z-implement")
        self.assertEqual(invalid["action"], "resolve-errors")
        self.assertFalse(invalid["valid"])
        self.assertTrue(any("current task 必须是" in error for error in invalid["errors"]))

    def test_oversize_contract_is_explicit_and_not_truncated(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        contract = zyes.entry_context(root, "z-brainstorm")
        marker = "blocking-detail-" * 300
        contract["errors"] = [marker]
        base_prompt = zyes.render_entry_prompt(contract)
        contract["budget"] = {
            "limit": 450,
            "estimated_tokens": zyes.estimate_context_tokens(base_prompt),
            "oversize": True,
        }

        prompt = zyes.render_entry_prompt(contract)

        self.assertIn(marker, prompt)
        self.assertIn("Oversize: true", prompt)
        self.assertIn("Expand:", prompt)

    def test_every_entry_action_has_required_and_stop_contracts(self) -> None:
        expected = {
            "resolve-errors",
            "select-task",
            "create-planning-task",
            "refine-plan",
            "approve-or-revise-plan",
            "start-ticket",
            "implement-ticket",
            "verify-task",
            "reverify-or-finish",
            "cancel-or-supersede-task",
            "archive-task",
            "list-tasks",
            "use-entry-for-status",
            "no-matching-task",
        }

        self.assertEqual(set(zyes.ACTION_INSTRUCTIONS), expected)
        self.assertTrue(
            all(required and stop for required, stop in zyes.ACTION_INSTRUCTIONS.values())
        )

    def test_v2_implement_context_extracts_only_referenced_spec_items(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-v2-context"
        write(task / "task.md", task_file("V2 上下文", "in-progress"))
        write(task / "spec.md", spec_file_v2("V2 上下文", include_second_acceptance=True))
        ticket_path = task / "tickets/01-work.md"
        write(
            ticket_path,
            ticket_file_v2(
                "01 — 工作",
                "in-progress",
                "none",
                ("D-001", "AC-002"),
            ),
        )
        relative_ticket = f"tasks/{task.name}/tickets/{ticket_path.name}"
        write(
            root / "runtime/current.yaml",
            f"task: tasks/{task.name}\nticket: {relative_ticket}\n",
        )

        contract = zyes.entry_context(root, "z-implement")

        self.assertTrue(contract["valid"], contract)
        self.assertEqual(contract["action"], "implement-ticket")
        self.assertEqual(contract["state"]["format_version"], 2)
        self.assertNotIn(f"tasks/{task.name}/spec.md", contract["inputs"])
        self.assertIn(relative_ticket, contract["inputs"])
        self.assertEqual(
            [item["id"] for item in contract["context"]["spec_refs"]],
            ["D-001", "AC-002"],
        )
        self.assertNotIn("AC-001", json.dumps(contract["context"], ensure_ascii=False))
        self.assertEqual(contract["context"]["out_of_scope"], "不改变其他行为。")

    def test_v2_ticket_refs_are_required_unique_and_known(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-v2-refs"
        write(task / "task.md", task_file("V2 引用", "ready"))
        write(task / "spec.md", spec_file_v2("V2 引用"))
        ticket_path = task / "tickets/01-work.md"

        write(ticket_path, ticket_file("01 — 工作", "ready", "none"))
        missing = zyes.snapshot(root)
        self.assertTrue(
            any("缺少 Spec refs" in error for error in missing["tasks"][0]["errors"]),
            missing,
        )

        write(
            ticket_path,
            ticket_file_v2("01 — 工作", "ready", "none", ("AC-999",)),
        )
        unknown = zyes.snapshot(root)
        self.assertTrue(
            any("Spec refs 不存在" in error for error in unknown["tasks"][0]["errors"]),
            unknown,
        )

        duplicate_refs = ticket_file_v2(
            "01 — 工作",
            "ready",
            "none",
            ("AC-001", "AC-001"),
        )
        write(ticket_path, duplicate_refs)
        duplicate = zyes.snapshot(root)
        self.assertTrue(
            any("Spec refs 不得重复" in error for error in duplicate["tasks"][0]["errors"]),
            duplicate,
        )

        invalid_syntax = ticket_file_v2(
            "01 — 工作",
            "ready",
            "none",
            ("AC-001",),
        ).replace("`AC-001`", "`AC-001`, AC-002")
        write(ticket_path, invalid_syntax)
        malformed = zyes.snapshot(root)
        self.assertTrue(
            any("Spec refs 只能包含" in error for error in malformed["tasks"][0]["errors"]),
            malformed,
        )

    def test_v2_spec_rejects_duplicate_stable_ids(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-v2-duplicate"
        write(task / "task.md", task_file("V2 重复", "ready"))
        spec = spec_file_v2("V2 重复").replace(
            "- AC-001: 用户可以完成目标行为。",
            "- AC-001: 用户可以完成目标行为。\n- AC-001: 重复条件。",
        )
        write(task / "spec.md", spec)
        write(
            task / "tickets/01-work.md",
            ticket_file_v2("01 — 工作", "ready", "none", ("AC-001",)),
        )

        data = zyes.snapshot(root)

        self.assertFalse(data["valid"])
        self.assertTrue(
            any("稳定 ID 重复: AC-001" in error for error in data["tasks"][0]["errors"]),
            data,
        )

    def test_v2_verify_context_builds_evidence_matrix_and_coverage_gap(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-v2-matrix"
        write(task / "task.md", task_file("V2 矩阵", "verifying"))
        write(task / "spec.md", spec_file_v2("V2 矩阵", include_second_acceptance=True))
        ticket_path = task / "tickets/01-work.md"
        write(
            ticket_path,
            ticket_file_v2(
                "01 — 工作",
                "completed",
                "none",
                ("D-001", "AC-001"),
                True,
            ),
        )
        write(
            root / "runtime/current.yaml",
            f"task: tasks/{task.name}\nticket: null\n",
        )

        contract = zyes.entry_context(root, "z-implement")
        matrix = contract["context"]["evidence_matrix"]

        self.assertTrue(contract["valid"], contract)
        self.assertEqual(contract["action"], "verify-task")
        self.assertNotIn(f"tasks/{task.name}/spec.md", contract["inputs"])
        self.assertNotIn(f"tasks/{task.name}/tickets/{ticket_path.name}", contract["inputs"])
        self.assertEqual(matrix[0]["acceptance_id"], "AC-001")
        self.assertEqual(matrix[0]["tickets"][0]["ticket"], "01-work")
        self.assertEqual(matrix[0]["blocking"], [])
        self.assertEqual(matrix[1]["acceptance_id"], "AC-002")
        self.assertEqual(matrix[1]["blocking"], ["no covering ticket"])
        prompt = zyes.render_entry_prompt(contract)
        self.assertIn("    Result:\n      已完成实现。", prompt)
        self.assertIn("    Verification:\n      测试通过。", prompt)

    def test_v1_verify_context_keeps_full_read_fallback(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-v1-fallback"
        write(task / "task.md", task_file("V1 兼容", "verifying"))
        write(task / "spec.md", spec_file("V1 兼容"))
        ticket_path = task / "tickets/01-work.md"
        write(ticket_path, ticket_file("01 — 工作", "completed", "none", True))

        contract = zyes.entry_context(root, "z-implement", task.name)

        self.assertTrue(contract["valid"], contract)
        self.assertEqual(contract["state"]["format_version"], 1)
        self.assertIn(f"tasks/{task.name}/spec.md", contract["inputs"])
        self.assertIn(f"tasks/{task.name}/tickets/{ticket_path.name}", contract["inputs"])
        self.assertEqual(contract["context"], {})

    def test_v2_request_changes_requires_and_preserves_spec_refs(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "tasks/2026-07-23-v2-rework"
        write(task / "task.md", task_file("V2 返工", "verifying"))
        write(task / "spec.md", spec_file_v2("V2 返工"))
        write(
            task / "tickets/01-work.md",
            ticket_file_v2("01 — 工作", "completed", "none", ("AC-001",), True),
        )
        write(task / "result.md", result_file())
        draft = root / "scratch/rework/02-fix.md"
        write(
            draft,
            ticket_file_v2("02 — 修复", "ready", "01-work", ("D-001", "AC-001")),
        )

        changes = zyes.request_changes(root, task.name, "scratch/rework/02-fix.md")

        self.assertTrue(changes["valid"], changes)
        imported = task / "tickets/02-fix.md"
        self.assertTrue(imported.is_file())
        self.assertIn("Spec refs: `D-001`, `AC-001`", imported.read_text(encoding="utf-8"))

    def test_v2_targeted_implement_context_reduces_expanded_input(self) -> None:
        def create_context(root: Path, version: int) -> dict[str, object]:
            root.mkdir()
            task = root / f"tasks/2026-07-23-v{version}-size"
            write(task / "task.md", task_file(f"V{version} 体积", "in-progress"))
            if version == 1:
                spec = spec_file(f"V{version} 体积").replace(
                    "## Further Notes\n\nnone",
                    "## Further Notes\n\n" + ("与当前 ticket 无关的历史背景。" * 300),
                )
                ticket = ticket_file("01 — 工作", "in-progress", "none")
            else:
                spec = spec_file_v2(f"V{version} 体积").replace(
                    "## Further Notes\n\nnone",
                    "## Further Notes\n\n" + ("与当前 ticket 无关的历史背景。" * 300),
                )
                ticket = ticket_file_v2(
                    "01 — 工作",
                    "in-progress",
                    "none",
                    ("D-001", "AC-001"),
                )
            write(task / "spec.md", spec)
            ticket_path = task / "tickets/01-work.md"
            write(ticket_path, ticket)
            relative_ticket = f"tasks/{task.name}/tickets/{ticket_path.name}"
            write(
                root / "runtime/current.yaml",
                f"task: tasks/{task.name}\nticket: {relative_ticket}\n",
            )
            return zyes.entry_context(root, "z-implement")

        v1_root = self.base / "v1"
        v2_root = self.base / "v2"
        v1 = create_context(v1_root, 1)
        v2 = create_context(v2_root, 2)

        def expanded_tokens(root: Path, contract: dict[str, object]) -> int:
            text = zyes.render_entry_prompt(contract)
            for relative in contract["inputs"]:
                path = root.joinpath(*Path(relative).parts)
                if path.is_file():
                    text += path.read_text(encoding="utf-8")
            return zyes.estimate_context_tokens(text)

        v1_tokens = expanded_tokens(v1_root, v1)
        v2_tokens = expanded_tokens(v2_root, v2)

        self.assertLess(v2_tokens, v1_tokens * 0.6, (v1_tokens, v2_tokens))

    def test_main_dispatches_new_lifecycle_commands(self) -> None:
        root = self.base / "zyes"
        root.mkdir()

        def run(*arguments: str) -> tuple[int, dict[str, object]]:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = zyes.main([*arguments, "--project-root", str(root), "--json"])
            return exit_code, json.loads(output.getvalue())

        exit_code, payload = run(
            "create-task",
            "--title",
            "命令分发",
            "--slug",
            "command-dispatch",
            "--date",
            "2026-07-23",
        )
        self.assertEqual(exit_code, 0, payload)
        task = root / "tasks/2026-07-23-command-dispatch"
        write(task / "spec.md", spec_file("命令分发"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "ready", "none"))

        exit_code, payload = run("ready-task", "--task", task.name)
        self.assertEqual(exit_code, 0, payload)
        exit_code, payload = run("reopen-planning", "--task", task.name)
        self.assertEqual(exit_code, 0, payload)
        exit_code, payload = run("ready-task", "--task", task.name)
        self.assertEqual(exit_code, 0, payload)

        write(task / "task.md", task_file("命令分发", "verifying"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(task / "result.md", result_file())
        draft = root / "scratch/02-fix.md"
        write(draft, ticket_file("02 — 修复", "ready", "01-work"))
        exit_code, payload = run(
            "request-changes",
            "--task",
            task.name,
            "--ticket-draft",
            "scratch/02-fix.md",
        )
        self.assertEqual(exit_code, 0, payload)

        write(task / "task.md", task_file("命令分发", "completed"))
        write(task / "tickets/02-fix.md", ticket_file("02 — 修复", "completed", "01-work", True))
        exit_code, payload = run("reverify-task", "--task", task.name)
        self.assertEqual(exit_code, 0, payload)
        exit_code, payload = run("accept-task", "--task", task.name)
        self.assertEqual(exit_code, 0, payload)
        self.assertEqual(payload["task"]["status"], "completed")

    def test_main_return_codes(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        self.create_valid_task(root)
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(zyes.main(["validate", "--project-root", str(root), "--json"]), 0)
        write(root / "runtime/current.yaml", "task: ../../outside\nticket: null\n")
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(zyes.main(["validate", "--project-root", str(root), "--json"]), 1)
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            self.assertEqual(
                zyes.main(["validate", "--project-root", str(self.base / "missing"), "--json"]),
                2,
            )

    def test_archived_task_must_be_terminal(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "archive/2026-07/2026-07-23-old-task"
        write(task / "task.md", task_file("旧任务", "verifying"))
        write(task / "spec.md", spec_file("旧任务"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(task / "result.md", result_file())
        result = zyes.snapshot(root, include_archive=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any("归档任务必须处于" in error for error in result["archive"][0]["errors"]))

    def test_archived_cancelled_task_is_valid(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "archive/2026-07/2026-07-23-cancelled-task"
        write(task / "task.md", task_file("取消任务", "cancelled") + "Reason: 用户停止任务。\n")
        write(task / "spec.md", "# 取消任务\n")
        data = zyes.snapshot(root, include_archive=True)
        self.assertTrue(data["valid"], data)

    def test_archive_month_must_be_a_calendar_month(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "archive/2026-99/2026-07-23-old-task"
        write(task / "task.md", task_file("旧任务", "completed"))
        write(task / "spec.md", spec_file("旧任务"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(task / "result.md", result_file())
        result = zyes.snapshot(root, include_archive=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any("非法归档月份目录" in error for error in result["errors"]))

    def test_list_archive_prints_archived_tasks(self) -> None:
        root = self.base / "zyes"
        root.mkdir()
        task = root / "archive/2026-07/2026-07-23-old-task"
        write(task / "task.md", task_file("旧任务", "completed"))
        write(task / "spec.md", spec_file("旧任务"))
        write(task / "tickets/01-work.md", ticket_file("01 — 工作", "completed", "none", True))
        write(task / "result.md", result_file())
        data = zyes.snapshot(root, include_archive=True)
        self.assertTrue(data["valid"], data)
        output = io.StringIO()
        with redirect_stdout(output):
            zyes.print_list(data)
        self.assertIn("ARCHIVE", output.getvalue())
        self.assertIn("archive/2026-07/2026-07-23-old-task", output.getvalue())


if __name__ == "__main__":
    unittest.main()
