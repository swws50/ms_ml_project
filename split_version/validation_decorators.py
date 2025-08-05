# validation_decorators.py - 统一的数据验证和错误处理装饰器

import functools
import os
import pandas as pd
import numpy as np
from tkinter import messagebox
from utils import log_message

def handle_file_operations(show_ui_error=True, return_none_on_error=True):
    """
    文件操作错误处理装饰器
    
    参数:
        show_ui_error: 是否显示UI错误弹窗
        return_none_on_error: 错误时是否返回None
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                error_msg = f"文件未找到: {str(e)}"
                log_message(error_msg, "ERROR")
                if show_ui_error:
                    messagebox.showerror("文件错误", error_msg)
                return None if return_none_on_error else False
            except PermissionError as e:
                error_msg = f"文件权限错误: {str(e)}"
                log_message(error_msg, "ERROR")
                if show_ui_error:
                    messagebox.showerror("权限错误", error_msg)
                return None if return_none_on_error else False
            except pd.errors.EmptyDataError as e:
                error_msg = "文件为空或格式不正确"
                log_message(error_msg, "ERROR")
                if show_ui_error:
                    messagebox.showerror("数据错误", error_msg)
                return None if return_none_on_error else False
            except Exception as e:
                error_msg = f"文件操作时出错: {str(e)}"
                log_message(error_msg, "ERROR")
                if show_ui_error:
                    messagebox.showerror("未知错误", error_msg)
                return None if return_none_on_error else False
        return wrapper
    return decorator

def validate_training_data(min_samples=5):
    """
    训练数据验证装饰器
    
    参数:
        min_samples: 最小样本数量要求
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 如果返回的是训练数据元组，进行验证
            if isinstance(result, tuple) and len(result) >= 2:
                row, column = result[0], result[1]
                
                # 检查数据是否正确加载
                if row is None or column is None:
                    log_message("数据未正确加载", "ERROR")
                    messagebox.showerror("数据验证错误", "数据未正确加载")
                    return None, None, None if len(result) == 3 else (None, None)

                # 检查样本数量
                n_samples = row.shape[0] if hasattr(row, 'shape') else len(row)
                if n_samples < min_samples:
                    error_msg = f"样本数量不足（当前只有{n_samples}个样本，需要至少{min_samples}个）"
                    log_message(error_msg, "ERROR")
                    messagebox.showerror("数据验证错误", error_msg)
                    return None, None, None if len(result) == 3 else (None, None)

                # 检查类别分布
                unique_classes = np.unique(column)
                if len(unique_classes) < 2:
                    error_msg = f"数据中只包含一种类别 ({unique_classes[0]})，需要至少两种类别"
                    log_message(error_msg, "ERROR")
                    messagebox.showerror("数据验证错误", error_msg)
                    return None, None, None if len(result) == 3 else (None, None)

                log_message(f"数据验证通过 - 样本数: {n_samples}, 类别: {unique_classes}", "SUCCESS")
            
            return result
        return wrapper
    return decorator

def safe_model_operation(operation_name="模型操作"):
    """
    模型操作安全执行装饰器
    
    参数:
        operation_name: 操作名称，用于错误提示
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                error_msg = f"{operation_name}参数错误: {str(e)}"
                log_message(error_msg, "ERROR")
                messagebox.showerror("参数错误", error_msg)
                return None
            except ImportError as e:
                error_msg = f"{operation_name}缺少必要依赖: {str(e)}"
                log_message(error_msg, "ERROR")
                messagebox.showerror("依赖错误", error_msg)
                return None
            except Exception as e:
                error_msg = f"{operation_name}时出现未知错误: {str(e)}"
                log_message(error_msg, "ERROR")
                messagebox.showerror("未知错误", error_msg)
                return None
        return wrapper
    return decorator

def require_data_store(data_type="training_data"):
    """
    检查data_store中是否有必要数据的装饰器
    
    参数:
        data_type: 需要的数据类型 ("training_data", "model", "classification")
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import data_store
            
            if data_type == "training_data":
                if not data_store.has_training_data():
                    error_msg = "未找到有效训练数据，请先选择数据文件"
                    log_message(error_msg, "ERROR")
                    messagebox.showerror("数据错误", error_msg)
                    return None
                    
            elif data_type == "model":
                if data_store.get_best_model() is None:
                    error_msg = "未找到训练好的模型，请先完成模型训练"
                    log_message(error_msg, "ERROR")
                    messagebox.showerror("模型错误", error_msg)
                    return None
                    
            elif data_type == "classification":
                classification = data_store.get_file_classification()
                if not classification['class_0_files'] and not classification['class_1_files']:
                    error_msg = "未找到文件分类信息，请先进行文件分类"
                    log_message(error_msg, "ERROR")
                    messagebox.showerror("分类错误", error_msg)
                    return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def log_execution_time(func):
    """
    记录函数执行时间的装饰器
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        log_message(f"开始执行: {func.__name__}")
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        execution_time = end_time - start_time
        log_message(f"执行完成: {func.__name__} (耗时: {execution_time:.2f}秒)", "SUCCESS")
        
        return result
    return wrapper

def validate_file_path(check_exists=True, allowed_extensions=None):
    """
    文件路径验证装饰器
    
    参数:
        check_exists: 是否检查文件存在
        allowed_extensions: 允许的文件扩展名列表，如 ['.txt', '.csv']
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(file_path, *args, **kwargs):
            if not file_path:
                log_message("文件路径为空", "ERROR")
                return None
                
            if check_exists and not os.path.exists(file_path):
                error_msg = f"文件不存在: {file_path}"
                log_message(error_msg, "ERROR")
                return None
                
            if allowed_extensions:
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext not in allowed_extensions:
                    error_msg = f"不支持的文件格式: {file_ext}，支持的格式: {allowed_extensions}"
                    log_message(error_msg, "ERROR")
                    return None
            
            return func(file_path, *args, **kwargs)
        return wrapper
    return decorator

# 组合装饰器：常用的装饰器组合
def safe_data_processing(min_samples=5):
    """
    安全数据处理组合装饰器
    结合了文件操作、数据验证和执行时间记录
    """
    def decorator(func):
        # 多个装饰器的组合应用
        decorated_func = handle_file_operations()(func)
        decorated_func = validate_training_data(min_samples)(decorated_func)
        decorated_func = log_execution_time(decorated_func)
        return decorated_func
    return decorator
