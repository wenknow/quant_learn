"""
Week 24-26: 组合优化与风险管理
工具：cvxpy + PyPortfolioOpt
"""

import numpy as np
import pandas as pd
import cvxpy as cp
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')


# ============================================================
# 1. 均值-方差优化（Markowitz）
# ============================================================

class MeanVarianceOptimizer:
    """
    Markowitz均值-方差组合优化
    目标：在给定风险水平下最大化预期收益
    """

    def __init__(self, expected_returns: pd.Series,
                 cov_matrix: pd.DataFrame):
        assert len(expected_returns) == cov_matrix.shape[0]
        self.mu = expected_returns.values
        self.Sigma = cov_matrix.values
        self.assets = expected_returns.index
        self.n = len(expected_returns)

    def max_sharpe(self, rf: float = 0.02/252,
                   max_weight: float = 0.1,
                   long_only: bool = True) -> pd.Series:
        """最大化Sharpe比率"""
        # 变量替换：令 y = w / (mu-rf)'w，使问题变为凸问题
        y = cp.Variable(self.n, nonneg=long_only)
        kappa = cp.Variable(nonneg=True)

        excess_mu = self.mu - rf

        objective = cp.Minimize(cp.quad_form(y, self.Sigma))
        constraints = [
            excess_mu @ y == 1,
            cp.sum(y) == kappa,
            y <= max_weight * kappa,
        ]

        prob = cp.Problem(objective, constraints)
        prob.solve(solver=cp.ECOS, warm_start=True)

        if prob.status not in ['optimal', 'optimal_inaccurate']:
            raise RuntimeError(f"优化失败: {prob.status}")

        w = y.value / kappa.value
        w = np.clip(w, 0, None)
        w /= w.sum()
        return pd.Series(w, index=self.assets)

    def min_variance(self, max_weight: float = 0.1) -> pd.Series:
        """最小化组合方差"""
        w = cp.Variable(self.n, nonneg=True)

        objective = cp.Minimize(cp.quad_form(w, self.Sigma))
        constraints = [
            cp.sum(w) == 1,
            w <= max_weight,
        ]

        prob = cp.Problem(objective, constraints)
        prob.solve()

        return pd.Series(w.value, index=self.assets)

    def mean_variance(self, risk_aversion: float = 2.0,
                      max_weight: float = 0.1) -> pd.Series:
        """均值-方差优化（调节风险厌恶系数）"""
        w = cp.Variable(self.n, nonneg=True)

        objective = cp.Maximize(
            self.mu @ w - risk_aversion * cp.quad_form(w, self.Sigma)
        )
        constraints = [
            cp.sum(w) == 1,
            w <= max_weight,
        ]

        prob = cp.Problem(objective, constraints)
        prob.solve()

        return pd.Series(w.value, index=self.assets)

    def efficient_frontier(self, n_points: int = 50) -> pd.DataFrame:
        """绘制有效前沿"""
        target_returns = np.linspace(
            self.mu.min() * 1.01,
            self.mu.max() * 0.99,
            n_points
        )
        frontier = []

        for target in target_returns:
            w = cp.Variable(self.n, nonneg=True)
            objective = cp.Minimize(cp.quad_form(w, self.Sigma))
            constraints = [
                cp.sum(w) == 1,
                self.mu @ w >= target,
                w <= 0.15
            ]
            prob = cp.Problem(objective, constraints)
            prob.solve()

            if prob.status == 'optimal':
                port_vol = np.sqrt(w.value @ self.Sigma @ w.value) * np.sqrt(252)
                port_ret = self.mu @ w.value * 252
                frontier.append({'return': port_ret, 'volatility': port_vol})

        return pd.DataFrame(frontier)


# ============================================================
# 2. 风险平价（Risk Parity）
# ============================================================

class RiskParityOptimizer:
    """
    等风险贡献（ERC）组合
    原理：每只资产对组合总风险的贡献相等
    适合：不需要预测预期收益，只需协方差矩阵
    """

    def __init__(self, cov_matrix: pd.DataFrame):
        self.Sigma = cov_matrix.values
        self.assets = cov_matrix.index
        self.n = len(cov_matrix)

    def risk_contribution(self, w: np.ndarray) -> np.ndarray:
        """计算每只资产的风险贡献"""
        port_var = w @ self.Sigma @ w
        marginal_risk = self.Sigma @ w
        risk_contrib = w * marginal_risk / port_var
        return risk_contrib

    def optimize(self, target_risk: np.ndarray = None) -> pd.Series:
        """
        等风险贡献优化
        target_risk: 目标风险权重，默认等权重（1/n）
        """
        if target_risk is None:
            target_risk = np.ones(self.n) / self.n

        def objective(w):
            rc = self.risk_contribution(w)
            return np.sum((rc - target_risk) ** 2)

        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = [(1e-6, 1.0)] * self.n
        x0 = np.ones(self.n) / self.n

        result = minimize(objective, x0, method='SLSQP',
                          bounds=bounds, constraints=constraints,
                          options={'ftol': 1e-12, 'maxiter': 1000})

        w = result.x / result.x.sum()
        return pd.Series(w, index=self.assets)


# ============================================================
# 3. Kelly准则：仓位管理
# ============================================================

def kelly_fraction(win_rate: float, avg_win: float,
                   avg_loss: float, fraction: float = 0.5) -> float:
    """
    Kelly准则：最优下注比例
    f* = (W*b - L) / b
    其中：
      W = 胜率
      L = 败率 = 1 - W
      b = 平均盈利 / 平均亏损（盈亏比）

    fraction: 实际使用的Kelly比例（通常用半Kelly）
    """
    b = avg_win / avg_loss
    kelly = (win_rate * b - (1 - win_rate)) / b
    kelly = max(kelly, 0)  # Kelly为负表示不该参与

    print(f"=== Kelly准则计算 ===")
    print(f"胜率:         {win_rate:.1%}")
    print(f"盈亏比:       {b:.2f}")
    print(f"Full Kelly:   {kelly:.1%}")
    print(f"Half Kelly:   {kelly * fraction:.1%}（推荐使用）")
    print(f"\n建议：对单一策略，实际仓位不超过Full Kelly的50%")

    return kelly * fraction


def multi_asset_kelly(expected_returns: np.ndarray,
                      cov_matrix: np.ndarray) -> np.ndarray:
    """
    多资产连续Kelly准则
    f* = Sigma^{-1} * mu
    然后归一化到总仓位限制
    """
    try:
        inv_cov = np.linalg.inv(cov_matrix)
        kelly_weights = inv_cov @ expected_returns
        kelly_weights = np.maximum(kelly_weights, 0)   # 只做多
        if kelly_weights.sum() > 0:
            kelly_weights /= kelly_weights.sum()
    except np.linalg.LinAlgError:
        kelly_weights = np.ones(len(expected_returns)) / len(expected_returns)

    return kelly_weights


# ============================================================
# 4. 动态风险控制
# ============================================================

class RiskController:
    """
    组合级风险控制
    包含：止损、波动率目标、回撤控制
    """

    def __init__(self, max_drawdown_limit: float = 0.15,
                 vol_target: float = 0.12,
                 position_limit: float = 0.1):
        self.max_dd_limit = max_drawdown_limit
        self.vol_target = vol_target
        self.position_limit = position_limit

    def vol_targeting(self, returns: pd.Series,
                      lookback: int = 20) -> pd.Series:
        """
        波动率目标化：动态调整仓位使组合波动率接近目标值
        实际使用：仓位 = vol_target / realized_vol
        """
        realized_vol = returns.rolling(lookback).std() * np.sqrt(252)
        leverage = (self.vol_target / realized_vol).clip(0, 2)   # 限制杠杆上限
        return leverage

    def drawdown_control(self, nav: pd.Series,
                          returns: pd.Series) -> pd.Series:
        """
        回撤控制：当回撤超过阈值时减仓
        """
        rolling_max = nav.cummax()
        current_dd = (nav - rolling_max) / rolling_max

        # 线性减仓：回撤越大，仓位越低
        position_multiplier = pd.Series(1.0, index=nav.index)
        severe_dd = current_dd < -self.max_dd_limit * 0.5
        position_multiplier[severe_dd] = 0.5

        extreme_dd = current_dd < -self.max_dd_limit
        position_multiplier[extreme_dd] = 0.0   # 全部清仓

        return position_multiplier

    def check_concentration(self, weights: pd.Series) -> dict:
        """检查持仓集中度"""
        hhi = (weights ** 2).sum()   # Herfindahl指数
        effective_n = 1 / hhi         # 有效股票数

        result = {
            'HHI指数':      hhi,
            '有效持仓数':   effective_n,
            '最大单仓':     weights.max(),
            '前5仓位和':    weights.nlargest(5).sum(),
        }

        if weights.max() > self.position_limit:
            print(f"⚠️  警告：最大单仓 {weights.max():.1%} 超过限制 {self.position_limit:.1%}")
        if effective_n < 10:
            print(f"⚠️  警告：有效持仓数 {effective_n:.1f} 只，集中度过高")

        return result


# ============================================================
# 演示
# ============================================================

if __name__ == "__main__":
    np.random.seed(42)
    n_assets = 20

    assets = [f'stock_{i:03d}' for i in range(n_assets)]
    expected_returns = pd.Series(
        np.random.uniform(0.0002, 0.001, n_assets),
        index=assets
    )

    # 生成正定协方差矩阵
    A = np.random.randn(n_assets, n_assets)
    cov_matrix = pd.DataFrame(
        A.T @ A / n_assets * 0.0004,
        index=assets, columns=assets
    )

    print("=" * 50)
    print("组合优化演示")
    print("=" * 50)

    # 均值-方差优化
    mv_opt = MeanVarianceOptimizer(expected_returns, cov_matrix)

    print("\n1. 最大Sharpe组合:")
    max_sharpe_w = mv_opt.max_sharpe()
    print(f"  非零仓位数: {(max_sharpe_w > 0.01).sum()}")
    print(f"  最大仓位: {max_sharpe_w.max():.1%}")

    print("\n2. 最小方差组合:")
    min_var_w = mv_opt.min_variance()
    print(f"  非零仓位数: {(min_var_w > 0.01).sum()}")

    print("\n3. 风险平价组合:")
    rp_opt = RiskParityOptimizer(cov_matrix)
    rp_w = rp_opt.optimize()
    rc = rp_opt.risk_contribution(rp_w.values)
    print(f"  各资产风险贡献（应接近1/{n_assets}={1/n_assets:.3f}）:")
    print(f"  均值={rc.mean():.4f}, 标准差={rc.std():.4f}")

    print("\n4. Kelly准则（单策略）:")
    kelly_fraction(win_rate=0.55, avg_win=0.02, avg_loss=0.015)

    print("\n5. 风险控制检查:")
    rc_checker = RiskController()
    concentration = rc_checker.check_concentration(max_sharpe_w)
    for k, v in concentration.items():
        print(f"  {k}: {v:.4f}")
