# Week 01-02：Python 数据科学栈

## 每日学习计划

| 天 | 主题 | 文件 | 核心任务 |
|----|------|------|---------|
| 周一 | NumPy 核心 | `numpy_basics.py` | 向量化运算、广播机制 |
| 周二 | Pandas 核心 | `pandas_basics.py` | 时间索引、rolling、groupby |
| 周三 | 可视化 | `visualization.py` | K线图、双轴图、热力图 |
| 周四 | SciPy 统计 | `scipy_stats.py` | 分布检验、相关性、OLS |
| 周五 | 综合项目 | `project_stock_analysis.py` | 完整股票分析报告 |
| 周末 | 环境搭建 + 数据源 | `data_fetcher.py` | 本地数据库构建 |

## 环境配置

```bash
# 推荐使用 conda 虚拟环境
conda create -n quant python=3.11
conda activate quant
pip install -r ../../requirements.txt

# 配置 Tushare token
cp .env.example .env
# 编辑 .env 填入你的 token
```

## 学习资源

- **书**：《利用Python进行数据分析》第3版（Pandas作者写的）
- **文档**：[Pandas 10分钟入门](https://pandas.pydata.org/docs/user_guide/10min.html)
- **数据**：[Tushare Pro](https://tushare.pro) | [AkShare](https://akshare.akfan.com)
