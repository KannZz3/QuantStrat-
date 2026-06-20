# QuantStrat: Quantitative Finance Research Platform: Replication and Extension (UIUC MSFE 2026)

本项目是 **QuantStrat** 与**伊利诺伊大学金融工程硕士项目（UIUC MSFE）** 2026年夏季的量化金融研究合作项目。项目主要针对**中国商品期货市场主力合约**，采用学术规范与研究方法，以文献为锚进行复现与拓展检验，构建了一套包含**商品期货行为金融异象、高阶异方差频域检验与动态风险管理**的量化研究参考系统。
This project is a collaborative quantitative finance research initiative between **QuantStrat** and the **Master of Science in Financial Engineering (MSFE)** program at the **University of Illinois Urbana-Champaign (UIUC)** for Summer 2026. Focusing on active contracts in the Chinese commodity futures market, the project adopts rigorous academic methodologies to replicate and extend literature-anchored hypotheses. It constructs a quantitative research system encompassing commodity futures behavioral anomalies, frequency-domain diagnostics for high-order heteroscedasticity, and dynamic risk management.

目前项目已基本完成核心研究模块的开发与实证分析，并规划了未来深入研究的两个方向。
Currently, the core research modules and empirical analyses are complete, and two future research directions are planned.

---

## 一、 已完成核心模块全景与成果 / I. Overview and Outcomes of Completed Core Modules

### 1. Market_Anomalies —— 商品期货技术分析异象、活跃度衰减与发表后衰减 / Technical Anomalies, Activity Attenuation, and Post-Publication Decay in Commodity Futures

*   **研究背景 / Research Background**：
    *   **中文**：复刻与拓展 **Han et al. (2013)**（高波动技术分析横截面超额收益）、**Chordia et al. (2014)**（流动性/活跃度对资本市场异象的削弱）以及 **McLean & Pontiff (2016)**（学术发表及策略筛选后收益预测性衰减）的核心假说，测试中国商品期货市场中的技术异象稳定性。
    *   **English**: Replicates and extends the core hypotheses of **Han et al. (2013)** (cross-sectional excess returns of technical indicators under high volatility), **Chordia et al. (2014)** (attenuation of capital market anomalies by liquidity and trading activity), and **McLean & Pontiff (2016)** (predictive return decay post academic publication and strategy selection) to test the stability of technical anomalies in the Chinese commodity futures market.

*   **框架与流程 / Framework & Workflow**：
    *   **02_vol_sorted_technical_anomaly.ipynb**：
        *   **中文**：以日频面板为基础，计算各品种信号日 $s$ 的 60 日滚动历史波动率 `rv_60_signal` 并将其横截面划分为 `Low / Mid / High` 三个波动率桶（要求每日标的不少于 9 个）；以 $s$ 日收盘价计算四类技术指标（MA10至MA120）的 `long_flat`/`long_short` 仓位信号；于 $t = s + 1$ 日（延迟交易）执行并以 Forward 1D 收益率 `fwd_ret_1d` 计算策略日收益（扣除单边 5 bps 成本），构建 HML 组合收益。
        *   **English**: Computes the 60-day rolling historical volatility (`rv_60_signal`) on each signal day $s$ across a daily panel, grouping contracts cross-sectionally into `Low / Mid / High` volatility buckets (requiring at least 9 eligible assets daily). Generates `long_flat` / `long_short` position signals using four classes of technical indicators (MA10 to MA120) based on day $s$ closing prices. Positions are executed on day $t = s + 1$ (delayed trading) and performance is evaluated using the forward 1D return (`fwd_ret_1d`) net of a 5 bps one-way transaction cost to construct High-Minus-Low (HML) portfolio returns.
    *   **03_liquidity_attenuation.ipynb**：
        *   **中文**：根据成交量、持仓量及成交额的 z-score 合成 `activity_score`，在信号日分置为 `Low / Mid / High` 活跃度桶；与 HML 收益对齐后进行双重分桶收益分析与包含交互项的衰减 OLS 回归（计算 HC1 异方差稳健标准误）。
        *   **English**: Synthesizes a composite `activity_score` from the z-scores of trading volume, open interest, and turnover to categorize assets into `Low / Mid / High` activity buckets on signal days. Conducts double-sorting portfolio return analysis and OLS regressions with interaction terms using HC1 heteroscedasticity-robust standard errors.
    *   **04_post_selection_decay.ipynb**：
        *   **中文**：生成覆盖 MA、TSMOM、BREAKOUT、REVERSAL 四大类族的 26 个候选策略；切分样本为样本内（IS: 2016-01-05 至 2020-12-31）、样本外（OOS: 2021-01-01 至 2023-12-31）与伪实盘（Pseudo-Live: 2024-01-01 起）区间（隔离收益实现窗口防范数据泄露）；以 IS 收益率筛选 Top 10 策略并评估其表现跨区间衰减幅度。
        *   **English**: Generates a candidate pool of 26 strategies across MA, TSMOM, BREAKOUT, and REVERSAL families. Splits the sample into In-Sample (IS: 2016-01-05 to 2020-12-31), Out-of-Sample (OOS: 2021-01-01 to 2023-12-31), and Pseudo-Live (2024-01-01 onward) periods (isolating forward return windows to prevent data leakage). Selects the Top 10 strategies based on IS Sharpe ratios and quantifies their performance decay across splits.

*   **数据实证结论 / Empirical Findings**：
    *   **高波动技术异象不具备稳定显著性 / High-Volatility Technical Anomalies Lack Statistical Significance** (基于 / based on `02_high_minus_low_summary.csv` 与 / and `02_monotonic_flags.csv`)：
        *   **中文**：在 8 个技术交易策略中，仅 5 个策略的 HML 年化超额收益为正（MA10 long_flat 为 **0.65%**，MA20 long_flat 为 **4.30%**，MA20 long_short 为 **5.27%**，MA60 long_flat 为 **1.75%**，MA60 long_short 为 **0.18%**），且全部 8 个策略的 HML 收益在 5% 显著性水平下统计上均不显著（$|t| < 1.96$）。MA20 long_short 策略表现相对最强（HML 年化收益为 **5.27%**，t 统计量为 **0.91**）。而在长周期策略 MA120 long_short 上，HML 出现反转（年化收益为 **-10.23%**，t 统计量为 **-1.77**）。
        *   **English**: Out of the 8 technical trading strategies, only 5 yield positive annualized HML excess returns (MA10 long_flat: **0.65%**, MA20 long_flat: **4.30%**, MA20 long_short: **5.27%**, MA60 long_flat: **1.75%**, MA60 long_short: **0.18%**), and all 8 HML returns are statistically insignificant at the 5% significance level ($|t| < 1.96$). The MA20 long_short strategy shows the strongest relative performance (HML annualized return: **5.27%**, t-statistic: **0.91**). Conversely, the long-term MA120 long_short strategy exhibits an HML reversal (annualized return: **-10.23%**, t-statistic: **-1.77**).
    *   **交易活跃度对异象呈现方向性弱削弱 / Trading Activity Directionally Dampens HML Returns** (基于 / based on `03_activity_attenuation_summary.csv` 与 / and `03_activity_flags.csv`)：
        *   **中文**：在 24 个衡量净收益 HML 的活跃度衰减测试中，有 **18** 个（占比 **75.00%**）在方向上表现出 HML 收益随活跃度上升而收窄的特征，但统计上均不显著（$|t| < 1.96$）。例如，MA120 long_short 策略的 HML 年化收益从低活跃度下的 **1.20%** 收缩至高活跃度下的 **-16.44%**，衰减幅度达 **-22.24%**，对应的 t 统计量为 **-1.47**。
        *   **English**: Among the 24 HML tests for net returns, **18** (representing **75.00%**) directionally exhibit narrowing HML spreads as trading activity increases, though none are statistically significant ($|t| < 1.96$). For example, the HML annualized return of the MA120 long_short strategy contracts from **1.20%** under low activity to **-16.44%** under high activity—a decay of **-22.24%** (t-statistic: **-1.47**).
    *   **流动性与波动率对趋势收益的回归冲击 / Impact of Liquidity and Volatility on Trend Returns** (基于 / based on `03_activity_interaction_regression.csv`)：
        *   **中文**：包含交互项的 OLS 回归表明，交易活跃度评分 (`activity_score`) 是中长线趋势策略（MA60, MA120）收益的显著正向驱动力（对 MA60 long_short 的系数为 $3.18 \times 10^{-4}$，t 值为 **3.33**；对 MA120 long_short 的系数为 $3.28 \times 10^{-4}$，t 值为 **3.44**）。此外，对于长线策略（MA120 long_short），处于高波状态 (`high_vol_dummy`) 对其收益有显著的负向冲击（系数为 $-4.79 \times 10^{-4}$，t 值为 **-2.39**），反映了长线趋势跟踪策略在高波动率市场中容易遭受双边洗盘（whipsaws）导致损耗。
        *   **English**: OLS regressions with interaction terms reveal that the composite `activity_score` acts as a significant positive driver for medium-to-long term trend strategies (coefficient for MA60 long_short: $3.18 \times 10^{-4}$, t-value: **3.33**; coefficient for MA120 long_short: $3.28 \times 10^{-4}$, t-value: **3.44**). Furthermore, for the long-term MA120 long_short strategy, being in a high-volatility state (`high_vol_dummy`) exerts a significant negative shock on returns (coefficient: $-4.79 \times 10^{-4}$, t-value: **-2.39**), reflecting the performance drag on trend-following strategies due to whipsaws in highly volatile markets.
    *   **选择偏差与样本外表现的系统性大幅衰减 / Out-of-Sample Performance Decay Due to Selection Bias** (基于 / based on `04_post_selection_decay_summary.csv` 与 / and `04_all_strategy_decay_summary.csv`)：
        *   **中文**：在 26 个候选策略池中，仅有 **2** 个策略在全区间表现稳健（ROBUST）：`BREAKOUT_120_long_flat`（IS 夏普 **0.26** → OOS **0.52** → Pseudo-Live **0.49**）和 `MA_60_long_short`（IS 夏普 **0.18** → OOS **0.16** → Pseudo-Live **0.19**）。它们由于在样本内（IS）表现适中而未能入选 Top 10。相反，IS 筛选出的 Top 10 策略呈现出严重的选择偏差（Selection Bias），其夏普比率均值从 IS 阶段的 **0.68** 大幅降至 OOS 阶段的 **0.35**，并在 Pseudo-Live 阶段进一步降至 **0.11**（中位数分别从 **0.67** 降至 **0.40** 和 **0.07**）；各策略夏普比率保留率中位数在 OOS 和 Pseudo-Live 阶段分别仅为 **55.47%** 和 **16.56%**。
        *   **English**: In the pool of 26 candidates, only **2** strategies show robust performance across all periods (ROBUST): `BREAKOUT_120_long_flat` (IS Sharpe: **0.26** → OOS: **0.52** → Pseudo-Live: **0.49**) and `MA_60_long_short` (IS Sharpe: **0.18** → OOS: **0.16** → Pseudo-Live: **0.19**). These were not selected in the Top 10 due to moderate IS performance. Conversely, the selected Top 10 strategies suffer from severe selection bias: their mean Sharpe ratio decays from **0.68** during the IS phase to **0.35** in the OOS phase, and further declines to **0.11** in the Pseudo-Live phase (medians drop from **0.67** to **0.40** and **0.07**, respectively). The median Sharpe ratio retention rate is only **55.47%** in OOS and **16.56%** in Pseudo-Live.

---

## 二、 Volatility_Time_Series —— 波动率建模与 Hong-Lee 谱充分性检验 / Volatility Modeling and Hong-Lee Spectral Adequacy Diagnostics

*   **研究背景 / Research Background**：
    *   **中文**：复刻与拓展 **Hong & Lee (2017)** 的广义谱波动率模型充分性检验。测试将原论文单合约设计推广至中国商品期货多合约时的有限样本统计特征及动态风控逻辑。
    *   **English**: Replicates and extends the generalized spectral test for volatility model adequacy proposed by **Hong & Lee (2017)**. Evaluates the finite-sample statistical properties and dynamic risk-control logic when scaling the original single-contract design to a multi-contract framework across Chinese commodity futures.

*   **框架与流程 / Framework & Workflow**：
    *   **模型拟合与选择 / Model Fitting and Selection**（`Traditional_Model_Selection_Sugar.ipynb`）：
        *   **中文**：针对 20 个主力商品期货日收益率，拟合包含常数/AR(1) 均值，结合 GARCH, EGARCH11/21, GJR, TARCH 条件方差，以及 Normal, Student-t, Skewed Student-t, GED 误差分布的 19 种参数组合；通过标准化残差 Ljung-Box 自相关（$z$ 与 $z^2$ 的 10/20/30 阶滞后）与 ARCH-LM 检验（10阶）过滤后，以 BIC 最小化规则确立最优模型。
        *   **English**: Fits 19 parameter combinations consisting of Constant/AR(1) mean specifications paired with GARCH, EGARCH11/21, GJR, and TARCH conditional variance equations under Normal, Student-t, Skewed Student-t, and GED error distributions on daily returns of 20 active futures. Selects the optimal model by minimizing the Bayesian Information Criterion (BIC) after filtering via Ljung-Box autocorrelation tests (on standardized residuals $z$ and $z^2$ up to lags 10/20/30) and ARCH-LM tests (up to lag 10).
    *   **Hong-Lee 广义谱检验 / Hong-Lee Generalized Spectral Test**（`hong_lee_20_contracts.ipynb`）：
        *   **中文**：基于广义特征函数残差构建稳健谱密度函数，在固定带宽（主带宽 $p \approx 21$）与惩罚性数据驱动自适应带宽下，对最优模型进行频域非线性结构异方差检验，计算 robust M 统计量及 p 值；运行 100 次蒙特卡洛 Size 仿真，基于 Wilson Score 方法计算其 95% 置信区间。
        *   **English**: Constructs a robust spectral density function based on generalized characteristic function residuals. Conducts frequency-domain non-linear heteroscedasticity diagnostics under both fixed bandwidth ($p \approx 21$) and data-driven adaptive bandwidths to compute robust M-statistics and p-values. Runs 100 Monte Carlo Size simulations with Wilson Score 95% confidence intervals.
    *   **风险控制参考 / Risk Control Reference**：
        *   **中文**：计算单日 95% 与 99% 双向 VaR 并完成 Kupiec POF 回测；根据目标波动率计算仓位参考系数（`Raw Scale`），当品种被谱检验拒绝（`REJECT`）或因自由度估计值 $\nu \le 4$ 导致第四矩理论不收敛时，自动乘降权折扣系数（`Health Multiplier`）。
        *   **English**: Estimates 95% and 99% two-way daily VaR and performs Kupiec POF backtests. Computes raw target-volatility position scaling factors (`Raw Scale`) and applies a penalty discount (`Health Multiplier`) if a contract's optimal model is rejected by the spectral test or fails fourth-moment convergence (estimated degrees of freedom $\nu \le 4$).

*   **数据实证结论 / Empirical Findings**：
    *   **EGARCH 族与非正态厚尾假定适用 / Prevalence of EGARCH Specifications and Non-Normal Tails** (基于 / based on `02_best_model_by_symbol.csv`)：
        *   **中文**：在 20 个主力商品期货中，有 **15** 个品种的 BIC 最优方差模型为 **EGARCH 族**，且全线排除正态分布（14 个为 Student-t，3 个为 GED，3 个为 Skewed Student-t）。模型参数展现出强波动持续性（例如，白糖 SR 的最优模型 EGARCH(1,1)-t 估计 $\beta_1 = 0.9900$，自由度估计 $\nu = 4.495$；沪银 AG 估计 $\nu = 3.164$）。
        *   **English**: For **15 out of 20** active commodity futures, the BIC-optimal conditional variance model belongs to the **EGARCH family**, and normal error distributions are rejected across all contracts (14 Student-t, 3 GED, and 3 Skewed Student-t). Model parameters indicate high volatility persistence (e.g., White Sugar SR's optimal EGARCH(1,1)-t model yields $\beta_1 = 0.9900$ and estimated degrees of freedom $\nu = 4.495$; Silver AG yields $\nu = 3.164$).
    *   **数据驱动谱检验精准识别普通检验盲区 / Data-Driven Spectral Test Detects Misspecifications in Traditional Diagnostics' Blind Spots** (基于 / based on `13_hong_lee_data_driven_bandwidth_selected-Copy1.csv`)：
        *   **中文**：在标准化残差通过传统 Ljung-Box 自相关与 ARCH-LM 检验（p > 0.05）的前提下，自适应数据驱动谱检验在 5% 显著性水平下**显著拒绝了 3 个最优模型的充分性**：
            1.  **AU (沪金)**：最优带宽 $p=5.32$，统计量 $M_{robust}=1.69$，p 值 = **0.0455**；
            2.  **I (铁矿石)**：最优带宽 $p=5.32$，统计量 $M_{robust}=2.51$，p 值 = **0.0061**；
            3.  **P (棕榈油)**：最优带宽 $p=5.32$，统计量 $M_{robust}=1.85$，p 值 = **0.0324**。
        *   **English**: Even when standardized residuals pass traditional Ljung-Box and ARCH-LM tests (p > 0.05), the data-driven spectral test **significantly rejects model adequacy for 3 optimal specifications** at the 5% significance level:
            1.  **AU (Gold)**: Optimal bandwidth $p=5.32$, robust statistic $M_{robust}=1.69$, p-value = **0.0455**;
            2.  **I (Iron Ore)**: Optimal bandwidth $p=5.32$, robust statistic $M_{robust}=2.51$, p-value = **0.0061**;
            3.  **P (Palm Oil)**: Optimal bandwidth $p=5.32$, robust statistic $M_{robust}=1.85$, p-value = **0.0324**.
    *   **部分品种第四矩理论收敛受限 / Fourth-Moment Convergence Constraints** (基于 / based on `02_best_model_by_symbol.csv` 与 / and `10_model_health_summary.csv`)：
        *   **中文**：检测发现 **AG (沪银)**（$\nu = 3.1640$）、**CF (棉花)**（$\nu = 3.2287$）、**M (豆粕)**（$\nu = 3.8361$）、**RU (橡胶)**（$\nu = 3.3530$）和 **SN (沪锡)**（$\nu = 3.7399$）共 5 个品种的最优模型自由度估计值 $\nu \le 4$，触发了 `hl_moment_condition_ok = False` 警报，表明其理论第四矩（峰度）发散，谱检验的标准渐进方差推导在数学上受限。
        *   **English**: Five contracts—**AG (Silver)** ($\nu = 3.1640$), **CF (Cotton)** ($\nu = 3.2287$), **M (Soymeal)** ($\nu = 3.8361$), **RU (Rubber)** ($\nu = 3.3530$), and **SN (Tin)** ($\nu = 3.7399$)—exhibit optimal model degrees of freedom $\nu \le 4$. This triggers the `hl_moment_condition_ok = False` alert, indicating that their theoretical kurtosis is infinite, which mathematically restricts the asymptotic variance derivations of the spectral test.
    *   **谱检验在有限样本下表现保守 / Conservative Finite-Sample Performance of the Spectral Test** (基于 / based on `15_hong_lee_monte_carlo_size_summary.csv`)：
        *   **中文**：以最优估计模型为数据生成过程（DGP）运行 100 次蒙特卡洛 Size 仿真，在 5% 的名义显著性水平下，AL（GARCH-t）的经验第一类错误拒绝率为 **1.00%**，AG（EGARCH-t）的经验拒绝率为 **0.00%**，表明该检验在有限样本中实际第一类错误偏低，表现相对保守。
        *   **English**: Utilizing the optimal fitted specifications as the Data Generating Process (DGP) for 100 Monte Carlo Size simulations at a 5% nominal significance level, the empirical Type I error rate is **1.00%** for AL (GARCH-t) and **0.00%** for AG (EGARCH-t), demonstrating that the test is statistically conservative in finite samples.
    *   **动态 VaR 预测回测准确度极高 / High Accuracy in Dynamic VaR Forecasting** (基于 / based on `05_var_backtest_by_symbol.csv`)：
        *   **中文**：在 20 个品种的 VaR 双向回测中，95% VaR 的 Long / Short 端 Kupiec POF 检验通过率分别为 **18/20** 和 **17/20**，平均违约率分别为 **4.91%** 和 **4.82%**；99% VaR 的 Long / Short 端通过率分别为 **17/20** 和 **19/20**，平均违约率分别为 **0.74%** 和 **0.93%**，充分印证了 GARCH 族模型的动态风险刻画能力。
        *   **English**: Kupiec POF backtests on 20 contracts show VaR success rates of **18/20** (Long) and **17/20** (Short) at the 95% level (mean breach rates: **4.91%** and **4.82%**), and **17/20** (Long) and **19/20** (Short) at the 99% level (mean breach rates: **0.74%** and **0.93%**), validating the strength of GARCH-family models in dynamic risk estimation.
    *   **条件波动率及仓位参考因子横截面分化 / Cross-Sectional Dispersion in Volatility States and Position Scaling** (基于 / based on `06_current_vol_state_and_position_scaling.csv`)：
        *   **中文**：最新数据日（2026年6月18日）品种条件波动率分化明显：**AG (沪银)** 和 **MA (甲醇)** 处于极端高波状态（条件波动率分别为 **3.805%** 和 **2.884%**，分位数分别为 **95.86%** 和 **96.61%**），其仓位参考因子分别收缩至 **0.417x** 和 **0.566x**；而 **AL (沪铝)** 处于常态波动状态（条件波动率 **0.880%**，分位数 **38.71%**），仓位释放至 **1.091x**；**I (铁矿石)** 处于极端低波状态（条件波动率 **1.103%**，分位数 **1.34%**），仓位参考因子释放至 capped 上限 **1.500x** (原始值为 **2.007x**)。
        *   **English**: For the latest trading day (June 18, 2026), conditional volatility varies widely. **AG (Silver)** and **MA (Methanol)** are in extreme high-volatility states (conditional volatilities: **3.805%** and **2.884%**, percentiles: **95.86%** and **96.61%**), compressing their position scaling factors to **0.417x** and **0.566x**. Conversely, **AL (Aluminum)** is in a normal volatility state (conditional volatility: **0.880%**, percentile: **38.71%**), expanding its exposure scale to **1.091x**. **I (Iron Ore)** lies in an extreme low-volatility state (conditional volatility: **1.103%**, percentile: **1.34%**), pushing its scaling factor to the capped limit of **1.500x** (raw scale: **2.007x**).

---

## 三、 Crypto_Pricing —— 加密资产多维度定价与下沿估值 / Multidimensional Valuation and Lower-Bound Pricing for Crypto Assets

*   **研究背景 / Research Background**：
    *   **中文**：针对无现金流、无传统估值锚的加密资产（BTC），复刻与拓展 **Bhambhwani et al. (2019, BDK)**（链上基本面与网络价值锚定）、**Biais et al. (2023)**（均衡交易便利与折价层）以及 **Liu & Tsyvinski (2021)**（动量与注意力折价层）三篇文献，构建具备强容错与降级能力的级联下沿估值系统。
    *   **English**: Replicates and extends the core frameworks of **Bhambhwani et al. (2019, BDK)** (on-chain fundamentals and network value anchors), **Biais et al. (2023)** (equilibrium convenience yields and transaction friction discounts), and **Liu & Tsyvinski (2021)** (momentum and attention-based risks) to construct a cascade downside valuation system with adaptive downgrade and risk-control capabilities for crypto assets (BTC) lacking traditional cash flows.

*   **框架与流程 / Framework & Workflow**：
    *   **主控工作流与采集校验 / Pipeline Control & Validation**：
        *   **中文**：利用 `pipeline.py` 串联工作流。通过 `fetchers.py` 从 CoinGecko、Binance、Blockchain.com、Coin Metrics 等多源抓取日频特征，并由 `validator.py` 执行多源 Gap 校验与延迟相关性（Spearman）筛选，输出 `Strict-tier`（严格验证）与 `Research-tier`（研究代理级）双轨特征库。
        *   **English**: Utilizes `pipeline.py` to coordinate workflows. Fetches daily features from CoinGecko, Binance, Blockchain.com, Coin Metrics, and other sources via `fetchers.py`. Performs multi-source gap and lead-lag Spearman correlation checks in `validator.py` to output dual-track databases: `Strict-tier` (strictly validated) and `Research-tier` (research proxy).
    *   **基本面锚定与 OLS 重校准 / Fundamental Anchor & OLS Recalibration**：
        *   **中文**：`pricing.py` 实现 BDK 二元 Log-Log 基准模型并支持样本内 OLS 动态重校准以捕获最新周期的弹性系数，并在特定压力目标下缩放算力与活跃地址生成基本面底座 $V_{BDK}$。
        *   **English**: Implements the BDK log-log baseline specification in `pricing.py`, supporting in-sample OLS dynamic recalibration to capture cyclical elasticity drift. Computes the fundamental anchor $V_{BDK}$ by scaling hashrate and active addresses under specific stress targets.
    *   **交易摩擦与行为情绪折价 / Friction & Behavioral Discounts**：
        *   **中文**：加权整合交易收益/成本/准入/崩盘风险计算 $S_{Biais}$ 评分（对崩盘风险整体进行上限归零过滤牛市噪点），加权整合动量/注意力/活跃增长计算 $S_{Liu}$ 评分（对单源研究级注意力进行 0.60 权重打折）；通过连续指数下行映射生成折价系数。
        *   **English**: Computes the composite $S_{Biais}$ score by weighting transaction benefits, costs, market access, and drawdown risks (capping the crash-risk component at 0.0 to filter out bull market peaks). Computes the $S_{Liu}$ score by weighting price momentum, ordinary attention, negative attention, and activity growth (penalizing single-source Wikipedia attention with a 0.60 weight reduction). Generates discount coefficients via continuous exponential downside mappings.

*   **数据实证结论 / Empirical Findings** (基于最新样例输出 / based on the latest sample output `btc_three_paper_framework_pricing_v1_3.csv`，当时 BTC 价格约为 10.5 万美元)：
    *   **基本面公允价估算与弹性表现 / Fundamental Fair Value Estimation**：
        *   **中文**：当前样本内 OLS 重校准的算力与活跃地址弹性均为正，系统成功切换至 `full_ols_insample` 校准模式。全样本有效交叉验证观测天数达 **97 天**（无需额外天数惩罚）。模型估算当前比特币的长期 Log-Log 基本面公允价值为 **71,588.21 美元**（实际市场价存在约 33% 泡沫溢价）。
        *   **English**: The OLS-recalibrated elasticities for hashrate and network size are both positive, successfully triggering the `full_ols_insample` calibration mode. Validated observations over the rolling window total **97 days** (requiring no sample size width penalty). The model estimates BTC's long-term baseline fair value at **$71,588.21** (indicating an approximate 33% bubble premium over the actual market price).
    *   **行为折价层发挥差异化作用 / Behavioral Discounts**：
        *   **中文**：在当前牛市高位状态下，Biais 评分得分为 **1.058**（收益与风控分量主导），对应交易折价系数为 **1.00**（无折价，即网络交易便利效能高）。而 Liu 评分受 7D/14D 动量反转与研究级注意力偏弱拖累，得分为 **-0.405**，对应动量注意力折价系数为 **0.960**（约打 96 折）。系统最终以级联联合折价系数 **0.960** 入模。
        *   **English**: Under current high-market conditions, the Biais score stands at **1.058** (dominated by transaction activity and low drawdowns), yielding a transaction discount coefficient of **1.00** (no discount, indicating strong network convenience utility). However, the Liu score is dragged down by weak momentum and research-tier attention, scoring **-0.405** and yielding an attention discount of **0.960** (a 4% discount). The cascade pricing engine applies a joint discount coefficient of **0.960**.
    *   **多情景价格下沿区间输出 / Pricing floors under Stress Scenarios**：
        1.  **基础压力下沿 / Base Pressure**：
            *   **中文**：在算力收缩至 919.22 EH/s、地址收缩至 46.49 万的轻度压力下，价格下沿支撑点为 **57,605.37 美元**，对应估值区间为 `[51,844.83, 63,365.90]`；
            *   **English**: Under a mild contraction (hashrate: 919.22 EH/s, addresses: 46.49k), the strict lower point is **$57,605.37**, corresponding to a valuation range of `[$51,844.83, $63,365.90]`.
        2.  **核心估值下沿（常规参考） / Core Lower Bound (Recommended Reference)**：
            *   **中文**：在算力降至 891.08 EH/s、地址降至 45.07 万（15% 历史分位）的核心压力下，下沿支撑点为 **52,312.48 美元**，对应估值区间为 `[47,081.23, 57,543.72]`（带宽 $W = 0.10$）；
            *   **English**: Under core stress (hashrate: 891.08 EH/s, addresses: 45.07k, representing the 15th percentile), the strict lower point is **$52,312.48**, corresponding to a valuation range of `[$47,081.23, $57,543.72]` (with width $W = 0.10$).
        3.  **严重压力下沿 / Severe Lower Bound**：
            *   **中文**：在 5% 历史极值下，下沿点降至 **44,239.87 美元**，对应估值区间为 `[39,815.89, 48,663.86]`；
            *   **English**: Under severe stress (5th percentile), the strict lower point is **$44,239.87**, corresponding to a range of `[$39,815.89, $48,663.86]`.
        4.  **极端尾部下沿 / Extreme Tail**：
            *   **中文**：在 5% 历史极值加 85% 当前上限下压（无二次重压）的黑天鹅底场景下，估值下沿低至 **36,931.48 美元**，对应区间为 `[33,238.33, 40,624.63]`；
            *   **English**: Under a black-swan panic (5th percentile with an 85% current cap, removing double-press), the strict lower point drops to **$36,931.48**, corresponding to a range of `[$33,238.33, $40,624.63]`.

---

## 四、 规划中研究模块与后续方向 / IV. Planned Research Modules and Future Directions

本项目后续将进一步探索以下两个量化金融课题，并逐步完成相关学术文献的复现与拓展检验：
The project will further explore the following two quantitative finance topics, progressively completing the replication and extension of relevant academic literature:

### 1. 动量 / 反转 / 趋势跟踪 / Momentum, Reversal, and Trend-Following
*   **研究主题 / Research Topics**：价格延续、均值反转、趋势规则构建、波动率自适应调整以及两状态机制切换（Regime-Switching）。
    Price continuation, mean reversion, trend rule construction, volatility-adaptive timing adjustments, and two-state regime-switching (Regime-Switching) models.
*   **核心文献 / Core Literature**：
    *   *Ammann, Moellenbeck, and Schmid (2011)* — Feasible Momentum Strategies in the US Stock Market
    *   *Baltas and Kosowski (2012)* — Improving Time-Series Momentum Strategies: The Role of Trading Signals and Volatility Estimators
    *   *Caporale and Plastun (2020)* — Momentum Effects in the Cryptocurrency Market After One-Day Abnormal Returns
    *   *Dobrynskaya (2021)* — Cryptocurrency Momentum and Reversal
    *   *Dudler, Gmuer, and Malamud (2014)* — Risk Adjusted Time Series Momentum
    *   *Karassavidis, Kateris, and Ioannidis (2025)* — Quantitative Evaluation of Volatility-Adaptive Trend-Following Models in Cryptocurrency Markets
    *   *Li et al. (2021)* — MAX Momentum in Cryptocurrency Markets
    *   *Tayal (2009)* — Regime Switching and Technical Trading with Dynamic Bayesian Networks in High-Frequency Stock Markets
    *   *Zakamulin and Giner (2022)* — Optimal Trend Following Rules in Two-State Regime-Switching Models

### 2. 机器学习 / AI / 预测模型 / Machine Learning, AI, and Forecasting Models
*   **研究主题 / Research Topics**：高维资产预测、可解释人工智能（XAI）在资产配置中的应用、深度强化学习交易系统以及多模型（如决策树、神经网络等）非线性预测比较。
    High-dimensional asset forecasting, Explainable AI (XAI) in asset allocation, deep reinforcement learning trading systems, and non-linear forecasting model comparisons.
*   **核心文献 / Core Literature**：
    *   *Afolabi et al. (2017)* — Hierarchical Meta-Learning in Time Series Forecasting for Improved Inference-Less Machine Learning
    *   *Babaei, Giudici, and Raffinetti (2022)* — Explainable Artificial Intelligence for Crypto Asset Allocation
    *   *Campisi, Muzzioli, and De Baets (2024)* — A Comparison of Machine Learning Methods for Predicting the Direction of the US Stock Market on the Basis of Volatility Indices
    *   *Chandak et al. (2019)* — Learning Action Representations for Reinforcement Learning
    *   *Gu, Kelly, and Xiu (2020)* — Empirical Asset Pricing via Machine Learning
    *   *Shen, Jiang, and Zhang (2012)* — Stock Market Forecasting Using Machine Learning Algorithms
    *   *Tran, Pham-Hi, and Bui (2023)* — Optimizing Automated Trading Systems with Deep Reinforcement Learning

---

## 五、 目录结构说明 / V. Repository Directory Structure

```text
QuantStrat/
├── README.md                                          # 根目录说明文档（中英文对照）/ Root repository guide (this file, bilingual)
├── QuantStrat x UIUC MSFE.pdf                         # UIUC MSFE 夏季项目合作及 bibliography 课件 / Slide deck for UIUC MSFE summer project & bibliography
├── Commodity_Futures_Raw_Data/                        # 商品期货原始价格与特征面板数据 (27个品种) / Commodity futures raw price & feature panel data (27 symbols)
│   ├── AG.csv, AL.csv, ...
│   └── futures_panel.csv                              # 商品期货横截面主面板 / Commodity futures cross-sectional main panel
├── Market_Anomalies——市场异象/                        # 模块一：技术异象、活跃度衰减与发表后衰减 / Module 1: Technical anomalies, activity decay, post-pub decay
│   ├── 02_vol_sorted_technical_anomaly.ipynb          # 波动率排序横截面技术分析异象回测 / Vol-sorted cross-sectional technical anomaly backtesting
│   ├── 03_liquidity_attenuation.ipynb                 # 交易活跃度对技术异象的削弱检验 / Trading activity attenuation testing on anomalies
│   ├── 04_post_selection_decay.ipynb                  # 策略选择后的样本外与伪实盘衰减测试 / Post-strategy selection OOS and pseudo-live decay tests
│   ├── *.csv                                          # 策略与回归 of 运行结果表 / CSV files storing strategies and regression outcomes
│   └── README.md                                      # 模块一详细设计与CSV发现文档 / Module 1 detailed design & CSV findings document
└── Volatility_Time_Series——波动率&时间序列检验/       # 模块二：波动率建模与 Hong-Lee 谱检验风控模块 / Module 2: Volatility modeling & Hong-Lee spectral risk control
    ├── Traditional_Model_Selection_Sugar.ipynb        # 单合约复刻论文及全流程检验 (白糖主力) / Single contract replication & full pipeline diagnostic (Sugar SR)
    ├── hong_lee_20_contracts.ipynb                    # 多合约拓展运行脚本 (20个商品期货主力) / Multi-contract extension execution script (20 symbols)
    ├── *.csv                                          # 20合约波动率建模与健康谱检验表 / 20-contract volatility models & spectral diagnostic tables
    └── README.md                                      # 模块二详细设计、CSV发现与风控逻辑文档 / Module 2 detailed design, findings & risk control document
├── Crypto_Pricing—— 加密货币定价/                     # 模块三：BTC多维定价与下沿估值模块 / Module 3: BTC multidimensional pricing & downside valuation
    ├── btc_unified_pricing_model/                     # Python 核心模型包 (fetchers, validator, pricing) / Python core package
    ├── tests/                                         # 单元测试模块 / Unit testing module
    └── README.md                                      # 模块三详细设计文档 / Module 3 detailed design document
```
