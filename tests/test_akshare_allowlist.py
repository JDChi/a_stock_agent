from pathlib import Path

from a_stock_agent.akshare_allowlist import (
    classify_url,
    discover_python_urls,
    render_markdown_report,
)


ALLOWLIST = [
    "https://push2his.eastmoney.com/api/qt/stock/kline/get",
    "https://82.push2.eastmoney.com/api/qt/clist/get",
]


def test_classify_url_matches_patch_substring_semantics():
    assert classify_url(
        "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.600519",
        ALLOWLIST,
    )
    assert not classify_url(
        "https://finance.sina.com.cn/realstock/company/sh000001/nc.shtml",
        ALLOWLIST,
    )


def test_discover_python_urls_groups_by_function_and_classifies(tmp_path):
    source = tmp_path / "stock_demo.py"
    source.write_text(
        '''
def stock_zh_a_hist():
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    return url

def stock_zh_index_daily():
    url = "https://finance.sina.com.cn/realstock/company/sh000001/nc.shtml"
    return url

OUTSIDE_FUNCTION_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
''',
        encoding="utf-8",
    )

    endpoints = discover_python_urls(tmp_path, allowlist=ALLOWLIST)

    by_url = {endpoint.url: endpoint for endpoint in endpoints}
    assert by_url["https://push2his.eastmoney.com/api/qt/stock/kline/get"].function_name == "stock_zh_a_hist"
    assert by_url["https://push2his.eastmoney.com/api/qt/stock/kline/get"].allowlisted is True
    assert by_url["https://finance.sina.com.cn/realstock/company/sh000001/nc.shtml"].function_name == "stock_zh_index_daily"
    assert by_url["https://finance.sina.com.cn/realstock/company/sh000001/nc.shtml"].allowlisted is False
    assert by_url["https://datacenter-web.eastmoney.com/api/data/v1/get"].function_name == "<module>"


def test_render_markdown_report_lists_non_allowlisted_section(tmp_path):
    source = tmp_path / "stock_demo.py"
    source.write_text(
        '''
def stock_zh_index_daily():
    return "https://finance.sina.com.cn/realstock/company/sh000001/nc.shtml"
''',
        encoding="utf-8",
    )
    endpoints = discover_python_urls(tmp_path, allowlist=ALLOWLIST)

    report = render_markdown_report(endpoints)

    assert "## Non-Allowlisted URLs" in report
    assert "stock_zh_index_daily" in report
    assert "finance.sina.com.cn" in report
