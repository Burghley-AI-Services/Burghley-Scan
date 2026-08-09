#!/usr/bin/env python3
"""
Burghley Scan - free, open-source lite scanner.

This is a genuine reduced-config subset of Burghley AI Services' paid
scanning engine: same detection logic for the rules it includes, just a
smaller rule set and aggregate-only output. It is NOT a separate tool.

What it deliberately does NOT do, by design, not by omission:
  - No secrets detection of any kind (API keys, passwords, connection
    strings, private keys). Finding a live exposed secret and disclosing
    it only behind a paywall would be withholding a known active
    security risk for commercial leverage - so this scan never even
    looks for one.
  - No file paths, line numbers, commit hashes, author names, or dates
    in its output. Category-level aggregate counts only.
  - Zero network calls. Nothing is written to disk and nothing is sent
    anywhere, ever. Everything below is stdlib-only and local.

Full paid audit: https://burghley-ai-services.co.uk
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERSION = "1.0.0-lite"

CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".cs", ".java", ".go", ".rb", ".php"}
EXCLUDE_DIRS = {".git", "node_modules", "bin", "obj", "dist", "build", ".venv", "venv", "__pycache__"}

# --- Time window ---
# Recent activity only, so the scan stays fast and reflects current practice
# rather than a repo's entire history. Try a 30-day window first; if that's
# too thin to say anything useful, fall back to the last N commits instead
# so a low-activity repo doesn't come back looking (falsely) clean.
WINDOW_DAYS = 30
MIN_COMMITS_FOR_DAY_WINDOW = 5
FALLBACK_COMMIT_COUNT = 50

DEBT_GENERIC_VAR_PATTERN = re.compile(r"\b(temp|tmp|data|value|result)\b")

CO_AUTHOR_AI_PATTERN = re.compile(
    r"co-authored-by:.*(claude|copilot|chatgpt|openai|gpt-4|gemini|cursor)", re.I
)
AI_FOOTER_PATTERN = re.compile(
    r"generated\s+(with|by|using)\b.{0,20}?\b(claude|copilot|chatgpt|gpt|gemini|cursor|ai)\b", re.I
)
GENERIC_COMMIT_SUBJECTS = {
    "add error handling", "refactor function", "improve code quality", "fix bug",
    "update code", "clean up code", "add tests", "improve performance",
    "add comments", "refactor code", "fix issue", "update logic", "code cleanup",
    "minor fixes", "general improvements",
}
BOILERPLATE_COMMENT_PATTERN = re.compile(
    r"^\s*(//|#)\s*(increment|initialize|initialise|declare a variable|"
    r"loop through|return the result|set the value|assign the value|"
    r"check if|create a new|define the)\b", re.I
)

NODE_BUILTIN_MODULES = {
    "fs", "path", "http", "https", "os", "crypto", "util", "events", "stream",
    "url", "querystring", "child_process", "assert", "buffer", "net", "dns",
    "readline", "zlib", "process", "cluster", "timers",
}

try:
    PYTHON_STDLIB = set(sys.stdlib_module_names)
except AttributeError:
    PYTHON_STDLIB = {
        "os", "sys", "re", "json", "math", "random", "datetime", "collections",
        "itertools", "functools", "subprocess", "pathlib", "typing", "logging",
        "unittest", "argparse", "io", "time", "copy", "csv", "sqlite3", "hashlib",
    }

JS_IMPORT_PATTERN = re.compile(r"""from\s+['"]([^'".][^'"]*)['"]|require\(\s*['"]([^'".][^'"]*)['"]\s*\)""")
PY_IMPORT_PATTERN = re.compile(r"^\s*(?:import|from)\s+([A-Za-z0-9_]+)")

TEST_FILENAME_PATTERNS = [
    re.compile(r"^(.+)Tests$"),
    re.compile(r"^(.+)Test$"),
    re.compile(r"^test_(.+)$", re.I),
    re.compile(r"^(.+)_test$", re.I),
    re.compile(r"^(.+)\.test$", re.I),
    re.compile(r"^(.+)\.spec$", re.I),
]

KNOWN_VENDOR_NAMES = (
    "jquery", "modernizr", "bootstrap", "popper", "plugins", "slick",
    "lazysizes", "fontawesome", "font-awesome", "moment", "lodash",
    "underscore", "respond", "html5shiv", "polyfill", "normalize",
    "waypoints", "coffee-script", "require.js", "requirejs", "d3.min",
    "chart.js", "swiper", "owl.carousel", "select2",
)
LICENSE_HEADER_MARKERS = (
    "@license", "licensed under", "jquery foundation", "opensource.org/licenses",
    "this program is free software", "mit license", "apache license",
    "all rights reserved", "released under the",
)
MINIFIED_AVG_LINE_LENGTH_THRESHOLD = 300
GENERATED_FILE_MARKERS = (".generated.", ".designer.", ".g.", ".g.i.", ".min.")

LARGE_COMMIT_PRODUCTION_FILE_THRESHOLD = 3


def extract_test_subject(stem: str):
    for pattern in TEST_FILENAME_PATTERNS:
        m = pattern.match(stem)
        if m:
            subject = m.group(1).rstrip("._-")
            if subject:
                return subject.lower()
    return None


def is_test_path(rel_path: str) -> bool:
    lower = rel_path.lower()
    if "/tests/" in f"/{lower}" or ".tests/" in lower or lower.startswith("test/"):
        return True
    return extract_test_subject(Path(rel_path).stem) is not None


def is_vendor_path(rel_path: str) -> bool:
    name_lower = Path(rel_path).name.lower()
    return any(vendor in name_lower for vendor in KNOWN_VENDOR_NAMES)


def is_generated_file(repo_file: Path) -> bool:
    name_lower = repo_file.name.lower()
    return any(marker in name_lower for marker in GENERATED_FILE_MARKERS)


def is_third_party_file(repo_file: Path, text: str, lines: list) -> bool:
    name_lower = repo_file.name.lower()
    if any(vendor in name_lower for vendor in KNOWN_VENDOR_NAMES):
        return True
    header_text = "\n".join(lines[:30]).lower()
    if any(marker in header_text for marker in LICENSE_HEADER_MARKERS):
        return True
    if lines:
        avg_line_length = len(text) / len(lines)
        if avg_line_length > MINIFIED_AVG_LINE_LENGTH_THRESHOLD:
            return True
    return False


def should_scan(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return False
    return path.suffix in CODE_EXTENSIONS


def get_tracked_files(repo: Path):
    """Return git-tracked file paths (relative, forward-slash), or None if this
    isn't a git repo. Restricting to tracked files keeps vendored/generated
    content out of scope, same rationale as the paid tool."""
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=repo, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=30,
        )
        if out.returncode != 0:
            return None
        return {line.strip() for line in out.stdout.splitlines() if line.strip()}
    except Exception:
        return None


def build_test_subject_index(tracked) -> set:
    index = set()
    for p in tracked:
        if Path(p).suffix not in CODE_EXTENSIONS:
            continue
        subject = extract_test_subject(Path(p).stem)
        if subject:
            index.add(subject)
    return index


def has_test_file(repo: Path, rel_path: str, test_index: set) -> bool:
    repo_file = repo / rel_path
    stem = repo_file.stem
    directory = repo_file.parent
    candidates = [
        f"{stem}.test{repo_file.suffix}",
        f"{stem}.spec{repo_file.suffix}",
        f"{stem}_test{repo_file.suffix}",
        f"test_{stem}{repo_file.suffix}",
    ]
    if any((directory / c).exists() for c in candidates):
        return True
    return stem.lower() in test_index


def load_js_dependencies(repo: Path):
    pkg = repo / "package.json"
    if not pkg.exists():
        return None
    try:
        import json
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except Exception:
        return None
    deps = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        deps.update((data.get(key) or {}).keys())
    return deps


def load_python_dependencies(repo: Path):
    req = repo / "requirements.txt"
    if not req.exists():
        return None
    deps = set()
    for line in req.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = re.split(r"[=<>~!\[; ]", line)[0].strip()
        if name:
            deps.add(name.lower().replace("_", "-"))
    return deps


def get_commits_in_window(repo: Path):
    """Return a list of commit dicts covering recent activity: the last 30
    days if that yields enough commits to say anything meaningful, otherwise
    the last FALLBACK_COMMIT_COUNT commits regardless of date, so a
    low-activity repo doesn't come back with an unconvincing empty result."""

    def _run_log(extra_args):
        try:
            out = subprocess.run(
                ["git", "log", "--name-only", "--date=short",
                 "--pretty=format:\x02%H\x1f%ad\x1f%B"] + extra_args,
                cwd=repo, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=60,
            )
        except Exception as e:
            print(f"WARN: could not read commit history - {e}", file=sys.stderr)
            return []
        if out.returncode != 0:
            return []
        commits = []
        for block in out.stdout.split("\x02"):
            block = block.strip("\n")
            if not block.strip():
                continue
            block_lines = block.split("\n")
            header = block_lines[0].split("\x1f", 2)
            if len(header) != 3:
                continue
            commit_hash, commit_date, body = header
            changed_files = [l.strip() for l in block_lines[1:] if l.strip()]
            commits.append({"hash": commit_hash, "date": commit_date, "body": body,
                             "files": changed_files})
        return commits

    since = (datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%d")
    commits = _run_log([f"--since={since}"])
    window_label = f"the last {WINDOW_DAYS} days"

    if len(commits) < MIN_COMMITS_FOR_DAY_WINDOW:
        fallback = _run_log([f"-n{FALLBACK_COMMIT_COUNT}"])
        if len(fallback) > len(commits):
            commits = fallback
            window_label = f"the last {len(commits)} commits"

    return commits, window_label


def scan_commits(commits):
    """Commit-message and commit-shape signals: AI-disclosure trailers/
    footers, generic AI-flavoured wording, and large commits with no
    accompanying test changes. Returns aggregate counts only."""
    counts = {
        "ai_signal_co_authored_trailer": 0,
        "ai_signal_generated_footer": 0,
        "ai_signal_generic_commit_message": 0,
        "large_commit_no_test_changes": 0,
    }
    touched_files = set()

    for commit in commits:
        body = commit["body"]
        subject = body.strip().splitlines()[0].strip() if body.strip() else ""

        if CO_AUTHOR_AI_PATTERN.search(body):
            counts["ai_signal_co_authored_trailer"] += 1
        if AI_FOOTER_PATTERN.search(body):
            counts["ai_signal_generated_footer"] += 1
        if subject.lower() in GENERIC_COMMIT_SUBJECTS:
            counts["ai_signal_generic_commit_message"] += 1

        changed_files = commit["files"]
        production_files = [
            f for f in changed_files
            if Path(f).suffix in CODE_EXTENSIONS and not is_test_path(f) and not is_vendor_path(f)
        ]
        test_files_touched = [f for f in changed_files if is_test_path(f)]
        if len(production_files) >= LARGE_COMMIT_PRODUCTION_FILE_THRESHOLD and not test_files_touched:
            counts["large_commit_no_test_changes"] += 1

        touched_files.update(changed_files)

    return counts, touched_files


def scan_files(repo: Path, rel_paths, tracked, test_index, js_deps, py_deps):
    """File-content signals over the set of files touched within the scan
    window. Returns aggregate counts only - no file paths in the output."""
    counts = {
        "ai_signal_boilerplate_comment": 0,
        "ai_signal_hallucinated_dependency": 0,
        "oversized_file": 0,
        "generic_naming_density": 0,
        "untested_file": 0,
    }
    files_scanned = 0

    for rel_path in sorted(rel_paths):
        path = repo / rel_path
        if not path.is_file() or not should_scan(path):
            continue
        if tracked is not None and rel_path not in tracked:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        lines = text.splitlines()
        total_lines = len(lines)

        if is_third_party_file(path, text, lines):
            continue

        files_scanned += 1

        if any(BOILERPLATE_COMMENT_PATTERN.match(line) for line in lines):
            counts["ai_signal_boilerplate_comment"] += 1

        if total_lines > 500:
            counts["oversized_file"] += 1

        if total_lines > 0:
            generic_hits = sum(1 for l in lines if DEBT_GENERIC_VAR_PATTERN.search(l))
            if generic_hits / total_lines > 0.05:
                counts["generic_naming_density"] += 1

        if scan_file_has_hallucinated_dependency(path, lines, js_deps, py_deps):
            counts["ai_signal_hallucinated_dependency"] += 1

        if not has_test_file(repo, rel_path, test_index) and not is_generated_file(path):
            counts["untested_file"] += 1

    return counts, files_scanned


def scan_file_has_hallucinated_dependency(file: Path, lines, js_deps, py_deps) -> bool:
    suffix = file.suffix.lower()
    if suffix in (".js", ".ts", ".jsx", ".tsx") and js_deps is not None:
        for line in lines:
            m = JS_IMPORT_PATTERN.search(line)
            if not m:
                continue
            pkg_path = m.group(1) or m.group(2)
            if not pkg_path:
                continue
            pkg_name = "/".join(pkg_path.split("/")[:2]) if pkg_path.startswith("@") else pkg_path.split("/")[0]
            if pkg_name in NODE_BUILTIN_MODULES or pkg_name in js_deps:
                continue
            return True
    elif suffix == ".py" and py_deps is not None:
        for line in lines:
            m = PY_IMPORT_PATTERN.match(line)
            if not m:
                continue
            module_name = m.group(1)
            normalised = module_name.lower().replace("_", "-")
            if module_name in PYTHON_STDLIB or normalised in py_deps or module_name in py_deps:
                continue
            return True
    return False


def _find_git_root(path: Path):
    """Resolve to the repository's top-level directory. `git log --name-only`
    always reports paths relative to the repo root regardless of cwd, while
    other commands are cwd-relative - normalising to the root here keeps every
    path the scan collects on the same footing, even if the user points the
    tool at a subdirectory of a larger repo."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=path, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=10,
        )
        if out.returncode != 0:
            return None
        return Path(out.stdout.strip())
    except Exception:
        return None


def run_scan(repo_path_str="."):
    repo = Path(repo_path_str).resolve()
    if not repo.is_dir():
        raise ValueError(f"Not a directory: {repo}")

    git_root = _find_git_root(repo)
    if git_root is None:
        raise ValueError(
            f"{repo} does not look like a git repository (or git isn't on your PATH). "
            "This tool needs git history to work."
        )
    repo = git_root

    tracked = get_tracked_files(repo)
    if tracked is None:
        raise ValueError(
            f"{repo} does not look like a git repository (or git isn't on your PATH). "
            "This tool needs git history to work."
        )

    commits, window_label = get_commits_in_window(repo)
    if not commits:
        print("No commit history found to scan.")

    commit_counts, touched_files = scan_commits(commits)

    js_deps = load_js_dependencies(repo)
    py_deps = load_python_dependencies(repo)
    test_index = build_test_subject_index(tracked)

    file_counts, files_scanned = scan_files(repo, touched_files, tracked, test_index, js_deps, py_deps)

    ai_signal_total = (
        commit_counts["ai_signal_co_authored_trailer"]
        + commit_counts["ai_signal_generated_footer"]
        + commit_counts["ai_signal_generic_commit_message"]
        + file_counts["ai_signal_boilerplate_comment"]
        + file_counts["ai_signal_hallucinated_dependency"]
    )

    summary = {
        "commits_scanned": len(commits),
        "window_label": window_label,
        "files_scanned": files_scanned,
        "large_commit_no_test_changes": commit_counts["large_commit_no_test_changes"],
        "untested_file": file_counts["untested_file"],
        "possible_ai_usage_signals": ai_signal_total,
        "oversized_file": file_counts["oversized_file"],
        "generic_naming_density": file_counts["generic_naming_density"],
    }
    return summary


def print_summary(summary):
    print(f"Scanned {summary['files_scanned']} files touched across {summary['commits_scanned']} "
          f"commits over {summary['window_label']}")
    print(f"Large commits with no test changes: {summary['large_commit_no_test_changes']}")
    print(f"Untested files: {summary['untested_file']}")
    print(f"Possible AI-usage signals: {summary['possible_ai_usage_signals']}")
    print(f"Oversized files: {summary['oversized_file']}")
    print(f"Generic naming density: {summary['generic_naming_density']}")
    print()
    print("These are correlation signals, not proof. See the README for how to read them.")
    print("Nothing was uploaded or written to disk. This scan ran entirely on your machine.")


def main():
    parser = argparse.ArgumentParser(
        description="Burghley Scan (lite) - free, offline scan for ungoverned AI-usage patterns. "
                     "Prints aggregate category counts only. Nothing is uploaded, nothing is written to disk."
    )
    parser.add_argument("repo_path", nargs="?", default=".",
                        help="Path to the repository to scan. Defaults to the current directory.")
    parser.add_argument("--version", action="version", version=f"burghley-scan {VERSION}")
    args = parser.parse_args()

    try:
        summary = run_scan(args.repo_path)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    print_summary(summary)


if __name__ == "__main__":
    main()
