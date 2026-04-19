from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


URL_PATTERN = re.compile(r"https?://[^\s'\"<>]+")


@dataclass(frozen=True)
class DiscoveredEndpoint:
    function_name: str
    source_file: str
    line: int
    url: str
    allowlisted: bool

    def model_dump(self) -> dict:
        return asdict(self)


def classify_url(url: str, allowlist: Iterable[str]) -> bool:
    return any(hook in url for hook in allowlist)


def discover_python_urls(root: str | Path, allowlist: Iterable[str]) -> list[DiscoveredEndpoint]:
    root_path = Path(root)
    hooks = list(allowlist)
    endpoints: list[DiscoveredEndpoint] = []
    for path in sorted(root_path.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        endpoints.extend(_discover_file_urls(path, hooks, root_path))
    return sorted(
        _dedupe(endpoints),
        key=lambda endpoint: (
            endpoint.allowlisted,
            endpoint.source_file,
            endpoint.function_name,
            endpoint.url,
        ),
    )


def render_markdown_report(endpoints: list[DiscoveredEndpoint]) -> str:
    non_allowlisted = [endpoint for endpoint in endpoints if not endpoint.allowlisted]
    allowlisted = [endpoint for endpoint in endpoints if endpoint.allowlisted]
    lines = [
        "# AKShare Proxy Allowlist Report",
        "",
        f"- Total discovered URLs: {len(endpoints)}",
        f"- Non-allowlisted URLs: {len(non_allowlisted)}",
        f"- Allowlisted URLs: {len(allowlisted)}",
        "",
        "## Non-Allowlisted URLs",
        "",
    ]
    lines.extend(_render_table(non_allowlisted))
    lines.extend(["", "## Allowlisted URLs", ""])
    lines.extend(_render_table(allowlisted))
    return "\n".join(lines).rstrip() + "\n"


def render_json_report(endpoints: list[DiscoveredEndpoint]) -> str:
    payload = {
        "total": len(endpoints),
        "non_allowlisted": sum(1 for endpoint in endpoints if not endpoint.allowlisted),
        "allowlisted": sum(1 for endpoint in endpoints if endpoint.allowlisted),
        "endpoints": [endpoint.model_dump() for endpoint in endpoints],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _discover_file_urls(path: Path, allowlist: list[str], root: Path) -> list[DiscoveredEndpoint]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    parent_by_child = _parent_map(tree)
    endpoints = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        for url in URL_PATTERN.findall(node.value):
            function = _enclosing_function_name(node, parent_by_child)
            endpoints.append(
                DiscoveredEndpoint(
                    function_name=function,
                    source_file=str(path.relative_to(root)),
                    line=getattr(node, "lineno", 0),
                    url=url.rstrip("),];"),
                    allowlisted=classify_url(url, allowlist),
                )
            )
    return endpoints


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _enclosing_function_name(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
    return "<module>"


def _dedupe(endpoints: Iterable[DiscoveredEndpoint]) -> list[DiscoveredEndpoint]:
    seen = set()
    result = []
    for endpoint in endpoints:
        key = (endpoint.function_name, endpoint.source_file, endpoint.url)
        if key in seen:
            continue
        seen.add(key)
        result.append(endpoint)
    return result


def _render_table(endpoints: list[DiscoveredEndpoint]) -> list[str]:
    if not endpoints:
        return ["No URLs found."]
    lines = [
        "| Function | Source | Line | URL |",
        "| --- | --- | ---: | --- |",
    ]
    for endpoint in endpoints:
        lines.append(
            f"| `{endpoint.function_name}` | `{endpoint.source_file}` | {endpoint.line} | `{endpoint.url}` |"
        )
    return lines
