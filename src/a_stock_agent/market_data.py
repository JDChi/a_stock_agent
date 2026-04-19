from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class StockSnapshot:
    symbol: str
    name: str
    price: float | None
    change_pct: float | None
    volume: float | None
    turnover_rate: float | None
    fetched_at: str
    source: str

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HistoryRow:
    date: str
    open: float | None
    close: float | None
    high: float | None
    low: float | None
    volume: float | None
    change_pct: float | None
    turnover_rate: float | None


@dataclass(frozen=True)
class StockHistory:
    symbol: str
    adjust: str
    rows: list[HistoryRow]
    fetched_at: str
    source: str

    def model_dump(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "adjust": self.adjust,
            "rows": [asdict(row) for row in self.rows],
            "fetched_at": self.fetched_at,
            "source": self.source,
        }


class AKShareService:
    def __init__(self, client: Any | None = None):
        if client is None:
            import akshare as ak

            client = ak
        self.client = client

    def get_stock_snapshot(self, symbol: str) -> StockSnapshot:
        df = self.client.stock_zh_a_spot_em()
        row = _find_row(df, "代码", symbol)
        if row is None:
            raise ValueError(f"No AKShare snapshot found for symbol {symbol}")
        return StockSnapshot(
            symbol=str(row.get("代码", symbol)),
            name=str(row.get("名称", "")),
            price=_to_float(row.get("最新价")),
            change_pct=_to_float(row.get("涨跌幅")),
            volume=_to_float(row.get("成交量")),
            turnover_rate=_to_float(row.get("换手率")),
            fetched_at=_now(),
            source="akshare.stock_zh_a_spot_em",
        )

    def get_stock_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq",
    ) -> StockHistory:
        df = self.client.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )
        rows = [
            HistoryRow(
                date=str(row.get("日期", "")),
                open=_to_float(row.get("开盘")),
                close=_to_float(row.get("收盘")),
                high=_to_float(row.get("最高")),
                low=_to_float(row.get("最低")),
                volume=_to_float(row.get("成交量")),
                change_pct=_to_float(row.get("涨跌幅")),
                turnover_rate=_to_float(row.get("换手率")),
            )
            for row in _records(df)
        ]
        return StockHistory(
            symbol=symbol,
            adjust=adjust,
            rows=rows,
            fetched_at=_now(),
            source="akshare.stock_zh_a_hist",
        )

    def get_company_profile(self, symbol: str) -> dict[str, Any]:
        df = self.client.stock_individual_info_em(symbol=symbol)
        profile = {"symbol": symbol, "source": "akshare.stock_individual_info_em", "fetched_at": _now()}
        for row in _records(df):
            key = row.get("item") or row.get("项目")
            value = row.get("value") or row.get("值")
            if key:
                profile[str(key)] = value
        return profile

    def get_financial_indicators(self, symbol: str, start_year: int | None = None) -> dict[str, Any]:
        df = self.client.stock_financial_analysis_indicator(symbol=symbol)
        rows = _records(df)
        if start_year is not None:
            rows = [row for row in rows if str(row.get("日期", ""))[:4].isdigit() and int(str(row["日期"])[:4]) >= start_year]
        return {
            "symbol": symbol,
            "rows": rows,
            "fetched_at": _now(),
            "source": "akshare.stock_financial_analysis_indicator",
        }


def _records(df: Any) -> list[dict[str, Any]]:
    if hasattr(df, "to_dict"):
        return list(df.to_dict(orient="records"))
    return list(df)


def _find_row(df: Any, column: str, value: str) -> dict[str, Any] | None:
    for row in _records(df):
        if str(row.get(column)) == value:
            return row
    return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
