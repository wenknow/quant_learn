"""
Week 01 - Day 1: NumPy 核心
目标：掌握向量化运算，理解为什么量化中不用for循环
"""

import numpy as np
import time

# ============================================================
# 1. 数组创建
# ============================================================

# 基础创建
arr = np.array([1, 2, 3, 4, 5], dtype=np.float64)
matrix = np.zeros((3, 3))
identity = np.eye(4)
prices = np.linspace(10, 20, 100)       # 100个均匀分布的价格
dates_idx = np.arange(0, 252, 1)        # 252个交易日索引

# 随机数（量化中大量使用）
np.random.seed(42)
returns = np.random.normal(loc=0.001, scale=0.02, size=252)  # 模拟日收益率
noise = np.random.standard_t(df=5, size=1000)                 # t分布噪声（更真实）

print("=== 基础数组 ===")
print(f"形状: {returns.shape}, 均值: {returns.mean():.4f}, 标准差: {returns.std():.4f}")

# ============================================================
# 2. 向量化运算（量化核心技能）
# ============================================================

# 计算累计收益（向量化 vs 循环对比）
prices_arr = np.array([100.0] * 252)

# 慢的写法（禁止在量化代码中出现）
start = time.time()
for i in range(1, len(returns)):
    prices_arr[i] = prices_arr[i-1] * (1 + returns[i])
loop_time = time.time() - start

# 快的写法（向量化）
start = time.time()
prices_vec = 100 * np.cumprod(1 + returns)
vec_time = time.time() - start

print(f"\n=== 性能对比 ===")
print(f"循环耗时:   {loop_time*1000:.3f} ms")
print(f"向量化耗时: {vec_time*1000:.3f} ms")
print(f"加速比: {loop_time/vec_time:.1f}x")

# ============================================================
# 3. 广播机制（Broadcasting）
# ============================================================

# 场景：对股票池每只股票减去市场均值（中性化操作）
n_stocks = 500
n_days = 252
factor_matrix = np.random.randn(n_days, n_stocks)   # 因子矩阵

# 每日截面去均值（广播）
daily_mean = factor_matrix.mean(axis=1, keepdims=True)   # (252, 1)
factor_demeaned = factor_matrix - daily_mean              # (252, 500) 广播

print(f"\n=== 广播机制 ===")
print(f"因子矩阵形状: {factor_matrix.shape}")
print(f"每日均值形状: {daily_mean.shape}")
print(f"去均值后各行均值（应接近0）: {factor_demeaned.mean(axis=1)[:3].round(10)}")

# ============================================================
# 4. 移动统计（量化中最常用的操作）
# ============================================================

def rolling_mean(arr: np.ndarray, window: int) -> np.ndarray:
    """用卷积实现移动平均（比循环快）"""
    kernel = np.ones(window) / window
    return np.convolve(arr, kernel, mode='valid')

def rolling_std(arr: np.ndarray, window: int) -> np.ndarray:
    """移动标准差"""
    result = np.full(len(arr), np.nan)
    for i in range(window - 1, len(arr)):
        result[i] = arr[i - window + 1:i + 1].std()
    return result

close_prices = 100 * np.cumprod(1 + np.random.normal(0.001, 0.02, 252))
ma20 = rolling_mean(close_prices, 20)
print(f"\n=== 移动统计 ===")
print(f"原始价格序列长度: {len(close_prices)}")
print(f"20日均线长度: {len(ma20)}")

# ============================================================
# 5. 协方差矩阵（组合优化核心）
# ============================================================

n_assets = 10
daily_returns = np.random.multivariate_normal(
    mean=np.zeros(n_assets),
    cov=np.eye(n_assets) * 0.0004,   # 假设无相关性，年化波动率约10%
    size=252
)

cov_matrix = np.cov(daily_returns.T)   # (10, 10) 协方差矩阵
corr_matrix = np.corrcoef(daily_returns.T)

print(f"\n=== 协方差矩阵 ===")
print(f"协方差矩阵形状: {cov_matrix.shape}")
print(f"对角线（方差）: {np.diag(cov_matrix).round(6)}")

# 年化波动率
annual_vol = np.sqrt(np.diag(cov_matrix) * 252)
print(f"年化波动率: {annual_vol.round(4)}")

# ============================================================
# 6. 特征值分解（PCA降维基础）
# ============================================================

eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
explained_variance = eigenvalues / eigenvalues.sum()
print(f"\n=== PCA 特征值分解 ===")
print(f"前3个主成分解释方差: {explained_variance[-3:][::-1].round(4)}")

# ============================================================
# 练习题（独立完成，不看答案）
# ============================================================
"""
练习1：
给定价格序列，用纯NumPy（不用pandas）计算布林带：
- 中轨：20日移动平均
- 上轨：中轨 + 2倍20日标准差
- 下轨：中轨 - 2倍20日标准差

练习2：
给定一个 (252, 500) 的日收益率矩阵，
用向量化的方式计算每只股票的：
- 年化收益率
- 年化波动率
- 夏普比率（假设无风险利率2%）
不允许使用任何循环。

练习3：
实现一个向量化的回撤计算函数：
输入：净值序列（np.ndarray）
输出：最大回撤值（float）和回撤序列（np.ndarray）
"""

if __name__ == "__main__":
    # 答案验证（自己先做完再看）

    # 练习1答案
    close = 100 * np.cumprod(1 + np.random.normal(0.001, 0.02, 252))
    window = 20
    mid = np.array([close[i-window:i].mean() for i in range(window, len(close)+1)])
    std = np.array([close[i-window:i].std() for i in range(window, len(close)+1)])
    upper = mid + 2 * std
    lower = mid - 2 * std
    print(f"\n练习1 布林带: 上轨={upper[-1]:.2f}, 中轨={mid[-1]:.2f}, 下轨={lower[-1]:.2f}")

    # 练习2答案
    rets = np.random.normal(0.001, 0.02, (252, 500))
    annual_return = (1 + rets).prod(axis=0) ** (252/252) - 1  # 已经是252天
    annual_vol_2 = rets.std(axis=0) * np.sqrt(252)
    sharpe = (annual_return - 0.02) / annual_vol_2
    print(f"练习2 夏普比率均值={sharpe.mean():.4f}")

    # 练习3答案
    def max_drawdown(nav: np.ndarray):
        rolling_max = np.maximum.accumulate(nav)
        drawdown = (nav - rolling_max) / rolling_max
        return drawdown.min(), drawdown

    nav = np.cumprod(1 + np.random.normal(0.001, 0.02, 252))
    mdd, dd_series = max_drawdown(nav)
    print(f"练习3 最大回撤={mdd:.2%}")
