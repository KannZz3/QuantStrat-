# QuantStrat 量化金融研究项目复现与拓展平台 (UIUC MSFE 2026)

本项目是 **QuantStrat** 与**伊利诺伊大学金融工程硕士项目（UIUC MSFE）** 2026年夏季的量化金融研究合作项目。项目主要针对**中国商品期货市场主力合约**，采用学术规范与研究方法，以文献为锚进行复现与拓展检验，构建了一套包含**商品期货行为金融异象、高阶异方差频域检验与动态风险管理**的量化研究参考系统。

目前项目已基本完成核心研究模块的开发与实证分析，并规划了未来深入研究的三个方向。

---

## 一、 已完成核心模块全景与成果

### 1. Market_Anomalies —— 商品期货技术分析异象、活跃度衰减与发表后衰减
*   **研究背景**：复刻与拓展 **Han et al. (2013)**（高波动技术分析横截面超额收益）、**Chordia et al. (2014)**（流动性/活跃度对资本市场异象的削弱）以及 **McLean & Pontiff (2016)**（学术发表及策略筛选后收益预测性衰减）的核心假说，测试中国商品期货市场中的技术异象稳定性。
*   **框架与流程**：
    *   **02_vol_sorted_technical_anomaly.ipynb**：以日频面板为基础，计算各品种信号日 $s$ 的 60 日滚动历史波动率 `rv_60_signal` 并将其横截面划分为 `Low / Mid / High` 三个波动率桶（要求每日标的不少于 9 个）；以 $s$ 日收盘价计算四类技术指标（MA10至MA120）的 `long_flat`/`long_short` 仓位信号；于 $t = s + 1$ 日（延迟交易）执行并以 Forward 1D 收益率 `fwd_ret_1d` 计算策略日收益（扣除单边 5 bps 成本），构建 HML 组合收益。
    *   **03_liquidity_attenuation.ipynb**：根据成交量、持仓量及成交额的 z-score 合成 `activity_score`，在信号日分置为 `Low / Mid / High` 活跃度桶；与 HML 收益对齐后进行双重分桶收益分析与包含交互项的衰减 OLS 回归（计算 HC1 异方差稳健标准误）。
    *   **04_post_selection_decay.ipynb**：生成覆盖 MA、TSMOM、BREAKOUT、REVERSAL 四大类族的 26 个候选策略；切分样本为样本内（IS: 2016-01-05 至 2020-12-31）、样本外（OOS: 2021-01-01 至 2023-12-31）与伪实盘（Pseudo-Live: 2024-01-01 起）区间（隔离收益实现窗口防范数据泄露）；以 IS 收益率筛选 Top 10 策略并评估其表现跨区间衰减幅度。
*   **数据实证结论**：
    *   **高波动技术异象不具备稳定显著性（基于 `02_high_minus_low_summary.csv` 与 `02_monotonic_flags.csv`）**：在 8 个技术交易策略中，仅 5 个策略的 HML 年化超额收益为正（MA10 long_flat 为 **0.65%**，MA20 long_flat 为 **4.30%**，MA20 long_short 为 **5.27%**，MA60 long_flat 为 **1.75%**，MA60 long_short 为 **0.18%**），且全部 8 个策略的 HML 收益在 5% 显著性水平下统计上均不显著（$|t| < 1.96$）。MA20 long_short 策略表现相对最强（HML 年化收益为 **5.27%**，t 统计量为 **0.91**）。而在长周期策略 MA120 long_short 上，HML 出现反转（年化收益为 **-10.23%**，t 统计量为 **-1.77**）。
    *   **交易活跃度对异象呈现方向性弱削弱（基于 `03_activity_attenuation_summary.csv` 与 `03_activity_flags.csv`）**：在 24 个衡量净收益 HML 的活跃度衰减测试中，有 **18** 个（占比 **75.00%**）在方向上表现出 HML 收益随活跃度上升而收窄的特征，但统计上均不显著（$|t| < 1.96$）。例如，MA120 long_short 策略的 HML 年化收益从低活跃度下的 **1.20%** 收缩至高活跃度下的 **-16.44%**，衰减幅度达 **-22.24%**，对应的 t 统计量为 **-1.47**。
    *   **流动性与波动率对趋势收益的回归冲击（基于 `03_activity_interaction_regression.csv`）**：包含交互项的 OLS 回归表明，交易活跃度评分 (`activity_score`) 是中长线趋势策略（MA60, MA120）收益的显著正向驱动力（对 MA60 long_short 的系数为 $3.18 \times 10^{-4}$，t 值为 **3.33**；对 MA120 long_short 的系数为 $3.28 \times 10^{-4}$，t 值为 **3.44**）。此外，对于长线策略（MA120 long_short），处于高波状态 (`high_vol_dummy`) 对其收益有显著的负向冲击（系数为 $-4.79 \times 10^{-4}$，t 值为 **-2.39**），反映了长线趋势跟踪策略在高波动率市场中容易遭受双边洗盘（whipsaws）导致损耗。
    *   **选择偏差与样本外表现的系统性大幅衰减（基于 `04_post_selection_decay_summary.csv` 与 `04_all_strategy_decay_summary.csv`）**：在 26 个候选策略池中，仅有 **2** 个策略在全区间表现稳健（ROBUST）：`BREAKOUT_120_long_flat`（IS 夏普 **0.26** → OOS **0.52** → Pseudo-Live **0.49**）和 `MA_60_long_short`（IS 夏普 **0.18** → OOS **0.16** → Pseudo-Live **0.19**）。它们由于在样本内（IS）表现适中而未能入选 Top 10。相反，IS 筛选出的 Top 10 策略呈现出严重的选择偏差（Selection Bias），其夏普比率均值从 IS 阶段的 **0.68** 大幅降至 OOS 阶段的 **0.35**，并在 Pseudo-Live 阶段进一步降至 **0.11**（中位数分别从 **0.67** 降至 **0.40** 和 **0.07**）；各策略夏普比率保留率中位数在 OOS 和 Pseudo-Live 阶段分别仅为 **55.47%** 和 **16.56%**。

### 2. Volatility_Time_Series —— 波动率建模与 Hong-Lee 谱充分性检验
*   **研究背景**：复刻与拓展 **Hong & Lee (2017)** 的广义谱波动率模型充分性检验。测试将原论文单合约设计推广至中国商品期货多合约时的有限样本统计特征及动态风控逻辑。
*   **框架与流程**：
    *   **模型拟合与选择**（`Traditional_Model_Selection_Sugar.ipynb`）：针对 20 个主力商品期货日收益率，拟合包含常数/AR(1) 均值，结合 GARCH, EGARCH11/21, GJR, TARCH 条件方差，以及 Normal, Student-t, Skewed Student-t, GED 误差分布的 19 种参数组合；通过标准化残差 Ljung-Box 自相关（$z$ 与 $z^2$ 的 10/20/30 阶滞后）与 ARCH-LM 检验（10阶）过滤后，以 BIC 最小化规则确立最优模型。
    *   **Hong-Lee 广义谱检验**（`hong_lee_20_contracts.ipynb`）：基于广义特征函数残差构建稳健谱密度函数，在固定带宽（主带宽 $p \approx 21$）与惩罚性数据驱动自适应带宽下，对最优模型进行频域非线性结构异方差检验，计算 robust M 统计量及 p 值；运行 100 次蒙特卡洛 Size 仿真，基于 Wilson Score 方法计算其 95% 置信区间。
    *   **风险控制参考**：计算单日 95% 与 99% 双向 VaR 并完成 Kupiec POF 回测；根据目标波动率计算仓位参考系数（`Raw Scale`），当品种被谱检验拒绝（`REJECT`）或因自由度估计值 $\nu \le 4$ 导致第四矩理论不收敛时，自动乘降权折扣系数（`Health Multiplier`）。
*   **数据实证结论**：
    *   **EGARCH 族与非正态厚尾假定适用（基于 `02_best_model_by_symbol.csv`）**：在 20 个主力商品期货中，有 **15** 个品种的 BIC 最优方差模型为 **EGARCH 族**，且全线排除正态分布（14 个为 Student-t，3 个为 GED，3 个为 Skewed Student-t）。模型参数展现出强波动持续性（例如，白糖 SR 的最优模型 EGARCH(1,1)-t 估计 $\beta_1 = 0.9900$，自由度估计 $\nu = 4.495$；沪银 AG 估计 $\nu = 3.164$）。
    *   **数据驱动谱检验精准识别普通检验盲区（基于 `13_hong_lee_data_driven_bandwidth_selected-Copy1.csv`）**：在标准化残差均通过传统 Ljung-Box 自相关与 ARCH-LM 检验（p > 0.05）的前提下，自适应数据驱动谱检验在 5% 显著性水平下**显著拒绝了 3 个最优模型的充分性**：
        1.  **AU (沪金)**：最优带宽 $p=5.32$，统计量 $M_{robust}=1.69$，p 值 = **0.0455**；
        2.  **I (铁矿石)**：最优带宽 $p=5.32$，统计量 $M_{robust}=2.51$，p 值 = **0.0061**；
        3.  **P (棕榈油)**：最优带宽 $p=5.32$，统计量 $M_{robust}=1.85$，p 值 = **0.0324**。
    *   **部分品种第四矩理论收敛受限（基于 `02_best_model_by_symbol.csv` 与 `10_model_health_summary.csv`）**：检测发现 **AG (沪银)**（$\nu = 3.1640$）、**CF (棉花)**（$\nu = 3.2287$）、**M (豆粕)**（$\nu = 3.8361$）、**RU (橡胶)**（$\nu = 3.3530$）和 **SN (沪锡)**（$\nu = 3.7399$）共 5 个品种的最优模型自由度估计值 $\nu \le 4$，触发了 `hl_moment_condition_ok = False` 警报，表明其理论第四矩（峰度）发散，谱检验的标准渐进方差推导在数学上受限。
    *   **谱检验在有限样本下表现保守（基于 `15_hong_lee_monte_carlo_size_summary.csv`）**：以最优估计模型为数据生成过程（DGP）运行 100 次蒙特卡洛 Size 仿真，在 5% 的名义显著性水平下，AL（GARCH-t）的经验第一类错误拒绝率为 **1.00%**，AG（EGARCH-t）的经验拒绝率为 **0.00%**，表明该检验在有限样本中实际第一类错误偏低，表现相对保守。
    *   **动态 VaR 预测回测准确度极高（基于 `05_var_backtest_by_symbol.csv`）**：在 20 个品种的 VaR 双向回测中，95% VaR 的 Long / Short 端 Kupiec POF 检验通过率分别为 **18/20** 和 **17/20**，平均违约率分别为 **4.91%** 和 **4.82%**；99% VaR 的 Long / Short 端通过率分别为 **17/20** 和 **19/20**，平均违约率分别为 **0.74%** 和 **0.93%**，充分印证了 GARCH 族模型的动态风险刻画能力。
    *   **条件波动率及仓位参考因子横截面分化（基于 `06_current_vol_state_and_position_scaling.csv`）**：最新数据日（2026年6月18日）品种条件波动率分化明显：**AG (沪银)** 和 **MA (甲醇)** 处于极端高波状态（条件波动率分别为 **3.805%** 和 **2.884%**，分位数分别为 **95.86%** 和 **96.61%**），其仓位参考因子分别收缩至 **0.417x** 和 **0.566x**；而 **AL (沪铝)** 处于常态波动状态（条件波动率 **0.880%**，分位数 **38.71%**），仓位释放至 **1.091x**；**I (铁矿石)** 处于极端低波状态（条件波动率 **1.103%**，分位数 **1.34%**），仓位参考因子释放至 capped 上限 **1.500x** (原始值为 **2.007x**)。

### 3. Crypto_Pricing —— 加密资产多维度定价与下沿估值
*   **研究背景**：针对无现金流、无传统估值锚的加密资产（BTC），复刻与拓展 **Bhambhwani et al. (2019, BDK)**（链上基本面与网络价值锚定）、**Biais et al. (2023)**（均衡交易便利与折价层）以及 **Liu & Tsyvinski (2021)**（动量与注意力折价层）三篇文献，构建具备强容错与降级能力的级联下沿估值系统。
*   **框架与流程**：
    *   **主控工作流与采集校验**：利用 `pipeline.py` 串联工作流。通过 `fetchers.py` 从 CoinGecko、Binance、Blockchain.com、Coin Metrics 等多源抓取日频特征，并由 `validator.py` 执行多源 Gap 校验与延迟相关性（Spearman）筛选，输出 `Strict-tier`（严格验证）与 `Research-tier`（研究代理级）双轨特征库。
    *   **基本面锚定与 OLS 重校准**：`pricing.py` 实现 BDK 二元 Log-Log 基准模型并支持样本内 OLS 动态重校准以捕获最新周期的弹性系数，并在特定压力目标下缩放算力与活跃地址生成基本面底座 $V_{BDK}$。
    *   **交易摩擦与行为情绪折价**：加权整合交易收益/成本/准入/崩盘风险计算 $S_{Biais}$ 评分（对崩盘风险整体进行上限归零过滤牛市噪点），加权整合动量/注意力/活跃增长计算 $S_{Liu}$ 评分（对单源研究级注意力进行 0.60 权重打折）；通过连续指数下行映射生成折价系数。
*   **数据实证结论**（基于最新样例输出 `btc_three_paper_framework_pricing_v1_3.csv`，当时 BTC 价格约为 10.5 万美元）：
    *   **基本面公允价估算与弹性表现**：当前样本内 OLS 重校准的算力与活跃地址弹性均为正，系统成功切换至 `full_ols_insample` 校准模式。全样本有效交叉验证观测天数达 **97 天**（无需额外天数惩罚）。模型估算当前比特币的长期 Log-Log 基本面公允价值为 **71,588.21 美元**（实际市场价存在约 33% 泡沫溢价）。
    *   **行为折价层发挥差异化作用**：在当前牛市高位状态下，Biais 评分得分为 **1.058**（收益与风控分量主导），对应交易折价系数为 **1.00**（无折价，即网络交易便利效能高）。而 Liu 评分受 7D/14D 动量反转与研究级注意力偏弱拖累，得分为 **-0.405**，对应动量注意力折价系数为 **0.960**（约打 96 折）。系统最终以级联联合折价系数 **0.960** 入模。
    *   **多情景价格下沿区间输出**：
        1. **基础压力下沿**：在算力收缩至 919.22 EH/s、地址收缩至 46.49 万的轻度压力下，价格下沿支撑点为 **57,605.37 美元**，对应估值区间为 `[51,844.83, 63,365.90]`；
        2. **核心估值下沿（常规参考）**：在算力降至 891.08 EH/s、地址降至 45.07 万（15% 历史分位）的核心压力下，下沿支撑点为 **52,312.48 美元**，对应估值区间为 `[47,081.23, 57,543.72]`（带宽 $W = 0.10$）；
        3. **严重压力下沿**：在 5% 历史极值下，下沿点降至 **44,239.87 美元**，对应估值区间为 `[39,815.89, 48,663.86]`；
        4. **极端尾部下沿**：在 5% 历史极值加 85% 当前上限下压（无二次重压）的黑天鹅底场景下，估值下沿低至 **36,931.48 美元**，对应区间为 `[33,238.33, 40,624.63]`。


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
