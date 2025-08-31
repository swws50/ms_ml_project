# data_processing.py - 数据处理模块

# 标准库导入 
import os
import time

# 第三方库导入 
import customtkinter as ctk
import numpy as np
import pandas as pd
import pyopenms as oms
from tkinter import filedialog, messagebox, ttk

# 本地模块导入 
from config import (
    OUTPUT_FILES, MZ_TOLERANCE, MAX_FEATURES, MIN_OCCURRENCE_RATE, 
    MIN_FOLD_CHANGE, get_class_mapping
)
import data_store
from output_manager import output_manager
from utils import log_message, create_backup_filename
from validation_decorators import safe_data_processing, handle_file_operations, validate_file_path



def get_file_classification(file_path):
    """根据文件路径获取分类"""
    
    classification = data_store.get_file_classification()
    
    if file_path in classification['class_0_files']:
        return classification['class_0_name']
    elif file_path in classification['class_1_files']:
        return classification['class_1_name']
    else:
        return None

@safe_data_processing(min_samples=5)
def open_data_file(normalization_label, start_button):
    """
    打开并加载已处理的特征矩阵.csv文件，准备机器学习模型训练。
    
    参数:
        normalization_label: 显示文件选择状态的标签
        start_button: 训练开始按钮
        progress_bar: 进度条组件
        
    返回:
        tuple: (row, column, df) 特征矩阵、标签和原始DataFrame
    """
    initial_dir = str(output_manager.get_path('data', ''))
    
    # 如果data文件夹不存在，回退到当前目录
    if not os.path.exists(initial_dir):
        initial_dir = "/"
    
    file_path = filedialog.askopenfilename(
        initialdir=initial_dir,  # 默认打开data文件夹
        title="选择归一化CSV文件",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not file_path:
        log_message("用户取消了文件选择")
        return None, None, None
    
    data_store.set_training_data_path(file_path)
    
    log_message(f"正在加载文件: {os.path.basename(file_path)}")
    
    
    df = pd.read_csv(file_path, index_col=0)
    df = df.iloc[:, 1:]
    
    # 清除旧的分类信息，强制使用CSV中的实际标签
    data_store.clear_file_classification()

    # 更新 CustomTkinter 控件状态 
    normalization_label.configure(text="已选择")
    start_button.configure(state='normal')
    log_message("数据文件已成功加载")

    # 处理数据
    row = df.iloc[1:, :].values.T
    ylabels = df.iloc[0, :].values
    ylabels = pd.Series(ylabels).astype(str)

    # 从CSV读取类别并保存到datastore
    unique_labels = ylabels.unique()
    if len(unique_labels) >= 2:
        classification_data = {
            'class_0_name': str(unique_labels[0]),
            'class_1_name': str(unique_labels[1]),
            'class_0_files': [],  # CSV模式下不需要文件列表
            'class_1_files': []
        }
        data_store.set_file_classification(classification_data)
        log_message(f"从CSV读取类别并保存: {unique_labels[0]}, {unique_labels[1]}")
        
    log_message(f"数据形状: {row.shape}, 样本数: {row.shape[0]}, 特征数: {row.shape[1]}")
    log_message(f"类别标签统计: {dict(ylabels.value_counts())}")

    # 检查类别数量
    if len(ylabels.value_counts()) < 2:
        warning_msg = "数据中只有一种类别，需要至少两种类别才能训练模型"
        messagebox.showwarning("警告", warning_msg)
        log_message(f"警告：{warning_msg}")
        
    # 标签编码
    class_mapping, _ = get_class_mapping()
    column = np.array([class_mapping[label] for label in ylabels])


    log_message("标签编码完成，数据预处理成功")

    return row, column, df
