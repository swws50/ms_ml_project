# utils.py - 工具函数和日志系统

# 标准库导入 
import datetime
import os

# 第三方库导入 
import customtkinter as ctk
from tkinter import PhotoImage


# 全局变量
info_text = None
root = None

def set_window_icon(window):
    """设置应用程序图标"""
    from config import ICON_CONFIG
    try:
        window.iconbitmap(ICON_CONFIG['app_icon_ico'])
    except:
        try:
            icon = PhotoImage(file=ICON_CONFIG['app_icon_png'])
            window.iconphoto(True, icon)
            window._app_icon_ref = icon
        except:
            pass

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

