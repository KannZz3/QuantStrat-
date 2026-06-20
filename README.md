# QuantStrat 量化金融研究项目复现与拓展平台 (UIUC MSFE 2026)

本项目是 **QuantStrat** 与**伊利诺伊大学金融工程硕士项目（UIUC MSFE）** 2026年夏季的量化金融研究合作项目。项目采用学术规范与科学研究范式，以文献理论为锚，针对加密货币与中国商品期货主力合约，构建了一套包含**基本面锚定、行为金融异象、高阶异方差频域检验以及动态风险管理**的量化研究与执行参考系统。

目前项目已基本完成三大核心研究模块的开发与实证分析，并规划了未来深入研究的三个学术方向。

---

## 一、 已完成核心模块全景与成果

### 1. Crypto_Pricing —— 加密货币统一多维定价与下沿估值
*   **主要目的**：针对无贴现现金流特性的加密资产（BTC），探索其链上基本面的公允价值与市场行为折价的动态变化，提供下沿估值区间的量化参考。
*   **核心逻辑**：级联融合三篇学术论文：
    1.  **BDK 链上基本面价值锚 (Bhambhwani et al., 2019)**：以算力与活跃地址数作为自变量，计算算力下行与用户规模萎缩情景下的底层安全价值。
    2.  **Biais 均衡交易折价层 (Biais et al., 2023)**：加权评估交易收益（40%）、交易成本（20%）、市场准入（20%）与崩盘风险（20%），映射折价系数。
    3.  **Liu-Tsyvinski 风险注意力折价层 (Liu & Tsyvinski, 2021)**：结合价格动量（40%）、普通关注度（25%）、负面关注度（20%）与活跃度增长率（15%），评估投机热度共识。
*   **主要成果与设计亮点**：
    *   构建了基于 Python 的学术级数据交叉验证系统 (`validator.py`)，包含 lead/lag 延迟相关性检验（Spearman Correlation）以及注意力指标的双源检验。
    *   设计了动态模型降级（Full Model $\rightarrow$ Core $\rightarrow$ BDK Only）与样本天数不足惩罚机制，使估值区间（Price Range）的宽度能较好地反映数据置信度。
    *   网络规模变量（Active Addresses）仅在基本面价值锚中使用，在行为折价模块中被禁止二次计算，以防范潜在的共线性偏误。

### 2. Market_Anomalies —— 商品期货技术分析异象、活跃度衰减与选择后衰减
*   **主要目的**：检验“高波动资产中技术异象更强”的横截面收益假说，测试高交易活跃度状态是否会削弱该异象，以及量化策略在“样本内筛选-发表/选择后”的样本外（OOS）与伪实盘（Pseudo-Live）阶段的衰减效应。
*   **实证成果（基于 27 个主力商品期货日频 CSV 运行结果）**：
    *   **高波动技术异象局部且不显著**（Han et al. 2013复刻）：在 `High-minus-Low` 波动率桶的测试中，8个技术指标中有5个年化超额收益为正（如 MA20 年化 5.27%），但在 5% 显著性水平下 t 统计量全线不显著（最高为 0.96）。长周期指标（如 MA120）在所选样本中表现出反转（年化 -10.23%，t = -1.77）。
    *   **活跃度对异象呈现方向性弱衰减**（Chordia et al. 2014复刻）：以成交量、持仓量、 turnover 合成的交易活跃度 z-score 显示，24 个测试中 18 个表现出衰减方向（如 MA120 HML 收益在低活跃度下为 1.20%，高活跃度下为 -16.44%，相差 -22.24%），但统计显著性较弱（t = -1.47）。
    *   **选择后衰减是表现较强且一致的数据结果**（McLean & Pontiff 2016复刻）：在 IS 阶段（2016-2020）筛选出的 Top 10 策略，在 OOS（2021-2023）与 Pseudo-Live（2024-2026）阶段发生较明显的收益下滑：
        
        | 阶段 (Split) | 平均年化收益率 | 平均夏普比率 | 夏普保留率 (Sharpe Retention) | 衰减特征 |
        | :--- | :---: | :---: | :---: | :--- |
        | **IS (样本内)** | 5.96% | 0.68 | 100.0% | 基准筛选 |
        | **OOS (样本外)** | 3.72% | 0.35 | 55.5% | 收益中位保留率约 66.6% |
        | **PSEUDO_LIVE (伪实盘)**| 1.06% | 0.11 | 16.6% | 大幅塌陷，部分策略转负 |

### 3. Volatility_Time_Series —— 波动率建模与 Hong-Lee 谱充分性检验
*   **主要目的**：引入频域谱分析，评估经过传统诊断（Ljung-Box, ARCH-LM）合格后的最优 GARCH 波动率模型，探索残差中可能遗留的高阶矩依赖与非线性异方差结构，并将其转化为动态风控参考。
*   **实证成果（基于 20 个主力商品期货日频 CSV 运行结果）**：
    *   **EGARCH-t 模型占多数**：20 个被测合约中，有 15 个被 BIC 筛选为非对称 EGARCH 族。所有被测品种的最优模型均采用非正态厚尾假定（Student-t/GED），提示商品收益率具有厚尾分布特征。
    *   **谱检验提示传统方法盲区**（Hong & Lee 2017复刻）：最优模型在标准化残差的传统诊断中均通过了自相关检验（p > 0.05）。但在数据驱动最佳带宽检验下，**AU (沪金)**（p = 0.0455）、**I (铁矿石)**（p = 0.0061）、**P (棕榈油)**（p = 0.0324）三品种的充分性原假设在 5% 水平下被拒绝。
    *   **风险控制与仓位参考调节**：
        *   **动态风险预算（Volatility Targeting）**：根据条件波动率调整风险敞口。如在 2026年6月18日，由于银价大幅波动，**AG（沪银）** 条件波动率处于历史 95.86% 分位数，对应的仓位缩放参考系数收缩至 **0.417**；而正常波动率下的 **AL（沪铝）** 仓位参考系数为 **1.091**。
        *   **健康度修正参考**：对于被谱检验拒绝（AU, I, P）或第四矩发散的品种（AG, CF），引入降权乘数（健康乘数）进行应对，防范潜在的尾部风险低估。

---

## 二、 规划中研究模块与后续方向

本项目后续将进一步探索以下三个量化金融经典课题，并逐步完成相关学术文献的复现与拓展检验：

### 1. 动量 / 反转 / 趋势跟踪 (Momentum, Reversal, and Trend-Following)
*   **研究主题**：价格延续、均值反转、趋势规则构建、波动率自适应调整以及两状态机制切换（Regime-Switching）。
*   **核心文献**：
    *   *Ammann, Moellenbeck, and Schmid (2011)* — Feasible Momentum Strategies in the US Stock Market
    *   *Baltas and Kosowski (2012)* — Improving Time-Series Momentum Strategies: The Role of Trading Signals and Volatility Estimators
    *   *Caporale and Plastun (2020)* — Momentum Effects in the Cryptocurrency Market After One-Day Abnormal Returns
    *   *Dobrynskaya (2021)* — Cryptocurrency Momentum and Reversal
    *   *Dudler, Gmuer, and Malamud (2014)* — Risk Adjusted Time Series Momentum
    *   *Karassavidis, Kateris, and Ioannidis (2025)* — Quantitative Evaluation of Volatility-Adaptive Trend-Following Models in Cryptocurrency Markets
    *   *Li et al. (2021)* — MAX Momentum in Cryptocurrency Markets
    *   *Tayal (2009)* — Regime Switching and Technical Trading with Dynamic Bayesian Networks in High-Frequency Stock Markets
    *   *Zakamulin and Giner (2022)* — Optimal Trend Following Rules in Two-State Regime-Switching Models

### 2. 机器学习 / AI / 预测模型 (Machine Learning, AI, and Forecasting Models)
*   **研究主题**：高维资产预测、可解释人工智能（XAI）在资产配置中的应用、深度强化学习交易系统以及多模型（如决策树、神经网络等）非线性预测比较。
*   **核心文献**：
    *   *Afolabi et al. (2017)* — Hierarchical Meta-Learning in Time Series Forecasting for Improved Interference-Less Machine Learning
    *   *Babaei, Giudici, and Raffinetti (2022)* — Explainable Artificial Intelligence for Crypto Asset Allocation
    *   *Campisi, Muzzioli, and De Baets (2024)* — A Comparison of Machine Learning Methods for Predicting the Direction of the US Stock Market on the Basis of Volatility Indices
    *   *Chandak et al. (2019)* — Learning Action Representations for Reinforcement Learning
    *   *Gu, Kelly, and Xiu (2020)* — Empirical Asset Pricing via Machine Learning
    *   *Shen, Jiang, and Zhang (2012)* — Stock Market Forecasting Using Machine Learning Algorithms
    *   *Tran, Pham-Hi, and Bui (2023)* — Optimizing Automated Trading Systems with Deep Reinforcement Learning

### 3. 市场微观结构 / 高频交易 / 算法交易 (Market Microstructure and High-Frequency Trading)
*   **研究主题**：高频数据下的波动率反馈效应、微观订单流动态执行、Pro Rata 匹配机制下的算法交易优化以及交易成本最小化控制。
*   **核心文献**：
    *   *Bollerslev, Litvinova, and Tauchen (2006)* — Leverage and Volatility Feedback Effects in High-Frequency Data
    *   *Funie, Salmon, and Luk (2014)* — A Hybrid Genetic-Programming Swarm-Optimisation Approach for Examining the Nature and Stability of High Frequency Trading Strategies
    *   *Guilbaud and Pham (2015)* — Optimal High-Frequency Trading in a Pro Rata Microstructure with Predictive Information
    *   *Kearns and Nevmyvaka (2013)* — Machine Learning for Market Microstructure and High Frequency Trading
    *   *Labadie, Lehalle, et al. (2010)* — Optimal Algorithmic Trading and Market Microstructure
    *   *Lehalle (2013)* — Market Microstructure Knowledge Needed for Controlling an Intra-Day Trading Process

---

## 三、 量化研究规范与工程设计亮点

1.  **时序逻辑一致（防范 Look-ahead Bias）**：
    所有策略回测均执行延迟交易原则。信号在 `t-1` 收盘后形成，仓位在 `t` 日执行，收益窗口为 `close[t] -> close[t+1]`。样本切分使用完整 Return Window 以防范跨区间收益渗透。
2.  **统计工具的稳健性**：
    *   横截面回归采用 OLS 结合 **HC1 异方差稳健标准误** 评估显著性。
    *   蒙特卡洛有限样本 Size 校验采用 **Wilson Score 置信区间** 代替 Wald 渐进区间，防范边界概率出现退化。
3.  **高性能数据管道**：
    数据流主要采用 Parquet 格式进行处理，数据源涵盖 CoinGecko, Binance, Yahoo Finance, Farside, GDELT 等十余个接口，支持离线数据资产在 Git 上的完全可复现性。

---

## 四、 目录结构说明

```text
QuantStrat/
├── README.md                                          # 根目录说明文档（本文件）
├── QuantStrat x UIUC MSFE.pdf                         # UIUC MSFE 夏季项目合作及 bibliography 课件
├── Commodity_Futures_Raw_Data/                        # 商品期货原始价格与特征面板数据 (27个品种)
│   ├── AG.csv, AL.csv, ...
│   └── futures_panel.csv                              # 商品期货横截面主面板
├── Crypto_Pricing—— 加密货币定价/                     # 模块一：BTC多维定价与下沿估值模块
│   ├── btc_unified_pricing_model/                     # Python 核心模型包 (fetchers, validator, pricing)
│   ├── tests/                                         # 单元测试模块
│   └── README.md                                      # 模块一详细设计文档
├── Market_Anomalies——市场异象/                        # 模块二：技术异象、活跃度衰减与发表后衰减模块
│   ├── 02_vol_sorted_technical_anomaly.ipynb          # 波动率排序横截面技术分析异象回测
│   ├── 03_liquidity_attenuation.ipynb                 # 交易活跃度对技术异象的削弱检验
│   ├── 04_post_selection_decay.ipynb                  # 策略选择后的样本外与伪实盘衰减测试
│   ├── *.csv                                          # 策略与回归的运行结果表 (02_至04_系列)
│   └── README.md                                      # 模块二详细设计与CSV发现文档
└── Volatility_Time_Series——波动率&时间序列检验/       # 模块三：波动率建模与 Hong-Lee 谱检验风控模块
    ├── Traditional_Model_Selection_Sugar.ipynb        # 单合约复刻论文及全流程检验 (白糖主力)
    ├── hong_lee_20_contracts.ipynb                    # 多合约拓展运行脚本 (20个商品期货主力)
    ├── *.csv                                          # 20合约波动率建模与健康谱检验表 (01_至16_系列)
    └── README.md                                      # 模块三详细设计、CSV发现与风控逻辑文档
```
