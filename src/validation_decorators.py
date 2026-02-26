# validation_decorators.py - 统一的数据验证和错误处理装饰器
# v1.9.8.3 - 清理未使用的装饰器

import functools
import time

import numpy as np
import pandas as pd
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
            except pd.errors.EmptyDataError:
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
            result = func(*args, **kwargs)
            
            if isinstance(result, tuple) and len(result) >= 2:
                row, column = result[0], result[1]
                
                if row is None or column is None:
                    log_message("数据未正确加载", "ERROR")
                    messagebox.showerror("数据验证错误", "数据未正确加载")
                    return None, None, None if len(result) == 3 else (None, None)

                n_samples = row.shape[0] if hasattr(row, 'shape') else len(row)
                if n_samples < min_samples:
                    error_msg = f"样本数量不足（当前只有{n_samples}个样本，需要至少{min_samples}个）"
                    log_message(error_msg, "ERROR")
                    messagebox.showerror("数据验证错误", error_msg)
                    return None, None, None if len(result) == 3 else (None, None)

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


def log_execution_time(func):
    """记录函数执行时间的装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        log_message(f"开始执行: {func.__name__}")
        
        result = func(*args, **kwargs)
        
        execution_time = time.time() - start_time
        log_message(f"执行完成: {func.__name__} (耗时: {execution_time:.2f}秒)", "SUCCESS")
        
        return result
    return wrapper


def safe_data_processing(min_samples=5):
    """
    安全数据处理组合装饰器
    结合了文件操作、数据验证和执行时间记录
    """
    def decorator(func):
        decorated_func = handle_file_operations()(func)
        decorated_func = validate_training_data(min_samples)(decorated_func)
        decorated_func = log_execution_time(decorated_func)
        return decorated_func
    return decorator