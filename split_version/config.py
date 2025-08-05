# config.py - 简化后的配置文件和常量定义

from sklearn.model_selection import StratifiedKFold

# ========== 智能峰发现参数 ==========
# 特征选择参数
MAX_FEATURES = 50                # 最大特征数量
MIN_OCCURRENCE_RATE = 0.2        # 最小出现频率（20%的文件中出现）
MIN_FOLD_CHANGE = 1.3            # 最小倍数变化（30%强度差异）

# pyOpenMS峰拾取参数
SIGNAL_TO_NOISE = 1.0            # 信噪比阈值
SPACING_DIFFERENCE = 1.5         # 峰间距要求

# 备用策略参数（当严格条件找不到特征时）
ENABLE_FALLBACK = True           # 是否启用备用策略
FALLBACK_OCCURRENCE_RATE = 0.1   # 备用模式的出现频率
FALLBACK_FOLD_CHANGE = 1.2       # 备用模式的倍数变化

# ========== 模型配置 ==========
# 支持的模型类型及其参数配置
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

# ========== 训练配置 ==========
TRAINING_ITERATIONS = 500
TEST_SIZE = 0.2
MZ_TOLERANCE = 0.2
NORMALIZATION_FACTOR = 871.7725  # 默认归一化因子（作为后备值）

# ========== 文件名配置 ==========
OUTPUT_FILES = {
    'processed_data': 'normalized_ms_data.csv',
    'confusion_matrix': 'Con_matrix_SVM.csv',
    'fscore': 'Fscore_SVM.csv',
    'auc': '2C_auc_SVM.csv',
    'fpr_values': 'fpr_values.npy',
    'tpr_values': 'tpr_values.npy',
    'thresholds_values': 'thresholds_values.npy',
    'pls_thresholds': 'PLS_optimal_thresholds.csv',
    'best_model': 'best_model.joblib'
}

# ========== 动态类别映射管理 ==========
def get_class_mapping():
    """
    获取当前的类别映射
    
    优先级：
    1. data_store中的用户自定义类别
    2. 默认类别映射
    
    返回:
        tuple: (正向映射dict, 反向映射dict)
    """
    try:
        import data_store
        classification = data_store.get_file_classification()
        
        # 检查是否有有效的用户分类
        if (classification['class_0_files'] or classification['class_1_files'] or 
            classification['class_0_name'] != '0类' or classification['class_1_name'] != '1类'):
            
            # 使用用户自定义的类别名称
            forward_mapping = {
                classification['class_0_name']: 0,
                classification['class_1_name']: 1
            }
            reverse_mapping = {
                0: classification['class_0_name'],
                1: classification['class_1_name']
            }
            return forward_mapping, reverse_mapping
    except (ImportError, AttributeError):
        pass
    
    # 回退到默认映射
    default_forward = {"类别0": 0, "类别1": 1}
    default_reverse = {0: "类别0", 1: "类别1"}
    return default_forward, default_reverse

def get_current_class_names():
    """
    获取当前的类别名称
    
    返回:
        tuple: (class_0_name, class_1_name)
    """
    _, reverse_mapping = get_class_mapping()
    return reverse_mapping[0], reverse_mapping[1]

def get_class_mapping_for_labels(labels):
    """
    根据给定的标签数据自动创建类别映射
    
    参数:
        labels: pandas.Series 或 list，包含类别标签
        
    返回:
        dict: 标签到数字的映射
    """
    import pandas as pd
    if isinstance(labels, pd.Series):
        unique_labels = labels.unique()
    else:
        unique_labels = list(set(labels))
    
    if len(unique_labels) >= 2:
        return {unique_labels[0]: 0, unique_labels[1]: 1}
    else:
        # 如果只有一个类别，返回默认映射
        forward_mapping, _ = get_class_mapping()
        return forward_mapping

# ========== 便捷函数 ==========
def update_class_names(class_0_name, class_1_name):
    """
    更新类别名称到data_store
    
    参数:
        class_0_name: 类别0的名称
        class_1_name: 类别1的名称
    """
    try:
        import data_store
        classification = data_store.get_file_classification()
        classification['class_0_name'] = class_0_name
        classification['class_1_name'] = class_1_name
        data_store.set_file_classification(classification)
        
        from utils import log_message
        log_message(f"类别名称已更新: {class_0_name}, {class_1_name}", "INFO")
    except Exception as e:
        from utils import log_message
        log_message(f"更新类别名称失败: {str(e)}", "WARNING")

def get_normalization_factor():
    """
    获取归一化因子
    
    优先级：
    1. 智能方法保存的归一化因子文件
    2. 默认归一化因子
    
    返回:
        float: 归一化因子
    """
    import os
    
    # 尝试读取智能方法的归一化因子
    normalization_file = 'intelligent_normalization_factor.txt'
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
        with open('intelligent_normalization_factor.txt', 'w') as f:
            f.write(str(factor))
        
        from utils import log_message
        log_message(f"归一化因子已保存: {factor:.2f}", "SUCCESS")
    except Exception as e:
        from utils import log_message
        log_message(f"保存归一化因子失败: {str(e)}", "WARNING")