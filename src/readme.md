# 诊断分析工具 / Diagnostic Analysis Tool

*[English version below / 英文版本在下方]*

## 中文说明

### 📋 项目简介

这是一个用于质谱数据分析和疾病诊断的机器学习工具。该工具可以处理原始质谱数据，训练多种机器学习模型，并对未知样本进行分类预测（HC vs LC）。

### 🎯 主要功能

- **数据预处理**: 自动提取47个m/z值的峰值强度
- **模型训练**: 支持多种机器学习算法（随机森林、逻辑回归、神经网络、PLS回归等）
- **性能评估**: 生成准确率、混淆矩阵、ROC曲线等评估图表
- **样本预测**: 对新样本进行HC/LC分类预测
- **可视化界面**: 友好的图形用户界面，支持进度跟踪和帮助系统

### 📁 文件结构

```
project_folder/
├── main.py                    # 主程序入口和GUI界面
├── config.py                  # 配置文件和常量定义
├── utils.py                   # 工具函数和日志系统
├── data_processing.py         # 数据处理模块
├── model_training.py          # 模型训练和预测模块
├── visualization.py           # 可视化和图表生成
├── help_system.py            # 帮助系统和进度跟踪
├── requirements.txt          # 依赖包列表
└── README.md                 # 说明文档
```

### 🛠️ 安装要求

**Python版本**: 3.8或更高版本

**依赖包**:
```bash
pip install -r requirements.txt
```

主要依赖包括:
- numpy >= 1.21.0
- pandas >= 1.3.0
- scikit-learn >= 1.0.0
- matplotlib >= 3.5.0
- tkinter (通常随Python安装)

### 🚀 使用方法

#### 1. 启动程序
```bash
python main.py
```

#### 2. 使用流程

**步骤1: 数据预处理**
- 点击菜单 "数据预处理" → "选择处理文件"
- 选择原始的txt格式质谱数据文件
- 等待处理完成，生成 `LC_MAX.xlsx` 文件

**步骤2: 加载数据**
- 点击 "选择归一化excel文件" 按钮
- 选择步骤1生成的 `LC_MAX.xlsx` 文件

**步骤3: 选择模型**
- 从菜单 "模型选择" 中选择机器学习算法
- 推荐选项:
  - `LogisticRegressionCV`: 适合小数据集
  - `RandomForestClassifier`: 适合大数据集
  - `PLSRegression`: 适合高维数据

**步骤4: 训练模型**
- 点击 "开始分析" 按钮
- 等待训练完成（约1-3分钟，进行500轮交叉验证）

**步骤5: 查看结果**
- 查看生成的评估图表（准确率、混淆矩阵、ROC曲线等）
- 检查模型性能指标

**步骤6: 预测新样本**
- 点击 "选择要检测的txt文件" 按钮
- 选择要预测的未知样本文件
- 查看预测结果（HC或LC）和置信度

### 📊 输出文件

程序运行后会生成以下文件:
- `LC_MAX.xlsx`: 处理后的特征矩阵
- `best_model.joblib`: 最佳模型文件
- `*.png`: 各种评估图表
- `*.csv` / `*.npy`: 训练结果数据

### 💡 提示和技巧

1. **数据格式**: 确保输入的txt文件为两列格式（m/z值和强度）
2. **样本命名**: 文件名前两个字符应为类别标签（HC或LC）
3. **内存使用**: 大数据集可能需要较多内存，建议关闭其他程序
4. **帮助系统**: 首次使用时会显示使用向导，也可通过菜单访问

### 🐛 常见问题

**问题**: 无法保存文件
**解决**: 检查文件是否被其他程序打开，或选择其他保存位置

**问题**: 训练过程中出错
**解决**: 检查数据格式是否正确，确保有足够的不同类别样本

**问题**: 预测结果异常
**解决**: 确保模型已正确训练，输入样本格式与训练数据一致

---

## English Version

### 📋 Project Overview

This is a machine learning tool for mass spectrometry data analysis and disease diagnosis. The tool can process raw mass spectrometry data, train various machine learning models, and perform classification predictions on unknown samples (HC vs LC).

### 🎯 Key Features

- **Data Preprocessing**: Automatically extract peak intensities for 47 m/z values
- **Model Training**: Support multiple machine learning algorithms (Random Forest, Logistic Regression, Neural Networks, PLS Regression, etc.)
- **Performance Evaluation**: Generate evaluation charts including accuracy, confusion matrix, ROC curves
- **Sample Prediction**: Classify new samples as HC/LC
- **Visualization Interface**: User-friendly GUI with progress tracking and help system

### 📁 File Structure

```
project_folder/
├── main.py                    # Main entry point and GUI interface
├── config.py                  # Configuration and constants
├── utils.py                   # Utility functions and logging
├── data_processing.py         # Data processing module
├── model_training.py          # Model training and prediction
├── visualization.py           # Visualization and chart generation
├── help_system.py            # Help system and progress tracking
├── requirements.txt          # Dependencies list
└── README.md                 # Documentation
```

### 🛠️ Installation Requirements

**Python Version**: 3.8 or higher

**Dependencies**:
```bash
pip install -r requirements.txt
```

Key dependencies include:
- numpy >= 1.21.0
- pandas >= 1.3.0
- scikit-learn >= 1.0.0
- matplotlib >= 3.5.0
- tkinter (usually included with Python)

### 🚀 Usage Instructions

#### 1. Launch the Program
```bash
python main.py
```

#### 2. Workflow

**Step 1: Data Preprocessing**
- Click menu "数据预处理" → "选择处理文件"
- Select raw txt format mass spectrometry data files
- Wait for processing to complete, generates `LC_MAX.xlsx` file

**Step 2: Load Data**
- Click "选择归一化excel文件" button
- Select the `LC_MAX.xlsx` file generated in Step 1

**Step 3: Select Model**
- Choose a machine learning algorithm from "模型选择" menu
- Recommended options:
  - `LogisticRegressionCV`: Good for small datasets
  - `RandomForestClassifier`: Good for large datasets
  - `PLSRegression`: Good for high-dimensional data

**Step 4: Train Model**
- Click "开始分析" button
- Wait for training completion (about 1-3 minutes, 500 cross-validation rounds)

**Step 5: View Results**
- Examine generated evaluation charts (accuracy, confusion matrix, ROC curves, etc.)
- Check model performance metrics

**Step 6: Predict New Samples**
- Click "选择要检测的txt文件" button
- Select unknown sample files for prediction
- View prediction results (HC or LC) and confidence scores

### 📊 Output Files

The program generates the following files:
- `LC_MAX.xlsx`: Processed feature matrix
- `best_model.joblib`: Best model file
- `*.png`: Various evaluation charts
- `*.csv` / `*.npy`: Training result data

### 💡 Tips and Tricks

1. **Data Format**: Ensure input txt files are in two-column format (m/z values and intensities)
2. **Sample Naming**: First two characters of filename should be class labels (HC or LC)
3. **Memory Usage**: Large datasets may require more memory, consider closing other programs
4. **Help System**: Usage wizard displays on first run, also accessible through menu

### 🐛 Troubleshooting

**Issue**: Cannot save files
**Solution**: Check if files are open in other programs, or choose a different save location

**Issue**: Error during training
**Solution**: Verify data format is correct, ensure sufficient samples of different classes

**Issue**: Abnormal prediction results
**Solution**: Ensure model is properly trained, input sample format matches training data

### 📄 License

This project is for research and educational purposes. Please cite appropriately if used in academic work.

### 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

### 📞 Support

For questions and support, please refer to the in-built help system or contact the development team.
