# DETEQX

**基于质谱指纹图谱和AI的疾病样本智能分析系统**
基于 SALDI 质谱与脂质指纹分析的肝癌早筛科研工具

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()
[![Version](https://img.shields.io/badge/Version-1.13.1-green.svg)]()

> **免责声明**：本软件仅供学术研究与科学实验使用，不构成医疗器械，结果不得作为临床诊断依据。任何医疗决策请咨询执业医师。

---

## 📖 项目简介

DETEQX 是一套端到端的质谱数据分析系统，立项起初专为肝细胞癌（HCC）早期筛查设计，不过对于所有疾病都可适用。系统通过分析血清样本的 SALDI 质谱数据（0-1000 m/z 范围），利用脂质指纹特征构建机器学习分类模型，实现对肝癌与正常样本的智能区分。

### 核心能力

- **智能峰发现**：集成 pyOpenMS 专业质谱分析，自动发现并筛选最优特征峰
- **样本级归一化**：支持 Max/Sum/Median 三种归一化方法，消除技术变异
- **严格交叉验证**：RepeatedStratifiedKFold (5折×20重复)，设计参考医疗AI规范
- **多算法支持**：PLS、Random Forest、SVM、LDA、Logistic Regression、MLP
- **完整评估体系**：95%置信区间、ROC曲线、混淆矩阵、敏感度/特异度分析
- **PDF 诊断报告**：自动生成含模型性能指标与评估图表的结构化报告
- **实时状态反馈**：预处理 / 训练 / 预测三阶段 Chip 状态栏，进度一目了然

---

## 🔧 环境配置

### 系统要求

- **Python**: 3.8+
- **操作系统**: Windows / macOS / Linux
- **内存**: 建议 4GB+

### 依赖安装

```bash
pip install -r requirements.txt
```

### 核心依赖

```
numpy >= 1.21.0
pandas >= 1.3.0
scikit-learn >= 1.0.0
scipy >= 1.7.0
matplotlib >= 3.5.0
customtkinter >= 5.0.0
pyopenms >= 3.0.0
joblib >= 1.1.0
pillow >= 9.0.0          # 登录界面图片显示
```

---

## 🚀 快速开始

```bash
python main.py
```

### 标准工作流程

```
┌─────────────────┐
│  1. 数据预处理   │  选择原始质谱文件夹 → 分类 → 选择归一化方法
└────────┬────────┘
         ↓
┌─────────────────┐
│  2. 特征提取     │  pyOpenMS峰发现 → 共识峰筛选 → 构建特征矩阵
└────────┬────────┘
         ↓
┌─────────────────┐
│  3. 模型训练     │  选择算法 → 5×20交叉验证 → 保存最优模型
└────────┬────────┘
         ↓
┌─────────────────┐
│  4. 性能评估     │  ROC曲线 / 混淆矩阵 / 95%CI / 敏感度特异度
└────────┬────────┘
         ↓
┌─────────────────┐
│  5. 样本预测     │  加载新样本 → 自动归一化 → 输出分类结果
└─────────────────┘
```

---

## 📁 项目架构

```
DETEQX/
├── src/
│   │
│   │  # ===== 核心模块 =====
│   ├── main.py                    # 程序入口，主界面管理 (MainGUIManager)
│   ├── config.py                  # 全局配置参数
│   ├── data_store.py              # 运行时数据仓库 + ClassMappingManager
│   │
│   │  # ===== 数据处理 =====
│   ├── data_preprocessor.py       # 数据预处理核心（峰发现+归一化）
│   ├── data_processing.py         # 数据加载 + FeatureDetector
│   │
│   │  # ===== 机器学习 =====
│   ├── model_training.py          # 模型训练引擎
│   ├── model_predictor.py         # 样本预测管理
│   │
│   │  # ===== 界面组件 =====
│   ├── ui_components.py           # GUI组件库（各类Panel）
│   ├── help_system.py             # 帮助系统与用户向导
│   ├── visualization.py           # 图表生成（含95%CI）
│   ├── print_manager.py           # 诊断报告打印
│   │
│   │  # ===== 项目管理 =====
│   ├── project_manager.py         # 多项目管理（创建/切换/删除）
│   ├── output_manager.py          # 输出文件管理
│   │
│   │  # ===== 辅助模块 =====
│   ├── login_system.py            # 登录界面（演示用，无实际验证）
│   ├── parameter_tuning_window.py # 模型参数调优窗口
│   ├── automated_workflow.py      # 自动化工作流（一键预处理→训练→预测）
│   ├── validation_decorators.py   # 验证装饰器
│   └── utils.py                   # 工具函数
│
├── outputs/                       # 输出目录（按项目隔离）
│   └── {project_name}/
│       ├── data/                  # 处理后的特征矩阵
│       ├── models/                # 训练好的模型文件
│       ├── metrics/               # 评估指标数据（每次训练 .json）
│       └── charts/                # 可视化图表
│           └── {model_stem}/      # 与模型同名的独立目录（永久绑定）
│
├── assets/                        # 图标资源
├── requirements.txt
└── README.md
```

### 核心模块职责

| 模块                           | 职责                                    | 关键类/函数                                               |
| ---------------------------- | ------------------------------------- | ---------------------------------------------------- |
| `data_preprocessor.py`       | 峰发现、归一化、特征矩阵构建                        | `DataPreprocessor`, `NormalizationManager`           |
| `data_processing.py`         | 数据加载、预测样本处理                           | `FeatureDetector`, `open_data_file()`                |
| `data_store.py`              | 全局状态管理、类别映射                           | `ClassMappingManager` (单例)                           |
| `model_training.py`          | 交叉验证训练、保存 model bundle + metrics JSON | `ModelTrainer`, `train_model()`                      |
| `model_predictor.py`         | 样本预测、结果格式化                            | `PredictionManager`                                  |
| `visualization.py`           | 图表生成、性能指标计算，图表存入模型同名子目录               | `MetricsCalculator`, `generate_performance_charts()` |
| `print_manager.py`           | PDF 诊断报告生成（ReportLab Platypus）        | `PrintManager`                                       |
| `project_manager.py`         | 多项目管理                                 | `ProjectManager`, `ProjectCreationWizard`            |
| `parameter_tuning_window.py` | 模型超参数调整                               | `ParameterTuningWindow`                              |

### 辅助模块说明

| 模块                              | 说明                  | 状态        |
| ------------------------------- | ------------------- | --------- |
| `login_system.py`               | 演示用登录界面，任意输入可通过     | × 计划删除    |
| `automated_workflow.py`         | 一键完成预处理→训练→预测的自动化流程 | ✅ 可用      |
| `consensus_peak_diagnostics.py` | 共识峰诊断调试脚本           | 🔧 已调整为可用 |

---

## ⚙️ 配置参数

### 特征选择参数 (`config.py`)

```python
MAX_FEATURES = 50           # 最大特征数量
MIN_OCCURRENCE_RATE = 0.5   # 最小出现频率（50%样本中出现）
MIN_FOLD_CHANGE = 1.3       # 最小倍数变化（30%强度差异）
MZ_TOLERANCE = 0.2          # m/z匹配容差
```

### 交叉验证配置

```python
CV_SPLITS = 5               # 5折交叉验证
CV_REPEATS = 20             # 重复20次
CV_RANDOM_STATE = 42        # 随机种子（可复现）
# 总训练次数: 5 × 20 = 100
```

### 支持的模型

| 模型                         | 配置               | 适用场景         |
| -------------------------- | ---------------- | ------------ |
| **PLSRegression** (默认)     | n_components=4   | 质谱数据首选，高维小样本 |
| RandomForestClassifier     | n_estimators=250 | 大数据集，稳定性优先   |
| LinearSVC                  | max_iter=5000    | 线性可分数据       |
| LinearDiscriminantAnalysis | shrinkage='auto' | 降维+分类        |
| LogisticRegressionCV       | Cs=20, cv=5      | 小数据集，可解释性    |
| MLPClassifier              | hidden=(100,)    | 复杂非线性模式      |

> 💡 可通过菜单栏"参数调优"窗口修改模型超参数

---

## 🔬 技术要点

### 1. 归一化架构 (v1.9.8+)

**设计原则**：样本级归一化（within-sample），非跨样本操作，无数据泄露风险。

```
原始质谱数据
     ↓
峰发现（pyOpenMS）
     ↓
收集统计特征 {max, sum, median}
     ↓
应用归一化: intensity_norm = intensity_raw / stat_value
     ↓
特征选择 → 矩阵构建
```

**归一化方法对比**：

| 方法           | 公式            | 特点             |
| ------------ | ------------- | -------------- |
| **max** (推荐) | I / I_max     | 保持相对强度，范围[0,1] |
| sum (TIC)    | I / Σ(I)      | 消除进样量差异        |
| median       | I / median(I) | 对极端值稳健         |

**预测时归一化**：归一化方法随模型一起打包保存于 model bundle（v1.11.7+），预测时直接读取，无需依赖文件名或训练 CSV。

### 2. 交叉验证方法 (v1.9.7+)

**从 Monte Carlo 升级为 RepeatedStratifiedKFold**：

| 对比项    | 旧方法 (v1.9.6) | 新方法 (v1.9.7+)           |
| ------ | ------------ | ----------------------- |
| 方式     | 500次随机采样     | 5折×20重复                 |
| 样本测试次数 | 不均匀          | 每样本恰好20次                |
| 方差估计   | 可能低估         | 无偏估计                    |
| 计算时间   | 基准           | ~20%基准                  |
| 符合标准   | -            | FDA/NMPA, Nature/Lancet |

### 3. 类别映射管理 (v1.9.9+)

**统一使用 `ClassMappingManager` 单例**：

```python
from data_store import class_manager

# 读取
class_manager.class_0_name      # 'HCC'
class_manager.class_1_name      # 'Normal'
class_manager.names             # ('HCC', 'Normal')

# 编码/解码
class_manager.encode('HCC')     # 0
class_manager.decode(0)         # 'HCC'

# 设置
class_manager.set_names('HCC', 'Normal')
```

### 4. 可视化与统计 (v1.9.5+)

**MetricsCalculator 统一计算所有指标**，避免重复计算：

- 所有图表包含 **95%置信区间**（t分布）
- 性能指标表格输出为 CSV（便于复制）
- `MetricsTable.csv` 中 Sensitivity/Specificity 行标签绑定实际类别名（如 `Sensitivity – HCC`），避免类别互换时产生歧义（v1.11.8+）
- 图表存储：每次训练生成独立子目录 `charts/{ModelType}_{timestamp}/`，与模型文件永久绑定，后续训练不覆盖旧图表（v1.12.5+）

### 5. 多项目管理

**ProjectManager 支持**：

- 创建/删除/切换项目
- 每个项目独立的输出目录
- 项目描述和元信息管理

### 6. Model Bundle 格式 (v1.11.7+)

模型保存为 dict bundle，包含预测所需的全部元数据：

```python
model_bundle = {
    "model":                sklearn 模型对象,
    "training_features":    训练特征 m/z 列表（用于预测时特征对齐）,
    "normalization_method": 'max' / 'sum' / 'median' / None,
    "pls_threshold":        PLS 决策阈值均值（仅 PLS 模型）,
}
```

跨会话、自动化流程、切换模型后均可直接预测，不再依赖训练 CSV 文件。旧格式（纯 sklearn 对象）不再兼容，加载时明确报错。

### 7. 训练指标文件格式 (v1.11.9+)

每次训练生成 `metrics/{ModelType}_{timestamp}.json`，与模型文件同名同戳：

```json
{
  "meta": {
    "model": "PLSRegression",
    "timestamp": "20260321_1805",
    "cv": "5折×20次重复 (100次迭代)",
    "n_samples": 19,
    "class_names": ["HCC", "Normal"],
    "threshold_strategy": "Youden's J"
  },
  "confusion_matrices": [{"tn": 10, "fp": 0, "fn": 0, "tp": 9}, ...],
  "f_scores": [{"precision": 1.0, "recall": 1.0, "f1": 1.0}, ...],
  "auc_list": [...],
  "fpr_values": [...],
  "tpr_values": [...]
}
```

历史数据永不覆盖，JSON 可直接查阅。

### 8. PDF 诊断报告 (v1.12.2+)

使用 ReportLab Platypus 布局引擎生成结构化报告：

- **内容**：病人信息表格、预测结果、模型性能指标（AUC/灵敏度/特异度/F1，含 95% CI）、评估图表（ROC 曲线 + 混淆矩阵并排）
- **图表绑定**：从 metrics JSON 反推 `charts/{stem}/` 路径，确保报告图表与模型一一对应
- **预览**：生成临时 PDF 后调起系统默认阅读器，所见即所得
- **免责声明**：报告末尾自动追加"仅供临床参考，不得作为诊断依据"声明

### 9. 首次启动免责声明 (v1.13.1+)

首次运行时强制弹出使用须知，用户勾选同意后方可继续：

- 同意记录以 **HMAC-SHA256** 签名，存入 `help_config.json` 的 `_ev` 字段
- 记录绑定机器 hostname，手动篡改任意字段后签名校验失败，下次启动重新弹出
- 已同意的机器后续打开向导时不再显示须知 tab

---

## 📊 输出文件

### 数据文件

```
outputs/{project}/data/
└── data_{method}.csv          # 特征矩阵（method: max/sum/median/raw）
```

**CSV结构**：

```
m/z_123.45, m/z_234.56, ..., label
0.85,       0.23,       ..., HCC
0.12,       0.67,       ..., Normal
```

### 模型文件

```
outputs/{project}/models/
└── {ModelType}_{timestamp}.joblib    # 如 PLSRegression_20251201_143022.joblib
```

### 评估图表

```
outputs/{project}/charts/
└── {ModelType}_{timestamp}/          # 每次训练独立目录，与模型文件同名
    ├── ClassPerformance.png          # Sensitivity/Specificity/Precision 小提琴图
    ├── BalanceMetrics.png            # F1-Score/MCC 小提琴图
    ├── ConfusionMatrix.png           # 平均混淆矩阵
    ├── ROC_Curve.png                 # ROC曲线（含AUC±CI）
    ├── MetricsTable.csv              # 性能指标汇总表（含类别标签）
    └── PLS_Thresholds.png            # PLS阈值分布（仅PLS模型）
```

---

## 🔄 版本历史

### v1.13.x (2026-03) 合规安全

- **首次启动免责声明**：强制弹出使用须知，HMAC-SHA256 签名防篡改，记录绑定机器 hostname
- 向导弹窗尺寸扩大（750×600），措辞调整（"筛查"→"分析"，"符合"→"参考"）

### v1.12.x (2026-03) ⭐ 诊断报告重构

- **PDF 报告全面升级**：从 `canvas.drawString` 迁移至 ReportLab Platypus，支持表格、图表嵌入、自动分页
- **模型性能指标入报告**：AUC / 灵敏度 / 特异度 / F1（含 95% CI）自动写入"模型信息"节
- **预览改为真实 PDF**：生成临时文件后调起系统 PDF 阅读器，所见即所得
- **图表存储架构重构**：`charts/latest` + `archive/` → `charts/{model_stem}/`，图表与模型永久绑定
- 病人信息区域改为表格布局；标题行加入应用图标；末尾追加免责声明
- 打印勾选项根据 `data_store` 当前数据自动设置默认状态
- 修复自动化工作流加载数据少一个样本的 Bug

### v1.11.x (2026-03) 稳定性与架构

- **Model Bundle 格式**：模型保存为包含特征列表、归一化方法、PLS 阈值的 dict，跨会话预测不再依赖训练 CSV
- **训练指标改为 JSON**：6 个分散文件合并为单个 `{stem}.json`，含具名混淆矩阵与元数据
- **启动体验优化**：`-alpha=0` 方案消除逐步渲染；新增卡片式闪屏；修复高 DPI 子窗口居中偏移
- Sensitivity/Specificity 标签绑定实际类别名，消除类别互换歧义
- 修复面板宽度被长文字撑开的布局问题
- 修复切换模型后特征缓存不刷新导致预测静默出错的 Bug

### v1.10.x (2026-03) ⭐ 状态栏重构

- **新增三状态 Chip 栏**：预处理 / 训练 / 预测各有独立状态指示（○等待 / ◐进行中 / ✓完成 / ✗失败 / ◼已终止）
- 自动化工作流适配回调机制，替代原轮询逻辑，修复 chip 不更新问题
- 「开始训练」按钮防重入保护，操作期间自动禁用

### v1.9.12.x (2026-03)

- 自动化工作流级联更新，正式可用
- 菜单栏改用 Unicode 图标，单一功能项减少点击层级
- 新增「关于 DETEQX」对话框
- 可视化面板空状态占位符
- 项目命名支持更多字符，新增「+ 日期」快捷按钮
- 帮助向导内容更新（修正 CSV 文件名、交叉验证轮数描述）

### v1.9.11 (2026-02)

- 代码精简：删除未使用 import 6 处、未使用函数/方法 38 个，减少约 500 行

### v1.9.10.x (2025-12)

- 修复 ROC 曲线使用硬标签的 Bug（改用连续分数）
- 合并 `feature_detector.py` 到 `data_processing.py`
- 统一 `normalization_method` 命名规范

### v1.9.9 (2025-11)

- 引入 `ClassMappingManager` 集中管理类别映射
- 新增菜单栏"类别设置"对话框

### v1.9.8.x (2025-11) ⭐ 重大更新

- **归一化架构重构**：样本级归一化，支持 max/sum/median
- **新增 Max 归一化**：性能优于 TIC，成为默认方法
- **图表归档系统**（已被 v1.12.5 取代）

### v1.9.7 (2025-11) ⭐ 重大更新

- **交叉验证升级**：Monte Carlo → RepeatedStratifiedKFold
- 训练次数从 500 降至 100，统计可靠性反而提升
- 新增 95%CI 报告

### v1.9.5.x (2025-10)

- 可视化模块重构，引入 `MetricsCalculator`
- 所有图表增加 95%置信区间显示
- 性能提升约 37.5%

---

## 📝 开发备忘

### 若要添加新功能

1. **UI 功能**：在 `ui_components.py` 创建新 Panel 类
2. **业务逻辑**：创建新 Manager 类
3. **数据操作**：在 `data_store.py` 添加管理函数
4. **配置参数**：在 `config.py` 添加常量

### 关键设计模式

- **中介者模式**：`MainGUIManager` 协调所有组件
- **单例模式**：`data_store`, `class_manager`, `output_manager`
- **装饰器模式**：`validation_decorators.py` 统一错误处理

### 日志记录

```python
from utils import log_message
log_message("操作成功", "SUCCESS")  # INFO, SUCCESS, WARNING, ERROR
```

### 已知限制

- **UI 线程阻塞**：预处理、训练均在主线程运行，小样本场景（20~40 个）通过增密 `root.update()` 缓解，大数据集或低性能设备仍可能卡顿；根本解决方案为 `threading.Thread` + 消息队列
- **参数配置不持久化**：`parameter_tuning_window.py` 的超参数修改重启后重置，演示场景影响不大
- **批次效应**：跨批次样本验证显示约 10% 精度下降，属科学问题，取决于后续数据

---

**最后更新**: 2026年3月
**当前版本**: v1.13.1
