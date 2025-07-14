# data_processing.py - 数据处理模块

import os
import time
import pandas as pd
import numpy as np
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk

from config import DEFAULT_MZ_VALUES, CLASS_MAPPING, OUTPUT_FILES, NORMALIZATION_FACTOR, MZ_TOLERANCE
from utils import log_message, create_backup_filename

def process_file(file_name, X):
    """
    处理原始光谱数据文件，提取指定m/z值附近的最大信号强度。
    
    对每个指定的m/z值，在其±0.2的范围内查找最大信号强度，并进行归一化处理。
    
    参数:
        file_name (str): 原始数据文件路径
        X (list): 待提取的m/z值列表
        
    返回:
        pd.DataFrame: 包含m/z值和对应最大归一化信号强度的DataFrame
    """
    raw_data = pd.read_csv(file_name, sep=r'\s+', header=None)
    results = []
    
    for x in X:
        lower_bound = x - MZ_TOLERANCE
        upper_bound = x + MZ_TOLERANCE

        filtered_df = raw_data[(raw_data[0] >= lower_bound) & (raw_data[0] <= upper_bound)]
        max_value = filtered_df[1].div(NORMALIZATION_FACTOR).max() if not filtered_df.empty else None
        results.append([x, max_value])
    
    return pd.DataFrame(results, columns=['m/z', 'Max_Value'])

def select_and_process_files(root):
    """
    选择并处理多个原始光谱数据文件，生成用于机器学习的特征矩阵。
    
    参数:
        root: tkinter根窗口对象
    """
    file_paths = filedialog.askopenfilenames(
        title="选择要分析的文件", 
        filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
    )

    if not file_paths:
        log_message("未选择任何文件", "WARNING")
        return

    log_message("开始处理原始数据文件...")
    
    # 定义特征列表
    X = ['class'] + DEFAULT_MZ_VALUES
    X_series = pd.Series(data=X, index=X)
    all_results = pd.DataFrame(X_series, columns=['m/z'])

    # === 创建 CustomTkinter 进度条 ===
    progress_label = ctk.CTkLabel(root, text="进度: 0%")
    progress_label.grid(row=8, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
    
    progress_bar = ctk.CTkProgressBar(root, width=300)
    progress_bar.grid(row=9, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
    progress_bar.set(0)  # CustomTkinter 使用 0-1 范围

    progress_label.configure(text="正在处理文件...")

    # 处理每个文件
    for index, file_path in enumerate(file_paths, 1):
        file_result = process_file(file_path, [x for x in X if x != 'class'])
        file_result.set_index('m/z', inplace=True) 
        file_result.columns = [os.path.splitext(os.path.basename(file_path))[0]]
        file_result.loc['class'] = [os.path.splitext(os.path.basename(file_path))[0][:2]]
        all_results = pd.concat([all_results, file_result], axis=1)
        
        log_message(f"已处理文件 {index}/{len(file_paths)}: {os.path.basename(file_path)}")

        # 更新进度条
        progress_value = index / len(file_paths)
        progress_bar.set(progress_value)
        progress_label.configure(text=f"正在处理: {index}/{len(file_paths)} ({progress_value:.0%})")
        root.update()

    # 保存结果
    success = safe_file_save(all_results, OUTPUT_FILES['processed_data'])
    
    # 清理进度条
    progress_bar.grid_remove()
    progress_label.grid_remove()
    
    if not success:
        # 提供选择其他位置保存的选项
        response = messagebox.askyesno("权限错误", "无法保存文件到当前位置。\n是否选择其他位置保存文件？")
        if response:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("CSV files", "*.csv")],  # 改为CSV文件类型
                initialfile=OUTPUT_FILES['processed_data']
            )
            if save_path:
                try:
                    all_results.to_csv(save_path, index=True, float_format='%.8f')  # 改为to_csv
                    log_message(f"数据处理完成！结果已保存为 {os.path.abspath(file_path)}", "SUCCESS")
                    messagebox.showinfo("保存成功", f"文件已成功保存到:\n{save_path}")
                except Exception as e:
                    log_message(f"保存到新位置时出错: {str(e)}", "ERROR")
                    messagebox.showerror("保存失败", f"保存文件时出错:\n{str(e)}")

def safe_file_save(data, file_path):
    """安全地保存文件，包含备份和错误处理"""
    try:
        # 检查文件是否已存在
        if os.path.exists(file_path):
            log_message("发现已存在的文件，正在创建备份...", "INFO")
            backup_path = create_backup_filename(file_path)
            
            try:
                os.rename(file_path, backup_path)
                log_message(f"备份完成: {os.path.abspath(backup_path)}", "SUCCESS")
            except Exception as e:
                log_message(f"无法重命名已有文件: {str(e)}，将尝试直接保存新文件", "WARNING")

        # 保存新文件 - 改为.csv 格式
        log_message("正在保存处理结果...", "INFO")
        data.iloc[:, 1:].to_csv(file_path, index=True, float_format='%.8f')
        log_message(f"数据处理完成！结果已保存为 {os.path.abspath(file_path)}", "SUCCESS")
        return True

    except PermissionError:
        log_message("无法保存文件，可能是文件已被打开或没有写入权限", "ERROR")
        return False
    except Exception as e:
        log_message(f"保存文件时出错: {str(e)}", "ERROR")
        return False

def open_data_file(normalization_label, start_button, progress_bar):
    """
    打开并加载已处理的特征矩阵Excel文件，准备机器学习模型训练。
    
    参数:
        normalization_label: 显示文件选择状态的标签
        start_button: 训练开始按钮
        progress_bar: 进度条组件
        
    返回:
        tuple: (row, column, df) 特征矩阵、标签和原始DataFrame
    """
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])  # 改为CSV文件
    
    if not file_path:
        log_message("用户取消了文件选择")
        return None, None, None
    
    log_message(f"正在加载文件: {os.path.basename(file_path)}")
    
    try:
        df = pd.read_csv(file_path, index_col=0)
        df = df.iloc[:, 1:]

        if df.empty:
            normalization_label.configure(text="文件未选择")
            log_message("错误：所选文件为空，请选择有效的数据文件")
            return None, None, None

        # 检查文件格式
        if df.shape[0] < 2:
            error_msg = "Excel文件格式不正确，至少需要类别行和特征行"
            messagebox.showerror("格式错误", error_msg)
            log_message(f"错误：{error_msg}")
            return None, None, None

        # === 更新 CustomTkinter 控件状态 ===
        normalization_label.configure(text="已选择")
        start_button.configure(state='normal')
        progress_bar.set(0)  # CustomTkinter 进度条重置
        log_message("数据文件已成功加载")

        # 处理数据
        row = df.iloc[1:, :].values.T
        ylabels = df.iloc[0, :].values
        ylabels = pd.Series(ylabels)

        log_message(f"数据形状: {row.shape}, 样本数: {row.shape[0]}, 特征数: {row.shape[1]}")
        log_message(f"类别标签统计: {dict(ylabels.value_counts())}")

        # 检查类别数量
        if len(ylabels.value_counts()) < 2:
            warning_msg = "数据中只有一种类别，需要至少两种类别才能训练模型"
            messagebox.showwarning("警告", warning_msg)
            log_message(f"警告：{warning_msg}")

        # 标签编码
        column = np.array([CLASS_MAPPING.get(label, -1) for label in ylabels])

        # 检查未知类别
        if -1 in column:
            unknown_classes = set(ylabels[column == -1])
            warning_msg = f"发现未知类别: {unknown_classes}，请检查您的类别映射"
            log_message(f"警告：{warning_msg}")
            messagebox.showwarning("警告", warning_msg)
        else:
            log_message("标签编码完成，数据预处理成功")

        return row, column, df

    except FileNotFoundError:
        error_msg = f"文件未找到: {file_path}"
        messagebox.showerror("文件错误", error_msg)
        log_message(f"错误：{error_msg}")
    except pd.errors.EmptyDataError:
        error_msg = "Excel文件为空或格式不正确"
        messagebox.showerror("数据错误", error_msg)
        log_message(f"错误：{error_msg}")
    except Exception as e:
        error_msg = f"加载Excel文件时出错: {str(e)}"
        messagebox.showerror("未知错误", error_msg)
        log_message(f"错误：{error_msg}")
    
    return None, None, None
