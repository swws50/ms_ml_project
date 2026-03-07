# automated_workflow.py - 自动化工作流程模块

import os
from tkinter import messagebox

from utils import log_message
from config import get_output_paths
import data_store


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

        # 启用静默模式，避免预处理完成后的弹窗阻塞自动化流程
        self.gui_manager.data_preprocessor.silent_mode = True

        # 三个 chip 统一显示自动化提示
        gp = self.gui_manager.global_progress
        gp.update_chip('preprocess', '⚙ 自动化中...', '#888888')
        gp.update_chip('train',      '⚙ 自动化中...', '#888888')
        gp.update_chip('predict',    '⚙ 自动化中...', '#888888')

        # 注册预处理完成回调
        self.gui_manager.data_preprocessor.on_complete_callback = self._on_preprocess_done

        # 显示预处理对话框（wait_window 阻塞至窗口关闭）
        self.gui_manager.data_preprocessor.show_classification_dialog(self.root)

        # 清理回调
        self.gui_manager.data_preprocessor.on_complete_callback = None

    def _on_preprocess_done(self):
        """预处理完成回调 - 由 DataPreprocessor 在保存成功后触发"""
        log_message("预处理完成，准备自动加载数据并训练", "INFO")
        self.root.after(1000, self._training_step)

    def _find_latest_data_csv(self):
        """查找最新的数据CSV文件（支持 data.csv 或 data_*.csv）"""
        import glob

        current_paths = get_output_paths()
        base_path = current_paths['processed_data']
        data_dir = os.path.dirname(base_path)

        # 查找所有匹配的CSV文件
        pattern = os.path.join(data_dir, "data*.csv")
        csv_files = glob.glob(pattern)

        if not csv_files:
            return None

        # 按修改时间排序，返回最新的
        csv_files.sort(key=os.path.getmtime, reverse=True)
        return csv_files[0]

    def _training_step(self):
        """步骤3: 自动训练"""
        log_message("步骤 3/4: 自动加载数据并训练模型", "INFO")

        try:
            csv_path = self._find_latest_data_csv()

            if not csv_path or not os.path.exists(csv_path):
                messagebox.showerror("错误", "未找到预处理生成的CSV文件")
                return

            log_message(f"使用数据文件: {os.path.basename(csv_path)}")
            
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
        from data_store import class_manager
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
        column = np.array([class_manager.encode(label) for label in ylabels])
        
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

        try:
            # 调用训练方法（同步执行，会阻塞直到训练和可视化完成）
            self.gui_manager.handle_start_training()

            # 训练完成后检查模型是否成功保存
            latest_model, latest_path = data_store.get_latest_trained_model()

            if latest_model is not None:
                log_message("训练完成，准备进入预测阶段", "SUCCESS")
                # 延迟一小段时间确保UI更新完成，然后进入预测准备步骤
                self.root.after(500, self._prediction_preparation_step)
            else:
                log_message("训练完成但未检测到模型，可能训练失败", "WARNING")
                messagebox.showwarning("警告", "训练完成但未能保存模型，请检查日志")

        except Exception as e:
            log_message(f"自动训练失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"自动训练失败:\n{str(e)}")
    
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

            # 恢复三个 chip 为最终状态
            gp = self.gui_manager.global_progress
            gp.update_chip('preprocess', '✓ 预处理: 完成', 'green')
            gp.update_chip('train',      '✓ 训练: 完成', 'green')
            gp.update_chip('predict',    '✓ 预测: 模型已加载，可进行预测', 'green')

            # 重置静默模式
            self.gui_manager.data_preprocessor.silent_mode = False

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
            gp = self.gui_manager.global_progress
            gp.update_chip('preprocess', '✓ 预处理: 完成', 'green')
            gp.update_chip('train',      '✗ 训练: 失败', 'red')
            gp.update_chip('predict',    '○ 预测: --', 'gray')
            self.gui_manager.data_preprocessor.silent_mode = False
            messagebox.showerror("错误", "未找到训练好的模型,无法继续")


# 使用示例:
# workflow = AutomatedWorkflow(gui_manager)
# workflow.start_workflow()