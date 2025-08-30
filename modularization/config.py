# config.py - 简化后的配置文件和常量定义

# 标准库导入 
import os

# 第三方库导入 
import pandas as pd
from sklearn.model_selection import StratifiedKFold

# 本地模块导入 
import data_store
from output_manager import output_manager
from utils import log_message

# 应用程序图标路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_CONFIG = {
    'app_icon_ico': os.path.join(BASE_DIR, 'assets', 'app_icon.ico'),
    'app_icon_png': os.path.join(BASE_DIR, 'assets', 'app_icon.png'),
}


# 智能峰发现参数 
# 特征选择参数
MAX_FEATURES = 50                # 最大特征数量
MIN_OCCURRENCE_RATE = 0.2        # 最小出现频率（20%的文件中出现）
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
    "PLSRegression": {"n_components": 10},
}

# 默认模型选择
DEFAULT_MODEL = "PLSRegression"

# 训练配置 
TRAINING_ITERATIONS = 500
TEST_SIZE = 0.2
MZ_TOLERANCE = 0.2
NORMALIZATION_FACTOR = 871.7725  # 默认归一化因子（作为后备值）

# 文件路径配置（使用输出管理器）
def get_output_paths():
    """动态生成输出文件路径"""
    return {
        # 数据文件
        'processed_data': output_manager.get_path('data', 'normalized_ms_data.csv'),
        'normalization_factor': output_manager.get_path('data', 'intelligent_normalization_factor.txt'),
        
        # 模型文件
        'best_model': output_manager.get_path('model', 'best_model.joblib'),
        
        # 结果文件
        'confusion_matrix': output_manager.get_path('result', 'Con_matrix_SVM.csv'),
        'fscore': output_manager.get_path('result', 'Fscore_SVM.csv'),
        'auc': output_manager.get_path('result', '2C_auc_SVM.csv'),
        'fpr_values': output_manager.get_path('result', 'fpr_values.npy'),
        'tpr_values': output_manager.get_path('result', 'tpr_values.npy'),
        'thresholds_values': output_manager.get_path('result', 'thresholds_values.npy'),
        'pls_thresholds': output_manager.get_path('result', 'PLS_optimal_thresholds.csv'),
        
        # 图表文件
        'chart_accuracy': output_manager.get_path('chart', 'Training and Test Balanced Accuracy.png'),
        'chart_metrics': output_manager.get_path('chart', 'Weighted Average Precision, Recall, and F1-score.png'),
        'chart_confusion': output_manager.get_path('chart', 'Mean Confusion Matrix.png'),
        'chart_roc': output_manager.get_path('chart', 'Mean ROC Curve.png'),
        'chart_thresholds': output_manager.get_path('chart', 'PLS_optimal_thresholds.png')
    }

OUTPUT_FILES = get_output_paths()

# 便捷保存函数 
def save_data_file(data, filename, method='pandas'):
    """保存数据文件"""
    return output_manager.save_file(data, 'data', filename, method)

def save_model_file(model, filename):
    """保存模型文件"""
    return output_manager.save_file(model, 'model', filename, 'joblib')

def save_result_file(data, filename, method='numpy'):
    """保存结果文件"""
    return output_manager.save_file(data, 'result', filename, method)

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


def get_normalization_factor():
    """
    获取归一化因子
    
    优先级：
    1. 智能方法保存的归一化因子文件
    2. 默认归一化因子
    
    返回:
        float: 归一化因子
    """
    
    # 尝试读取智能方法的归一化因子
    normalization_file = OUTPUT_FILES['normalization_factor']
    if os.path.exists(normalization_file):
        try:
            with open(normalization_file, 'r') as f:
                factor = float(f.read().strip())
            return factor
        except Exception:
            pass
    
    # 返回默认值
    return NORMALIZATION_FACTOR

def save_normalization_factor(factor):
    """
    保存归一化因子到文件
    
    参数:
        factor: 要保存的归一化因子
    """
    try:
        # 修复：使用输出管理器的正确路径
        normalization_file = OUTPUT_FILES['normalization_factor']
        
        # 确保目录存在
        os.makedirs(os.path.dirname(normalization_file), exist_ok=True)
        
        with open(normalization_file, 'w') as f:
            f.write(str(factor))
        
        log_message(f"归一化因子已保存到: {normalization_file}, 值: {factor:.2f}", "SUCCESS")
    except Exception as e:
        log_message(f"保存归一化因子失败: {str(e)}", "WARNING")