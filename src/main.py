# main.py - 使用UI组件的主程序（渐进式升级）

# 标准库导入 
import os

# 第三方库导入 
import customtkinter as ctk
from tkinter import filedialog, messagebox,PhotoImage, simpledialog

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

class MainGUIManager:
    """主界面管理器类 - 使用模块化UI组件"""
    
    def __init__(self, root):
        self.root = root
        self.root.gui_manager = self
        self.help_system = None
        self.exact_selection = DEFAULT_MODEL

        self._operation_cancelled = False  # 简单的终止标志

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
        """创建菜单栏"""
        self.menu_frame = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, columnspan=4, sticky='ew', padx=0, pady=0)
        
        menu_container = ctk.CTkFrame(self.menu_frame, fg_color="transparent")
        menu_container.pack(side="left", padx=20, pady=15)
        
        # 将重置按钮改为动态按钮
        self.action_btn = ctk.CTkButton(
            menu_container, 
            text="重置进度", 
            width=100, 
            height=35,
            command=self._handle_action_button
        )
        self.action_btn.pack(side="left", padx=5)
        
        self._is_operation_running = False

        # 归一化开关（替换按钮）
        self.normalize_switch = ctk.CTkSwitch(
            menu_container, text="归一化", width=80,
            command=self._toggle_normalization
        )
        self.normalize_switch.pack(side="left", padx=5)
        self.normalize_switch.select()  # 默认开启

        project_btn = ctk.CTkButton(menu_container, text="项目管理", width=100, height=35,
                           command=self._show_project_manager)
        project_btn.pack(side="left", padx=5)
        
        # 新增：打印按钮
        print_btn = ctk.CTkButton(menu_container, text="打印报告", width=100, height=35,
                                command=self.handle_print_report)
        print_btn.pack(side="left", padx=5)

        # 帮助按钮
        help_btn = ctk.CTkButton(menu_container, text="使用向导", width=100, height=35,
                                command=self.help_system.show_wizard)
        help_btn.pack(side="left", padx=5)

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
                    self.root.after(1000, self.handle_reset_progress)
            # 如果是禁用状态就不响应
        else:
            # 非运行时作为重置按钮
            self.handle_reset_progress()

    def _toggle_normalization(self):
        """切换归一化状态"""
        new_state = self.normalize_switch.get()
        data_store.set_normalization_enabled(new_state)
        status = "启用" if new_state else "禁用"
        log_message(f"归一化已{status}")
        self.ui_panels['control'].update_normalization_status()
        self.ui_panels['prediction'].update_normalization_status()

    def _detect_normalization_factor(self, df):
        """检测归一化因子"""

        if data_store.is_normalization_enabled():
            # 归一化模式：必须有归一化因子
            factor = data_store.get_normalization_factor()
            if factor is None:
                log_message("归一化模式下无法获取归一化因子，请先进行数据预处理", "ERROR")
                raise ValueError("归一化模式下无法获取归一化因子，请先进行数据预处理")
            log_message(f"归一化模式：使用归一化因子 {factor:.2f}", "INFO")
            return factor
        else:
            # 非归一化模式：不需要归一化因子
            log_message("非归一化模式：使用原始强度值", "INFO")
            return None  # 返回None表示不需要归一化
            
    def handle_print_report(self):
        """处理打印报告"""
        self.print_manager.show_print_dialog(self.root)

    def _show_project_manager(self):
        """显示项目管理对话框"""
        ProjectManagerDialog(self.root, self)

    def _refresh_project_status(self):
        """刷新项目状态显示"""
        from output_manager import output_manager
        current_project = output_manager.get_current_project()
        log_message(f"当前项目: {current_project}")
                
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
    
    
    def handle_model_info(self):
        """处理模型信息查看"""
        prediction_panel = self.ui_panels['prediction']
        selected_model_path = prediction_panel.current_model_selection
        
        if selected_model_path and selected_model_path != "自动检测":
            self.prediction_manager.show_model_info_window(self.root, model_path=selected_model_path)
        else:
            self.prediction_manager.show_model_info_window(self.root)
        
    def handle_reset_progress(self):
        """完整重置到初始状态 - 修复TclError问题"""

        # 设置取消标志
        self._operation_cancelled = True
        
        try:
            log_message("开始重置系统...", "INFO")
            
            # 0. 先重置按钮状态，避免UI锁死问题
            self._is_operation_running = False
            self.action_btn.configure(text="重置进度", state="normal")
            
            # 1. 安全销毁可视化面板 - 添加存在性检查
            try:
                if hasattr(self, 'ui_panels') and 'visualization' in self.ui_panels:
                    viz_panel = self.ui_panels['visualization']
                    if viz_panel and hasattr(viz_panel, 'frame') and viz_panel.frame.winfo_exists():
                        viz_panel.frame.destroy()
            except Exception as e:
                log_message(f"销毁可视化面板时出错: {e}", "WARNING")
            
            # 2. 强制更新UI，确保销毁操作完成
            self.root.update_idletasks()
            
            # 3. 重置数据存储
            data_store.clear_all_data()
            
            # 4. 重置帮助系统进度
            for step in self.help_system.steps:
                step['completed'] = False
            self.help_system.current_step_index = 0
            self.help_system.update_progress_display()
            self.help_system.hide_all_tips()

            # 5. 重置UI面板
            self.ui_panels['result'].reset_results()
            self.ui_panels['prediction'].update_result("状态：等待选择文件")
            self.ui_panels['prediction'].reset_model_selection()
            self.ui_panels['control'].update_file_status("文件未选择")
            self.ui_panels['control'].enable_training(False)
            self.ui_panels['control'].components['model_menu'].set(DEFAULT_MODEL)
            self.ui_panels['control'].current_model = DEFAULT_MODEL
            self.ui_panels['preprocessing'].update_status("等待开始预处理")
            self.normalize_switch.select()  # 重置为开启状态
            data_store.set_normalization_enabled(True)  # 重置data_store状态
            self.ui_panels['control'].update_normalization_status()
            self.ui_panels['prediction'].update_normalization_status()
            
            # 6. 重新创建可视化面板
            try:
                self.ui_panels['visualization'] = VisualizationPanel(self.root, self.help_system)
                self.ui_panels['visualization'].create_panel(row=4, column=0, rowspan=2, columnspan=3)
                self.root.visualization_container = self.ui_panels['visualization'].get_container()
                self.root.visualization_placeholder = self.ui_panels['visualization'].get_placeholder()
            except Exception as e:
                log_message(f"重新创建可视化面板时出错: {e}", "ERROR")
            
            # 7. 隐藏进度条并重置模型选择
            self.hide_global_progress()
            self.exact_selection = DEFAULT_MODEL
            clear_log()
            
            self._operation_cancelled = False
            log_message("系统已完全重置", "SUCCESS")
        
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

class ProjectManagerDialog:
    """项目管理对话框"""
    
    def __init__(self, parent, gui_manager):
        self.parent = parent
        self.gui_manager = gui_manager
        
        # 创建对话框窗口
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("项目管理")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
        
        self._create_dialog_content()
        self._refresh_project_list()
    
    def _create_dialog_content(self):
        """创建对话框内容"""
        # 标题
        title_label = ctk.CTkLabel(self.dialog, text="项目管理", 
                                  font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=10)
        
        # 当前项目显示
        from output_manager import output_manager
        current_project = output_manager.get_current_project()
        self.current_label = ctk.CTkLabel(self.dialog, 
                                         text=f"当前项目: {current_project}",
                                         font=ctk.CTkFont(size=12, weight="bold"),
                                         text_color="blue")
        self.current_label.pack(pady=5)
        
        # 按钮框架
        button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        button_frame.pack(pady=10)
        
        # 创建项目按钮
        create_btn = ctk.CTkButton(button_frame, text="创建项目", 
                                  command=self._create_project)
        create_btn.pack(side="left", padx=5)
        
        # 切换项目按钮
        switch_btn = ctk.CTkButton(button_frame, text="切换项目", 
                                  command=self._switch_project)
        switch_btn.pack(side="left", padx=5)
        
        # 删除项目按钮
        delete_btn = ctk.CTkButton(button_frame, text="删除项目", 
                                  command=self._delete_project)
        delete_btn.pack(side="left", padx=5)
        
        # 项目列表框架
        list_frame = ctk.CTkFrame(self.dialog)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 项目列表标题
        list_title = ctk.CTkLabel(list_frame, text="所有项目:", 
                                 font=ctk.CTkFont(size=14, weight="bold"))
        list_title.pack(pady=5)
        
        # 项目列表（使用文本框显示）
        self.project_textbox = ctk.CTkTextbox(list_frame, height=200)
        self.project_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 关闭按钮
        close_btn = ctk.CTkButton(self.dialog, text="关闭", 
                                 command=self.dialog.destroy)
        close_btn.pack(pady=10)
    
    def _refresh_project_list(self):
        """刷新项目列表显示"""
        from output_manager import output_manager
        
        # 清空文本框
        self.project_textbox.delete("1.0", "end")
        
        # 获取所有项目
        all_projects = output_manager.get_all_projects()
        current_project = output_manager.get_current_project()
        
        # 显示项目信息
        for project_name in all_projects:
            project_info = output_manager.get_project_info(project_name)
            if project_info:
                status = "[当前]" if project_info['is_current'] else "      "
                created_date = project_info.get('created_date', '未知')
                description = project_info.get('description', '无描述')
                
                # 统计文件数量
                file_counts = project_info.get('file_counts', {})
                total_files = sum(file_counts.values()) if file_counts else 0
                
                project_text = f"{status} {project_name}\n"
                project_text += f"      创建时间: {created_date}\n"
                project_text += f"      描述: {description}\n"
                project_text += f"      文件总数: {total_files}\n"
                project_text += f"      详情: data({file_counts.get('data', 0)}) "
                project_text += f"models({file_counts.get('models', 0)}) "
                project_text += f"results({file_counts.get('results', 0)}) "
                project_text += f"charts({file_counts.get('charts', 0)})\n\n"
                
                self.project_textbox.insert("end", project_text)
        
        # 更新当前项目显示
        self.current_label.configure(text=f"当前项目: {current_project}")
    
    def _create_project(self):
        """创建新项目"""
        # 获取项目名称
        project_name = simpledialog.askstring(
            "创建项目", 
            "请输入项目名称:",
            parent=self.dialog
        )
        
        if not project_name:
            return
        
        if not project_name.strip():
            messagebox.showerror("错误", "项目名称不能为空")
            return
        
        # 获取项目描述
        description = simpledialog.askstring(
            "项目描述", 
            "请输入项目描述（可选）:",
            parent=self.dialog
        ) or ""
        
        # 创建项目
        from output_manager import output_manager
        if output_manager.create_project(project_name.strip(), description.strip()):
            messagebox.showinfo("成功", f"项目 '{project_name}' 创建成功")
            self._refresh_project_list()
            self.gui_manager._refresh_project_status()
        else:
            messagebox.showerror("错误", f"项目 '{project_name}' 已存在")
    
    def _switch_project(self):
        """切换项目"""
        from output_manager import output_manager
        
        all_projects = output_manager.get_all_projects()
        if len(all_projects) <= 1:
            messagebox.showinfo("提示", "只有一个项目，无需切换")
            return
        
        # 创建项目选择对话框
        selection_dialog = ProjectSelectionDialog(self.dialog, all_projects, "选择要切换的项目")
        self.dialog.wait_window(selection_dialog.dialog)
        
        if selection_dialog.selected_project:
            selected_project = selection_dialog.selected_project
            if output_manager.switch_project(selected_project):
                messagebox.showinfo("成功", f"已切换到项目 '{selected_project}'")
                self._refresh_project_list()
                self.gui_manager._refresh_project_status()
    
    def _delete_project(self):
        """删除项目"""
        from output_manager import output_manager
        
        all_projects = output_manager.get_all_projects()
        if len(all_projects) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个项目")
            return
        
        # 选择要删除的项目
        selection_dialog = ProjectSelectionDialog(self.dialog, all_projects, "选择要删除的项目")
        self.dialog.wait_window(selection_dialog.dialog)
        
        if selection_dialog.selected_project:
            selected_project = selection_dialog.selected_project
            
            # 确认删除
            response = messagebox.askyesnocancel(
                "确认删除", 
                f"确定要删除项目 '{selected_project}' 吗？\n\n"
                "选择:\n"
                "是 - 删除项目配置和所有文件\n"
                "否 - 仅删除项目配置，保留文件\n"
                "取消 - 不删除"
            )
            
            if response is not None:  # 用户没有选择取消
                delete_files = response  # True=删除文件，False=保留文件
                
                if output_manager.delete_project(selected_project, delete_files):
                    action = "及文件" if delete_files else "配置"
                    messagebox.showinfo("成功", f"项目 '{selected_project}' 的{action}已删除")
                    self._refresh_project_list()
                    self.gui_manager._refresh_project_status()


class ProjectSelectionDialog:
    """项目选择对话框"""
    
    def __init__(self, parent, projects, title="选择项目"):
        self.parent = parent
        self.projects = projects
        self.selected_project = None
        set_window_icon(self.parent)
        # 创建对话框
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (250 // 2)
        self.dialog.geometry(f"300x250+{x}+{y}")
        
        self._create_content()
    
    def _create_content(self):
        """创建对话框内容"""
        # 标题
        title_label = ctk.CTkLabel(self.dialog, text="请选择项目:", 
                                  font=ctk.CTkFont(size=14, weight="bold"))
        title_label.pack(pady=10)
        
        # 项目选择菜单
        self.project_var = ctk.StringVar(value=self.projects[0])
        self.project_menu = ctk.CTkOptionMenu(self.dialog, 
                                             values=self.projects,
                                             variable=self.project_var,
                                             width=200)
        self.project_menu.pack(pady=10)
        
        # 按钮框架
        button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        button_frame.pack(pady=20)
        
        # 确认按钮
        confirm_btn = ctk.CTkButton(button_frame, text="确认", 
                                   command=self._confirm_selection)
        confirm_btn.pack(side="left", padx=10)
        
        # 取消按钮
        cancel_btn = ctk.CTkButton(button_frame, text="取消", 
                                  command=self._cancel_selection)
        cancel_btn.pack(side="left", padx=10)
    
    def _confirm_selection(self):
        """确认选择"""
        self.selected_project = self.project_var.get()
        self.dialog.destroy()
    
    def _cancel_selection(self):
        """取消选择"""
        self.selected_project = None
        self.dialog.destroy()

if __name__ == "__main__":
    root = ctk.CTk()
    gui_manager = MainGUIManager(root)
    root.mainloop()