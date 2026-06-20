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
*   **数据实证结论与交易指导意义**：
    *   **高波动技术异象不具备稳定显著性（基于 `02_high_minus_low_summary.csv`）**：在测试的 8 个技术策略中，仅 5 个策略的 HML 年化超额收益为正，且均在 5% 水平下统计不显著。其中 **MA20 策略表现相对最强**（long_short 版本 HML 年化收益为 **5.27%**，t 统计量仅为 **0.91**）。而在长周期策略 **MA120** 上异象发生反转（long_short 年化收益为 **-10.23%**，t 统计量为 **-1.77**）。
        *   *交易意义*：高波动并不能稳定增强技术分析的盈利能力；相反，长周期趋势策略在高波动资产上极易因“趋势衰竭”与“宽幅震荡”而产生亏损（HML反转），提示交易员应避免在高波动商品合约上重仓长周期趋势跟踪策略。
    *   **交易活跃度对异象呈现方向性弱削弱（基于 `03_activity_attenuation_summary.csv`）**：在 24 个活跃度衰减测试中，有 18 个在方向上表现出 HML 收益随活跃度上升而收窄的特征（无统计显著性，$|t| < 1.96$）。其中衰减最明显的是 **MA120 long_short** 策略，其在低活跃度下 HML 年化收益为 **1.20%**，而在高活跃度状态下收缩至 **-16.44%**，活跃度带来的溢价衰减幅度达 **-22.24%**（t 统计量为 **-1.47**）。
        *   *交易意义*：当商品合约的成交持仓活跃度大幅飙升时，市场套利与流动性提供者会加速抹平技术分析异象（尤其是长周期策略）。交易员应在合约交易量及持仓量创历史新高（拥挤度极高）时，主动降低对该合约的技术指标配比。
    *   **策略选择后收益衰减表现出强显著性（基于 `04_post_selection_decay_summary.csv`）**：在样本内（IS）表现最优的 Top 10 策略，在出样（OOS）与伪实盘（Pseudo-Live）阶段出现系统性滑坡，**没有一个策略能够保持表现稳健**。其中 5 个策略为严重衰减（表现减半），2 个策略收益彻底转负。
        
        | 阶段 (Split) | 平均年化收益率 | 平均夏普比率 | 夏普保留率 | 代表策略表现变化 (BREAKOUT_20_long_flat) |
        | :--- | :---: | :---: | :---: | :--- |
        | **IS (2016-2020)** | **5.96%** | **0.68** | **100.0%** | 年化 **8.93%**，表现稳健 |
        | **OOS (2021-2023)** | **3.72%** | **0.35** | **55.5%** | 年化 **4.93%**，部分衰减 (Partial Decay) |
        | **PSEUDO_LIVE (2024-2026)**| **1.06%** | **0.11** | **16.6%** | 年化 **3.55%**，累计保留率仅 39.8% |

        *   *交易意义*：单纯基于回测表现筛选策略存在极高的选择性偏差与 alpha 衰减风险。实盘交易系统必须对回测夏普比率进行系统性折价（OOS 阶段至少折价 50%，Live 阶段折价 80%），并倾向于采用多策略均配，而非参数最优化。

### 2. Volatility_Time_Series —— 波动率建模与 Hong-Lee 谱充分性检验
*   **研究背景**：复刻与拓展 **Hong & Lee (2017)** 的广义谱波动率模型充分性检验。测试将原论文单合约设计推广至中国商品期货多合约时的有限样本统计特征及动态风控逻辑。
*   **框架与流程**：
    *   对 20 个主力商品期货日收益率拟合包含 GARCH, EGARCH, TARCH, GJR-GARCH 的 19 种参数组合，以 BIC 最小化规则选出最优模型。
    *   利用广义特征函数在频域构建谱密度，诊断经过传统检验（Ljung-Box, ARCH-LM）通过的最优模型标准化残差是否仍余留高阶非线性或特定形式的异方差结构。
    *   利用条件波动率预测值动态调控仓位，并针对被拒绝或第四矩发散的品种引入降权参考。
*   **数据实证结论与交易指导意义**：
    *   **非对称波动与厚尾特征普遍适用（基于 `02_best_model_by_symbol.csv`）**：在 20 个商品期货中，有 15 个品种的最优模型为 **EGARCH 族**，且所有品种均选用了非正态厚尾分布（如 Student-t 或 GED）。模型参数表现出极强的波动持续性（以白糖为例，$\beta_1 = 0.9899$）和显著的厚尾特征（白糖自由度 $\nu = 4.497$，沪银 $\nu = 3.164$）。
        *   *交易意义*：商品期货波动率具有极强的粘性（ clustering ），一旦进入高波状态将长期持续；极低的自由度参数表明极端暴涨暴跌风险远高于正态分布假设，系统必须使用 Student-t 类分布计算动态 VaR，否则将严重低估极端尾部风险。
    *   **数据驱动谱检验精准穿透传统盲区（基于 `13_hong_lee_data_driven_bandwidth_selected-Copy1.csv`）**：在标准化残差均通过传统 Ljung-Box 与 ARCH-LM 检验（p > 0.05）的前提下，惩罚性数据驱动带宽选择器在 5% 显著性水平下**显著拒绝了 3 个最优模型的充分性**：
        1.  **AU (沪金)**：最优带宽 $p=5.32$，统计量 $M_{robust}=1.69$，p 值 = **0.0455**；
        2.  **I (铁矿石)**：最优带宽 $p=5.32$，统计量 $M_{robust}=2.51$，p 值 = **0.0061**；
        3.  **P (棕榈油)**：最优带宽 $p=5.32$，统计量 $M_{robust}=1.85$，p 值 = **0.0324**。
        *   *交易意义*：传统检验存在严重盲区。对于黄金、铁矿石和棕榈油，即使经典诊断认为异方差已消除，但谱检验揭示其短滞后频域仍残留显著的非线性波动率依赖。风控端必须对这三个品种的风险输出增加安全保护垫（如人工将计算出的风险敞口收缩 15-20%）。
    *   **第四矩理论收敛受限提示（基于 `10_model_health_summary.csv`）**：检测发现 **AG (沪银)** 和 **CF (棉花)** 等品种的自由度估计值 $\nu \le 4$（AG 为 3.1640，CF 为 3.2287），触发了 `hl_inference_limited_fourth_moment` 警报。
        *   *交易意义*：当 $\nu \le 4$ 时，标准化残差的理论第四矩（峰度）不存在，会导致依赖第四矩收敛的传统渐进方差检验在数理上失效。在构建组合优化模型时，应避免对沪银和棉花使用依赖样本高阶矩（如超额峰度）的参数估计方法。
    *   **目标波动率仓位缩放的动态避险参考（基于 `06_current_vol_state_and_position_scaling.csv`）**：以 2026年6月18日 最新截面数据为例，系统根据条件波动率状态实现了完全分化的仓位控制：
        *   **AG (沪银)**：条件波动率高达 **3.805%**，历史分位数 **95.86%**（`extreme_high_vol`），仓位自动缩减至标准的 **0.417x**。
        *   **AL (沪铝)**：条件波动率仅为 **0.880%**，历史分位数 **38.71%**（`normal_vol`），仓位释放至 **1.091x**。
        *   *交易意义*：在突发极端波动（如沪银大涨）时，目标波动率算法能够自动收缩敞口至 4.17 折以规避保证金穿透风险，同时将额度向常态波动的沪铝释放，起到了平滑组合资金曲线、保护保证金安全的实质风控作用。

### 3. Crypto_Pricing —— 加密资产多维定价与下沿估值
*   **研究背景**：复刻 **Bhambhwani et al. (2019)**（链上基本面与网络价值锚）、**Biais et al. (2023)**（均衡交易便利收益与成本折价）以及 **Liu & Tsyvinski (2021)**（动量与注意力溢价）三篇论文，在缺乏传统估值模型下对加密资产（BTC）进行下沿估值区间的探讨。
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
