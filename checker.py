#!/usr/bin/env python3
"""
Centralized Code Quality Checker
Scans multiple repos and generates reports with timestamps
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class CodeQualityChecker:
    def __init__(self, reports_dir="reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def clone_repo(self, repo_url: str, target_dir: Path) -> bool:
        """Clone a GitHub repository or update it if it already exists."""
        try:
            if target_dir.exists():
                print(f"  Updating existing repo...")
                subprocess.run(
                    ["git", "-C", str(target_dir), "pull"],
                    check=True,
                    capture_output=True,
                )
            else:
                print(f"  Cloning {repo_url}...")
                subprocess.run(
                    ["git", "clone", repo_url, str(target_dir)],
                    check=True,
                    capture_output=True,
                )
            return True
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode("utf-8", "ignore") if e.stderr else ""
            stdout = e.stdout.decode("utf-8", "ignore") if e.stdout else ""
            print(f"  ❌ Failed to clone or update: {e}")
            if stderr:
                print(f"    stderr: {stderr.strip()}")
            if stdout:
                print(f"    stdout: {stdout.strip()}")
            return False

    def scan_repo(self, repo_path: Path) -> Dict:
        """Scan a single repository for code quality issues."""
        issues = {
            "any_type": [],
            "console_logs": [],
            "todos": [],
            "bad_naming": [],
            "large_files": [],
            "deep_nesting": [],
        }

        src_path = repo_path / "src"
        if not src_path.exists():
            possible_src = ["src", "lib", "app", "client/src", "frontend/src"]
            for p in possible_src:
                test_path = repo_path / p
                if test_path.exists():
                    src_path = test_path
                    break
            else:
                return {"error": f"No src folder found in {repo_path}"}

        for file_path in src_path.rglob("*"):
            if not file_path.is_file():
                continue

            rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")

            if file_path.suffix in [".ts", ".tsx", ".js", ".jsx"]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        lines = content.count("\n") + 1

                        if re.search(r"\bany\b", content):
                            issues["any_type"].append(rel_path)
                        if re.search(r"console\.(log|warn|error|debug)", content):
                            issues["console_logs"].append(rel_path)
                        if re.search(r"\b(TODO|FIXME|HACK|BUG)\b", content):
                            issues["todos"].append(rel_path)
                        if lines > 300:
                            issues["large_files"].append(f"{rel_path} ({lines} lines)")

                        name = file_path.stem
                        if file_path.suffix == ".tsx" and "hooks" not in str(file_path.parent):
                            if not re.match(r"^[A-Z][a-zA-Z0-9]*$", name):
                                issues["bad_naming"].append(
                                    f"{rel_path} (component should be PascalCase)"
                                )
                        if "hooks" in str(file_path.parent) and not name.startswith("use"):
                            issues["bad_naming"].append(
                                f"{rel_path} (hook should start with 'use')"
                            )
                except Exception:
                    pass

            depth = len(file_path.relative_to(src_path).parents)
            if depth > 4:
                issues["deep_nesting"].append(f"{rel_path} (depth: {depth})")

        return issues

    def generate_report(self, repo_name: str, issues: Dict) -> Tuple[Path, Path]:
        """Generate JSON and Markdown reports with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base_name = f"{repo_name}_{timestamp}"

        json_path = self.reports_dir / f"{base_name}.json"
        report_data = {
            "repo": repo_name,
            "timestamp": timestamp,
            "datetime": datetime.now().isoformat(),
            "summary": {
                "total_issues": sum(
                    len(v) for v in issues.values() if isinstance(v, list)
                ),
                "any_count": len(issues.get("any_type", [])),
                "console_count": len(issues.get("console_logs", [])),
                "todo_count": len(issues.get("todos", [])),
                "naming_count": len(issues.get("bad_naming", [])),
                "large_files_count": len(issues.get("large_files", [])),
                "deep_nesting_count": len(issues.get("deep_nesting", [])),
            },
            "issues": issues,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        md_path = self.reports_dir / f"{base_name}.md"
        md_content = self._generate_markdown(repo_name, timestamp, issues, report_data["summary"])
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return json_path, md_path

    def _generate_markdown(self, repo_name: str, timestamp: str, issues: Dict, summary: Dict) -> str:
        """Generate markdown formatted report."""
        md = f"""# Code Quality Report: {repo_name}

**Scan Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Report ID:** {timestamp}

## 📊 Summary

| Issue Type | Count |
|------------|-------|
| 🔴 `any` Type Usage | {summary['any_count']} |
| 🔊 Console Statements | {summary['console_count']} |
| 📝 TODOs/FIXMEs | {summary['todo_count']} |
| 📛 Naming Convention Violations | {summary['naming_count']} |
| 📄 Large Files (>300 lines) | {summary['large_files_count']} |
| 📁 Deep Nesting (>4 levels) | {summary['deep_nesting_count']} |
| **Total Issues** | **{summary['total_issues']}** |

---
"""

        for category, label in [
            ("any_type", "🔴 `any` Type Usage"),
            ("console_logs", "🔊 Console Statements"),
            ("todos", "📝 TODOs & FIXMEs"),
            ("bad_naming", "📛 Naming Violations"),
            ("large_files", "📄 Large Files"),
            ("deep_nesting", "📁 Deep Nesting"),
        ]:
            if issues.get(category):
                md += f"\n## {label}\n\n"
                for item in issues[category][:50]:
                    md += f"- `{item}`\n"
                if len(issues[category]) > 50:
                    md += f"\n*... and {len(issues[category]) - 50} more issues*\n"

        md += "\n---\n*Generated by Code Quality Checker*"
        return md

    def check_repo(self, repo_url: str, repo_name: str = None) -> Dict:
        """Check a single repository."""
        if not repo_name:
            repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")

        print(f"\n📁 Checking {repo_name}...")
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / repo_name

            if not self.clone_repo(repo_url, repo_path):
                return {
                    "repo": repo_name,
                    "error": f"Failed to clone {repo_url}",
                }

            issues = self.scan_repo(repo_path)
            if "error" in issues:
                return {
                    "repo": repo_name,
                    "error": issues["error"],
                }

            json_path, md_path = self.generate_report(repo_name, issues)
            return {
                "success": True,
                "repo": repo_name,
                "json_report": str(json_path),
                "md_report": str(md_path),
                "summary": {
                    "total_issues": sum(
                        len(v) for v in issues.values() if isinstance(v, list)
                    )
                },
            }

    def check_multiple_repos(self, repos: List[Dict]) -> List[Dict]:
        """Check multiple repositories from config."""
        results = []
        for repo in repos:
            result = self.check_repo(repo["url"], repo.get("name"))
            results.append(result)
        return results


def main():
    if len(sys.argv) > 1:
        checker = CodeQualityChecker()
        repo_url = sys.argv[1]
        repo_name = sys.argv[2] if len(sys.argv) > 2 else None
        result = checker.check_repo(repo_url, repo_name)
        print(json.dumps(result, indent=2))
        return

    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        checker = CodeQualityChecker(config.get("reports_dir", "reports"))
        results = checker.check_multiple_repos(config["repositories"])

        print("\n" + "=" * 60)
        print("📊 SCAN COMPLETE")
        print("=" * 60)
        for result in results:
            if result.get("success"):
                print(f"\n✅ {result['repo']}")
                print(f"   Issues: {result['summary']['total_issues']}")
                print(f"   Report: {result['md_report']}")
            else:
                print(f"\n❌ {result.get('repo', 'Unknown')}: {result.get('error', 'Unknown error')}")
        print("=" * 60)
    else:
        print("❌ No config.json found!")
        print("\nCreate config.json with:")
        print(json.dumps({
            "reports_dir": "reports",
            "repositories": [
                {"name": "my-project", "url": "https://github.com/username/my-project.git"},
                {"name": "another-repo", "url": "https://github.com/username/another-repo.git"}
            ]
        }, indent=2))


if __name__ == "__main__":
    main()
