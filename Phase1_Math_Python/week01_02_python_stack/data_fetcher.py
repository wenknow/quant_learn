"""
Week 01-02 周末任务：构建本地数据库
目标：从 Tushare/AkShare 下载数据，存储到本地，为后续研究做准备
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import time
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ============================================================
# Tushare 数据获取（需要注册 tushare.pro 获取token）
# ============================================================

class TushareDataFetcher:
    """
    Tushare数据获取器
    注册地址：https://tushare.pro
    免费用户每分钟限速，需要控制请求频率
    """

    def __init__(self, token: str = None):
        token = token or os.getenv('TUSHARE_TOKEN')
        if not token:
            raise ValueError("请设置 TUSHARE_TOKEN 环境变量或传入token参数")
        try:
            import tushare as ts
            ts.set_token(token)
            self.pro = ts.pro_api()
            logger.info("Tushare 连接成功")
        except ImportError:
            raise ImportError("请先安装 tushare: pip install tushare")

    def get_stock_list(self) -> pd.DataFrame:
        """获取A股全量股票列表"""
        df = self.pro.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,area,industry,list_date'
        )
        save_path = DATA_DIR / "stock_list.parquet"
        df.to_parquet(save_path)
        logger.info(f"股票列表已保存: {len(df)} 只股票 -> {save_path}")
        return df

    def get_daily_prices(self, ts_code: str,
                         start_date: str = '20150101',
                         end_date: str = None) -> pd.DataFrame:
        """获取单股票日线行情"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')

        df = self.pro.daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            fields='ts_code,trade_date,open,high,low,close,vol,amount'
        )
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date').set_index('trade_date')
        return df

    def download_index_daily(self,
                              index_codes: list = None,
                              start_date: str = '20150101') -> dict:
        """下载主要指数日线数据"""
        if index_codes is None:
            index_codes = {
                '000001.SH': '上证指数',
                '000300.SH': '沪深300',
                '000905.SH': '中证500',
                '000852.SH': '中证1000',
                '399006.SZ': '创业板指',
            }

        result = {}
        for code, name in index_codes.items():
            try:
                df = self.pro.index_daily(
                    ts_code=code,
                    start_date=start_date,
                    fields='ts_code,trade_date,open,high,low,close,vol,amount'
                )
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df = df.sort_values('trade_date').set_index('trade_date')

                save_path = DATA_DIR / f"index_{code.replace('.', '_')}.parquet"
                df.to_parquet(save_path)
                result[code] = df
                logger.info(f"✅ {name}({code}): {len(df)} 条记录")
                time.sleep(0.3)   # 控制请求频率
            except Exception as e:
                logger.error(f"❌ {name}({code}) 下载失败: {e}")

        return result

    def download_hs300_components(self, start_date: str = '20150101') -> pd.DataFrame:
        """下载沪深300成分股日线数据"""
        # 获取当前成分股
        hs300 = self.pro.index_weight(
            index_code='000300.SH',
            trade_date=datetime.now().strftime('%Y%m%d')
        )
        stock_list = hs300['con_code'].tolist()
        logger.info(f"沪深300成分股: {len(stock_list)} 只")

        all_data = []
        for i, code in enumerate(stock_list[:10]):  # 先下载前10只测试
            try:
                df = self.get_daily_prices(code, start_date)
                all_data.append(df)
                logger.info(f"[{i+1}/{len(stock_list[:10])}] {code}: {len(df)} 条")
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"❌ {code}: {e}")

        return pd.concat(all_data) if all_data else pd.DataFrame()


# ============================================================
# AkShare 数据获取（完全免费，无需注册）
# ============================================================

class AkShareDataFetcher:
    """
    AkShare数据获取器（免费，覆盖A/港/美股）
    文档：https://akshare.akfan.com
    """

    def __init__(self):
        try:
            import akshare as ak
            self.ak = ak
            logger.info("AkShare 加载成功")
        except ImportError:
            raise ImportError("请先安装 akshare: pip install akshare")

    def get_a_stock_daily(self, symbol: str,
                           start_date: str = "20150101",
                           end_date: str = None,
                           adjust: str = "qfq") -> pd.DataFrame:
        """
        获取A股日线（前复权）
        symbol: 股票代码，如 '000001'（不含交易所后缀）
        adjust: 复权方式 'qfq'前复权 / 'hfq'后复权 / ''不复权
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')

        df = self.ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        df.columns = ['date', 'open', 'close', 'high', 'low',
                      'volume', 'amount', 'amplitude', 'pct_change',
                      'change', 'turnover']
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        return df

    def get_us_stock_daily(self, symbol: str) -> pd.DataFrame:
        """获取美股日线（通过AkShare）"""
        df = self.ak.stock_us_hist(
            symbol=symbol,
            period="daily",
            adjust="qfq"
        )
        return df

    def get_hk_stock_daily(self, symbol: str,
                            start_date: str = "20150101") -> pd.DataFrame:
        """获取港股日线"""
        df = self.ak.stock_hk_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            adjust="qfq"
        )
        return df

    def get_fund_etf_daily(self, fund_code: str,
                            start_date: str = "20150101") -> pd.DataFrame:
        """
        获取ETF日线数据
        常用ETF：
        - 510300 沪深300ETF
        - 510500 中证500ETF
        - 159915 创业板ETF
        - 513100 纳斯达克ETF
        """
        df = self.ak.fund_etf_hist_sina(symbol=f"sh{fund_code}")
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['date'] >= start_date].set_index('date').sort_index()
        return df


# ============================================================
# 本地数据库管理
# ============================================================

class LocalDataBase:
    """简单的本地数据库（基于Parquet格式）"""

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or DATA_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, df: pd.DataFrame, name: str) -> Path:
        path = self.base_dir / f"{name}.parquet"
        df.to_parquet(path)
        logger.info(f"已保存: {path} ({len(df)} 行)")
        return path

    def load(self, name: str) -> pd.DataFrame:
        path = self.base_dir / f"{name}.parquet"
        if not path.exists():
            raise FileNotFoundError(f"找不到数据文件: {path}")
        df = pd.read_parquet(path)
        logger.info(f"已加载: {path} ({len(df)} 行)")
        return df

    def list_available(self) -> list:
        return [f.stem for f in self.base_dir.glob("*.parquet")]


# ============================================================
# 快速入门（直接运行这个文件）
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("量化数据获取入门")
    print("=" * 60)

    # 方法1：使用 AkShare（无需注册，推荐新手）
    print("\n📊 方法1：AkShare（免费，无需注册）")
    try:
        fetcher = AkShareDataFetcher()
        db = LocalDataBase()

        # 下载平安银行近5年数据
        print("正在下载平安银行(000001)数据...")
        df = fetcher.get_a_stock_daily('000001', start_date='20200101')
        db.save(df, 'stock_000001_daily')

        print(f"\n数据概览:")
        print(df.tail())
        print(f"\n日期范围: {df.index[0].date()} ~ {df.index[-1].date()}")
        print(f"数据条数: {len(df)}")

    except Exception as e:
        print(f"AkShare 获取失败: {e}")
        print("请先运行: pip install akshare")

    # 方法2：使用 Tushare（需要注册）
    print("\n📊 方法2：Tushare（需要注册获取token）")
    token = os.getenv('TUSHARE_TOKEN')
    if token:
        try:
            ts_fetcher = TushareDataFetcher(token)
            index_data = ts_fetcher.download_index_daily()
            print("指数数据下载完成！")
        except Exception as e:
            print(f"Tushare 获取失败: {e}")
    else:
        print("未设置 TUSHARE_TOKEN，请注册 tushare.pro 后设置环境变量")
        print("export TUSHARE_TOKEN=your_token_here")
