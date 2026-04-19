# Agent Development Notes

## Market Data Source Policy

- Prefer AKShare interfaces that do not match `AKSHARE_PROXY_PATCH_HOOK_URLS`.
- Before adding a new AKShare interface, inspect the underlying request URL with source search or `scripts/check_akshare_proxy_allowlist.py`.
- Use `akshare-proxy-patch` only for the explicit Eastmoney URL allowlist configured by `AKSHARE_PROXY_PATCH_HOOK_URLS`.
- Do not broaden the proxy patch to all Eastmoney domains without an explicit product decision.
- When two AKShare interfaces provide similar data, choose the non-allowlisted interface first.
- If an allowlisted interface is unavoidable, document why and prefer cache/fallback behavior around it.
- Keep `.env` secrets local. Never commit MiniMax keys or `AKSHARE_PROXY_PATCH_TOKEN`.

## Current Allowlist Intent

The proxy patch allowlist is intentionally narrow and based on known costly or fragile Eastmoney endpoints, including realtime quote, history, intraday, and fund-flow endpoints. Interfaces outside this allowlist should bypass proxy patching.

## Useful Verification Commands

```bash
uv run pytest
uv run python scripts/check_akshare_proxy_allowlist.py --format markdown
uv run python scripts/check_akshare_proxy_allowlist.py --format json --output data/akshare_allowlist_report.json
```
