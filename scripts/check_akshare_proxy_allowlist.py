#!/usr/bin/env python
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from a_stock_agent.akshare_allowlist import (
    discover_python_urls,
    render_json_report,
    render_markdown_report,
)
from a_stock_agent.config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan AKShare source URLs and classify them against the proxy patch allowlist."
    )
    parser.add_argument("--akshare-root", type=Path, default=None)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    root = args.akshare_root or _installed_akshare_root()
    settings = Settings()
    endpoints = discover_python_urls(root, allowlist=settings.akshare_proxy_patch_hook_urls)
    report = render_json_report(endpoints) if args.format == "json" else render_markdown_report(endpoints)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")


def _installed_akshare_root() -> Path:
    spec = importlib.util.find_spec("akshare")
    if not spec or not spec.submodule_search_locations:
        raise RuntimeError("akshare is not installed")
    return Path(next(iter(spec.submodule_search_locations)))


if __name__ == "__main__":
    main()
