# DETEQX

**基于质谱指纹图谱和AI的疾病阴阳性筛查系统**  
基于 SALDI 质谱与脂质指纹分析的肝癌早筛智能诊断系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()
[![Version](https://img.shields.io/badge/Version-1.9.10.2-green.svg)]()

---

## 📖 项目简介

DETEQX 是一套端到端的质谱数据分析系统，立项起初专为肝细胞癌（HCC）早期筛查设计，不过对于所有疾病都可适用。系统通过分析血清样本的 SALDI 质谱数据（0-1000 m/z 范围），利用脂质指纹特征构建机器学习分类模型，实现对肝癌与正常样本的智能区分。

### 核心能力

- **智能峰发现**：集成 pyOpenMS 专业质谱分析，自动发现并筛选最优特征峰
- **样本级归一化**：支持 Max/Sum/Median 三种归一化方法，消除技术变异
- **严格交叉验证**：RepeatedStratifiedKFold (5折×20重复)，符合医疗AI验证标准
- **多算法支持**：PLS、Random Forest、SVM、LDA、Logistic Regression、MLP
- **完整评估体系**：95%置信区间、ROC曲线、混淆矩阵、敏感度/特异度分析

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
# 直接启动主程序
python main.py

# 或通过登录界面启动（演示用）
python login_system.py
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
│   ├── automated_workflow.py      # 自动化工作流（⚠️ 暂不可用）
│   ├── validation_decorators.py   # 验证装饰器
│   └── utils.py                   # 工具函数
│
├── outputs/                       # 输出目录（按项目隔离）
│   └── {project_name}/
│       ├── data/                  # 处理后的特征矩阵
│       ├── models/                # 训练好的模型文件
│       ├── metrics/               # 评估指标数据
│       └── charts/                # 可视化图表
│           └── archive/           # 历史图表归档
│
├── assets/                        # 图标资源
├── requirements.txt
└── README.md
```

### 核心模块职责

| 模块                           | 职责             | 关键类/函数                                               |
| ---------------------------- | -------------- | ---------------------------------------------------- |
| `data_preprocessor.py`       | 峰发现、归一化、特征矩阵构建 | `DataPreprocessor`, `NormalizationManager`           |
| `data_processing.py`         | 数据加载、预测样本处理    | `FeatureDetector`, `open_data_file()`                |
| `data_store.py`              | 全局状态管理、类别映射    | `ClassMappingManager` (单例)                           |
| `model_training.py`          | 交叉验证训练、模型保存    | `ModelTrainer`, `train_model()`                      |
| `model_predictor.py`         | 样本预测、结果格式化     | `PredictionManager`                                  |
| `visualization.py`           | 图表生成、性能指标计算    | `MetricsCalculator`, `generate_performance_charts()` |
| `project_manager.py`         | 多项目管理          | `ProjectManager`, `ProjectCreationWizard`            |
| `parameter_tuning_window.py` | 模型超参数调整        | `ParameterTuningWindow`                              |

### 辅助模块说明

| 模块                              | 说明                  | 状态             |
| ------------------------------- | ------------------- | -------------- |
| `login_system.py`               | 演示用登录界面，任意输入可通过     | ✅ 可用           |
| `automated_workflow.py`         | 一键完成预处理→训练→预测的自动化流程 | ⚠️ 暂不可用（未级联更新） |
| `consensus_peak_diagnostics.py` | 共识峰诊断调试脚本           | 🔧 开发调试用       |

---

## ⚙️ 配置参数

### 特征选择参数 (`config.py`)

```python
MAX_FEATURES = 50           # 最大特征数量
MIN_OCCURRENCE_RATE = 0.5   # 最小出现频率（50%样本中出现）
MIN_FOLD_CHANGE = 1.3       # 最小倍数变化（30%强度差异）
MZ_TOLERANCE = 0.2          # m/z匹配容差
```

### 峰检测参数 (pyOpenMS)

```python
SIGNAL_TO_NOISE = 1.0       # 信噪比阈值
SPACING_DIFFERENCE = 1.5    # 峰间距要求
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

**预测时归一化**：从训练数据文件名自动推断（如 `data_max.csv` → max方法）

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
- 图表归档系统：`/charts/` 存最新，`/charts/archive/` 存历史

### 5. 多项目管理

**ProjectManager 支持**：

- 创建/删除/切换项目
- 每个项目独立的输出目录
- 项目描述和元信息管理

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
├── ClassPerformance.png      # Sensitivity/Specificity/Precision 小提琴图
├── BalanceMetrics.png        # F1-Score/MCC 小提琴图
├── ConfusionMatrix.png       # 平均混淆矩阵
├── ROC_Curve.png             # ROC曲线（含AUC±CI）
├── MetricsTable.csv          # 性能指标汇总表
├── PLS_Thresholds.png        # PLS阈值分布（仅PLS模型）
└── archive/
    └── 20251201_143022/      # 历史归档
```

---

## 🔄 版本历史

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
- **预测时自动归一化**：从文件名推断训练时使用的方法
- **图表归档系统**：latest + archive 模式

### v1.9.7 (2025-11) ⭐ 重大更新

- **交叉验证升级**：Monte Carlo → RepeatedStratifiedKFold
- 训练次数从 500 降至 100，统计可靠性反而提升
- 新增 95%CI 报告

### v1.9.5.x (2025-10)

- 可视化模块重构，引入 `MetricsCalculator`
- 所有图表增加 95%置信区间显示
- 性能提升约 37.5%
- 新增登录界面（演示用），启用方式见下方说明

---

## 🛠️ 故障排除

### 常见问题

**Q: "未发现任何有效峰"**

- 检查输入文件格式（两列：m/z 和 intensity）
- 尝试降低 `SIGNAL_TO_NOISE` 参数

**Q: "共识特征峰数量不足"**

- 降低 `MIN_OCCURRENCE_RATE`（如 0.3）
- 降低 `MIN_FOLD_CHANGE`（如 1.2）
- 确认两类样本有足够差异

**Q: 预测结果与训练不一致**

- 确认使用正确的训练数据文件（文件名包含归一化方法）
- 检查日志是否显示"检测到归一化方法: xxx"

**Q: 界面冻结**

- 正常现象，100轮交叉验证需要约1-2分钟
- 可在 `config.py` 中临时降低 `CV_REPEATS` 加速测试

---

## 📝 开发备忘

### 启用登录界面

修改 `main.py` 末尾的启动代码：

```python
# 直接启动（默认）
if __name__ == "__main__":
    root = ctk.CTk()
    app = MainGUIManager(root)
    root.mainloop()

# 通过登录界面启动（取消注释以下代码）
# if __name__ == "__main__":
#     from login_system import SimpleLogin
#     login = SimpleLogin()
#     login.run()
```

### 添加新功能

1. **UI功能**：在 `ui_components.py` 创建新 Panel 类
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

### 待修复/完善

- [ ] `automated_workflow.py` - 需要级联更新以适配新架构
- [ ] 批次效应处理 - 跨批次验证显示约10%准确率下降

---

## 📚 相关文档

- `docs/normalization_methods.md` - 归一化方法技术文档
- `docs/cross_validation_guide.md` - 交叉验证方法对比
- `docs/feature_selection_guide.md` - 特征数量选择指南

---

**最后更新**: 2025年1月  
**当前版本**: v1.9.10.2
