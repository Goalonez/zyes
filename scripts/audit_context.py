#!/usr/bin/env python3
"""只读审计 Zyes、Matt skills 与 Trellis Codex 切片的上下文体积。"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
FIELD_RE = re.compile(r"^(name|description):\s*(.*?)\s*$", re.MULTILINE)

ZYES_SCENARIOS = {
    "idle": (),
    "planning": (
        "skills/explicit/z-brainstorm/SKILL.md",
        "skills/internal/z-grilling/SKILL.md",
        "skills/explicit/z-brainstorm/references/SPEC.md",
        "skills/explicit/z-brainstorm/references/TICKETS.md",
        "skills/explicit/z-brainstorm/references/DOMAIN.md",
    ),
    "implement-review": (
        "skills/explicit/z-implement/SKILL.md",
        "skills/explicit/z-implement/references/TDD.md",
        "skills/explicit/z-implement/references/REVIEW.md",
    ),
    "verify-finish": (
        "skills/explicit/z-implement/SKILL.md",
        "skills/explicit/z-implement/references/REVIEW.md",
        "skills/explicit/z-implement/references/VERIFY.md",
        "skills/explicit/z-finish-task/SKILL.md",
    ),
}


def estimate_tokens(text: str) -> int:
    """返回适合中英混合 Markdown 的确定性回归估算，不模拟账单 tokenizer。"""
    ascii_characters = sum(ord(character) < 128 for character in text)
    non_ascii_characters = len(text) - ascii_characters
    return math.ceil(ascii_characters / 4) + non_ascii_characters


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    return sorted({path.resolve() for path in paths}, key=lambda path: path.as_posix())


def text_stats(paths: Iterable[Path], content_prefix: str = "") -> dict[str, Any]:
    selected = unique_paths(paths)
    text = content_prefix + "".join(read_text(path) for path in selected)
    return {
        "files": len(selected),
        "bytes": len(text.encode("utf-8")),
        "characters": len(text),
        "estimated_tokens": estimate_tokens(text),
        "paths": [path.as_posix() for path in selected],
    }


def skill_metadata(skill_files: Iterable[Path]) -> tuple[str, list[dict[str, str]]]:
    records: list[dict[str, str]] = []
    blocks: list[str] = []
    for path in unique_paths(skill_files):
        text = read_text(path)
        match = FRONTMATTER_RE.search(text)
        if not match:
            raise ValueError(f"缺少 YAML front matter: {path}")
        fields = dict(FIELD_RE.findall(match.group(1)))
        if "name" not in fields or "description" not in fields:
            raise ValueError(f"front matter 缺少 name 或 description: {path}")
        records.append(
            {
                "name": fields["name"].strip('"\''),
                "description": fields["description"].strip('"\''),
                "path": path.as_posix(),
            }
        )
        blocks.append(f"name: {fields['name']}\ndescription: {fields['description']}\n")
    return "".join(blocks), records


def markdown_files(*roots: Path) -> list[Path]:
    return unique_paths(
        path
        for root in roots
        if root.is_dir()
        for path in root.rglob("*.md")
        if path.is_file()
    )


def relative_existing(repo_root: Path, names: Iterable[str]) -> list[Path]:
    paths = [repo_root / name for name in names]
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise ValueError("审计场景缺少文件: " + ", ".join(path.as_posix() for path in missing))
    return paths


def zyes_report(repo_root: Path) -> dict[str, Any]:
    skill_files = list((repo_root / "skills").rglob("SKILL.md"))
    metadata_text, metadata = skill_metadata(skill_files)
    scenarios: dict[str, Any] = {}
    for name, relative_paths in ZYES_SCENARIOS.items():
        scenarios[name] = text_stats(
            relative_existing(repo_root, relative_paths),
            content_prefix=metadata_text,
        )

    lifecycle_paths = unique_paths(
        path
        for paths in ZYES_SCENARIOS.values()
        for path in relative_existing(repo_root, paths)
    )
    scenarios["lifecycle-deduplicated"] = text_stats(
        lifecycle_paths,
        content_prefix=metadata_text,
    )
    return {
        "discoverable_skills": len(skill_files),
        "discovery": {
            "characters": len(metadata_text),
            "bytes": len(metadata_text.encode("utf-8")),
            "estimated_tokens": estimate_tokens(metadata_text),
            "skills": metadata,
        },
        "runtime_markdown": text_stats(markdown_files(repo_root / "skills")),
        "scenarios": scenarios,
    }


def matt_report(repo_root: Path) -> dict[str, Any]:
    promoted_roots = (
        repo_root / "skills" / "engineering",
        repo_root / "skills" / "productivity",
    )
    skill_files = [path for root in promoted_roots for path in root.rglob("SKILL.md")]
    metadata_text, metadata = skill_metadata(skill_files)
    return {
        "discoverable_skills": len(skill_files),
        "discovery": {
            "characters": len(metadata_text),
            "bytes": len(metadata_text.encode("utf-8")),
            "estimated_tokens": estimate_tokens(metadata_text),
            "skills": metadata,
        },
        "runtime_markdown": text_stats(markdown_files(*promoted_roots)),
        "scope": [root.as_posix() for root in promoted_roots],
    }


def trellis_report(repo_root: Path) -> dict[str, Any]:
    template_root = repo_root / "packages" / "cli" / "src" / "templates"
    skill_root = template_root / "codex" / "skills"
    skill_files = list(skill_root.rglob("SKILL.md"))
    metadata_text, metadata = skill_metadata(skill_files)
    runtime_paths = [*skill_files]
    runtime_paths.extend((template_root / "codex" / "agents").glob("*.toml"))
    runtime_paths.extend((template_root / "trellis" / "agents").glob("*.md"))
    return {
        "discoverable_skills": len(skill_files),
        "discovery": {
            "characters": len(metadata_text),
            "bytes": len(metadata_text.encode("utf-8")),
            "estimated_tokens": estimate_tokens(metadata_text),
            "skills": metadata,
        },
        "runtime_prompt_material": text_stats(runtime_paths),
        "scope": {
            "skills": skill_root.as_posix(),
            "codex_agents": (template_root / "codex" / "agents").as_posix(),
            "trellis_agents": (template_root / "trellis" / "agents").as_posix(),
            "excluded": "hook 源码、业务源码、项目 spec/task 与其他平台重复模板",
        },
    }


def compact_stats(stats: dict[str, Any]) -> str:
    return (
        f"{stats.get('files', '-'):>4} files  "
        f"{stats['characters']:>7} chars  "
        f"{stats['bytes']:>7} bytes  "
        f"{stats['estimated_tokens']:>7} est.tokens"
    )


def print_report(report: dict[str, Any], details: bool) -> None:
    print("估算口径: ceil(ASCII 字符 / 4) + 非 ASCII 字符；只用于回归，不等同账单 token。")
    for project_name in ("zyes", "matt", "trellis"):
        project = report.get(project_name)
        if not project:
            continue
        print(f"\n{project_name.upper()}  discoverable={project['discoverable_skills']}")
        print("  discovery ", compact_stats(project["discovery"]))
        runtime_key = "runtime_markdown" if "runtime_markdown" in project else "runtime_prompt_material"
        print("  runtime   ", compact_stats(project[runtime_key]))
        if project_name == "zyes":
            for scenario_name, stats in project["scenarios"].items():
                print(f"  {scenario_name:<21}", compact_stats(stats))
        if details:
            for path in project[runtime_key]["paths"]:
                print(f"    {path}")
    if report["warnings"]:
        print("\nWARNINGS")
        for warning in report["warnings"]:
            print(f"- {warning}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Zyes 仓库根目录",
    )
    parser.add_argument("--matt-root", type=Path, help="mattpocock/skills 仓库根目录")
    parser.add_argument("--trellis-root", type=Path, help="Trellis 仓库根目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--details", action="store_true", help="输出运行素材文件清单")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    report: dict[str, Any] = {
        "method": {
            "token_estimate": "ceil(ascii_characters / 4) + non_ascii_characters",
            "note": "确定性本地回归估算；最终结论使用目标宿主 telemetry",
        },
        "zyes": zyes_report(repo_root),
        "warnings": [],
    }
    if args.matt_root:
        matt_root = args.matt_root.expanduser().resolve()
        if matt_root.is_dir():
            report["matt"] = matt_report(matt_root)
        else:
            report["warnings"].append(f"Matt 比较目录不存在: {matt_root}")
    if args.trellis_root:
        trellis_root = args.trellis_root.expanduser().resolve()
        if trellis_root.is_dir():
            report["trellis"] = trellis_report(trellis_root)
        else:
            report["warnings"].append(f"Trellis 比较目录不存在: {trellis_root}")

    if args.json:
        json.dump(report, fp=__import__("sys").stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print_report(report, args.details)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
