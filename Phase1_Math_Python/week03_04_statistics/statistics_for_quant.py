"""
Week 03-04: 量化必备统计学
核心：不是学统计学，而是学量化中用到的统计工具
"""

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. 收益率分布特征（量化的基础认知）
# ============================================================

np.random.seed(42)
n = 2520  # 约10年交易日

# 模拟真实股票收益率（使用t分布，更接近真实）
real_returns = stats.t.rvs(df=4, loc=0.0005, scale=0.012, size=n)

print("=== 收益率分布特征 ===")
print(f"均值:   {real_returns.mean():.6f}  (年化: {real_returns.mean()*252:.4f})")
print(f"标准差: {real_returns.std():.6f}  (年化波动率: {real_returns.std()*np.sqrt(252):.4f})")
print(f"偏度:   {stats.skew(real_returns):.4f}  (负偏 = 下跌尾部更厚)")
print(f"峰度:   {stats.kurtosis(real_returns):.4f}  (>0 = 厚尾，极端事件更多)")

# 正态性检验
jb_stat, jb_p = stats.jarque_bera(real_returns)
sw_stat, sw_p = stats.shapiro(real_returns[:500])  # Shapiro限样本量

print(f"\n=== 正态性检验 ===")
print(f"Jarque-Bera: 统计量={jb_stat:.2f}, p值={jb_p:.6f}")
print(f"  -> {'拒绝正态分布假设（真实）' if jb_p < 0.05 else '无法拒绝'}")
print(f"Shapiro-Wilk: p值={sw_p:.6f}")
print(f"  -> {'拒绝正态分布假设（真实）' if sw_p < 0.05 else '无法拒绝'}")
print("\n💡 结论：真实收益率不服从正态分布！这是量化中的基本常识。")

# ============================================================
# 2. 假设检验：因子有效性判断
# ============================================================

print("\n=== 因子有效性检验（t检验）===")

# 场景：你发现一个因子，高因子值组比低因子值组平均多赚0.1%/月
# 但这个差异是真实的 alpha，还是随机噪声？

np.random.seed(123)
n_months = 60  # 5年月度数据

# 模拟：高分组 vs 低分组的月度收益率
high_group = np.random.normal(0.015, 0.06, n_months)   # 高分组：均值1.5%/月
low_group  = np.random.normal(0.008, 0.06, n_months)   # 低分组：均值0.8%/月

# 双样本t检验
t_stat, p_value = stats.ttest_ind(high_group, low_group)
print(f"高分组均值: {high_group.mean():.4f}")
print(f"低分组均值: {low_group.mean():.4f}")
print(f"差值:       {high_group.mean() - low_group.mean():.4f}")
print(f"t统计量:    {t_stat:.4f}")
print(f"p值:        {p_value:.4f}")
print(f"结论:       {'因子有效（p<0.05）' if p_value < 0.05 else '因子无效（p>=0.05）'}")

# ============================================================
# 3. 多重检验问题（量化中最大的陷阱！）
# ============================================================

print("\n=== 多重检验陷阱 ===")
print("场景：你测试了100个因子，其中3个p值<0.05，是否代表有效？")

np.random.seed(42)
n_factors = 100
n_obs = 60
significance = 0.05

# 模拟：100个纯随机因子（真实alpha=0）
false_discoveries = 0
for _ in range(1000):  # 重复实验1000次
    p_values = []
    for _ in range(n_factors):
        random_factor = np.random.normal(0, 1, n_obs)
        random_returns = np.random.normal(0, 1, n_obs)
        _, p = stats.pearsonr(random_factor, random_returns)
        p_values.append(p)
    # 至少有一个p<0.05（假阳性）
    if any(p < significance for p in p_values):
        false_discoveries += 1

print(f"测试100个随机因子，至少发现1个'有效'因子的概率: {false_discoveries/1000:.1%}")
print(f"（理论值: 1-(0.95^100) = {1-(0.95**100):.1%}）")
print(f"⚠️  这说明：如果你测试了100个因子，即使全是随机的，")
print(f"   也有{1-(0.95**100):.0%}的概率'发现'至少1个'有效'因子！")

# Bonferroni 校正
bonferroni_threshold = significance / n_factors
print(f"\nBonferroni校正后的显著性水平: {bonferroni_threshold:.6f}")
print("💡 正确做法：测试多个因子时，需要用校正后的阈值判断有效性")
print("   推荐阅读：Harvey et al. (2016) - '...and the Cross-Section of Expected Returns'")

# ============================================================
# 4. 相关性分析（因子相关性、配对交易基础）
# ============================================================

print("\n=== 相关性分析 ===")

# Pearson vs Spearman（量化中通常用Spearman，对异常值不敏感）
np.random.seed(42)
factor = np.random.randn(500)
returns = 0.3 * factor + 0.7 * np.random.randn(500)   # 有相关性
returns_with_outlier = returns.copy()
returns_with_outlier[0] = 10   # 加入极端值

pearson_r, _ = stats.pearsonr(factor, returns_with_outlier)
spearman_r, _ = stats.spearmanr(factor, returns_with_outlier)

print(f"含极端值时：")
print(f"  Pearson相关系数:  {pearson_r:.4f}（受极端值影响大）")
print(f"  Spearman相关系数: {spearman_r:.4f}（更稳健）")
print(f"💡 量化因子分析中，优先使用 Spearman 秩相关（IC计算标准）")

# ============================================================
# 5. 置信区间（评估策略稳健性）
# ============================================================

print("\n=== 策略夏普比率置信区间 ===")

# 场景：策略历史夏普比率1.2，但真实夏普是多少？
n_years = 5
daily_returns = np.random.normal(0.0008, 0.012, n_years * 252)
sharpe = daily_returns.mean() / daily_returns.std() * np.sqrt(252)

# Bootstrap置信区间（不依赖正态假设）
def bootstrap_sharpe(returns: np.ndarray, n_bootstrap: int = 1000,
                     confidence: float = 0.95) -> tuple:
    sharpes = []
    n = len(returns)
    for _ in range(n_bootstrap):
        sample = np.random.choice(returns, size=n, replace=True)
        s = sample.mean() / sample.std() * np.sqrt(252)
        sharpes.append(s)
    alpha = (1 - confidence) / 2
    lower = np.percentile(sharpes, alpha * 100)
    upper = np.percentile(sharpes, (1 - alpha) * 100)
    return lower, upper

lower, upper = bootstrap_sharpe(daily_returns)
print(f"策略历史Sharpe: {sharpe:.4f}")
print(f"95%置信区间:    [{lower:.4f}, {upper:.4f}]")
print(f"💡 即使历史Sharpe=1.2，真实Sharpe可能只有{lower:.1f}左右")

# ============================================================
# 练习题
# ============================================================
"""
练习1：
下载沪深300过去10年日收益率，检验：
1) 是否服从正态分布？
2) 偏度和峰度与正态分布相比如何？
3) 极端收益率（超过3σ）出现频率是否高于正态分布预测？

练习2：
你发现一个因子，在过去3年月度IC均值为0.05，IC标准差为0.08。
计算：
1) ICIR（信息比率）
2) 该因子均值显著不为0的p值（单样本t检验）
3) 需要多少个月的数据才能在95%置信水平下确认因子有效？

练习3（重要）：
模拟"因子挖掘陷阱"：
- 生成500个随机特征和随机收益率
- 找出所有p<0.05的"有效"特征
- 对这些"有效"特征在新的样本外数据上验证
- 观察样本外表现如何（这就是过拟合的数学原理）
"""

if __name__ == "__main__":
    print("\n✅ 统计学模块加载完成")
