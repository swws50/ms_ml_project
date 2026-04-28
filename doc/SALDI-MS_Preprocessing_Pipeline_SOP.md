# SALDI-MS 脂质组学数据预处理标准流程

> 基于质谱代谢组学领域通用 SOP，针对 SALDI-MS + HCC 筛查场景整理。
> 用于对比 DETEQX 现有 Python 实现，识别差距与改进方向。

---

## 总览：处理链全貌

```
Raw mzML
  │
  ├─ 1. 峰识别（Peak Picking）
  │     pyOpenMS, SNR=1.0, spacing_difference=1.5
  │
  ├─ 2. 峰对齐（Peak Alignment / Consensus Peak Finding）
  │     层次聚类 (complete linkage, tolerance=0.2 Da)
  │     输出：统一的 m/z × sample 特征矩阵
  │
  ├─ 3. 空白扣除（Blank Subtraction）
  │     剔除在空白样本中也出现的峰（背景/基质干扰）
  │
  ├─ 4. 缺失峰筛选（Occurrence Rate Filtering）
  │     保留在 ≥ 50% 样本中出现的峰
  │     目的：剔除偶发性、不可靠的信号
  │
  ├─ 5. 缺失值填充（Missing Value Imputation）
  │     Per-feature half-minimum：每个峰取所有样本中最小非零值 / 2
  │     假设：缺失 = 低于检测限，信号存在但未被捕获
  │
  ├─ 6. 样本级归一化（Sample-level Normalization）
  │     Max / TIC(Sum) / Median，校正样本间系统性偏差
  │     属于分析化学归一化（within-sample），不引入数据泄漏
  │
  ├─ 7. 对数转换（Log₂ Transformation）
  │     压缩右偏分布，将乘法关系转为加法关系
  │     log₂ 的优势：差 1 = 2 倍变化，直接读 fold change
  │     前提：矩阵中不能有零值（第 5 步已保证）
  │
  ├─ 8. 特征缩放（Pareto Scaling）
  │     x_scaled = (x - mean) / √SD
  │     折中方案：削弱高方差特征主导性，但不像 Z-score 那样完全拉平
  │     保留高丰度特征的部分权重优势
  │
  ├─ 9. 特征筛选（Feature Selection）——三层联合筛选
  │     ┌─ 9a. Occurrence Rate ≥ 0.5（已在第 4 步完成）
  │     ├─ 9b. Fold Change ≥ 1.3（效应大小，生物学意义）
  │     └─ 9c. Mann-Whitney U + BH-FDR adjusted p < 0.05（统计显著性）
  │     三项指标同时计算，取交集
  │
  └─ 10. 建模（Model Training）
        交叉验证 → 模型选择 → 性能评估
```

---

## 各步骤详解

### 1. 峰识别（Peak Picking）

- **工具**：pyOpenMS `PeakPickerHiRes` 或 centroiding 算法
- **关键参数**：signal_to_noise = 1.0, spacing_difference = 1.5
- **输入**：原始 mzML 文件
- **输出**：每个样本的峰列表 [(m/z, intensity), ...]

### 2. 峰对齐 / 共识峰识别（Consensus Peak Finding）

**问题**：同一种脂质在不同样本中的 m/z 值存在仪器漂移，需要将"几乎一样"的峰归为同一个特征。

**推荐方案：层次聚类 + Complete Linkage**

```python
from scipy.cluster.hierarchy import fcluster, linkage
import numpy as np

def find_consensus_peaks(all_mz_values, tolerance=0.2):
    mz_sorted = np.sort(all_mz_values)
    Z = linkage(mz_sorted.reshape(-1, 1), method='complete')
    labels = fcluster(Z, t=tolerance, criterion='distance')
    return labels
```

- Complete linkage 要求 cluster 内任意两点距离 ≤ tolerance，杜绝链式漂移
- 每个 cluster 的中位数作为共识峰的 m/z 代表值
- 对比贪心匹配：结果确定性强，不受处理顺序影响

**输出**：m/z（特征） × sample（样本）的强度矩阵，缺失位置为 NaN

### 3. 空白扣除（Blank Subtraction）

- 剔除在空白/溶剂对照样本中也出现的峰
- 这些峰代表基质干扰、溶剂信号、仪器背景，不携带生物学信息
- **必须在归一化之前**：否则噪声信号参与归一化基数，污染归一化系数

### 4. 缺失峰筛选（Occurrence Rate Filtering）

```python
# 保留在至少 50% 样本中出现的峰
threshold = 0.5
occurrence_rate = (df > 0).sum(axis=0) / len(df)
df_filtered = df.loc[:, occurrence_rate >= threshold]
```

- **必须在填充和归一化之前**：避免对不可靠的峰做无意义的填充和运算
- **必须在统计检验之前**：出现率太低的峰没有足够数据点做有意义的检验

### 5. 缺失值填充（Missing Value Imputation）

**方法：Per-feature Half-minimum**

```python
# 每个峰：该峰所有样本中最小非零值 / 2
df_imputed = df.apply(lambda col: col.fillna(col[col > 0].min() / 2))
```

- **原理**：缺失 ≠ 不存在，而是低于检测限（LOD）。取最小观测值的一半作为保守估计
- **为什么 per-feature**：不同 m/z 峰天然丰度差异巨大，必须按各自量级填充
- **为什么在归一化之前**：归一化计算需要完整矩阵，不能有 NaN
- **为什么在 log 之前**：log(0) 无定义，必须先消除零值

### 6. 样本级归一化（Sample-level Normalization）

| 方法 | 公式 | 特点 |
|------|------|------|
| Max | x / max(x_sample) | 简单稳健，受极端值影响 |
| TIC (Sum) | x / sum(x_sample) | 经典方法，但会压缩组间方差 |
| Median | x / median(x_sample) | 抗离群值，但受零值影响大 |

- **性质**：分析化学归一化（within-sample），不涉及跨样本信息，不引入数据泄漏
- **与 ML 归一化的区别**：Z-score 等跨样本归一化必须在 CV fold 内做，防止数据泄漏
- **DETEQX 现状**：Max normalization 为默认，表现优于 TIC 和 Median

### 7. 对数转换（Log₂ Transformation）

```python
df_log = np.log2(df_normalized)
```

- **作用**：压缩右偏分布，使高/低丰度特征的数值范围更可比
- **解读**：log₂ 值差 1 = 原始强度差 2 倍，直接对应 fold change
- **前提**：矩阵中所有值 > 0（第 5 步 half-minimum 已保证）
- **必须在归一化之后**：先让样本可比，再压缩分布
- **必须在 Pareto scaling 之前**：先压缩量级，再做缩放效果更稳定

### 8. 特征缩放（Pareto Scaling）

```python
mean = df_log.mean()
sd = df_log.std()
df_pareto = (df_log - mean) / np.sqrt(sd)
```

- **与 Auto Scaling (Z-score) 的对比**：Z-score 除以 SD，所有特征方差完全拉平 → 噪声特征被过度放大；Pareto 除以 √SD，折中保留高丰度特征的部分权重
- **适用场景**：代谢组学/脂质组学数据的默认推荐
- **注意**：这是跨样本操作，如果在 ML pipeline 中使用，应在 CV fold 内计算 mean 和 SD

### 9. 特征筛选（Feature Selection）

三个维度联合筛选，取交集：

#### 9a. Occurrence Rate（数据质量）
- 已在第 4 步完成

#### 9b. Fold Change（效应大小）

```python
# HCC 组均值 / Normal 组均值
fc = hcc_mean / normal_mean
significant_fc = (fc >= 1.3) | (fc <= 1/1.3)  # 双向筛选
```

- 保证组间差异具有生物学意义，而非仅统计噪声

#### 9c. Mann-Whitney U + BH-FDR（统计显著性）

```python
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests

p_values = []
for feature in features:
    _, p = mannwhitneyu(
        hcc_group[feature],
        normal_group[feature],
        alternative='two-sided'
    )
    p_values.append(p)

reject, adjusted_p, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
```

- **Mann-Whitney U**：非参数检验，不依赖正态分布假设，基于秩次，抗离群值
- **BH-FDR**：控制假发现率，比 Bonferroni 更适合特征数较多的场景
- **适用条件**：两组独立样本（HCC vs Normal 血清样本符合）

#### 联合筛选

```python
selected = (occurrence_rate >= 0.5) & (abs_fc >= 1.3) & (adjusted_p < 0.05)
final_features = df.columns[selected]
```

可视化为 **Volcano Plot**：横轴 log₂(FC)，纵轴 -log₁₀(adjusted_p)

### 10. 建模

筛选后的特征进入建模阶段：

- 交叉验证：RepeatedStratifiedKFold (5×20 = 100 iterations)
- 模型选择：PLS-DA / RF / LDA / SVC / LR / MLP
- 评估指标：Sensitivity, Specificity, AUC-ROC

---

## DETEQX 现有实现 vs 标准流程对比检查表

| 步骤 | 标准流程 | DETEQX 现状 | 差距 |
|------|----------|-------------|------|
| 峰识别 | pyOpenMS | ✅ 已实现 | — |
| 峰对齐 | 层次聚类 (complete linkage) | 贪心匹配 + 0.2 Da | 可能存在链式漂移 |
| 空白扣除 | 归一化前剔除 | ❓ 待确认 | — |
| 出现率筛选 | ≥ 50% | ✅ MIN_OCCURRENCE_RATE=0.5 | — |
| 缺失值填充 | Per-feature half-minimum | ❓ 待确认 | — |
| 归一化 | Max / TIC / Median | ✅ Max normalization | — |
| Log₂ 转换 | 归一化后，scaling 前 | ❌ 未实现 | 可选改进 |
| Pareto Scaling | log 后，特征选择前 | ❌ 未实现 | 可选改进 |
| Fold Change 筛选 | ≥ 1.3 | ✅ MIN_FOLD_CHANGE=1.3 | — |
| 统计检验 | Mann-Whitney U + BH-FDR | ❌ 未实现 | 建议添加 |
| 建模 | CV + 多模型比选 | ✅ 5×20 RSKF, 6 algorithms | — |

---

## 注意事项

1. **Log₂ + Pareto 不是必须的**：如果现有 pipeline 性能已经满足需求，不必强行添加。添加后需要重新调参和评估，可能影响现有模型表现。

2. **Pareto Scaling 是跨样本操作**：在 CV pipeline 中使用时，mean 和 SD 必须仅从训练集计算，再 apply 到测试集，防止数据泄漏。

3. **统计检验应在 CV 外部做**：Mann-Whitney U + BH-FDR 用于整体特征筛选（确定候选特征集），不应在每个 CV fold 内重复做，否则引入选择偏差。

4. **Fold Change 的计算时机**：应在归一化之后、log 转换之前计算（或在 log 域计算 log₂FC = mean_log_HCC - mean_log_Normal），两者等价。

5. **所有预处理步骤的顺序不可随意调换**：每一步都依赖前一步的输出是干净、完整的。
