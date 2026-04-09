"""
Week 11-12: 因子投资理论与IC分析
这是量化研究员最核心的日常工作
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


# ============================================================
# 1. IC（信息系数）计算 —— 因子有效性的核心指标
# ============================================================

def calc_ic(factor: pd.Series, forward_return: pd.Series,
            method: str = 'rank') -> float:
    """
    计算单期IC（信息系数）
    IC = corr(本期因子值, 下期收益率)

    method:
        'rank'   → Spearman秩相关（推荐，对异常值稳健）
        'normal' → Pearson线性相关
    """
    common = factor.index.intersection(forward_return.index)
    f = factor[common].dropna()
    r = forward_return[common].reindex(f.index).dropna()
    common2 = f.index.intersection(r.index)

    if len(common2) < 10:
        return np.nan

    if method == 'rank':
        ic, _ = stats.spearmanr(f[common2], r[common2])
    else:
        ic, _ = stats.pearsonr(f[common2], r[common2])
    return ic


def calc_ic_series(factor_panel: pd.DataFrame,
                   return_panel: pd.DataFrame,
                   method: str = 'rank') -> pd.DataFrame:
    """
    计算IC时间序列
    factor_panel:  index=date, columns=stock_code
    return_panel:  index=date, columns=stock_code（已向前shift）
    """
    ic_list = []
    for date in factor_panel.index:
        if date not in return_panel.index:
            continue
        ic = calc_ic(factor_panel.loc[date], return_panel.loc[date], method)
        ic_list.append({'date': date, 'IC': ic})

    ic_df = pd.DataFrame(ic_list).set_index('date').dropna()

    # 计算关键统计指标
    mean_ic = ic_df['IC'].mean()
    std_ic  = ic_df['IC'].std()
    icir    = mean_ic / std_ic if std_ic > 0 else 0
    win_rate = (ic_df['IC'] > 0).mean()

    # t检验：IC均值是否显著不为0
    t_stat, p_value = stats.ttest_1samp(ic_df['IC'].dropna(), 0)

    print(f"IC分析结果:")
    print(f"  IC均值:   {mean_ic:.4f}  (|IC|>0.03 认为有效)")
    print(f"  IC标准差: {std_ic:.4f}")
    print(f"  ICIR:     {icir:.4f}  (>0.5 认为优秀)")
    print(f"  IC胜率:   {win_rate:.1%}  (>55% 认为稳定)")
    print(f"  t统计量:  {t_stat:.4f}")
    print(f"  p值:      {p_value:.4f}  ({'显著' if p_value < 0.05 else '不显著'})")

    return ic_df


# ============================================================
# 2. 分层回测（Quantile Analysis）
# ============================================================

def quantile_backtest(factor_panel: pd.DataFrame,
                      price_panel: pd.DataFrame,
                      n_quantiles: int = 10,
                      holding_period: int = 20) -> pd.DataFrame:
    """
    分层回测：将股票按因子值分为N组，观察各组收益率
    好因子的特征：分组收益单调递增（或递减）
    """
    # 计算持有期收益率
    forward_returns = price_panel.pct_change(holding_period).shift(-holding_period)

    group_returns = []

    for date in factor_panel.index:
        if date not in forward_returns.index:
            continue

        f = factor_panel.loc[date].dropna()
        r = forward_returns.loc[date].reindex(f.index).dropna()
        common = f.index.intersection(r.index)

        if len(common) < n_quantiles * 5:
            continue

        # 分组
        try:
            groups = pd.qcut(f[common], n_quantiles,
                             labels=False, duplicates='drop')
        except Exception:
            continue

        for g in range(n_quantiles):
            stocks_in_group = groups[groups == g].index
            if len(stocks_in_group) == 0:
                continue
            group_returns.append({
                'date': date,
                'group': g + 1,
                'return': r[stocks_in_group].mean(),
                'count': len(stocks_in_group)
            })

    df = pd.DataFrame(group_returns)
    if df.empty:
        return df

    # 计算各组平均收益
    avg_returns = df.groupby('group')['return'].mean()

    # 多空收益（第N组 - 第1组）
    long_short_return = avg_returns.iloc[-1] - avg_returns.iloc[0]
    annual_ls = long_short_return * 252 / holding_period

    print(f"\n分层回测结果（{n_quantiles}分位，持有{holding_period}日）:")
    for g, r in avg_returns.items():
        bar = '█' * int(abs(r) * 10000)
        sign = '+' if r > 0 else '-'
        print(f"  第{g:2d}组: {sign}{abs(r):.4f} {bar}")
    print(f"\n多空年化收益: {annual_ls:.2%}")

    return df


# ============================================================
# 3. 因子预处理（量化研究的标准流程）
# ============================================================

def winsorize(series: pd.Series, n_std: float = 3.0) -> pd.Series:
    """去极值（3σ法）"""
    mean = series.mean()
    std  = series.std()
    return series.clip(mean - n_std * std, mean + n_std * std)


def mad_winsorize(series: pd.Series, n: float = 3.0) -> pd.Series:
    """去极值（MAD法，更稳健）"""
    median = series.median()
    mad = (series - median).abs().median()
    return series.clip(median - n * 1.4826 * mad,
                       median + n * 1.4826 * mad)


def standardize(series: pd.Series) -> pd.Series:
    """Z-score标准化"""
    return (series - series.mean()) / series.std()


def neutralize(factor: pd.Series,
               market_cap: pd.Series,
               industry: pd.Series) -> pd.Series:
    """
    市值+行业中性化（量化标准预处理步骤）
    原理：用OLS回归去掉市值和行业对因子的影响
    """
    common = factor.index.intersection(market_cap.index).intersection(industry.index)
    f = factor[common]
    mc = np.log(market_cap[common])   # 对数市值

    # 构建行业哑变量
    ind_dummies = pd.get_dummies(industry[common], prefix='ind', drop_first=True)

    # 设计矩阵
    X = pd.concat([mc, ind_dummies], axis=1).values
    y = f.values

    # OLS回归
    from numpy.linalg import lstsq
    X = np.column_stack([np.ones(len(X)), X])
    beta, _, _, _ = lstsq(X, y, rcond=None)

    # 残差即为中性化后的因子
    residuals = y - X @ beta
    return pd.Series(residuals, index=common)


def preprocess_factor(factor: pd.Series,
                      market_cap: pd.Series = None,
                      industry: pd.Series = None) -> pd.Series:
    """完整因子预处理流程"""
    # Step 1: 去极值
    f = mad_winsorize(factor)
    # Step 2: 中性化（如果提供了市值和行业）
    if market_cap is not None and industry is not None:
        f = neutralize(f, market_cap, industry)
    # Step 3: 标准化
    f = standardize(f)
    return f


# ============================================================
# 4. 常用因子计算
# ============================================================

class CommonFactors:
    """常用因子计算（基于OHLCV数据）"""

    @staticmethod
    def momentum(close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """
        动量因子：过去N日收益率
        预期方向：正（动量效应）
        """
        return close.pct_change(window)

    @staticmethod
    def reversal(close: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """
        短期反转因子：过去N日收益率取负
        预期方向：负（短期过度反应）
        """
        return -close.pct_change(window)

    @staticmethod
    def volatility(close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """
        波动率因子：过去N日收益率标准差
        预期方向：负（低波动溢价）
        """
        return close.pct_change().rolling(window).std()

    @staticmethod
    def turnover(volume: pd.DataFrame,
                 shares_outstanding: pd.DataFrame,
                 window: int = 20) -> pd.DataFrame:
        """
        换手率因子：成交量/流通股本
        预期方向：负（高换手率股票未来表现差）
        """
        daily_turnover = volume / shares_outstanding
        return daily_turnover.rolling(window).mean()

    @staticmethod
    def size(market_cap: pd.DataFrame) -> pd.DataFrame:
        """
        市值因子：流通市值的对数
        预期方向：负（小市值溢价）
        """
        return np.log(market_cap)

    @staticmethod
    def bp_ratio(book_value: pd.DataFrame,
                 market_cap: pd.DataFrame) -> pd.DataFrame:
        """
        账面市值比（B/P）= 净资产 / 市值
        预期方向：正（价值因子）
        """
        return book_value / market_cap


# ============================================================
# 5. 模拟演示
# ============================================================

if __name__ == "__main__":
    np.random.seed(42)
    n_dates = 120
    n_stocks = 200

    dates = pd.bdate_range('2022-01-01', periods=n_dates)
    stocks = [f'stock_{i:04d}' for i in range(n_stocks)]

    # 模拟价格数据
    price_panel = pd.DataFrame(
        100 * np.cumprod(1 + np.random.normal(0.0005, 0.02, (n_dates, n_stocks)), axis=0),
        index=dates, columns=stocks
    )

    # 模拟动量因子（有真实alpha）
    forward_ret = price_panel.pct_change(20).shift(-20)

    # 因子值 = 过去20日收益率（有噪声）
    factor_panel = price_panel.pct_change(20) + np.random.normal(0, 0.01, (n_dates, n_stocks))
    factor_panel = pd.DataFrame(factor_panel, index=dates, columns=stocks)

    print("=" * 50)
    print("因子分析演示：20日动量因子")
    print("=" * 50)

    ic_series = calc_ic_series(factor_panel, forward_ret)

    print("\n" + "=" * 50)
    quantile_backtest(factor_panel, price_panel, n_quantiles=5, holding_period=20)
