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
    MIN_FOLD_CHANGE, get_output_paths
)
import data_store
from data_store import class_manager
from utils import log_message, create_backup_filename, set_window_icon

# 诊断模块导入（可选，如果文件不存在则禁用诊断）
try:
    from consensus_peak_diagnostics import ConsensusPeakDiagnostics, create_diagnostics
    DIAGNOSTICS_AVAILABLE = True
except ImportError:
    DIAGNOSTICS_AVAILABLE = False


class DataPreprocessor:
    """数据预处理器类 - 保持原有接口的简单版本"""
    
    def __init__(self):
        # 初始化缓存和归一化统计学特征
        self.all_file_peaks_cache = {}
        self.normalization_stats = {}

        # GUI组件
        self.root = None
        self.progress_bar = None
        self.progress_label = None
        self.classification_window = None
        
        # 分类数据
        self.class_0_files = []
        self.class_1_files = []

        # 归一化设置默认值
        self.current_normalization_enabled = True
        self.current_normalization_method = 'max'
        
        # 诊断实例
        self.diagnostics = None
        self.enable_diagnostics = True  # 可通过设置禁用

    # 第一部分：类初始化和主流程方法
    def show_classification_dialog(self, parent_root):
        """显示文件分类对话框"""
        self.root = parent_root
        self._create_classification_window()
    
    def process_classified_files(self, root):
        """主处理函数"""
        self.root = root
        classification = data_store.get_file_classification()
        file_paths = classification['class_0_files'] + classification['class_1_files']
        
        if not file_paths:
            log_message("未找到已分类的文件", "WARNING")
            messagebox.showerror("错误", "未找到已分类的文件，请先进行文件分类")
            return
        
        self._execute_processing(file_paths)

    # 第二部分：核心三阶段处理流程
    def _execute_processing(self, file_paths: List[str]):
        """执行数据处理"""
        # 创建进度显示
        self._create_progress_ui()
        
        # 初始化诊断
        if self.enable_diagnostics and DIAGNOSTICS_AVAILABLE:
            self.diagnostics = create_diagnostics()
            self.diagnostics.set_parameters(
                min_occurrence_rate=MIN_OCCURRENCE_RATE,
                min_fold_change=MIN_FOLD_CHANGE,
                mz_tolerance=MZ_TOLERANCE,
                max_features=MAX_FEATURES
            )
            log_message("诊断模式已启用")
        
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
            self._save_and_notify_results(feature_matrix, consensus_peaks, file_paths)
            
            # 生成诊断报告
            self._generate_diagnostics_report()
                
        except Exception as e:
            log_message(f"智能峰发现处理失败: {str(e)}", "ERROR")
            messagebox.showerror("处理错误", f"智能峰发现过程中出现错误：{str(e)}")
        finally:
            self._cleanup_progress_ui()
  
    def _phase1_discover_peaks(self, file_paths: List[str]) -> List[pd.DataFrame]:
        """阶段1: 峰发现 + 归一化"""
        self._update_progress(0, "阶段1: 峰发现和归一化中...")
        
        all_peaks_data = []
        
        # 初始化归一化统计存储
        self.normalization_stats = {}
        
        # 设置类别名称到诊断器（用于分类统计）
        if self.diagnostics:
            self.diagnostics.phase1._class_0_name = class_manager.class_0_name
        
        # 步骤1：峰发现（自动收集统计特征）
        for index, file_path in enumerate(file_paths):
            peaks_df = self._discover_peaks_from_file(file_path)
            file_id = os.path.splitext(os.path.basename(file_path))[0]
            file_class = self._get_file_classification(file_path)
            
            # 收集诊断数据
            if self.diagnostics:
                self.diagnostics.phase1.add_file_result(
                    file_id=file_id,
                    file_class=file_class,
                    peaks_df=peaks_df,
                    success=not peaks_df.empty
                )
            
            if not peaks_df.empty:
                all_peaks_data.append(peaks_df)
                log_message(f"文件 {os.path.basename(file_path)}: 发现 {len(peaks_df)} 个峰")
            
            # 更新进度 (0-25%)
            progress = (index + 1) / len(file_paths) * 0.25
            self._update_progress(progress, f"峰发现: {index+1}/{len(file_paths)}")
        
        # 步骤2：归一化（如果启用）
        if self.current_normalization_enabled and all_peaks_data:
            # 使用本地保存的归一化方法
            norm_method = self.current_normalization_method
            
            # 创建归一化管理器（传入已计算的统计特征）
            norm_manager = NormalizationManager(
                method=norm_method, 
                normalization_stats=self.normalization_stats
            )
            
            # 显示归一化摘要
            log_message(norm_manager.get_normalization_summary())
            
            # 应用归一化 (25-33%)
            self._update_progress(0.25, "应用归一化...")
            for i, peaks_df in enumerate(all_peaks_data):
                all_peaks_data[i] = norm_manager.normalize_sample(peaks_df)
                
                # 【关键修复】更新缓存，确保后续矩阵构建使用归一化数据
                file_id = all_peaks_data[i]['file_id'].iloc[0]
                self.all_file_peaks_cache[file_id] = all_peaks_data[i]
                
                # 更新进度
                progress = 0.25 + (i + 1) / len(all_peaks_data) * 0.08
                self._update_progress(progress, f"归一化: {i+1}/{len(all_peaks_data)}")
            
            log_message(f"归一化完成（方法: {norm_method}）")
        else:
            log_message("未启用归一化，使用原始数据")
        
        return all_peaks_data
    
    def _phase2_consensus_peaks(self, all_peaks_data: List[pd.DataFrame]) -> pd.DataFrame:
        """阶段2: 共识峰识别"""
        self._update_progress(0.33, "阶段2: 特征选择中...")
        
        # 合并所有峰数据
        all_peaks_df = pd.concat(all_peaks_data, ignore_index=True)
        log_message(f"总计发现 {len(all_peaks_df)} 个峰候选")
        self._update_progress(0.40, "阶段2: 数据合并完成")  # 新增
        
        # 获取动态类别映射
        class_0_name, class_1_name = class_manager.names      
        log_message(f"使用类别: {class_0_name}, {class_1_name}")
        
        # 统计信息
        class_0_files = all_peaks_df[all_peaks_df['class'] == class_0_name]['file_id'].nunique()
        class_1_files = all_peaks_df[all_peaks_df['class'] == class_1_name]['file_id'].nunique()
        
        # 按m/z分组分析
        all_peaks_df = all_peaks_df.copy()
        all_peaks_df['mz_group'] = np.round(all_peaks_df['mz'] / 0.2) * 0.2
        self._update_progress(0.45, "阶段2: 数据分组完成")  # 新增
        
        consensus_peaks = []
        unique_groups = all_peaks_df['mz_group'].unique()
        total_groups = len(unique_groups)
        
        # 用于参数敏感性分析的数据收集
        all_groups_data = []
        
        for i, mz_group in enumerate(unique_groups):
            group_data = all_peaks_df[all_peaks_df['mz_group'] == mz_group]
            
            class_0_data = group_data[group_data['class'] == class_0_name]
            class_1_data = group_data[group_data['class'] == class_1_name]
            
            # 计算诊断所需的指标
            class_0_file_count = class_0_data['file_id'].nunique() if len(class_0_data) > 0 else 0
            class_1_file_count = class_1_data['file_id'].nunique() if len(class_1_data) > 0 else 0
            class_0_occurrence = class_0_file_count / class_0_files if class_0_files > 0 else 0
            class_1_occurrence = class_1_file_count / class_1_files if class_1_files > 0 else 0
            class_0_mean = class_0_data['intensity'].mean() if len(class_0_data) > 0 else 0
            class_1_mean = class_1_data['intensity'].mean() if len(class_1_data) > 0 else 0
            fold_change = max(class_0_mean, class_1_mean) / (min(class_0_mean, class_1_mean) + 1e-6)
            
            # 检查是否通过选择标准
            passed = self._passes_selection_criteria(class_0_data, class_1_data, class_0_files, class_1_files)
            
            # 收集诊断数据
            if self.diagnostics:
                self.diagnostics.phase2.record_group_analysis(
                    mz_group=mz_group,
                    class_0_occurrence=class_0_occurrence,
                    class_1_occurrence=class_1_occurrence,
                    class_0_samples=len(class_0_data),
                    class_1_samples=len(class_1_data),
                    fold_change=fold_change,
                    min_occurrence_rate=MIN_OCCURRENCE_RATE,
                    min_fold_change=MIN_FOLD_CHANGE,
                    passed=passed
                )
                # 收集用于敏感性分析的数据
                all_groups_data.append({
                    'class_0_occurrence': class_0_occurrence,
                    'class_1_occurrence': class_1_occurrence,
                    'class_0_samples': len(class_0_data),
                    'class_1_samples': len(class_1_data),
                    'fold_change': fold_change,
                })
            
            if passed:
                peak_info = self._calculate_peak_metrics(group_data, class_0_data, class_1_data, len(consensus_peaks))
                consensus_peaks.append(peak_info)
            
            # 每处理100个分组更新一次进度 (45% - 60%)
            if i % 100 == 0 or i == total_groups - 1:
                progress = 0.45 + (i + 1) / total_groups * 0.15
                self._update_progress(progress, f"阶段2: 分析峰群 {i+1}/{total_groups}")
        
        # 执行参数敏感性分析
        if self.diagnostics and all_groups_data:
            self.diagnostics.phase2.analyze_parameter_sensitivity(
                all_groups_data, MIN_OCCURRENCE_RATE, MIN_FOLD_CHANGE
            )
        
        consensus_df = pd.DataFrame(consensus_peaks)
        
        if not consensus_df.empty:
            # 按ML友好性得分排序
            consensus_df = consensus_df.sort_values('ml_score', ascending=False)
            self._update_progress(0.62, "阶段2: 特征排序完成")  # 新增
            
            # 限制特征数量
            if len(consensus_df) > MAX_FEATURES:
                original_count = len(consensus_df)
                consensus_df = consensus_df.head(MAX_FEATURES)
                log_message(f"从 {original_count} 个候选中选择了top {MAX_FEATURES} 个特征")
        
        log_message(f"识别出 {len(consensus_df)} 个共识特征峰")
        
        # 更新进度到66%
        self._update_progress(0.66, "阶段2: 特征选择完成 (66%)")
        
        return consensus_df
    
    def _phase3_build_matrix(self, file_paths: List[str], consensus_peaks: pd.DataFrame) -> pd.DataFrame:
        """阶段3: 构建特征矩阵"""
        start_progress = 0.66
        progress_range = 0.34
        
        return self._build_unified_matrix(file_paths, consensus_peaks, 
                                        start_progress, progress_range)

    # 第三部分：核心算法方法
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
            
            # 【新增】计算并存储归一化统计特征
            self.normalization_stats[file_id] = {
                'sum': results['intensity'].sum(),
                'median': results['intensity'].median(),
                'max': results['intensity'].max(), 
            }
            
            return results
            
        except Exception as e:
            log_message(f"处理文件 {file_path} 时出错: {str(e)}", "ERROR")
            return pd.DataFrame()

    def _build_unified_matrix(self, file_paths: List[str], consensus_peaks: pd.DataFrame,
                        start_progress: float, progress_range: float) -> pd.DataFrame:
        """统一的特征矩阵构建方法（归一化已在阶段1完成）"""
        
        # 构建基础矩阵结构
        feature_names = ['class'] + [f"{peak['consensus_mz']:.1f}" 
                                for _, peak in consensus_peaks.iterrows()]
        all_results = pd.DataFrame(
            pd.Series(feature_names, index=feature_names), 
            columns=['m/z']
        )
        
        # 处理每个文件
        for i, file_path in enumerate(file_paths):
            file_id = os.path.splitext(os.path.basename(file_path))[0]
            file_class = self._get_file_classification(file_path)
            peaks_df = self.all_file_peaks_cache.get(file_id, pd.DataFrame())
            
            # 提取所有特征值（直接使用，不再归一化）
            file_results = [file_class] + [
                self._extract_intensity(peaks_df, peak['consensus_mz'])
                for _, peak in consensus_peaks.iterrows()
            ]
            
            # 添加到矩阵
            file_series = pd.Series(file_results, index=feature_names)
            file_df = pd.DataFrame(file_series, columns=[file_id])
            all_results = pd.concat([all_results, file_df], axis=1)
            
            # 动态进度更新
            progress = start_progress + (i + 1) / len(file_paths) * progress_range
            self._update_progress(progress, f"构建矩阵: {i+1}/{len(file_paths)}")
        
        return all_results
        
    def _extract_intensity(self, peaks_df: pd.DataFrame, target_mz: float) -> float:
        """提取强度值（数据已在阶段1归一化）"""
        if peaks_df.empty:
            return 0.0
        
        # 在容差范围内查找
        mz_diff = np.abs(peaks_df['mz'] - target_mz)
        matches = peaks_df[mz_diff <= MZ_TOLERANCE]
        
        if not matches.empty:
            # 选择最接近的峰
            best_match_idx = mz_diff[mz_diff <= MZ_TOLERANCE].idxmin()
            return peaks_df.loc[best_match_idx, 'intensity']
        else:
            return 0.0
            
    def _passes_selection_criteria(self, class_0_data, class_1_data, 
                             class_0_files, class_1_files) -> bool:
        """检查峰是否通过选择标准"""
        # 计算出现频率
        class_0_file_count = class_0_data['file_id'].nunique() if len(class_0_data) > 0 else 0
        class_1_file_count = class_1_data['file_id'].nunique() if len(class_1_data) > 0 else 0
        
        class_0_occurrence_rate = class_0_file_count / class_0_files if class_0_files > 0 else 0
        class_1_occurrence_rate = class_1_file_count / class_1_files if class_1_files > 0 else 0
        
        # 修改：至少在一个类别中满足最小出现频率（改为OR逻辑）
        if not (class_0_occurrence_rate >= MIN_OCCURRENCE_RATE or 
                class_1_occurrence_rate >= MIN_OCCURRENCE_RATE):
            return False
        
        # 检查最小样本数 - 也需要改为OR逻辑
        if len(class_0_data) < 2 and len(class_1_data) < 2:
            return False
        
        # 检查折叠变化（保持不变）
        class_0_mean = class_0_data['intensity'].mean() if len(class_0_data) > 0 else 0
        class_1_mean = class_1_data['intensity'].mean() if len(class_1_data) > 0 else 0
        fold_change = max(class_0_mean, class_1_mean) / (min(class_0_mean, class_1_mean) + 1e-6)
        
        return fold_change >= MIN_FOLD_CHANGE
    
    def _calculate_peak_metrics(self, group_data, class_0_data, class_1_data, peak_index) -> dict:
        """计算峰的统计指标"""
        consensus_mz = np.average(group_data['mz'], weights=group_data['intensity'])
        class_0_mean = class_0_data['intensity'].mean()
        class_1_mean = class_1_data['intensity'].mean()
        
        fold_change = max(class_0_mean, class_1_mean) / (min(class_0_mean, class_1_mean) + 1e-6)
        
        # 简化出现频率计算
        class_0_occurrence = class_0_data['file_id'].nunique() / data_store.get_file_classification()['class_0_files'].__len__()
        class_1_occurrence = class_1_data['file_id'].nunique() / data_store.get_file_classification()['class_1_files'].__len__()
        
        coverage_score = (class_0_occurrence + class_1_occurrence) / 2
        ml_score = fold_change * coverage_score
        
        return {
            'consensus_mz': consensus_mz,
            'peak_id': f'Peak_{peak_index:03d}',
            'class_0_occurrence_rate': class_0_occurrence,
            'class_1_occurrence_rate': class_1_occurrence,
            'class_0_mean': class_0_mean,
            'class_1_mean': class_1_mean,
            'fold_change': fold_change,
            'ml_score': ml_score
        }

    # 第四部分：数据处理和保存
    def _generate_diagnostics_report(self):
        """生成诊断报告"""
        if not self.diagnostics:
            return
        
        try:
            # 生成完整报告
            report = self.diagnostics.generate_report()
            
            # 输出到日志
            log_message("=" * 50)
            log_message("共识峰识别诊断报告")
            log_message("=" * 50)
            
            # 分行输出报告
            for line in report.split('\n'):
                if line.strip():
                    log_message(line)
            
            # 获取快速统计
            quick_stats = self.diagnostics.get_quick_stats()
            
            # 保存报告到文件
            report_path = os.path.join(
                os.path.dirname(get_output_paths()['processed_data']),
                'diagnostics_report.txt'
            )
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            log_message(f"诊断报告已保存: {report_path}")
            
            # 如果共识峰数量异常少，显示警告
            if quick_stats['consensus_peaks'] < 20:
                log_message(f"⚠️ 警告: 共识峰数量较少 ({quick_stats['consensus_peaks']})", "WARNING")
                log_message(f"   主要瓶颈: {quick_stats['bottleneck']}", "WARNING")
            
        except Exception as e:
            log_message(f"生成诊断报告时出错: {str(e)}", "WARNING")
    
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
        # 动态获取当前的输出路径
        current_paths = get_output_paths()
        base_path = current_paths['processed_data']
        
        # 根据归一化方法添加后缀
        if self.current_normalization_enabled:
            # 在文件名后面添加归一化方法标识
            path_parts = os.path.splitext(base_path)
            output_path = f"{path_parts[0]}_{self.current_normalization_method}{path_parts[1]}"
        else:
            output_path = base_path
        
        try:
            # 检查当前要保存的文件是否已存在（而不是检查固定的normalized文件）
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
            feature_matrix.iloc[:, 1:].to_csv(
                output_path, 
                index=True, 
                float_format='%.8f',
                encoding='utf-8-sig'
            )
            
            # 获取归一化状态用于日志
            norm_status = f"已归一化({self.current_normalization_method})" if self.current_normalization_enabled else "原始数据"
            log_message(f"数据处理完成，{norm_status}结果已保存为 {os.path.abspath(output_path)}", "SUCCESS")
            return True
            
        except PermissionError:
            log_message("无法保存文件，可能是文件已被打开或没有写入权限", "ERROR")
            return False
        except Exception as e:
            log_message(f"保存文件时出错: {str(e)}", "ERROR")
            return False

    def _save_and_notify_results(self, feature_matrix, consensus_peaks, file_paths):
        """保存结果并显示通知"""
        success = self._save_results(feature_matrix)
        
        if success:
            current_paths = get_output_paths()
            norm_status = f"已归一化({self.current_normalization_method})" if self.current_normalization_enabled else "未归一化"
            log_message("智能峰发现处理完成！", "SUCCESS")
            messagebox.showinfo("处理完成", 
                            f"智能峰发现完成！\n"
                            f"• 发现 {len(consensus_peaks)} 个特征峰\n"
                            f"• 处理 {len(file_paths)} 个样本\n"
                            f"• 数据状态: {norm_status}\n"
                            f"• 结果已保存为 {os.path.basename(current_paths['processed_data'])}")
        else:
            self._handle_save_failure()
            
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


    # 第五部分：GUI相关方法
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

        # 窗口焦点设置
        self.classification_window.transient(self.root)
        self.classification_window.focus_force()
        self.classification_window.lift()
        self.classification_window.grab_set()
        
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
        
        ctk.CTkLabel(name_frame, text="基础设置", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=5)
        
        ctk.CTkLabel(name_frame, text="类别名称（可自定义）:", 
            font=ctk.CTkFont(size=10), text_color="gray").pack(anchor='w', padx=10, pady=(0, 2))

        name_input_frame = ctk.CTkFrame(name_frame, fg_color="transparent")
        name_input_frame.pack(fill='x', padx=10, pady=5)
        
       # 类别名称输入框 - 从 class_manager 读取真实值
        class_0_name_var = ctk.StringVar(value=class_manager.class_0_name)
        class_1_name_var = ctk.StringVar(value=class_manager.class_1_name)

        ctk.CTkLabel(name_input_frame, text="类别0:").pack(side='left', padx=5)
        class_0_entry = ctk.CTkEntry(name_input_frame, textvariable=class_0_name_var, width=120)
        class_0_entry.pack(side='left', padx=5)

        ctk.CTkLabel(name_input_frame, text="类别1:").pack(side='left', padx=(20, 5))
        class_1_entry = ctk.CTkEntry(name_input_frame, textvariable=class_1_name_var, width=120)
        class_1_entry.pack(side='left', padx=5)

        ctk.CTkLabel(name_input_frame, text="|", text_color="gray").pack(side='left', padx=10)

        # 归一化设置（第三列）
        ctk.CTkLabel(name_input_frame, text="归一化:").pack(side='left', padx=(20, 5))
        self.normalization_method_var = ctk.StringVar(value="max (最大峰)")
        self.normalization_method_combobox = ctk.CTkComboBox(
            name_input_frame,
            values=["不归一化", "sum (总和)", "median (中位数)", "max (最大峰)"],
            variable=self.normalization_method_var,
            state="readonly",
            width=150
        )
        self.normalization_method_combobox.pack(side='left', padx=5)
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
        
        # 保存预览文本框的引用
        self.preview_text_widget = preview_text
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
        folder_path = filedialog.askdirectory(
            title=f"选择类别{class_index}文件夹",
            parent=self.classification_window
        )
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
    
    def _create_normalization_settings_ui(self):
        """创建归一化设置UI"""
        norm_frame = ctk.CTkFrame(self.classification_window)
        norm_frame.pack(fill='x', padx=20, pady=10)
        
        ctk.CTkLabel(norm_frame, text="归一化设置:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=5)
        
        # 归一化方法选择（包含"不归一化"选项）
        method_frame = ctk.CTkFrame(norm_frame, fg_color="transparent")
        method_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(method_frame, text="归一化方法:").pack(side='left', padx=5)
        
        self.normalization_method_var = ctk.StringVar(value="max (最大峰)")
        self.normalization_method_combobox = ctk.CTkComboBox(
            method_frame,
            values=["不归一化", "sum (总和)", "median (中位数)", "max (最大峰)"],
            variable=self.normalization_method_var,
            state="readonly",
            width=150
        )
        self.normalization_method_combobox.pack(side='left', padx=5)
        
        # 说明文本
        info_frame = ctk.CTkFrame(norm_frame, fg_color="transparent")
        info_frame.pack(fill='x', padx=10, pady=5)
        
        info_text = ctk.CTkLabel(
            info_frame,
            text="💡 归一化会在峰发现阶段对每个样本单独应用",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        info_text.pack(anchor='w', padx=5)
        
    def _update_preview(self, preview_text, class_0_name_var, class_1_name_var):
        """更新预览信息"""
        # 使用保存的引用或传入的参数
        if preview_text is None:
            preview_text = getattr(self, 'preview_text_widget', None)
        
        # 检查widget是否有效
        if preview_text is None:
            return
            
        try:
            # 检查widget是否仍然存在
            if not preview_text.winfo_exists():
                return
        except:
            return
        
        try:
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
                
        except Exception:
            # 静默处理错误，避免崩溃
            pass 
        
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
        
        # 在开始实际处理前，重新设置按钮状态
        if self.root and hasattr(self.root, 'gui_manager'):
            self.root.gui_manager._set_operation_running(True, "数据预处理", allow_termination=False)
        
        # 解析归一化设置
        selected_method = self.normalization_method_var.get()
        if selected_method == "不归一化":
            self.current_normalization_enabled = False
            self.current_normalization_method = None
            log_message("归一化设置: 不归一化")
        else:
            self.current_normalization_enabled = True
            method_map = {
                "sum (总和)": "sum",
                "median (中位数)": "median",
                "max (最大峰)": "max"
            }
            self.current_normalization_method = method_map.get(selected_method, "sum")
            log_message(f"归一化设置: 方法={self.current_normalization_method}")
        
        # 从输入框获取类别名称，直接设置到 class_manager
        c0_name = class_0_name_var.get()
        c1_name = class_1_name_var.get()
        class_manager.set_names(c0_name, c1_name)

        # 保存分类信息到 data_store（class_manager 已同步更新 _file_classification）
        classification_data = {
            'class_0_name': c0_name,
            'class_1_name': c1_name,
            'class_0_files': self.class_0_files,
            'class_1_files': self.class_1_files
        }
        data_store.set_file_classification(classification_data)
        
        log_message(f"文件分类完成: {c0_name}({len(self.class_0_files)}个), {c1_name}({len(self.class_1_files)}个)")
        
        # 关闭分类窗口
        self.classification_window.grab_release()
        self.classification_window.destroy()
        self.classification_window = None
        
        # 直接开始处理
        file_paths = self.class_0_files + self.class_1_files
        self._execute_processing(file_paths)


    def _create_progress_ui(self):
        """创建进度显示界面"""
        if self.root and hasattr(self.root, 'gui_manager'):
            self.root.gui_manager.show_global_progress("开始智能峰发现处理...")
    
    def _cleanup_progress_ui(self):
        """清理进度显示界面 - 隐藏全局进度条"""  
        if self.root and hasattr(self.root, 'gui_manager'):
            self.root.gui_manager.hide_global_progress()
            self.root.gui_manager._set_operation_running(False)
        
    def _update_progress(self, progress: float, message: str):
        """更新进度显示"""
        if self.root and hasattr(self.root, 'gui_manager'):
            # 使用全局进度条
            self.root.gui_manager.update_global_progress(progress, message)
        
        if self.root:
            self.root.update()
  
class NormalizationManager:
    """归一化管理器 - 使用预计算的统计特征"""
    
    def __init__(self, method='sum', normalization_stats=None):
        """
        Parameters:
        - method: 'sum' 或 'median'
        - normalization_stats: 从DataPreprocessor传入的统计特征字典
        """
        if method not in ['sum', 'median', 'max']:
            raise ValueError(f"不支持的归一化方法: {method}，仅支持 'sum'、'median' 和 'max'")
        
        self.method = method
        self.normalization_stats = normalization_stats or {}
    
    def normalize_sample(self, peaks_df: pd.DataFrame) -> pd.DataFrame:
        """
        对单个样本进行归一化
        
        Parameters:
        - peaks_df: 单个样本的峰数据
        
        Returns:
        - 归一化后的峰数据（新的DataFrame）
        """
        if peaks_df.empty:
            return peaks_df
        
        # 获取样本ID
        file_id = peaks_df['file_id'].iloc[0]
        
        # 检查是否有该样本的统计数据
        if file_id not in self.normalization_stats:
            log_message(f"警告：未找到样本 {file_id} 的统计数据，跳过归一化", "WARNING")
            return peaks_df
        
        # 获取归一化因子
        norm_factor = self.normalization_stats[file_id][self.method]
        
        # 避免除以0
        if norm_factor == 0 or np.isnan(norm_factor):
            log_message(f"警告：样本 {file_id} 的归一化因子无效（{norm_factor}），跳过归一化", "WARNING")
            return peaks_df
        
        # 复制并归一化
        normalized_df = peaks_df.copy()
        normalized_df['intensity'] = normalized_df['intensity'] / norm_factor
        
        return normalized_df
    
    def get_normalization_summary(self) -> str:
        """获取归一化摘要信息"""
        if not self.normalization_stats:
            return "无归一化统计数据"
        
        factors = [stats[self.method] for stats in self.normalization_stats.values()]
        
        # 根据不同方法显示不同的描述
        method_desc = {
            'sum': '总离子流(TIC)',
            'median': '中位数强度',
            'max': '最大峰强度'
        }
        desc = method_desc.get(self.method, self.method)
        
        return (f"归一化方法: {self.method}\n"
                f"样本数量: {len(self.normalization_stats)}\n"
                f"样本{desc}范围: {min(factors):.2f} - {max(factors):.2f}\n"
                f"样本{desc}中位数: {np.median(factors):.2f}")