# utils.py - 工具函数和日志系统

# 标准库导入
import datetime
import os

# 第三方库导入
import customtkinter as ctk
import tkinter as tk
import sys

# 全局变量
info_text = None
root = None

def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径（兼容开发和打包环境）
    
    Args:
        relative_path: 相对路径，例如 'assets/app_icon.ico'
    
    Returns:
        str: 资源文件的绝对路径
    """
    try:
        # PyInstaller 打包后的临时文件夹路径
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境，使用项目根目录
        # 假设此文件在 src/ 目录下，根目录是父目录
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_path, relative_path)

def center_window(window, width, height):
    """
    将窗口居中显示，兼容 Windows 高 DPI 缩放。

    Args:
        window: tk/ctk 窗口对象
        width:  窗口宽度（逻辑像素）
        height: 窗口高度（逻辑像素）
    """
    window.update_idletasks()
    try:
        import ctypes
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        sh = ctypes.windll.user32.GetSystemMetrics(1)
        scale = sw / window.winfo_screenwidth()
        x = (sw - int(width * scale)) // 2
        y = (sh - int(height * scale)) // 2
    except Exception:
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
    window.geometry(f"+{x}+{y}")


def set_window_icon(window):
    """设置窗口图标 - 带稳定性保证"""
    if not window.winfo_exists():
        return
    try:
        from config import ICON_CONFIG
        if sys.platform == "darwin":
            icon = tk.PhotoImage(
                file=str(ICON_CONFIG.get('app_icon_png', 'icon.png')))
            window.iconphoto(False, icon)
            # 保持引用防止被垃圾回收
            window._icon_ref = icon
        else:
            window.iconbitmap(ICON_CONFIG.get('app_icon_ico', 'icon.ico'))
            # window.after(200, lambda: window.iconbitmap(
            #    ICON_CONFIG.get('app_icon_ico', 'icon.ico')))
            window.after(200, window.iconbitmap,
                         ICON_CONFIG.get('app_icon_ico', 'icon.ico'))

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
