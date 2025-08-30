# main.py - 使用UI组件的主程序（渐进式升级）

# 标准库导入 
import os

# 第三方库导入 
import customtkinter as ctk
from tkinter import filedialog, messagebox,PhotoImage

# 本地模块导入 
from config import MODEL_CONFIGS, DEFAULT_MODEL
from utils import log_message, clear_log, set_global_widgets, set_window_icon
from data_processing import open_data_file
from model_training import TrainingUI
from model_predictor import PredictionManager
from help_system import HelpSystem
from visualization import reset_analysis
import data_store
# 导入新的UI组件
from ui_components import (
    ControlPanel, ResultPanel, PredictionPanel, 
    VisualizationPanel, InfoPanel, PreprocessingPanel
)
from data_preprocessor import  DataPreprocessor
from ui_components import ProgressComponent
from print_manager import PrintManager

class MainGUIManager:
    """主界面管理器类 - 使用模块化UI组件"""
    
    def __init__(self, root):
        self.root = root
        self.root.gui_manager = self
        self.help_system = None
        self.exact_selection = DEFAULT_MODEL

        # 业务逻辑管理器
        self.data_preprocessor = DataPreprocessor()
        self.training_ui = None
        self.prediction_manager = None

        # UI组件面板
        self.ui_panels = {
            'control': None,
            'result': None,
            'prediction': None,
            'visualization': None,
            'info': None
        }
        
        self.menu_frame = None

        # 添加打印管理器
        self.print_manager = PrintManager()

    def create_gui_components(self):
        """ 
        创建GUI界面 - 使用模块化UI组件
        """
        # 设置主题和窗口
        self._setup_window()
        
        # 初始化业务逻辑管理器
        self._init_managers()
        
        # 创建UI布局
        self._create_layout()
        
        # 设置全局引用和初始化
        self._finalize_setup()
    
    def _setup_window(self):
        """设置窗口基本属性"""
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("dark-blue")
        self.root.title('诊断分析')
        
        # 设置图标
        set_window_icon(self.root)
        # 创建帮助系统
        self.help_system = HelpSystem(self.root)
        
        # 设置窗口大小
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{height}+0+0")
        try:
            self.root.state('zoomed')  # Windows
        except:
            self.root.attributes('-zoomed', True)  # Linux
    
    def _init_managers(self):
        """初始化业务逻辑管理器"""
        self.training_ui = TrainingUI(self.help_system)
        self.prediction_manager = PredictionManager(self.help_system)
    
    def _create_layout(self):
        """创建UI布局"""
        # 创建顶部菜单栏 - row=0
        self._create_menu_bar()
        
        # 创建进度指示器 - row=1 
        self.help_system.create_progress_indicator(self.root, row=1, column=0, columnspan=4)
        

        # 配置网格权重 
        self.root.grid_rowconfigure(3, minsize=30, weight=0)  # 进度条行限制高度
        self.root.grid_rowconfigure(4, weight=1)  # 下方面板区域可扩展
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_columnconfigure(3, weight=1)

        # 先创建面板 - row=2
        self._create_ui_panels()

        # 后创建进度条 - row=3
        self._create_global_progress()

    def _create_global_progress(self):
        """创建全局进度组件"""
        # 进度容器放在row=3
        self.progress_container = ctk.CTkFrame(self.root, fg_color="transparent", height=25)
        self.progress_container.grid(row=3, column=0, columnspan=4, sticky='ew', padx=20, pady=2)
        self.progress_container.grid_columnconfigure(0, weight=1)
        
        self.global_progress = ProgressComponent(self.progress_container, width=200, show_label=True)
        self.global_progress.create(row=0, column=0, sticky='ew', padx=0, pady=0)
        self.global_progress.hide()
            
    def _create_menu_bar(self):
        """创建菜单栏"""
        self.menu_frame = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, columnspan=4, sticky='ew', padx=0, pady=0)
        
        menu_container = ctk.CTkFrame(self.menu_frame, fg_color="transparent")
        menu_container.pack(side="left", padx=20, pady=15)
        
        # 项目管理按钮
        project_btn = ctk.CTkButton(menu_container, text="重置进度", width=100, height=35,
                                command=self.handle_reset_progress)
        project_btn.pack(side="left", padx=5)
        
        # 新增：打印按钮
        print_btn = ctk.CTkButton(menu_container, text="打印报告", width=100, height=35,
                                command=self.handle_print_report)
        print_btn.pack(side="left", padx=5)

        # 帮助按钮
        help_btn = ctk.CTkButton(menu_container, text="使用向导", width=100, height=35,
                                command=self.help_system.show_wizard)
        help_btn.pack(side="left", padx=5)
        
    def handle_print_report(self):
        """处理打印报告"""
        self.print_manager.show_print_dialog(self.root)
               
    def _create_ui_panels(self):
        """使用UI组件创建各个面板"""
        # 上方面板在row=2
        # 0. 预处理面板
        preprocessing_callbacks = {
            'on_start_preprocessing':self._handle_preprocessing_start
        }
        self.ui_panels['preprocessing'] = PreprocessingPanel(self.root, self.help_system, preprocessing_callbacks)
        self.ui_panels['preprocessing'].create_panel(2, column=0)

        # 1. 控制面板 
        control_callbacks = {
            'on_file_select': self.handle_file_select,
            'on_model_select': self.handle_model_select,
            'on_start_training': self.handle_start_training
        }
        self.ui_panels['control'] = ControlPanel(self.root, self.help_system, control_callbacks)
        self.ui_panels['control'].create_panel(row=2, column=1)
        
        # 2. 结果面板 
        self.ui_panels['result'] = ResultPanel(self.root, self.help_system)
        self.ui_panels['result'].create_panel(row=2, column=2)
        
        # 3. 预测面板 
        prediction_callbacks = {
            'on_predict_file': self.handle_predict_file,
            'on_model_info': self.handle_model_info,
        }
        self.ui_panels['prediction'] = PredictionPanel(self.root, self.help_system, prediction_callbacks)
        self.ui_panels['prediction'].create_panel(row=2, column=3)
        
        # 4. 可视化面板 
        self.ui_panels['visualization'] = VisualizationPanel(self.root, self.help_system)
        self.ui_panels['visualization'].create_panel(row=4, column=0, columnspan=2)
        
        # 5. 信息面板 
        self.ui_panels['info'] = InfoPanel(self.root, self.help_system)
        self.ui_panels['info'].create_panel(row=4, column=2, columnspan=2)
    
    def _finalize_setup(self):
        """完成设置"""
        # 为visualization模块设置引用
        self.root.visualization_container = self.ui_panels['visualization'].get_container()
        self.root.visualization_placeholder = self.ui_panels['visualization'].get_placeholder()
        
        # 设置全局日志引用
        info_textbox = self.ui_panels['info'].get_textbox()
        set_global_widgets(info_textbox, self.root)
        
        # 初始化日志
        log_message("系统已启动，等待用户操作...")
        log_message("使用模块化UI组件，界面更加清晰", "INFO")
        
        # 显示向导
        if self.help_system.show_wizard_on_startup:
            self.root.after(500, self.help_system.show_wizard)
    
    # 业务逻辑处理方法 
    
    def handle_file_select(self):
        """处理文件选择"""
        # 获取控制面板的组件引用
        control_panel = self.ui_panels['control']
        
        # 调用原有的数据处理逻辑
        row, column, df = open_data_file(
            control_panel.components['file_status'],  # 传递状态标签
            control_panel.components['start_button'], # 传递训练按钮
        )

        if row is not None and column is not None:
            # 将数据存储到data_store模块
            data_store.set_training_data(row, column, df)
            log_message("训练数据已加载到数据存储模块", "SUCCESS")
            
            # 更新UI状态
            control_panel.update_file_status("已选择")
            control_panel.enable_training(True)
            
            # 推进步骤
            if self.help_system:
                self.help_system.advance_step("select_model")
        else:
            log_message("数据加载失败", "ERROR")
    
    def handle_model_select(self, model_name):
        """处理模型选择"""
        self.exact_selection = model_name
        log_message(f"已选择模型: {model_name}")
        
        # 推进帮助系统步骤
        if self.help_system:
            self.help_system.advance_step("train_model")
    
    def handle_predict_file(self):
        """处理文件预测"""
        prediction_panel = self.ui_panels['prediction']
        self.prediction_manager.open_file_dialog(prediction_panel.components['result_label'])
    
    def handle_model_info(self):
        """处理模型信息查看"""
        self.prediction_manager.show_model_info_window(self.root)
    
    def handle_reset_progress(self):
        """完整的重置操作"""
        # 重置数据和进度
        reset_analysis(self.help_system)
        
        # 清理UI显示
        clear_log()
        self.ui_panels['result'].reset_results()
        self.ui_panels['prediction'].update_result("状态：等待选择文件")
        
         # 重新创建可视化面板
        old_viz_panel = self.ui_panels['visualization'].frame
        old_viz_panel.destroy()
        # 重新创建
        self.ui_panels['visualization'] = VisualizationPanel(self.root, self.help_system)
        self.ui_panels['visualization'].create_panel(row=4, column=0, columnspan=2)
        # 更新引用
        self.root.visualization_container = self.ui_panels['visualization'].get_container()
        self.root.visualization_placeholder = self.ui_panels['visualization'].get_placeholder()
        
        
        log_message("系统已重置，可以开始新的分析流程", "SUCCESS")

    def show_global_progress(self, message="处理中..."):
        """显示全局进度条"""
        self.global_progress.show()
        self.global_progress.update(0, message)

    def update_global_progress(self, progress, message):
        """更新全局进度"""
        self.global_progress.update(progress, message)

    def hide_global_progress(self):
        """隐藏全局进度条"""
        self.global_progress.hide()

    def _handle_preprocessing_start(self):
        """处理预处理开始"""
        self.show_global_progress("正在启动数据预处理...")
        self.data_preprocessor.show_classification_dialog(self.root)

    def handle_start_training(self):
        """处理开始训练"""
        control_panel = self.ui_panels['control']
        result_panel = self.ui_panels['result']
        
        # 重置结果显示
        result_panel.reset_results()
        
        # 显示全局进度条
        self.show_global_progress("开始模型训练...")
        
        # 使用训练UI进行训练
        self.training_ui.train_with_ui_feedback(
            self.exact_selection,
            self.global_progress.status_label,
            self.global_progress.progress_bar,
            result_panel.components['train_accuracy'],
            result_panel.components['test_accuracy'],
            result_panel.components['model_status'],
            self.root
        )
            
    # 公共接口方法（供其他模块调用）
    
    def get_control_panel(self):
        """获取控制面板实例"""
        return self.ui_panels['control']
    
    def get_result_panel(self):
        """获取结果面板实例"""
        return self.ui_panels['result']
    
    def get_prediction_panel(self):
        """获取预测面板实例"""
        return self.ui_panels['prediction']
    
    def update_training_progress(self, progress, message):
        """更新训练进度（供训练模块调用）"""
        if self.ui_panels['control']:
            self.ui_panels['control'].update_progress(progress, message)
    
    def update_training_results(self, train_acc, test_acc, model_status, score=None):
        """更新训练结果（供训练模块调用）"""
        if self.ui_panels['result']:
            result_panel = self.ui_panels['result']
            result_panel.update_train_accuracy(train_acc)
            result_panel.update_test_accuracy(test_acc)
            result_panel.update_model_status(model_status, score)
    
    def show_prediction_result(self, result_text, color='black'):
        """显示预测结果（供预测模块调用）"""
        if self.ui_panels['prediction']:
            self.ui_panels['prediction'].update_result(result_text, color)


# 保持原有的便捷函数（向后兼容）


def create_gui():
    """创建GUI - 使用模块化UI组件"""
    root = ctk.CTk()
    gui_manager = MainGUIManager(root)
    gui_manager.create_gui_components()
    return root


if __name__ == "__main__":
    root = create_gui()
    root.mainloop()