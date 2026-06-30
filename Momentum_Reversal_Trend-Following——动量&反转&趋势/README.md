# Momentum, Reversal, and Trend-Following -- 动量、反转与趋势跟踪

本目录研究中国商品期货主力连续合约中的 **Trend-Following / 趋势跟踪**、**Momentum / 时间序列动量** 与 **Reversal / 后续反转**。当前 README 只保留全局、全历史、逐标的结论；不再展示 2026-06-29 或 2026-06-30 的当前截面逐标的判断。

> **重要口径**：本模块目前是**全样本历史研究总结**，不是 OOS、pseudo-live 或实时交易信号。模型选择、最佳窗口、状态识别和统计结论均基于全样本 CSV 结果，天然存在前置时间泄露和模型选择偏差。因此，下文只能解释“在当前 CSV 全样本内发生了什么”，不能被解读为样本外预测能力或实盘有效性。

---

## 一、研究定位

本 README 回答九个全样本问题：

1. 全历史中，每个合约是否反复出现可识别趋势？
2. 全历史中，趋势 episode 的典型持续时间是多少？
3. 全历史中，趋势 episode 的结束概率是多少？
4. 全历史中，每个合约是否存在可验证的时间序列动量？
5. 全历史中，动量 episode 的典型持续时间是多少？
6. 全历史中，动量 episode 的消失概率是多少？
7. 全历史中，每个合约是否存在可验证的后续反转？
8. 全历史中，反转 episode 的典型持续时间是多少？
9. 全历史中，反转 episode 的结束概率是多少？

术语说明：

- `CONFIRMED`：通过样本数、Newey-West t 值、hit rate 和 stationary bootstrap 的确认模型。
- `CANDIDATE`：通过较低门槛的候选模型。
- `DIAGNOSTIC_ONLY`：仅作诊断展示，不视为可验证模型。
- `episode`：同方向、同来源的连续有效状态段。
- `validated-active observations`：Reversal duration 的单位，表示反转 validated-active 状态内的观测数，不等同于自然日或保证持仓天数。

---

## 二、核心文献对应关系

本项目参考文献映射到四类研究设计：

1. **动量与时间序列动量基础**：Jegadeesh and Titman (1993), Moskowitz, Ooi, and Pedersen (2012), Asness, Moskowitz, and Pedersen (2013), Hurst, Ooi, and Pedersen (2017) 支持“过去收益延续”和跨资产趋势/动量可检验性。
2. **风险调整与波动率自适应动量**：Ammann, Moellenbeck, and Schmid (2011), Baltas and Kosowski (2012), Dudler, Gmuer, and Malamud (2014/2015), Karassavidis, Kateris, and Ioannidis (2025) 对应波动率标准化收益、Newey-West t 值、bootstrap 和模型质量分级。
3. **技术规则与趋势状态切换**：Brock, Lakonishok, and LeBaron (1992), Lo, Mamaysky, and Wang (2000), Tayal (2009), Zakamulin and Giner (2022/2024) 对应 rolling OLS trend rule、状态机、episode duration 和结束风险。
4. **反转、极端收益与多策略推断**：Caporale and Plastun (2020), Dobrynskaya (2021/2023), Li et al. (2021), Daniel and Moskowitz (2016), Newey and West (1987), Politis and Romano (1994), White (2000), Hansen (2005) 对应异常收益后的反转、动量崩盘风险与数据挖掘控制。

完整参考文献：

- Ammann, Moellenbeck, and Schmid (2011): Feasible Momentum Strategies in the US Stock Market
- Baltas and Kosowski (2012): Improving Time-Series Momentum Strategies: The Role of Trading Signals and Volatility Estimators
- Caporale and Plastun (2020): Momentum Effects in the Cryptocurrency Market After One-Day Abnormal Returns
- Dobrynskaya (2021/2023): Cryptocurrency Momentum and Reversal
- Dudler, Gmuer, and Malamud (2014/2015): Risk-Adjusted Time Series Momentum
- Karassavidis, Kateris, and Ioannidis (2025): Quantitative Evaluation of Volatility-Adaptive Trend-Following Models in Cryptocurrency Markets
- Li et al. (2021): MAX Momentum in Cryptocurrency Markets
- Tayal (2009): Regime Switching and Technical Trading with Dynamic Bayesian Networks in High-Frequency Stock Markets
- Zakamulin and Giner (2022/2024): Optimal Trend-Following Rules in Two-State Regime-Switching Models
- Jegadeesh and Titman (1993): Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency
- Moskowitz, Ooi, and Pedersen (2012): Time Series Momentum
- Hurst, Ooi, and Pedersen (2017): A Century of Evidence on Trend-Following Investing
- Brock, Lakonishok, and LeBaron (1992): Simple Technical Trading Rules and the Stochastic Properties of Stock Returns
- Lo, Mamaysky, and Wang (2000): Foundations of Technical Analysis: Computational Algorithms, Statistical Inference, and Empirical Implementation
- Newey and West (1987): A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix
- Politis and Romano (1994): The Stationary Bootstrap
- White (2000): A Reality Check for Data Snooping
- Hansen (2005): A Test for Superior Predictive Ability
- Daniel and Moskowitz (2016): Momentum Crashes
- Asness, Moskowitz, and Pedersen (2013): Value and Momentum Everywhere

---

## 三、数据与流程

### 1. 标的与数据

基础数据为天勤主力连续合约日线，三个 notebook 共用同一套 11 个品种：

| 代码 | 品种 | 天勤主力连续合约 | 样本起始过滤日 |
| :--- | :--- | :--- | :--- |
| AG | 沪银 | `KQ.m@SHFE.ag` | 2012-05-10 |
| CF | 棉花 | `KQ.m@CZCE.CF` | 2004-06-01 |
| EB | 苯乙烯 | `KQ.m@DCE.eb` | 2019-09-26 |
| FG | 玻璃 | `KQ.m@CZCE.FG` | 2012-12-03 |
| LH | 生猪 | `KQ.m@DCE.lh` | 2021-01-08 |
| M | 豆粕 | `KQ.m@DCE.m` | 2000-01-01 |
| MA | 甲醇 | `KQ.m@CZCE.MA` | 2011-10-28 |
| SA | 纯碱 | `KQ.m@CZCE.SA` | 2019-12-06 |
| SP | 纸浆 | `KQ.m@SHFE.sp` | 2018-11-27 |
| SR | 白糖 | `KQ.m@CZCE.SR` | 2006-01-06 |
| V | PVC | `KQ.m@DCE.v` | 2009-05-25 |

核心代码：

- `Trend/Main_Continuous_Daily_Trend.ipynb`
- `Momentum/Main_Continuous_Daily_Momentum.ipynb`
- `Reversal/Main_Continuous_Daily_Reversal.ipynb`

### 2. 全样本流程

1. 从天勤主力连续合约日线生成统一 panel。
2. 清洗 OHLCV，计算对数收益、滚动波动率、EWMA fallback、标准化远期收益。
3. 对 Trend / Momentum / Reversal 分别构造候选信号网格。
4. 在全样本内计算方向收益、Newey-West t 值、hit rate、stationary bootstrap p 值。
5. 在全样本内挑选每个品种的最佳模型。
6. 基于最佳模型回填全历史状态、episode、duration 与 survival/end probability。
7. 输出 `hist_*` CSV，并据此写出本 README 的逐标的结论。

再次强调：第 4-6 步均使用全样本结果，因此本 README 不是样本外验证。

---

## 四、核心指标与公式

基础收益与波动率：

$$
r_t=\log(C_t/C_{t-1})
$$

$$
\sigma_t=\mathrm{RollingStd}_{20}(r_t)
$$

若 20 日滚动波动率尚不可用，代码使用 EWMA 波动率 fallback。远期标准化收益：

$$
Y_{t,k}=\frac{\log(C_{t+k}/C_t)}{\sigma_t\sqrt{k}}
$$

### 1. Trend

趋势强度来自 rolling OLS：

$$
\log(C_{t-h+1:t})=\alpha+\beta x+\epsilon
$$

`TTrend_h` 为斜率 t 值，`TrendFit_h` 为 rolling OLS 的 $R^2$。

趋势存在：

$$
|TTrend_h|\ge 2.0,\quad TrendFit_h\ge 0.20
$$

趋势方向：

$$
s^{trend}_{t,h}=\mathrm{sign}(TTrend_{t,h})
$$

趋势确立要求同方向趋势存在状态连续至少 2 天；`TrendEndRisk` 表示过度延展风险，`TrendEndConfirmed` 表示信号消失、方向反转或 ATR stop 触发。

### 2. Momentum

风险调整时间序列动量：

$$
RAMOM_{t,J}=\sum_{i=1}^{J}\frac{r_{t-i}}{\sigma_{t-i}}
$$

动量一致性：

$$
MCS_{t,J}=\frac{1}{J}\sum_{i=1}^{J}1\{\mathrm{sign}(r_{t-i})=\mathrm{sign}(RAMOM_{t,J})\}
$$

动量存在：

$$
|RAMOM_{t,J}|\ge 1.0,\quad MCS_{t,J}\ge 0.58
$$

动量确立要求同方向动量存在状态连续至少 2 天；验证确立还要求最佳模型为 `CONFIRMED` 或 `CANDIDATE`。

### 3. Reversal

Reversal 使用三类反转来源：

1. **TSREV**：过去 $J$ 日累计收益的反向交易。

$$
R_{t,J}=\sum_{i=0}^{J-1}r_{t-i},\quad D_{t,J}=\frac{R_{t,J}}{\sigma_t\sqrt{J}}
$$

$$
s^{TSREV}_{t,J}=-\mathrm{sign}(R_{t,J}),\quad |D_{t,J}|\ge 1.0
$$

2. **RAREV**：风险调整动量的反向交易。

$$
s^{RAREV}_{t,J}=-\mathrm{sign}(RAMOM_{t,J}),\quad |RAMOM_{t,J}|\ge 1.0
$$

3. **FastREV**：单纯极端标准化累计收益后的快速反转。

$$
s^{FastREV}_{t,J}=-\mathrm{sign}(D_{t,J}),\quad |D_{t,J}|\ge 2.0
$$

Reversal validated signal 要求 raw reversal signal 同方向连续至少 2 个 observation，并且最佳模型可用。Reversal duration 以 `validated_active_observations` 计数，不按自然日计数。

### 4. 统一模型评分

三个方向均使用方向收益：

$$
DirectedY_{t,k}=s_tY_{t,k}
$$

模型质量分级：

- `CANDIDATE`：`n>=60`、`mean_y>0`、`t_nw>=1.0`、`hit_rate>0.50`。
- `CONFIRMED`：满足 `CANDIDATE`，且 `n>=120`、`t_nw>=2.0`、`hit_rate>0.50`、bootstrap `p(mean<=0)<=0.10` 或 p 值缺失。
- `DIAGNOSTIC_ONLY`：不满足上述可验证门槛。

---

## 五、CSV 结论依据

本 README 的结论只使用以下全历史 CSV：

| 方向 | Q1 存在 | Q2 持续 | Q3 结束/消失 |
| :--- | :--- | :--- | :--- |
| Trend | `trend_hist_q1_existence_model.csv` | `trend_hist_q2_duration_distribution.csv` | `trend_hist_q3_end_risk_survival.csv` |
| Momentum | `momentum_hist_q1_existence_model.csv` | `momentum_hist_q2_duration_distribution.csv` | `momentum_hist_q3_end_risk_survival.csv` |
| Reversal | `reversal_hist_q1_existence_model.csv` | `reversal_hist_q2_duration_distribution.csv` | `reversal_hist_q3_end_survival.csv` |

`*_current*` 文件是 notebook 的当前截面运行产物，但不作为本 README 的逐标的结论依据。

---

## 六、全历史 Trend 结论

判读规则：`存在/确立` 为全历史日度状态频率；`主导方向` 为确立趋势日内 UP/DOWN 占比更高的一侧；Q2/Q3 仅针对该主导方向。

| 合约 | 样本 | Q1: 趋势存在 | 最佳趋势模型 | Q2: 主导方向持续时间 | Q3: 主导方向结束概率 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AG 沪银 | 2016-01-05~2026-06-29; n=2544 | 存在 67.3%; 确立 65.0%; 主导 UP 59.1% | h=40,K=20, CONFIRMED, t=3.11, hit=50.7%, p=0.000 | UP: median 1d; mean 5.9d; episodes=167; ended=167; rel=HIGH | NO_RISK 5=43.9%/10=59.5%/20=74.4%<br>RISK 5=26.0%/10=42.9%/20=71.8% |
| CF 棉花 | 2016-01-05~2026-06-29; n=2544 | 存在 69.8%; 确立 67.6%; 主导 UP 58.8% | h=40,K=10, CANDIDATE, t=1.79, hit=52.0%, p=0.013 | UP: median 1d; mean 7.6d; episodes=133; ended=133; rel=HIGH | NO_RISK 5=37.2%/10=49.7%/20=63.4%<br>RISK 5=24.1%/10=41.1%/20=65.6% |
| EB 苯乙烯 | 2019-09-26~2026-06-29; n=1634 | 存在 62.2%; 确立 53.0%; 主导 DOWN 51.7% | h=10,K=2, CONFIRMED, t=2.08, hit=52.5%, p=0.015 | DOWN: median 5d; mean 6.2d; episodes=72; ended=71; rel=HIGH | NO_RISK 5=69.6%/10=89.8%/20=99.4%<br>RISK 5=32.5%/10=68.7%/20=92.2% |
| FG 玻璃 | 2016-01-05~2026-06-29; n=2544 | 存在 61.4%; 确立 52.6%; 主导 UP 50.4% | h=10,K=20, CANDIDATE, t=1.72, hit=51.9%, p=0.018 | UP: median 5d; mean 6.6d; episodes=103; ended=103; rel=HIGH | NO_RISK 5=69.8%/10=89.0%/20=97.9%<br>RISK 5=43.8%/10=77.6%/20=100.0% |
| LH 生猪 | 2021-01-08~2026-06-29; n=1323 | 存在 72.2%; 确立 69.8%; 主导 DOWN 61.5% | h=40,K=20, CONFIRMED, t=2.13, hit=55.0%, p=0.010 | DOWN: median 1d; mean 5.7d; episodes=99; ended=99; rel=HIGH | NO_RISK 5=40.1%/10=55.4%/20=75.8%<br>RISK 5=37.5%/10=50.6%/20=73.9% |
| M 豆粕 | 2016-01-05~2026-06-29; n=2544 | 存在 71.6%; 确立 66.7%; 主导 DOWN 50.1% | h=20,K=10, DIAGNOSTIC_ONLY, t=0.87, hit=49.3%, p=0.180 | DOWN: median 10d; mean 12.7d; episodes=67; ended=67; rel=HIGH | NO_RISK 5=39.6%/10=61.9%/20=83.9%<br>RISK 5=8.2%/10=39.5%/20=76.2% |
| MA 甲醇 | 2016-01-05~2026-06-29; n=2544 | 存在 68.3%; 确立 66.0%; 主导 UP 55.7% | h=40,K=20, CONFIRMED, t=2.52, hit=51.3%, p=0.000 | UP: median 1d; mean 6.0d; episodes=155; ended=155; rel=HIGH | NO_RISK 5=40.7%/10=55.1%/20=77.1%<br>RISK 5=28.6%/10=51.6%/20=70.9% |
| SA 纯碱 | 2019-12-06~2026-06-29; n=1588 | 存在 71.2%; 确立 66.8%; 主导 DOWN 57.4% | h=20,K=10, CANDIDATE, t=1.37, hit=51.9%, p=0.052 | DOWN: median 10d; mean 14.9d; episodes=41; ended=40; rel=MEDIUM | NO_RISK 5=32.7%/10=54.6%/20=80.9%<br>RISK 5=18.4%/10=36.0%/20=59.6% |
| SP 纸浆 | 2018-11-27~2026-06-29; n=1838 | 存在 60.4%; 确立 51.5%; 主导 DOWN 52.3% | h=10,K=20, CANDIDATE, t=1.87, hit=52.1%, p=0.013 | DOWN: median 5d; mean 6.4d; episodes=77; ended=76; rel=HIGH | NO_RISK 5=61.0%/10=84.9%/20=99.2%<br>RISK 5=51.7%/10=80.0%/20=100.0% |
| SR 白糖 | 2016-01-05~2026-06-29; n=2544 | 存在 63.4%; 确立 61.8%; 主导 UP 51.4% | h=60,K=20, CANDIDATE, t=1.77, hit=50.7%, p=0.013 | UP: median 1d; mean 4.1d; episodes=197; ended=197; rel=HIGH | NO_RISK 5=55.4%/10=71.7%/20=91.8%<br>RISK 5=21.7%/10=32.6%/20=40.6% |
| V PVC | 2016-01-05~2026-06-29; n=2544 | 存在 69.9%; 确立 65.1%; 主导 UP 50.3% | h=20,K=20, CANDIDATE, t=1.84, hit=53.4%, p=0.010 | UP: median 7d; mean 11.0d; episodes=76; ended=76; rel=HIGH | NO_RISK 5=41.0%/10=62.2%/20=83.6%<br>RISK 5=17.2%/10=45.1%/20=77.9% |

全历史 Trend 的 CSV 事实：

- 11 个合约的趋势确立频率均超过 50%，说明趋势状态在全样本内普遍存在。
- `CONFIRMED` 趋势模型：AG、EB、LH、MA。`CANDIDATE`：CF、FG、SA、SP、SR、V。`DIAGNOSTIC_ONLY`：M。
- 主导方向并不单边一致：AG、CF、FG、MA、SR、V 偏 UP；EB、LH、M、SA、SP 偏 DOWN。
- 趋势 duration 中位数多数较短，M、SA、V 的主导方向中位数相对更长。

---

## 七、全历史 Momentum 结论

判读规则：`信号` 为原始动量信号频率，`验证确立` 为连续天数和模型可用性过滤后的频率；Q2/Q3 仅针对验证确立后的主导方向。

| 合约 | 样本 | Q1: 动量存在 | 最佳动量模型 | Q2: 主导方向持续时间 | Q3: 主导方向消失概率 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AG 沪银 | 2016-01-05~2026-06-30; n=2545 | 信号 31.4%; 验证确立 11.9%; 主导 UP 56.8% | J=2,K=1, CONFIRMED, t=2.44, hit=51.9%, p=0.003 | UP: median 1d; mean 1.7d; episodes=102; ended=102; rel=HIGH | NO_RISK 5=99.0%/10=100.0%/20=100.0%<br>RISK 5=100.0%/10=100.0%/20=100.0% |
| CF 棉花 | 2016-01-05~2026-06-30; n=2545 | 信号 47.5%; 验证确立 26.6%; 主导 UP 53.3% | J=3,K=2, CONFIRMED, t=3.20, hit=51.0%, p=0.000 | UP: median 2d; mean 2.3d; episodes=156; ended=156; rel=HIGH | NO_RISK 5=98.3%/10=100.0%/20=100.0%<br>RISK 5=91.0%/10=100.0%/20=100.0% |
| EB 苯乙烯 | 2019-09-26~2026-06-30; n=1635 | 信号 44.5%; 验证确立 37.7%; 主导 UP 51.1% | J=20,K=5, CONFIRMED, t=2.36, hit=54.0%, p=0.003 | UP: median 7d; mean 8.8d; episodes=36; ended=36; rel=MEDIUM | NO_RISK 5=42.2%/10=66.4%/20=83.2%<br>RISK 5=31.0%/10=64.8%/20=98.6% |
| FG 玻璃 | 2016-01-05~2026-06-30; n=2545 | 信号 20.0%; 验证确立 17.8%; 主导 UP 67.8% | J=40,K=1, CONFIRMED, t=2.13, hit=53.7%, p=0.018 | UP: median 8d; mean 15.4d; episodes=20; ended=20; rel=MEDIUM | NO_RISK 5=40.1%/10=53.5%/20=67.6%<br>RISK 5=10.2%/10=29.5%/20=61.4% |
| LH 生猪 | 2021-01-08~2026-06-30; n=1324 | 信号 43.0%; 验证确立 37.3%; 主导 DOWN 72.7% | J=20,K=5, CANDIDATE, t=1.56, hit=54.8%, p=0.058 | DOWN: median 5d; mean 10.9d; episodes=33; ended=33; rel=MEDIUM | NO_RISK 5=42.1%/10=61.7%/20=82.6%<br>RISK 5=20.2%/10=37.9%/20=71.8% |
| M 豆粕 | 2016-01-05~2026-06-30; n=2545 | 信号 48.6%; 验证确立 28.1%; 主导 UP 53.5% | J=3,K=20, CANDIDATE, t=1.36, hit=51.6%, p=0.068 | UP: median 2d; mean 2.4d; episodes=161; ended=160; rel=HIGH | NO_RISK 5=95.7%/10=100.0%/20=100.0%<br>RISK 5=93.7%/10=100.0%/20=100.0% |
| MA 甲醇 | 2016-01-05~2026-06-30; n=2545 | 信号 51.3%; 验证确立 0.0%; 无验证确立方向 | J=3,K=20, DIAGNOSTIC_ONLY, t=0.73, hit=50.4%, p=0.325 | 验证确立=0; 无可统计 episode | 验证确立=0; 不适用 |
| SA 纯碱 | 2019-12-06~2026-06-30; n=1589 | 信号 33.0%; 验证确立 12.8%; 主导 DOWN 54.7% | J=2,K=2, CONFIRMED, t=2.36, hit=55.0%, p=0.015 | DOWN: median 1d; mean 1.5d; episodes=74; ended=74; rel=HIGH | NO_RISK 5=100.0%/10=100.0%/20=100.0%<br>RISK 5=100.0%/10=100.0%/20=100.0% |
| SP 纸浆 | 2018-11-27~2026-06-30; n=1839 | 信号 19.5%; 验证确立 17.1%; 主导 UP 63.7% | J=40,K=20, CONFIRMED, t=3.41, hit=66.7%, p=0.000 | UP: median 4d; mean 11.8d; episodes=17; ended=17; rel=LOW | NO_RISK 5=39.1%/10=60.9%/20=89.1%<br>RISK 5=8.1%/10=17.7%/20=29.0% |
| SR 白糖 | 2016-01-05~2026-06-30; n=2545 | 信号 31.7%; 验证确立 0.0%; 无验证确立方向 | J=2,K=2, DIAGNOSTIC_ONLY, t=1.34, hit=48.8%, p=0.080 | 验证确立=0; 无可统计 episode | 验证确立=0; 不适用 |
| V PVC | 2016-01-05~2026-06-30; n=2545 | 信号 51.9%; 验证确立 31.7%; 主导 UP 51.3% | J=3,K=1, CONFIRMED, t=2.16, hit=50.9%, p=0.015 | UP: median 2d; mean 2.6d; episodes=162; ended=162; rel=HIGH | NO_RISK 5=96.1%/10=99.3%/20=100.0%<br>RISK 5=92.7%/10=100.0%/20=100.0% |

全历史 Momentum 的 CSV 事实：

- 9 个合约出现过验证确立动量；MA、SR 的验证确立频率为 0，不能形成可统计 episode。
- `CONFIRMED` 动量模型：AG、CF、EB、FG、SA、SP、V。`CANDIDATE`：LH、M。`DIAGNOSTIC_ONLY`：MA、SR。
- AG、CF、M、SA、V 的主导动量 episode 极短，5 日内消失概率接近或达到 100%。
- EB、FG、LH、SP 的主导动量 duration 相对更长，但部分样本可靠度为 MEDIUM 或 LOW。

---

## 八、全历史 Reversal 结论

判读规则：`信号` 为 raw reversal signal 频率，`验证确立` 为连续方向和模型可用性过滤后的频率；Q2/Q3 仅针对验证确立后的主导方向和来源。Reversal 的 duration 与结束概率单位均为 `validated-active observations`。

| 合约 | 样本 | Q1: 反转存在 | 最佳反转模型 | Q2: 主导方向持续时间 | Q3: 主导方向结束概率 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AG 沪银 | 2016-01-05~2026-06-30; n=2545 | 信号 32.7%; 验证确立 21.0%; 主导 DOWN 56.7% | TSREV, J=5,K=5, CANDIDATE, t=1.07, hit=54.3%, p=0.142 | DOWN/TSREV: median 3.0 obs; mean 2.9 obs; episodes=104; ended=104; rel=HIGH | 1obs=34.3%/5obs=94.4%/10obs=99.7%/20obs=100.0% |
| CF 棉花 | 2016-01-05~2026-06-30; n=2545 | 信号 4.3%; 验证确立 3.1%; 主导 DOWN 69.6% | FastREV, J=60,K=20, CANDIDATE, t=3.73, hit=67.9%, p=0.000 | DOWN/FastREV: median 6.0 obs; mean 6.1 obs; episodes=9; ended=9; rel=LOW | 1obs=16.4%/5obs=60.0%/10obs=90.9%/20obs=100.0% |
| EB 苯乙烯 | 2019-09-26~2026-06-30; n=1635 | 信号 3.9%; 验证确立 0.0%; 无验证确立方向 | FastREV, J=60,K=20, DIAGNOSTIC_ONLY, t=4.24, hit=78.9%, p=0.000 | 验证确立=0; 无可统计 episode | 验证确立=0; 不适用 |
| FG 玻璃 | 2016-01-05~2026-06-30; n=2545 | 信号 4.9%; 验证确立 1.9%; 主导 DOWN 56.2% | FastREV, J=3,K=10, CANDIDATE, t=1.61, hit=60.8%, p=0.075 | DOWN/FastREV: median 1.5 obs; mean 1.7 obs; episodes=16; ended=16; rel=LOW | 1obs=59.3%/5obs=100.0%/10obs=100.0%/20obs=100.0% |
| LH 生猪 | 2021-01-08~2026-06-30; n=1324 | 信号 7.8%; 验证确立 0.0%; 无验证确立方向 | FastREV, J=20,K=20, DIAGNOSTIC_ONLY, t=0.41, hit=53.4%, p=0.547 | 验证确立=0; 无可统计 episode | 验证确立=0; 不适用 |
| M 豆粕 | 2016-01-05~2026-06-30; n=2545 | 信号 30.0%; 验证确立 26.4%; 主导 DOWN 50.7% | TSREV, J=60,K=20, CONFIRMED, t=2.11, hit=57.9%, p=0.010 | DOWN/TSREV: median 6.0 obs; mean 10.7 obs; episodes=32; ended=32; rel=MEDIUM | 1obs=9.4%/5obs=36.7%/10obs=55.4%/20obs=79.5% |
| MA 甲醇 | 2016-01-05~2026-06-30; n=2545 | 信号 3.8%; 验证确立 2.8%; 主导 UP 68.6% | FastREV, J=60,K=10, CANDIDATE, t=5.79, hit=78.1%, p=0.000 | UP/FastREV: median 3.0 obs; mean 4.4 obs; episodes=11; ended=11; rel=LOW | 1obs=22.9%/5obs=72.9%/10obs=93.8%/20obs=100.0% |
| SA 纯碱 | 2019-12-06~2026-06-30; n=1589 | 信号 89.8%; 验证确立 85.7%; 主导 UP 50.5% | RAREV, J=60,K=20, CANDIDATE, t=1.67, hit=55.7%, p=0.055 | UP/RAREV: median 8.0 obs; mean 25.8 obs; episodes=27; ended=26; rel=MEDIUM | 1obs=3.8%/5obs=14.2%/10obs=24.6%/20obs=40.0% |
| SP 纸浆 | 2018-11-27~2026-06-30; n=1839 | 信号 6.0%; 验证确立 2.6%; 主导 UP 63.8% | FastREV, J=3,K=10, CANDIDATE, t=1.05, hit=53.8%, p=0.102 | UP/FastREV: median 2.0 obs; mean 1.8 obs; episodes=17; ended=17; rel=LOW | 1obs=56.7%/5obs=100.0%/10obs=100.0%/20obs=100.0% |
| SR 白糖 | 2016-01-05~2026-06-30; n=2545 | 信号 30.4%; 验证确立 12.0%; 主导 UP 53.8% | TSREV, J=2,K=10, CONFIRMED, t=2.40, hit=53.1%, p=0.005 | UP/TSREV: median 1.0 obs; mean 1.3 obs; episodes=123; ended=123; rel=HIGH | 1obs=75.0%/5obs=100.0%/10obs=100.0%/20obs=100.0% |
| V PVC | 2016-01-05~2026-06-30; n=2545 | 信号 32.2%; 验证确立 28.6%; 主导 UP 52.8% | TSREV, J=60,K=20, CANDIDATE, t=1.17, hit=59.2%, p=0.140 | UP/TSREV: median 7.5 obs; mean 12.3 obs; episodes=31; ended=30; rel=MEDIUM | 1obs=7.8%/5obs=30.6%/10obs=51.6%/20obs=75.4% |

全历史 Reversal 的 CSV 事实：

- 9 个合约出现过验证确立反转；EB、LH 的验证确立频率为 0，不能形成可统计 reversal episode。
- `CONFIRMED` 反转模型：M、SR。`CANDIDATE`：AG、CF、FG、MA、SA、SP、V。`DIAGNOSTIC_ONLY`：EB、LH。
- Reversal 的来源具有明显品种差异：AG、M、SR、V 为 TSREV；CF、FG、MA、SP 为 FastREV；SA 为 RAREV。
- SA 的反转最频繁，验证确立率 85.7%，且主导 UP/RAREV 的结束概率最低、duration 最长。SR、FG、SP 的主导反转 episode 极短，5 个 validated-active observations 内结束概率达到 100%。

---

## 九、总体全样本结论

1. **Trend**：11 个品种全历史均有高频率趋势状态，趋势确立率全部超过 50%。但其中 M 的最佳趋势模型为 `DIAGNOSTIC_ONLY`，只能作为状态频率事实，不能视为已验证模型。
2. **Momentum**：动量比趋势更稀疏。9 个品种有验证确立动量，MA、SR 没有可统计 validated momentum episode。
3. **Reversal**：9 个品种有验证确立反转，EB、LH 没有可统计 validated reversal episode。SA 的反转状态最密集，SR 的 TSREV 反转模型为 `CONFIRMED` 且持续极短。
4. **持续性差异**：Trend 的日历日 duration 相对可延展；Momentum 多数品种 episode 偏短；Reversal 用 validated-active observations 计数，不能和 Trend/Momentum 的日历日直接横向比较。
5. **结束/消失概率**：表中概率均为全样本 episode 内的经验频率，不是未来概率预测。尤其是 `CONFIRMED/CANDIDATE` 标签也来自全样本筛选，未经过 OOS 检验。
6. **下一步**：若要转化为可交易研究，需要重新切分 IS/OOS 或 rolling walk-forward，并在 OOS 中固定参数、重新计算状态和 episode survival。
