# visualization.py - 可视化和图表生成模块（增强版本）

# 标准库导入 
import os

# 第三方库导入 
import numpy as np
import matplotlib.pyplot as plt
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import matplotlib.patches as mpatches

# 本地模块导入 
from config import get_class_mapping, OUTPUT_FILES
from utils import log_message, set_window_icon
import data_store


def generate_performance_charts(balanced_accuracy_train, balanced_accuracy_test, 
                               Fscores, confusion_matrixs, fpr_list, tpr_list, 
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
        # 1. 生成准确率图表
        log_message("生成准确率对比图...")
        plt.figure(figsize=(6, 4))
        plt.scatter(range(len(balanced_accuracy_train)), balanced_accuracy_train,
                    label='Training Balanced Accuracy', color='b', s=5)
        plt.scatter(range(len(balanced_accuracy_test)), balanced_accuracy_test, 
                    label='Test Balanced Accuracy', color='r', s=5)
        plt.xlabel('Iteration')
        plt.ylabel('Balanced Accuracy')
        plt.legend()
        plt.title('Training and Test Balanced Accuracy over Iterations')
        
        chart_path = OUTPUT_FILES['chart_accuracy']
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close()
        generated_charts['accuracy'] = str(chart_path)

        # 2. 生成F1分数等指标图表
        log_message("生成精确率/召回率/F1分数图...")
        plt.figure(figsize=(6, 4))
        plt.scatter(range(len(Fscores)), Fscores[:, 0], label='Weighted Avg Precision', s=5)
        plt.scatter(range(len(Fscores)), Fscores[:, 1], label='Weighted Avg Recall', s=5)
        plt.scatter(range(len(Fscores)), Fscores[:, 2], label='Weighted Avg F1-score', s=5)
        plt.xlabel('Iteration')
        plt.ylabel('Score')
        plt.legend()
        plt.title('Weighted Average Precision, Recall, and F1-score over Iterations')
        
        chart_path = OUTPUT_FILES['chart_metrics']
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close()
        generated_charts['metrics'] = str(chart_path)

        # 3. 生成增强的混淆矩阵图表（带百分比和数值）
        log_message("生成增强混淆矩阵图...")
        plt.figure(figsize=(6, 5))
        mean_conf_matrix = confusion_matrixs.mean(axis=0).reshape((2, 2))
        
        # 计算每行的百分比（按真实类别归一化）
        row_sums = mean_conf_matrix.sum(axis=1, keepdims=True)
        conf_matrix_percent = (mean_conf_matrix / row_sums) * 100
        
        plt.imshow(mean_conf_matrix, interpolation='nearest', cmap='Blues')
        plt.colorbar(fraction=0.046, pad=0.04)
        plt.xticks([0, 1], ["Predicted\nClass 0", "Predicted\nClass 1"])
        plt.yticks([0, 1], ["True\nClass 0", "True\nClass 1"])
        
        # 添加数值和百分比标签
        for i in range(2):
            for j in range(2):
                count = mean_conf_matrix[i, j]
                percentage = conf_matrix_percent[i, j]
                # 根据背景色选择文字颜色
                text_color = "white" if count > mean_conf_matrix.max() / 2 else "black"
                plt.text(j, i, f"{count:.1f}\n({percentage:.1f}%)", 
                        ha="center", va="center", color=text_color, 
                        fontsize=11, fontweight='bold')
        
        plt.xlabel('Predicted Class', fontsize=11)
        plt.ylabel('True Class', fontsize=11)
        plt.title('Mean Confusion Matrix\n(Count and Percentage)', fontsize=12)
        plt.tight_layout()
        
        chart_path = OUTPUT_FILES['chart_confusion']
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close()
        generated_charts['confusion'] = str(chart_path)

        # 4. 生成ROC曲线
        log_message("生成ROC曲线图...")
        plt.figure(figsize=(6, 4))
        mean_fpr = np.linspace(0, 1, 100)
        mean_tpr = np.mean([np.interp(mean_fpr, fpr, tpr) for fpr, tpr in zip(fpr_list, tpr_list)], axis=0)
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
        mean_conf_matrix = confusion_matrixs.mean(axis=0).reshape((2, 2))
        tn, fp, fn, tp = mean_conf_matrix.ravel()

        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0
        f1 = 2 * (ppv * sensitivity) / (ppv + sensitivity) if (ppv + sensitivity) > 0 else 0
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        balanced_acc = np.mean(balanced_accuracy_test)
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
    """显示大图窗口"""
    window = ctk.CTkToplevel(parent)
    window.title(title)
    window.grab_set()
    set_window_icon(window)
    
    # 加载并显示原图
    image = Image.open(image_path)
    ctk_image = ctk.CTkImage(light_image=image, size=image.size)
    
    label = ctk.CTkLabel(window, image=ctk_image, text="")
    label.pack(padx=10, pady=10)
    
    # 居中显示窗口
    window.update_idletasks()
    x = (window.winfo_screenwidth() - window.winfo_reqwidth()) // 2
    y = (window.winfo_screenheight() - window.winfo_reqheight()) // 2
    window.geometry(f"+{x}+{y}")


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


def visualize_performance(balanced_accuracy_train, balanced_accuracy_test, Fscores, 
                         confusion_matrixs, fpr_list, tpr_list, auc_list, 
                         thresholds_used=None, root=None):
    """可视化机器学习模型的多种性能指标并在GUI中显示结果（增强版）"""
    try:
        # 生成图表
        generated_charts = generate_performance_charts(
            balanced_accuracy_train, balanced_accuracy_test, Fscores, 
            confusion_matrixs, fpr_list, tpr_list, auc_list, thresholds_used
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