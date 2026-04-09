"""
Week 01 - Day 2: Pandas 核心
目标：掌握金融时间序列的Pandas操作，这是量化日常工作的基础
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. 时间序列索引（量化最重要的数据结构）
# ============================================================

# 创建交易日日期序列
trading_dates = pd.bdate_range('2020-01-01', '2024-12-31', freq='B')
print(f"交易日数量（含周末）: {len(trading_dates)}")

# 模拟股票价格数据
np.random.seed(42)
n = len(trading_dates)

df = pd.DataFrame({
    'open':   100 * np.cumprod(1 + np.random.normal(0.0005, 0.015, n)),
    'high':   None,
    'low':    None,
    'close':  100 * np.cumprod(1 + np.random.normal(0.0008, 0.015, n)),
    'volume': np.random.randint(1e6, 1e8, n).astype(float),
}, index=trading_dates)

df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.abs(np.random.normal(0, 0.005, n)))
df['low']  = df[['open', 'close']].min(axis=1) * (1 - np.abs(np.random.normal(0, 0.005, n)))

print("\n=== OHLCV 数据结构 ===")
print(df.tail())
print(f"\n数据类型:\n{df.dtypes}")

# ============================================================
# 2. 技术指标计算（rolling 的核心应用）
# ============================================================

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """添加常用技术指标"""
    close = df['close']

    # 移动平均线
    df['ma5']  = close.rolling(5).mean()
    df['ma10'] = close.rolling(10).mean()
    df['ma20'] = close.rolling(20).mean()
    df['ma60'] = close.rolling(60).mean()

    # 布林带
    df['bb_mid']   = close.rolling(20).mean()
    df['bb_std']   = close.rolling(20).std()
    df['bb_upper'] = df['bb_mid'] + 2 * df['bb_std']
    df['bb_lower'] = df['bb_mid'] - 2 * df['bb_std']
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']

    # 收益率
    df['ret_1d']  = close.pct_change(1)
    df['ret_5d']  = close.pct_change(5)
    df['ret_20d'] = close.pct_change(20)

    # 波动率
    df['vol_20d'] = df['ret_1d'].rolling(20).std() * np.sqrt(252)

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df['macd']        = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist']   = df['macd'] - df['macd_signal']

    # 成交量指标
    df['vol_ma20'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_ma20']   # 量比

    return df

df = add_technical_indicators(df)
print("\n=== 添加技术指标后 ===")
print(df[['close', 'ma20', 'bb_upper', 'bb_lower', 'rsi', 'vol_20d']].tail())

# ============================================================
# 3. resample：日线转月线（量化调仓常用）
# ============================================================

monthly = df['close'].resample('ME').agg({
    'close': 'last'
}).rename(columns={'close': 'close'})

# 正确的OHLCV聚合方式
monthly_ohlcv = df.resample('ME').agg({
    'open':   'first',
    'high':   'max',
    'low':    'min',
    'close':  'last',
    'volume': 'sum',
})
print(f"\n=== 月线数据（共{len(monthly_ohlcv)}个月）===")
print(monthly_ohlcv.tail())

# ============================================================
# 4. groupby：多股票截面操作（因子研究核心）
# ============================================================

# 模拟多股票数据
symbols = ['000001.SZ', '000002.SZ', '600000.SH', '600036.SH', '000858.SZ']
dates = pd.bdate_range('2023-01-01', '2023-12-31')

multi_stock = pd.DataFrame([
    {'date': d, 'symbol': s,
     'close': 10 * np.exp(np.random.normal(0, 0.02)),
     'pe': np.random.uniform(10, 50),
     'industry': np.random.choice(['银行', '房地产', '食品饮料'])}
    for d in dates for s in symbols
])

# 按日期计算截面排名（因子标准化的常见操作）
multi_stock['pe_rank'] = multi_stock.groupby('date')['pe'].rank(pct=True)
multi_stock['pe_zscore'] = multi_stock.groupby('date')['pe'].transform(
    lambda x: (x - x.mean()) / x.std()
)

print(f"\n=== 截面排名（每日PE排名）===")
print(multi_stock[['date', 'symbol', 'pe', 'pe_rank', 'pe_zscore']].head(10))

# ============================================================
# 5. pivot_table：因子矩阵构建（回测框架标准格式）
# ============================================================

# 将长格式转为宽格式（日期 x 股票）
factor_matrix = multi_stock.pivot_table(
    index='date', columns='symbol', values='pe'
)
price_matrix = multi_stock.pivot_table(
    index='date', columns='symbol', values='close'
)

print(f"\n=== 因子矩阵（宽格式）===")
print(factor_matrix.tail())

# ============================================================
# 6. merge：合并财务数据与行情数据（实际工作中最常用）
# ============================================================

# 模拟季度财务数据（非每日更新）
quarterly_data = pd.DataFrame({
    'symbol': ['000001.SZ'] * 4,
    'report_date': pd.to_datetime(['2023-03-31', '2023-06-30',
                                    '2023-09-30', '2023-12-31']),
    'roe': [0.12, 0.13, 0.11, 0.14],
    'revenue_growth': [0.08, 0.12, 0.06, 0.15],
})

# 日线行情数据
daily_price = pd.DataFrame({
    'date': pd.bdate_range('2023-01-01', '2023-12-31'),
    'symbol': '000001.SZ',
    'close': np.random.uniform(9, 12, len(pd.bdate_range('2023-01-01', '2023-12-31')))
})

# 关键：用 merge_asof 合并（财务数据滞后匹配，避免未来函数！）
daily_price = daily_price.sort_values('date')
quarterly_data = quarterly_data.sort_values('report_date')

# 财务数据在披露日之后才能使用（通常滞后1-3个月）
quarterly_data['available_date'] = quarterly_data['report_date'] + pd.DateOffset(months=1)

merged = pd.merge_asof(
    daily_price,
    quarterly_data[['available_date', 'roe', 'revenue_growth']],
    left_on='date',
    right_on='available_date',
    direction='backward'   # 只使用过去已公布的数据
)

print(f"\n=== 财务数据点时合并（避免未来函数）===")
print(merged[['date', 'close', 'roe', 'revenue_growth']].dropna().head(10))
print("⚠️  注意：2023年前几个月没有ROE数据（因为财报还未披露）")

# ============================================================
# 练习题
# ============================================================
"""
练习1：
给定上面的 df（单股票OHLCV），计算：
- 连续上涨天数（当前价格高于昨日的连续天数）
- 提示：用 groupby + cumsum 的技巧

练习2：
给定 multi_stock 数据，用 groupby 计算：
- 每个行业每月的平均PE
- 每个股票相对其行业平均PE的偏差（行业中性化）

练习3：
实现一个函数，输入多股票价格矩阵，
输出所有股票对的滚动相关性矩阵（rolling=60日），
最终返回每日相关性均值（代表市场整体关联度）。
"""

if __name__ == "__main__":
    print("\n✅ Pandas基础模块加载完成")
    print("请完成练习题后再进入下一个模块")
