from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from collections.abc import Iterator
from typing import Any

from .config import Settings


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
    _proxy_lock = threading.Lock()

    def __init__(self, client: Any | None = None, settings: Settings | None = None):
        if client is None:
            import akshare as ak

            client = ak
        self.client = client
        self.settings = settings or Settings()

    def get_stock_snapshot(self, symbol: str) -> StockSnapshot:
        with self._network_environment():
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
        with self._network_environment():
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
        with self._network_environment():
            df = self.client.stock_individual_info_em(symbol=symbol)
        profile = {"symbol": symbol, "source": "akshare.stock_individual_info_em", "fetched_at": _now()}
        for row in _records(df):
            key = row.get("item") or row.get("项目")
            value = row.get("value") or row.get("值")
            if key:
                profile[str(key)] = value
        return profile

    def get_financial_indicators(self, symbol: str, start_year: int | None = None) -> dict[str, Any]:
        with self._network_environment():
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

    @contextmanager
    def _network_environment(self) -> Iterator[None]:
        with self._proxy_lock:
            saved = {key: os.environ.get(key) for key in _PROXY_ENV_KEYS}
            try:
                _apply_proxy_environment(self.settings)
                yield
            finally:
                _restore_environment(saved)


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


_PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "NO_PROXY",
    "no_proxy",
)


def _apply_proxy_environment(settings: Settings) -> None:
    proxy_url = settings.akshare_proxy_url
    if proxy_url:
        for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
            os.environ[key] = proxy_url
        os.environ.pop("NO_PROXY", None)
        os.environ.pop("no_proxy", None)
        return

    if settings.akshare_disable_system_proxy:
        os.environ["NO_PROXY"] = "*"
        os.environ["no_proxy"] = "*"


def _restore_environment(saved: dict[str, str | None]) -> None:
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
