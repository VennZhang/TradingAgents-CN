import logging
from typing import List, Optional, Dict
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

TARGET_INDICES = {
    "000016.SH": {"name": "上证50", "market": "SSE", "display": "上证50", "futures": "IH"},
    "000300.SH": {"name": "沪深300", "market": "CSI", "display": "沪深300", "futures": "IF"},
    "000905.SH": {"name": "中证500", "market": "CSI", "display": "中证500", "futures": "IC"},
    "000852.SH": {"name": "中证1000", "market": "CSI", "display": "中证1000", "futures": "IM"},
    "000688.SH": {"name": "科创50", "market": "SSE", "display": "科创50", "futures": "-"},
    "399006.SZ": {"name": "创业板指", "market": "SZSE", "display": "创业板指", "futures": "-"},
}


class IndexDataProvider:
    def __init__(self):
        self._tushare_available = False
        self._ts_pro = None
        self._init_tushare()

    def _init_tushare(self):
        try:
            from app.core.config import settings
            token = settings.TUSHARE_TOKEN
            if not token:
                logger.info("Tushare token not configured, index data uses AKShare only")
                return
            import tushare as ts
            self._ts_pro = ts.pro_api(token)
            self._tushare_available = True
            logger.info("Tushare initialized for index data")
        except Exception as e:
            logger.warning(f"Tushare init failed for index data: {e}")

    def get_index_metadata(self) -> List[dict]:
        return [
            {"code": k, "name": v["name"], "market": v["market"], "display": v["display"], "futures": v.get("futures", "-")}
            for k, v in TARGET_INDICES.items()
        ]

    def get_index_daily(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        if self._tushare_available:
            try:
                df = self._ts_pro.index_daily(
                    ts_code=index_code,
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                )
                if df is not None and not df.empty:
                    df["trade_date"] = pd.to_datetime(df["trade_date"])
                    df = df.sort_values("trade_date")
                    return df
            except Exception as e:
                logger.warning(f"Tushare index daily failed for {index_code}: {e}")

        try:
            import akshare as ak
            index_name = TARGET_INDICES.get(index_code, {}).get("display", index_code)
            if index_code == "000016.SH":
                symbol = "000016"
            elif index_code == "000300.SH":
                symbol = "000300"
            elif index_code == "000905.SH":
                symbol = "000905"
            elif index_code == "000852.SH":
                symbol = "000852"
            elif index_code == "000688.SH":
                symbol = "000688"
            elif index_code == "399006.SZ":
                symbol = "399006"
            else:
                symbol = index_code.split(".")[0]

            change = {"日": "daily", "周": "weekly", "月": "monthly"}
            for period, freq in change.items():
                try:
                    df = ak.stock_zh_index_daily_em(symbol=f"sh{symbol}" if ".SH" in index_code else f"sz{symbol}")
                    if df is not None and not df.empty:
                        return df
                except Exception:
                    try:
                        df = ak.stock_zh_index_daily(symbol=f"sh{symbol}" if ".SH" in index_code else f"sz{symbol}")
                        if df is not None and not df.empty:
                            return df
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"AKShare index daily failed for {index_code}: {e}")

        return pd.DataFrame()

    def get_index_constituents(self, index_code: str) -> List[dict]:
        if self._tushare_available:
            try:
                df = self._ts_pro.index_weight(
                    index_code=index_code,
                    trade_date=datetime.now().strftime("%Y%m%d"),
                )
                if df is None or df.empty:
                    dates = self._ts_pro.trade_cal(
                        exchange="SSE",
                        start_date="20200101",
                        end_date=datetime.now().strftime("%Y%m%d"),
                        is_open="1",
                    )
                    if dates is not None and not dates.empty:
                        dates = dates.sort_values("cal_date", ascending=False)
                        for _, date_row in dates.head(10).iterrows():
                            trade_date = date_row["cal_date"]
                            df = self._ts_pro.index_weight(
                                index_code=index_code,
                                trade_date=trade_date,
                            )
                            if df is not None and not df.empty:
                                break
                if df is not None and not df.empty:
                    result = []
                    for _, row in df.iterrows():
                        result.append({
                            "con_code": str(row.get("con_code", "")).strip(),
                            "weight": float(row.get("weight", 0)),
                        })
                    return result
            except Exception as e:
                logger.warning(f"Tushare index constituents failed for {index_code}: {e}")

        try:
            import akshare as ak
            symbol_map = {
                "000016.SH": "000016",
                "000300.SH": "000300",
                "000905.SH": "000905",
                "000852.SH": "000852",
                "000688.SH": "000688",
                "399006.SZ": "399006",
            }
            symbol = symbol_map.get(index_code)
            if symbol:
                df = ak.index_stock_cons_weight_csindex(symbol=symbol)
                if df is not None and not df.empty:
                    result = []
                    for _, row in df.iterrows():
                        result.append({
                            "con_code": str(row.get("成分券代码", row.get("stock_code", ""))).strip(),
                            "name": str(row.get("成分券名称", row.get("stock_name", ""))).strip(),
                            "weight": float(row.get("权重", 0)),
                        })
                    return result
        except Exception as e:
            logger.warning(f"AKShare index constituents failed for {index_code}: {e}")

        return []

    def get_index_sector_weights(self, index_code: str) -> dict:
        from .sector_data import get_sector_data_provider

        constituents = self.get_index_constituents(index_code)
        if not constituents:
            return {}

        sector_provider = get_sector_data_provider()
        sector_weights: Dict[str, float] = {}
        unmapped_weight = 0.0

        for const in constituents:
            stock_code = const.get("con_code", "")
            weight = const.get("weight", 0)
            mapping = sector_provider.get_stock_sector_mapping(stock_code)
            if mapping:
                sn = mapping["sector_name"]
                sector_weights[sn] = sector_weights.get(sn, 0) + weight
            else:
                unmapped_weight += weight

        if unmapped_weight > 0 and sector_weights:
            spread = unmapped_weight / len(sector_weights)
            for k in sector_weights:
                sector_weights[k] += spread
        elif not sector_weights and unmapped_weight > 0:
            sector_weights["其他"] = unmapped_weight

        total = sum(sector_weights.values())
        if total > 0:
            sector_weights = {k: round(v / total * 100, 2) for k, v in sector_weights.items()}

        return dict(sorted(sector_weights.items(), key=lambda x: x[1], reverse=True))


_index_provider: Optional[IndexDataProvider] = None


def get_index_data_provider() -> IndexDataProvider:
    global _index_provider
    if _index_provider is None:
        _index_provider = IndexDataProvider()
    return _index_provider
