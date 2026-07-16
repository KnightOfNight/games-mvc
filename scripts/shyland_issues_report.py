#!/usr/bin/env python3
"""Generate the Shyland GitHub issues report.

Writes a timestamped markdown snapshot of all issues to docs/shyland/,
for consumption by the Shyland design chat.

Read-only against GitHub (via the authenticated `gh` CLI) and against git.
Creates exactly one file. Never deletes or modifies prior reports.

Usage: python3 scripts/shyland_issues_report.py
Requires: gh CLI, authenticated (`gh auth status`).
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ISSUE_FIELDS = (
    "number,title,state,author,labels,milestone,assignees,"
    "createdAt,updatedAt,body,comments,url"
)
LIST_LIMIT = "500"


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a command, returning the completed process (check=False)."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def run_ok(cmd: list[str]) -> str:
    """Run a command that must succeed; abort the report if it doesn't."""
    proc = run(cmd)
    if proc.returncode != 0:
        sys.exit(
            f"FATAL: command failed ({' '.join(cmd)}):\n{proc.stderr.strip()}"
        )
    return proc.stdout


def repo_root() -> Path:
    return Path(run_ok(["git", "rev-parse", "--show-toplevel"]).strip())


def repo_name() -> str:
    out = run_ok(["gh", "repo", "view", "--json", "nameWithOwner"])
    return json.loads(out)["nameWithOwner"]


def check_auth() -> None:
    proc = run(["gh", "auth", "status"])
    if proc.returncode != 0:
        sys.exit(
            "FATAL: gh is not authenticated. Run `gh auth login` first.\n"
            + proc.stderr.strip()
        )


def fetch_open_numbers() -> list[int]:
    out = run_ok(
        ["gh", "issue", "list", "--state", "open", "--limit", LIST_LIMIT,
         "--json", "number"]
    )
    return sorted(item["number"] for item in json.loads(out))


def fetch_issue(number: int) -> dict:
    out = run_ok(["gh", "issue", "view", str(number), "--json", ISSUE_FIELDS])
    return json.loads(out)


def fetch_dependencies(number: int) -> tuple[list[int], list[int]] | None:
    """Return (blocked_by, blocks) issue numbers, or None if unavailable."""
    results = []
    for endpoint in ("blocked_by", "blocking"):
        proc = run(
            ["gh", "api",
             f"repos/{{owner}}/{{repo}}/issues/{number}/dependencies/{endpoint}"]
        )
        if proc.returncode != 0:
            return None
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return None
        results.append(sorted(item["number"] for item in data))
    return results[0], results[1]


def fetch_closed() -> list[dict]:
    out = run_ok(
        ["gh", "issue", "list", "--state", "closed", "--limit", LIST_LIMIT,
         "--json", "number,title,author,closedAt,labels"]
    )
    issues = json.loads(out)
    issues.sort(key=lambda i: i.get("closedAt") or "", reverse=True)
    return issues


# ---------------------------------------------------------------- rendering

def date_part(iso: str | None) -> str:
    return (iso or "")[:10]


def label_names(issue: dict) -> str:
    names = [lbl["name"] for lbl in issue.get("labels") or []]
    return ", ".join(names)


def author_login(issue: dict) -> str:
    return (issue.get("author") or {}).get("login", "")


def milestone_title(issue: dict) -> str:
    ms = issue.get("milestone")
    return ms["title"] if ms else ""


def assignee_logins(issue: dict) -> str:
    logins = [a["login"] for a in issue.get("assignees") or []]
    return ", ".join(logins)


def table_cell(text: str) -> str:
    return text.replace("|", "\\|")


def dep_list(numbers: list[int] | None, available: bool) -> str:
    if not available:
        return "unavailable via API"
    if not numbers:
        return "none"
    return ", ".join(f"#{n}" for n in numbers)


def render(stamp: str, repo: str, open_issues: list[dict],
           deps: dict[int, tuple[list[int], list[int]]],
           deps_available: bool, closed_issues: list[dict]) -> str:
    lines: list[str] = []
    add = lines.append

    add("# Shyland Issues Report")
    add("")
    add(f"- Generated: {stamp}")
    add(f"- Repo: {repo}")
    add(f"- Open issues: {len(open_issues)}")
    add(f"- Closed issues: {len(closed_issues)}")
    add(f"- Dependency data: "
        f"{'available' if deps_available else 'unavailable via API'}")
    add("")

    add("## Open Issues — Summary Table")
    add("")
    add("| # | Title | Author | Labels | Milestone | Updated |")
    add("|---|---|---|---|---|---|")
    for issue in open_issues:
        add(f"| {issue['number']} "
            f"| {table_cell(issue['title'])} "
            f"| {table_cell(author_login(issue))} "
            f"| {table_cell(label_names(issue))} "
            f"| {table_cell(milestone_title(issue))} "
            f"| {date_part(issue.get('updatedAt'))} |")
    add("")

    add("## Open Issues — Full Detail")
    add("")
    for issue in open_issues:
        n = issue["number"]
        blocked_by, blocks = deps.get(n, ([], []))
        add(f"## Issue #{n}: {issue['title']}")
        add("")
        add("- State: open")
        add(f"- Author: {author_login(issue) or 'unknown'}")
        add(f"- Labels: {label_names(issue) or 'none'}")
        add(f"- Milestone: {milestone_title(issue) or 'none'}")
        add(f"- Assignees: {assignee_logins(issue) or 'none'}")
        add(f"- Created: {date_part(issue.get('createdAt'))} "
            f"| Updated: {date_part(issue.get('updatedAt'))}")
        add(f"- Blocked by: {dep_list(blocked_by, deps_available)}")
        add(f"- Blocks: {dep_list(blocks, deps_available)}")
        add(f"- URL: {issue['url']}")
        add("")
        add("### Body")
        add("")
        add(issue.get("body") or "")
        add("")
        comments = sorted(issue.get("comments") or [],
                          key=lambda c: c.get("createdAt") or "")
        add(f"### Comments ({len(comments)})")
        add("")
        if not comments:
            add("None.")
            add("")
        else:
            for c in comments:
                author = (c.get("author") or {}).get("login", "unknown")
                add(f"**{author}** — {date_part(c.get('createdAt'))}:")
                add(c.get("body") or "")
                add("")

    add("## Closed Issues — Summary Table")
    add("")
    add("| # | Title | Author | Labels | Closed |")
    add("|---|---|---|---|---|")
    for issue in closed_issues:
        add(f"| {issue['number']} "
            f"| {table_cell(issue['title'])} "
            f"| {table_cell(author_login(issue))} "
            f"| {table_cell(label_names(issue))} "
            f"| {date_part(issue.get('closedAt'))} |")
    add("")

    return "\n".join(lines)


# --------------------------------------------------------------------- main

def main() -> None:
    check_auth()
    root = repo_root()
    repo = repo_name()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    numbers = fetch_open_numbers()
    open_issues = [fetch_issue(n) for n in numbers]

    deps: dict[int, tuple[list[int], list[int]]] = {}
    deps_available = True
    for n in numbers:
        if not deps_available:
            break
        result = fetch_dependencies(n)
        if result is None:
            deps_available = False
            deps.clear()
        else:
            deps[n] = result

    closed_issues = fetch_closed()

    out_dir = root / "docs" / "shyland"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"Shyland_Issues_Report_{stamp}.md"
    if out_path.exists():
        sys.exit(f"FATAL: {out_path} already exists; refusing to overwrite.")
    out_path.write_text(
        render(stamp, repo, open_issues, deps, deps_available, closed_issues),
        encoding="utf-8",
    )

    print(f"Report written: {out_path}")
    print(f"Open issues: {len(open_issues)}")
    print(f"Closed issues: {len(closed_issues)}")
    print(f"Dependency data: "
          f"{'available' if deps_available else 'unavailable via API'}")


if __name__ == "__main__":
    main()
