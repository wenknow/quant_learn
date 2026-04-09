# 量化交易系统学习路线

> 目标：18个月从后端工程师转型量化开发工程师
> 适合：有编程基础、了解基本金融交易、希望进入量化领域的工程师

---

## 总体路线图

```
Phase 1          Phase 2          Phase 3          Phase 4          Phase 5
数学+Python       金融市场基础      策略研究开发      工程化+实盘      求职准备
第1-8周          第9-14周         第15-26周        第27-36周       第37-42周
(2个月)          (1.5个月)        (3个月)          (2.5个月)       (1.5个月)
```

## 每周时间投入

| 时段 | 时长 | 内容 |
|------|------|------|
| 工作日（周一至周五）| 2.5小时/天（20:00-22:30）| 学习 + 编码 |
| 周六 | 6小时（09:00-12:00, 14:00-17:00）| 深度实践 |
| 周日 | 5小时（10:00-12:00, 14:00-17:00）| 阅读 + 总结 |
| **周均投入** | **约 23.5 小时** | |
| **18个月总计** | **约 1,700 小时** | |

---

## 目录结构

```
quant_learn/
├── Phase1_Math_Python/          # 第1-8周：数学与Python基础
│   ├── week01_02_python_stack/  # NumPy / Pandas / Matplotlib / SciPy
│   ├── week03_04_statistics/    # 概率论与统计
│   ├── week05_06_linear_algebra/# 线性代数与最优化
│   └── week07_08_time_series/   # 时间序列分析
│
├── Phase2_Finance_Basics/       # 第9-14周：金融市场基础
│   ├── week09_10_market_microstructure/  # 市场微观结构
│   ├── week11_12_factor_theory/          # 因子投资理论
│   └── week13_14_derivatives/            # 期权与衍生品
│
├── Phase3_Strategy_Research/    # 第15-26周：策略研究开发（核心）
│   ├── week15_17_factor_research/        # 因子研究全流程
│   ├── week18_20_backtesting/            # 回测系统搭建
│   ├── week21_23_machine_learning/       # 机器学习应用
│   └── week24_26_portfolio_optimization/ # 组合优化与风控
│
├── Phase4_Engineering/          # 第27-36周：工程化与实盘
│   ├── week27_30_trading_system/  # 交易系统架构
│   ├── week31_33_live_trading/    # 实盘演练
│   └── week34_36_performance/     # 性能优化
│
├── Phase5_Job_Prep/             # 第37-42周：求职准备
│   ├── projects/                  # Portfolio项目
│   └── interview_prep/            # 面试题库
│
└── resources/                   # 学习资源汇总
```

---

## 里程碑

| 时间 | 里程碑 | 验收标准 |
|------|--------|---------|
| 第8周末 | 数学+Python基础 | 独立实现OLS、GARCH、协整检验 |
| 第14周末 | 金融基础 | 能讲清Fama-French模型，手撕IC计算 |
| 第20周末 | 回测系统 | GitHub有完整框架+单因子测试报告 |
| 第26周末 | 多因子策略 | 6因子组合，年化超基准5%，Sharpe>1 |
| 第33周末 | 实盘演练 | 模拟盘运行1个月，日报自动生成 |
| 第38周末 | 求职Portfolio | 3个完整项目，README清晰 |
| **第42周** | **拿到Offer** | 目标：量化开发初级，年薪60-100万 |

---

## 每日执行模板

```
工作日 20:00-22:30
20:00-20:15  Anki复习昨日卡片
20:15-21:15  主学习任务（按当周计划）
21:15-21:30  整理笔记到Obsidian
21:30-22:30  实战编码
22:30        提交代码到GitHub

周末
09:00-10:00  复习本周内容
10:00-12:00  深度实践（不看教程）
14:00-16:00  阅读论文或书籍
16:00-17:00  写本周总结
```

## 核心原则

1. **代码优先**：每个概念学完立刻用Python实现
2. **GitHub每日提交**：保持commit记录
3. **写作输出**：每周写一篇研究笔记
4. **不追求完美**：先跑通，再优化
5. **18个月不换方向**：深度 > 广度

---

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置数据源（Tushare）
# 注册 tushare.pro 获取 token
export TUSHARE_TOKEN=your_token_here

# 3. 从Phase1开始
cd Phase1_Math_Python/week01_02_python_stack
jupyter notebook
```
