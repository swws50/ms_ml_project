# data_store.py - 简单的数据存储模块

"""
这个文件用来存储程序中需要共享的数据
相当于一个"数据仓库"，所有模块都可以访问
"""

# 全局数据变量
file_classification = {
    'class_0_name': '0类',
    'class_1_name': '1类', 
    'class_0_files': [],  # 存储完整文件路径
    'class_1_files': []
}
row = None           # 特征数据
column = None        # 标签数据  
df = None           # 原始DataFrame
best_model = None   # 最佳模型

def set_file_classification(classification_data):
    """设置文件分类信息"""
    global file_classification
    file_classification = classification_data

def get_file_classification():
    """获取文件分类信息"""
    return file_classification

def set_training_data(new_row, new_column, new_df):
    """设置训练数据"""
    global row, column, df
    row = new_row
    column = new_column
    df = new_df

def get_training_data():
    """获取训练数据"""
    return row, column, df

def has_training_data():
    """检查是否有训练数据"""
    return row is not None and column is not None

def clear_data():
    """清空所有数据"""
    global row, column, df, best_model
    row = None
    column = None
    df = None
    best_model = None
    file_classification = {
        'class_0_name': '0类',
        'class_1_name': '1类', 
        'class_0_files': [],
        'class_1_files': []
    }
    
def set_best_model(model):
    """设置最佳模型"""
    global best_model
    best_model = model

def get_best_model():
    """获取最佳模型"""
    return best_model
