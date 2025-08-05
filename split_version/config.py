# config.py - 配置文件和常量定义

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

# 类别映射
CLASS_MAPPING = {"HC": 0, "LC": 1}
REVERSE_CLASS_MAPPING = {0: "HC", 1: "LC"}

# 训练配置
TRAINING_ITERATIONS = 500
TEST_SIZE = 0.2
NORMALIZATION_FACTOR = 871.7725
MZ_TOLERANCE = 0.2

# 文件名配置
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
