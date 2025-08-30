# data_store.py - 简化后的数据存储模块
import numpy as np
"""
这个文件用来存储程序中需要共享的数据
相当于一个"数据仓库"，所有模块都可以访问
"""

# 全局数据变量 
_file_classification = {
    'class_0_name': '类别0',  # 统一默认名称
    'class_1_name': '类别1', 
    'class_0_files': [],  # 存储完整文件路径
    'class_1_files': []
}

_training_data = {
    'row': None,      # 特征数据
    'column': None,   # 标签数据  
    'df': None        # 原始DataFrame
}

_training_data_path = None

_best_model = None    # 最佳模型

_latest_prediction = None

# 文件分类相关函数 
def set_file_classification(classification_data):
    """
    设置文件分类信息
    
    参数:
        classification_data: 包含分类信息的字典
    """
    global _file_classification
    _file_classification.update(classification_data)

def get_file_classification():
    """获取文件分类信息"""
    return _file_classification.copy()  # 返回副本，避免外部修改

def get_class_names():
    """
    获取类别名称
    
    返回:
        tuple: (class_0_name, class_1_name)
    """
    return _file_classification['class_0_name'], _file_classification['class_1_name']

def get_class_files(class_index):
    """
    获取指定类别的文件列表
    
    参数:
        class_index: 0 或 1
        
    返回:
        list: 文件路径列表
    """
    if class_index == 0:
        return _file_classification['class_0_files'].copy()
    elif class_index == 1:
        return _file_classification['class_1_files'].copy()
    else:
        return []

def get_all_files():
    """
    获取所有分类文件
    
    返回:
        list: 所有文件路径的列表
    """
    return (_file_classification['class_0_files'] + 
            _file_classification['class_1_files'])

def has_file_classification():
    """
    检查是否有有效的文件分类
    
    返回:
        bool: 是否有分类文件
    """
    return (len(_file_classification['class_0_files']) > 0 or 
            len(_file_classification['class_1_files']) > 0)

# 训练数据相关函数 
def set_training_data(row, column, df):
    """设置训练数据"""
    global _training_data
    _training_data['row'] = row
    _training_data['column'] = column
    _training_data['df'] = df

def get_training_data():
    """获取训练数据"""
    return (_training_data['row'], 
            _training_data['column'], 
            _training_data['df'])

def has_training_data():
    """检查是否有训练数据"""
    return (_training_data['row'] is not None and 
            _training_data['column'] is not None)

def get_training_data_info():
    """
    获取训练数据的基本信息
    
    返回:
        dict: 包含数据形状、样本数等信息的字典
    """
    if not has_training_data():
        return {'has_data': False}
    
    row, column, df = get_training_data()
    
    unique_classes = np.unique(column) if column is not None else []
    
    return {
        'has_data': True,
        'n_samples': row.shape[0] if hasattr(row, 'shape') else len(row),
        'n_features': row.shape[1] if hasattr(row, 'shape') else 0,
        'classes': unique_classes.tolist() if len(unique_classes) > 0 else [],
        'class_distribution': dict(zip(*np.unique(column, return_counts=True))) if column is not None else {}
    }

def set_training_data_path(file_path):
    """保存训练数据文件路径"""
    global _training_data_path
    _training_data_path = file_path

def get_training_data_path():
    """获取训练数据文件路径"""
    return _training_data_path

# 模型相关函数 
def set_best_model(model):
    """设置最佳模型"""
    global _best_model
    _best_model = model

def get_best_model():
    """获取最佳模型"""
    return _best_model

def has_best_model():
    """检查是否有已训练的模型"""
    return _best_model is not None

def get_model_info():
    """
    获取模型基本信息
    
    返回:
        dict: 模型信息字典
    """
    if not has_best_model():
        return {'has_model': False}
    
    model = get_best_model()
    return {
        'has_model': True,
        'model_type': type(model).__name__,
        'model_params': model.get_params() if hasattr(model, 'get_params') else {}
    }

def set_latest_prediction(prediction_result):
    """保存最新预测结果"""
    global _latest_prediction
    _latest_prediction = prediction_result.copy() if prediction_result else None

def get_latest_prediction():
    """获取最新预测结果"""
    return _latest_prediction.copy() if _latest_prediction else None

def has_latest_prediction():
    """检查是否有预测结果"""
    return _latest_prediction is not None

# 数据清理函数 
def clear_file_classification():
    """清空文件分类数据"""
    global _file_classification
    _file_classification = {
        'class_0_name': '类别0',
        'class_1_name': '类别1', 
        'class_0_files': [],
        'class_1_files': []
    }

def clear_training_data():
    """清空训练数据"""
    global _training_data
    _training_data = {
        'row': None,
        'column': None,
        'df': None
    }

def clear_model():
    """清空模型数据"""
    global _best_model
    _best_model = None


def clear_prediction_results():
    """清空预测结果"""
    global _latest_prediction
    _latest_prediction = None

def clear_all_data():
    """清空所有数据"""
    clear_file_classification()
    clear_training_data()
    clear_model()
    clear_prediction_results()
    
# 状态检查函数 
def get_system_status():
    """
    获取系统整体状态
    
    返回:
        dict: 系统状态信息
    """
    return {
        'file_classification': {
            'has_data': has_file_classification(),
            'class_names': get_class_names(),
            'file_counts': {
                'class_0': len(_file_classification['class_0_files']),
                'class_1': len(_file_classification['class_1_files']),
                'total': len(get_all_files())
            }
        },
        'training_data': get_training_data_info(),
        'model': get_model_info()
    }

def is_ready_for_training():
    """
    检查是否准备好进行模型训练
    
    返回:
        tuple: (是否准备好, 缺少的条件列表)
    """
    missing = []
    
    if not has_training_data():
        missing.append("训练数据")
    
    if len(missing) == 0:
        return True, []
    else:
        return False, missing

def is_ready_for_prediction():
    """
    检查是否准备好进行样本预测
    
    返回:
        tuple: (是否准备好, 缺少的条件列表)
    """
    missing = []
    
    if not has_best_model():
        missing.append("训练好的模型")
    
    if len(missing) == 0:
        return True, []
    else:
        return False, missing