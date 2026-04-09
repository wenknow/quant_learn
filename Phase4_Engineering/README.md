# Phase 4：工程化 + 实盘

**时间**：第27-36周（约2.5个月）
**目标**：将研究成果转化为可运行的实盘系统

---

## 学习模块

| 模块 | 时间 | 核心内容 |
|------|------|---------|
| [week27_30_trading_system](./week27_30_trading_system/) | 第27-30周 | 事件驱动架构、vnpy框架、券商API |
| [week31_33_live_trading](./week31_33_live_trading/) | 第31-33周 | 模拟盘演练、日报系统、监控告警 |
| [week34_36_performance](./week34_36_performance/) | 第34-36周 | 向量化优化、ClickHouse、低延迟 |

## 系统架构

```
数据层（ClickHouse） → 策略层（信号生成） → 执行层（vnpy OMS） → 监控层（飞书告警）
```

## 第36周验收标准

- [ ] 完整交易系统跑通模拟盘1个月
- [ ] 日报自动生成（PnL + 归因分析）
- [ ] 异常告警系统（回撤超阈值→飞书通知）
- [ ] 能讲清楚真实交易成本的构成

## vnpy 快速开始

```bash
pip install vnpy
pip install vnpy_ctp         # 期货实盘接口
pip install vnpy_tora        # 华泰证券接口

# 启动vnpy
python -m vnpy_scripttrader
```

## 每日实盘日历

```
08:00  检查隔夜持仓
09:00  运行信号生成
09:25  分析集合竞价
09:30  监控开盘行情
14:57  收盘前确认
15:00  日终结算
15:30  生成日报
```
