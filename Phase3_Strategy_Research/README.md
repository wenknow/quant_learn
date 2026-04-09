# Phase 3：策略研究开发（核心阶段）

**时间**：第15-26周（约3个月）
**目标**：掌握完整的因子研究→回测→组合优化全流程

---

## 学习模块

| 模块 | 时间 | 核心内容 |
|------|------|---------|
| [week15_17_factor_research](./week15_17_factor_research/) | 第15-17周 | 因子全流程：预处理→IC分析→分层回测 |
| [week18_20_backtesting](./week18_20_backtesting/) | 第18-20周 | 向量化回测引擎从零实现 |
| [week21_23_machine_learning](./week21_23_machine_learning/) | 第21-23周 | LightGBM因子合成、防过拟合 |
| [week24_26_portfolio_optimization](./week24_26_portfolio_optimization/) | 第24-26周 | 均值-方差、风险平价、Kelly准则 |

## 第26周验收标准

- [ ] 独立实现完整回测引擎（含交易成本）
- [ ] 6个以上因子的多因子组合，Sharpe > 1.0
- [ ] GitHub上有回测报告（含净值图、绩效摘要）
- [ ] 能清楚解释回测中的各种偏差及规避方法

## 关键工具

```bash
pip install alphalens-reloaded  # 因子分析
pip install cvxpy               # 组合优化
pip install lightgbm            # 机器学习因子
pip install arch                # GARCH模型
```
