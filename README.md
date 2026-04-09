# 区块链 AI 量化交易 · 自营路线图

> **目标**：12个月建立稳定盈利的全自动AI量化系统，实现财务自由
> **定位**：个人自营交易（非求职），工程师转型为职业量化交易者
> **市场**：加密货币 CEX + DEX + 链上（Binance / OKX / Hyperliquid / ETH / SOL）

---

## 为什么选择加密市场做 AI 量化

| 维度 | 传统A股量化 | 加密AI量化 |
|------|-----------|----------|
| 交易时间 | 工作日9:30-15:00 | 24/7/365 |
| 市场效率 | 极高（难赚alpha） | 中低（机会窗口多） |
| 资金门槛 | 高（牌照+百万级） | 低（$5K可启动） |
| 数据获取 | 贵且受限 | 链上数据完全公开 |
| 策略竞争 | 顶级机构主导 | 散户alpha空间仍存 |
| 盈利目标 | 年化10-30%（顶级） | 年化50-300%（策略好时） |

---

## 总体路线图（12个月）

```
Phase 1          Phase 2          Phase 3          Phase 4          Phase 5
基础设施搭建      策略矩阵构建      AI赋能升级        生产级系统        规模化盈利
Month 1-2        Month 3-5        Month 6-8        Month 9-10       Month 11-12
Week 1-8         Week 9-20        Week 21-32       Week 33-40       Week 41-52
```

---

## 里程碑与验收标准

| 时间 | 里程碑 | 验收标准 |
|------|--------|---------|
| 第4周末 | 数据基础设施 | 实时获取10+交易所行情，历史数据入库 |
| 第8周末 | 第一个实盘bot | 资金费率套利策略跑通，有稳定正收益 |
| 第14周末 | 策略库建立 | 5+个回测验证策略，Sharpe>1.5 |
| 第20周末 | 链上alpha | 鲸鱼追踪系统跑通，有实盘验证的链上策略 |
| 第26周末 | AI信号上线 | ML模型接入实盘，预测准确率>55% |
| 第32周末 | 完整AI系统 | 多模型集成+动态仓位，月收益跑赢BTC持有 |
| 第40周末 | 生产系统 | 全自动运行，月回撤<15%，收益覆盖生活成本 |
| **第52周** | **财务自由** | 月收益稳定覆盖生活成本+持续复投增长 |

---

## 目录结构

```
quant_learn/
├── Phase1_Infrastructure/        # Month 1-2
│   ├── week01_02_data_pipeline/  # 数据采集与存储
│   ├── week03_04_backtesting/    # 回测框架搭建
│   ├── week05_06_first_bot/      # 第一个交易bot（资金费率套利）
│   └── week07_08_paper_trading/  # 纸交易 + 风控系统
│
├── Phase2_Strategy_Matrix/       # Month 3-5
│   ├── week09_10_trend/          # 趋势跟踪策略
│   ├── week11_12_stat_arb/       # 统计套利
│   ├── week13_14_microstructure/ # 市场微观结构
│   ├── week15_16_onchain_data/   # 链上数据采集
│   ├── week17_18_whale_tracking/ # 鲸鱼追踪策略
│   └── week19_20_defi_alpha/     # DeFi & Hyperliquid机会
│
├── Phase3_AI_Engine/             # Month 6-8
│   ├── week21_22_feature_eng/    # 多维度特征工程
│   ├── week23_24_ml_signals/     # XGBoost/LightGBM信号模型
│   ├── week25_26_deep_learning/  # LSTM/Transformer
│   ├── week27_28_rl_agent/       # 强化学习交易代理
│   ├── week29_30_sentiment/      # NLP情绪分析
│   └── week31_32_ensemble/       # 模型集成 + 动态仓位
│
├── Phase4_Production/            # Month 9-10
│   ├── week33_34_architecture/   # 生产架构（低延迟+高可用）
│   ├── week35_36_portfolio/      # 多策略组合管理
│   ├── week37_38_monitoring/     # Grafana监控 + Telegram告警
│   └── week39_40_optimization/   # 性能调优 + 容量扩展
│
├── Phase5_Scale/                 # Month 11-12
│   ├── week41_44_iteration/      # 策略持续迭代
│   ├── week45_48_scale/          # 资金规模扩大
│   └── week49_52_multichain/     # 多链布局 + 新alpha探索
│
├── live_system/                  # 实盘核心系统
│   ├── data/                     # 数据管道
│   ├── strategies/               # 策略库
│   ├── models/                   # AI模型
│   ├── execution/                # 执行引擎
│   ├── risk/                     # 风控系统
│   └── monitor/                  # 监控面板
│
└── resources/                    # 学习资源汇总
```

---

## 核心策略矩阵

### 低风险基础策略（先跑起来赚钱，建立信心）
| 策略 | 年化收益预期 | 风险 | 最低资金 |
|------|------------|------|---------|
| 资金费率套利（Delta中性） | 20-80% APY | 低 | $5K |
| 跨交易所现货套利 | 10-50% APY | 低-中 | $20K |
| Hyperliquid基差套利 | 20-60% APY | 低-中 | $5K |

### 中风险Alpha策略（主要盈利来源）
| 策略 | 年化收益预期 | 核心技术 |
|------|------------|---------|
| BTC/ETH趋势跟踪 | 50-200% | 技术分析 + ML信号 |
| 山寨币动量轮动 | 100-500% | 热点追踪 + 轮动模型 |
| 链上鲸鱼跟单 | 50-300% | on-chain实时分析 |

### AI增强策略（护城河，区分度最高）
| 策略 | 核心优势 | 关键技术 |
|------|---------|---------|
| 多因子ML信号 | 融合链上+技术+情绪 | XGBoost/LightGBM |
| LLM情绪套利 | 信息优势，速度快 | GPT API + NLP |
| RL执行优化 | 动态最优仓位 | PPO/SAC |

---

## 技术栈

```python
# 数据层
ccxt              # 统一交易所API（100+交易所）
web3.py           # 以太坊链上数据
solders/solana-py # Solana链上数据
dune-client       # Dune Analytics SQL查询
websockets        # 实时数据流

# 存储层
TimescaleDB       # 时序数据库（OHLCV/orderbook）
Redis             # 实时缓存（信号/仓位）
PostgreSQL        # 交易记录/元数据

# 量化计算
numpy / pandas    # 数据处理
vectorbt          # 高性能向量化回测（比backtrader快100x）
scipy / statsmodels # 统计检验

# AI/ML
scikit-learn      # 传统ML
xgboost / lightgbm # 主力信号模型
pytorch           # LSTM / Transformer / RL
transformers      # LLM情绪分析

# 执行层
ccxt              # CEX统一交易接口
hyperliquid-python-sdk # HL永续合约
web3.py / uniswap-python # DEX链上交互

# 监控
grafana           # 可视化面板
python-telegram-bot # 实时告警
loguru            # 结构化日志
```

---

## 财务自由目标拆解

| 阶段 | 资金规模 | 月均收益率 | 月收益（USD） |
|------|---------|-----------|------------|
| 第2个月：第一个实盘策略 | $5,000 | 5-10% | $250-500 |
| 第5个月：策略矩阵成型 | $15,000 | 8-12% | $1,200-1,800 |
| 第8个月：AI系统上线 | $40,000 | 8-15% | $3,200-6,000 |
| 第10个月：生产系统稳定 | $80,000 | 8-12% | $6,400-9,600 |
| **第12个月：财务自由** | **$150,000+** | **8-12%** | **$12,000-18,000** |

> 关键认知：复利 + 策略持续迭代 是核心。不追求单月暴利，追求可持续的alpha。

---

## 每周时间投入

| 时段 | 时长 | 内容 |
|------|------|------|
| 工作日（周一至周五） | 3小时/天（20:00-23:00） | 学习 + 编码 |
| 周六 | 8小时（09:00-12:00, 14:00-19:00） | 深度开发 |
| 周日 | 5小时（10:00-12:00, 14:00-17:00） | 研究 + 复盘 |
| **周均投入** | **约 29 小时** | |
| **12个月总计** | **约 1,500 小时** | |

---

## 核心原则

1. **资金安全第一**：单策略仓位上限30%，强制止损，保住本金才能复利
2. **先赚钱再优化**：简单可用的策略比复杂不稳定的策略更有价值
3. **链上数据是护城河**：AI + 链上数据是散户相对机构最独特的alpha来源
4. **小步验证快速迭代**：纸交易（1周）→ 小资金实盘（1-2周）→ 扩大规模
5. **自动化一切**：目标是睡觉时系统在赚钱，减少人工干预
6. **记录一切**：每笔交易都要有记录，建立自己的交易数据集

---

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API Keys（.env文件）
cp .env.example .env
# 填入 Binance/OKX API keys

# 3. 从Phase1开始
cd Phase1_Infrastructure/week01_02_data_pipeline
jupyter notebook

# 4. 查看详细周计划
cat WEEKLY_PLAN.md
```
