import logging
from typing import List, Optional, Dict
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class SectorDataProvider:
    def __init__(self):
        self._tushare_available = False
        self._ts_pro = None
        self._init_tushare()
        self._stock_to_sector_cache: Optional[Dict[str, dict]] = None

    def _build_stock_to_sector_cache(self):
        cache: Dict[str, dict] = {}
        sectors = self.get_sw_sector_list()
        for sector in sectors:
            consts = self.get_sector_constituents(sector["sector_code"])
            for c in consts:
                code = c.get("ts_code", "").strip()
                if code and code not in cache:
                    cache[code] = {
                        "stock_code": code,
                        "sector_code": sector["sector_code"],
                        "sector_name": sector["sector_name"],
                    }
        self._stock_to_sector_cache = cache
        logger.info(f"Built stock→sector cache: {len(cache)} stocks mapped")

    def get_stock_sector_mapping(self, ts_code: str) -> Optional[dict]:
        if self._stock_to_sector_cache is None:
            self._build_stock_to_sector_cache()
        return self._stock_to_sector_cache.get(ts_code.strip())

    def get_sector_daily(self, sector_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        if self._tushare_available:
            try:
                df = self._ts_pro.index_daily(
                    ts_code=sector_code,
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                )
                if df is not None and not df.empty:
                    df["trade_date"] = pd.to_datetime(df["trade_date"])
                    df = df.sort_values("trade_date")
                    return df
            except Exception as e:
                logger.warning(f"Tushare sector daily failed: {e}")

        try:
            import akshare as ak
            name_map = {}
            for s in self.get_sw_sector_list():
                name_map[s["sector_code"]] = s["sector_name"]
            sector_name = name_map.get(sector_code, sector_code)
            df = ak.stock_board_industry_index_ths(symbol=sector_name)
            if df is not None and not df.empty:
                df.columns = [c.strip() for c in df.columns]
                return df
        except Exception as e:
            logger.warning(f"AKShare sector daily failed: {e}")

        return pd.DataFrame()


_sector_provider: Optional[SectorDataProvider] = None


def get_sector_data_provider() -> SectorDataProvider:
    global _sector_provider
    if _sector_provider is None:
        _sector_provider = SectorDataProvider()
    return _sector_provider
