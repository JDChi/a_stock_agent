# AKShare Proxy Allowlist

This document is the day-to-day reference for choosing AKShare or efinance market data interfaces in this project.

Default policy:

- Prefer interfaces that are not listed here.
- Use `akshare-proxy-patch` only for the URLs listed in this table.
- Do not broaden the proxy patch to all Eastmoney domains without an explicit decision.
- Re-run `scripts/check_akshare_proxy_allowlist.py` only when AKShare is upgraded, this table changes, or a new market-data interface is being evaluated.

## Allowlisted Interfaces

| Library | Function | Eastmoney URL | Approx Cost | Notes |
| --- | --- | --- | --- | --- |
| akshare | `ak.stock_zh_a_spot_em` | `https://82.push2.eastmoney.com/api/qt/clist/get` | 12-18 | A-share realtime quote pagination. Expensive; prefer cached responses. |
| akshare | `ak.stock_individual_info_em` | `https://push2.eastmoney.com/api/qt/stock/get` | 1-2 | Individual stock profile. |
| akshare | `ak.stock_board_industry_name_em` | `https://17.push2.eastmoney.com/api/qt/clist/get` | 1-4 | Industry board list. |
| akshare | `ak.stock_zh_a_hist` | `https://push2his.eastmoney.com/api/qt/stock/kline/get` | 1-2 | Daily historical k-line. Prefer non-allowlisted alternatives if they satisfy the request. |
| akshare | `ak.stock_zh_a_hist_min_em` | `https://push2his.eastmoney.com/api/qt/stock/trends2/get` | 1 | Intraday trend data. |
| akshare | `ak.stock_zh_a_hist_min_em` | `https://push2his.eastmoney.com/api/qt/stock/kline/get` | 1 | Intraday k-line data. |
| akshare | `ef.stock_sector_fund_flow_rank` | `https://push2.eastmoney.com/api/qt/clist/get` | 1-2 | Sector fund-flow rank. |
| akshare | `ak.stock_individual_fund_flow` | `https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get` | 1 | Individual stock fund-flow history. |
| akshare | `ak.stock_individual_fund_flow_rank` | `https://push2.eastmoney.com/api/qt/clist/get` | 5-8 | Individual stock fund-flow rank. |
| efinance | `ef.stock.get_realtime_quotes` | `http://push2.eastmoney.com/api/qt/clist/get` | 5-10 | Realtime quotes via efinance. |
| efinance | `ef.stock.get_quote_history` | `https://push2his.eastmoney.com/api/qt/stock/kline/get` | 1-2 | Quote history via efinance. |

## Configured Hook URLs

`AKSHARE_PROXY_PATCH_HOOK_URLS` should include these URL fragments only:

```text
https://82.push2.eastmoney.com/api/qt/clist/get
https://push2.eastmoney.com/api/qt/stock/get
https://17.push2.eastmoney.com/api/qt/clist/get
https://push2his.eastmoney.com/api/qt/stock/kline/get
https://push2his.eastmoney.com/api/qt/stock/trends2/get
https://push2.eastmoney.com/api/qt/clist/get
https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get
http://push2.eastmoney.com/api/qt/clist/get
```

## Scanner Usage

Use the scanner for audits, not for every development task:

```bash
uv run python scripts/check_akshare_proxy_allowlist.py --format markdown
uv run python scripts/check_akshare_proxy_allowlist.py --format json --output data/akshare_allowlist_report.json
```

The generated report is an audit artifact. It is not the source of truth; this document is.
