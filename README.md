# QuantStrat 量化金融研究项目复现与拓展平台 (UIUC MSFE 2026)

本项目是 **QuantStrat** 与**伊利诺伊大学金融工程硕士项目（UIUC MSFE）** 2026年夏季的量化金融研究合作项目。项目主要针对**中国商品期货市场主力合约**，采用学术规范与研究方法，以文献为锚进行复现与拓展检验，构建了一套包含**商品期货行为金融异象、高阶异方差频域检验与动态风险管理**的量化研究参考系统。

目前项目已基本完成核心研究模块的开发与实证分析，并规划了未来深入研究的三个方向。

---

## 一、 已完成核心模块全景与成果

### 1. Market_Anomalies —— 商品期货技术分析异象、活跃度衰减与发表后衰减
*   **研究背景**：复刻与拓展 **Han et al. (2013)**（高波动技术分析横截面超额收益）、**Chordia et al. (2014)**（流动性/活跃度对资本市场异象的削弱）以及 **McLean & Pontiff (2016)**（学术发表及策略筛选后收益预测性衰减）的核心假说，测试中国商品期货市场中的技术异象稳定性。
*   **框架与流程**：
    *   每日按横截面收益波动率（RV60）分成 `Low / Mid / High` 波动率桶，构造 MA10 至 MA120 技术信号，计算 High-minus-Low（HML）等权策略收益。
    *   以成交量、持仓量、turnover 合成 rolling z-score 活跃度得分，评估 High-activity 状态下异象的衰减幅度。
    *   切分 IS（2016-2020）/ OOS（2021-2023）/ Pseudo-Live（2024-2026）样本区间，仅用 IS 收益率筛选出 Top 10 策略，比较跨阶段的表现变化。
*   **实证结论（基于 27 个主力商品期货日频 CSV 运行结果）**：
    *   **高波动技术异象局部且不显著**：在 HML 波动率桶测试中，8个技术指标中有5个年化超额收益为正（如 MA20 年化 5.27%），但在 5% 显著性水平下 t 统计量均不显著（最高为 0.96）。长周期指标（如 MA120）表现出反转（年化 -10.23%，t = -1.77）。
    *   **活跃度对异象呈现方向性弱衰减**：24 个活跃度衰减测试中 18 个表现出衰减方向（如 MA120 HML 收益在低活跃度下为 1.20%，高活跃度下为 -16.44%，相差 -22.24%），幕后统计显著性较弱（t = -1.47）。
    *   **选择后衰减表现出强显著与一致性**：在样本内（IS）筛选出的 Top 10 策略，在样本外（OOS）与伪实盘（Pseudo-Live）阶段表现出系统性滑坡：
        
        | 阶段 (Split) | 平均年化收益率 | 平均夏普比率 | 夏普保留率 (Sharpe Retention) | 衰减特征 |
        | :--- | :---: | :---: | :---: | :--- |
        | **IS (样本内)** | 5.96% | 0.68 | 100.0% | 基准筛选 |
        | **OOS (样本外)** | 3.72% | 0.35 | 55.5% | 收益中位保留率约 66.6% |
        | **PSEUDO_LIVE (伪实盘)**| 1.06% | 0.11 | 16.6% | 大幅塌陷，部分策略转负 |

### 2. Volatility_Time_Series —— 波动率建模与 Hong-Lee 谱充分性检验
*   **研究背景**：复刻与拓展 **Hong & Lee (2017)** 的广义谱波动率模型充分性检验。测试将原论文单合约设计推广至中国商品期货多合约时的有限样本统计特征及动态风控逻辑。
*   **框架与流程**：
    *   对 20 个主力商品期货日收益率拟合包含 GARCH, EGARCH, TARCH, GJR-GARCH 的 19 种参数组合，以 BIC 最小化规则选出最优模型。
    *   利用广义特征函数在频域构建谱密度，诊断经过传统检验（Ljung-Box, ARCH-LM）通过的最优模型标准化残差是否仍余留高阶非线性或特定形式的异方差结构。
    *   利用条件波动率预测值动态调控仓位，并针对被拒绝或第四矩发散的品种引入降权参考。
*   **实证结论（基于 20 个主力商品期货日频 CSV 运行结果）**：
    *   **EGARCH-t 模型占多数**：20 个被测合约中，有 15 个被 BIC 筛选为非对称 EGARCH 族。所有被测品种的最优模型均采用非正态厚尾假定（Student-t/GED），提示商品收益率具有厚尾分布特征。
    *   **谱检验提示传统方法盲区**：最优模型在标准化残差的传统诊断中均通过了自相关检验（p > 0.05）。但在数据驱动最佳带宽检验下，**AU (沪金)**（p = 0.0455）、**I (铁矿石)**（p = 0.0061）、**P (棕榈油)**（p = 0.0324）三品种的充分性原假设在 5% 水平下被拒绝，表明这些品种仍然残留有普通检验无法捕捉的异方差结构。
    *   **风险控制与仓位参考调节**：在 2026年6月18日，由于银价大幅波动，**AG（沪银）** 条件波动率处于历史 95.86% 分位数，对应的仓位缩放参考系数收缩至 **0.417**；而正常波动率下的 **AL（沪铝）** 仓位参考系数为 **1.091**。对谱检验拒绝或第四矩发散的品种，引入降权乘数（健康乘数）进行防范。

### 3. Crypto_Pricing —— 加密货币定价与下沿估值
*   **定位说明**：该模块是为对接项目大纲中指定的加密资产定价文献而开展的学术复刻工作，旨在探索将大宗商品定价与行为折价逻辑拓展应用至新兴资产领域。
*   **研究背景**：复刻大纲指定的 **Bhambhwani et al. (2019)**（链上基本面与网络价值锚）、**Biais et al. (2023)**（均衡交易便利收益与成本折价）以及 **Liu & Tsyvinski (2021)**（动量与注意力溢价）三篇论文，在缺乏传统估值模型下对加密资产（BTC）进行下沿估值区间的学术探讨。
*   **框架与流程**：
    *   **BDK 链上基本面价值锚**：以算力与活跃地址数作为自变量，计算算力下行与用户规模压力情景下的底层安全价值。
    *   **Biais 均衡交易折价层**：加权评估交易收益（40%）、交易成本（20%）、市场准入（20%）与崩盘风险（20%），映射折价系数。
    *   **Liu-Tsyvinski 风险注意力折价层**：结合价格动量（40%）、普通关注度（25%）、负面关注度（20%）与活跃度增长率（15%），评估投机热度共识。
*   **核心结论与成果**：
    *   构建了数据交叉验证系统 (`validator.py`)，实现 lead/lag 延迟相关性检验（Spearman Correlation）以及注意力指标的双源检验。
    *   设计了动态模型降级（Full Model $\rightarrow$ Core $\rightarrow$ BDK Only）与样本天数不足惩罚机制，使估值区间（Price Range）的宽度能反映数据置信度。
    *   网络规模变量（Active Addresses）仅在基本面价值锚中使用，在行为折价模块中被禁止二次计算，防范了共线性导致的偏误。

---

## 二、 规划中研究模块与后续方向

本项目后续将进一步探索以下三个量化金融课题，并逐步完成相关学术文献的复现与拓展检验：

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

## 三、 目录结构说明

```text
QuantStrat/
├── README.md                                          # 根目录说明文档（本文件）
├── QuantStrat x UIUC MSFE.pdf                         # UIUC MSFE 夏季项目合作及 bibliography 课件
├── Commodity_Futures_Raw_Data/                        # 商品期货原始价格与特征面板数据 (27个品种)
│   ├── AG.csv, AL.csv, ...
│   └── futures_panel.csv                              # 商品期货横截面主面板
├── Market_Anomalies——市场异象/                        # 模块一：技术异象、活跃度衰减与发表后衰减模块
│   ├── 02_vol_sorted_technical_anomaly.ipynb          # 波动率排序横截面技术分析异象回测
│   ├── 03_liquidity_attenuation.ipynb                 # 交易活跃度对技术异象的削弱检验
│   ├── 04_post_selection_decay.ipynb                  # 策略选择后的样本外与伪实盘衰减测试
│   ├── *.csv                                          # 策略与回归 of 运行结果表 (02_至04_系列)
│   └── README.md                                      # 模块一详细设计与CSV发现文档
└── Volatility_Time_Series——波动率&时间序列检验/       # 模块二：波动率建模与 Hong-Lee 谱检验风控模块
    ├── Traditional_Model_Selection_Sugar.ipynb        # 单合约复刻论文及全流程检验 (白糖主力)
    ├── hong_lee_20_contracts.ipynb                    # 多合约拓展运行脚本 (20个商品期货主力)
    ├── *.csv                                          # 20合约波动率建模与健康谱检验表 (01_至16_系列)
    └── README.md                                      # 模块二详细设计、CSV发现与风控逻辑文档
├── Crypto_Pricing—— 加密货币定价/                     # 模块三：BTC多维定价与下沿估值模块（大纲文献复刻）
    ├── btc_unified_pricing_model/                     # Python 核心模型包 (fetchers, validator, pricing)
    ├── tests/                                         # 单元测试模块
    └── README.md                                      # 模块三详细设计文档
```
