# data_processing.py - 数据处理模块

# ========== 标准库导入 ==========
import os
import time

# ========== 第三方库导入 ==========
import customtkinter as ctk
import numpy as np
import pandas as pd
import pyopenms as oms
from tkinter import filedialog, messagebox, ttk

# ========== 本地模块导入 ==========
from config import (
    OUTPUT_FILES, MZ_TOLERANCE, MAX_FEATURES, MIN_OCCURRENCE_RATE, 
    MIN_FOLD_CHANGE, ENABLE_FALLBACK, FALLBACK_OCCURRENCE_RATE, 
    FALLBACK_FOLD_CHANGE, get_current_class_names, get_class_mapping, 
    get_class_mapping_for_labels, save_normalization_factor
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

def select_and_process_files_intelligent(root):
    """
    智能峰发现和特征提取的主函数
    """
    classification = data_store.get_file_classification()
    file_paths = classification['class_0_files'] + classification['class_1_files']
    
    if not file_paths:
        log_message("未找到已分类的文件", "WARNING")
        messagebox.showerror("错误", "未找到已分类的文件，请先进行文件分类")
        return
    
    log_message(f"从分类结果获取到 {len(file_paths)} 个文件")
    if not file_paths:  
        log_message("未选择任何文件", "WARNING")
        return

    try:
        log_message("🔬 开始智能峰发现处理...")
        
        # === 创建进度条 ===
        progress_label = ctk.CTkLabel(root, text="智能峰发现进度: 0%")
        progress_label.grid(row=8, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        progress_bar = ctk.CTkProgressBar(root, width=300)
        progress_bar.grid(row=9, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        progress_bar.set(0)

        # === 阶段1：峰发现 ===
        progress_label.configure(text="阶段1: 峰发现中...")
        log_message("=== 阶段1：从所有文件中发现峰 ===")
        
        all_peaks_data = []
        for index, file_path in enumerate(file_paths):
            # 调用峰发现函数
            peaks_df = discover_peaks_from_file(file_path)
            if not peaks_df.empty:
                all_peaks_data.append(peaks_df)
                log_message(f"文件 {os.path.basename(file_path)}: 发现 {len(peaks_df)} 个峰")
            
            # 更新进度 (0-33%)
            progress = (index + 1) / len(file_paths) * 0.33
            progress_bar.set(progress)
            progress_label.configure(text=f"峰发现: {index+1}/{len(file_paths)} ({progress:.0%})")
            root.update()

        if not all_peaks_data:
            raise ValueError("未从任何文件中发现有效峰")

        # === 阶段2：共识峰发现 ===
        progress_label.configure(text="阶段2: 特征选择中...")
        log_message("=== 阶段2：识别共识特征峰 ===")
        
        # 合并所有峰数据
        all_peaks_df = pd.concat(all_peaks_data, ignore_index=True)
        log_message(f"总计发现 {len(all_peaks_df)} 个峰候选")
        
        # 发现共识峰
        consensus_peaks = find_consensus_peaks(all_peaks_df)
        log_message(f"识别出 {len(consensus_peaks)} 个共识特征峰")
        
        # 更新进度到66%
        progress_bar.set(0.66)
        progress_label.configure(text="阶段2: 特征选择完成 (66%)")
        root.update()

        # === 阶段3：特征矩阵构建 ===
        progress_label.configure(text="阶段3: 构建特征矩阵...")
        log_message("=== 阶段3：构建最终特征矩阵 ===")
        
        # 构建特征矩阵
        all_results = build_feature_matrix(file_paths, consensus_peaks, progress_bar, progress_label, root)
        
        # === 复用现有的保存函数 ===
        success = safe_file_save(all_results, OUTPUT_FILES['processed_data'])
        
        # 清理进度条
        progress_bar.grid_remove()
        progress_label.grid_remove()

        if success:
            log_message("🎉 智能峰发现处理完成！", "SUCCESS")
            messagebox.showinfo("处理完成", 
                              f"智能峰发现完成！\n"
                              f"• 发现 {len(consensus_peaks)} 个特征峰\n"
                              f"• 处理 {len(file_paths)} 个样本\n"
                              f"• 结果已保存为 {OUTPUT_FILES['processed_data']}")
        else:
            response = messagebox.askyesno("权限错误", "无法保存文件到当前位置。\n是否选择其他位置保存文件？")
            if response:
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")],
                    initialfile=OUTPUT_FILES['processed_data']
                )
                if save_path:
                    try:
                        all_results.iloc[:, 1:].to_csv(save_path, index=True, float_format='%.8f')
                        log_message(f"数据处理完成！结果已保存为 {os.path.abspath(save_path)}", "SUCCESS")
                        messagebox.showinfo("保存成功", f"文件已成功保存到:\n{save_path}")
                    except Exception as e:
                        log_message(f"保存到新位置时出错: {str(e)}", "ERROR")
                        messagebox.showerror("保存失败", f"保存文件时出错:\n{str(e)}")
            
    except Exception as e:
        log_message(f"智能峰发现处理失败: {str(e)}", "ERROR")
        messagebox.showerror("处理错误", f"智能峰发现过程中出现错误：{str(e)}")
        # 清理进度条
        try:
            progress_bar.grid_remove()
            progress_label.grid_remove()
        except:
            pass

@validate_file_path(check_exists=True, allowed_extensions=['.txt'])
@handle_file_operations(show_ui_error=False, return_none_on_error=False)
def discover_peaks_from_file(file_path):
    """
    最基础的峰发现版本 - 专注于确保能发现峰
    """
    log_message(f"处理文件: {os.path.basename(file_path)}")
    
    # 1. 读取数据
    raw_data = pd.read_csv(file_path, sep=r'\s+', header=None, names=['mz', 'intensity'])
    log_message(f"读取数据点数: {len(raw_data)}")
    
    if raw_data.empty:
        return pd.DataFrame()
    
    # 2. 基本清理
    raw_data = raw_data[raw_data['intensity'] > 0]
    raw_data = raw_data.sort_values('mz').reset_index(drop=True)
    log_message(f"清理后数据点数: {len(raw_data)}")
    
    # 3. pyOpenMS最简单的峰拾取
    spectrum = oms.MSSpectrum()
    mz_array = raw_data['mz'].values.astype(float)
    intensity_array = raw_data['intensity'].values.astype(float)
    spectrum.set_peaks([mz_array, intensity_array])
    spectrum.sortByPosition()
    
    # 4. 使用最宽松的峰拾取参数
    picker = oms.PeakPickerHiRes()
    picker_param = picker.getDefaults()
    picker_param.setValue("signal_to_noise", 1.0)  # 很低的信噪比
    picker.setParameters(picker_param)
    
    picked_spectrum = oms.MSSpectrum()
    picker.pick(spectrum, picked_spectrum)
    
    log_message(f"峰拾取结果: {picked_spectrum.size()} 个峰")
    
    if picked_spectrum.size() == 0:
        log_message("未发现峰", "WARNING")
        return pd.DataFrame()
    
    # 5. 提取峰信息
    peak_mz, peak_intensity = picked_spectrum.get_peaks()
    
    # 6. 构建结果 - 使用新的分类方式
    file_id = os.path.splitext(os.path.basename(file_path))[0]
    file_class_name = get_file_classification(file_path)
    file_class = get_file_classification(file_path)
    if file_class is None:
        file_class = "UNKNOWN"
    else:
        file_class = file_class_name
    
    results = pd.DataFrame({
        'mz': peak_mz,
        'intensity': peak_intensity,
        'file_id': file_id,
        'class': file_class  # 使用新的分类方式
    })
    
    log_message(f"最终结果: {len(results)} 个峰")
    return results
    

def find_consensus_peaks(all_peaks_df, max_features=50):
    """
    专门为机器学习设计的共识峰发现
    """
    if all_peaks_df.empty:
        log_message("输入峰数据为空", "ERROR")
        return pd.DataFrame()
    
    # === 动态获取类别名称 ===
    class_0_name, class_1_name = get_current_class_names()
    
    log_message(f"开始ML导向的共识峰发现，输入 {len(all_peaks_df)} 个峰")
    log_message(f"使用类别: {class_0_name}, {class_1_name}")
    log_message(f"配置参数: 最大特征={MAX_FEATURES}, 覆盖率≥{MIN_OCCURRENCE_RATE:.1%}, 倍数变化≥{MIN_FOLD_CHANGE:.1f}")
    
    # === 使用动态类别名称 ===
    class_0_files = all_peaks_df[all_peaks_df['class'] == class_0_name]['file_id'].nunique()
    class_1_files = all_peaks_df[all_peaks_df['class'] == class_1_name]['file_id'].nunique()
    total_files = all_peaks_df['file_id'].nunique()
    
    log_message(f"数据统计: {class_0_name}文件 {class_0_files} 个, {class_1_name}文件 {class_1_files} 个, 总计 {total_files} 个")
    
    # 1. 按0.2 Da精度分组m/z值
    all_peaks_df = all_peaks_df.copy()
    all_peaks_df['mz_group'] = np.round(all_peaks_df['mz'] / 0.2) * 0.2
    
    consensus_peaks = []
    
    # 2. 对每个m/z组分析
    for mz_group in all_peaks_df['mz_group'].unique():
        group_data = all_peaks_df[all_peaks_df['mz_group'] == mz_group]
        
        # === 使用动态类别名称 ===
        class_0_data = group_data[group_data['class'] == class_0_name]
        class_1_data = group_data[group_data['class'] == class_1_name]
        
        # === 关键条件：两类都必须存在这个峰 ===
        class_0_file_count = class_0_data['file_id'].nunique() if len(class_0_data) > 0 else 0
        class_1_file_count = class_1_data['file_id'].nunique() if len(class_1_data) > 0 else 0
        
        # 两类都至少要有一定比例的文件包含这个峰
        class_0_occurrence_rate = class_0_file_count / class_0_files if class_0_files > 0 else 0
        class_1_occurrence_rate = class_1_file_count / class_1_files if class_1_files > 0 else 0
        
        # 过滤条件：两类都至少在20%的文件中出现
        min_occurrence_rate = 0.2
        if class_0_occurrence_rate < min_occurrence_rate or class_1_occurrence_rate < min_occurrence_rate:
            continue
        
        # 确保两类都有足够的数据点进行统计分析
        if len(class_0_data) < 2 or len(class_1_data) < 2:
            continue
        
        # 3. 计算统计指标
        consensus_mz = np.average(group_data['mz'], weights=group_data['intensity'])
        class_0_intensity_mean = class_0_data['intensity'].mean()
        class_1_intensity_mean = class_1_data['intensity'].mean()
        
        # 计算区分性
        fold_change = max(class_0_intensity_mean, class_1_intensity_mean) / (min(class_0_intensity_mean, class_1_intensity_mean) + 1e-6)
        
        # 使用config中的区分性要求
        if fold_change >= MIN_FOLD_CHANGE:
            # 计算ML友好性评分
            coverage_score = (class_0_occurrence_rate + class_1_occurrence_rate) / 2
            ml_score = fold_change * coverage_score
           
            consensus_peaks.append({
                'consensus_mz': consensus_mz,
                'peak_id': f'Peak_{len(consensus_peaks):03d}',
                'class_0_occurrence_rate': class_0_occurrence_rate,
                'class_1_occurrence_rate': class_1_occurrence_rate,
                'class_0_mean': class_0_intensity_mean,
                'class_1_mean': class_1_intensity_mean,
                'fold_change': fold_change,
                'ml_score': ml_score
            })

    consensus_df = pd.DataFrame(consensus_peaks)
    
    if not consensus_df.empty:
        # 按ML友好性得分排序
        consensus_df = consensus_df.sort_values('ml_score', ascending=False)
        
        # 使用config中的特征数量限制
        if len(consensus_df) > MAX_FEATURES:
            original_count = len(consensus_df)
            consensus_df = consensus_df.head(MAX_FEATURES)
            log_message(f"从 {original_count} 个候选中选择了top {MAX_FEATURES} 个特征")
        
        log_message(f"发现 {len(consensus_df)} 个ML共识峰")
        log_message(f"倍数变化范围: {consensus_df['fold_change'].min():.2f} - {consensus_df['fold_change'].max():.2f}")
        log_message(f"平均覆盖率: {class_0_name} {consensus_df['class_0_occurrence_rate'].mean():.1%}, {class_1_name} {consensus_df['class_1_occurrence_rate'].mean():.1%}")
    else:
        log_message("未发现符合条件的ML共识峰，建议调整config.py的参数", "WARNING")
    
    return consensus_df

# 更新匹配容差
def build_feature_matrix(file_paths, consensus_peaks, progress_bar, progress_label, root):
    """
    使用动态归一化的特征矩阵构建
    
    步骤：
    1. 第一轮：扫描所有文件，找到全局最大强度值
    2. 第二轮：使用全局最大值进行归一化处理
    """
    if consensus_peaks.empty:
        log_message("共识峰为空", "ERROR")
        return pd.DataFrame()
    
    log_message(f"构建动态归一化特征矩阵: {len(file_paths)} 文件 × {len(consensus_peaks)} 特征")
    log_message(f"使用容差: {MZ_TOLERANCE} Da")
    
    # === 第一轮：扫描所有数据，找到全局最大强度值 ===
    log_message("第一轮：扫描全局最大强度值...")
    global_max_intensity = 0.0
    all_file_peaks = {}  # 缓存每个文件的峰数据，避免重复计算
    
    for i, file_path in enumerate(file_paths):
        peaks_df = discover_peaks_from_file(file_path)
        file_id = os.path.splitext(os.path.basename(file_path))[0]
        # 缓存峰数据
        all_file_peaks[file_id] = peaks_df
        
        if not peaks_df.empty:
            file_max = peaks_df['intensity'].max()
            global_max_intensity = max(global_max_intensity, file_max)
        
        # 更新进度 (第一轮占33%)
        progress = 0.66 + (i + 1) / len(file_paths) * 0.17  # 66% - 83%
        progress_bar.set(progress)
        progress_label.configure(text=f"扫描最大值: {i+1}/{len(file_paths)} ({progress:.0%})")
        root.update()
    
    if global_max_intensity == 0:
        log_message("警告：未找到任何有效强度值", "WARNING")
        global_max_intensity = 1.0  # 避免除零错误
    
    log_message(f"全局最大强度值: {global_max_intensity:.2f}")
    log_message(f"将使用此值作为归一化因子")
    # 保存归一化因子到文件
    save_normalization_factor(global_max_intensity)

    # === 构建基础矩阵结构 ===
    feature_names = ['class'] + [f"{peak['consensus_mz']:.1f}" for _, peak in consensus_peaks.iterrows()]
    feature_series = pd.Series(data=feature_names, index=feature_names)
    all_results = pd.DataFrame(feature_series, columns=['m/z'])
    
    # === 第二轮：使用全局最大值进行归一化处理 ===
    log_message("第二轮：构建归一化特征矩阵...")
    
    for i, file_path in enumerate(file_paths):
        file_id = os.path.splitext(os.path.basename(file_path))[0]
        
        file_class = get_file_classification(file_path)
        if file_class is None:
            file_class = "UNKNOWN"
            
        # 使用缓存的峰数据
        peaks_df = all_file_peaks[file_id]
        
        # 创建文件结果列
        file_results = []
        
        # 第一行：类别标签
        file_results.append(file_class)
        
        # 后续行：对每个共识峰提取并归一化特征值
        for _, consensus_peak in consensus_peaks.iterrows():
            target_mz = consensus_peak['consensus_mz']
            
            if peaks_df.empty:
                normalized_intensity = 0.0
            else:
                # 在0.2 Da容差范围内搜索
                mz_diff = np.abs(peaks_df['mz'] - target_mz)
                matches = peaks_df[mz_diff <= MZ_TOLERANCE]
                
                if not matches.empty:
                    # 选择最接近的峰
                    best_match_idx = mz_diff[mz_diff <= MZ_TOLERANCE].idxmin()
                    raw_intensity = peaks_df.loc[best_match_idx, 'intensity']
                    
                    # === 关键：使用全局最大值进行归一化 ===
                    normalized_intensity = raw_intensity / global_max_intensity
                else:
                    normalized_intensity = 0.0
            
            file_results.append(normalized_intensity)
        
        # 将结果添加到总矩阵中
        file_series = pd.Series(file_results, index=feature_names)
        file_df = pd.DataFrame(file_series, columns=[file_id])
        all_results = pd.concat([all_results, file_df], axis=1)
        
        # 更新进度 (第二轮占17%)
        progress = 0.83 + (i + 1) / len(file_paths) * 0.17  # 83% - 100%
        progress_bar.set(progress)
        progress_label.configure(text=f"归一化处理: {i+1}/{len(file_paths)} ({progress:.0%})")
        root.update()
    
    log_message(f"动态归一化特征矩阵完成: {all_results.shape}")
    log_message(f"归一化因子: {global_max_intensity:.2f}")
    log_message(f"归一化后数值范围: 0.0 - 1.0")
    
    return all_results

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

@safe_data_processing(min_samples=5)
def open_data_file(normalization_label, start_button, progress_bar):
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
    try:
        # 优先从CSV数据自动检测
        class_mapping = get_class_mapping_for_labels(ylabels)
        log_message(f"使用检测到的类别映射: {class_mapping}")
    except Exception as e:
        # 回退到当前用户设置的映射
        class_mapping, _ = get_class_mapping()
        log_message(f"使用默认类别映射: {class_mapping}")
    
    column = np.array([class_mapping.get(label, -1) for label in ylabels])

    # 检查未知类别
    if -1 in column:
        unknown_classes = set(ylabels[column == -1])
        warning_msg = f"发现未知类别: {unknown_classes}，请检查您的类别映射"
        log_message(f"警告：{warning_msg}")
        messagebox.showwarning("警告", warning_msg)
    else:
        log_message("标签编码完成，数据预处理成功")

    return row, column, df
