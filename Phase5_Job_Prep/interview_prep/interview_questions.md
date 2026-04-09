# 量化开发岗面试题库

> 整理自各大私募、券商量化部门面试真题

---

## 一、因子研究类（研究员方向必考）

### Q1：什么是IC？ICIR？如何判断因子有效性？

**标准回答：**
- IC（信息系数）= 本期因子值与下期收益率的相关系数
- 通常用 **Spearman秩相关**（对异常值稳健）
- ICIR = IC均值 / IC标准差（衡量因子稳定性）

**判断标准：**
| 指标 | 有效阈值 | 优秀阈值 |
|------|---------|---------|
| IC均值 | > 0.03 | > 0.06 |
| ICIR | > 0.5 | > 1.0 |
| IC胜率 | > 55% | > 60% |
| t统计量 | > 2.0 | > 3.0 |

**代码实现：**
```python
from scipy.stats import spearmanr

def calc_ic(factor, returns):
    common = factor.index.intersection(returns.index)
    ic, p_value = spearmanr(factor[common], returns[common])
    return ic, p_value
```

---

### Q2：回测中的 Look-ahead Bias（未来函数）有哪些常见形式？

**必须知道的4种形式：**

1. **财务数据点时问题**
   - 错误：用季报数据当天就放入因子
   - 正确：财报披露后1个月才可用（用 `merge_asof` 实现）

2. **技术指标计算错误**
   - 错误：用当日最高价计算布林带上轨
   - 正确：只用已知的收盘价序列

3. **调仓执行时点**
   - 错误：用当日收盘价计算信号，当日收盘价成交
   - 正确：T+1执行（当日信号→次日成交）

4. **退市股问题**
   - 错误：只用现存股票（幸存者偏差）
   - 正确：股票池包含所有历史上存在过的股票

---

### Q3：多重检验问题是什么？如何处理？

**背景：** 测试100个因子，即使全是随机的，也有99.4%概率"发现"显著因子

**处理方法：**
1. **Bonferroni校正**：显著性阈值 = α / n（最保守）
2. **BH校正（Benjamini-Hochberg）**：控制FDR（假发现率）
3. **Shaffer方法**
4. **样本外验证**：最直接的方法，必须用未见过的数据验证

```python
from statsmodels.stats.multitest import multipletests

# BH校正
reject, p_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
```

---

## 二、回测框架类（开发方向必考）

### Q4：用 Python 实现一个向量化回测引擎，注意哪些问题？

**面试评分要点：**

```python
class VectorizedBacktester:
    def run(self, weights, returns):
        # ✅ 正确：T+1执行
        portfolio_returns = (weights.shift(1) * returns).sum(axis=1)

        # ❌ 错误（未来函数）：
        # portfolio_returns = (weights * returns).sum(axis=1)

        # ✅ 交易成本
        turnover = weights.diff().abs().sum(axis=1)
        costs = turnover * (commission + slippage)

        net_returns = portfolio_returns - costs
        nav = (1 + net_returns).cumprod()
        return nav
```

**必须提到的细节：**
1. T+1执行（`weights.shift(1)`）
2. 交易成本（佣金+印花税+滑点）
3. 退市股填充0收益而非删除
4. 调仓频率对换手率的影响

---

### Q5：什么是Sharpe比率？如何计算？有什么缺陷？

```python
def sharpe_ratio(returns, rf=0.02, periods=252):
    excess = returns - rf / periods
    return excess.mean() / excess.std() * np.sqrt(periods)
```

**Sharpe的缺陷：**
1. 假设收益率正态分布（实际厚尾）
2. 对上涨波动和下跌波动同等惩罚
3. 不区分主动风险和被动风险
4. 对不同时间段的比较不公平

**替代指标：**
- Sortino Ratio：只惩罚下行波动
- Calmar Ratio：年化收益 / 最大回撤
- Omega Ratio：收益概率加权

---

## 三、统计与数学类

### Q6：ADF检验的原理？什么情况下需要用？

**原理：** 检验时间序列是否存在单位根（不平稳）
- H0：存在单位根（不平稳）
- H1：不存在单位根（平稳）

**量化中的应用：**
1. 配对交易：价差序列必须平稳
2. ARIMA建模：需要平稳输入
3. 因子有效性：收益率通常是平稳的，价格通常不是

```python
from statsmodels.tsa.stattools import adfuller

result = adfuller(series)
is_stationary = result[1] < 0.05  # p值
```

---

### Q7：解释 GARCH 模型，在量化中有什么用？

**GARCH(1,1)：**
σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}

**参数含义：**
- ω：长期均值波动率
- α：ARCH项（对新信息的反应速度）
- β：GARCH项（波动率持续性）
- α + β：持久性（越接近1，波动聚集效应越强）

**量化应用：**
1. 波动率预测 → 动态调整仓位
2. 期权定价中的历史波动率输入
3. 风险价值（VaR）计算
4. 波动率交易策略

---

## 四、Python/工程类（开发岗必考）

### Q8：手撕代码：计算滚动最大回撤

```python
import numpy as np
import pandas as pd

def rolling_max_drawdown(nav: pd.Series, window: int = 252) -> pd.Series:
    """计算滚动N日最大回撤"""
    rolling_max = nav.rolling(window, min_periods=1).max()
    drawdown = (nav - rolling_max) / rolling_max
    return drawdown.rolling(window, min_periods=1).min()

# 测试
nav = pd.Series([1, 1.1, 1.05, 1.2, 1.0, 1.15, 1.25])
print(rolling_max_drawdown(nav, window=4))
```

---

### Q9：手撕代码：向量化实现移动平均（不用pandas）

```python
import numpy as np

def fast_moving_average(arr: np.ndarray, window: int) -> np.ndarray:
    """用卷积实现移动平均（O(n)复杂度）"""
    kernel = np.ones(window) / window
    ma = np.convolve(arr, kernel, mode='valid')
    # 补齐长度
    result = np.full(len(arr), np.nan)
    result[window-1:] = ma
    return result

# 更快：cumsum法（O(1)查询）
def moving_average_cumsum(arr: np.ndarray, window: int) -> np.ndarray:
    result = np.full(len(arr), np.nan)
    cumsum = np.cumsum(np.insert(arr, 0, 0))
    result[window-1:] = (cumsum[window:] - cumsum[:-window]) / window
    return result
```

---

### Q10：什么是协整？与相关性有什么区别？

| 维度 | 相关性 | 协整 |
|------|--------|------|
| 本质 | 线性相关程度 | 长期均衡关系 |
| 时间维度 | 当期截面 | 时序长期 |
| 适用场景 | 因子分析 | 配对交易 |
| 稳定性 | 可能随时间变化 | 理论上稳定 |

**例子：**
- 茅台和五粮液：相关性高，但协整关系需要实证检验
- 两只ETF跟踪同一指数：协整关系强

---

## 五、市场认知类

### Q11：A股T+1制度对量化策略有什么影响？

1. **日内不能平仓**：买入的股票当天无法卖出
2. **日内可以卖空**：融券当日可以回补（但有门槛）
3. **对策略的影响**：
   - 日内趋势策略收益打折
   - 隔夜持仓带来额外风险（跳空风险）
   - 高频策略受限严重
4. **应对方法**：
   - 用ETF对冲隔夜风险
   - 避开需要当日换手的高频策略

---

### Q12：什么是冲击成本（Market Impact）？如何建模？

**定义：** 大额订单因改变供需关系而导致的执行价格偏差

**Almgren-Chriss 模型（经典）：**
```
临时冲击 = η * (v/σ) 
永久冲击 = γ * (v/σ)

其中：v = 交易速率，σ = 波动率
```

**实践经验：**
- 对于1亿规模的策略，冲击成本约为10-30bps
- 成交量参与率不超过当日成交量的5-10%
- 日内分拆订单（TWAP/VWAP算法）

---

## 面试准备计划（第37-42周）

### 每日刷题计划

```
周一：IC/ICIR相关题 + 手撕因子计算代码
周二：回测框架题 + 手撕Sharpe/回撤计算
周三：统计学题 + 手撕假设检验代码
周四：市场认知题 + 手撕GARCH/协整代码
周五：模拟面试（找朋友或自问自答录音）
```

### 必备 Portfolio 项目

- [ ] 多因子选股系统（GitHub，有完整README）
- [ ] 配对交易策略（含协整检验和动态对冲）
- [ ] 机器学习因子合成（LightGBM，正确CV）

### 目标公司 & 薪资范围

| 公司类型 | 代表机构 | 量化开发薪资 |
|---------|---------|------------|
| 头部私募 | 幻方、九坤、明汯、灵均 | 100-300万+ |
| 中型私募 | 各地10-100亿规模 | 60-150万 |
| 券商量化 | 中金、华泰、国君 | 50-120万 |
| 互联网金融 | 蚂蚁、字节金融 | 60-120万 |
