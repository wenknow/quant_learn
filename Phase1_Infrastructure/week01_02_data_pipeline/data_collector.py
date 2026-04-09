"""
Week 1-2: 多交易所数据采集器
目标：统一接口采集 Binance/OKX/Bybit 历史K线 + 实时数据
"""
import ccxt
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CryptoDataCollector:
    """多交易所统一数据采集器"""

    SUPPORTED_EXCHANGES = ["binance", "okx", "bybit", "hyperliquid"]

    def __init__(self, exchange_id: str = "binance", api_key: str = "", api_secret: str = ""):
        self.exchange_id = exchange_id
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,  # 自动限速，避免被ban
        })
        logger.info(f"初始化交易所: {exchange_id}")

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        since_days: int = 365,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        采集历史K线数据

        Args:
            symbol: 交易对，如 "BTC/USDT"
            timeframe: 时间粒度，如 "1m", "5m", "1h", "1d"
            since_days: 采集过去多少天的数据
            limit: 每次请求的K线数量

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        since = self.exchange.parse8601(
            (datetime.now() - timedelta(days=since_days)).strftime("%Y-%m-%dT00:00:00Z")
        )

        all_ohlcv = []
        while True:
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 1  # 从最后一条记录的下一毫秒继续
                logger.info(f"{symbol} {timeframe}: 已采集 {len(all_ohlcv)} 条，最新: {pd.Timestamp(ohlcv[-1][0], unit='ms')}")

                if len(ohlcv) < limit:
                    break  # 已到最新数据

                time.sleep(self.exchange.rateLimit / 1000)  # 限速
            except ccxt.RateLimitExceeded:
                logger.warning("触发限速，等待60秒...")
                time.sleep(60)
            except Exception as e:
                logger.error(f"采集失败: {e}")
                break

        if not all_ohlcv:
            return pd.DataFrame()

        df = pd.DataFrame(all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.set_index("timestamp").drop_duplicates()
        return df

    def fetch_funding_rate_history(self, symbol: str, days: int = 90) -> pd.DataFrame:
        """采集资金费率历史（永续合约核心数据）"""
        if not self.exchange.has.get("fetchFundingRateHistory"):
            logger.warning(f"{self.exchange_id} 不支持资金费率历史查询")
            return pd.DataFrame()

        since = self.exchange.parse8601(
            (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
        )
        rates = self.exchange.fetch_funding_rate_history(symbol, since=since)

        if not rates:
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df[["datetime", "symbol", "fundingRate"]].set_index("datetime")

    def fetch_orderbook_snapshot(self, symbol: str, depth: int = 20) -> dict:
        """获取当前订单簿快照"""
        orderbook = self.exchange.fetch_order_book(symbol, limit=depth)
        return {
            "timestamp": datetime.now(),
            "symbol": symbol,
            "bids": orderbook["bids"][:depth],
            "asks": orderbook["asks"][:depth],
            "bid1": orderbook["bids"][0][0] if orderbook["bids"] else None,
            "ask1": orderbook["asks"][0][0] if orderbook["asks"] else None,
            "spread": (
                orderbook["asks"][0][0] - orderbook["bids"][0][0]
                if orderbook["bids"] and orderbook["asks"]
                else None
            ),
        }

    def scan_high_funding_rates(
        self, min_rate: float = 0.0003, quote: str = "USDT"
    ) -> pd.DataFrame:
        """扫描高资金费率品种（套利机会发现）"""
        logger.info(f"扫描 {self.exchange_id} 高资金费率品种 (>{min_rate*100:.3f}%)...")

        markets = self.exchange.load_markets()
        swap_symbols = [
            s for s, m in markets.items()
            if m.get("swap") and m.get("quote") == quote and m.get("active")
        ]

        results = []
        for symbol in swap_symbols[:50]:  # 限制数量避免限速
            try:
                rate_data = self.exchange.fetch_funding_rate(symbol)
                rate = rate_data.get("fundingRate", 0)
                if abs(rate) >= min_rate:
                    results.append({
                        "symbol": symbol,
                        "funding_rate": rate,
                        "annual_rate": rate * 3 * 365,  # 8h结算，一年3*365次
                        "next_funding_time": rate_data.get("fundingDatetime"),
                    })
                time.sleep(0.1)
            except Exception:
                continue

        df = pd.DataFrame(results).sort_values("funding_rate", ascending=False)
        return df


# ========================
# 快速测试
# ========================
if __name__ == "__main__":
    collector = CryptoDataCollector("binance")

    # 1. 采集BTC近30天1小时K线
    print("采集 BTC/USDT 1h K线...")
    btc_df = collector.fetch_ohlcv("BTC/USDT", "1h", since_days=30)
    print(btc_df.tail())
    print(f"共 {len(btc_df)} 条数据")

    # 2. 查看当前订单簿
    print("\n当前 BTC/USDT 订单簿:")
    ob = collector.fetch_orderbook_snapshot("BTC/USDT")
    print(f"  买一: {ob['bid1']}, 卖一: {ob['ask1']}, 价差: {ob['spread']:.2f}")

    # 3. 扫描高资金费率机会
    print("\n扫描高资金费率品种...")
    high_fr = collector.scan_high_funding_rates(min_rate=0.0002)
    print(high_fr.head(10).to_string())
