# config.py - 简化后的配置文件和常量定义

# 标准库导入
import os

# 第三方库导入
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import RepeatedStratifiedKFold
# 本地模块导入
import data_store
from output_manager import output_manager
from utils import log_message, get_resource_path
from pathlib import Path

# 应用程序图标路径
BASE_DIR = Path(__file__).parent.parent
ASSETS_DIR = BASE_DIR / 'assets'
ICON_CONFIG = {
    'app_icon_ico': get_resource_path('assets/app_icon.ico'),  # ✅ 正确
    'app_icon_png': get_resource_path('assets/app_icon.png'),  # ✅ 正确
}


# 智能峰发现参数
# 特征选择参数
MAX_FEATURES = 50                # 最大特征数量
MIN_OCCURRENCE_RATE = 0.5        # 最小出现频率（50%的文件中出现）
MIN_FOLD_CHANGE = 1.3            # 最小倍数变化（30%强度差异）

# pyOpenMS峰拾取参数
SIGNAL_TO_NOISE = 1.0            # 信噪比阈值
SPACING_DIFFERENCE = 1.5         # 峰间距要求


# 模型配置
MODEL_CONFIGS = {
    "RandomForestClassifier": {"n_estimators": 500},
    "LinearSVC": {"max_iter": 10000},
    "LinearDiscriminantAnalysis": {"solver": 'eigen', "shrinkage": 'auto'},
    "LogisticRegressionCV": {
        "Cs": 20,
        "penalty": 'l1',
        "cv": StratifiedKFold(5, shuffle=True),
        "max_iter": 10000,
        "solver": 'liblinear',
        "scoring": 'balanced_accuracy',
        "n_jobs": -1
    },
    "MLPClassifier": {
        "hidden_layer_sizes": (100, 200, 100),
        "activation": 'logistic',
        "max_iter": 2000
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

# 训练配置 - 使用嵌套交叉验证
# 交叉验证配置
CV_SPLITS = 5           # 5折交叉验证
CV_REPEATS = 20         # 重复20次
CV_RANDOM_STATE = 42    # 随机种子

# 创建交叉验证对象（总共50次训练：5×10=50）
CROSS_VALIDATOR = RepeatedStratifiedKFold(
    n_splits=CV_SPLITS,
    n_repeats=CV_REPEATS,
    random_state=CV_RANDOM_STATE
)

# 保留这个（仍需用于其他地方）
TEST_SIZE = 0.2
MZ_TOLERANCE = 0.2

# 文件路径配置（使用输出管理器）


def get_output_paths():
    """动态生成输出文件路径"""

    # 基础文件名，归一化后缀由data_preprocessor处理
    csv_filename = 'data.csv'
    
    return {
        # 数据文件
        'processed_data': output_manager.get_path('data', csv_filename),
        
        # 模型文件
        # 于model_training.py中动态生成
        # 'trained_model': output_manager.get_path('model', 'trained_model.joblib'),

        # 结果文件
        'confusion_matrix': output_manager.get_path('metrics', 'Con_matrix_SVM.csv'),
        'fscore': output_manager.get_path('metrics', 'Fscore_SVM.csv'),
        'auc': output_manager.get_path('metrics', '2C_auc_SVM.csv'),
        'fpr_values': output_manager.get_path('metrics', 'fpr_values.npy'),
        'tpr_values': output_manager.get_path('metrics', 'tpr_values.npy'),
        'thresholds_values': output_manager.get_path('metrics', 'thresholds_values.npy'),
        'pls_thresholds': output_manager.get_path('metrics', 'PLS_optimal_thresholds.csv'),

        # 图表文件 - 使用描述性基础名称（时间戳在保存时添加）
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

# 便捷保存函数


def save_data_file(data, filename, method='pandas'):
    """保存数据文件"""
    return output_manager.save_file(data, 'data', filename, method)


def save_model_file(model, filename):
    """保存模型文件"""
    return output_manager.save_file(model, 'model', filename, 'joblib')


def save_metric_file(data, filename, method='numpy'):
    """保存训练指标文件（改名）"""
    return output_manager.save_file(data, 'metric', filename, method)  


def save_chart_file(figure, filename):
    """保存图表文件"""
    return output_manager.save_file(figure, 'chart', filename, 'matplotlib')

# 动态类别映射管理


def get_class_mapping(labels=None):
    """
    获取当前的类别映射 - 优先使用datastore中的类别

    返回:
        tuple: (正向映射dict, 反向映射dict)
    """
    try:
        classification = data_store.get_file_classification()

        # 直接使用datastore中的类别名称
        forward_mapping = {
            classification['class_0_name']: 0,
            classification['class_1_name']: 1
        }
        reverse_mapping = {
            0: classification['class_0_name'],
            1: classification['class_1_name']
        }
        return forward_mapping, reverse_mapping

    except Exception as e:
        # 回退到默认映射
        log_message(f"获取类别映射失败，使用默认值: {e}")
        default_forward = {"类别0": 0, "类别1": 1}
        default_reverse = {0: "类别0", 1: "类别1"}
        return default_forward, default_reverse