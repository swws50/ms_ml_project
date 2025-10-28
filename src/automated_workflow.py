# automated_workflow.py - 自动化工作流程模块

import os
import time
from pathlib import Path
from tkinter import messagebox, simpledialog
import customtkinter as ctk

from utils import log_message, set_window_icon
from config import get_output_paths
import data_store
from output_manager import output_manager


class AutomatedWorkflow:
    """自动化工作流程管理器"""
    
    def __init__(self, gui_manager):
        """
        初始化自动化工作流
        
        参数:
            gui_manager: 主界面管理器实例
        """
        self.gui_manager = gui_manager
        self.root = gui_manager.root
        self.workflow_window = None
        
    def start_workflow(self):
        """启动自动化工作流程"""
        log_message("=== 启动自动化工作流程 ===", "INFO")
        
        # 步骤1: 创建新项目
        project_name = self._create_project_step()
        if not project_name:
            log_message("用户取消了项目创建,工作流终止", "WARNING")
            return
        
        # 步骤2: 数据预处理(用户手动操作)
        self._preprocessing_step()
        
    def _create_project_step(self):
        """步骤1: 创建新项目"""
        log_message("步骤 1/4: 创建新项目", "INFO")
        
        # 显示项目创建向导
        wizard = self.gui_manager.project_manager.create_project_wizard(self.root)
        self.root.wait_window(wizard.dialog)
        
        if wizard.result:
            project_name = wizard.result['name']
            log_message(f"项目 '{project_name}' 创建成功", "SUCCESS")
            return project_name
        else:
            return None
    
    def _preprocessing_step(self):
        """步骤2: 数据预处理"""
        log_message("步骤 2/4: 数据预处理", "INFO")
        log_message("请在弹出的窗口中完成文件分类和预处理操作", "INFO")
        
        # 显示预处理对话框
        self.gui_manager.data_preprocessor.show_classification_dialog(self.root)
        
        # 注册预处理完成的回调 - 通过监听
        self._monitor_preprocessing_completion()
    
    def _monitor_preprocessing_completion(self):
        """监听预处理是否完成"""
        def check_completion():
            # 检查CSV文件是否已生成
            current_paths = get_output_paths()
            csv_path = current_paths['processed_data']
            
            if os.path.exists(csv_path):
                # 预处理完成,继续下一步
                log_message("检测到预处理完成,继续自动化流程", "SUCCESS")
                self.root.after(1000, self._training_step)  # 延迟1秒再继续
            else:
                # 继续监听
                self.root.after(2000, check_completion)  # 每2秒检查一次
        
        # 开始监听
        self.root.after(3000, check_completion)  # 3秒后开始首次检查
    
    def _training_step(self):
        """步骤3: 自动训练"""
        log_message("步骤 3/4: 自动加载数据并训练模型", "INFO")
        
        try:
            # 自动选择刚生成的CSV文件
            current_paths = get_output_paths()
            csv_path = current_paths['processed_data']
            
            if not os.path.exists(csv_path):
                messagebox.showerror("错误", "未找到预处理生成的CSV文件")
                return
            
            # 程序化加载CSV文件
            self._auto_load_csv(csv_path)
            
            # 等待数据加载完成
            self.root.after(500, self._start_auto_training)
            
        except Exception as e:
            log_message(f"自动训练步骤失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"自动训练失败:\n{str(e)}")
    
    def _auto_load_csv(self, csv_path):
        """自动加载CSV文件"""
        import pandas as pd
        from config import get_class_mapping
        import numpy as np
        
        log_message(f"自动加载文件: {os.path.basename(csv_path)}")
        
        # 读取CSV
        df = pd.read_csv(csv_path, index_col=0)
        df = df.iloc[:, 1:]
        
        # 清除旧的分类信息
        data_store.clear_file_classification()
        
        # 处理数据
        row = df.iloc[1:, :].values.T
        ylabels = df.iloc[0, :].values
        ylabels = pd.Series(ylabels).astype(str)
        
        # 从CSV读取类别
        unique_labels = ylabels.unique()
        if len(unique_labels) >= 2:
            classification_data = {
                'class_0_name': str(unique_labels[0]),
                'class_1_name': str(unique_labels[1]),
                'class_0_files': [],
                'class_1_files': []
            }
            data_store.set_file_classification(classification_data)
            log_message(f"自动识别类别: {unique_labels[0]}, {unique_labels[1]}")
        
        # 标签编码
        class_mapping, _ = get_class_mapping()
        column = np.array([class_mapping[label] for label in ylabels])
        
        # 保存到data_store
        data_store.set_training_data(row, column, df)
        data_store.set_training_data_path(csv_path)
        
        # 更新UI状态
        self.gui_manager.ui_panels['control'].update_file_status("已自动选择")
        self.gui_manager.ui_panels['control'].enable_training(True)
        
        log_message(f"数据自动加载成功: {row.shape[0]}个样本, {row.shape[1]}个特征", "SUCCESS")
    
    def _start_auto_training(self):
        """开始自动训练"""
        log_message("开始自动训练模型...", "INFO")
        
        # 获取当前选择的模型
        model_name = self.gui_manager.ui_panels['control'].current_model
        log_message(f"使用模型: {model_name}")
        
        # 调用训练方法
        self.gui_manager.handle_start_training()
        
        # 训练完成后自动进入预测准备
        # 通过监听训练状态
        self._monitor_training_completion()
    
    def _monitor_training_completion(self):
        """监听训练是否完成（带超时机制）"""
        max_wait_time = 30000  # 最多等待30秒
        start_time = [time.time() * 1000]  # 使用列表以便在嵌套函数中修改
        last_chart_count = [0]  # 记录上次的图表数量
        
        def check_training_status():
            # 检查是否有最新训练的模型
            latest_model, latest_path = data_store.get_latest_trained_model()

            if latest_model is not None:
                # 额外检查:确保图表也已生成
                import os
                from output_manager import output_manager
                
                # 获取图表目录
                charts_dir = output_manager.get_path('chart', '')
                
                if os.path.exists(charts_dir):
                    # 获取模型类型和最近的图表文件
                    model_type = latest_model.__class__.__name__ if latest_model else "Model"
                    
                    # 列出目录中所有图表文件
                    chart_files = [f for f in os.listdir(charts_dir) 
                                  if f.startswith(model_type) and f.endswith('.png')]
                    
                    # 检查关键图表 - 只检查3个核心图表
                    has_class_performance = any('ViolinPlot_ClassPerformance' in f for f in chart_files)
                    has_confusion = any('ConfusionMatrix' in f for f in chart_files)
                    has_roc = any('ROC_Curve' in f for f in chart_files)
                    
                    # 计算已等待时间
                    elapsed_time = time.time() * 1000 - start_time[0]
                    
                    # 图表数量稳定（连续两次检查数量相同）
                    charts_stable = (last_chart_count[0] == len(chart_files) and 
                                    last_chart_count[0] > 0)
                    
                    # 判断是否完成的条件（简化版）：
                    # 1. 有3个核心图表且图表数量>=3
                    # 2. 图表数量稳定且>=3（说明生成完毕）
                    # 3. 等待超时
                    charts_ready = (
                        (has_class_performance and has_confusion and has_roc and len(chart_files) >= 3) or
                        (charts_stable and len(chart_files) >= 3) or
                        (elapsed_time > max_wait_time and len(chart_files) >= 1)
                    )
                    
                    if charts_ready:
                        # 训练和图表生成都完成
                        log_message(f"检测到训练完成,图表已生成 (共{len(chart_files)}个)", "SUCCESS")
                        self.root.after(1000, self._prediction_preparation_step)
                    else:
                        # 更新图表计数
                        last_chart_count[0] = len(chart_files)
                        
                        # 模型已保存但图表还在生成中,继续等待
                        remaining = int((max_wait_time - elapsed_time) / 1000)
                        log_message(f"等待图表生成... (已有{len(chart_files)}个, 剩余{remaining}秒)", "INFO")
                        self.root.after(2000, check_training_status)
                else:
                    # 图表目录不存在,继续等待
                    log_message("模型已训练,等待图表生成...", "INFO")
                    self.root.after(2000, check_training_status)
            else:
                # 继续监听
                self.root.after(2000, check_training_status)
        
        # 延迟开始检查,给训练一些时间
        self.root.after(5000, check_training_status)
    
    def _prediction_preparation_step(self):
        """步骤4: 准备预测"""
        log_message("步骤 4/4: 准备预测未知样本", "INFO")
        
        # 自动选择最新训练的模型
        latest_model, model_path = data_store.get_latest_trained_model()
        
        if latest_model is not None and model_path:
            model_name = os.path.basename(model_path)
            
            # 获取预测面板
            prediction_panel = self.gui_manager.ui_panels['prediction']
            
            # 使用标准方法设置模型（模拟用户手动选择）
            prediction_panel.current_model_selection = model_path
            prediction_panel.components['model_select_button'].configure(
                text=f"已选择: {model_name}"
            )
            prediction_panel.components['compatibility_status'].configure(
                text="模型: 已选择", 
                text_color="green"
            )
            
            # 更新预测面板显示
            prediction_panel.update_result(
                f"自动化流程完成!\n\n"
                f"已自动选择模型:\n{model_name}\n\n"
                f"现在可以选择未知样本进行预测",
                color="green"
            )
            
            log_message(f"已自动选择模型: {model_name}", "SUCCESS")
            log_message("=== 自动化工作流程完成 ===", "SUCCESS")
            
            # 显示完成提示
            messagebox.showinfo(
                "工作流程完成",
                "自动化流程已完成!\n\n"
                "已完成的步骤:\n"
                "✓ 创建新项目\n"
                "✓ 数据预处理\n"
                "✓ 模型训练\n"
                "✓ 模型选择\n\n"
                "现在可以使用右侧预测面板\n"
                "选择未知样本进行预测了!"
            )
            
            # 推进帮助步骤
            if self.gui_manager.help_system:
                self.gui_manager.help_system.advance_step("predict_sample")
        else:
            log_message("未找到训练好的模型", "ERROR")
            messagebox.showerror("错误", "未找到训练好的模型,无法继续")


# 使用示例:
# workflow = AutomatedWorkflow(gui_manager)
# workflow.start_workflow()