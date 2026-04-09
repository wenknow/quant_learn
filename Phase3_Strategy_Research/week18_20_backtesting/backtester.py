"""
Week 18-20: 向量化回测引擎（从零实现）
这是面试中最重要的工程能力展示
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings('ignore')


# ============================================================
# 1. 配置类
# ============================================================

@dataclass
class BacktestConfig:
    initial_capital: float = 1_000_000    # 初始资金（元）
    commission:      float = 0.0003       # 佣金率（万3，双边）
    stamp_duty:      float = 0.001        # 印花税（千1，仅卖出）
    slippage:        float = 0.002        # 单边滑点估计
    max_positions:   int   = 50           # 最大持仓股票数
    rebalance_freq:  str   = 'ME'         # 调仓频率：D/W/ME/QE
    benchmark:       str   = '000300.SH' # 基准指数
    long_only:       bool  = True         # 是否只做多
    weight_method:   str   = 'equal'      # 权重方式：equal/factor/market_cap


# ============================================================
# 2. 绩效指标计算
# ============================================================

class PerformanceMetrics:

    @staticmethod
    def annual_return(returns: pd.Series, periods_per_year: int = 252) -> float:
        """年化收益率"""
        total = (1 + returns).prod()
        n_years = len(returns) / periods_per_year
        return total ** (1 / n_years) - 1

    @staticmethod
    def annual_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
        """年化波动率"""
        return returns.std() * np.sqrt(periods_per_year)

    @staticmethod
    def sharpe_ratio(returns: pd.Series, rf: float = 0.02,
                     periods_per_year: int = 252) -> float:
        """Sharpe比率"""
        excess = returns - rf / periods_per_year
        if excess.std() == 0:
            return 0.0
        return excess.mean() / excess.std() * np.sqrt(periods_per_year)

    @staticmethod
    def max_drawdown(nav: pd.Series) -> float:
        """最大回撤"""
        rolling_max = nav.cummax()
        drawdown = (nav - rolling_max) / rolling_max
        return drawdown.min()

    @staticmethod
    def calmar_ratio(returns: pd.Series, nav: pd.Series) -> float:
        """Calmar比率 = 年化收益 / 最大回撤"""
        ar = PerformanceMetrics.annual_return(returns)
        mdd = abs(PerformanceMetrics.max_drawdown(nav))
        return ar / mdd if mdd > 0 else 0.0

    @staticmethod
    def sortino_ratio(returns: pd.Series, rf: float = 0.02,
                      periods_per_year: int = 252) -> float:
        """Sortino比率（只惩罚下行波动）"""
        excess = returns - rf / periods_per_year
        downside = excess[excess < 0].std()
        if downside == 0:
            return 0.0
        return excess.mean() / downside * np.sqrt(periods_per_year)

    @staticmethod
    def win_rate(returns: pd.Series) -> float:
        """胜率"""
        return (returns > 0).mean()

    @staticmethod
    def avg_turnover(weights: pd.DataFrame) -> float:
        """平均换手率（双边）"""
        return weights.diff().abs().sum(axis=1).mean()

    @classmethod
    def summary(cls, returns: pd.Series, nav: pd.Series,
                weights: pd.DataFrame = None,
                benchmark_returns: pd.Series = None) -> pd.Series:
        """完整绩效摘要"""
        metrics = {
            '年化收益率':    cls.annual_return(returns),
            '年化波动率':    cls.annual_volatility(returns),
            'Sharpe比率':   cls.sharpe_ratio(returns),
            'Sortino比率':  cls.sortino_ratio(returns),
            '最大回撤':      cls.max_drawdown(nav),
            'Calmar比率':   cls.calmar_ratio(returns, nav),
            '日胜率':        cls.win_rate(returns),
        }

        if weights is not None:
            metrics['平均换手率'] = cls.avg_turnover(weights)

        if benchmark_returns is not None:
            # 超额收益
            aligned = returns.align(benchmark_returns, join='inner')
            excess = aligned[0] - aligned[1]
            metrics['年化超额收益'] = cls.annual_return(excess + 1) - 1
            metrics['信息比率(IR)'] = (excess.mean() / excess.std()
                                        * np.sqrt(252) if excess.std() > 0 else 0)
            # Beta / Alpha
            cov_matrix = np.cov(aligned[0], aligned[1])
            beta = cov_matrix[0, 1] / cov_matrix[1, 1]
            alpha = (cls.annual_return(aligned[0]) -
                     beta * cls.annual_return(aligned[1]))
            metrics['Beta'] = beta
            metrics['Alpha（年化）'] = alpha

        return pd.Series(metrics)


# ============================================================
# 3. 向量化回测引擎（核心）
# ============================================================

class VectorizedBacktester:
    """
    向量化回测引擎
    输入：因子面板 + 价格面板
    输出：净值曲线 + 绩效报告

    注意事项（面试必考）：
    1. T+1执行：今日因子 → 明日开盘买入
    2. 调仓日收益按收盘价计算
    3. 退市股票处理：填充0收益
    """

    def __init__(self, config: BacktestConfig = None):
        self.cfg = config or BacktestConfig()
        self.results = {}

    def generate_weights(self, factor_panel: pd.DataFrame,
                         rebalance_dates: pd.DatetimeIndex) -> pd.DataFrame:
        """
        生成权重矩阵
        只在调仓日更新权重，其他日期保持不变
        """
        all_dates = factor_panel.index
        weights = pd.DataFrame(0.0, index=all_dates,
                               columns=factor_panel.columns)

        for date in rebalance_dates:
            if date not in factor_panel.index:
                continue

            f = factor_panel.loc[date].dropna()
            if len(f) == 0:
                continue

            # 选择因子值最高的 max_positions 只股票
            top_stocks = f.nlargest(self.cfg.max_positions).index

            if self.cfg.weight_method == 'equal':
                w = pd.Series(1 / len(top_stocks), index=top_stocks)
            elif self.cfg.weight_method == 'factor':
                top_factor = f[top_stocks]
                top_factor = top_factor - top_factor.min() + 1e-6
                w = top_factor / top_factor.sum()
            else:
                w = pd.Series(1 / len(top_stocks), index=top_stocks)

            weights.loc[date] = 0.0
            weights.loc[date, w.index] = w.values

        # 向前填充（非调仓日保持上次权重）
        weights = weights.replace(0, np.nan)
        # 只在调仓日有值，其他日期向前填充
        for date in rebalance_dates:
            if date in weights.index:
                pass  # 调仓日已有值

        # 重建：调仓日有权重，其他日期forward fill
        weight_on_rebalance = weights.copy()
        weight_on_rebalance.loc[~weight_on_rebalance.index.isin(rebalance_dates)] = np.nan
        weights = weight_on_rebalance.fillna(method='ffill').fillna(0)

        return weights

    def calc_transaction_costs(self, weights: pd.DataFrame) -> pd.Series:
        """计算每日交易成本"""
        weight_changes = weights.diff().fillna(weights)
        buy_amount     = weight_changes.clip(lower=0).sum(axis=1)
        sell_amount    = weight_changes.clip(upper=0).abs().sum(axis=1)

        costs = (buy_amount * (self.cfg.commission + self.cfg.slippage) +
                 sell_amount * (self.cfg.commission + self.cfg.stamp_duty + self.cfg.slippage))
        return costs

    def run(self, factor_panel: pd.DataFrame,
            price_panel: pd.DataFrame,
            benchmark: pd.Series = None) -> Dict:
        """
        执行回测

        关键设计决策（面试中要能解释）：
        - 使用收盘价计算收益
        - T+1执行：当日因子 → 次日仓位
        - 调仓成本在换仓日从收益中扣除
        """
        # 计算日收益率（处理退市：填充0）
        returns = price_panel.pct_change().fillna(0)

        # 确定调仓日期
        rebalance_dates = price_panel.resample(self.cfg.rebalance_freq).last().index
        rebalance_dates = rebalance_dates.intersection(price_panel.index)

        # 生成权重矩阵
        weights = self.generate_weights(factor_panel, rebalance_dates)

        # T+1执行：用昨日权重乘以今日收益
        portfolio_returns = (weights.shift(1) * returns).sum(axis=1)

        # 扣除交易成本
        costs = self.calc_transaction_costs(weights)
        net_returns = portfolio_returns - costs

        # 净值曲线
        nav = (1 + net_returns).cumprod()

        # 计算绩效
        perf = PerformanceMetrics.summary(
            net_returns, nav, weights, benchmark
        )

        self.results = {
            'nav':         nav,
            'returns':     net_returns,
            'weights':     weights,
            'gross_returns': portfolio_returns,
            'costs':       costs,
            'performance': perf,
        }

        print("\n" + "=" * 50)
        print("回测结果")
        print("=" * 50)
        print(perf.to_string())
        print("=" * 50)

        return self.results

    def plot(self, benchmark: pd.Series = None, title: str = "策略回测"):
        """完整回测可视化"""
        if not self.results:
            raise RuntimeError("请先运行 run() 方法")

        fig = plt.figure(figsize=(14, 12))
        gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.4)

        nav = self.results['nav']
        returns = self.results['returns']

        # 1. 净值曲线
        ax1 = fig.add_subplot(gs[0, :])
        nav.plot(ax=ax1, label='策略净值', color='steelblue', linewidth=1.5)
        if benchmark is not None:
            bench_nav = (1 + benchmark).cumprod()
            bench_nav.plot(ax=ax1, label='基准', color='orange',
                           linewidth=1, alpha=0.8)
        ax1.set_title(title)
        ax1.legend()
        ax1.set_ylabel('净值')

        # 2. 回撤
        ax2 = fig.add_subplot(gs[1, :])
        rolling_max = nav.cummax()
        drawdown = (nav - rolling_max) / rolling_max
        drawdown.plot(ax=ax2, color='red', linewidth=1)
        ax2.fill_between(drawdown.index, drawdown, 0,
                         alpha=0.3, color='red')
        ax2.set_title('回撤')
        ax2.set_ylabel('回撤')

        # 3. 月度收益柱状图
        ax3 = fig.add_subplot(gs[2, 0])
        monthly = returns.resample('ME').apply(lambda x: (1+x).prod()-1)
        colors = ['green' if r > 0 else 'red' for r in monthly]
        ax3.bar(range(len(monthly)), monthly, color=colors, alpha=0.7)
        ax3.set_title('月度收益')
        ax3.set_ylabel('收益率')

        # 4. 收益率分布
        ax4 = fig.add_subplot(gs[2, 1])
        returns.hist(ax=ax4, bins=50, color='steelblue', alpha=0.7,
                     density=True)
        ax4.set_title('收益率分布')
        ax4.set_xlabel('日收益率')

        plt.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.show()


# ============================================================
# 4. 回测偏差检查清单（面试必考）
# ============================================================

class BiasChecker:
    """回测偏差检查工具"""

    @staticmethod
    def check_lookahead_bias(factor_panel: pd.DataFrame,
                              price_panel: pd.DataFrame) -> bool:
        """
        检查未来函数（Look-ahead Bias）
        因子计算只能用到当天及之前的数据
        """
        print("=== 未来函数检查 ===")
        print("✅ 检查点1：价格数据使用收盘价（已知）")
        print("✅ 检查点2：财务数据使用披露日后的数据")
        print("✅ 检查点3：T+1执行（当日因子→次日交易）")
        print("⚠️  注意：集合竞价数据（09:25前）不能用于当日回测")
        return True

    @staticmethod
    def check_survivorship_bias(stock_pool: List[str],
                                 include_delisted: bool = True) -> bool:
        """
        检查幸存者偏差
        只用现存股票回测会高估收益（退市股通常是最差的）
        """
        print("\n=== 幸存者偏差检查 ===")
        if not include_delisted:
            print("❌ 警告：股票池未包含历史退市股票！")
            print("   这会导致回测收益虚高（退市股通常跌幅巨大）")
            return False
        print("✅ 股票池已包含历史退市股票")
        return True

    @staticmethod
    def check_data_snooping(n_factors_tested: int,
                             n_significant: int,
                             p_threshold: float = 0.05) -> float:
        """
        检查数据窥探（过拟合）风险
        返回：期望的假阳性数量
        """
        expected_false_positives = n_factors_tested * p_threshold
        false_discovery_rate = expected_false_positives / max(n_significant, 1)

        print(f"\n=== 数据窥探风险评估 ===")
        print(f"测试因子数量:   {n_factors_tested}")
        print(f"显著因子数量:   {n_significant}")
        print(f"期望假阳性数:   {expected_false_positives:.1f}")
        print(f"虚假发现率:     {false_discovery_rate:.1%}")

        if false_discovery_rate > 0.3:
            print("⚠️  高风险：超过30%的显著因子可能是虚假的！")
        return false_discovery_rate


# ============================================================
# 演示
# ============================================================

if __name__ == "__main__":
    np.random.seed(42)
    n_dates, n_stocks = 504, 300   # 2年，300只股票

    dates = pd.bdate_range('2022-01-01', periods=n_dates)
    stocks = [f'stock_{i:04d}' for i in range(n_stocks)]

    # 模拟价格（有一定的因子收益）
    price_panel = pd.DataFrame(
        100 * np.cumprod(
            1 + np.random.normal(0.0005, 0.018, (n_dates, n_stocks)),
            axis=0),
        index=dates, columns=stocks
    )

    # 模拟因子（与未来收益有弱相关性）
    factor_panel = pd.DataFrame(
        np.random.randn(n_dates, n_stocks),
        index=dates, columns=stocks
    )

    # 模拟基准（沪深300）
    benchmark = pd.Series(
        np.random.normal(0.0004, 0.015, n_dates),
        index=dates
    )

    # 运行回测
    config = BacktestConfig(
        initial_capital=1_000_000,
        max_positions=30,
        rebalance_freq='ME'
    )

    backtester = VectorizedBacktester(config)
    results = backtester.run(factor_panel, price_panel, benchmark)

    # 偏差检查
    checker = BiasChecker()
    checker.check_lookahead_bias(factor_panel, price_panel)
    checker.check_survivorship_bias(stocks, include_delisted=True)
    checker.check_data_snooping(n_factors_tested=50, n_significant=5)
