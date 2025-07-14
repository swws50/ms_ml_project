# config.py - 配置文件和常量定义

from sklearn.model_selection import StratifiedKFold

# 默认的47个m/z特征值列表
DEFAULT_MZ_VALUES = [
    563.43, 887.77, 804.50, 811.54, 619.52, 647.56, 805.51, 591.47, 806.53, 579.38, 
    771.60, 797.60, 769.59, 655.39, 695.57, 731.54, 565.36, 929.75, 759.48, 697.59, 
    807.55, 671.56, 673.57, 879.76, 931.77, 953.77, 641.50, 881.77, 901.73, 927.68, 
    799.59, 763.52, 903.77, 883.70, 979.80, 955.71, 675.59, 669.52, 905.77, 643.53, 
    825.70, 639.41, 971.65, 981.84, 869.71, 925.73, 907.77, 507.27
]

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
