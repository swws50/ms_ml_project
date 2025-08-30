# Python文件功能说明文档

## 核心入口文件

### `main.py` - 程序主入口
**功能**: 程序启动入口，主界面管理和组件协调
**主要类**:
- `MainGUIManager`: 主界面管理器，协调所有UI组件和业务逻辑

**核心方法**:
- `__init__()`: 初始化界面和管理器
- `handle_file_select()`: 处理数据文件选择
- `handle_start_training()`: 启动模型训练流程
- `handle_predict_file()`: 处理样本预测
- `handle_reset_progress()`: 重置系统状态

**职责**: 作为中介者模式的协调器，管理用户交互和模块间通信

---

### `__init__.py` - 包初始化
**功能**: 将项目定义为Python包，提供统一导入接口
**导出模块**:
- `create_gui`: 主入口函数
- `config`: 配置模块
- `utils`: 工具函数模块

---

## 核心业务模块

### `config.py` - 配置管理
**功能**: 集中管理系统配置参数、文件路径和模型参数
**核心常量**:
- `MAX_FEATURES`: 最大特征数量(50)
- `MIN_OCCURRENCE_RATE`: 最小出现频率(0.2)
- `MODEL_CONFIGS`: 各算法的参数配置

**主要函数**:
- `get_class_mapping()`: 获取动态类别映射
- `get_normalization_factor()`: 获取归一化因子
- `save_normalization_factor()`: 保存归一化因子
- `get_output_paths()`: 动态生成输出文件路径

**职责**: 统一管理配置参数，支持动态路径和类别名称

---

### `data_store.py` - 数据存储管理
**功能**: 全局数据仓库，管理运行时共享数据
**存储数据类型**:
- 文件分类信息 (`_file_classification`)
- 训练数据 (`_training_data`)
- 最佳模型 (`_best_model`)
- 最新预测结果 (`_latest_prediction`)

**主要函数**:
- `set_file_classification()`: 设置文件分类
- `get_training_data()`: 获取训练数据
- `set_best_model()`: 保存最佳模型
- `clear_all_data()`: 清空所有数据
- `get_system_status()`: 获取系统整体状态

**职责**: 作为单例模式的数据中心，避免模块间数据传递

---

## 数据处理模块

### `data_processing.py` - 传统数据处理
**功能**: 处理传统格式数据加载和基本数据操作
**主要函数**:
- `open_data_file()`: 打开并验证CSV数据文件
- `get_file_classification()`: 根据文件路径获取分类

**装饰器支持**:
- `@safe_data_processing`: 安全数据处理
- `@handle_file_operations`: 文件操作错误处理

**职责**: 处理已预处理数据的加载和验证

---

### `data_preprocessor.py` - 智能数据预处理器
**功能**: 实现智能峰发现和文件分类对话框
**主要类**:
- `DataPreprocessor`: 数据预处理器主类

**核心方法**:
- `show_classification_dialog()`: 显示文件分类对话框
- `process_classified_files()`: 处理已分类文件
- `_phase1_discover_peaks()`: 阶段1-峰发现
- `_phase2_consensus_peaks()`: 阶段2-共识峰识别
- `_phase3_build_matrix()`: 阶段3-特征矩阵构建
- `_discover_peaks_from_file()`: 从单文件发现峰

**职责**: 集成pyOpenMS进行专业质谱分析，提供文件夹分类UI

---

### `feature_detector.py` - 特征检测器
**功能**: 特征检测和样本预处理的统一管理
**主要类**:
- `FeatureDetector`: 特征检测器类

**核心方法**:
- `load_training_features()`: 检测训练特征和归一化因子
- `process_prediction_sample()`: 处理预测样本文件
- `validate_sample_file()`: 验证样本文件格式
- `_extract_intensity_for_mz()`: 为指定m/z值提取强度

**职责**: 在训练和预测间建立特征匹配桥梁

---

## 机器学习模块

### `model_training.py` - 模型训练引擎
**功能**: 专门负责机器学习模型训练和评估
**主要类**:
- `ModelTrainer`: 模型训练器类
- `TrainingUI`: 训练界面处理类

**核心方法**:
- `train_model()`: 执行完整训练流程
- `train_single_iteration()`: 单次训练迭代
- `find_optimal_threshold()`: 寻找最优分类阈值(PLS)
- `save_training_results()`: 保存训练结果文件
- `train_with_ui_feedback()`: 带UI反馈的训练

**职责**: 实现500轮交叉验证训练，支持多种算法

---

### `model_predictor.py` - 样本预测管理
**功能**: 统一管理样本预测、模型信息显示和UI交互
**主要类**:
- `PredictionManager`: 预测管理器类

**核心方法**:
- `predict_sample()`: 预测单个样本
- `get_prediction_probability()`: 获取预测概率
- `format_prediction_result()`: 格式化预测结果
- `get_model_info()`: 获取模型详细信息
- `show_model_info_window()`: 显示模型信息窗口
- `batch_predict()`: 批量预测功能

**职责**: 处理预测相关的所有操作和UI显示

---

## 界面组件模块

### `ui_components.py` - UI组件库
**功能**: 模块化UI组件，实现界面组件的独立管理
**主要类**:
- `BasePanel`: 基础面板类，提供公共功能
- `ControlPanel`: 操作控制面板
- `ResultPanel`: 训练结果面板
- `PredictionPanel`: 样本预测面板
- `VisualizationPanel`: 可视化面板
- `InfoPanel`: 运行信息面板
- `PreprocessingPanel`: 数据预处理面板
- `ProgressComponent`: 进度组件

**核心方法**:
- `create_panel()`: 创建完整面板
- `create_frame()`: 创建基础框架
- `add_hover_tip()`: 添加悬停提示

**职责**: 提供可复用的UI组件，实现界面模块化

---

### `help_system.py` - 帮助系统
**功能**: 用户向导、进度跟踪和悬停提示管理
**主要类**:
- `HelpSystem`: 统一帮助系统类

**核心方法**:
- `show_wizard()`: 显示欢迎向导
- `create_progress_indicator()`: 创建步骤进度指示器
- `advance_step()`: 推进到指定步骤
- `add_hover_tip()`: 添加延迟悬停提示
- `update_progress_display()`: 更新进度显示

**职责**: 提供用户引导和操作提示，跟踪用户操作进度

---

## 可视化和输出模块

### `visualization.py` - 可视化生成器
**功能**: 生成机器学习评估图表和GUI显示集成
**主要函数**:
- `generate_performance_charts()`: 生成性能评估图表
- `create_visualization_tabs()`: 在GUI中创建图表选项卡
- `visualize_performance()`: 完整可视化流程

**生成图表类型**:
- 训练/测试准确率对比图
- 精确率/召回率/F1分数图
- 平均混淆矩阵图
- 平均ROC曲线图
- PLS阈值分布图

**职责**: 将训练结果转换为直观的图表展示

---

### `print_manager.py` - 打印管理器
**功能**: 诊断报告生成和打印功能
**主要类**:
- `PrintManager`: 打印管理器
- `PrintDialog`: 打印设置对话框

**核心功能**:
- 病人信息录入界面
- 打印内容选择(数据集信息、训练信息、预测结果、模型信息)
- 报告预览和导出
- 控制台打印和文件导出

**职责**: 提供医用级别的报告生成和打印功能

---

### `output_manager.py` - 输出文件管理
**功能**: 统一管理输出文件的分类保存和路径管理
**主要类**:
- `OutputManager`: 输出文件管理器

**核心方法**:
- `get_path()`: 获取分类文件路径
- `save_file()`: 按类型保存文件
- `create_directories()`: 创建输出目录结构
- `open_output_folder()`: 打开输出文件夹

**目录结构**:
```
outputs/
├── data/     # 数据文件
├── models/   # 模型文件  
├── results/  # 结果文件
└── charts/   # 图表文件
```

**职责**: 提供统一的文件组织和存储管理

---

## 工具和支撑模块

### `utils.py` - 工具函数库
**功能**: 提供通用工具函数和日志系统
**主要函数**:
- `log_message()`: 增强日志记录，支持不同级别
- `clear_log()`: 清空日志信息
- `set_global_widgets()`: 设置全局组件引用
- `set_window_icon()`: 设置窗口图标(带稳定性保证)
- `create_backup_filename()`: 创建备份文件名

**日志级别**: INFO, SUCCESS, WARNING, ERROR
**职责**: 提供基础工具函数和统一日志系统

---

### `validation_decorators.py` - 验证装饰器
**功能**: 统一的数据验证和错误处理装饰器系统
**主要装饰器**:
- `@handle_file_operations()`: 文件操作错误处理
- `@validate_training_data()`: 训练数据验证
- `@safe_model_operation()`: 模型操作安全执行
- `@require_data_store()`: 检查data_store必要数据
- `@log_execution_time`: 记录函数执行时间
- `@validate_file_path()`: 文件路径验证

**组合装饰器**:
- `@safe_data_processing()`: 安全数据处理组合

**职责**: 提供统一的错误处理和数据验证机制

---

## 依赖关系图

```
main.py (程序入口)
├── ui_components.py (界面组件)
├── help_system.py (帮助系统)
├── data_preprocessor.py (数据预处理)
├── model_training.py (模型训练)
├── model_predictor.py (样本预测)
├── print_manager.py (打印管理)
└── 支撑模块
    ├── config.py (配置管理)
    ├── data_store.py (数据存储)
    ├── feature_detector.py (特征检测)
    ├── visualization.py (可视化)
    ├── output_manager.py (文件管理)
    ├── utils.py (工具函数)
    └── validation_decorators.py (验证装饰器)
```

## 模块交互说明

### 数据流转
1. **用户操作** → UI组件回调 → MainGUIManager
2. **MainGUIManager** → 业务逻辑Manager → data_store
3. **data_store** → 文件保存 → output_manager

### 核心设计模式
- **中介者模式**: MainGUIManager协调各组件
- **观察者模式**: 回调机制处理用户交互
- **外观模式**: Manager类封装复杂业务逻辑
- **单例模式**: data_store全局数据存储
- **装饰器模式**: validation_decorators统一错误处理

### 架构特点
- **模块化**: 每个文件职责单一明确
- **松耦合**: 通过data_store和回调机制降低依赖
- **可扩展**: 组件化设计便于添加新功能
- **错误安全**: 装饰器提供统一异常处理

## 开发维护指南

### 添加新功能
1. **UI功能**: 在ui_components.py中创建新Panel类
2. **业务逻辑**: 创建新的Manager类处理复杂逻辑
3. **数据操作**: 在data_store.py中添加数据管理函数
4. **配置参数**: 在config.py中添加相关配置

### 错误处理
- 所有文件操作使用`@handle_file_operations`装饰器
- 模型操作使用`@safe_model_operation`装饰器
- 数据验证使用`@validate_training_data`装饰器

### 日志记录
- 使用`log_message(message, level)`记录所有重要操作
- 支持INFO、SUCCESS、WARNING、ERROR四个级别
- 自动显示在界面日志面板中

这种架构设计实现了功能模块化、错误处理统一化、数据管理集中化，便于维护和扩展。