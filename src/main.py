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
import data_store
# 导入新的UI组件
from ui_components import (
    ControlPanel, ResultPanel, PredictionPanel, 
    VisualizationPanel, InfoPanel, PreprocessingPanel
)
from data_preprocessor import  DataPreprocessor
from ui_components import ProgressComponent
from print_manager import PrintManager
# 在现有导入后添加
from project_manager import ProjectManager
from automated_workflow import AutomatedWorkflow
from parameter_tuning_window import ParameterTuningWindow
from data_store import class_manager

class MainGUIManager:
    """主界面管理器类 - 使用模块化UI组件"""
    
    def __init__(self, root):
        self.root = root
        self.root.gui_manager = self
        self.help_system = None
        self.exact_selection = DEFAULT_MODEL
        self.project_manager = ProjectManager()
        self._operation_cancelled = False  # 简单的终止标志

        self.automated_workflow = AutomatedWorkflow(self)

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

        # 全局GUI组件
        self._setup_window()
        self._init_managers()
        self._create_layout()
        self._finalize_setup()
    
    def _setup_window(self):
        """设置窗口基本属性"""
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("dark-blue")
        self.root.title('DETEQX')
        
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
        """创建新的4x4网格布局"""
        # 配置主窗口网格权重 - 4列4行
        self.root.grid_rowconfigure(0, weight=0)    # 菜单栏
        self.root.grid_rowconfigure(1, weight=0)    # 进度指示器  
        self.root.grid_rowconfigure(2, weight=0)    # 主要面板行 - 减小权重
        self.root.grid_rowconfigure(3, weight=0)    # 进度条行
        self.root.grid_rowconfigure(4, weight=1)    # 可视化和日志行 - 增加权重
        self.root.grid_rowconfigure(5, weight=0)    # 额外行，

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_columnconfigure(3, weight=1)

        # 创建各个组件
        self._create_menu_bar()                    # row=0
        self.help_system.create_progress_indicator(self.root, row=1, column=0, columnspan=4)  # row=1
        self._create_ui_panels()                   # row=2,4
        self._create_global_progress()             # row=3

    def _create_global_progress(self):
        """创建全局进度组件"""
        # 进度容器放在row=3
        self.progress_container = ctk.CTkFrame(self.root, fg_color="transparent", height=25)
        self.progress_container.grid(row=3, column=0, columnspan=3, sticky='ew', padx=20, pady=2)  # 只跨3列
        self.progress_container.grid_columnconfigure(0, weight=1)
        
        self.global_progress = ProgressComponent(self.progress_container, width=200, show_label=True)
        self.global_progress.create(row=0, column=0, sticky='ew', padx=0, pady=0)
        self.global_progress.hide()
            
    def _create_menu_bar(self):
        """创建传统tkinter菜单栏"""
        from tkinter import Menu, BooleanVar
        
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # 项目管理菜单
        project_menu = Menu(menubar, tearoff=0)
        project_menu.configure(
            font=("Microsoft YaHei UI", 14),
            bg='#f0f0f0',
            activebackground='#0078d4',
            activeforeground='white',
            borderwidth=2,
            relief='raised'
        )
        menubar.add_cascade(label="文件", menu=project_menu)
        project_menu.add_command(
            label="\n打开项目管理\n",
            command=lambda: self.project_manager.show_manager_dialog(self.root)
        )

        # 自动化流程菜单
        auto_menu = Menu(menubar, tearoff=0)
        auto_menu.configure(
            font=("Microsoft YaHei UI", 14),
            bg='#f0f0f0',
            activebackground='#0078d4',
            activeforeground='white',
            borderwidth=2,
            relief='raised'
        )
        menubar.add_cascade(label="自动化", menu=auto_menu)
        auto_menu.add_command(
            label="\n启动自动化流程\n",
            command=self.automated_workflow.start_workflow
        )
        
        # 重置/终止菜单
        action_menu = Menu(menubar, tearoff=0)
        action_menu.configure(
            font=("Microsoft YaHei UI", 14),
            bg='#f0f0f0',
            activebackground='#0078d4',
            activeforeground='white',
            borderwidth=2,
            relief='raised'
        )
        menubar.add_cascade(label="重置", menu=action_menu)
        action_menu.add_command(
            label="\n重置进度/终止训练\n",
            command=self._handle_action_button
        )
        
        # 类别设置菜单
        class_menu = Menu(menubar, tearoff=0)
        class_menu.configure(
            font=("Microsoft YaHei UI", 14),
            bg='#f0f0f0',
            activebackground='#0078d4',
            activeforeground='white',
            borderwidth=2,
            relief='raised'
        )
        menubar.add_cascade(label="类别", menu=class_menu)
        class_menu.add_command(
            label="查看\设置类别名称",
            command=self._show_class_settings_dialog
        )

        # 专业菜单（合并归一化和参数调优）
        pro_menu = Menu(menubar, tearoff=0)
        pro_menu.configure(
            font=("Microsoft YaHei UI", 14),
            bg='#f0f0f0',
            activebackground='#0078d4',
            activeforeground='white',
            borderwidth=2,
            relief='raised'
        )
        menubar.add_cascade(label="专业", menu=pro_menu)
        
        # 参数调优子菜单项
        pro_menu.add_command(
            label="\n打开参数调优\n",
            command=self.handle_parameter_tuning
        )
        
        
        # 打印报告菜单
        print_menu = Menu(menubar, tearoff=0)
        print_menu.configure(
            font=("Microsoft YaHei UI", 14),
            bg='#f0f0f0',
            activebackground='#0078d4',
            activeforeground='white',
            borderwidth=2,
            relief='raised'
        )
        menubar.add_cascade(label="打印", menu=print_menu)
        print_menu.add_command(
            label="\n生成打印报告\n",
            command=self.handle_print_report
        )
        
        # 使用向导菜单
        help_menu = Menu(menubar, tearoff=0)
        help_menu.configure(
            font=("Microsoft YaHei UI", 14),
            bg='#f0f0f0',
            activebackground='#0078d4',
            activeforeground='white',
            borderwidth=2,
            relief='raised'
        )
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(
            label="\n打开使用向导\n",
            command=self.help_system.show_wizard
        )
        
        self._is_operation_running = False
        self.action_btn = None

        # 创建隐藏的虚拟按钮以保持兼容性
        self.action_btn = ctk.CTkButton(self.root, text="")
        # 不要grid或pack，让它隐藏

    def _handle_action_button(self):
        """处理动态按钮点击"""
        if self._is_operation_running:
            # 只有显示"终止训练"时才能终止
            if self.action_btn.cget("text") == "终止训练":
                response = messagebox.askyesno("确认终止", "确定要终止训练吗？\n终止后将自动重置系统。")
                if response:
                    self._operation_cancelled = True
                    self.action_btn.configure(state="disabled")  # 禁用防止重复点击
                    log_message("用户请求终止训练", "WARNING")
                    self.root.after(1500, self.handle_reset_progress)
            # 如果是禁用状态就不响应
        else:
            # 非运行时作为重置按钮
            self.handle_reset_progress()

    def _show_class_settings_dialog(self):
        """显示类别名称设置对话框"""
        from data_store import class_manager
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("类别名称设置")
        dialog.geometry("360x220")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 360) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 220) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 设置图标
        set_window_icon(dialog)
        
        # 标题
        ctk.CTkLabel(
            dialog, 
            text="设置类别名称", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 10))
        
        # 输入区域
        input_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        input_frame.pack(fill='x', padx=20, pady=10)
        
        # 类别0
        ctk.CTkLabel(input_frame, text="类别 0 (阳性):").grid(row=0, column=0, sticky='e', padx=5, pady=8)
        class_0_var = ctk.StringVar(value=class_manager.class_0_name)
        class_0_entry = ctk.CTkEntry(input_frame, textvariable=class_0_var, width=180)
        class_0_entry.grid(row=0, column=1, padx=5, pady=8)
        
        # 类别1
        ctk.CTkLabel(input_frame, text="类别 1 (阴性):").grid(row=1, column=0, sticky='e', padx=5, pady=8)
        class_1_var = ctk.StringVar(value=class_manager.class_1_name)
        class_1_entry = ctk.CTkEntry(input_frame, textvariable=class_1_var, width=180)
        class_1_entry.grid(row=1, column=1, padx=5, pady=8)
        
        # 按钮区域
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill='x', padx=20, pady=15)
        
        def save_and_close():
            c0 = class_0_var.get().strip()
            c1 = class_1_var.get().strip()
            if c0 and c1:
                class_manager.set_names(c0, c1)
                log_message(f"类别名称已更新: {c0} / {c1}", "SUCCESS")
                dialog.destroy()
            else:
                messagebox.showwarning("警告", "类别名称不能为空", parent=dialog)
        
        ctk.CTkButton(btn_frame, text="取消", width=80, command=dialog.destroy).pack(side='left')
        ctk.CTkButton(btn_frame, text="保存", width=80, command=save_and_close).pack(side='right')
                
    def handle_print_report(self):
        """处理打印报告"""
        self.print_manager.show_print_dialog(self.root)

    def handle_parameter_tuning(self):
        """处理参数调优"""
        current_model = self.ui_panels['control'].current_model or DEFAULT_MODEL
        tuning_window = ParameterTuningWindow(self.root, current_model)
        self.root.wait_window(tuning_window)
                
    def _create_ui_panels(self):
        """创建新网格布局的UI面板"""
        #第2行：预处理、控制、结果、预测（上半部分）
        preprocessing_callbacks = {
            'on_start_preprocessing': self._handle_preprocessing_start
        }
        self.ui_panels['preprocessing'] = PreprocessingPanel(self.root, self.help_system, preprocessing_callbacks)
        self.ui_panels['preprocessing'].create_panel(row=2, column=0)

        control_callbacks = {
            'on_file_select': self.handle_file_select,
            'on_model_select': self.handle_model_select,
            'on_start_training': self.handle_start_training
        }
        self.ui_panels['control'] = ControlPanel(self.root, self.help_system, control_callbacks)
        self.ui_panels['control'].create_panel(row=2, column=1)
        
        self.ui_panels['result'] = ResultPanel(self.root, self.help_system)
        self.ui_panels['result'].create_panel(row=2, column=2)
        
        prediction_callbacks = {
            'on_predict_file': self.handle_predict_file,
            'on_model_info': self.handle_model_info,
        }
        self.ui_panels['prediction'] = PredictionPanel(self.root, self.help_system, prediction_callbacks)
        self.ui_panels['prediction'].create_panel(row=2, column=3, rowspan=3)  # 跨2行
        
        # 第4行：可视化（3列）+ 日志（1列）
        self.ui_panels['visualization'] = VisualizationPanel(self.root, self.help_system)
        self.ui_panels['visualization'].create_panel(row=4, column=0, rowspan=2, columnspan=3)
        
         # 第5行：信息面板（1列）
         # 信息面板放在第5行第4列
        
        self.ui_panels['info'] = InfoPanel(self.root, self.help_system)
        self.ui_panels['info'].create_panel(row=5, column=3)
    
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
        control_panel = self.ui_panels['control']
        
        # 调用数据加载（不再传递UI组件）
        row, column, df, file_path = open_data_file()

        if row is not None and column is not None:
            # 存储数据
            data_store.set_training_data(row, column, df)
            log_message("训练数据已加载到数据存储模块", "SUCCESS")
            
            # 统一更新UI状态
            filename = os.path.basename(file_path)
            control_panel.update_file_status(f"已选择: {filename}")
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
    
    
    def handle_model_info(self):
        """处理模型信息查看"""
        prediction_panel = self.ui_panels['prediction']
        selected_model_path = prediction_panel.current_model_selection
        
        if selected_model_path and selected_model_path != "自动检测":
            self.prediction_manager.show_model_info_window(self.root, model_path=selected_model_path)
        else:
            self.prediction_manager.show_model_info_window(self.root)
        
    def handle_reset_progress(self):
        """完整重置到初始状态 - 彻底修复方案"""

        # 设置取消标志
        self._operation_cancelled = True
        
        try:
            log_message("开始重置系统...", "INFO")
            
            # 0. 先重置按钮状态
            self._is_operation_running = False
            if self.action_btn:
                self.action_btn.configure(text="重置进度", state="normal")
            
            # 1. 清空可视化面板内容（不销毁）
            try:
                if hasattr(self, 'ui_panels') and 'visualization' in self.ui_panels:
                    viz_panel = self.ui_panels['visualization']
                    if viz_panel:
                        viz_panel.clear_content()  # 调用清空方法
            except Exception as e:
                log_message(f"清空可视化面板时出错: {e}", "WARNING")
            
            # 2. 重置数据存储
            data_store.clear_all_data()
            
            # 3. 重置帮助系统进度
            for step in self.help_system.steps:
                step['completed'] = False
            self.help_system.current_step_index = 0
            self.help_system.update_progress_display()
            self.help_system.hide_all_tips()

            # 4. 重置UI面板
            self.ui_panels['result'].reset_results()
            self.ui_panels['prediction'].update_result("状态：等待选择文件")
            self.ui_panels['prediction'].reset_model_selection()
            if hasattr(self, 'prediction_manager') and self.prediction_manager:
                self.prediction_manager.close_info_window()
            self.ui_panels['control'].update_file_status("文件未选择")
            self.ui_panels['control'].enable_training(False)
            self.ui_panels['control'].components['model_menu'].set(DEFAULT_MODEL)
            self.ui_panels['control'].current_model = DEFAULT_MODEL
            self.ui_panels['preprocessing'].update_status("等待开始预处理")
            
            # 5. 隐藏进度条并重置模型选择
            self.hide_global_progress()
            self.exact_selection = DEFAULT_MODEL

            # 延迟清空日志和显示完成消息（避免并发冲突）
            def finish_reset():
                clear_log()
                self._operation_cancelled = False
                log_message("系统已完全重置", "SUCCESS")

            self.root.after(300, finish_reset)
        
        except Exception as e:
            self._operation_cancelled = False
            log_message(f"重置失败: {str(e)}", "ERROR")

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

    def _set_operation_running(self, running: bool, operation_name: str = "", allow_termination: bool = False):
        """设置操作运行状态"""
        self._is_operation_running = running
        
        if running:
            if allow_termination:
                # 可终止的操作（如训练）
                self.action_btn.configure(text="终止训练", state="normal")
                log_message(f"开始{operation_name}，可点击终止按钮取消", "INFO")
            else:
                # 不可终止的操作（如预处理、预测）
                self.action_btn.configure(text="重置进度", state="disabled")
                log_message(f"开始{operation_name}，请等待完成", "INFO")
        else:
            self.action_btn.configure(text="重置进度", state="normal")
            self._operation_cancelled = False

    def _handle_preprocessing_start(self):
        """处理预处理开始 - 不支持终止"""
        self._set_operation_running(True, "数据预处理", allow_termination=False)
        
        try:
            self.show_global_progress("正在启动数据预处理...")
            self.data_preprocessor.show_classification_dialog(self.root)
        finally:
            self._set_operation_running(False)

    def handle_start_training(self):
        """处理开始训练 - 支持终止功能"""
        self._set_operation_running(True, "模型训练", allow_termination=True) 
        
        try:
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
        except InterruptedError:
            log_message("训练被终止", "WARNING")
            # 确保UI状态正确显示终止结果
            if 'result' in self.ui_panels:
                self.ui_panels['result'].components['model_status'].configure(
                    text='模型保存状态: 训练被终止', 
                    text_color='orange'
                )
        finally:
            self._set_operation_running(False)

    def handle_predict_file(self):
        """处理文件预测"""
        self._set_operation_running(True, "文件预测", allow_termination=False)
        
        try:
            prediction_panel = self.ui_panels['prediction']
            selected_model_path = prediction_panel.current_model_selection
            
            # 如果用户选择了特定模型，临时设置给预测管理器
            if selected_model_path and selected_model_path != "自动检测":
                self.prediction_manager.temp_model_path = selected_model_path
            
            # 直接调用预测管理器的方法（它已经处理了单个和批量的逻辑）
            self.prediction_manager.open_file_dialog(prediction_panel.components['result_textbox'])
            
        finally:
            # 清理临时模型路径
            if hasattr(self.prediction_manager, 'temp_model_path'):
                delattr(self.prediction_manager, 'temp_model_path')
            self._set_operation_running(False)
                            
                  
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

if __name__ == "__main__":
    
    # 直接运行登录系统
    #from login_system import SimpleLogin
    #login = SimpleLogin()
    #login.run()
    
    # 若要跳过登录，取消注释以下代码：
    root = ctk.CTk()
    gui_manager = MainGUIManager(root)
    root.mainloop()