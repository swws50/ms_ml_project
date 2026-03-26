# visualization.py - 重构版（保持原有函数名，可直接替换）
# 核心改进：使用 MetricsCalculator 统一管理所有指标计算
# 图表管理：采用 latest + archive 模式

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from scipy import stats
from dataclasses import dataclass
from typing import Dict, Optional
import os
from datetime import datetime

# ============================================================================
# 核心数据类：统一管理所有评估指标
# ============================================================================

@dataclass
class MetricStats:
    """单个指标的统计信息"""
    name: str
    data: np.ndarray
    mean: float = 0
    std: float = 0
    ci_lower: float = 0
    ci_upper: float = 0
    ci_margin: float = 0
    cv: float = 0
    min_val: float = 0
    max_val: float = 0
    range_val: float = 0
    
    def __post_init__(self):
        """自动计算所有统计量"""
        if self.data is not None and len(self.data) > 0:
            self.mean = np.mean(self.data)
            self.std = np.std(self.data)
            self.min_val = np.min(self.data)
            self.max_val = np.max(self.data)
            self.range_val = self.max_val - self.min_val
            self.cv = self.std / (self.mean + 1e-10)
            
            # 计算95%置信区间
            n = len(self.data)
            std_err = stats.sem(self.data)
            ci = stats.t.interval(0.95, n-1, loc=self.mean, scale=std_err)
            self.ci_lower = ci[0]
            self.ci_upper = ci[1]
            self.ci_margin = ci[1] - self.mean


class MetricsCalculator:
    """指标计算器 - 统一计算和管理所有性能指标"""
    
    def __init__(self, confusion_matrices: np.ndarray, 
                 f_scores: np.ndarray,
                 test_accuracy: np.ndarray,
                 auc_list: np.ndarray,
                 train_accuracy: Optional[np.ndarray] = None):
        self.confusion_matrices = confusion_matrices
        self.f_scores = f_scores
        self.test_accuracy = test_accuracy
        self.auc_list = auc_list
        self.train_accuracy = train_accuracy
        
        self.metrics: Dict[str, MetricStats] = {}
        self._calculate_all_metrics()
    
    def _calculate_all_metrics(self):
        """一次性计算所有性能指标"""
        # 从混淆矩阵提取
        TNs = self.confusion_matrices[:, 0]
        FPs = self.confusion_matrices[:, 1]
        FNs = self.confusion_matrices[:, 2]
        TPs = self.confusion_matrices[:, 3]
        
        # 计算各项指标
        sensitivity_arr = TPs / (TPs + FNs + 1e-10)
        specificity_arr = TNs / (TNs + FPs + 1e-10)
        precision_arr = self.f_scores[:, 0]
        npv_arr = TNs / (TNs + FNs + 1e-10)
        f1_arr = self.f_scores[:, 2]
        recall_arr = self.f_scores[:, 1]
        accuracy_arr = (TPs + TNs) / (TPs + TNs + FPs + FNs + 1e-10)
        
        # 计算MCC
        numerator = (TPs * TNs) - (FPs * FNs)
        denominator = np.sqrt((TPs + FPs) * (TPs + FNs) * (TNs + FPs) * (TNs + FNs))
        mcc_arr = numerator / (denominator + 1e-10)
        
        # 存储所有指标
        self.metrics['Sensitivity'] = MetricStats('Sensitivity (TPR)', sensitivity_arr)
        self.metrics['Specificity'] = MetricStats('Specificity (TNR)', specificity_arr)
        self.metrics['Precision'] = MetricStats('Precision (PPV)', precision_arr)
        self.metrics['NPV'] = MetricStats('NPV', npv_arr)
        self.metrics['Recall'] = MetricStats('Recall', recall_arr)
        self.metrics['F1'] = MetricStats('F1-Score', f1_arr)
        self.metrics['MCC'] = MetricStats('MCC', mcc_arr)
        self.metrics['Accuracy'] = MetricStats('Accuracy', accuracy_arr)
        self.metrics['BalancedAcc'] = MetricStats('Balanced Accuracy', self.test_accuracy)
        self.metrics['AUC'] = MetricStats('AUC-ROC', self.auc_list)
        
        if self.train_accuracy is not None:
            self.metrics['TrainAcc'] = MetricStats('Training Accuracy', self.train_accuracy)
    
    def get_metric(self, name: str) -> MetricStats:
        """获取指定指标"""
        return self.metrics.get(name)


# ============================================================================
# 原有函数名 - 重构后的实现
# ============================================================================

def generate_class_performance_chart(confusion_matrices, f_scores, model_type="Model",
                                    show_ci=True, confidence=0.95):
    """
    生成类别性能图表：Sensitivity, Specificity, Precision
    
    参数：
        confusion_matrices: 混淆矩阵 (100x4) [TN, FP, FN, TP]
        f_scores: 精确率/召回率/F1 (100x3)
        model_type: 模型类型名称
        show_ci: 是否显示置信区间（默认True）
        confidence: 置信水平（默认0.95）
    """
    from config import get_output_paths
    from utils import log_message
    
    OUTPUT_FILES = get_output_paths()

    # 使用MetricsCalculator统一计算
    metrics_calc = MetricsCalculator(confusion_matrices, f_scores, 
                                     np.zeros(len(confusion_matrices)), 
                                     np.zeros(len(confusion_matrices)))
    
    # 设置论文风格
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial']
    
    # 从MetricsCalculator获取指标
    sensitivity = metrics_calc.get_metric('Sensitivity')
    specificity = metrics_calc.get_metric('Specificity')
    precision = metrics_calc.get_metric('Precision')
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(8, 5))
    
    metrics_list = [sensitivity, specificity, precision]
    data_list = [m.data for m in metrics_list]
    labels = ['Sensitivity\n(TPR)', 'Specificity\n(TNR)', 'Precision\n(PPV)']
    
    # 绘制小提琴图
    parts = ax.violinplot(data_list, positions=[1, 2, 3], widths=0.6,
                          showmeans=True, showmedians=False, showextrema=True)
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.8)
        pc.set_edgecolor('black')
        pc.set_linewidth(0.5)
    
    parts['cmeans'].set_color('red')
    parts['cmeans'].set_linewidth(1.5)
    parts['cbars'].set_color('black')
    parts['cbars'].set_linewidth(0.8)
    parts['cmaxes'].set_color('black')
    parts['cmaxes'].set_linewidth(0.8)
    parts['cmins'].set_color('black')
    parts['cmins'].set_linewidth(0.8)
    
    # 添加统计信息
    for i, metric in enumerate(metrics_list):
        if show_ci:
            ax.text(i+1, 1.02, f'{metric.mean:.3f}±{metric.ci_margin:.3f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
            ax.text(i+1, 0.985, f'95%CI: [{metric.ci_lower:.3f}, {metric.ci_upper:.3f}]',
                    ha='center', va='top', fontsize=8, style='italic', color='gray')
        else:
            ax.text(i+1, 1.02, f'{metric.mean:.3f}±{metric.std:.3f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    
    title = f'Class-wise Performance ({model_type})'
    if show_ci:
        title += ' - 95% CI'
    ax.set_title(title, fontsize=13, fontweight='bold', pad=20)
    
    ax.set_ylim(0.6, 1.08 if show_ci else 1.05)
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    
    ax.axhline(y=0.9, color='green', linestyle=':', alpha=0.4, linewidth=1)
    ax.axhline(y=0.8, color='orange', linestyle=':', alpha=0.4, linewidth=1)
    
    legend_elements = [
        Patch(facecolor=colors[0], alpha=0.8, label='Sensitivity'),
        Patch(facecolor=colors[1], alpha=0.8, label='Specificity'),
        Patch(facecolor=colors[2], alpha=0.8, label='Precision')
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=10, framealpha=0.9)
    
    plt.tight_layout()
    
    # 使用固定文件名（不带时间戳）
    chart_path = OUTPUT_FILES['chart_accuracy']
    plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    log_message(f"ClassPerformance.png 已生成")
    return str(chart_path)


def generate_balance_metrics_chart(confusion_matrices, f_scores, model_type="Model",
                                   show_ci=True, confidence=0.95):
    """
    生成综合平衡指标图表：F1-Score, MCC
    
    参数：
        confusion_matrices: 混淆矩阵 (100x4) [TN, FP, FN, TP]
        f_scores: 精确率/召回率/F1 (100x3)
        model_type: 模型类型名称
        show_ci: 是否显示置信区间（默认True）
        confidence: 置信水平（默认0.95）
    """
    from config import get_output_paths
    from utils import log_message
    
    OUTPUT_FILES = get_output_paths()

    # 使用MetricsCalculator统一计算
    metrics_calc = MetricsCalculator(confusion_matrices, f_scores,
                                     np.zeros(len(confusion_matrices)),
                                     np.zeros(len(confusion_matrices)))
    
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial']
    
    f1 = metrics_calc.get_metric('F1')
    mcc = metrics_calc.get_metric('MCC')
    
    fig, ax = plt.subplots(figsize=(7, 5))
    
    metrics_list = [f1, mcc]
    data_list = [m.data for m in metrics_list]
    labels = ['F1-Score', 'MCC']
    
    parts = ax.violinplot(data_list, positions=[1, 2], widths=0.5,
                          showmeans=True, showmedians=False, showextrema=True)
    
    colors = ['#9467bd', '#e377c2']
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.8)
        pc.set_edgecolor('black')
        pc.set_linewidth(0.5)
    
    parts['cmeans'].set_color('red')
    parts['cmeans'].set_linewidth(1.5)
    parts['cbars'].set_color('black')
    parts['cbars'].set_linewidth(0.8)
    parts['cmaxes'].set_color('black')
    parts['cmaxes'].set_linewidth(0.8)
    parts['cmins'].set_color('black')
    parts['cmins'].set_linewidth(0.8)
    
    for i, metric in enumerate(metrics_list):
        if show_ci:
            ax.text(i+1, 1.02, f'{metric.mean:.3f}±{metric.ci_margin:.3f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
            ax.text(i+1, 0.985, f'95%CI: [{metric.ci_lower:.3f}, {metric.ci_upper:.3f}]',
                    ha='center', va='top', fontsize=8, style='italic', color='gray')
            ax.text(i+1, 0.58, f'CV={metric.cv:.3f}',
                    ha='center', va='top', fontsize=9, style='italic', color='darkgray')
        else:
            ax.text(i+1, 1.02, f'{metric.mean:.3f}±{metric.std:.3f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
            ax.text(i+1, 0.58, f'CV={metric.cv:.3f}',
                    ha='center', va='top', fontsize=9, style='italic', color='gray')
    
    ax.set_xticks([1, 2])
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    
    title = f'Balance Metrics ({model_type})'
    if show_ci:
        title += ' - 95% CI'
    ax.set_title(title, fontsize=13, fontweight='bold', pad=20)
    
    ax.set_ylim(0.6, 1.08 if show_ci else 1.05)
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    
    ax.axhline(y=0.9, color='green', linestyle=':', alpha=0.4, linewidth=1)
    ax.axhline(y=0.8, color='orange', linestyle=':', alpha=0.4, linewidth=1)
    
    ax.text(1.5, 0.62, 'F1: Harmonic mean of Precision and Recall\nMCC: Correlation coefficient (-1 to +1)',
            ha='center', va='bottom', fontsize=8, style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    
    # 使用固定文件名
    chart_path = OUTPUT_FILES['chart_metrics']
    plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    log_message(f"BalanceMetrics.png 已生成")
    return str(chart_path)


def generate_confusion_matrix_with_stability(confusion_matrices, model_type="Model"):
    """
    论文标准版混淆矩阵
    """
    from config import get_output_paths
    from utils import log_message
    
    OUTPUT_FILES = get_output_paths()
    
    mean_cm = confusion_matrices.mean(axis=0).reshape((2, 2))
    std_cm = confusion_matrices.std(axis=0).reshape((2, 2))
    
    row_sums = mean_cm.sum(axis=1, keepdims=True)
    cm_percent = (mean_cm / row_sums) * 100
    
    fig, ax = plt.subplots(figsize=(8, 6.5))
    
    im = ax.imshow(mean_cm, interpolation='nearest', cmap='Blues',
                   vmin=0, vmax=mean_cm.max() * 1.05)
    
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel('Mean Count', rotation=-90, va="bottom", 
                       fontsize=11, fontfamily='sans-serif')
    cbar.ax.tick_params(labelsize=10)
    
    # 获取类别名称并判断是否使用实际标签
    from data_store import class_manager
    class_0_name, class_1_name = class_manager.names
    
    # 检查类别名称是否为英文或数字（ASCII可打印字符）
    def is_ascii_safe(text):
        if not text:
            return False
        return all(c.isascii() and (c.isalnum() or c in ' _-') for c in text)
    
    use_actual_labels = is_ascii_safe(class_0_name) and is_ascii_safe(class_1_name)

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    
    if use_actual_labels:
        ax.set_xticklabels([f'{class_0_name}', f'{class_1_name}'], 
                           fontsize=15, fontfamily='sans-serif')
        ax.set_yticklabels([f'{class_0_name}', f'{class_1_name}'], 
                           fontsize=15, fontfamily='sans-serif')
    else:
        ax.set_xticklabels(['Negative (0)', 'Positive (1)'], 
                           fontsize=10, fontfamily='sans-serif')
        ax.set_yticklabels(['Negative (0)', 'Positive (1)'], 
                           fontsize=10, fontfamily='sans-serif')
    
    # 添加单元格内容
    for i in range(2):
        for j in range(2):
            mean_val = mean_cm[i, j]
            std_val = std_cm[i, j]
            percent = cm_percent[i, j]
            
            flat_idx = i * 2 + j
            cell_data = confusion_matrices[:, flat_idx]
            
            data_range = np.ptp(cell_data)
            cv_val = std_val / (mean_val + 1e-10)
            
            # 智能稳定性指标选择
            if mean_val < 20:
                stability_metric = f'Range: {data_range:.1f}'
            else:
                stability_metric = f'CV: {cv_val:.3f}'
            
            # 文本颜色
            text_color = 'white' if mean_val > mean_cm.max() / 2 else 'black'
            
            # 主文本：百分比
            ax.text(j, i - 0.25, f'{percent:.1f}%',
                   ha='center', va='center', color=text_color,
                   fontsize=16, fontweight='bold', fontfamily='sans-serif')
            
            # 副文本：均值±标准差
            ax.text(j, i + 0.05, f'{mean_val:.1f}±{std_val:.1f}',
                   ha='center', va='center', color=text_color,
                   fontsize=11, fontfamily='sans-serif')
            
            # 底部文本：稳定性指标
            ax.text(j, i + 0.25, stability_metric,
                   ha='center', va='center', color=text_color,
                   fontsize=9, style='italic', fontfamily='sans-serif')
    
    ax.set_xlabel('Predicted Label', fontsize=11, fontweight='bold', fontfamily='sans-serif')
    ax.set_ylabel('True Label', fontsize=11, fontweight='bold', fontfamily='sans-serif')
    ax.set_title(f'Confusion Matrix ({model_type}) - Mean ± SD', 
                fontsize=12, fontweight='bold', pad=15, fontfamily='sans-serif')
    
    plt.tight_layout()
    
    # 使用固定文件名
    chart_path = OUTPUT_FILES['chart_confusion']
    plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    log_message(f"ConfusionMatrix.png 已生成")
    return str(chart_path)


def generate_performance_charts(train_accuracy, test_accuracy,
                               f_scores, confusion_matrices, fpr_values, tpr_values,
                               auc_list, thresholds_used=None):
    """生成所有性能评估图表，保存至 charts/{model_stem}/ 专属目录，返回路径 dict。"""
    from utils import log_message
    from config import get_output_paths
    from output_manager import output_manager
    import data_store
    from data_store import class_manager

    log_message("开始生成可视化图表...")
    generated_charts = {}
    OUTPUT_FILES = get_output_paths()
    
    latest_model, _ = data_store.get_latest_trained_model()
    model_type = latest_model.__class__.__name__ if latest_model else "Model"
    
    # ========== 核心改进：创建MetricsCalculator ==========
    metrics_calc = MetricsCalculator(
        confusion_matrices=confusion_matrices,
        f_scores=f_scores,
        test_accuracy=test_accuracy,
        auc_list=auc_list,
        train_accuracy=train_accuracy
    )
    
    try:
        # 1. 生成类别性能图表
        chart_path = generate_class_performance_chart(
            confusion_matrices, f_scores, model_type,
            show_ci=True, confidence=0.95
        )
        generated_charts['chart_accuracy'] = chart_path

        # 2. 生成综合平衡指标图表
        chart_path = generate_balance_metrics_chart(
            confusion_matrices, f_scores, model_type,
            show_ci=True, confidence=0.95
        )
        generated_charts['chart_metrics'] = chart_path

        # 3. 生成混淆矩阵
        chart_path = generate_confusion_matrix_with_stability(confusion_matrices, model_type)
        generated_charts['chart_confusion'] = chart_path

        # 4. 生成ROC曲线
        plt.figure(figsize=(6, 4))
        mean_fpr = np.linspace(0, 1, 200)
        mean_tpr = np.mean([np.interp(mean_fpr, fpr, tpr)
                            for fpr, tpr in zip(fpr_values, tpr_values)], axis=0)
        auc_metric = metrics_calc.get_metric('AUC')
        plt.plot(mean_fpr, mean_tpr, color='red', lw=3,
                 label=f'Mean ROC (AUC={auc_metric.mean:.3f}±{auc_metric.ci_margin:.3f})')
        plt.plot([0, 1], [0, 1], color='gray', linestyle='--')
        plt.xlabel('False Positive Rate', fontsize=11)
        plt.ylabel('True Positive Rate', fontsize=11)
        plt.title(f'ROC Curve ({model_type})', fontsize=12, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(alpha=0.3)
        plt.savefig(OUTPUT_FILES['chart_roc'], dpi=150, bbox_inches='tight')
        plt.close()
        generated_charts['chart_roc'] = str(OUTPUT_FILES['chart_roc'])
        log_message("ROC_Curve.png 已生成")

        # 5. 生成性能指标表格（CSV）
        import csv
        label_overrides = {
            'Sensitivity (TPR)': f'Sensitivity – {class_manager.class_1_name}',
            'Specificity (TNR)': f'Specificity – {class_manager.class_0_name}',
        }
        csv_path = str(OUTPUT_FILES['chart_metrics_table'])
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value', '±CI', '95% CI Range'])
            for name in ['Sensitivity', 'Specificity', 'Precision', 'NPV',
                         'Accuracy', 'BalancedAcc', 'F1', 'AUC']:
                metric = metrics_calc.get_metric(name)
                if metric is None:
                    continue
                writer.writerow([
                    label_overrides.get(metric.name, metric.name),
                    f'{metric.mean:.3f}',
                    f'±{metric.ci_margin:.3f}',
                    f'[{metric.ci_lower:.3f}, {metric.ci_upper:.3f}]'
                ])
        generated_charts['chart_metrics_table'] = csv_path
        log_message("MetricsTable.csv 已生成")

        # 6. 生成PLS阈值分布图（仅 PLS 模型）
        if thresholds_used is not None and len(thresholds_used) > 0:
            mean_threshold = np.mean(thresholds_used)
            std_threshold  = np.std(thresholds_used)
            plt.figure(figsize=(6, 4))
            hist_data = plt.hist(thresholds_used, bins=20, color='skyblue',
                                 edgecolor='black', alpha=0.7)
            y_max = max(hist_data[0]) * 1.1 if isinstance(hist_data, tuple) else plt.ylim()[1] * 1.1
            plt.axvline(x=mean_threshold, color='r', linestyle='--', linewidth=2,
                        label=f'Mean Threshold: {mean_threshold:.4f}')
            plt.axvline(x=0.5, color='g', linestyle='--', linewidth=2,
                        label='Default Threshold: 0.5')
            plt.xlabel('Threshold Value', fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            plt.legend(loc='upper right', fontsize=10)
            plt.title(f'PLS-DA Optimal Threshold Distribution\n'
                      f'(Mean={mean_threshold:.4f}, Std={std_threshold:.4f})', fontsize=12)
            plt.ylim(0, y_max)
            plt.tight_layout()
            plt.savefig(OUTPUT_FILES['chart_thresholds'], dpi=100, bbox_inches='tight')
            plt.close()
            generated_charts['chart_thresholds'] = str(OUTPUT_FILES['chart_thresholds'])
            log_message("PLS_Thresholds.png 已生成")

        # 将所有图表移入以模型命名的专属子目录
        try:
            import shutil
            from pathlib import Path
            _model_path = str(data_store.get_latest_model_info().get('model_path', ''))
            _stem = os.path.splitext(os.path.basename(_model_path))[0] if _model_path \
                    else datetime.now().strftime("%Y%m%d_%H%M%S")
            _run_dir = Path(str(output_manager.get_path('chart', _stem)))
            _run_dir.mkdir(parents=True, exist_ok=True)
            for key in generated_charts:
                src = str(generated_charts[key])
                if os.path.exists(src) and os.path.isfile(src):
                    dest = str(_run_dir / os.path.basename(src))
                    shutil.move(src, dest)
                    generated_charts[key] = dest
            log_message(f"图表已保存至: {_run_dir}")
        except Exception as e:
            log_message(f"图表整理失败（不影响训练）: {e}", "WARNING")

        return generated_charts

    except Exception as e:
        log_message(f"生成图表时出错: {str(e)}", "ERROR")
        return {}


# ============================================================================
# 其他原有函数（保持不变）
# ============================================================================

def show_large_image(parent, image_path, title="查看大图"):
    """显示大图窗口"""
    from utils import log_message, set_window_icon
    from tkinter import messagebox
    import customtkinter as ctk
    from PIL import Image
    
    try:
        window = ctk.CTkToplevel(parent)
        window.title(title)
        window.grab_set()
        set_window_icon(window)
        
        image = Image.open(image_path)
        img_width, img_height = image.size
        
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)
        
        scale_w = max_width / img_width if img_width > max_width else 1
        scale_h = max_height / img_height if img_height > max_height else 1
        scale = min(scale_w, scale_h)
        
        if scale < 1:
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            display_image = image
            new_width = img_width
            new_height = img_height
        
        window_width = min(new_width + 40, max_width)
        window_height = min(new_height + 40, max_height)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        ctk_image = ctk.CTkImage(light_image=display_image, size=(new_width, new_height))
        
        label = ctk.CTkLabel(window, image=ctk_image, text="")
        label.pack(padx=20, pady=20)
        
    except Exception as e:
        log_message(f"显示大图时出错: {str(e)}", "ERROR")
        messagebox.showerror("显示错误", f"无法显示图片: {str(e)}")


def create_visualization_tabs(root, generated_charts):
    """在GUI中创建可视化标签页显示图表"""
    from utils import log_message
    import customtkinter as ctk
    from tkinter import ttk
    from PIL import Image
    import csv

    if hasattr(root, 'visualization_container') and hasattr(root, 'visualization_placeholder'):
        try:
            root.visualization_placeholder.destroy()
        except:
            pass
        notebook = ctk.CTkTabview(root.visualization_container, width=800, height=500)
        notebook.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
    else:
        notebook = ctk.CTkTabview(root, width=800, height=500)
        notebook.grid(row=6, column=0, columnspan=4, sticky='nsew')

    chart_configs = [
        (generated_charts.get('chart_metrics_table', ''), '性能指标总览'),
        (generated_charts.get('chart_accuracy',      ''), '类别性能'),
        (generated_charts.get('chart_metrics',       ''), '综合指标'),
        (generated_charts.get('chart_confusion',     ''), '混淆矩阵'),
        (generated_charts.get('chart_roc',           ''), 'ROC曲线'),
    ]
    if generated_charts.get('chart_thresholds'):
        chart_configs.append((generated_charts['chart_thresholds'], '阈值分布'))
    
    for chart_file, tab_name in chart_configs:
        if not chart_file or not os.path.exists(chart_file):
            log_message(f"图表文件不存在: {chart_file}")
            continue
            
        try:
            tab = notebook.add(tab_name)
            
            # CSV文件用Treeview表格显示
            if chart_file.endswith('.csv'):
                _create_table_view(tab, chart_file, root)
                log_message(f"已加载表格: {tab_name}")
            else:
                # 图片文件用Image显示
                _create_image_view(tab, chart_file, notebook, tab_name)
                log_message(f"已加载图表: {tab_name}")
                
        except Exception as e:
            log_message(f"加载 {tab_name} 时出错: {str(e)}")
            error_label = ctk.CTkLabel(tab, text=f"无法加载: {chart_file}\n错误: {str(e)}", 
                                      text_color="red")
            error_label.pack(fill='both', expand=True)
    
    log_message("可视化加载完成！","SUCCESS")
    root.update()
    return notebook


def _create_table_view(parent, csv_path, root):
    """在标签页中创建表格视图"""
    from tkinter import ttk
    import tkinter as tk
    import csv
    
    # 读取CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        data = list(reader)
    
    # 创建Frame容器
    frame = ttk.Frame(parent)
    frame.pack(fill='both', expand=True, padx=15, pady=15)
    
    # 配置样式
    style = ttk.Style()
    style.theme_use('clam')
    
    # 表头样式
    style.configure("Metrics.Treeview.Heading", 
                    font=('Arial', 18, 'bold'),
                    background='#4472C4',
                    foreground='white',
                    padding=(10, 8))
    
    # 表格内容样式
    style.configure("Metrics.Treeview",
                    font=('Arial', 18),
                    rowheight=74,
                    background='white',
                    fieldbackground='white')
    
    # 选中样式
    style.map('Metrics.Treeview', 
              background=[('selected', '#cce5ff')],
              foreground=[('selected', 'black')])
    
    # 创建Treeview
    tree = ttk.Treeview(frame, columns=headers, show='headings', 
                        height=len(data), style="Metrics.Treeview")
    
    # 设置列宽 - 自适应填满
    col_widths = [300, 150, 150, 250]
    for i, header in enumerate(headers):
        width = col_widths[i] if i < len(col_widths) else 120
        tree.heading(header, text=header)
        tree.column(header, width=width, minwidth=width, anchor='center')
    
    # 交替行颜色
    tree.tag_configure('oddrow', background='#ffffff')
    tree.tag_configure('evenrow', background='#f0f4f8')
    
    for i, row in enumerate(data):
        tag = 'evenrow' if i % 2 == 0 else 'oddrow'
        tree.insert('', 'end', values=row, tags=(tag,))
    
    # 水平居中，顶部对齐
    tree.pack(fill='none', anchor='n')
    
    # 右键复制菜单
    menu = tk.Menu(tree, tearoff=0, font=('Arial', 15))
    
    def copy_all():
        lines = ['\t'.join(headers)]
        for item in tree.get_children():
            values = tree.item(item)['values']
            lines.append('\t'.join(str(v) for v in values))
        root.clipboard_clear()
        root.clipboard_append('\n'.join(lines))
    
    menu.add_command(label="复制全部", command=copy_all,font=("Microsoft YaHei UI", 14))
    tree.bind('<Button-3>', lambda e: menu.post(e.x_root, e.y_root))


def _create_image_view(parent, image_path, notebook, tab_name):
    """在标签页中创建图片视图"""
    import customtkinter as ctk
    from PIL import Image
    
    image_frame = ctk.CTkFrame(parent, fg_color="transparent")
    image_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    image = Image.open(image_path)
    img_width, img_height = image.size
    
    available_width = 760
    available_height = 440
    
    scale = min(available_width / img_width, available_height / img_height)
    final_width = int(img_width * scale)
    final_height = int(img_height * scale)
    
    resized_image = image.resize((final_width, final_height), Image.Resampling.LANCZOS)
    ctk_image = ctk.CTkImage(light_image=resized_image, size=(final_width, final_height))
    
    label = ctk.CTkLabel(image_frame, image=ctk_image, text="")
    label.place(relx=0.5, rely=0.5, anchor='center')
    
    def on_click(event, path=image_path):
        show_large_image(notebook.master, path, f"查看大图 - {tab_name}")
    
    label.bind("<Button-1>", on_click)
    
    return notebook


def visualize_performance(train_accuracy, test_accuracy, f_scores, 
                         confusion_matrices, fpr_values, tpr_values, auc_list, 
                         thresholds_used=None, root=None):
    """可视化机器学习模型的多种性能指标并在GUI中显示结果"""
    from utils import log_message
    from tkinter import messagebox
    
    try:
        generated_charts = generate_performance_charts(
            train_accuracy, test_accuracy, f_scores, 
            confusion_matrices, fpr_values, tpr_values, auc_list, thresholds_used
        )
        
        if not generated_charts:
            log_message("没有生成任何图表", "WARNING")
            return
        
        if root is not None:
            create_visualization_tabs(root, generated_charts)
        
    except Exception as e:
        log_message(f"创建可视化界面时出错: {str(e)}", "ERROR")
        messagebox.showerror("界面创建错误", f"创建可视化界面时出现错误：{str(e)}")