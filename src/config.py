# config.py - 简化后的配置文件和常量定义
# v1.9.8.3 - 清理未使用的变量和函数

# 标准库导入
import os

# 第三方库导入
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold

# 本地模块导入
from output_manager import output_manager
from utils import log_message, get_resource_path


# 应用程序图标路径
ICON_CONFIG = {
    'app_icon_ico': get_resource_path('assets/app_icon.ico'),
    'app_icon_png': get_resource_path('assets/app_icon.png'),
}

# 特征选择参数
MAX_FEATURES = 50                # 最大特征数量
MIN_OCCURRENCE_RATE = 0.5        # 最小出现频率（50%的文件中出现）
MIN_FOLD_CHANGE = 1.3            # 最小倍数变化（30%强度差异）

# 模型配置
MODEL_CONFIGS = {
    "RandomForestClassifier": {"n_estimators": 250},
    "LinearSVC": {"max_iter": 5000},
    "LinearDiscriminantAnalysis": {"solver": 'lsqr', "shrinkage": 'auto'},
    "LogisticRegressionCV": {
        "Cs": 20,
        "penalty": 'l2',
        "cv": 5,
        "cv_shuffle": True,
        "max_iter": 10000,
        "solver": 'liblinear',
        "scoring": 'balanced_accuracy',
        "n_jobs": -1
    },
    "MLPClassifier": {
        "hidden_layer_sizes": (100,),
        "activation": 'logistic',
        "max_iter": 2500
    },
    "PLSRegression": {
        "n_components": 4,
        "scale": False,
        "max_iter": 300,
        "tol": 1e-06
    },
}

# 默认模型选择
DEFAULT_MODEL = "PLSRegression"

# 交叉验证配置
CV_SPLITS = 5           # 5折交叉验证
CV_REPEATS = 20         # 重复20次
CV_RANDOM_STATE = 42    # 随机种子

# 创建交叉验证对象（总共100次训练：5×20=100）
CROSS_VALIDATOR = RepeatedStratifiedKFold(
    n_splits=CV_SPLITS,
    n_repeats=CV_REPEATS,
    random_state=CV_RANDOM_STATE
)

# 其他配置
TEST_SIZE = 0.2
MZ_TOLERANCE = 0.2


def get_output_paths():
    """动态生成输出文件路径"""
    csv_filename = 'data.csv'
    
    return {
        # 数据文件
        'processed_data': output_manager.get_path('data', csv_filename),
        'diagnostics_report': output_manager.get_path('data', 'diagnostics_report.txt'),
        
        # 图表文件
        'chart_accuracy': output_manager.get_path('chart', 'ClassPerformance.png'),
        'chart_metrics': output_manager.get_path('chart', 'BalanceMetrics.png'),
        'chart_confusion': output_manager.get_path('chart', 'ConfusionMatrix.png'),
        'chart_roc': output_manager.get_path('chart', 'ROC_Curve.png'),
        'chart_thresholds': output_manager.get_path('chart', 'PLS_Thresholds.png'),
        'chart_metrics_table': output_manager.get_path('chart', 'MetricsTable.csv'),

        # 预测结果目录
        'predictions_dir': output_manager.get_path('prediction', ''),    
    }


OUTPUT_FILES = get_output_paths()