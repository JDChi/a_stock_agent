import pandas as pd

from a_stock_agent.market_data import AKShareService


class FakeAKShare:
    def stock_zh_a_spot_em(self):
        return pd.DataFrame(
            [
                {
                    "代码": "600519",
                    "名称": "贵州茅台",
                    "最新价": 1680.5,
                    "涨跌幅": 1.2,
                    "成交量": 1000,
                    "换手率": 0.3,
                }
            ]
        )

    def stock_zh_a_hist(self, **kwargs):
        assert kwargs["symbol"] == "600519"
        assert kwargs["adjust"] == "qfq"
        return pd.DataFrame(
            [
                {
                    "日期": "2024-01-02",
                    "开盘": 1600.0,
                    "收盘": 1610.0,
                    "最高": 1620.0,
                    "最低": 1590.0,
                    "成交量": 2000,
                    "涨跌幅": 0.5,
                    "换手率": 0.2,
                }
            ]
        )

    def stock_individual_info_em(self, symbol):
        return pd.DataFrame([{"item": "股票简称", "value": "贵州茅台"}])

    def stock_financial_analysis_indicator(self, symbol):
        return pd.DataFrame([{"日期": "2023-12-31", "净资产收益率(%)": 30.5}])


def test_stock_snapshot_normalizes_akshare_dataframe():
    service = AKShareService(client=FakeAKShare())

    snapshot = service.get_stock_snapshot("600519")

    assert snapshot.symbol == "600519"
    assert snapshot.name == "贵州茅台"
    assert snapshot.price == 1680.5
    assert snapshot.source == "akshare.stock_zh_a_spot_em"


def test_stock_history_normalizes_rows_and_preserves_adjustment():
    service = AKShareService(client=FakeAKShare())

    history = service.get_stock_history("600519", "20240101", "20240131", adjust="qfq")

    assert history.symbol == "600519"
    assert history.adjust == "qfq"
    assert history.rows[0].close == 1610.0
