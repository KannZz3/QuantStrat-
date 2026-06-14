# Summer 2026 Financial Engineering Research Projects

## 论文分类与项目实现框架 / Paper Classification and Implementation Framework

## 1. 项目定位 / Project Positioning

本项目是一个量化金融论文复现项目，目标是通过复现候选论文，训练完整的量化研究流程：文献理解、数据处理、模型实现、结果复现、稳健性检验和研究报告输出。

This is a quantitative finance research replication project. Its goal is to train the full research workflow: literature review, data processing, model implementation, result replication, robustness testing, and research reporting.

## 2. 分类逻辑 / Classification Logic

本文按照论文的核心研究问题进行分类，而不是单纯按照资产类别划分。

Papers are classified by their core research questions rather than by asset class alone.

## 3. 论文分类 / Paper Classification

### 3.1 动量 / 反转 / 趋势跟踪

### Momentum / Reversal / Trend-Following

核心主题：价格延续、反转、趋势规则、波动率调整、状态切换。
Core focus: price continuation, reversal, trend rules, volatility adjustment, and regime switching.

1. Ammann, Moellenbeck, and Schmid (2011) — Feasible Momentum Strategies in the US Stock Market
2. Baltas and Kosowski (2012) — Improving Time-Series Momentum Strategies: The Role of Trading Signals and Volatility Estimators
3. Caporale and Plastun (2020) — Momentum Effects in the Cryptocurrency Market After One-Day Abnormal Returns
4. Dobrynskaya (2021) — Cryptocurrency Momentum and Reversal
5. Dudler, Gmuer, and Malamud (2014) — Risk Adjusted Time Series Momentum
6. Karassavidis, Kateris, and Ioannidis (2025) — Quantitative Evaluation of Volatility-Adaptive Trend-Following Models in Cryptocurrency Markets
7. Li et al. (2021) — MAX Momentum in Cryptocurrency Markets
8. Tayal (2009) — Regime Switching and Technical Trading with Dynamic Bayesian Networks in High-Frequency Stock Markets
9. Zakamulin and Giner (2022) — Optimal Trend Following Rules in Two-State Regime-Switching Models

### 3.2 机器学习 / AI / 预测模型

### Machine Learning / AI / Forecasting Models

核心主题：机器学习预测、资产配置、强化学习、模型比较。
Core focus: machine learning prediction, asset allocation, reinforcement learning, and model comparison.

1. Afolabi et al. (2017) — Hierarchical Meta-Learning in Time Series Forecasting for Improved Interference-Less Machine Learning
2. Babaei, Giudici, and Raffinetti (2022) — Explainable Artificial Intelligence for Crypto Asset Allocation
3. Campisi, Muzzioli, and De Baets (2024) — A Comparison of Machine Learning Methods for Predicting the Direction of the US Stock Market on the Basis of Volatility Indices
4. Chandak et al. (2019) — Learning Action Representations for Reinforcement Learning
5. Gu, Kelly, and Xiu (2020) — Empirical Asset Pricing via Machine Learning
6. Shen, Jiang, and Zhang (2012) — Stock Market Forecasting Using Machine Learning Algorithms
7. Tran, Pham-Hi, and Bui (2023) — Optimizing Automated Trading Systems with Deep Reinforcement Learning

### 3.3 加密货币定价 / 基本面 / 风险收益

### Cryptocurrency Pricing / Fundamentals / Risk and Return

核心主题：加密货币基本面、均衡定价、风险收益特征。
Core focus: cryptocurrency fundamentals, equilibrium pricing, and risk-return characteristics.

1. Bhambhwani, Delikouras, and Korniotis (2019) — Do Fundamentals Drive Cryptocurrency Prices?
2. Biais et al. (2023) — Equilibrium Bitcoin Pricing
3. Liu and Tsyvinski (2021) — Risks and Returns of Cryptocurrency

### 3.4 市场微观结构 / 高频交易 / 算法交易

### Market Microstructure / High-Frequency Trading / Algorithmic Trading

核心主题：高频数据、市场机制、订单执行、算法交易。
Core focus: high-frequency data, market mechanisms, order execution, and algorithmic trading.

1. Bollerslev, Litvinova, and Tauchen (2006) — Leverage and Volatility Feedback Effects in High-Frequency Data
2. Funie, Salmon, and Luk (2014) — A Hybrid Genetic-Programming Swarm-Optimisation Approach for Examining the Nature and Stability of High Frequency Trading Strategies
3. Guilbaud and Pham (2015) — Optimal High-Frequency Trading in a Pro Rata Microstructure with Predictive Information
4. Kearns and Nevmyvaka (2013) — Machine Learning for Market Microstructure and High Frequency Trading
5. Labadie, Lehalle, et al. (2010) — Optimal Algorithmic Trading and Market Microstructure
6. Lehalle (2013) — Market Microstructure Knowledge Needed for Controlling an Intra-Day Trading Process

### 3.5 市场异象 / Alpha 衰减 / 技术分析有效性

### Market Anomalies / Alpha Decay / Technical Analysis

核心主题：市场异象、技术分析收益、公开研究后的 alpha 衰减。
Core focus: market anomalies, technical-analysis profitability, and alpha decay after publication.

1. Chordia, Subrahmanyam, and Tong (2014) — Have Capital Market Anomalies Attenuated in the Recent Era of High Liquidity and Trading Activity?
2. Han, Yang, and Zhou (2013) — A New Anomaly: The Cross-Sectional Profitability of Technical Analysis
3. McLean and Pontiff (2016) — Does Academic Research Destroy Stock Return Predictability?

### 3.6 波动率模型 / 时间序列检验

### Volatility Modeling / Time-Series Model Testing

核心主题：波动率模型设定、统计检验、时间序列模型验证。
Core focus: volatility model specification, statistical testing, and time-series model validation.

1. Hong and Lee (2017) — A General Approach to Testing Volatility Models in Time Series

## 4. 分类汇总 / Classification Summary

| Category                                             | Count | Main Use                  |
| ---------------------------------------------------- | ----: | ------------------------- |
| 动量 / 反转 / 趋势跟踪 Momentum / Reversal / Trend-Following |     9 | 策略复现 Strategy replication |
| 机器学习 / AI / 预测模型 ML / AI / Forecasting               |     7 | 模型构建 Model building       |
| 加密货币定价 / 风险收益 Crypto Pricing / Risk and Return       |     3 | 资产定价 Asset pricing        |
| 市场微观结构 / 高频交易 Market Microstructure / HFT            |     6 | 高频与执行 HFT and execution   |
| 市场异象 / Alpha 衰减 Market Anomalies / Alpha Decay       |     3 | 信号衰减 Signal decay         |
| 波动率模型 / 时间序列检验 Volatility / Time-Series Testing      |     1 | 模型检验 Model testing        |

Total: 29 papers.

## 5. 项目实现流程 / Implementation Workflow

### Step 1: 选择论文 / Select Paper

根据数据可得性、方法难度、复现可行性和扩展空间选择论文。
Select a paper based on data availability, methodological difficulty, replication feasibility, and extension potential.

### Step 2: 拆解论文 / Decompose Paper

明确研究问题、样本区间、数据频率、变量定义、模型方法、组合构建和核心结论。
Identify the research question, sample period, data frequency, variable definitions, methodology, portfolio construction, and main conclusions.

### Step 3: 构建数据管道 / Build Data Pipeline

完成数据获取、清洗、缺失值处理、收益计算、特征构建和版本管理。
Build the data pipeline: acquisition, cleaning, missing-value handling, return calculation, feature construction, and version control.

### Step 4: 复现核心方法 / Replicate Core Method

复现论文中的信号、模型、组合、回测或统计检验。
Replicate the paper’s signals, models, portfolios, backtests, or statistical tests.

### Step 5: 结果对比 / Compare Results

将复现结果与原论文结果比较，并解释差异来源。
Compare replicated results with the original paper and explain sources of differences.

### Step 6: 稳健性检验 / Robustness Tests

检验不同样本、参数、交易成本、资产池和市场阶段下的结果稳定性。
Test robustness across samples, parameters, transaction costs, asset universes, and market regimes.

### Step 7: 扩展研究 / Research Extension

可加入新样本、新资产、不同信号、波动率调整、状态切换或 alpha 衰减检验。
Extend the research with new samples, new assets, alternative signals, volatility adjustment, regime filters, or alpha decay tests.

### Step 8: 最终输出 / Final Output

形成 README、代码、数据说明、图表、复现结果、稳健性检验和研究报告。
Deliver a README, codebase, data documentation, figures, replication results, robustness tests, and final research report.

## 6. 推荐目录结构 / Suggested Repository Structure

```text
project-root/
├── README.md
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
│   ├── 01_data_cleaning.ipynb
│   ├── 02_replication.ipynb
│   └── 03_robustness.ipynb
├── src/
│   ├── data_loader.py
│   ├── signals.py
│   ├── models.py
│   ├── backtest.py
│   └── metrics.py
├── results/
│   ├── figures/
│   └── tables/
├── reports/
│   └── final_report.qmd
└── requirements.txt
```

## 7. 关键研究控制 / Key Research Controls

1. 未来函数 / Look-ahead Bias
   Only use information available at the decision time.

2. 幸存者偏差 / Survivorship Bias
   Avoid using only surviving assets.

3. 过拟合 / Overfitting
   Control excessive parameter tuning and model complexity.

4. 交易成本 / Transaction Costs
   Evaluate whether results survive realistic costs.

5. 数据挖掘 / Data Snooping
   Avoid reporting only the best-performing specification.

6. 样本外检验 / Out-of-Sample Testing
   Validate whether results hold outside the original sample.

7. 可复现性 / Reproducibility
   Ensure code, data processing, parameters, and results can be reproduced.

## 8. 最终目标 / Final Objective

本项目最终目标是形成一个清晰、严谨、可复现的量化金融研究项目。

The final goal is to produce a clear, rigorous, and reproducible quantitative finance research project.

理想成果应回答五个问题：原论文研究什么、如何实现、是否能复现、结论是否稳健、可以如何扩展。

The final output should answer five questions: what the original paper studies, how it is implemented, whether the results can be replicated, whether the conclusions are robust, and how the research can be extended.
