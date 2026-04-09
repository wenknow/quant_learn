"""
Week 07-08: 量化必备时间序列分析
核心工具：平稳性、ARIMA、GARCH、协整
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller, coint, acf, pacf
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from arch import arch_model
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# ============================================================
# 1. 平稳性检验（ADF检验）
# ============================================================

print("=== 1. ADF 平稳性检验 ===")

def adf_test(series: pd.Series, name: str = "序列") -> bool:
    """
    ADF检验：判断时间序列是否平稳
    H0：存在单位根（不平稳）
    H1：不存在单位根（平稳）
    p < 0.05 → 拒绝H0 → 序列平稳
    """
    result = adfuller(series.dropna(), autolag='AIC')
    print(f"\n{name}:")
    print(f"  ADF统计量: {result[0]:.4f}")
    print(f"  p值:       {result[1]:.6f}")
    print(f"  临界值:    1%={result[4]['1%']:.3f}, 5%={result[4]['5%']:.3f}")
    is_stationary = result[1] < 0.05
    print(f"  结论:      {'✅ 平稳' if is_stationary else '❌ 不平稳（需要差分）'}")
    return is_stationary

# 生成不同类型的序列
n = 500
random_walk = np.cumsum(np.random.randn(n))        # 随机游走（不平稳）
stationary  = np.random.randn(n) * 0.5             # 平稳白噪声
returns     = np.diff(random_walk)                  # 对随机游走取差分 → 平稳

adf_test(pd.Series(random_walk), "随机游走（价格序列）")
adf_test(pd.Series(stationary),  "白噪声（平稳序列）")
adf_test(pd.Series(returns),     "一阶差分（收益率序列）")

print("\n💡 结论：")
print("  - 价格序列：通常不平稳（随机游走）")
print("  - 收益率序列：通常平稳（一阶差分平稳）")
print("  - ARIMA等模型要求平稳序列作为输入")

# ============================================================
# 2. GARCH 模型：波动率建模与预测
# ============================================================

print("\n=== 2. GARCH(1,1) 波动率建模 ===")
print("应用：风险管理、仓位调整、期权定价")

# 生成具有波动率聚集效应的收益率序列
def simulate_garch(omega=0.00001, alpha=0.1, beta=0.85, n=1000):
    """模拟GARCH(1,1)过程"""
    returns = np.zeros(n)
    sigma2 = np.zeros(n)
    sigma2[0] = omega / (1 - alpha - beta)

    for t in range(1, n):
        sigma2[t] = omega + alpha * returns[t-1]**2 + beta * sigma2[t-1]
        returns[t] = np.sqrt(sigma2[t]) * np.random.randn()

    return returns, np.sqrt(sigma2)

garch_returns, true_vol = simulate_garch(n=1000)

# 拟合GARCH模型
model = arch_model(garch_returns * 100, vol='Garch', p=1, q=1,
                   mean='Constant', dist='normal')
result = model.fit(disp='off')

print(result.summary().tables[1])

# 预测未来5天波动率
forecasts = result.forecast(horizon=5)
vol_forecast = np.sqrt(forecasts.variance.values[-1]) / 100

print(f"\n未来5日波动率预测（年化）:")
for i, v in enumerate(vol_forecast):
    print(f"  Day+{i+1}: {v * np.sqrt(252):.2%}")

# ============================================================
# 3. 协整检验：配对交易的数学基础
# ============================================================

print("\n=== 3. 协整检验（配对交易基础）===")

def simulate_cointegrated_pair(n=500, beta=1.5, noise_std=1.0):
    """
    模拟协整对：
    y = beta * x + epsilon
    其中 epsilon 是平稳过程（均值回归）
    x 是随机游走（非平稳）
    """
    x = np.cumsum(np.random.randn(n))
    epsilon = np.zeros(n)
    for t in range(1, n):
        epsilon[t] = 0.7 * epsilon[t-1] + np.random.randn() * noise_std

    y = beta * x + epsilon
    return pd.Series(x, name='X'), pd.Series(y, name='Y')

x, y = simulate_cointegrated_pair()

# 对每个序列单独做ADF检验
print("单独检验：")
adf_test(x, "X（非平稳）")
adf_test(y, "Y（非平稳）")

# 协整检验（Engle-Granger两步法）
print("\n协整检验（Engle-Granger）：")
coint_stat, p_value, critical_values = coint(x, y)
print(f"协整统计量: {coint_stat:.4f}")
print(f"p值:        {p_value:.6f}")
print(f"临界值:     1%={critical_values[0]:.3f}, 5%={critical_values[1]:.3f}")
print(f"结论:       {'✅ 存在协整关系（可做配对交易）' if p_value < 0.05 else '❌ 不存在协整关系'}")

# 计算价差（spread）
from sklearn.linear_model import LinearRegression
reg = LinearRegression()
reg.fit(x.values.reshape(-1, 1), y.values)
beta_hat = reg.coef_[0]
spread = y - beta_hat * x

print(f"\n估计的对冲比例 beta: {beta_hat:.4f}（真实值: 1.5）")
adf_test(spread, "价差序列（应该平稳）")
print(f"\n价差均值: {spread.mean():.4f}")
print(f"价差标准差: {spread.std():.4f}")

# 配对交易信号
z_score = (spread - spread.mean()) / spread.std()
entry_threshold = 2.0
exit_threshold  = 0.5

long_signal  = z_score < -entry_threshold   # 价差过低，做多Y做空X
short_signal = z_score >  entry_threshold   # 价差过高，做空Y做多X
exit_signal  = abs(z_score) < exit_threshold

print(f"\n配对交易信号统计:")
print(f"  做多信号次数:  {long_signal.sum()}")
print(f"  做空信号次数:  {short_signal.sum()}")
print(f"  平仓信号次数:  {exit_signal.sum()}")

# ============================================================
# 4. Kalman 滤波（动态对冲比例）
# ============================================================

print("\n=== 4. Kalman 滤波（动态Beta估计）===")
print("应用：配对交易中动态调整对冲比例，比OLS更适应市场变化")

def kalman_filter_beta(x: np.ndarray, y: np.ndarray,
                       delta: float = 1e-5) -> np.ndarray:
    """
    用Kalman滤波估计动态beta
    delta: 状态转移噪声（越大，beta变化越快）
    """
    n = len(x)
    # 状态：[beta, alpha]
    beta_hat = np.zeros(n)
    P = np.eye(2)
    x_state = np.vstack([x, np.ones(n)]).T   # 设计矩阵

    theta = np.array([1.0, 0.0])  # 初始估计
    Q = delta / (1 - delta) * np.eye(2)  # 状态噪声

    for t in range(n):
        xt = x_state[t]
        # 预测
        P = P + Q
        # 更新
        innovation = y[t] - xt @ theta
        S = xt @ P @ xt + 1.0
        K = P @ xt / S
        theta = theta + K * innovation
        P = P - np.outer(K, xt) @ P
        beta_hat[t] = theta[0]

    return beta_hat

dynamic_beta = kalman_filter_beta(x.values, y.values)
dynamic_spread = y.values - dynamic_beta * x.values

print(f"静态OLS beta:  {beta_hat:.4f}")
print(f"动态Kalman beta（最新）: {dynamic_beta[-1]:.4f}")
print(f"动态价差标准差: {dynamic_spread.std():.4f}")
print(f"静态价差标准差: {spread.std():.4f}")

# ============================================================
# 练习题
# ============================================================
"""
练习1：
从AkShare下载茅台(600519)和五粮液(000858)的历史价格，
进行协整检验，判断是否适合做配对交易。
计算价差的半衰期（half-life）：
half_life = -ln(2) / log(phi)，其中phi是AR(1)系数

练习2：
对沪深300指数日收益率拟合GARCH(1,1)模型，
预测未来20日波动率，并与历史实现波动率对比。
计算模型的持久性（persistence = alpha + beta），
解释这个数字的经济含义。

练习3（配对交易实战）：
选择同行业的两支股票，
实现完整的配对交易回测：
1. 用Kalman滤波动态估计对冲比例
2. 当z-score > 2时开仓，< 0.5时平仓
3. 计算年化收益、夏普比率、最大回撤
4. 与Buy&Hold基准对比
"""

if __name__ == "__main__":
    print("\n✅ 时间序列模块加载完成")
