# 每周详细计划 · 区块链AI量化自营

> 更新日期：2026-04-09
> 总周期：52周（12个月）
> 每周投入：~29小时

---

# PHASE 1：基础设施搭建（Week 1-8）

目标：建立数据管道、回测框架，跑通第一个实盘盈利策略

---

## Week 1-2：数据基础设施 + 市场认知

### 学习目标
- 理解加密市场结构：CEX/DEX/链上、现货/合约/期权、资金费率机制
- 掌握 ccxt 获取多交易所实时/历史数据
- 建立本地时序数据库

### 每日任务

**周一**（3h）
- 阅读：加密市场结构扫盲（CEX vs DEX vs 链上的本质区别）
- 实操：注册 Binance、OKX、Bybit 账号，开通API权限
- 代码：`pip install ccxt`，跑通第一个 fetch_ohlcv

**周二**（3h）
- 深入：ccxt 统一API文档，理解市场类型（spot/swap/future/option）
- 代码：封装多交易所数据采集器，支持自动重试、限速处理
- 输出：`data_collector.py` - 可采集 Binance/OKX/Bybit 历史K线

**周三**（3h）
- 学习：TimescaleDB 安装与基本使用（为什么用时序DB）
- 实操：本地安装 TimescaleDB（或用 PostgreSQL + 时序扩展）
- 代码：设计数据表结构（ohlcv、orderbook、trades、funding_rate）

**周四**（3h）
- 代码：实现数据入库管道，支持增量更新
- 实操：采集 BTC/ETH 过去2年 1h K线数据入库
- 工具：安装配置 Redis（用于实时数据缓存）

**周五**（3h）
- 代码：WebSocket 实时数据流（orderbook + trades + ticker）
- 输出：`realtime_feed.py` - 实时推送到 Redis
- 测试：验证数据完整性，处理断线重连

**周六**（8h）
- 上午（3h）：深入学习资金费率机制（永续合约核心）
  - 什么是资金费率，为什么存在，如何套利
  - 采集各大交易所历史资金费率数据
- 下午（5h）：数据清洗与质量检验
  - 缺失值处理，异常值检测
  - 跨交易所时间对齐
  - 输出：完整的数据质量报告

**周日**（5h）
- 上午（2h）：研究整理周内笔记，深化市场理解
- 下午（3h）：探索 Binance 全量品种数据
  - 哪些币种流动性最好（bid-ask spread分析）
  - 资金费率最高的永续合约有哪些
  - 写本周总结

### 本周验收
- [ ] 能实时采集10+交易所数据
- [ ] 本地数据库有BTC/ETH过去2年完整数据
- [ ] 资金费率历史数据完整入库
- [ ] 实时WebSocket数据流稳定运行

### 关键代码文件
```
Phase1_Infrastructure/week01_02_data_pipeline/
├── data_collector.py      # 历史数据采集
├── realtime_feed.py       # 实时数据流
├── db_schema.sql          # 数据库表结构
└── data_quality_check.py  # 数据质量检验
```

---

## Week 3-4：回测框架搭建

### 学习目标
- 理解回测的常见陷阱（幸存者偏差、未来函数、滑点）
- 用 vectorbt 建立高性能回测框架
- 理解加密市场特有指标：资金费率成本、滑点模型

### 每日任务

**周一**（3h）
- 阅读：quantopian 回测陷阱总结，加密市场特殊性
- 安装：`pip install vectorbt`，跑通官方示例
- 对比：vectorbt vs backtrader vs 自研，选择理由

**周二**（3h）
- 代码：封装自己的回测基类
  - 统一数据接口（从 TimescaleDB 读取）
  - 手续费模型（maker/taker，加密市场实际费率）
  - 滑点模型（基于成交量的动态滑点）

**周三**（3h）
- 代码：实现第一个完整回测
  - 策略：BTC 简单移动均线交叉（用于验证框架）
  - 输出指标：年化收益、Sharpe、最大回撤、Calmar
  - 可视化：收益曲线、回撤曲线

**周四**（3h）
- 深入：加密市场回测的特殊处理
  - 永续合约资金费率成本计算
  - 24/7市场的仓位管理差异
  - 多标的组合回测框架

**周五**（3h）
- 代码：回测结果分析模块
  - 月度收益热力图
  - 滚动 Sharpe / 滚动最大回撤
  - 策略相关性分析

**周六**（8h）
- 上午（4h）：深度实战——用框架跑10个不同参数的均线策略
  - 参数优化（网格搜索）
  - 过拟合检验（walk-forward分析）
- 下午（4h）：加入资金费率数据到回测框架
  - 实现 Delta 中性策略的回测支持
  - 计算真实盈亏（含资金费率收入/支出）

**周日**（5h）
- 上午：阅读 vectorbt 高级文档
- 下午：为后续策略研究准备数据集（山寨币200个，过去3年1h数据）
- 写本周总结

### 本周验收
- [ ] 完整回测框架可用（含手续费/滑点/资金费率）
- [ ] 能在200个品种上批量跑回测
- [ ] walk-forward 验证流程跑通
- [ ] 回测报告自动生成

---

## Week 5-6：第一个实盘 Bot（资金费率套利）

### 学习目标
- 深刻理解资金费率套利原理和风险
- 实现第一个完整的自动交易系统
- 掌握仓位管理、风险控制基础

### 策略逻辑
```
资金费率套利（Delta中性）：
1. 选择资金费率高的永续合约（如 >0.05%/8h）
2. 在现货做多 + 永续做空（Delta中性）
3. 每8小时收取资金费率
4. 当资金费率回落到阈值以下时平仓
```

### 每日任务

**周一-周二**（6h）
- 代码：交易执行模块
  - ccxt 下单封装（限价单/市价单/止损单）
  - 智能重试和错误处理
  - 仓位同步（本地仓位与交易所实际仓位对账）

**周三-周四**（6h）
- 代码：资金费率套利策略逻辑
  - 实时扫描全市场资金费率（Binance+OKX+Bybit）
  - 机会评分（资金费率 - 开仓成本 - 预期关仓成本）
  - 开仓/平仓决策逻辑

**周五**（3h）
- 代码：风控模块
  - 单策略最大仓位限制
  - 最大亏损自动平仓（止损）
  - 账户余额监控

**周六**（8h）
- 全天：纸交易测试
  - 模拟盘运行整天，验证逻辑
  - 记录所有决策日志
  - 发现并修复bug

**周日**（5h）
- 上午：复盘纸交易结果
- 下午：优化执行逻辑，准备实盘

### 本周验收
- [ ] 资金费率套利 bot 完整可运行
- [ ] 纸交易连续运行24小时无崩溃
- [ ] 风控模块测试通过（模拟极端情况）

---

## Week 7-8：纸交易 + 风控完善 + 小额实盘

### 学习目标
- 完善风控体系
- 资金费率策略正式实盘（$1,000-$3,000 小额验证）
- 建立交易日志和绩效追踪系统

### 每日任务

**周一-周二**（6h）
- 代码：完善风控系统
  - 强制止损（单笔最大亏损$X）
  - 账户级别保护（总回撤超过Y%暂停所有交易）
  - 流动性检查（成交量不足时禁止开仓）

**周三-周四**（6h）
- 代码：绩效追踪系统
  - 实时P&L计算（含未实现盈亏）
  - 策略归因分析（资金费率收入 vs 价格损益）
  - Telegram 每日报告自动推送

**周五**（3h）
- 实操：部署到云服务器（阿里云/腾讯云）
  - 配置 systemd 服务自动重启
  - 设置告警（服务宕机/余额不足）

**周六-周日**（13h）
- 正式小额实盘（$1,000-$3,000）
  - 持续监控，记录所有异常
  - 复盘每笔交易，对比预期

### Phase 1 验收标准
- [ ] 第一个实盘策略稳定运行
- [ ] 24/7自动化运行，无需人工干预
- [ ] 绩效追踪系统可用，每日报告自动生成
- [ ] 风控系统测试全通过

---

# PHASE 2：策略矩阵构建（Week 9-20）

目标：建立多个独立可盈利的策略，形成策略库，降低依赖单一策略的风险

---

## Week 9-10：趋势跟踪策略

### 学习目标
- 掌握加密市场的趋势特性（比传统市场更明显的趋势性）
- 实现多周期趋势跟踪系统
- 理解趋势策略的适用场景和失效场景

### 研究重点

**趋势跟踪核心指标**
```python
# 需要研究和实现的指标组合
indicators = [
    "EMA交叉（短期/中期/长期）",
    "ADX（趋势强度）",
    "ATR（波动率归一化止损）",
    "布林带宽度（波动率挤压）",
    "RSI（避免追顶追底）",
    "成交量确认（价量共振）",
]
```

**策略框架**
```
信号生成：EMA(7) > EMA(25) > EMA(99) 多头排列
趋势确认：ADX > 25
入场：回调至EMA25附近 + RSI < 60 时买入
止损：ATR(14) * 2 以下
止盈：移动止盈（追踪EMA25）
品种：BTC、ETH、主流山寨（按市值前20）
```

### 每日任务
- 周一：研究加密市场趋势统计特性（自相关性分析）
- 周二：实现指标库（基于 pandas-ta 或自研）
- 周三：趋势策略回测（2020-2025，覆盖牛熊）
- 周四：参数优化 + 稳定性检验
- 周五：多品种组合回测（20个主流币）
- 周六：深度分析——趋势策略在不同市场状态下的表现
- 周日：写策略研究报告，记录关键发现

### 本周验收
- [ ] 趋势跟踪策略完整实现并通过回测
- [ ] 覆盖2020-2025牛熊周期，Sharpe > 1.5
- [ ] 多品种组合表现优于单一BTC持有

---

## Week 11-12：统计套利

### 学习目标
- 掌握协整检验（Engle-Granger / Johansen）
- 实现跨交易所套利 + 相关币种配对交易
- 理解统计套利在加密市场的局限性

### 研究重点

**策略类型**
1. **跨交易所价差套利**：同一品种在不同交易所的价差
   - BTC-USDT: Binance vs OKX vs Bybit
   - 需要快速执行，关注提现时间和费用
   
2. **相关币种配对交易**：
   - BTC vs ETH（历史相关性高）
   - SOL vs AVAX（同类Layer1）
   - 协整检验确认关系
   - 价差均值回归时开仓

3. **现货-永续基差套利**：
   - 现货价格 vs 永续价格的基差
   - 基差过大时套利

### 每日任务
- 周一：协整理论复习 + 在加密数据上验证
- 周二：跨交易所价差数据采集和分析
- 周三：配对交易策略实现（协整版本）
- 周四：现货-永续基差套利策略
- 周五：回测并对比三种套利策略
- 周六：深度研究——套利机会的频率和稳定性分析
- 周日：总结、选择最优套利策略进入实盘候选

---

## Week 13-14：市场微观结构分析

### 学习目标
- 理解订单簿动态和价格发现机制
- 利用orderbook特征预测短期价格方向
- 实现流动性分析工具

### 研究重点

**orderbook 特征提取**
```python
features = {
    "bid_ask_spread": "买卖价差（流动性代理变量）",
    "order_book_imbalance": "买卖盘量不平衡度",
    "mid_price_impact": "大单冲击成本",
    "depth_profile": "不同价位的挂单分布",
    "trade_flow_imbalance": "成交流方向",
    "large_order_detection": "大单检测（鲸鱼行为）",
}
```

**应用方向**
- 短期价格预测（5min/15min级别信号）
- 最优执行（减少滑点）
- 鲸鱼行为预警

### 每日任务
- 周一-周二：orderbook数据采集 + 特征计算
- 周三-周四：微观结构特征与短期价格的相关性研究
- 周五：初步预测模型（orderbook -> 短期方向）
- 周六：深度：大单检测系统
- 周日：总结微观结构分析工具集

---

## Week 15-16：链上数据采集

### 学习目标
- 掌握以太坊/Solana 链上数据读取
- 建立链上数据管道（地址追踪/合约事件）
- 对接 Dune Analytics，利用现有分析成果

### 关键数据源

**以太坊链上**
```python
# web3.py 读取
- 区块/交易数据
- ERC20 Transfer 事件（大额转账）
- Uniswap V3 Swap 事件（DEX交易流）
- Aave/Compound 借贷数据（杠杆水位）
- 交易所热钱包流入/流出（持仓变化）
```

**Solana 链上**
```python
# Solana RPC
- Jupiter DEX聚合器交易
- Raydium/Orca AMM 流动性
- 聪明钱地址追踪
```

**Dune Analytics**
- 预建仪表板快速获取数据
- 自定义SQL查询链上聚合数据

### 每日任务
- 周一：web3.py 基础，连接以太坊节点（Alchemy/Infura免费额度）
- 周二：监听大额 ETH/USDT 转账
- 周三：追踪主要 CEX 热钱包（Binance/OKX 地址）
- 周四：Dune Analytics API 对接，提取关键指标
- 周五：Solana RPC 对接，聪明钱地址数据库建立
- 周六：整合链上数据入库，建立实时监控面板
- 周日：分析链上数据与价格的关系，寻找领先指标

---

## Week 17-18：鲸鱼追踪策略

### 学习目标
- 识别链上"聪明钱"地址
- 建立鲸鱼行为追踪系统
- 验证跟单策略的有效性

### 策略逻辑
```
1. 识别聪明钱地址（历史上持续盈利的钱包）
   - 过去6个月收益率 > 200%
   - 交易频率适中（非机器人）
   - 早期买入新项目的记录

2. 实时监控大额交易
   - 交易所大额提币（可能购买）
   - 交易所大额充币（可能出售）
   - DEX大额买入/卖出

3. 跟单执行
   - 检测到鲸鱼买入信号后X分钟内跟单
   - 风控：单次跟单不超过总资金5%
   - 止损：跟单亏损10%自动止损
```

### 每日任务
- 周一：链上聪明钱识别算法（盈利历史分析）
- 周二：建立聪明钱地址数据库（top 200个地址）
- 周三：实时监控系统实现
- 周四：跟单信号生成逻辑
- 周五：历史回测验证（模拟跟单过去1年）
- 周六：深度分析——哪类鲸鱼行为最有预测价值
- 周日：纸交易准备，实盘候选策略评估

---

## Week 19-20：DeFi Alpha + Hyperliquid

### 学习目标
- 理解 DeFi 协议创造的量化机会
- 掌握 Hyperliquid 永续合约交易
- 探索 MEV 基础（三明治/套利/清算）

### 重点方向

**Hyperliquid 策略**
```python
strategies = [
    "HLP Vault 流动性提供（年化20-40%）",
    "Hyperliquid 资金费率套利",
    "Hyperliquid vs CEX 价差套利",
    "Builder Codes 返佣优化",
]
```

**DeFi 套利**
- AMM 价格套利（Uniswap V3 vs CEX）
- 借贷协议利率套利
- 清算机会捕获

### 每日任务
- 周一-周二：Hyperliquid SDK 深度使用，历史数据分析
- 周三-周四：HL资金费率套利实现 + 回测
- 周五：DeFi套利工具搭建
- 周六：整合Phase2所有策略，建立策略评分体系
- 周日：Phase2总结，选出最优3个策略进入实盘

### Phase 2 验收标准
- [ ] 5+个策略通过回测验证（Sharpe > 1.5）
- [ ] 链上数据管道稳定运行
- [ ] 至少2个策略小额实盘验证
- [ ] 策略相关性分析（选择低相关性组合）

---

# PHASE 3：AI 赋能升级（Week 21-32）

目标：用AI显著提升策略表现，建立技术护城河

---

## Week 21-22：特征工程体系

### 学习目标
- 构建加密市场多维度特征库
- 理解特征重要性和有效性检验
- 建立特征存储和复用体系

### 特征分类

**技术面特征（100+个）**
```python
technical_features = {
    "trend": ["EMA_diff", "ADX", "MACD", "trend_strength"],
    "momentum": ["RSI", "MOM", "ROC", "STOCH"],
    "volatility": ["ATR", "BB_width", "realized_vol"],
    "volume": ["OBV", "VWAP_diff", "volume_ratio"],
    "pattern": ["candle_patterns", "support_resistance"],
}
```

**链上特征（50+个）**
```python
onchain_features = {
    "exchange_flow": ["大额充值", "大额提现", "净流入"],
    "whale_activity": ["鲸鱼累积", "鲸鱼分散", "聪明钱方向"],
    "network": ["活跃地址数", "交易数", "gas价格"],
    "defi": ["总锁仓量", "借贷率", "清算风险"],
    "funding": ["资金费率", "持仓量", "多空比"],
}
```

**情绪/舆论特征（30+个）**
```python
sentiment_features = {
    "fear_greed": "恐贪指数",
    "social_volume": "社交媒体提及量",
    "news_sentiment": "新闻情绪评分",
    "google_trends": "搜索趋势",
}
```

### 每日任务
- 周一-周二：技术面特征全量实现（pandas-ta + 自定义）
- 周三：链上特征入库，与K线对齐
- 周四：情绪数据API对接（Alternative.me Fear&Greed，CryptoQuant）
- 周五：特征有效性检验（IC分析，与未来收益的相关性）
- 周六：特征存储优化（列式存储，快速加载）
- 周日：特征重要性分析，筛选Top 50有效特征

---

## Week 23-24：XGBoost/LightGBM 信号模型

### 学习目标
- 建立可解释的ML信号分类模型
- 掌握时序CV（walk-forward）防过拟合
- 实现模型信号到仓位的转换

### 模型框架

```python
# 任务定义：预测未来N小时价格方向
# 标签：未来4h/12h/24h 涨跌幅 > X%（3分类：涨/平/跌）

# 训练策略：Walk-Forward CV
# 训练窗口：过去6个月
# 验证窗口：下1个月（滚动）

# 核心模型
model = LightGBM(
    objective="multiclass",
    num_class=3,
    features=top_50_features,
    time_series_cv=WalkForwardCV(n_splits=12),
)

# 信号转仓位
# P(涨) > 0.6 → 做多，仓位正比于概率
# P(跌) > 0.6 → 做空，仓位正比于概率
# 否则 → 持仓不动
```

### 每日任务
- 周一：数据集构建（特征对齐，标签生成，时序分割）
- 周二：LightGBM基础模型训练和评估
- 周三：超参数优化（Optuna贝叶斯搜索）
- 周四：SHAP特征解释，理解模型决策
- 周五：信号转仓位逻辑，与趋势策略结合
- 周六：Walk-Forward全量验证（2021-2025）
- 周日：模型性能分析，与纯规则策略对比

### 验收标准
- [ ] 模型IC（信息系数）> 0.05（月均）
- [ ] Walk-forward Sharpe > 1.5
- [ ] 显著优于Buy-and-Hold基准

---

## Week 25-26：深度学习（LSTM / Transformer）

### 学习目标
- 理解时序深度学习在量化中的真实价值（和局限）
- 实现 LSTM 和 Temporal Fusion Transformer
- 和ML模型结合，不要孤立使用

### 模型架构

```python
# LSTM价格预测模型
class CryptoPriceLSTM(nn.Module):
    """
    输入：过去N个时间步的多维特征
    输出：未来M步的价格变化分布
    """
    layers = [LSTM(hidden=256), Dropout(0.3), Linear(3)]  # 3分类

# Temporal Fusion Transformer（更强）
class CryptoTFT(nn.Module):
    """
    优点：内建注意力机制，可解释，处理多变量时序
    适合：融合技术面 + 链上 + 情绪多类型特征
    """
```

### 每日任务
- 周一：PyTorch时序数据集封装（CryptoDataset）
- 周二：LSTM模型实现和训练
- 周三：Transformer/TFT实现（用 pytorch-forecasting 库）
- 周四：模型集成（DL + ML 加权融合）
- 周五：推理速度优化（生产需要低延迟）
- 周六：深度实验：DL在不同市场状态下的表现
- 周日：确定最优模型组合，准备集成

---

## Week 27-28：强化学习交易代理

### 学习目标
- 用RL学习最优交易决策（仓位管理）
- 理解RL在量化交易中的实际应用场景
- 实现基于PPO的仓位管理代理

### 应用场景
```
RL不擅长：预测价格方向（噪声太大，奖励稀疏）
RL擅长：给定信号后，如何动态调整仓位
  → 应该开多少仓？
  → 什么时候加仓？减仓？
  → 如何在回撤中动态止损？
```

### 框架

```python
# 环境设计
class CryptoTradingEnv(gym.Env):
    state = [ML_signal, current_position, recent_pnl, volatility, ...]
    action = [-1, -0.5, 0, 0.5, 1]  # 仓位比例
    reward = risk_adjusted_pnl  # Sharpe-aware reward

# 算法：PPO（稳定，适合连续动作空间）
agent = PPO("MlpPolicy", env, learning_rate=3e-4)
```

### 每日任务
- 周一-周二：RL交易环境实现（gym接口）
- 周三：PPO代理训练（稳定版）
- 周四：奖励函数设计（Sortino / Calmar 导向）
- 周五：RL代理与ML信号结合的完整系统
- 周六：对比：RL仓位 vs 固定仓位，Sharpe提升？
- 周日：RL代理迁移到更多品种

---

## Week 29-30：NLP情绪分析

### 学习目标
- 建立实时加密市场情绪监控系统
- 利用LLM快速分析大量文本
- 情绪信号与价格信号结合

### 数据源和处理

```python
sentiment_sources = {
    "twitter/x": "KOL推文情绪（关键意见领袖）",
    "telegram": "主流币Telegram群聊情绪",
    "reddit": "r/cryptocurrency, r/bitcoin",
    "news": "CoinDesk/CoinTelegraph新闻",
    "on_chain_labels": "链上地址标签事件",
}

# 分析方法
methods = [
    "规则based：关键词打分（快，低成本）",
    "FinBERT：金融领域BERT（中等成本）",
    "GPT-4 API：复杂分析（高成本，按需用）",
]
```

### 高价值信号
- 大型KOL首次提及某个项目（往往是早期信号）
- 交易所异常公告（提币暂停 = 危险）
- 监管新闻实时解读（重大政策对价格冲击）
- 项目方异常链上行为配合舆情

---

## Week 31-32：模型集成 + 动态仓位

### 学习目标
- 整合所有信号源，建立统一决策框架
- 动态仓位管理（Kelly准则 + 风险调节）
- 全系统压力测试

### 集成框架

```python
class AISignalAggregator:
    """整合所有信号的主控模块"""
    
    def generate_signal(self, symbol, timestamp):
        signals = {
            "ml_lgbm": self.lgbm_model.predict(features),      # 0.3权重
            "dl_tft": self.tft_model.predict(features),         # 0.2权重
            "rl_position": self.rl_agent.act(state),            # 0.2权重
            "sentiment": self.sentiment_scorer.score(symbol),   # 0.15权重
            "onchain_whale": self.whale_tracker.signal(symbol), # 0.15权重
        }
        return self.ensemble(signals)  # 加权+投票结合
    
    def calculate_position_size(self, signal, volatility):
        # Kelly准则 + 最大仓位限制
        kelly_fraction = self.kelly(signal.confidence, signal.odds)
        vol_adjusted = kelly_fraction / (volatility / target_vol)
        return min(vol_adjusted, max_position_pct)
```

### Phase 3 验收标准
- [ ] AI信号系统接入实盘
- [ ] 全量集成测试通过（6个月Walk-Forward）
- [ ] 综合Sharpe > 2.0
- [ ] 月度最大回撤 < 15%

---

# PHASE 4：生产级系统（Week 33-40）

目标：将策略升级为稳定可靠的生产系统，实现完全自动化

---

## Week 33-34：生产架构

### 系统架构
```
                    ┌─────────────────┐
                    │   数据采集层     │
                    │ WebSocket×5交易所│
                    └────────┬────────┘
                             │实时数据
                    ┌────────▼────────┐
                    │   数据处理层     │
                    │ Redis缓存+特征计算│
                    └────────┬────────┘
                             │特征向量
                    ┌────────▼────────┐
                    │   AI决策层       │
                    │ 信号聚合+仓位计算 │
                    └────────┬────────┘
                             │交易指令
                    ┌────────▼────────┐
                    │   执行层         │
                    │ 智能路由+最优执行 │
                    └────────┬────────┘
                             │
               ┌─────────────┼─────────────┐
               ▼             ▼             ▼
          Binance API    OKX API    Hyperliquid SDK
```

### 每日任务
- 周一-周二：微服务拆分（数据服务 / 信号服务 / 执行服务）
- 周三：消息队列（Redis Streams / Kafka）
- 周四：故障恢复机制（断线重连/状态恢复）
- 周五：部署脚本（Docker Compose）
- 周六-周日：全系统集成测试

---

## Week 35-36：多策略组合管理

### 策略组合框架

```python
strategies_portfolio = {
    "funding_rate_arb": {
        "allocation": 0.20,   # 20%资金，稳定基础收益
        "type": "market_neutral",
    },
    "trend_following": {
        "allocation": 0.25,   # BTC/ETH趋势
        "type": "directional",
    },
    "whale_copycat": {
        "allocation": 0.20,   # 链上鲸鱼跟单
        "type": "event_driven",
    },
    "ai_ml_signals": {
        "allocation": 0.25,   # AI综合信号
        "type": "directional",
    },
    "defi_arb": {
        "allocation": 0.10,   # DeFi套利
        "type": "arb",
    },
}
# 动态再平衡：每日根据各策略近期表现调整allocation
```

---

## Week 37-38：监控告警系统

### 监控面板（Grafana）
```
实时监控指标：
├── 账户总资产（USD）
├── 各策略P&L（实时 + 历史）
├── 当前持仓（多空方向 + 规模）
├── 系统状态（数据延迟 / 服务心跳）
├── 风险指标（VaR / 最大回撤 / 杠杆率）
└── 执行质量（滑点 / 成交率 / 延迟）
```

### Telegram 告警规则
```python
alerts = {
    "CRITICAL": [
        "任何策略单日亏损 > 5%",
        "账户总回撤 > 10%",
        "服务宕机 > 5分钟",
        "API连接失败",
    ],
    "WARNING": [
        "账户余额 < 最小保证金",
        "数据延迟 > 30秒",
        "异常大额未实现亏损",
    ],
    "INFO": [
        "每日9:00 绩效日报",
        "策略开仓/平仓通知",
        "周报（周一早9:00）",
    ],
}
```

---

## Week 39-40：性能优化 + 容量扩展

### 重点优化
- 信号计算延迟（目标：<100ms）
- 数据库查询优化（分区索引，物化视图）
- 执行质量改善（TWAP/VWAP大单拆分）
- 多账户支持（不同资金规模隔离）

### Phase 4 验收标准
- [ ] 全自动运行30天无人工干预
- [ ] 月度最大回撤 < 15%
- [ ] 月收益稳定，覆盖生活成本
- [ ] 系统稳定性 > 99.5%（月度）

---

# PHASE 5：规模化盈利（Week 41-52）

目标：持续迭代优化，扩大资金规模，实现可持续的财务自由

---

## Week 41-44：策略持续迭代

### 迭代方法论

```
每月固定Review：
1. 各策略绩效归因（为什么赚/亏？）
2. 失效策略分析（是市场状态变了，还是逻辑有问题？）
3. 新机会探索（市场热点/新上市代币/新DeFi协议）
4. 模型再训练（加入最新数据，防止模型衰退）

每季度大优化：
1. 全量Walk-Forward重新评估所有策略
2. 资金分配再平衡（淘汰表现差的，增加好的）
3. 探索新策略类型
```

### 新策略探索方向
- **Solana生态**：Pump.fun早期发现，Jito MEV
- **Layer2 DeFi**：Arbitrum/Base新协议机会
- **RWA（真实资产代币化）**：新兴叙事的先机
- **AI Agent加密应用**：Virtuals Protocol生态
- **跨链套利**：桥接价差，不同链的同资产价差

---

## Week 45-48：规模扩大策略

### 资金规模扩大的原则

```
规模扩大规则（保守策略）：
- 前提：策略连续3个月盈利，且最大回撤 < 20%
- 扩大幅度：每月最多增加50%的资金
- 流动性检查：成交量必须支撑更大规模（不超过日均量的1%）
- 策略容量评估：不同策略有不同的资金上限
  - 资金费率套利：无上限（但高费率机会减少）
  - 趋势跟踪主流币：$500K内无问题
  - 山寨币策略：需要严格控制（流动性限制）
  - 链上鲸鱼跟单：$200K内（跟太多会影响市场）
```

---

## Week 49-52：多链布局 + 新 Alpha 探索

### 多链扩张

```
第12个月目标：
├── ETH主网：DeFi套利 + 鲸鱼追踪
├── Solana：MEV + 新项目早期发现
├── Base/Arbitrum：Layer2 DeFi机会
├── Hyperliquid：永续合约主战场
└── 新兴链：探索小仓位，寻找早期机会（<5%总资金）
```

### 财务自由验收

**硬指标**
- [ ] 月净收益（扣除生活成本后）持续为正
- [ ] 月生活成本完全由交易收益覆盖
- [ ] 资金规模持续增长（年化复利 > 60%）
- [ ] 系统稳定，无需全职监控（每天<2小时维护）

**软指标**
- 有清晰的策略迭代框架
- 建立了可持续的alpha发现能力
- 对自己的盈利来源有深刻理解（不是运气）

---

# 每日执行模板

```
工作日 20:00-23:00（3小时）
20:00-20:15  查看实盘P&L和告警
20:15-21:30  主学习/开发任务（按当周计划）
21:30-22:00  整理代码和笔记
22:00-23:00  实战编码或研究

周六 09:00-19:00（8小时有效）
09:00-12:00  深度开发（最难的任务放这里）
12:00-14:00  午休
14:00-19:00  实战 + 实验 + 测试

周日 10:00-17:00（5小时）
10:00-12:00  阅读：论文/Substack/链上分析报告
14:00-16:00  本周总结 + 下周计划
16:00-17:00  复盘实盘，调整策略参数
```

---

# 学习资源

## 必读书籍
- 《Advances in Financial Machine Learning》Marcos Lopez de Prado（量化ML圣经）
- 《Algorithmic Trading》Ernest Chan（实战导向）
- 《Flash Boys》Michael Lewis（理解市场微观结构）

## 重要论文（加密量化）
- "Cryptocurrency Trading: A Comprehensive Survey" (2021)
- "Do Cryptocurrency Prices Respond to Economic and Financial Shock?" 
- "On-Chain Analysis as a Predictive Tool for Cryptocurrency Returns"

## 必关注资源
- **Substack**: Delphi Digital, Messari Research, Nansen Insights
- **Twitter**: 关注顶级链上分析师（@lookonchain, @spotonchain）
- **Dune Analytics**: 浏览热门链上分析仪表板
- **CryptoQuant**: 交易所链上数据
- **Glassnode**: 链上指标（部分免费）

## 技术资源
- ccxt 官方文档 + GitHub
- Hyperliquid 官方文档
- web3.py 文档
- vectorbt 文档和示例
