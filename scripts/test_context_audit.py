#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = Path(__file__).with_name("audit_context.py")
SPEC = importlib.util.spec_from_file_location("context_audit", AUDIT_PATH)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)

EXPECTED_GRILLING_BODY = """# 逐题追问

围绕这件事的每个方面持续追问我，直到我们达成共同理解。沿着决策树的每个分支往下走，一个接一个解决决策之间的依赖。每个问题都给出你的推荐答案。

一次只问一个问题，并等待我对该问题的反馈后再继续。一次问多个问题会让人无所适从。

如果某个*事实*可以通过探索环境（文件系统、工具等）找到，就去查，而不是问我。但*决策*属于我：把每个决策交给我，并等待我的回答。

在我确认我们已经达成共同理解之前，不要执行它。
"""


class ContextAuditTests(unittest.TestCase):
    def test_estimator_uses_documented_mixed_language_formula(self) -> None:
        self.assertEqual(audit.estimate_tokens("abcdefgh中文"), 4)

    def test_all_skills_have_name_and_description(self) -> None:
        skill_files = list((REPO_ROOT / "skills").rglob("SKILL.md"))

        metadata_text, records = audit.skill_metadata(skill_files)

        self.assertEqual(len(records), 7)
        self.assertEqual(
            {record["name"] for record in records},
            {
                "z-init",
                "z-brainstorm",
                "z-implement",
                "z-list-tasks",
                "z-finish-task",
                "z-handoff",
                "z-grilling",
            },
        )
        self.assertTrue(metadata_text)
        self.assertTrue(all(record["name"] and record["description"] for record in records))

    def test_discovery_budget_after_stage_one(self) -> None:
        report = audit.zyes_report(REPO_ROOT)

        self.assertLessEqual(report["discovery"]["estimated_tokens"], 700)

    def test_skill_frontmatter_only_uses_public_trigger_fields(self) -> None:
        for path in (REPO_ROOT / "skills").rglob("SKILL.md"):
            match = audit.FRONTMATTER_RE.search(path.read_text(encoding="utf-8"))
            self.assertIsNotNone(match, path)
            assert match
            keys = set(re.findall(r"^([A-Za-z][A-Za-z0-9_-]*):", match.group(1), re.MULTILINE))
            with self.subTest(path=path):
                self.assertEqual(keys, {"name", "description"})

    def test_stage_three_profiles_stay_within_budget(self) -> None:
        profile_paths = [
            *(REPO_ROOT / "skills/explicit/z-brainstorm/references").glob("*.md"),
            *(REPO_ROOT / "skills/explicit/z-implement/references").glob("*.md"),
        ]

        self.assertEqual(len(profile_paths), 6)
        for path in profile_paths:
            with self.subTest(path=path):
                tokens = audit.estimate_tokens(path.read_text(encoding="utf-8"))
                self.assertGreaterEqual(tokens, 200)
                self.assertLessEqual(tokens, 400)

    def test_stage_three_lifecycle_static_budget(self) -> None:
        report = audit.zyes_report(REPO_ROOT)

        self.assertLessEqual(
            report["scenarios"]["lifecycle-deduplicated"]["estimated_tokens"],
            5000,
        )

    def test_grilling_body_matches_protected_golden_contract(self) -> None:
        path = REPO_ROOT / "skills/internal/z-grilling/SKILL.md"
        text = path.read_text(encoding="utf-8")
        match = audit.FRONTMATTER_RE.search(text)
        self.assertIsNotNone(match)
        assert match

        self.assertEqual(text[match.end() :], EXPECTED_GRILLING_BODY)

    def test_repository_markdown_local_links_exist(self) -> None:
        markdown_files = [
            REPO_ROOT / "README.md",
            REPO_ROOT / "THIN-RUNTIME-OPTIMIZATION-PLAN.md",
            *(REPO_ROOT / "skills").rglob("*.md"),
        ]
        for markdown in markdown_files:
            text = markdown.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "#")):
                    continue
                path_part = target.split("#", 1)[0]
                if not path_part:
                    continue
                with self.subTest(markdown=markdown, target=target):
                    self.assertTrue((markdown.parent / path_part).resolve().exists())


if __name__ == "__main__":
    unittest.main()
