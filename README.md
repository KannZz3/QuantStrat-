# QuantStrat: Quantitative Finance Research Platform: Replication and Extension (UIUC MSFE 2026)

This project is a collaborative quantitative finance research initiative between **QuantStrat** and the **Master of Science in Financial Engineering (MSFE)** program at the **University of Illinois Urbana-Champaign (UIUC)** for Summer 2026. Focusing on active contracts in the Chinese commodity futures market, the project adopts rigorous academic methodologies to replicate and extend literature-anchored hypotheses. It constructs a quantitative research system encompassing commodity futures behavioral anomalies, frequency-domain diagnostics for high-order heteroscedasticity, and dynamic risk management.

本项目是 **QuantStrat** 与**伊利诺伊大学金融工程硕士项目（UIUC MSFE）** 2026年夏季的量化金融 research 合作项目。项目主要针对**中国商品期货市场主力合约**，采用学术规范与研究方法，以文献为锚进行复现与拓展检验，构建了一套包含**商品期货行为金融异象、高阶异方差频域检验与动态风险管理**的量化研究参考系统。

Currently, four core research modules and empirical analyses are complete, and two future research directions are planned.

目前项目已基本完成4个核心研究模块的开发与实证分析，并规划了未来深入研究的两个方向。

---

## 1. Momentum, Reversal, and Trend-Following in Commodity Futures / Momentum_Reversal_Trend-Following —— 动量、反转与趋势跟踪

*   **Research Background / 研究背景**：
    *   Replicates and extends the commodity futures momentum/reversal/trend-following literature to systematically answer three practical questions for Chinese commodity futures: (Q1) do the signals exist and are they statistically validated? (Q2) how long do the signals typically last (duration distribution)? (Q3) what is the survival probability of an active signal over future horizons? All conclusions are derived exclusively from full-history panel data covering 11 commodity futures contracts.
    *   针对中国商品期货市场，复刻与拓展动量/反转/趋势跟踪文献，系统回答三个实战问题：（Q1）信号是否存在并经统计验证？（Q2）信号历史上持续多久（持续期分布）？（Q3）当前活跃信号未来 N 期内的存活概率？所有结论严格基于覆盖 11 个主力合约的全历史面板数据。

*   **Framework & Workflow / 框架与流程**：
    *   Three sub-modules each follow an identical three-question pipeline: **Q1 Existence Model** (best-model selection via Newey-West t-statistics with bootstrap p-values, full-period confirmed/candidate grading), **Q2 Duration Distribution** (episode-level Kaplan-Meier style active-duration statistics: mean, median, Q25/Q75), and **Q3 Survival / End-Risk** (forward horizon-conditional ending probabilities from historical episodes). Momentum uses J-day look-back / K-day skip / validated episode windows; Reversal applies three detector types (FastREV, TSREV, RAREV) with independent L/K parameters; Trend uses h-day rolling channel with K-day confirmation threshold.
    *   三个子模块均遵循相同的三问流水线：**Q1 存在性模型**（Newey-West t 统计量 + bootstrap p 值，全历史品种级 CONFIRMED / CANDIDATE 评级）、**Q2 持续期分布**（episode 级 Kaplan-Meier 式有效活跃期统计：均值、中位数、Q25/Q75）、**Q3 存活/结束概率**（基于历史 episode 的前瞻 N 期条件结束概率）。动量使用 J 日回看 / K 日跳过 / 验证窗口；反转通过 FastREV / TSREV / RAREV 三类探测器（独立 L/K 参数）；趋势使用 h 日滚动通道 + K 日确认阈值。

*   **Empirical Findings / 数据实证结论**：
    *   **Trend-Following Is the Most Pervasive and Reliable Signal / 趋势跟踪是三类信号中覆盖最广、统计最稳健的** (based on / 基于 `trend_hist_q1_existence_model.csv` & `trend_hist_q2_duration_distribution.csv`)：
        *   Across all 11 commodity futures, **10/11** pass CONFIRMED or CANDIDATE grading (only EB is DIAGNOSTIC_ONLY at the medium-difficulty threshold), and **4/11** reach full CONFIRMED status. The full-history `trend_exists_rate` ranges from **60.45%** to **72.18%** (median **68.28%**), meaning commodity futures are in a directional trend state for more than 60% of all trading days. The `trend_established_rate` (strictly validated trend episodes) ranges from **51.47%** to **69.77%** (median **65.13%**). Among HIGH-reliability contracts (20 direction-side pairs), mean active trend duration spans from **3.5 to 12.7 days** depending on the commodity and direction, with soybean meal (M UP: mean **11.3 days**, median **7 days**; M DOWN: mean **12.7 days**, median **10 days**) and PVC (V UP: mean **11.0 days**, median **7 days**; V DOWN: mean **11.9 days**, median **10 days**) showing the longest trend episodes. Short-cycle commodities such as White Sugar (SR UP: mean **4.1 days**, median **1 day**; SR DOWN: mean **3.5 days**, median **1 day**) exhibit the shortest trend durations.
        *   全部 11 个主力合约中，**10/11** 通过 CONFIRMED 或 CANDIDATE 评级（仅 EB 在中等难度阈值下为 DIAGNOSTIC_ONLY），其中 **4/11** 达到 CONFIRMED。全历史 `trend_exists_rate` 范围为 **60.45%～72.18%**（中位数 **68.28%**），表明商品期货超过 60% 的交易日处于方向性趋势状态。`trend_established_rate`（严格验证趋势 episode）范围为 **51.47%～69.77%**（中位数 **65.13%**）。在 HIGH 可靠性合约的 20 个方向对中，趋势活跃期均值为 **3.5～12.7 天**，其中豆粕（M 多方均值 **11.3 天**，中位数 **7 天**；M 空方均值 **12.7 天**，中位数 **10 天**）与 PVC（V 多方均值 **11.0 天**，中位数 **7 天**；V 空方均值 **11.9 天**，中位数 **10 天**）趋势持续时间最长；白糖（SR 多方均值 **4.1 天**，中位数 **1 天**；SR 空方均值 **3.5 天**，中位数 **1 天**）趋势持续时间最短。
    *   **Momentum Exists in High Frequency but Dissipates Rapidly / 动量信号高频存在但衰减极快** (based on / 基于 `momentum_hist_q1_existence_model.csv` & `momentum_hist_q2_duration_distribution.csv`)：
        *   **7/11** commodity futures reach CONFIRMED status and **9/11** pass CONFIRMED or CANDIDATE grading. The full-history `mom_exists_rate` ranges from **19.47%** to **51.94%** (median **42.98%**). However, momentum signals are characteristically short-lived: among HIGH-reliability contracts (10 direction-side pairs), the mean active duration is only **1.5 to 2.6 days** (median universally **1–2 days**). White Sugar Pulp (SP) shows the longest momentum episodes (UP mean **11.8 days**, DOWN mean **9.5 days**), but with only LOW duration reliability due to small sample sizes. The HIGH-reliability group (AG, CF, M, SA, V) all have mean durations ≤ **2.6 days**, confirming that commodity futures momentum is a rapid-reversion short-duration phenomenon. The per-episode end-risk rate (probability of momentum ending within the next observation) for HIGH-reliability contracts ranges from **36.4% to 48.0%**, consistent with the short average duration.
        *   **7/11** 个主力合约达到 CONFIRMED，**9/11** 通过 CONFIRMED 或 CANDIDATE 评级。全历史 `mom_exists_rate` 范围为 **19.47%～51.94%**（中位数 **42.98%**）。然而动量信号持续期极短：HIGH 可靠性合约（10 个方向对）的活跃期均值仅为 **1.5～2.6 天**（中位数全部为 **1～2 天**），白糖纸浆（SP）均值最长（多方 **11.8 天**、空方 **9.5 天**，但样本量小仅 LOW 可靠性），HIGH 可靠性组（AG、CF、M、SA、V）均值均不超过 **2.6 天**，证实商品期货动量是快速均值回归的短持续期现象。HIGH 可靠性合约的单期结束概率（end_risk_rate）为 **36.4%～48.0%**，与短均值持续期高度吻合。
    *   **Reversal Signal Exists in Select Commodities with Highly Heterogeneous Duration / 反转信号存在于少数品种且持续期高度异质** (based on / 基于 `reversal_hist_q1_existence_model.csv` & `reversal_hist_q2_duration_distribution.csv`)：
        *   **2/11** reach CONFIRMED (M via TSREV and SR via TSREV) and **9/11** pass CONFIRMED or CANDIDATE grading, but **2** remain DIAGNOSTIC_ONLY (EB and LH), whose `rev_validated_rate` = **0.000**. The full-history `rev_signal_rate` ranges from **3.77%** to **89.80%** (median **7.78%**), and `rev_validated_rate` ranges from **0.00%** to **85.71%** (median **3.10%**), revealing an extreme cross-sectional disparity: pure alkali (SA) via RAREV generates validated reversal observations on **85.71%** of days, while glass (FG) and cotton (CF) achieve validated rates of only **1.89%** and **3.10%** respectively. Among the two HIGH-reliability contracts (SR), the TSREV mean active duration is extremely short at **1.3 days** (median **1 day**), consistent with rapid mean reversion; while M (TSREV, MEDIUM reliability) shows a mean of **10.7–12.3 days** (median **6 days**), indicating a slower-cycle reversal structure.
        *   **2/11** 达到 CONFIRMED（M 使用 TSREV 和 SR 使用 TSREV），**9/11** 通过 CONFIRMED 或 CANDIDATE 评级，但 **2** 个品种（EB、LH）仍为 DIAGNOSTIC_ONLY，其 `rev_validated_rate` = **0.000**。全历史 `rev_signal_rate` 范围为 **3.77%～89.80%**（中位数 **7.78%**），`rev_validated_rate` 范围为 **0.00%～85.71%**（中位数 **3.10%**），横截面分化极端：纯碱（SA）通过 RAREV 在 **85.71%** 的交易日生成有效反转观测，而玻璃（FG）和棉花（CF）的验证率仅为 **1.89%** 和 **3.10%**。在 HIGH 可靠性品种（SR）中，TSREV 均值活跃期极短仅 **1.3 天**（中位数 **1 天**），与快速均值回归一致；豆粕（M，TSREV，MEDIUM 可靠性）均值为 **10.7～12.3 天**（中位数 **6 天**），呈现慢周期反转结构。

---

## 2. Technical Anomalies, Activity Attenuation, and Post-Publication Decay in Commodity Futures / Market_Anomalies —— 商品期货技术分析异象、活跃度衰减与发表后衰减

*   **Research Background / 研究背景**：
    *   Replicates and extends the core hypotheses of **Han et al. (2013)** (cross-sectional excess returns of technical indicators under high volatility), **Chordia et al. (2014)** (attenuation of capital market anomalies by liquidity and trading activity), and **McLean & Pontiff (2016)** (predictive return decay post academic publication and strategy selection) to test the stability of technical anomalies in the Chinese commodity futures market.
    *   复刻与拓展 **Han et al. (2013)**（高波动技术分析横截面超额收益）、**Chordia et al. (2014)**（流动性/活跃度对资本市场异象的削弱）以及 **McLean & Pontiff (2016)**（学术发表及策略筛选后收益预测性衰减）的核心假说，测试中国商品期货市场中的技术异象稳定性。

*   **Framework & Workflow / 框架与流程**：
    *   **02_vol_sorted_technical_anomaly.ipynb**：
        *   Computes the 60-day rolling historical volatility (`rv_60_signal`) on each signal day $s$ across a daily panel, grouping contracts cross-sectionally into `Low / Mid / High` volatility buckets (requiring at least 9 eligible assets daily). Generates `long_flat` / `long_short` position signals using four classes of technical indicators (MA10 to MA120) based on day $s$ closing prices. Positions are executed on day $t = s + 1$ (delayed trading) and performance is evaluated using the forward 1D return (`fwd_ret_1d`) net of a 5 bps one-way transaction cost to construct High-Minus-Low (HML) portfolio returns.
        *   以日频面板为基础，计算各品种信号日 $s$ 的 60 日滚动历史波动率 `rv_60_signal` 并将其横截面划分为 `Low / Mid / High` 三个波动率桶（要求每日标的不少于 9 个）；以 $s$ 日收盘价计算四类技术指标（MA10至MA120）的 `long_flat`/`long_short` 仓位信号；于 $t = s + 1$ 日（延迟交易）执行并以 Forward 1D 收益率 `fwd_ret_1d` 计算策略日收益（扣除单边 5 bps 成本），构建 HML 组合收益。
    *   **03_liquidity_attenuation.ipynb**：
        *   Synthesizes a composite `activity_score` from the z-scores of trading volume, open interest, and turnover to categorize assets into `Low / Mid / High` activity buckets on signal days. Conducts double-sorting portfolio return analysis and OLS regressions with interaction terms using HC1 heteroscedasticity-robust standard errors.
        *   根据成交量、持仓量及成交额的 z-score 合成 `activity_score`，在信号日分置为 `Low / Mid / High` 活跃度桶；与 HML 收益对齐后进行双重分桶收益分析与包含交互项的衰减 OLS 回归（计算 HC1 异方差稳健标准误）。
    *   **04_post_selection_decay.ipynb**：
        *   Generates a candidate pool of 26 strategies across MA, TSMOM, BREAKOUT, and REVERSAL families. Splits the sample into In-Sample (IS: 2016-01-05 to 2020-12-31), Out-of-Sample (OOS: 2021-01-01 to 2023-12-31), and Pseudo-Live (2024-01-01 onward) periods (isolating forward return windows to prevent data leakage). Selects the Top 10 strategies based on IS Sharpe ratios and quantifies their performance decay across splits.
        *   生成覆盖 MA、TSMOM、BREAKOUT、REVERSAL 四大类族的 26 个候选策略；切分样本为样本内（IS: 2016-01-05 至 2020-12-31）、样本外（OOS: 2021-01-01 至 2023-12-31）与伪实盘（Pseudo-Live: 2024-01-01 起）区间（隔离收益实现窗口防范数据泄露）；以 IS 收益率筛选 Top 10 策略并评估其表现跨区间衰减幅度。

*   **Empirical Findings / 数据实证结论**：
    *   **High-Volatility Technical Anomalies Lack Statistical Significance / 高波动技术异象不具备稳定显著性** (based on / 基于 `02_high_minus_low_summary.csv` and / 与 `02_monotonic_flags.csv`)：
        *   Out of the 8 technical trading strategies, only 5 yield positive annualized HML excess returns (MA10 long_flat: **0.65%**, MA20 long_flat: **4.30%**, MA20 long_short: **5.27%**, MA60 long_flat: **1.75%**, MA60 long_short: **0.18%**), and all 8 HML returns are statistically insignificant at the 5% significance level ($|t| < 1.96$). The MA20 long_short strategy shows the strongest relative performance (HML annualized return: **5.27%**, t-statistic: **0.91**). Conversely, the long-term MA120 long_short strategy exhibits an HML reversal (annualized return: **-10.23%**, t-statistic: **-1.77**).
        *   在 8 个技术交易策略中，仅 5 个策略的 HML 年化超额收益为正（MA10 long_flat 为 **0.65%**，MA20 long_flat 为 **4.30%**，MA20 long_short 为 **5.27%**，MA60 long_flat 为 **1.75%**，MA60 long_short 为 **0.18%**），且全部 8 个策略的 HML 收益在 5% 显著性水平下统计上均不显著（$|t| < 1.96$）。MA20 long_short 策略表现相对最强（HML 年化收益为 **5.27%**，t 统计量为 **0.91**）。而在长周期策略 MA120 long_short 上，HML 出现反转（年化收益为 **-10.23%**，t 统计量为 **-1.77**）。
    *   **Trading Activity Directionally Dampens HML Returns / 交易活跃度对异象呈现方向性弱削弱** (based on / 基于 `03_activity_attenuation_summary.csv` and / 与 `03_activity_flags.csv`)：
        *   Among the 24 HML tests for net returns, **18** (representing **75.00%**) directionally exhibit narrowing HML spreads as trading activity increases, though none are statistically significant ($|t| < 1.96$). For example, the HML annualized return of the MA120 long_short strategy contracts from **1.20%** under low activity to **-16.44%** under high activity—a decay of **-22.24%** (t-statistic: **-1.47**).
        *   在 24 个衡量净收益 HML 的活跃度衰减测试中，有 **18** 个（占比 **75.00%**）在方向上表现出 HML 收益随活跃度上升而收窄的特征，但统计上均不显著（$|t| < 1.96$）。例如，MA120 long_short 策略的 HML 年化收益从低活跃度下的 **1.20%** 收缩至高活跃度下的 **-16.44%**，衰减幅度达 **-22.24%**，对应的 t 统计量为 **-1.47**。
    *   **Impact of Liquidity and Volatility on Trend Returns / 流动性与波动率对趋势收益的回归冲击** (based on / 基于 `03_activity_interaction_regression.csv`)：
        *   OLS regressions with interaction terms reveal that the composite `activity_score` acts as a significant positive driver for medium-to-long term trend strategies (coefficient for MA60 long_short: $3.18 \times 10^{-4}$, t-value: **3.33**; coefficient for MA120 long_short: $3.28 \times 10^{-4}$, t-value: **3.44**). Furthermore, for the long-term MA120 long_short strategy, being in a high-volatility state (`high_vol_dummy`) exerts a significant negative shock on returns (coefficient: $-4.79 \times 10^{-4}$, t-value: **-2.39**), reflecting the performance drag on trend-following strategies due to whipsaws in highly volatile markets.
        *   包含交互项的 OLS 回归表明，交易活跃度评分 (`activity_score`) 是中长线趋势策略（MA60, MA120）收益的显著正向驱动力（对 MA60 long_short 的系数为 $3.18 \times 10^{-4}$，t 值为 **3.33**；对 MA120 long_short 的系数为 $3.28 \times 10^{-4}$，t 值为 **3.44**）。此外，对于长线策略（MA120 long_short），处于高波状态 (`high_vol_dummy`) 对其收益有显著的负向冲击（系数为 $-4.79 \times 10^{-4}$，t 值为 **-2.39**），反映了长线趋势跟踪策略在高波动率市场中容易遭受双边洗盘（whipsaws）导致损耗。
    *   **Out-of-Sample Performance Decay Due to Selection Bias / 选择偏差与样本外表现的系统性大幅衰减** (based on / 基于 `04_post_selection_decay_summary.csv` and / 与 `04_all_strategy_decay_summary.csv`)：
        *   In the pool of 26 candidates, only **2** strategies show robust performance across all periods (ROBUST): `BREAKOUT_120_long_flat` (IS Sharpe: **0.26** → OOS: **0.52** → Pseudo-Live: **0.49**) and `MA_60_long_short` (IS Sharpe: **0.18** → OOS: **0.16** → Pseudo-Live: **0.19**). These were not selected in the Top 10 due to moderate IS performance. Conversely, the selected Top 10 strategies suffer from severe selection bias: their mean Sharpe ratio decays from **0.68** during the IS phase to **0.35** in the OOS phase, and further declines to **0.11** in the Pseudo-Live phase (medians drop from **0.67** to **0.40** and **0.07**, respectively). The median Sharpe ratio retention rate is only **55.47%** in OOS and **16.56%** in Pseudo-Live.
        *   在 26 个候选策略池中，仅有 **2** 个策略在全区间表现稳健（ROBUST）：`BREAKOUT_120_long_flat`（IS 夏普 **0.26** → OOS **0.52** → Pseudo-Live **0.49**）和 `MA_60_long_short`（IS 夏普 **0.18** → OOS **0.16** → Pseudo-Live **0.19**）。它们由于在样本内（IS）表现适中而未能入选 Top 10。相反，IS 筛选出的 Top 10 策略呈现出严重的选择偏差（Selection Bias），其夏普比率均值从 IS 阶段的 **0.68** 大幅降至 OOS 阶段的 **0.35**，并在 Pseudo-Live 阶段进一步降至 **0.11**（中位数分别从 **0.67** 降至 **0.40** 和 **0.07**）；各策略夏普比率保留率中位数在 OOS 和 Pseudo-Live 阶段分别仅为 **55.47%** 和 **16.56%**。

---

## 3. Volatility Modeling and Hong-Lee Spectral Adequacy Diagnostics / Volatility_Time_Series —— 波动率建模与 Hong-Lee 谱充分性检验

*   **Research Background / 研究背景**：
    *   Replicates and extends the generalized spectral test for volatility model adequacy proposed by **Hong & Lee (2017)**. Evaluates the finite-sample statistical properties and dynamic risk-control logic when scaling the original single-contract design to a multi-contract framework across Chinese commodity futures.
    *   复刻与拓展 **Hong & Lee (2017)** 的广义谱波动率模型充分性检验。测试将原论文单合约设计推广至中国商品期货多合约时的有限样本统计特征及动态风控逻辑。

*   **Framework & Workflow / 框架与流程**：
    *   **Model Fitting and Selection / 模型拟合与选择**（`Traditional_Model_Selection_Sugar.ipynb`）：
        *   Fits 19 parameter combinations consisting of Constant/AR(1) mean specifications paired with GARCH, EGARCH11/21, GJR, and TARCH conditional variance equations under Normal, Student-t, Skewed Student-t, and GED error distributions on daily returns of 20 active futures. Selects the optimal model by minimizing the Bayesian Information Criterion (BIC) after filtering via Ljung-Box autocorrelation tests (on standardized residuals $z$ and $z^2$ up to lags 10/20/30) and ARCH-LM tests (up to lag 10).
        *   针对 20 个主力商品期货日收益率，拟合包含常数/AR(1) 均值，结合 GARCH, EGARCH11/21, GJR, TARCH 条件方差，以及 Normal, Student-t, Skewed Student-t, GED 误差分布 of 19 种参数组合；通过标准化残差 Ljung-Box 自相关（$z$ 与 $z^2$ 的 10/20/30 阶滞后）与 ARCH-LM 检验（10阶）过滤后，以 BIC 最小化规则确立最优模型。
    *   **Hong-Lee Generalized Spectral Test / Hong-Lee 广义谱检验**（`hong_lee_20_contracts.ipynb`）：
        *   Constructs a robust spectral density function based on generalized characteristic function residuals. Conducts frequency-domain non-linear heteroscedasticity diagnostics under both fixed bandwidth ($p \approx 21$) and data-driven adaptive bandwidths to compute robust M-statistics and p-values. Runs 100 Monte Carlo Size simulations with Wilson Score 95% confidence intervals.
        *   基于广义特征函数残差构建稳健谱密度函数，在固定带宽（主带宽 $p \approx 21$）与惩罚性数据驱动自适应带宽下，对最优模型进行频域非线性结构异方差检验，计算 robust M 统计量及 p 值；运行 100 次蒙特卡洛 Size 仿真，基于 Wilson Score 方法计算其 95% 置信区间。
    *   **Risk Control Reference / 风险控制参考**：
        *   Estimates 95% and 99% two-way daily VaR and performs Kupiec POF backtests. Computes raw target-volatility position scaling factors (`Raw Scale`) and applies a penalty discount (`Health Multiplier`) if a contract's optimal model is rejected by the spectral test or fails fourth-moment convergence (estimated degrees of freedom $\nu \le 4$).
        *   计算单日 95% 与 99% 双向 VaR 并完成 Kupiec POF 回测；根据目标波动率计算仓位参考系数（`Raw Scale`），当品种被谱检验拒绝（`REJECT`）或因自由度估计值 $\nu \le 4$ 导致第四矩理论不收敛时，自动乘降权折扣系数（`Health Multiplier`）。

*   **Empirical Findings / 数据实证结论**：
    *   **Prevalence of EGARCH Specifications and Non-Normal Tails / EGARCH 族与非正态厚尾假定适用** (based on / 基于 `02_best_model_by_symbol.csv`)：
        *   For **15 out of 20** active commodity futures, the BIC-optimal conditional variance model belongs to the **EGARCH family**, and normal error distributions are rejected across all contracts (14 Student-t, 3 GED, and 3 Skewed Student-t). Model parameters indicate high volatility persistence (e.g., White Sugar SR's optimal EGARCH(1,1)-t model yields $\beta_1 = 0.9900$ and estimated degrees of freedom $\nu = 4.495$; Silver AG yields $\nu = 3.164$).
        *   在 20 个主力商品期货中，有 **15** 个品种 of BIC 最优方差模型为 **EGARCH 族**，且全线排除正态分布（14 个为 Student-t，3 个为 GED，3 个为 Skewed Student-t）。模型参数展现出强波动持续性（例如，白糖 SR 的最优模型 EGARCH(1,1)-t 估计 $\beta_1 = 0.9900$，自由度估计 $\nu = 4.495$；沪银 AG 估计 $\nu = 3.164$）。
    *   **Data-Driven Spectral Test Detects Misspecifications in Traditional Diagnostics' Blind Spots / 数据驱动谱检验精准识别普通检验盲区** (based on / 基于 `13_hong_lee_data_driven_bandwidth_selected-Copy1.csv`)：
        *   Even when standardized residuals pass traditional Ljung-Box and ARCH-LM tests (p > 0.05), the data-driven spectral test **significantly rejects model adequacy for 3 optimal specifications** at the 5% significance level:
            1.  **AU (Gold)**: Optimal bandwidth $p=5.32$, robust statistic $M_{robust}=1.69$, p-value = **0.0455**;
            2.  **I (Iron Ore)**: Optimal bandwidth $p=5.32$, robust statistic $M_{robust}=2.51$, p-value = **0.0061**;
            3.  **P (Palm Oil)**: Optimal bandwidth $p=5.32$, robust statistic $M_{robust}=1.85$, p-value = **0.0324**.
        *   在标准化残差通过传统 Ljung-Box 自相关与 ARCH-LM 检验（p > 0.05）的前提下，自适应数据驱动谱检验在 5% 显著性水平下**显著拒绝了 3 个最优模型的充分性**：
            1.  **AU (沪金)**：最优带宽 $p=5.32$，统计量 $M_{robust}=1.69$，p 值 = **0.0455**；
            2.  **I (铁矿石)**：最优带宽 $p=5.32$，统计量 $M_{robust}=2.51$，p 值 = **0.0061**；
            3.  **P (棕榈油)**：最优带宽 $p=5.32$，统计量 $M_{robust}=1.85$，p 值 = **0.0324**。
    *   **Fourth-Moment Convergence Constraints / 部分品种第四矩理论收敛受限** (based on / 基于 `02_best_model_by_symbol.csv` and / 与 `10_model_health_summary.csv`)：
        *   Five contracts—**AG (Silver)** ($\nu = 3.1640$), **CF (Cotton)** ($\nu = 3.2287$), **M (Soymeal)** ($\nu = 3.8361$), **RU (Rubber)** ($\nu = 3.3530$), and **SN (Tin)** ($\nu = 3.7399$)—exhibit optimal model degrees of freedom $\nu \le 4$. This triggers the `hl_moment_condition_ok = False` alert, indicating that their theoretical kurtosis is infinite, which mathematically restricts the asymptotic variance derivations of the spectral test.
        *   检测发现 **AG (沪银)**（$\nu = 3.1640$）、**CF (棉花)**（$\nu = 3.2287$）、**M (豆粕)**（$\nu = 3.8361$）、**RU (橡胶)**（$\nu = 3.3530$）和 **SN (沪锡)**（$\nu = 3.7399$）共 5 个品种的最优模型自由度估计值 $\nu \le 4$，触发了 `hl_moment_condition_ok = False` 警报，表明其理论第四矩（峰度）发散，谱检验的标准渐进方差推导在数学上受限。
    *   **Conservative Finite-Sample Performance of the Spectral Test / 谱检验在有限样本下表现保守** (based on / 基于 `15_hong_lee_monte_carlo_size_summary.csv`)：
        *   Utilizing the optimal fitted specifications as the Data Generating Process (DGP) for 100 Monte Carlo Size simulations at a 5% nominal significance level, the empirical Type I error rate is **1.00%** for AL (GARCH-t) and **0.00%** for AG (EGARCH-t), demonstrating that the test is statistically conservative in finite samples.
        *   以最优估计模型为数据生成过程（DGP）运行 100 次蒙特关洛 Size 仿真，在 5% 的名义显著性水平下，AL（GARCH-t）的经验第一类错误拒绝率为 **1.00%**，AG（EGARCH-t）的经验拒绝率为 **0.00%**，表明该检验在有限样本中实际第一类错误偏低，表现相对保守。
    *   **High Accuracy in Dynamic VaR Forecasting / 动态 VaR 预测回测准确度极高** (based on / 基于 `05_var_backtest_by_symbol.csv`)：
        *   Kupiec POF backtests on 20 contracts show VaR success rates of **18/20** (Long) and **17/20** (Short) at the 95% level (mean breach rates: **4.91%** and **4.82%**), and **17/20** (Long) and **19/20** (Short) at the 99% level (mean breach rates: **0.74%** and **0.93%**), validating the strength of GARCH-family models in dynamic risk estimation.
        *   在 20 个品种的 VaR 双向回测中，95% VaR 的 Long / Short 端 Kupiec POF 检验通过率分别为 **18/20** 和 **17/20**，平均违约率分别为 **4.91%** 和 **4.82%**；99% VaR 的 Long / Short 端通过率分别为 **17/20** 和 **19/20**，平均违约率分别为 **0.74%** 和 **0.93%**，充分印证了 GARCH 族模型的动态风险刻画能力。
    *   **Cross-Sectional Dispersion in Volatility States and Position Scaling / 条件波动率及仓位参考因子横截面分化** (based on / 基于 `06_current_vol_state_and_position_scaling.csv`)：
        *   For the latest trading day (June 18, 2026), conditional volatility varies widely. **AG (Silver)** and **MA (Methanol)** are in extreme high-volatility states (conditional volatilities: **3.805%** and **2.884%**, percentiles: **95.86%** and **96.61%**), compressing their position scaling factors to **0.417x** and **0.566x**. Conversely, **AL (Aluminum)** is in a normal volatility state (conditional volatility: **0.880%**, percentile: **38.71%**), expanding its exposure scale to **1.091x**. **I (Iron Ore)** lies in an extreme low-volatility state (conditional volatility: **1.103%**, percentile: **1.34%**), pushing its scaling factor to the capped limit of **1.500x** (raw scale: **2.007x**).
        *   最新数据日（2026年6月18日）品种条件波动率分化明显：**AG (沪银)** 和 **MA (甲醇)** 处于极端高波状态（条件波动率分别为 **3.805%** 和 **2.884%**，分位数分别为 **95.86%** 和 **96.61%**），其仓位参考因子分别收缩至 **0.417x** 和 **0.566x**；而 **AL (沪铝)** 处于常态波动状态（条件波动率 **0.880%**，分位数 **38.71%**），仓位释放至 **1.091x**；**I (铁矿石)** 处于极端低波状态（条件波动率 **1.103%**，分位数 **1.34%**），仓位参考因子释放至 capped 上限 **1.500x** (原始值为 **2.007x**)。

---

## 4. Multidimensional Valuation and Lower-Bound Pricing for Crypto Assets / Crypto_Pricing —— 加密资产多维度定价与下沿估值

*   **Research Background / 研究背景**：
    *   Replicates and extends the core frameworks of **Bhambhwani et al. (2019, BDK)** (on-chain fundamentals and network value anchors), **Biais et al. (2023)** (equilibrium convenience yields and transaction friction discounts), and **Liu & Tsyvinski (2021)** (momentum and attention-based risks) to construct a cascade downside downside valuation system with adaptive downgrade and risk-control capabilities for crypto assets (BTC) lacking traditional cash flows.
    *   针对无现金流、无传统估值锚的加密资产（BTC），复刻与拓展 **Bhambhwani et al. (2019, BDK)**（链上基本面与网络价值锚定）、**Biais et al. (2023)**（均衡交易便利与折价层）以及 **Liu & Tsyvinski (2021)**（动量与注意力折价层）三篇文献，构建具备强容错与降级能力的级联下沿估值系统。

*   **Framework & Workflow / 框架与流程**：
    *   **Pipeline Control & Validation / 主控工作流与采集校验**：
        *   Utilizes `pipeline.py` to coordinate workflows. Fetches daily features from CoinGecko, Binance, Blockchain.com, Coin Metrics, and other sources via `fetchers.py`. Performs multi-source gap and lead-lag Spearman correlation checks in `validator.py` to output dual-track databases: `Strict-tier` (strictly validated) and `Research-tier` (research proxy).
        *   利用 `pipeline.py` 串联工作流。通过 `fetchers.py` 从 CoinGecko、Binance、Blockchain.com、Coin Metrics 等多源抓取日频特征，并由 `validator.py` 执行多源 Gap 校验与延迟相关性（Spearman）筛选，输出 `Strict-tier`（严格验证）与 `Research-tier`（研究代理级）双轨特征库。
    *   **Fundamental Anchor & OLS Recalibration / 基本面锚定与 OLS 重校准**：
        *   Implements the BDK log-log baseline specification in `pricing.py`, supporting in-sample OLS dynamic recalibration to capture cyclical elasticity drift. Computes the fundamental anchor $V_{BDK}$ by scaling hashrate and active addresses under specific stress targets.
        *   `pricing.py` 实现 BDK 二元 Log-Log 基准模型并支持样本内 OLS 动态重校准以捕获最新周期的弹性系数，并在特定压力目标下缩放算力与活跃地址生成基本面底座 $V_{BDK}$。
    *   **Friction & Behavioral Discounts / 交易摩擦与行为情绪折价**：
        *   Computes the composite $S_{Biais}$ score by weighting transaction benefits, costs, market access, and drawdown risks (capping the crash-risk component at 0.0 to filter out bull market peaks). Computes the $S_{Liu}$ score by weighting price momentum, ordinary attention, negative attention, and activity growth (penalizing single-source Wikipedia attention with a 0.60 weight reduction). Generates discount coefficients via continuous exponential downside mappings.
        *   加权整合交易收益/成本/准入/崩盘风险计算 $S_{Biais}$ 评分（对崩盘风险整体进行上限归零过滤牛市噪点），加权整合动量/注意力/活跃增长计算 $S_{Liu}$ 评分（对单源研究级注意力进行 0.60 权重打折）；通过连续指数下行映射生成折价系数。

*   **Empirical Findings / 数据实证结论** (based on the latest sample output / 基于最新样例输出 `btc_three_paper_framework_pricing_v1_3.csv`，当时 BTC 价格约为 10.5 万美元)：
    *   **Fundamental Fair Value Estimation / 基本面公允价估算与弹性表现**：
        *   The OLS-recalibrated elasticities for hashrate and network size are both positive, successfully triggering the `full_ols_insample` calibration mode. Validated observations over the rolling window total **97 days** (requiring no sample size width penalty). The model estimates BTC's long-term baseline fair value at **$71,588.21** (indicating an approximate 33% bubble premium over the actual market price).
        *   当前样本内 OLS 重校准的算力与活跃地址弹性均为正，系统成功切换至 `full_ols_insample` 校准模式。全样本有效交叉验证观测天数达 **97 天**（无需额外天数惩罚）。模型估算当前比特币的长期 Log-Log 基本面公允价值为 **71,588.21 美元**（实际市场价存在约 33% 泡沫溢价）。
    *   **Behavioral Discounts / 行为折价层发挥差异化作用**：
        *   Under current high-market conditions, the Biais score stands at **1.058** (dominated by transaction activity and low drawdowns), yielding a transaction discount coefficient of **1.00** (no discount, indicating strong network convenience utility). However, the Liu score is dragged down by weak momentum and research-tier attention, scoring **-0.405** and yielding an attention discount of **0.960** (a 4% discount). The cascade pricing engine applies a joint discount coefficient of **0.960**.
        *   在当前牛市高位状态下，Biais 评分得分为 **1.058**（收益与风控分量主导），对应交易折价系数为 **1.00**（无折价，即网络交易便利效能高）。而 Liu 评分受 7D/14D 动量反转与研究级注意力偏弱拖累，得分为 **-0.405**，对应动量注意力折价系数为 **0.960**（约打 96 折）。系统最终以级联联合折价系数 **0.960** 入模。
    *   **Pricing floors under Stress Scenarios / 多情景价格下沿区间输出**：
        1.  **Base Pressure / 基础压力下沿**：
            *   Under a mild contraction (hashrate: 919.22 EH/s, addresses: 46.49k), the strict lower point is **$57,605.37**, corresponding to a valuation range of `[$51,844.83, $63,365.90]`.
            *   在算力收缩至 919.22 EH/s、地址收缩至 46.49 万的轻度压力下，价格下沿支撑点为 **57,605.37 美元**，对应估值区间为 `[51,844.83, 63,365.90]`；
        2.  **Core Lower Bound (Recommended Reference) / 核心估值下沿（常规参考）**：
            *   Under core stress (hashrate: 891.08 EH/s, addresses: 45.07k, representing the 15th percentile), the strict lower point is **$52,312.48**, corresponding to a valuation range of `[$47,081.23, $57,543.72]` (with width $W = 0.10$).
            *   在算力降至 891.08 EH/s、地址降至 45.07 万（15% 历史分位）的核心压力下，下沿支撑点为 **52,312.48 美元**，对应估值区间为 `[47,081.23, 57,543.72]`（带宽 $W = 0.10$）；
        3.  **Severe Lower Bound / 严重压力下沿**：
            *   Under severe stress (5th percentile), the strict lower point is **$44,239.87**, corresponding to a range of `[$39,815.89, $48,663.86]`.
            *   在 5% 历史极值下，下沿点降至 **44,239.87 美元**，对应估值区间为 `[39,815.89, 48,663.86]`；
        4.  **Extreme Tail / 极端尾部下沿**：
            *   Under a black-swan panic (5th percentile with an 85% current cap, removing double-press), the strict lower point drops to **$36,931.48**, corresponding to a range of `[$33,238.33, $40,624.63]`.
            *   在 5% 历史极值加 85% 当前上限下压（无二次重压）的黑天鹅底场景下，估值下沿低至 **36,931.48 美元**，对应区间为 `[33,238.33, 40,624.63]`；

---

## 5. Planned Research Modules and Future Directions / 五、 规划中研究模块与后续方向

The project will further explore the following two quantitative finance topics, progressively completing the replication and extension of relevant academic literature:

本项目后续将进一步探索以下两个量化金融课题，并逐步完成相关学术文献的复现与拓展检验：

### 1. Machine Learning, AI, and Forecasting Models / 机器学习 / AI / 预测模型
*   **Research Topics / 研究主题**：
    High-dimensional asset forecasting, Explainable AI (XAI) in asset allocation, deep reinforcement learning trading systems, and non-linear forecasting model comparisons.

    高维资产预测、可解释人工智能（XAI）在资产配置中的应用、深度强化学习交易系统以及多模型（如决策树、神经网络等）非线性预测比较。
*   **Core Literature / 核心文献**：
    *   *Afolabi et al. (2017)* — Hierarchical Meta-Learning in Time Series Forecasting for Improved Inference-Less Machine Learning
    *   *Babaei, Giudici, and Raffinetti (2022)* — Explainable Artificial Intelligence for Crypto Asset Allocation
    *   *Campisi, Muzzioli, and De Baets (2024)* — A Comparison of Machine Learning Methods for Predicting the Direction of the US Stock Market on the Basis of Volatility Indices
    *   *Chandak et al. (2019)* — Learning Action Representations for Reinforcement Learning
    *   *Gu, Kelly, and Xiu (2020)* — Empirical Asset Pricing via Machine Learning
    *   *Shen, Jiang, and Zhang (2012)* — Stock Market Forecasting Using Machine Learning Algorithms
    *   *Tran, Pham-Hi, and Bui (2023)* — Optimizing Automated Trading Systems with Deep Reinforcement Learning

### 2. Market Microstructure and High-Frequency Trading / 市场微观结构 / 高频交易 / 算法交易
*   **Research Topics / 研究主题**：
    Volatility feedback effects in high-frequency data, dynamic execution of micro-order flows, algorithmic trading optimization under Pro Rata matching mechanisms, and transaction cost minimization control.

    高频数据下的波动率反馈效应、微观订单流动态执行、Pro Rata 匹配机制下的算法交易优化以及交易成本最小化控制。
*   **Core Literature / 核心文献**：
    *   *Bollerslev, Litvinova, and Tauchen (2006)* — Leverage and Volatility Feedback Effects in High-Frequency Data
    *   *Funie, Salmon, and Luk (2014)* — A Hybrid Genetic-Programming Swarm-Optimisation Approach for Examining the Nature and Stability of High Frequency Trading Strategies
    *   *Guilbaud and Pham (2015)* — Optimal High-Frequency Trading in a Pro Rata Microstructure with Predictive Information
    *   *Kearns and Nevmyvaka (2013)* — Machine Learning for Market Microstructure and High Frequency Trading
    *   *Labadie, Lehalle, et al. (2010)* — Optimal Algorithmic Trading and Market Microstructure
    *   *Lehalle (2013)* — Market Microstructure Knowledge Needed for Controlling an Intra-Day Trading Process

---

## 6. Repository Directory Structure / 六、 目录结构说明

```text
QuantStrat/
├── README.md                                          # Root repository guide (this file, bilingual) / 根目录说明文档（中英文对照）
├── QuantStrat x UIUC MSFE.pdf                         # Slide deck for UIUC MSFE summer project & bibliography / UIUC MSFE 夏季项目合作及 bibliography 课件
├── Commodity_Futures_Raw_Data/                        # Commodity futures raw price & feature panel data (27 symbols) / 商品期货原始价格与特征面板数据 (27个品种)
│   ├── AG.csv, AL.csv, ...
│   └── futures_panel.csv                              # Commodity futures cross-sectional main panel / 商品期货横截面主面板
├── Market_Anomalies——市场异象/                        # Module 2: Technical anomalies, activity decay, post-pub decay / 模块二：技术异象、活跃度衰减与发表后衰减
│   ├── 02_vol_sorted_technical_anomaly.ipynb          # Vol-sorted cross-sectional technical anomaly backtesting / 波动率排序横截面技术分析异象回测
│   ├── 03_liquidity_attenuation.ipynb                 # Trading activity attenuation testing on anomalies / 交易活跃度对技术异象的削弱检验
│   ├── 04_post_selection_decay.ipynb                  # Post-strategy selection OOS and pseudo-live decay tests / 策略选择后的样本外与伪实盘衰减测试
│   ├── *.csv                                          # CSV files storing strategies and regression outcomes / 策略与回归的运行结果表
│   └── README.md                                      # Module 1 detailed design & CSV findings document / 模块一详细设计与CSV发现文档
├── Volatility_Time_Series——波动率&时间序列检验/       # Module 3: Volatility modeling & Hong-Lee spectral risk control / 模块三：波动率建模与 Hong-Lee 谱检验风控模块
│   ├── Traditional_Model_Selection_Sugar.ipynb        # Single contract replication & full pipeline diagnostic (Sugar SR) / 单合约复刻论文及全流程检验 (白糖主力)
│   ├── hong_lee_20_contracts.ipynb                    # Multi-contract extension execution script (20 symbols) / 多合约拓展运行脚本 (20个商品期货主力)
│   ├── *.csv                                          # 20-contract volatility models & spectral diagnostic tables / 20合约波动率建模与健康谱检验表
│   └── README.md                                      # Module 2 detailed design, findings & risk control document / 模块二详细设计、CSV发现与风控逻辑文档
├── Crypto_Pricing—— 加密货币定价/                     # Module 4: BTC multidimensional pricing & downside valuation / 模块四：BTC多维定价与下沿估值模块
│   ├── btc_unified_pricing_model/                     # Python core package / Python 核心模型包 (fetchers, validator, pricing)
│   ├── tests/                                         # Unit testing module / 单元测试模块
│   └── README.md                                      # Module 3 detailed design document / 模块三详细设计文档
└── Momentum_Reversal_Trend-Following——动量&反转&趋势/ # Module 1: momentum, reversal, trend-following / 模块一：动量、反转与趋势跟踪
    ├── Trend/                                         # Trend-following notebook and CSV outputs / 趋势跟踪 notebook 与 CSV 输出
    ├── Momentum/                                      # Momentum notebook and CSV outputs / 动量 notebook 与 CSV 输出
    ├── Reversal/                                      # Reversal notebook and CSV outputs / 反转 notebook 与 CSV 输出
    └── README.md                                      # Module 4 detailed design & CSV findings document / 模块四详细设计与CSV发现文档
```
