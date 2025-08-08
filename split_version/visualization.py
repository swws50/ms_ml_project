# visualization.py - 可视化和图表生成模块（修复版本）

# ========== 标准库导入 ==========
import os

# ========== 第三方库导入 ==========
import numpy as np
import matplotlib.pyplot as plt
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

# ========== 本地模块导入 ==========
from config import get_class_mapping, OUTPUT_FILES
from utils import log_message
import data_store



def generate_performance_charts(balanced_accuracy_train, balanced_accuracy_test, 
                               Fscores, confusion_matrixs, fpr_list, tpr_list, 
                               auc_list, thresholds_used=None):
    """
    生成机器学习模型的性能评估图表
    """
    log_message("开始生成可视化图表...")
    generated_charts = {}
    
    # 获取动态类别映射
    _, reverse_class_mapping = get_class_mapping()

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
        
        # 修复：使用config中定义的路径
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
        
        # 修复：使用config中定义的路径
        chart_path = OUTPUT_FILES['chart_metrics']
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close()
        generated_charts['metrics'] = str(chart_path)

        # 3. 生成混淆矩阵图表
        log_message("生成混淆矩阵图...")
        plt.figure(figsize=(5, 5))
        mean_conf_matrix = confusion_matrixs.mean(axis=0).reshape((2, 2))
        plt.imshow(mean_conf_matrix, interpolation='nearest', cmap='Blues')
        plt.colorbar(fraction=0.046, pad=0.04)
        plt.xticks([0, 1], ["class 0","class 1"])
        plt.yticks([0, 1], ["class 0","class 1"])
        
        # 添加数值标签
        for i in range(2):
            for j in range(2):
                plt.text(j, i, f"{mean_conf_matrix[i, j]:.1f}", 
                        ha="center", va="center", color="black")
        
        plt.xlabel('Predicted Class')
        plt.ylabel('True Class')
        plt.title('Mean Confusion Matrix')
        
        # 修复：使用config中定义的路径
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
        
        # 修复：使用config中定义的路径
        chart_path = OUTPUT_FILES['chart_roc']
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close()
        generated_charts['roc'] = str(chart_path)
        
        # 5. 生成PLS阈值分布图（如果有阈值数据）
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
                
            # 添加平均阈值和默认阈值的竖线
            plt.axvline(x=mean_threshold, color='r', linestyle='--', 
                       label=f'Mean Threshold: {mean_threshold:.4f}')
            plt.axvline(x=0.5, color='g', linestyle='--', 
                       label='Default Threshold: 0.5')
            
            plt.xlabel('Threshold Value', fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            plt.legend(loc='upper right', fontsize=10)
            plt.title(f'PLS-DA Optimal Threshold Distribution (Mean={mean_threshold:.4f}, Std={std_threshold:.4f})', 
                      fontsize=12)
            plt.ylim(0, y_max)
            plt.tight_layout()
            
            # 修复：使用config中定义的路径
            chart_path = OUTPUT_FILES['chart_thresholds']
            plt.savefig(chart_path, dpi=100, bbox_inches='tight')
            plt.close()
            generated_charts['thresholds'] = str(chart_path)

        log_message("所有图表生成完成")
        return generated_charts

    except Exception as e:
        log_message(f"生成图表时出错: {str(e)}", "ERROR")
        return {}

def create_visualization_tabs(root, generated_charts):
    """
    在GUI中创建可视化标签页显示图表
    """
    # 检查是否有可视化容器
    if hasattr(root, 'visualization_container') and hasattr(root, 'visualization_placeholder'):
        # 先销毁占位标签
        try:
            root.visualization_placeholder.destroy()
        except:
            pass
        
        # === 创建更大的选项卡视图 ===
        notebook = ctk.CTkTabview(root.visualization_container, width=800, height=500)
        notebook.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
    else:
        # 如果没有找到可视化容器，使用原来的方式（兼容性）
        notebook = ctk.CTkTabview(root, width=800, height=500)
        notebook.grid(row=6, column=0, columnspan=4, sticky='nsew')

    # 修复：图表文件列表使用config中的路径
    chart_configs = [
        (str(OUTPUT_FILES['chart_accuracy']), '准确率'),
        (str(OUTPUT_FILES['chart_metrics']), '精确率/召回率/F1'),
        (str(OUTPUT_FILES['chart_confusion']), '混淆矩阵'),
        (str(OUTPUT_FILES['chart_roc']), 'ROC曲线')
    ]
    
    # 如果有阈值数据，添加阈值分布图
    if str(OUTPUT_FILES['chart_thresholds']) in generated_charts.values():
        chart_configs.append((str(OUTPUT_FILES['chart_thresholds']), '阈值分布'))
    
    # 创建选项卡
    for chart_file, tab_name in chart_configs:
        if os.path.exists(chart_file):
            try:
                # 创建选项卡
                tab = notebook.add(tab_name)
                 
                # === 创建图像显示框架 ===
                image_frame = ctk.CTkFrame(tab, fg_color="transparent")
                image_frame.pack(fill='both', expand=True, padx=10, pady=10)
                
                # 加载原始图像
                image = Image.open(chart_file)
                img_width, img_height = image.size
                
               # === 计算最佳显示尺寸 ===
                # 可用的显示区域尺寸（考虑选项卡的标题栏和边距）
                available_width = 760   # 800 - 40 (左右边距)
                available_height = 440  # 500 - 60 (上下边距 + 选项卡标题)
                
                # 计算缩放比例，保持图片宽高比
                scale_width = available_width / img_width
                scale_height = available_height / img_height
                scale = min(scale_width, scale_height)  # 取较小的比例，确保图片完全显示
                
                # 计算最终尺寸
                final_width = int(img_width * scale)
                final_height = int(img_height * scale)
                
                # 调整图像大小并创建CTkImage
                resized_image = image.resize((final_width, final_height), Image.Resampling.LANCZOS)
                ctk_image = ctk.CTkImage(light_image=resized_image, size=(final_width, final_height))

                # === 居中显示图像 ===
                label = ctk.CTkLabel(image_frame, image=ctk_image, text="")
                label.place(relx=0.5, rely=0.5, anchor='center')  # 精确居中
                
                log_message(f"已加载图表: {tab_name}")

            except Exception as e:
                # 错误处理
                log_message(f"加载图表 {tab_name} 时出错: {str(e)}")
                tab = notebook.add(f"{tab_name}(错误)")
                error_label = ctk.CTkLabel(tab, text=f"无法加载图表: {chart_file}\n错误: {str(e)}", 
                                          text_color="red")
                error_label.pack(fill='both', expand=True)
        else:
            # 文件不存在的错误处理
            log_message(f"警告: 图表文件不存在: {chart_file}")
            tab = notebook.add(f"{tab_name}(缺失)")
            missing_label = ctk.CTkLabel(tab, text=f"图表文件未找到:\n{chart_file}", 
                                        text_color="orange")
            missing_label.pack(fill='both', expand=True)
    
    log_message("可视化界面创建完成！")
    root.update()
    return notebook

def visualize_performance(balanced_accuracy_train, balanced_accuracy_test, Fscores, 
                         confusion_matrixs, fpr_list, tpr_list, auc_list, 
                         thresholds_used=None, root=None):
    """可视化机器学习模型的多种性能指标并在GUI中显示结果"""
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

def reset_analysis(help_system):
    """重置分析进度，开始新的分析流程"""
    
    if help_system:
        help_system.reset_progress()
    
    # 清空数据存储模块中的数据
    data_store.clear_all_data()  # 修复：使用正确的函数名
    
    log_message("分析进度已重置，数据存储模块已清空", "INFO")