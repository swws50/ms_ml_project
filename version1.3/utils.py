# utils.py - 工具函数和日志系统
import customtkinter as ctk
import os
import datetime

# 全局变量
info_text = None
root = None

def set_global_widgets(info_widget, root_widget):
    """设置全局组件引用"""
    global info_text, root
    info_text = info_widget
    root = root_widget

def log_message(message, level="INFO"):
    """增强的日志函数，支持不同级别"""
    global info_text, root
    if info_text is not None:
        # 使用简单符号
        if level == "ERROR":
            formatted_message = f"x 错误: {message}"
        elif level == "WARNING": 
            formatted_message = f"! 警告: {message}"
        elif level == "SUCCESS":
            formatted_message = f"√ 成功: {message}"
        elif level == "INFO":
            formatted_message = f"i 信息: {message}"
        else:
            formatted_message = message

        # CustomTkinter 的文本框使用 "end" 而不是 tkinter.END    
        info_text.insert("end", formatted_message + "\n")
        info_text.see("end")  # 滚动到最后
        if root is not None:
            root.update()
    else:
        print(message)

def clear_log():
    """清空日志信息"""
    global info_text
    if info_text is not None:
        # CustomTkinter 使用不同的删除方法
        info_text.delete("1.0", "end")

def create_backup_filename(original_path):
    """创建备份文件名"""
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    base_name = os.path.splitext(original_path)[0]
    extension = os.path.splitext(original_path)[1]
    
    backup_file_path = f'{base_name}-{current_date}{extension}'
    
    # 如果备份文件也存在，添加编号
    counter = 1
    while os.path.exists(backup_file_path):
        backup_file_path = f'{base_name}-{current_date}_{counter}{extension}'
        counter += 1
    
    return backup_file_path

def validate_data(row, column, min_samples=5):
    """验证训练数据的有效性"""
    try:
        # 检查数据是否正确加载
        if row is None or column is None:
            return False, "数据未正确加载"

        # 检查样本数量
        n_samples = row.shape[0] if hasattr(row, 'shape') else len(row)
        if n_samples < min_samples:
            return False, f"样本数量不足（当前只有{n_samples}个样本）"

        # 检查类别分布
        import numpy as np
        unique_classes = np.unique(column)
        if len(unique_classes) < 2:
            return False, f"数据中只包含一种类别 ({unique_classes[0]})"

        return True, f"数据验证通过，样本数: {n_samples}, 类别: {unique_classes}"

    except Exception as e:
        return False, f"数据验证出错: {str(e)}"
