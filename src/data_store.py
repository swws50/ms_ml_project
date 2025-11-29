# data_store.py - 数据存储模块（含类别映射管理）
import numpy as np
import os

"""
数据仓库模块 - 所有模块共享的数据存储中心
包含：文件分类、训练数据、模型、类别映射
"""

# ==================== 类别映射管理器 ====================

class ClassMappingManager:
    """
    类别映射管理器 - 直接操作 _file_classification
    
    使用方式：
        from data_store import class_manager
        
        # 设置
        class_manager.set_names('HCC', 'Normal')
        
        # 读取
        class_manager.class_0_name          # 'HCC'
        class_manager.names                 # ('HCC', 'Normal')
        class_manager.forward_mapping       # {'HCC': 0, 'Normal': 1}
        class_manager.reverse_mapping       # {0: 'HCC', 1: 'Normal'}
        
        # 编码/解码
        class_manager.encode('HCC')         # 0
        class_manager.decode(0)             # 'HCC'
    """
    
    # ========== 属性（直接读取 _file_classification） ==========
    
    @property
    def class_0_name(self) -> str:
        return _file_classification['class_0_name']
    
    @property
    def class_1_name(self) -> str:
        return _file_classification['class_1_name']
    
    @property
    def names(self) -> tuple:
        """返回 (class_0, class_1)"""
        return (_file_classification['class_0_name'], 
                _file_classification['class_1_name'])
    
    @property
    def forward_mapping(self) -> dict:
        """名称 → 数字"""
        return {
            _file_classification['class_0_name']: 0, 
            _file_classification['class_1_name']: 1
        }
    
    @property
    def reverse_mapping(self) -> dict:
        """数字 → 名称"""
        return {
            0: _file_classification['class_0_name'], 
            1: _file_classification['class_1_name']
        }
    
    # ========== 设置方法 ==========
    
    def set_names(self, class_0: str, class_1: str):
        """设置类别名称"""
        _file_classification['class_0_name'] = class_0
        _file_classification['class_1_name'] = class_1
    
    def reset(self):
        """重置为默认值"""
        _file_classification['class_0_name'] = "类别0"
        _file_classification['class_1_name'] = "类别1"
    
    # ========== 编码/解码 ==========
    
    def encode(self, name: str) -> int:
        """名称 → 数字"""
        mapping = self.forward_mapping
        if name not in mapping:
            raise ValueError(f"未知类别: '{name}'，有效类别: {list(mapping.keys())}")
        return mapping[name]
    
    def decode(self, label: int) -> str:
        """数字 → 名称"""
        mapping = self.reverse_mapping
        if label not in mapping:
            raise ValueError(f"无效标签: {label}")
        return mapping[label]
    
    def safe_encode(self, name: str, default: int = -1) -> int:
        """安全编码，失败返回默认值"""
        try:
            return self.encode(name)
        except ValueError:
            return default


# 全局单例
class_manager = ClassMappingManager()


# ==================== 原有数据存储 ====================

# 全局数据变量 
_file_classification = {
    'class_0_name': '类别0',
    'class_1_name': '类别1', 
    'class_0_files': [],
    'class_1_files': []
}

_training_data = {
    'row': None,
    'column': None,
    'df': None
}

_training_data_path = None
_latest_trained_model = None
_latest_model_path = None
_latest_prediction = None


# ==================== 文件分类相关函数 ====================

def set_file_classification(classification_data):
    """设置文件分类信息"""
    global _file_classification
    _file_classification.update(classification_data)

def get_file_classification():
    """获取文件分类信息"""
    return _file_classification.copy()

def get_class_names():
    """获取类别名称 - 返回 (class_0_name, class_1_name)"""
    return _file_classification['class_0_name'], _file_classification['class_1_name']

def get_class_files(class_index):
    """获取指定类别的文件列表"""
    if class_index == 0:
        return _file_classification['class_0_files'].copy()
    elif class_index == 1:
        return _file_classification['class_1_files'].copy()
    return []

def get_all_files():
    """获取所有分类文件"""
    return (_file_classification['class_0_files'] + 
            _file_classification['class_1_files'])

def has_file_classification():
    """检查是否有有效的文件分类"""
    return (len(_file_classification['class_0_files']) > 0 or 
            len(_file_classification['class_1_files']) > 0)


# ==================== 训练数据相关函数 ====================

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
    """获取训练数据的基本信息"""
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


# ==================== 模型相关函数 ====================

def set_latest_trained_model(model, model_path):
    """设置最新训练的模型"""
    global _latest_trained_model, _latest_model_path
    _latest_trained_model = model
    _latest_model_path = model_path

def get_latest_trained_model():
    """获取最新训练的模型"""
    return _latest_trained_model, _latest_model_path

def get_latest_model_info():
    """获取最新模型信息"""
    latest_model, latest_path = get_latest_trained_model()
    
    if latest_model is None and latest_path is None:
        return {'has_model': False}
    
    return {
        'has_model': True,
        'model_type': type(latest_model).__name__ if latest_model else 'Unknown',
        'model_file': os.path.basename(latest_path) if latest_path else None,
        'model_path': latest_path,
        'is_in_memory': latest_model is not None
    }


# ==================== 预测结果相关函数 ====================

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


# ==================== 数据清理函数 ====================

def clear_file_classification():
    """清空文件分类数据（含类别名称重置）"""
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
    global _latest_trained_model, _latest_model_path
    _latest_trained_model = None
    _latest_model_path = None

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


# ==================== 状态检查函数 ====================

def get_system_status():
    """获取系统整体状态"""
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
        'model': get_latest_model_info()
    }

def is_ready_for_training():
    """检查是否准备好进行模型训练"""
    missing = []
    if not has_training_data():
        missing.append("训练数据")
    return (len(missing) == 0, missing)


