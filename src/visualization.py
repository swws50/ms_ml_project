# visualization.py - 可视化和图表生成模块（增强版本）

# 标准库导入 
import os

# 第三方库导入 
import numpy as np
import matplotlib.pyplot as plt
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
from matplotlib.patches import Patch

# 本地模块导入 
from config import get_class_mapping, OUTPUT_FILES
from utils import log_message, set_window_icon
import data_store



def generate_class_performance_chart(confusion_matrices, f_scores):
    """
    生成类别性能图表（组1）：Sensitivity, Specificity, Precision
    使用小提琴图展示分布，符合论文标准
    
    参数：
        confusion_matrices: 混淆矩阵 (100x4) [TN, FP, FN, TP]
        f_scores: 精确率/召回率/F1 (100x3)
    
    返回：
        图表保存路径
    """
    from config import get_output_paths
    from utils import log_message
    
    OUTPUT_FILES = get_output_paths()
    log_message("生成类别性能小提琴图...")
    
    # 设置论文风格
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial']
    
    # 从混淆矩阵提取数据
    TNs = confusion_matrices[:, 0]
    FPs = confusion_matrices[:, 1]
    FNs = confusion_matrices[:, 2]
    TPs = confusion_matrices[:, 3]
    
    # 计算指标
    sensitivity = TPs / (TPs + FNs + 1e-10)  # TPR/Recall
    specificity = TNs / (TNs + FPs + 1e-10)  # TNR
    precision = f_scores[:, 0]  # PPV
    
    # 创建图形 - 论文标准尺寸
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # 数据准备
    data_list = [sensitivity, specificity, precision]
    labels = ['Sensitivity\n(TPR)', 'Specificity\n(TNR)', 'Precision\n(PPV)']
    
    # 绘制小提琴图
    parts = ax.violinplot(data_list, positions=[1, 2, 3], widths=0.6,
                          showmeans=True, showmedians=False, showextrema=True)
    
    # 设置颜色 - 使用学术配色
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # 蓝、橙、绿
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.8)
        pc.set_edgecolor('black')
        pc.set_linewidth(0.5)
    
    # 设置其他元素样式
    parts['cmeans'].set_color('red')
    parts['cmeans'].set_linewidth(1.5)
    parts['cbars'].set_color('black')
    parts['cbars'].set_linewidth(0.8)
    parts['cmaxes'].set_color('black')
    parts['cmaxes'].set_linewidth(0.8)
    parts['cmins'].set_color('black')
    parts['cmins'].set_linewidth(0.8)
    
    # 添加均值文本
    for i, data in enumerate(data_list):
        mean_val = np.mean(data)
        std_val = np.std(data)
        ax.text(i+1, 1.02, f'{mean_val:.3f}±{std_val:.3f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 设置轴标签和标题
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Class-wise Performance Metrics', fontsize=13, fontweight='bold', pad=20)
    
    # 设置y轴范围和网格
    ax.set_ylim(0.6, 1.05)
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    
    # 添加参考线
    ax.axhline(y=0.9, color='green', linestyle=':', alpha=0.4, linewidth=1)
    ax.axhline(y=0.8, color='orange', linestyle=':', alpha=0.4, linewidth=1)
    
    # 添加图例
    legend_elements = [
        Patch(facecolor=colors[0], alpha=0.8, label='Sensitivity'),
        Patch(facecolor=colors[1], alpha=0.8, label='Specificity'),
        Patch(facecolor=colors[2], alpha=0.8, label='Precision')
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=10, framealpha=0.9)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表 - 使用原有路径名
    chart_path = OUTPUT_FILES['chart_accuracy']  # 替代原准确率图
    plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    # 日志输出
    log_message(f"类别性能图表已保存: {chart_path}")
    log_message(f"  Sensitivity: {np.mean(sensitivity):.3f}±{np.std(sensitivity):.3f}")
    log_message(f"  Specificity: {np.mean(specificity):.3f}±{np.std(specificity):.3f}")
    log_message(f"  Precision: {np.mean(precision):.3f}±{np.std(precision):.3f}")
    
    return str(chart_path)


def generate_balance_metrics_chart(confusion_matrices, f_scores):
    """
    生成综合平衡指标图表（组2）：F1-Score, MCC
    使用小提琴图展示分布，符合论文标准
    
    参数：
        confusion_matrices: 混淆矩阵 (100x4) [TN, FP, FN, TP]
        f_scores: 精确率/召回率/F1 (100x3)
    
    返回：
        图表保存路径
    """
    from config import get_output_paths
    from utils import log_message
    
    OUTPUT_FILES = get_output_paths()
    log_message("生成综合平衡指标小提琴图...")
    
    # 设置论文风格
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial']
    
    # 从混淆矩阵提取数据
    TNs = confusion_matrices[:, 0]
    FPs = confusion_matrices[:, 1]
    FNs = confusion_matrices[:, 2]
    TPs = confusion_matrices[:, 3]
    
    # 计算F1和MCC
    f1_scores = f_scores[:, 2]  # F1-score
    
    # 计算MCC
    numerator = (TPs * TNs) - (FPs * FNs)
    denominator = np.sqrt((TPs + FPs) * (TPs + FNs) * (TNs + FPs) * (TNs + FNs))
    mcc_scores = numerator / (denominator + 1e-10)
    
    # 创建图形 - 论文标准尺寸
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # 数据准备
    data_list = [f1_scores, mcc_scores]
    labels = ['F1-Score', 'MCC']
    
    # 绘制小提琴图
    parts = ax.violinplot(data_list, positions=[1, 2], widths=0.5,
                          showmeans=True, showmedians=False, showextrema=True)
    
    # 设置颜色 - 使用学术配色
    colors = ['#9467bd', '#e377c2']  # 紫色系
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.8)
        pc.set_edgecolor('black')
        pc.set_linewidth(0.5)
    
    # 设置其他元素样式
    parts['cmeans'].set_color('red')
    parts['cmeans'].set_linewidth(1.5)
    parts['cbars'].set_color('black')
    parts['cbars'].set_linewidth(0.8)
    parts['cmaxes'].set_color('black')
    parts['cmaxes'].set_linewidth(0.8)
    parts['cmins'].set_color('black')
    parts['cmins'].set_linewidth(0.8)
    
    # 添加统计信息
    for i, data in enumerate(data_list):
        mean_val = np.mean(data)
        std_val = np.std(data)
        cv_val = std_val / (mean_val + 1e-10)
        
        # 均值±标准差
        ax.text(i+1, 1.02, f'{mean_val:.3f}±{std_val:.3f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # CV值
        ax.text(i+1, 0.58, f'CV={cv_val:.3f}',
                ha='center', va='top', fontsize=9, style='italic', color='gray')
    
    # 设置轴标签和标题
    ax.set_xticks([1, 2])
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Comprehensive Balance Metrics', fontsize=13, fontweight='bold', pad=20)
    
    # 设置y轴范围和网格
    ax.set_ylim(0.6, 1.05)
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    
    # 添加参考线
    ax.axhline(y=0.9, color='green', linestyle=':', alpha=0.4, linewidth=1)
    ax.axhline(y=0.8, color='orange', linestyle=':', alpha=0.4, linewidth=1)
    
    # 添加说明文本
    ax.text(1.5, 0.62, 'F1: Harmonic mean of Precision and Recall\nMCC: Correlation coefficient (-1 to +1)',
            ha='center', va='bottom', fontsize=8, style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.3))
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表 - 使用原有路径名
    chart_path = OUTPUT_FILES['chart_metrics']  # 替代原精确率/召回率/F1图
    plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    # 日志输出
    log_message(f"综合平衡指标图表已保存: {chart_path}")
    log_message(f"  F1-Score: {np.mean(f1_scores):.3f}±{np.std(f1_scores):.3f}")
    log_message(f"  MCC: {np.mean(mcc_scores):.3f}±{np.std(mcc_scores):.3f}")
    log_message(f"  F1 CV: {np.std(f1_scores)/np.mean(f1_scores):.3f}")
    log_message(f"  MCC CV: {np.std(mcc_scores)/np.mean(mcc_scores):.3f}")
    
    return str(chart_path)


def generate_confusion_matrix_with_stability(confusion_matrices):
    """
    论文标准版混淆矩阵
    
    特点：
    - 保留V3的智能稳定性评估（Range用于小样本，CV用于大样本）
    - 简洁的视觉风格，符合学术期刊要求
    - 清晰的层级结构：百分比 > 均值±SD > 稳定性指标
    """
    log_message("生成论文标准版混淆矩阵...")
    
    from config import get_output_paths
    OUTPUT_FILES = get_output_paths()
    
    # 计算统计量
    mean_cm = confusion_matrices.mean(axis=0).reshape((2, 2))
    std_cm = confusion_matrices.std(axis=0).reshape((2, 2))
    
    # 计算百分比
    row_sums = mean_cm.sum(axis=1, keepdims=True)
    cm_percent = (mean_cm / row_sums) * 100
    
    # 创建图形 - 论文标准尺寸
    fig, ax = plt.subplots(figsize=(8, 6.5))
    
    # 绘制热力图 - 使用学术风格配色
    im = ax.imshow(mean_cm, interpolation='nearest', cmap='Blues',
                   vmin=0, vmax=mean_cm.max() * 1.05)
    
    # 颜色条 - 简洁样式
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel('Mean Count', rotation=-90, va="bottom", 
                       fontsize=10, fontfamily='sans-serif')
    cbar.ax.tick_params(labelsize=9)
    
    # 设置刻度 - 简洁标签
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(['Predicted\nNegative (0)', 'Predicted\nPositive (1)'], 
                       fontsize=10, fontfamily='sans-serif')
    ax.set_yticklabels(['True\nNegative (0)', 'True\nPositive (1)'], 
                       fontsize=10, fontfamily='sans-serif')
    
    # 添加单元格内容
    for i in range(2):
        for j in range(2):
            mean_val = mean_cm[i, j]
            std_val = std_cm[i, j]
            percent = cm_percent[i, j]
            
            # 获取该位置的100次原始数据
            flat_idx = i * 2 + j
            cell_values = confusion_matrices[:, flat_idx]
            
            # 文字颜色
            text_color = "white" if mean_val > mean_cm.max() / 2 else "black"
            
            # 第一行：百分比（最突出）
            ax.text(j, i - 0.25, f'{percent:.1f}%',
                   ha="center", va="center", 
                   color=text_color, fontsize=18, fontweight='bold',
                   fontfamily='sans-serif')
            
            # 第二行：均值±标准差（辅助信息）
            ax.text(j, i, f'({mean_val:.1f} ± {std_val:.1f})',
                   ha="center", va="center", 
                   color=text_color, fontsize=10, style='italic',
                   fontfamily='sans-serif')
            
            # 第三行：稳定性指标（V3逻辑）
            if mean_val < 5.0:
                # 小样本：使用Range
                min_val = np.min(cell_values)
                max_val = np.max(cell_values)
                range_val = max_val - min_val
                
                # 评估稳定性
                if range_val <= 2:
                    stability_text = f'Range={range_val:.0f} (Excellent)'
                    stability_color = '#006400' if text_color == 'black' else '#90EE90'
                elif range_val <= 4:
                    stability_text = f'Range={range_val:.0f} (Good)'
                    stability_color = '#228B22' if text_color == 'black' else '#98FB98'
                else:
                    stability_text = f'Range={range_val:.0f} (Variable)'
                    stability_color = '#B8860B' if text_color == 'black' else '#FFD700'
                
            else:
                # 大样本：使用CV
                cv_val = std_val / mean_val
                
                if cv_val < 0.15:
                    stability_text = f'CV={cv_val:.3f} (High)'
                    stability_color = '#006400' if text_color == 'black' else '#90EE90'
                elif cv_val < 0.30:
                    stability_text = f'CV={cv_val:.3f} (Mod)'
                    stability_color = '#B8860B' if text_color == 'black' else '#FFD700'
                else:
                    stability_text = f'CV={cv_val:.3f} (Low)'
                    stability_color = '#8B0000' if text_color == 'black' else '#FF6B6B'
            
            ax.text(j, i + 0.25, stability_text,
                   ha="center", va="center", 
                   color=stability_color, fontsize=8, 
                   style='italic', fontweight='normal',
                   fontfamily='sans-serif')
    
    # 轴标签 - 简洁
    ax.set_xlabel('Predicted Class', fontsize=11, fontweight='bold',
                  fontfamily='sans-serif')
    ax.set_ylabel('True Class', fontsize=11, fontweight='bold',
                  fontfamily='sans-serif')
    
    # 标题 - 学术风格
    ax.set_title('Confusion Matrix - Percentage (Mean ± SD) across 100 random splits', 
                fontsize=12, fontweight='bold', pad=15,
                fontfamily='sans-serif')
    
    # 网格线 - 细线
    ax.set_xticks([0.5], minor=True)
    ax.set_yticks([0.5], minor=True)
    ax.grid(which="minor", color="gray", linestyle='-', linewidth=1.5)
    ax.tick_params(which="minor", size=0)
    
    # 说明框 - 横向分布版本（更美观）
    textstr = ('Adaptive Stability Assessment:\n'
               'For rare events (Mean < 5): Range ≤ 2 = Excellent, ≤ 4 = Good, > 4 = Variable\n'
               'For frequent events (Mean ≥ 5): CV < 0.15 = High, < 0.30 = Moderate, ≥ 0.30 = Low')
    
    props = dict(boxstyle='round,pad=0.6', facecolor='wheat', 
                alpha=0.85, edgecolor='gray', linewidth=1)
    
    ax.text(0.5, -0.15, textstr, transform=ax.transAxes,
            fontsize=8, verticalalignment='top', 
            horizontalalignment='center',
            bbox=props, fontfamily='sans-serif')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存 - 高质量
    chart_path = OUTPUT_FILES['chart_confusion']
    plt.savefig(chart_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    # 日志输出（保持不变）
    log_message("=" * 70)
    log_message("混淆矩阵稳定性分析 (论文标准版):")
    log_message("-" * 70)
    
    positions = [
        ('TN [True Negative]', 0, 0, 0), 
        ('FP [False Positive]', 0, 1, 1), 
        ('FN [False Negative]', 1, 0, 2), 
        ('TP [True Positive]', 1, 1, 3)
    ]
    
    for name, i, j, flat_idx in positions:
        mean_val = mean_cm[i, j]
        std_val = std_cm[i, j]
        percent_val = cm_percent[i, j]
        cell_values = confusion_matrices[:, flat_idx]
        
        log_message(f"\n{name}:")
        log_message(f"  百分比: {percent_val:.1f}%")
        log_message(f"  均值±SD: {mean_val:.2f} ± {std_val:.2f}")
        
        if mean_val < 5.0:
            min_val = np.min(cell_values)
            max_val = np.max(cell_values)
            range_val = max_val - min_val
            q1 = np.percentile(cell_values, 25)
            median = np.percentile(cell_values, 50)
            q3 = np.percentile(cell_values, 75)
            
            unique, counts = np.unique(cell_values, return_counts=True)
            freq_str = ", ".join([f"{int(u)}次:{c}个实验" for u, c in zip(unique, counts)])
            
            log_message(f"  罕见事件 - 使用Range评估:")
            log_message(f"    范围: [{min_val:.0f}, {max_val:.0f}], Range={range_val:.0f}")
            log_message(f"    四分位: Q1={q1:.1f}, Median={median:.1f}, Q3={q3:.1f}")
            log_message(f"    分布: {freq_str}")
            
            if range_val <= 2:
                log_message(f"    评价: 优秀 - 错误非常少且一致")
            elif range_val <= 4:
                log_message(f"    评价: 良好 - 波动在可接受范围")
            else:
                log_message(f"    评价: 有一定变异")
                
        else:
            cv_val = std_val / mean_val
            log_message(f"  常见事件 - 使用CV评估:")
            log_message(f"    CV = {cv_val:.4f} ({cv_val*100:.2f}%)")
            
            if cv_val < 0.15:
                log_message(f"    评价: 高度稳定")
            elif cv_val < 0.30:
                log_message(f"    评价: 中等稳定")
            else:
                log_message(f"    评价: 稳定性较低")
    
    log_message("=" * 70)
    log_message(f"图表已保存: {chart_path} (300 DPI, 适合论文发表)")
    
    return str(chart_path)



def generate_performance_charts(train_accuracy, test_accuracy, 
                               f_scores, confusion_matrices, fpr_values, tpr_values, 
                               auc_list, thresholds_used=None):
    """
    生成机器学习模型的性能评估图表（增强版）
    """
    log_message("开始生成可视化图表...")
    generated_charts = {}
    
    # 获取动态类别映射
    _, reverse_class_mapping = get_class_mapping()

    # 获取输出文件路径
    from config import get_output_paths
    OUTPUT_FILES = get_output_paths()

    try:
        
        # 1. 生成类别性能图表（Sensitivity, Specificity, Precision）
        chart_path = generate_class_performance_chart(confusion_matrices, f_scores)
        generated_charts['accuracy'] = chart_path

        # 2. 生成综合平衡指标图表（F1-Score, MCC）
        chart_path = generate_balance_metrics_chart(confusion_matrices, f_scores)
        generated_charts['metrics'] = chart_path

        # 3. 生成专业混淆矩阵（带标准差和变异系数）
        chart_path = generate_confusion_matrix_with_stability(confusion_matrices)
        generated_charts['confusion'] = chart_path

        # 4. 生成ROC曲线
        log_message("生成ROC曲线图...")
        plt.figure(figsize=(6, 4))
        mean_fpr = np.linspace(0, 1, 100)
        mean_tpr = np.mean([np.interp(mean_fpr, fpr, tpr) for fpr, tpr in zip(fpr_values, tpr_values)], axis=0)
        plt.plot(mean_fpr, mean_tpr, color='red', lw=3, 
                label=f'Mean ROC (AUC={np.mean(auc_list):.2f})')
        plt.plot([0, 1], [0, 1], color='gray', linestyle='--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Mean ROC Curve')
        plt.legend()
        
        chart_path = OUTPUT_FILES['chart_roc']
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close()
        generated_charts['roc'] = str(chart_path)
        
        
        # 5. 新增：生成详细性能指标表格
        log_message("生成详细性能指标表格...")

        # Calculate metrics
        mean_conf_matrix = confusion_matrices.mean(axis=0).reshape((2, 2))
        tn, fp, fn, tp = mean_conf_matrix.ravel()

        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0
        f1 = 2 * (ppv * sensitivity) / (ppv + sensitivity) if (ppv + sensitivity) > 0 else 0
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        balanced_acc = np.mean(test_accuracy)
        mean_auc = np.mean(auc_list)

        # Create compact table with key metrics only
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.axis('tight')
        ax.axis('off')

        table_data = [
            ['Metric', 'Value'],
            ['Sensitivity', f'{sensitivity:.4f}'],
            ['Specificity', f'{specificity:.4f}'],
            ['PPV', f'{ppv:.4f}'],
            ['NPV', f'{npv:.4f}'],
            ['Accuracy', f'{accuracy:.4f}'],
            ['Balanced Acc', f'{balanced_acc:.4f}'],
            ['F1-Score', f'{f1:.4f}'],
            ['AUC-ROC', f'{mean_auc:.4f}'],
        ]

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.55, 0.45])

        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)

        # Header row
        table[(0, 0)].set_facecolor('#4472C4')
        table[(0, 1)].set_facecolor('#4472C4')
        table[(0, 0)].set_text_props(weight='bold', color='white', size=10)
        table[(0, 1)].set_text_props(weight='bold', color='white', size=10)

        # Data rows with alternating colors
        for i in range(1, len(table_data)):
            color = '#F2F2F2' if i % 2 == 0 else '#FFFFFF'
            table[(i, 0)].set_facecolor(color)
            table[(i, 1)].set_facecolor(color)
            table[(i, 1)].set_text_props(weight='bold')

        plt.title('Key Metrics', fontsize=11, fontweight='bold', pad=10)
        plt.tight_layout()

        chart_path = OUTPUT_FILES.get('chart_metrics_table', 'output/chart_metrics_table.png')
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close()
        generated_charts['metrics_table'] = str(chart_path)
        
        # 6. 生成PLS阈值分布图（如果有阈值数据）
        if thresholds_used is not None and len(thresholds_used) > 0:
            log_message("生成PLS阈值分布图...")
            mean_threshold = np.mean(thresholds_used)
            std_threshold = np.std(thresholds_used)
            
            plt.figure(figsize=(6, 4))
            hist_data = plt.hist(thresholds_used, bins=20, color='skyblue', 
                               edgecolor='black', alpha=0.7)
            
            if isinstance(hist_data, tuple) and len(hist_data) > 0:
                y_max = max(hist_data[0]) * 1.1
            else:
                y_max = plt.ylim()[1] * 1.1
                
            plt.axvline(x=mean_threshold, color='r', linestyle='--', linewidth=2,
                       label=f'Mean Threshold: {mean_threshold:.4f}')
            plt.axvline(x=0.5, color='g', linestyle='--', linewidth=2,
                       label='Default Threshold: 0.5')
            
            plt.xlabel('Threshold Value', fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            plt.legend(loc='upper right', fontsize=10)
            plt.title(f'PLS-DA Optimal Threshold Distribution\n(Mean={mean_threshold:.4f}, Std={std_threshold:.4f})', 
                      fontsize=12)
            plt.ylim(0, y_max)
            plt.tight_layout()
            
            chart_path = OUTPUT_FILES['chart_thresholds']
            plt.savefig(chart_path, dpi=100, bbox_inches='tight')
            plt.close()
            generated_charts['thresholds'] = str(chart_path)

        log_message("所有图表生成完成")
        return generated_charts

    except Exception as e:
        log_message(f"生成图表时出错: {str(e)}", "ERROR")
        return {}


def show_large_image(parent, image_path, title="查看大图"):
    """显示大图窗口（增强版）- 支持自适应缩放和滚动"""
    try:
        window = ctk.CTkToplevel(parent)
        window.title(title)
        window.grab_set()
        set_window_icon(window)
        
        # 加载原始图像
        image = Image.open(image_path)
        img_width, img_height = image.size
        
        # 获取屏幕尺寸
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # 计算合适的窗口尺寸（屏幕的80%）
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)
        
        # 计算缩放比例（如果图片太大）
        scale_w = max_width / img_width if img_width > max_width else 1
        scale_h = max_height / img_height if img_height > max_height else 1
        scale = min(scale_w, scale_h)
        
        # 应用缩放
        if scale < 1:
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            display_image = image
            new_width = img_width
            new_height = img_height
        
        # 设置窗口尺寸并居中
        window_width = min(new_width + 40, max_width)
        window_height = min(new_height + 40, max_height)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建CTkImage
        ctk_image = ctk.CTkImage(light_image=display_image, size=(new_width, new_height))
        
        # 创建标签显示图像
        label = ctk.CTkLabel(window, image=ctk_image, text="")
        label.pack(padx=20, pady=20)
        
        
    except Exception as e:
        log_message(f"显示大图时出错: {str(e)}", "ERROR")
        messagebox.showerror("显示错误", f"无法显示图片: {str(e)}")


def create_visualization_tabs(root, generated_charts):
    """
    在GUI中创建可视化标签页显示图表（增强版）
    """
    from config import get_output_paths
    OUTPUT_FILES = get_output_paths()

    # 检查是否有可视化容器
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

    # 图表配置列表（按显示顺序）
    chart_configs = [
        (OUTPUT_FILES.get('chart_metrics_table', 'output/chart_metrics_table.png'), '性能指标总览'),
        (str(OUTPUT_FILES['chart_accuracy']), '准确率'),
        (str(OUTPUT_FILES['chart_metrics']), '精确率/召回率/F1'),
        (str(OUTPUT_FILES['chart_confusion']), '混淆矩阵'),
        (str(OUTPUT_FILES['chart_roc']), 'ROC曲线'),
    ]
    
    # 如果有阈值数据，添加阈值分布图
    if str(OUTPUT_FILES['chart_thresholds']) in generated_charts.values():
        chart_configs.append((str(OUTPUT_FILES['chart_thresholds']), '阈值分布'))
    
    # 创建选项卡
    for chart_file, tab_name in chart_configs:
        if os.path.exists(chart_file):
            try:
                tab = notebook.add(tab_name)
                
                image_frame = ctk.CTkFrame(tab, fg_color="transparent")
                image_frame.pack(fill='both', expand=True, padx=10, pady=10)
                
                # 加载原始图像
                image = Image.open(chart_file)
                img_width, img_height = image.size
                
                # 计算最佳显示尺寸
                available_width = 760
                available_height = 440
                
                scale_width = available_width / img_width
                scale_height = available_height / img_height
                scale = min(scale_width, scale_height)
                
                final_width = int(img_width * scale)
                final_height = int(img_height * scale)
                
                resized_image = image.resize((final_width, final_height), Image.Resampling.LANCZOS)
                ctk_image = ctk.CTkImage(light_image=resized_image, size=(final_width, final_height))

                label = ctk.CTkLabel(image_frame, image=ctk_image, text="")
                label.place(relx=0.5, rely=0.5, anchor='center')
                
                # 添加点击事件
                def on_click(event, path=chart_file):
                    show_large_image(notebook.master, path, f"查看大图 - {tab_name}")
                    
                label.bind("<Button-1>", on_click)

                log_message(f"已加载图表: {tab_name}")

            except Exception as e:
                log_message(f"加载图表 {tab_name} 时出错: {str(e)}")
                tab = notebook.add(f"{tab_name}(错误)")
                error_label = ctk.CTkLabel(tab, text=f"无法加载图表: {chart_file}\n错误: {str(e)}", 
                                          text_color="red")
                error_label.pack(fill='both', expand=True)
        else:
            log_message(f"警告: 图表文件不存在: {chart_file}")
    
    log_message("可视化界面创建完成！")
    root.update()
    return notebook


def visualize_performance(train_accuracy, test_accuracy, f_scores, 
                         confusion_matrices, fpr_values, tpr_values, auc_list, 
                         thresholds_used=None, root=None):
    """可视化机器学习模型的多种性能指标并在GUI中显示结果（增强版）"""
    try:
        # 生成图表
        generated_charts = generate_performance_charts(
            train_accuracy, test_accuracy, f_scores, 
            confusion_matrices, fpr_values, tpr_values, auc_list, thresholds_used
        )
        
        if not generated_charts:
            log_message("没有生成任何图表", "WARNING")
            return
        
        # 在GUI中显示图表
        if root is not None:
            create_visualization_tabs(root, generated_charts)
        
    except Exception as e:
        log_message(f"创建可视化界面时出错: {str(e)}", "ERROR")
        messagebox.showerror("界面创建错误", f"创建可视化界面时出现错误：{str(e)}")