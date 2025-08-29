# data_preprocessor.py - 简化版数据预处理器

import os
import time
from typing import List, Optional

import numpy as np
import pandas as pd
import pyopenms as oms
import customtkinter as ctk
from tkinter import messagebox, filedialog

from config import (
    OUTPUT_FILES, MZ_TOLERANCE, MAX_FEATURES, MIN_OCCURRENCE_RATE, 
    MIN_FOLD_CHANGE, get_class_mapping, save_normalization_factor
)
import data_store
from utils import log_message, create_backup_filename, set_window_icon


class DataPreprocessor:
    """数据预处理器类 - 保持原有接口的简单版本"""
    
    def __init__(self):
        self.global_max_intensity = 0.0
        self.all_file_peaks_cache = {}
        
        # GUI组件
        self.root = None
        self.progress_bar = None
        self.progress_label = None
        self.classification_window = None
        
        # 分类数据
        self.class_0_files = []
        self.class_1_files = []
        self.class_0_name = "类别0"
        self.class_1_name = "类别1"

    def show_classification_dialog(self, parent_root):
        """显示文件分类对话框"""
        self.root = parent_root
        self._create_classification_window()
    
    def process_classified_files(self, root):
        """处理已分类的文件（保持原接口）"""
        self.root = root
        
        # 获取分类文件
        classification = data_store.get_file_classification()
        file_paths = classification['class_0_files'] + classification['class_1_files']
        
        if not file_paths:
            log_message("未找到已分类的文件", "WARNING")
            messagebox.showerror("错误", "未找到已分类的文件，请先进行文件分类")
            return
        
        self._execute_processing(file_paths)    
    
    def _create_classification_window(self):
        """创建文件分类窗口"""
        # 检查是否已有窗口打开
        if self.classification_window and self.classification_window.winfo_exists():
            self.classification_window.lift()
            self.classification_window.focus_force()
            return
        
        # 创建新窗口
        self.classification_window = ctk.CTkToplevel(self.root)
        self.classification_window.title("数据文件分类设置")
        
        # 计算居中位置
        window_width, window_height = 700, 750
        screen_width = self.classification_window.winfo_screenwidth()
        screen_height = self.classification_window.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        self.classification_window.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.classification_window.resizable(True, True)
        
        # 图标
        set_window_icon(self.classification_window)

        # 窗口置顶和焦点设置
        self.classification_window.attributes('-topmost', True)
        self.classification_window.focus_force()
        self.classification_window.lift()
        self.classification_window.grab_set()
        self.classification_window.after(1000, lambda: self.classification_window.attributes('-topmost', False))
        
        # 创建UI组件
        self._create_classification_ui()
        
        # 窗口关闭处理
        def on_closing():
            self.classification_window.grab_release()
            self.classification_window.destroy()
            self.classification_window = None
        
        self.classification_window.protocol("WM_DELETE_WINDOW", on_closing)

    def _create_classification_ui(self):
        """创建分类窗口的UI组件"""
        # 标题
        title_label = ctk.CTkLabel(self.classification_window, 
                                  text="数据文件分类设置", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=10)
        
        # 类别名称设置区域
        name_frame = ctk.CTkFrame(self.classification_window)
        name_frame.pack(fill='x', padx=20, pady=10)
        
        ctk.CTkLabel(name_frame, text="类别名称设置（可手动更改命名）:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=5)
        
        name_input_frame = ctk.CTkFrame(name_frame, fg_color="transparent")
        name_input_frame.pack(fill='x', padx=10, pady=5)
        
        # 类别名称输入框
        class_0_name_var = ctk.StringVar(value=self.class_0_name)
        class_1_name_var = ctk.StringVar(value=self.class_1_name)
        
        ctk.CTkLabel(name_input_frame, text="类别0:").pack(side='left', padx=5)
        class_0_entry = ctk.CTkEntry(name_input_frame, textvariable=class_0_name_var, width=120)
        class_0_entry.pack(side='left', padx=5)
        
        ctk.CTkLabel(name_input_frame, text="类别1:").pack(side='left', padx=(20, 5))
        class_1_entry = ctk.CTkEntry(name_input_frame, textvariable=class_1_name_var, width=120)
        class_1_entry.pack(side='left', padx=5)
        
        # 文件夹选择区域
        self._create_folder_selection_ui(class_0_name_var, class_1_name_var)
        
        # 预览区域
        preview_text = self._create_preview_ui()
        
        # 底部按钮
        self._create_action_buttons(class_0_name_var, class_1_name_var, preview_text)
        
        # 绑定名称变化事件
        class_0_name_var.trace('w', lambda *args: self._update_preview(preview_text, class_0_name_var, class_1_name_var))
        class_1_name_var.trace('w', lambda *args: self._update_preview(preview_text, class_0_name_var, class_1_name_var))
    
    def _create_folder_selection_ui(self, class_0_name_var, class_1_name_var):
        """创建文件夹选择UI"""
        folder_frame = ctk.CTkFrame(self.classification_window)
        folder_frame.pack(fill='x', padx=20, pady=10)
        
        ctk.CTkLabel(folder_frame, text="文件夹选择:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=5)
        
        # 类别0文件夹选择
        class_0_folder_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
        class_0_folder_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(class_0_folder_frame, text="📁 类别0文件夹:").pack(anchor='w')
        
        self.class_0_path_label = ctk.CTkLabel(class_0_folder_frame, text="未选择", 
                                             font=ctk.CTkFont(size=10), text_color="gray")
        self.class_0_path_label.pack(anchor='w')
        
        self.class_0_count_label = ctk.CTkLabel(class_0_folder_frame, text="", 
                                              font=ctk.CTkFont(size=10), text_color="blue")
        self.class_0_count_label.pack(anchor='w')
        
        ctk.CTkButton(class_0_folder_frame, text="选择文件夹...", 
                     command=lambda: self._select_class_folder(0, class_0_name_var, class_1_name_var), 
                     width=120).pack(anchor='w', pady=2)
        
        # 类别1文件夹选择（类似的UI）
        class_1_folder_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
        class_1_folder_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(class_1_folder_frame, text="📁 类别1文件夹:").pack(anchor='w')
        
        self.class_1_path_label = ctk.CTkLabel(class_1_folder_frame, text="未选择", 
                                             font=ctk.CTkFont(size=10), text_color="gray")
        self.class_1_path_label.pack(anchor='w')
        
        self.class_1_count_label = ctk.CTkLabel(class_1_folder_frame, text="", 
                                              font=ctk.CTkFont(size=10), text_color="blue")
        self.class_1_count_label.pack(anchor='w')
        
        ctk.CTkButton(class_1_folder_frame, text="选择文件夹...", 
                     command=lambda: self._select_class_folder(1, class_0_name_var, class_1_name_var), 
                     width=120).pack(anchor='w', pady=2)
        
    def _create_preview_ui(self):
        """创建预览区域"""
        preview_frame = ctk.CTkFrame(self.classification_window)
        preview_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(preview_frame, text="预览:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=5)
        
        preview_text = ctk.CTkTextbox(preview_frame, height=120)
        preview_text.pack(fill='both', expand=True, padx=10, pady=5)
        
        return preview_text
    
    def _create_action_buttons(self, class_0_name_var, class_1_name_var, preview_text):
        """创建底部操作按钮"""
        button_frame = ctk.CTkFrame(self.classification_window, fg_color="transparent")
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ctk.CTkButton(button_frame, text="取消", 
                     command=self._cancel_classification, width=100).pack(side='left')
        
        ctk.CTkButton(button_frame, text="开始处理", 
                     command=lambda: self._confirm_and_process(class_0_name_var, class_1_name_var), 
                     width=120).pack(side='right')

    def _select_class_folder(self, class_index, class_0_name_var, class_1_name_var):
        """选择类别文件夹"""
        folder_path = filedialog.askdirectory(title=f"选择类别{class_index}文件夹")
        if folder_path:
            txt_files = []
            for file in os.listdir(folder_path):
                if file.lower().endswith('.txt'):
                    txt_files.append(os.path.join(folder_path, file))
            
            if class_index == 0:
                self.class_0_files = txt_files
                self.class_0_path_label.configure(text=f"路径: {folder_path}")
                self.class_0_count_label.configure(text=f"找到: {len(txt_files)} 个 .txt 文件")
            else:
                self.class_1_files = txt_files
                self.class_1_path_label.configure(text=f"路径: {folder_path}")
                self.class_1_count_label.configure(text=f"找到: {len(txt_files)} 个 .txt 文件")
            
            self._update_preview(None, class_0_name_var, class_1_name_var)
    
    def _update_preview(self, preview_text, class_0_name_var, class_1_name_var):
        """更新预览信息"""
        if not hasattr(self, 'preview_text_widget'):
            # 找到预览文本框（如果没有传入）
            for widget in self.classification_window.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkTextbox):
                            preview_text = child
                            self.preview_text_widget = preview_text
                            break
        else:
            preview_text = self.preview_text_widget
        
        if preview_text:
            preview_text.delete("1.0", "end")
            
            if self.class_0_files:
                file_names = [os.path.basename(f) for f in self.class_0_files[:5]]
                preview_text.insert("end", f"{class_0_name_var.get()} ({len(self.class_0_files)}个文件):\n")
                preview_text.insert("end", f"  {', '.join(file_names)}")
                if len(self.class_0_files) > 5:
                    preview_text.insert("end", f"... 还有{len(self.class_0_files)-5}个文件")
                preview_text.insert("end", "\n\n")
            
            if self.class_1_files:
                file_names = [os.path.basename(f) for f in self.class_1_files[:5]]
                preview_text.insert("end", f"{class_1_name_var.get()} ({len(self.class_1_files)}个文件):\n")
                preview_text.insert("end", f"  {', '.join(file_names)}")
                if len(self.class_1_files) > 5:
                    preview_text.insert("end", f"... 还有{len(self.class_1_files)-5}个文件")
                preview_text.insert("end", "\n\n")
            
            if not self.class_0_files and not self.class_1_files:
                preview_text.insert("end", "请选择文件夹以预览分类结果")
    
    def _cancel_classification(self):
        """取消分类"""
        if self.classification_window:
            self.classification_window.grab_release()
            self.classification_window.destroy()
            self.classification_window = None
    
    def _confirm_and_process(self, class_0_name_var, class_1_name_var):
        """确认分类并开始处理"""
        if not self.class_0_files and not self.class_1_files:
            messagebox.showwarning("警告", "请至少选择一个文件夹")
            return
        
        if not self.class_0_files:
            response = messagebox.askyesno("确认", "类别0没有文件，是否继续？")
            if not response:
                return
        
        if not self.class_1_files:
            response = messagebox.askyesno("确认", "类别1没有文件，是否继续？")
            if not response:
                return
        
        # 更新类别名称
        self.class_0_name = class_0_name_var.get()
        self.class_1_name = class_1_name_var.get()
        
        # 保存分类信息到data_store
        classification_data = {
            'class_0_name': self.class_0_name,
            'class_1_name': self.class_1_name,
            'class_0_files': self.class_0_files,
            'class_1_files': self.class_1_files
        }
        data_store.set_file_classification(classification_data)
        
        log_message(f"文件分类完成: {self.class_0_name}({len(self.class_0_files)}个), {self.class_1_name}({len(self.class_1_files)}个)")
        
        # 关闭分类窗口
        self.classification_window.grab_release()
        self.classification_window.destroy()
        self.classification_window = None
        
        # 直接开始处理
        file_paths = self.class_0_files + self.class_1_files
        self._execute_processing(file_paths)

    def _execute_processing(self, file_paths: List[str]):
        """执行数据处理"""
        # 创建进度显示
        self._create_progress_ui()
        
        try:
            log_message("开始智能峰发现处理...")
            
            # 阶段1: 峰发现
            log_message(" 阶段1：从所有文件中发现峰 ")
            all_peaks_data = self._phase1_discover_peaks(file_paths)
            
            if not all_peaks_data:
                raise ValueError("未从任何文件中发现有效峰")
            
            # 阶段2: 共识峰识别
            log_message(" 阶段2：识别共识特征峰 ")
            consensus_peaks = self._phase2_consensus_peaks(all_peaks_data)
            
            if consensus_peaks.empty:
                raise ValueError("未识别出共识特征峰")
            
            # 阶段3: 特征矩阵构建
            log_message(" 阶段3：构建最终特征矩阵 ")
            feature_matrix = self._phase3_build_matrix(file_paths, consensus_peaks)
            
            # 保存结果
            success = self._save_results(feature_matrix)
            
            if success:
                log_message("智能峰发现处理完成！", "SUCCESS")
                messagebox.showinfo("处理完成", 
                                  f"智能峰发现完成！\n"
                                  f"• 发现 {len(consensus_peaks)} 个特征峰\n"
                                  f"• 处理 {len(file_paths)} 个样本\n"
                                  f"• 结果已保存为 {OUTPUT_FILES['processed_data']}")
            else:
                self._handle_save_failure()
                
        except Exception as e:
            log_message(f"智能峰发现处理失败: {str(e)}", "ERROR")
            messagebox.showerror("处理错误", f"智能峰发现过程中出现错误：{str(e)}")
        finally:
            self._cleanup_progress_ui()

    def process_classified_files(self, root):
        """
        主处理函数 - 保持与原版本完全相同的调用接口
        
        Args:
            root: GUI根窗口，用于进度显示
        """
        self.root = root
        
        # 获取分类文件
        classification = data_store.get_file_classification()
        file_paths = classification['class_0_files'] + classification['class_1_files']
        
        if not file_paths:
            log_message("未找到已分类的文件", "WARNING")
            messagebox.showerror("错误", "未找到已分类的文件，请先进行文件分类")
            return
        
        # 创建进度显示
        self._create_progress_ui()
        
        try:
            log_message("开始智能峰发现处理...")
            
            # 阶段1: 峰发现
            log_message(" 阶段1：从所有文件中发现峰 ")
            all_peaks_data = self._phase1_discover_peaks(file_paths)
            
            if not all_peaks_data:
                raise ValueError("未从任何文件中发现有效峰")
            
            # 阶段2: 共识峰识别
            log_message(" 阶段2：识别共识特征峰 ")
            consensus_peaks = self._phase2_consensus_peaks(all_peaks_data)
            
            if consensus_peaks.empty:
                raise ValueError("未识别出共识特征峰")
            
            # 阶段3: 特征矩阵构建
            log_message(" 阶段3：构建最终特征矩阵 ")
            feature_matrix = self._phase3_build_matrix(file_paths, consensus_peaks)
            
            # 保存结果
            success = self._save_results(feature_matrix)
            
            if success:
                log_message("智能峰发现处理完成！", "SUCCESS")
                messagebox.showinfo("处理完成", 
                                  f"智能峰发现完成！\n"
                                  f"• 发现 {len(consensus_peaks)} 个特征峰\n"
                                  f"• 处理 {len(file_paths)} 个样本\n"
                                  f"• 结果已保存为 {OUTPUT_FILES['processed_data']}")
            else:
                self._handle_save_failure()
                
        except Exception as e:
            log_message(f"智能峰发现处理失败: {str(e)}", "ERROR")
            messagebox.showerror("处理错误", f"智能峰发现过程中出现错误：{str(e)}")
        finally:
            self._cleanup_progress_ui()
    
    def _create_progress_ui(self):
        """创建进度显示界面"""
        if self.root and hasattr(self.root, 'gui_manager'):
            self.root.gui_manager.show_global_progress("开始智能峰发现处理...")
    
    def _cleanup_progress_ui(self):
        """清理进度显示界面 - 隐藏全局进度条"""  
        if self.root and hasattr(self.root, 'gui_manager'):
            self.root.gui_manager.hide_global_progress()
        
    def _update_progress(self, progress: float, message: str):
        """更新进度显示"""
        if self.root and hasattr(self.root, 'gui_manager'):
            # 使用全局进度条
            self.root.gui_manager.update_global_progress(progress, message)
        
        if self.root:
            self.root.update()
    
    def _phase1_discover_peaks(self, file_paths: List[str]) -> List[pd.DataFrame]:
        """阶段1: 峰发现"""
        self._update_progress(0, "阶段1: 峰发现中...")
        
        all_peaks_data = []
        for index, file_path in enumerate(file_paths):
            peaks_df = self._discover_peaks_from_file(file_path)
            if not peaks_df.empty:
                all_peaks_data.append(peaks_df)
                log_message(f"文件 {os.path.basename(file_path)}: 发现 {len(peaks_df)} 个峰")
            
            # 更新进度 (0-33%)
            progress = (index + 1) / len(file_paths) * 0.33
            message = f"峰发现: {index+1}/{len(file_paths)} ({progress:.0%})"
            self._update_progress(progress, message)
        
        return all_peaks_data
    
    def _phase2_consensus_peaks(self, all_peaks_data: List[pd.DataFrame]) -> pd.DataFrame:
        """阶段2: 共识峰识别"""
        self._update_progress(0.33, "阶段2: 特征选择中...")
        
        # 合并所有峰数据
        all_peaks_df = pd.concat(all_peaks_data, ignore_index=True)
        log_message(f"总计发现 {len(all_peaks_df)} 个峰候选")
        
        # 发现共识峰
        consensus_peaks = self._find_consensus_peaks(all_peaks_df)
        log_message(f"识别出 {len(consensus_peaks)} 个共识特征峰")
        
        # 更新进度到66%
        self._update_progress(0.66, "阶段2: 特征选择完成 (66%)")
        
        return consensus_peaks
    
    def _phase3_build_matrix(self, file_paths: List[str], 
                           consensus_peaks: pd.DataFrame) -> pd.DataFrame:
        """阶段3: 构建特征矩阵"""
        self._update_progress(0.66, "阶段3: 构建特征矩阵...")
        log_message("构建动态归一化特征矩阵...")
        
        # 第一轮: 扫描全局最大强度值
        self._scan_global_max_intensity(file_paths)
        
        # 第二轮: 构建归一化特征矩阵
        feature_matrix = self._build_normalized_matrix(file_paths, consensus_peaks)
        
        return feature_matrix
    
    def _discover_peaks_from_file(self, file_path: str) -> pd.DataFrame:
        """从单个文件中发现峰（复制原有逻辑）"""
        log_message(f"处理文件: {os.path.basename(file_path)}")
        
        try:
            # 读取数据
            raw_data = pd.read_csv(file_path, sep=r'\s+', header=None, names=['mz', 'intensity'])
            
            if raw_data.empty:
                return pd.DataFrame()
            
            # 基本清理
            raw_data = raw_data[raw_data['intensity'] > 0]
            raw_data = raw_data.sort_values('mz').reset_index(drop=True)
            
            # pyOpenMS峰拾取
            spectrum = oms.MSSpectrum()
            mz_array = raw_data['mz'].values.astype(float)
            intensity_array = raw_data['intensity'].values.astype(float)
            spectrum.set_peaks([mz_array, intensity_array])
            spectrum.sortByPosition()
            
            picker = oms.PeakPickerHiRes()
            picker_param = picker.getDefaults()
            picker_param.setValue("signal_to_noise", 1.0)
            picker.setParameters(picker_param)
            
            picked_spectrum = oms.MSSpectrum()
            picker.pick(spectrum, picked_spectrum)
            
            if picked_spectrum.size() == 0:
                log_message("未发现峰", "WARNING")
                return pd.DataFrame()
            
            # 提取峰信息
            peak_mz, peak_intensity = picked_spectrum.get_peaks()
            
            # 构建结果
            file_id = os.path.splitext(os.path.basename(file_path))[0]
            file_class = self._get_file_classification(file_path)
            
            results = pd.DataFrame({
                'mz': peak_mz,
                'intensity': peak_intensity,
                'file_id': file_id,
                'class': file_class
            })
            
            # 缓存结果
            self.all_file_peaks_cache[file_id] = results
            
            return results
            
        except Exception as e:
            log_message(f"处理文件 {file_path} 时出错: {str(e)}", "ERROR")
            return pd.DataFrame()
    
    def _find_consensus_peaks(self, all_peaks_df: pd.DataFrame) -> pd.DataFrame:
        """发现共识峰（复制原有逻辑）"""
        if all_peaks_df.empty:
            return pd.DataFrame()
        
        # 获取动态类别映射
        _, reverse_mapping = get_class_mapping()
        class_0_name, class_1_name = reverse_mapping[0], reverse_mapping[1]
        
        log_message(f"使用类别: {class_0_name}, {class_1_name}")
        
        # 统计信息
        class_0_files = all_peaks_df[all_peaks_df['class'] == class_0_name]['file_id'].nunique()
        class_1_files = all_peaks_df[all_peaks_df['class'] == class_1_name]['file_id'].nunique()
        
        # 按m/z分组分析
        all_peaks_df = all_peaks_df.copy()
        all_peaks_df['mz_group'] = np.round(all_peaks_df['mz'] / 0.2) * 0.2
        
        consensus_peaks = []
        
        for mz_group in all_peaks_df['mz_group'].unique():
            group_data = all_peaks_df[all_peaks_df['mz_group'] == mz_group]
            
            class_0_data = group_data[group_data['class'] == class_0_name]
            class_1_data = group_data[group_data['class'] == class_1_name]
            
            # 计算出现频率
            class_0_file_count = class_0_data['file_id'].nunique() if len(class_0_data) > 0 else 0
            class_1_file_count = class_1_data['file_id'].nunique() if len(class_1_data) > 0 else 0
            
            class_0_occurrence_rate = class_0_file_count / class_0_files if class_0_files > 0 else 0
            class_1_occurrence_rate = class_1_file_count / class_1_files if class_1_files > 0 else 0
            
            # 过滤条件
            if (class_0_occurrence_rate < MIN_OCCURRENCE_RATE or 
                class_1_occurrence_rate < MIN_OCCURRENCE_RATE):
                continue
            
            if len(class_0_data) < 2 or len(class_1_data) < 2:
                continue
            
            # 计算统计指标
            consensus_mz = np.average(group_data['mz'], weights=group_data['intensity'])
            class_0_intensity_mean = class_0_data['intensity'].mean()
            class_1_intensity_mean = class_1_data['intensity'].mean()
            
            # 计算区分性
            fold_change = max(class_0_intensity_mean, class_1_intensity_mean) / (
                min(class_0_intensity_mean, class_1_intensity_mean) + 1e-6)
            
            if fold_change >= MIN_FOLD_CHANGE:
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
            
            # 限制特征数量
            if len(consensus_df) > MAX_FEATURES:
                original_count = len(consensus_df)
                consensus_df = consensus_df.head(MAX_FEATURES)
                log_message(f"从 {original_count} 个候选中选择了top {MAX_FEATURES} 个特征")
        
        return consensus_df
    
    def _scan_global_max_intensity(self, file_paths: List[str]):
        """扫描全局最大强度值"""
        log_message("第一轮：扫描全局最大强度值...")
        self.global_max_intensity = 0.0
        
        for i, file_path in enumerate(file_paths):
            file_id = os.path.splitext(os.path.basename(file_path))[0]
            
            # 使用缓存或重新发现峰
            if file_id in self.all_file_peaks_cache:
                peaks_df = self.all_file_peaks_cache[file_id]
            else:
                peaks_df = self._discover_peaks_from_file(file_path)
            
            if not peaks_df.empty:
                file_max = peaks_df['intensity'].max()
                self.global_max_intensity = max(self.global_max_intensity, file_max)
            
            # 更新进度 (66% - 83%)
            progress = 0.66 + (i + 1) / len(file_paths) * 0.17
            message = f"扫描最大值: {i+1}/{len(file_paths)} ({progress:.0%})"
            self._update_progress(progress, message)
        
        if self.global_max_intensity == 0:
            log_message("警告：未找到任何有效强度值", "WARNING")
            self.global_max_intensity = 1.0
        
        log_message(f"全局最大强度值: {self.global_max_intensity:.2f}")
        save_normalization_factor(self.global_max_intensity)
    
    def _build_normalized_matrix(self, file_paths: List[str], 
                               consensus_peaks: pd.DataFrame) -> pd.DataFrame:
        """构建归一化特征矩阵"""
        log_message("第二轮：构建归一化特征矩阵...")
        
        # 构建基础矩阵结构
        feature_names = ['class'] + [f"{peak['consensus_mz']:.1f}" 
                                   for _, peak in consensus_peaks.iterrows()]
        feature_series = pd.Series(data=feature_names, index=feature_names)
        all_results = pd.DataFrame(feature_series, columns=['m/z'])
        
        for i, file_path in enumerate(file_paths):
            file_id = os.path.splitext(os.path.basename(file_path))[0]
            file_class = self._get_file_classification(file_path)
            
            # 使用缓存的峰数据
            peaks_df = self.all_file_peaks_cache.get(file_id, pd.DataFrame())
            
            # 创建文件结果列
            file_results = [file_class]  # 第一行：类别标签
            
            # 后续行：对每个共识峰提取并归一化特征值
            for _, consensus_peak in consensus_peaks.iterrows():
                target_mz = consensus_peak['consensus_mz']
                normalized_intensity = self._extract_normalized_intensity(
                    peaks_df, target_mz, self.global_max_intensity)
                file_results.append(normalized_intensity)
            
            # 将结果添加到总矩阵中
            file_series = pd.Series(file_results, index=feature_names)
            file_df = pd.DataFrame(file_series, columns=[file_id])
            all_results = pd.concat([all_results, file_df], axis=1)
            
            # 更新进度 (83% - 100%)
            progress = 0.83 + (i + 1) / len(file_paths) * 0.17
            message = f"归一化处理: {i+1}/{len(file_paths)} ({progress:.0%})"
            self._update_progress(progress, message)
        
        log_message(f"动态归一化特征矩阵完成: {all_results.shape}")
        return all_results
    
    def _extract_normalized_intensity(self, peaks_df: pd.DataFrame, 
                                    target_mz: float, 
                                    normalization_factor: float) -> float:
        """提取归一化强度值"""
        if peaks_df.empty:
            return 0.0
        
        # 在容差范围内查找
        mz_diff = np.abs(peaks_df['mz'] - target_mz)
        matches = peaks_df[mz_diff <= MZ_TOLERANCE]
        
        if not matches.empty:
            # 选择最接近的峰
            best_match_idx = mz_diff[mz_diff <= MZ_TOLERANCE].idxmin()
            raw_intensity = peaks_df.loc[best_match_idx, 'intensity']
            return raw_intensity / normalization_factor
        else:
            return 0.0
    
    def _get_file_classification(self, file_path: str) -> str:
        """获取文件分类"""
        classification = data_store.get_file_classification()
        
        if file_path in classification['class_0_files']:
            return classification['class_0_name']
        elif file_path in classification['class_1_files']:
            return classification['class_1_name']
        else:
            return "UNKNOWN"
    
    def _save_results(self, feature_matrix: pd.DataFrame) -> bool:
        """保存结果文件"""
        output_path = OUTPUT_FILES['processed_data']
        
        try:
            # 检查文件是否已存在，创建备份
            if os.path.exists(output_path):
                log_message("发现已存在的文件，正在创建备份...", "INFO")
                backup_path = create_backup_filename(output_path)
                try:
                    os.rename(output_path, backup_path)
                    log_message(f"备份完成: {os.path.abspath(backup_path)}", "SUCCESS")
                except Exception as e:
                    log_message(f"无法重命名已有文件: {str(e)}，将尝试直接保存新文件", "WARNING")
            
            # 保存新文件
            log_message("正在保存处理结果...", "INFO")
            feature_matrix.iloc[:, 1:].to_csv(output_path, index=True, float_format='%.8f')
            log_message(f"数据处理完成，结果已保存为 {os.path.abspath(output_path)}", "SUCCESS")
            return True
            
        except PermissionError:
            log_message("无法保存文件，可能是文件已被打开或没有写入权限", "ERROR")
            return False
        except Exception as e:
            log_message(f"保存文件时出错: {str(e)}", "ERROR")
            return False
    
    def _handle_save_failure(self):
        """处理保存失败的情况"""
        from tkinter import filedialog
        
        response = messagebox.askyesno("权限错误", 
                                     "无法保存文件到当前位置。\n"
                                     "是否选择其他位置保存文件？")
        if response:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile="normalized_ms_data.csv"
            )
            if save_path:
                try:
                    # 这里需要重新获取feature_matrix，简化处理
                    log_message("用户选择了新的保存位置", "INFO")
                    messagebox.showinfo("提示", "请重新运行数据预处理以保存到新位置")
                except Exception as e:
                    log_message(f"保存到新位置时出错: {str(e)}", "ERROR")
                    messagebox.showerror("保存失败", f"保存文件时出错:\n{str(e)}")




# 全局实例和兼容函数
_preprocessor_instance = DataPreprocessor()

def show_data_preprocessing_dialog(root):
    """显示数据预处理对话框（新接口）"""
    _preprocessor_instance.show_classification_dialog(root)

def process_classified_files(root):
    """处理已分类文件（保持兼容的旧接口）"""
    _preprocessor_instance.process_classified_files(root)