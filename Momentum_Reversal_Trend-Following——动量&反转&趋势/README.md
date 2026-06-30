# Momentum, Reversal, and Trend-Following -- 动量、反转与趋势跟踪

本目录用于研究中国商品期货主力连续合约中的趋势跟踪、时间序列动量与后续反转模块。当前已经完成 `Trend` 与 `Momentum` 两个方向的 notebook 全流程和最终 CSV 输出；`Reversal` 仍作为后续补充模块保留。

本 README 严格基于当前仓库中的 notebook 代码与 CSV 结果撰写，不对 CSV 以外的数据做主观补估。当前截面按各 CSV 的最新日期读取：趋势表最新为 **2026-06-29**，动量表最新为 **2026-06-30**。因此，下文“当前截面”中的趋势结论对应 2026-06-29，动量结论对应当前动量 CSV 实际保存的 2026-06-30。

---

## 一、研究定位

本模块回答六个问题：

1. 全历史中，每个主力连续合约是否反复出现可识别趋势？
2. 全历史中，趋势 episode 的典型持续时间与结束概率是多少？
3. 当前截面中，每个合约的趋势是否已经确立、预计还能持续多久、是否已经结束或存在结束风险？
4. 全历史中，每个主力连续合约是否存在可验证的时间序列动量？
5. 全历史中，动量 episode 的典型持续时间与消失概率是多少？
6. 当前截面中，每个合约的动量是否已经确立、预计还能持续多久、是否已经消失或存在消失风险？

需要注意：这里的“趋势/动量存在”是统计状态识别，不等同于交易建议；“还能持续多久”来自历史同方向、同年龄 episode 的条件分布，不是确定性预测；“结束/消失”分为已确认结束与结束风险两个层级。

---

## 二、核心文献对应关系

本项目参考文献被映射到四类研究设计：

1. **动量与时间序列动量基础**：Jegadeesh and Titman (1993), Moskowitz, Ooi, and Pedersen (2012), Asness, Moskowitz, and Pedersen (2013), Hurst, Ooi, and Pedersen (2017) 提供“过去赢家延续”和跨资产趋势/动量可检验性的基础框架。
2. **可实施、风险调整与波动率自适应动量**：Ammann, Moellenbeck, and Schmid (2011), Baltas and Kosowski (2012), Dudler, Gmuer, and Malamud (2014/2015), Karassavidis, Kateris, and Ioannidis (2025) 支持本项目使用波动率标准化收益、Newey-West t 值、bootstrap 与模型可用性分级。
3. **技术规则、趋势跟踪与状态切换**：Brock, Lakonishok, and LeBaron (1992), Lo, Mamaysky, and Wang (2000), Tayal (2009), Zakamulin and Giner (2022/2024) 对应 rolling trend rule、路径确认、episode 状态机和两状态趋势/非趋势切换。
4. **反转、极端收益与数据挖掘控制**：Caporale and Plastun (2020), Dobrynskaya (2021/2023), Li et al. (2021), Daniel and Moskowitz (2016), Newey and West (1987), Politis and Romano (1994), White (2000), Hansen (2005) 对应后续反转模块、异常收益后的动量/反转、动量崩盘风险以及多策略检验中的稳健推断。

完整参考清单：

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

## 三、数据与 notebook 工作流

当前模块覆盖 11 个商品期货主力连续合约：

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

### 1. 数据层

- 代码文件：
  - `Trend/Main_Continuous_Daily_Trend.ipynb`
  - `Momentum/Main_Continuous_Daily_Momentum.ipynb`
- 数据源：天勤主力连续合约日线，`get_kline_serial(..., duration_seconds=24*60*60, data_length=8000)`。
- 本地落盘目录：`main_continuous_daily_trend_momentum_reversal_research/raw/tq_main_continuous_daily/`。
- 日线字段：`date, open, high, low, close, volume`，并补充 `commodity, commodity_name, main_symbol, data_source`。
- 研究区间：从各品种起始过滤日开始，到 notebook 运行日为止。CSV 中趋势最新日为 2026-06-29，动量最新日为 2026-06-30。

### 2. 核心特征公式

基础收益与波动率：

$$
r_t = \log(C_t / C_{t-1})
$$

$$
\sigma_t = \mathrm{RollingStd}_{20}(r_t)
$$

当 20 日滚动波动率尚不可用时，代码使用 EWMA 波动率作为 fallback。远期标准化收益：

$$
Y_{t,k} = \frac{\log(C_{t+k}/C_t)}{\sigma_t\sqrt{k}}
$$

趋势强度来自 rolling OLS：

$$
\log(C_{t-h+1:t}) = \alpha + \beta x + \epsilon
$$

其中 `TTrend_h` 为斜率 t 值，`TrendFit_h` 为 rolling OLS 的 $R^2$。趋势方向为：

$$
s^{trend}_{t,h} = \mathrm{sign}(TTrend_{t,h})
$$

动量强度来自风险调整时间序列动量：

$$
RAMOM_{t,J} = \sum_{i=1}^{J} \frac{r_{t-i}}{\sigma_{t-i}}
$$

动量一致性：

$$
MCS_{t,J} = \frac{1}{J}\sum_{i=1}^{J}1\{\mathrm{sign}(r_{t-i})=\mathrm{sign}(RAMOM_{t,J})\}
$$

模型评分统一使用方向收益：

$$
DirectedY_{t,k}=s_tY_{t,k}
$$

并计算 `mean_y, Newey-West t, hit_rate, stationary bootstrap p-value`。

### 3. 模型质量分级

候选模型 `CANDIDATE`：

- 样本数 `n >= 60`
- `mean_y > 0`
- Newey-West `t_nw >= 1.0`
- `hit_rate > 0.50`

确认模型 `CONFIRMED`：

- 满足 `CANDIDATE`
- 样本数 `n >= 120`
- Newey-West `t_nw >= 2.0`
- `hit_rate > 0.50`
- stationary bootstrap `p(mean <= 0) <= 0.10` 或 p 值缺失

其余为 `DIAGNOSTIC_ONLY`。在动量状态机中，只有 `CONFIRMED` 或 `CANDIDATE` 模型才可使 `MOMValidatedEstablished=1`。

### 4. 趋势状态机

趋势存在：

$$
|TTrend_h| \ge 2.0,\quad TrendFit_h \ge 0.20
$$

趋势确立：同方向趋势存在状态连续至少 2 天。趋势结束风险与确认结束分开处理：

- `TrendEndRisk`：趋势已确立且 `|TTrend|` 达到历史 90% 扩张分位数或固定阈值下限后的过度延展状态。
- `TrendEndConfirmed`：趋势信号消失、方向反转或 ATR stop 触发。
- `TrendEnd`：等于 `TrendEndConfirmed`，只表示已确认结束；风险状态看 `TrendEndRisk`。

### 5. 动量状态机

动量存在：

$$
|RAMOM_J| \ge 1.0,\quad MCS_J \ge 0.58
$$

动量确立：同方向动量存在状态连续至少 2 天。验证确立还要求最佳模型不是 `DIAGNOSTIC_ONLY`。

动量消失风险与确认消失：

- `MOMEndRisk`：动量已确立且 `|MOMMain|` 达到历史 90% 扩张分位数或固定阈值下限后的极端延展状态。
- `MOMEndConfirmed`：动量强度跌破阈值、方向反转、信号消失或路径一致性破坏。
- `MOMEnd`：等于 `MOMEndConfirmed`。

---

## 四、CSV 文件矩阵

### 1. Trend 输出

| 文件 | 范围 | 问题 | 含义 |
| :--- | :--- | :--- | :--- |
| `trend_q1_existence_current.csv` | 当前截面 | Q1 | 当前是否存在/确立趋势：方向、强度、拟合度、趋势年龄 |
| `trend_q2_duration_current.csv` | 当前截面 | Q2 | 当前趋势还能持续多久：剩余寿命、未来 N 日结束概率、历史同方向 duration 摘要 |
| `trend_q3_end_current.csv` | 当前截面 | Q3 | 当前趋势是否结束/是否有结束风险：确认结束、过度延伸、结束触发项 |
| `trend_hist_q1_existence_model.csv` | 全历史 | Q1 | 全历史趋势存在频率、方向分布、最佳趋势模型有效性 |
| `trend_hist_q2_duration_distribution.csv` | 全历史 | Q2 | 全历史趋势 episode 持续时间分布 |
| `trend_hist_q3_end_risk_survival.csv` | 全历史 | Q3 | 全历史趋势结束风险：按方向、风险状态、horizon 统计未来结束概率 |
| `trend_output_manifest.csv` | 索引 | ALL | Trend 输出文件说明 |

### 2. Momentum 输出

| 文件 | 范围 | 问题 | 含义 |
| :--- | :--- | :--- | :--- |
| `momentum_core_current_summary.csv` | 当前截面 | ALL | 当前动量主表：动量存在、持续周期、消失风险、最佳动量模型汇总 |
| `momentum_q1_existence_current.csv` | 当前截面 | Q1 | 当前是否存在/确立动量：方向、强度、一致性、动量年龄 |
| `momentum_q2_duration_current.csv` | 当前截面 | Q2 | 当前动量还能持续多久：剩余寿命、未来 N 日消失概率、历史同方向 duration 摘要 |
| `momentum_q3_end_current.csv` | 当前截面 | Q3 | 当前动量是否消失/是否有消失风险：确认消失、极端延展、消失触发项 |
| `momentum_hist_q1_existence_model.csv` | 全历史 | Q1 | 全历史动量存在频率、方向分布、最佳动量模型有效性 |
| `momentum_hist_q2_duration_distribution.csv` | 全历史 | Q2 | 全历史动量 episode 持续时间分布 |
| `momentum_hist_q3_end_risk_survival.csv` | 全历史 | Q3 | 全历史动量消失风险：按方向、风险状态、horizon 统计未来消失概率 |
| `momentum_output_manifest.csv` | 索引 | ALL | Momentum 输出文件说明 |

---

## 五、全历史趋势结论

判读规则：`存在/确立` 是全历史日度状态频率；`主导方向` 是确立趋势日内 UP/DOWN 占比更高的一侧；`持续时间` 和 `结束概率` 均只针对主导方向。

| 合约 | 样本 | Q1: 趋势存在 | 最佳趋势模型 | Q2: 主导方向持续时间 | Q3: 主导方向结束概率 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AG 沪银 | 2016-01-05 to 2026-06-29, n=2544 | 存在 67.3%, 确立 65.0%, 主导 UP 59.1% | h=40,K=20, CONFIRMED, t=3.11, hit=50.7%, p=0.000 | UP: median 1d, mean 5.9d, n=167, ended=167, HIGH, risk_rate=20.4% | NO_RISK: 5d=43.9%,10d=59.5%,20d=74.4%; RISK: 5d=26.0%,10d=42.9%,20d=71.8% |
| CF 棉花 | 2016-01-05 to 2026-06-29, n=2544 | 存在 69.8%, 确立 67.6%, 主导 UP 58.8% | h=40,K=10, CANDIDATE, t=1.79, hit=52.0%, p=0.013 | UP: median 1d, mean 7.6d, n=133, ended=133, HIGH, risk_rate=14.3% | NO_RISK: 5d=37.2%,10d=49.7%,20d=63.4%; RISK: 5d=24.1%,10d=41.1%,20d=65.6% |
| EB 苯乙烯 | 2019-09-26 to 2026-06-29, n=1634 | 存在 62.2%, 确立 53.0%, 主导 DOWN 51.7% | h=10,K=2, CONFIRMED, t=2.08, hit=52.5%, p=0.015 | DOWN: median 5d, mean 6.2d, n=72, ended=71, HIGH, risk_rate=37.5% | NO_RISK: 5d=69.6%,10d=89.8%,20d=99.4%; RISK: 5d=32.5%,10d=68.7%,20d=92.2% |
| FG 玻璃 | 2016-01-05 to 2026-06-29, n=2544 | 存在 61.4%, 确立 52.6%, 主导 UP 50.4% | h=10,K=20, CANDIDATE, t=1.72, hit=51.9%, p=0.018 | UP: median 5d, mean 6.6d, n=103, ended=103, HIGH, risk_rate=41.7% | NO_RISK: 5d=69.8%,10d=89.0%,20d=97.9%; RISK: 5d=43.8%,10d=77.6%,20d=100.0% |
| LH 生猪 | 2021-01-08 to 2026-06-29, n=1323 | 存在 72.2%, 确立 69.8%, 主导 DOWN 61.5% | h=40,K=20, CONFIRMED, t=2.13, hit=55.0%, p=0.010 | DOWN: median 1d, mean 5.7d, n=99, ended=99, HIGH, risk_rate=37.4% | NO_RISK: 5d=40.1%,10d=55.4%,20d=75.8%; RISK: 5d=37.5%,10d=50.6%,20d=73.9% |
| M 豆粕 | 2016-01-05 to 2026-06-29, n=2544 | 存在 71.6%, 确立 66.7%, 主导 DOWN 50.1% | h=20,K=10, DIAGNOSTIC_ONLY, t=0.87, hit=49.3%, p=0.180 | DOWN: median 10d, mean 12.7d, n=67, ended=67, HIGH, risk_rate=31.3% | NO_RISK: 5d=39.6%,10d=61.9%,20d=83.9%; RISK: 5d=8.2%,10d=39.5%,20d=76.2% |
| MA 甲醇 | 2016-01-05 to 2026-06-29, n=2544 | 存在 68.3%, 确立 66.0%, 主导 UP 55.7% | h=40,K=20, CONFIRMED, t=2.52, hit=51.3%, p=0.000 | UP: median 1d, mean 6.0d, n=155, ended=155, HIGH, risk_rate=16.1% | NO_RISK: 5d=40.7%,10d=55.1%,20d=77.1%; RISK: 5d=28.6%,10d=51.6%,20d=70.9% |
| SA 纯碱 | 2019-12-06 to 2026-06-29, n=1588 | 存在 71.2%, 确立 66.8%, 主导 DOWN 57.4% | h=20,K=10, CANDIDATE, t=1.37, hit=51.9%, p=0.052 | DOWN: median 10d, mean 14.9d, n=41, ended=40, MEDIUM, risk_rate=34.1% | NO_RISK: 5d=32.7%,10d=54.6%,20d=80.9%; RISK: 5d=18.4%,10d=36.0%,20d=59.6% |
| SP 纸浆 | 2018-11-27 to 2026-06-29, n=1838 | 存在 60.4%, 确立 51.5%, 主导 DOWN 52.3% | h=10,K=20, CANDIDATE, t=1.87, hit=52.1%, p=0.013 | DOWN: median 5d, mean 6.4d, n=77, ended=76, HIGH, risk_rate=39.0% | NO_RISK: 5d=61.0%,10d=84.9%,20d=99.2%; RISK: 5d=51.7%,10d=80.0%,20d=100.0% |
| SR 白糖 | 2016-01-05 to 2026-06-29, n=2544 | 存在 63.4%, 确立 61.8%, 主导 UP 51.4% | h=60,K=20, CANDIDATE, t=1.77, hit=50.7%, p=0.013 | UP: median 1d, mean 4.1d, n=197, ended=197, HIGH, risk_rate=7.1% | NO_RISK: 5d=55.4%,10d=71.7%,20d=91.8%; RISK: 5d=21.7%,10d=32.6%,20d=40.6% |
| V PVC | 2016-01-05 to 2026-06-29, n=2544 | 存在 69.9%, 确立 65.1%, 主导 UP 50.3% | h=20,K=20, CANDIDATE, t=1.84, hit=53.4%, p=0.010 | UP: median 7d, mean 11.0d, n=76, ended=76, HIGH, risk_rate=19.7% | NO_RISK: 5d=41.0%,10d=62.2%,20d=83.6%; RISK: 5d=17.2%,10d=45.1%,20d=77.9% |

全历史趋势的直接结论：

- 11 个合约全历史趋势确立频率均超过 50%，说明按当前规则，趋势状态在全部品种中都不是稀有状态。
- `CONFIRMED` 趋势模型出现在 AG、EB、LH、MA；`CANDIDATE` 出现在 CF、FG、SA、SP、SR、V；M 的趋势模型为 `DIAGNOSTIC_ONLY`，因此 M 的趋势状态频率可描述，但最佳趋势模型不能被写成已验证预测模型。
- 主导方向不是单边一致：AG、CF、FG、MA、SR、V 的历史确立趋势偏 UP；EB、LH、M、SA、SP 偏 DOWN。

---

## 六、当前趋势截面结论

趋势当前截面日期为 **2026-06-29**。

| 合约 | 日期/收盘 | Q1: 当前趋势存在 | 模型 | Q2: 预计剩余 | Q3: 结束判断 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AG 沪银 | 2026-06-29, close=14272 | 已确立 DOWN, age=13d, T=-10.84, Fit=0.76 | h=40,K=20, CONFIRMED | median=15d, mean=15.8d, n=13, LOW | risk=N, confirmed=N, 5d=30.8%,10d=46.2%,20d=69.2% |
| CF 棉花 | 2026-06-29, close=16070 | 已确立 DOWN, age=9d, T=-7.04, Fit=0.57 | h=40,K=10, CANDIDATE | median=9d, mean=16.0d, n=23, MEDIUM | risk=N, confirmed=N, 5d=30.4%,10d=52.2%,20d=73.9% |
| EB 苯乙烯 | 2026-06-29, close=7249 | 已确立 DOWN 且有结束风险, age=10d, T=-10.87, Fit=0.94 | h=10,K=2, CONFIRMED | median=3d, mean=5.6d, n=15, LOW | risk=Y, confirmed=N, 5d=66.7%,10d=80.0%,20d=100.0% |
| FG 玻璃 | 2026-06-29, close=978 | 已确立 DOWN, age=3d, T=-3.90, Fit=0.66 | h=10,K=20, CANDIDATE | median=4d, mean=6.1d, n=77, HIGH | risk=N, confirmed=N, 5d=59.7%,10d=81.8%,20d=96.1% |
| LH 生猪 | 2026-06-29, close=12415 | 已确立 UP, age=7d, T=5.84, Fit=0.47 | h=40,K=20, CONFIRMED | median=10d, mean=9.6d, n=14, LOW | risk=N, confirmed=N, 5d=21.4%,10d=57.1%,20d=100.0% |
| M 豆粕 | 2026-06-29, close=2967 | 未确立趋势, T=0.39, Fit=0.01 | h=20,K=10, DIAGNOSTIC_ONLY | NA | risk=N, confirmed=N, NA |
| MA 甲醇 | 2026-06-29, close=2460 | 已确立 DOWN, age=5d, T=-6.11, Fit=0.50 | h=40,K=20, CONFIRMED | median=11d, mean=15.9d, n=32, MEDIUM | risk=N, confirmed=N, 5d=37.5%,10d=46.9%,20d=68.8% |
| SA 纯碱 | 2026-06-29, close=1103 | 已确立 DOWN, age=13d, T=-10.93, Fit=0.87 | h=20,K=10, CANDIDATE | median=12d, mean=14.9d, n=17, LOW | risk=N, confirmed=N, 5d=23.5%,10d=47.1%,20d=82.4% |
| SP 纸浆 | 2026-06-29, close=4690 | 已确立 DOWN 且有结束风险, age=3d, T=-7.21, Fit=0.87 | h=10,K=20, CANDIDATE | median=4d, mean=6.1d, n=58, HIGH | risk=Y, confirmed=N, 5d=56.9%,10d=82.8%,20d=100.0% |
| SR 白糖 | 2026-06-29, close=5270 | 未确立趋势, T=-2.33, Fit=0.09 | h=60,K=20, CANDIDATE | NA | risk=N, confirmed=N, NA |
| V PVC | 2026-06-29, close=4391 | 已确立 DOWN 且有结束风险, age=27d, T=-19.04, Fit=0.95 | h=20,K=20, CANDIDATE | NA | risk=Y, confirmed=N, NA |

当前趋势的直接结论：

- 已明确确立趋势的合约为 AG、CF、EB、FG、LH、MA、SA、SP、V，共 9 个；M 与 SR 当前未确立趋势。
- 当前趋势方向以 DOWN 为主：AG、CF、EB、FG、MA、SA、SP、V 为 DOWN，LH 为 UP。
- 当前没有任何合约被 `TrendEndConfirmed` 标记为已确认结束。
- EB、SP、V 已进入 `TrendEndRisk`；其中 EB 与 SP 同时有历史同类剩余寿命和结束概率，V 虽有风险标记，但当前表未给出可用剩余寿命估计。

---

## 七、全历史动量结论

判读规则：`signal` 是原始动量信号出现频率，`validated` 是通过连续天数与模型可用性后的验证确立频率；`主导方向`、`持续时间` 与 `消失概率` 均只针对验证确立后的 episode。

| 合约 | 样本 | Q1: 动量存在 | 最佳动量模型 | Q2: 主导方向持续时间 | Q3: 主导方向消失概率 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AG 沪银 | 2016-01-05 to 2026-06-30, n=2545 | signal 31.4%, validated 11.9%, 主导 UP 56.8% | J=2,K=1, CONFIRMED, t=2.44, hit=51.9%, p=0.003 | UP: median 1d, mean 1.7d, n=102, ended=102, HIGH, risk_rate=48.0% | NO_RISK: 5d=99.0%,10d=100.0%,20d=100.0%; RISK: 5d=100.0%,10d=100.0%,20d=100.0% |
| CF 棉花 | 2016-01-05 to 2026-06-30, n=2545 | signal 47.5%, validated 26.6%, 主导 UP 53.3% | J=3,K=2, CONFIRMED, t=3.20, hit=51.0%, p=0.000 | UP: median 2d, mean 2.3d, n=156, ended=156, HIGH, risk_rate=41.0% | NO_RISK: 5d=98.3%,10d=100.0%,20d=100.0%; RISK: 5d=91.0%,10d=100.0%,20d=100.0% |
| EB 苯乙烯 | 2019-09-26 to 2026-06-30, n=1635 | signal 44.5%, validated 37.7%, 主导 UP 51.1% | J=20,K=5, CONFIRMED, t=2.36, hit=54.0%, p=0.003 | UP: median 7d, mean 8.8d, n=36, ended=36, MEDIUM, risk_rate=30.6% | NO_RISK: 5d=42.2%,10d=66.4%,20d=83.2%; RISK: 5d=31.0%,10d=64.8%,20d=98.6% |
| FG 玻璃 | 2016-01-05 to 2026-06-30, n=2545 | signal 20.0%, validated 17.8%, 主导 UP 67.8% | J=40,K=1, CONFIRMED, t=2.13, hit=53.7%, p=0.018 | UP: median 8d, mean 15.4d, n=20, ended=20, MEDIUM, risk_rate=50.0% | NO_RISK: 5d=40.1%,10d=53.5%,20d=67.6%; RISK: 5d=10.2%,10d=29.5%,20d=61.4% |
| LH 生猪 | 2021-01-08 to 2026-06-30, n=1324 | signal 43.0%, validated 37.3%, 主导 DOWN 72.7% | J=20,K=5, CANDIDATE, t=1.56, hit=54.8%, p=0.058 | DOWN: median 5d, mean 10.9d, n=33, ended=33, MEDIUM, risk_rate=30.3% | NO_RISK: 5d=42.1%,10d=61.7%,20d=82.6%; RISK: 5d=20.2%,10d=37.9%,20d=71.8% |
| M 豆粕 | 2016-01-05 to 2026-06-30, n=2545 | signal 48.6%, validated 28.1%, 主导 UP 53.5% | J=3,K=20, CANDIDATE, t=1.36, hit=51.6%, p=0.068 | UP: median 2d, mean 2.4d, n=161, ended=160, HIGH, risk_rate=41.6% | NO_RISK: 5d=95.7%,10d=100.0%,20d=100.0%; RISK: 5d=93.7%,10d=100.0%,20d=100.0% |
| MA 甲醇 | 2016-01-05 to 2026-06-30, n=2545 | signal 51.3%, validated 0.0%, 主导 NA | J=3,K=20, DIAGNOSTIC_ONLY, t=0.73, hit=50.4%, p=0.325 | NA | NA |
| SA 纯碱 | 2019-12-06 to 2026-06-30, n=1589 | signal 33.0%, validated 12.8%, 主导 DOWN 54.7% | J=2,K=2, CONFIRMED, t=2.36, hit=55.0%, p=0.015 | DOWN: median 1d, mean 1.5d, n=74, ended=74, HIGH, risk_rate=41.9% | NO_RISK: 5d=100.0%,10d=100.0%,20d=100.0%; RISK: 5d=100.0%,10d=100.0%,20d=100.0% |
| SP 纸浆 | 2018-11-27 to 2026-06-30, n=1839 | signal 19.5%, validated 17.1%, 主导 UP 63.7% | J=40,K=20, CONFIRMED, t=3.41, hit=66.7%, p=0.000 | UP: median 4d, mean 11.8d, n=17, ended=17, LOW, risk_rate=23.5% | NO_RISK: 5d=39.1%,10d=60.9%,20d=89.1%; RISK: 5d=8.1%,10d=17.7%,20d=29.0% |
| SR 白糖 | 2016-01-05 to 2026-06-30, n=2545 | signal 31.7%, validated 0.0%, 主导 NA | J=2,K=2, DIAGNOSTIC_ONLY, t=1.34, hit=48.8%, p=0.080 | NA | NA |
| V PVC | 2016-01-05 to 2026-06-30, n=2545 | signal 51.9%, validated 31.7%, 主导 UP 51.3% | J=3,K=1, CONFIRMED, t=2.16, hit=50.9%, p=0.015 | UP: median 2d, mean 2.6d, n=162, ended=162, HIGH, risk_rate=36.4% | NO_RISK: 5d=96.1%,10d=99.3%,20d=100.0%; RISK: 5d=92.7%,10d=100.0%,20d=100.0% |

全历史动量的直接结论：

- 动量比趋势更稀疏：除 MA、SR 外，其余 9 个合约均出现过验证确立动量，但验证确立频率最高也仅为 EB 的 37.7% 和 LH 的 37.3%。
- AG、CF、EB、FG、SA、SP、V 的最佳动量模型为 `CONFIRMED`；LH、M 为 `CANDIDATE`；MA、SR 为 `DIAGNOSTIC_ONLY`，因此 MA、SR 没有通过当前规则得到可验证动量 episode。
- AG、CF、M、SA、V 的动量 episode 典型持续时间很短，历史 5 日内消失概率接近或达到 100%；EB、FG、LH、SP 的动量持续分布更长，但样本可靠度多为 MEDIUM 或 LOW。

---

## 八、当前动量截面结论

动量当前截面日期为 **2026-06-30**，这是当前仓库动量 CSV 的实际最新日期。

| 合约 | 日期/收盘 | Q1: 当前动量存在 | 模型 | Q2: 预计剩余 | Q3: 消失判断 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AG 沪银 | 2026-06-30, close=13966 | 未确立动量, side=UP, MOM=0.90, MCS=1.00 | J=2,K=1, CONFIRMED | NA | risk=N, confirmed=N, NA |
| CF 棉花 | 2026-06-30, close=16065 | 未确立动量, side=UP, MOM=0.78, MCS=0.67 | J=3,K=2, CONFIRMED | NA | risk=N, confirmed=N, NA |
| EB 苯乙烯 | 2026-06-30, close=7368 | 已确立 DOWN 且有消失风险, age=10d, MOM=-10.22, MCS=0.70 | J=20,K=5, CONFIRMED | median=6d, mean=8.8d, n=12, OK | risk=Y, confirmed=N, 5d=50.0%,10d=75.0%,20d=83.3% |
| FG 玻璃 | 2026-06-30, close=967 | 动量已确认消失, side=DOWN, MOM=-4.63, MCS=0.57 | J=40,K=1, CONFIRMED | NA | risk=N, confirmed=Y, NA |
| LH 生猪 | 2026-06-30, close=12365 | 未确立动量, side=UP, MOM=3.77, MCS=0.50 | J=20,K=5, CANDIDATE | NA | risk=N, confirmed=N, NA |
| M 豆粕 | 2026-06-30, close=2951 | 已确立 UP, age=2d, MOM=1.01, MCS=0.67 | J=3,K=20, CANDIDATE | median=1d, mean=2.0d, n=108, OK | risk=N, confirmed=N, 5d=94.4%,10d=100.0%,20d=100.0% |
| MA 甲醇 | 2026-06-30, close=2442 | 未确立动量, side=UP, MOM=0.01, MCS=0.67 | J=3,K=20, DIAGNOSTIC_ONLY | NA | risk=N, confirmed=N, NA |
| SA 纯碱 | 2026-06-30, close=1084 | 动量已确认消失, side=DOWN, MOM=-0.78, MCS=0.50 | J=2,K=2, CONFIRMED | NA | risk=N, confirmed=Y, NA |
| SP 纸浆 | 2026-06-30, close=4700 | 未确立动量, side=DOWN, MOM=-10.59, MCS=0.57 | J=40,K=20, CONFIRMED | NA | risk=N, confirmed=N, NA |
| SR 白糖 | 2026-06-30, close=5281 | 未确立动量, side=UP, MOM=1.97, MCS=1.00 | J=2,K=2, DIAGNOSTIC_ONLY | NA | risk=N, confirmed=N, NA |
| V PVC | 2026-06-30, close=4354 | 已确立 DOWN, age=8d, MOM=-2.21, MCS=0.67 | J=3,K=1, CONFIRMED | NA | risk=N, confirmed=N, NA |

当前动量的直接结论：

- 当前仍处于验证确立动量的合约只有 EB、M、V。
- EB 为 DOWN 动量且进入 `MOMEndRisk`，但未确认消失；历史同类剩余寿命 median=6d，20 日内消失概率 83.3%。
- M 为 UP 动量，age=2d，但历史同类 5 日内消失概率已达 94.4%，说明当前动量在历史统计上偏短周期。
- V 为 DOWN 动量且未触发消失风险，但当前表没有给出可用剩余寿命估计。
- FG 与 SA 已被 `MOMEndConfirmed` 标记为动量确认消失。
- AG、CF、LH、MA、SP、SR 当前未确立动量；其中 MA 与 SR 的历史验证确立频率为 0.0%，当前只能描述原始信号状态，不能写成已验证动量。

---

## 九、总体结论

1. **趋势存在性**：按 rolling OLS t 值与拟合度阈值，11 个合约全历史均存在高频率趋势状态；当前 2026-06-29 有 9 个合约趋势已确立。
2. **趋势持续时间**：趋势 episode 的中位数通常较短，但部分品种和方向的均值更长，说明趋势持续时间分布右偏。当前 AG、CF、MA、SA 的剩余寿命估计相对更长；EB、FG、SP 的 10 日内结束概率较高。
3. **趋势结束判断**：当前没有趋势被确认结束；EB、SP、V 进入结束风险状态，需与后续 `TrendEndConfirmed` 区分。
4. **动量存在性**：动量比趋势更稀疏，且 MA、SR 在当前规则下没有验证确立动量 episode。当前 2026-06-30 只有 EB、M、V 处于验证确立动量。
5. **动量持续时间**：AG、CF、M、SA、V 的历史动量多为短周期；EB、FG、LH、SP 的历史动量更长，但部分样本可靠度偏低。
6. **动量消失判断**：当前 FG、SA 已确认动量消失；EB 尚未确认消失但已有消失风险；M 虽然已确立，但历史同类消失概率显示其当前动量偏短命。

---

## 十、后续补充

`Reversal` 子模块后续应沿用同一数据层与输出矩阵：先定义异常收益/过度延展后的反转触发，再将反转 episode 与当前截面输出分为 Q1 存在、Q2 持续/回补窗口、Q3 失效或恢复结束三类。完成后，可把本 README 的反转部分补齐，并将趋势、动量、反转三类信号统一到一个可比较的状态面板中。
