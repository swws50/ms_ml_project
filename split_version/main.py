# main.py - 使用UI组件的主程序（渐进式升级）

# ========== 标准库导入 ==========
import os

# ========== 第三方库导入 ==========
import customtkinter as ctk
from tkinter import filedialog, messagebox

# ========== 本地模块导入 ==========
from config import MODEL_CONFIGS, DEFAULT_MODEL
from utils import log_message, clear_log, set_global_widgets
from data_processing import open_data_file, select_and_process_files_intelligent
from model_training import TrainingUI
from model_predictor import PredictionManager
from help_system import HelpSystem
from visualization import reset_analysis
import data_store
# 导入新的UI组件
from ui_components import (
    ControlPanel, ResultPanel, PredictionPanel, 
    VisualizationPanel, InfoPanel
)


class MainGUIManager:
    """主界面管理器类 - 使用模块化UI组件"""
    
    def __init__(self, root):
        self.root = root
        self.help_system = None
        self.exact_selection = DEFAULT_MODEL
        
        # 业务逻辑管理器
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
        # === 创建顶部菜单栏（保持原样）===
        self._create_menu_bar()
        
        # === 创建进度指示器 ===
        self.help_system.create_progress_indicator(self.root, row=1, column=0, columnspan=3)
        
        # === 配置网格权重 ===
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        
        # === 使用UI组件创建面板 ===
        self._create_ui_panels()
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        self.menu_frame = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, columnspan=3, sticky='ew', padx=0, pady=0)
        
        menu_container = ctk.CTkFrame(self.menu_frame, fg_color="transparent")
        menu_container.pack(side="left", padx=20, pady=15)
        
        # 数据预处理按钮
        data_btn = ctk.CTkButton(menu_container, text="数据预处理", width=120, height=35,
                                command=lambda: open_folder_classification_window(self.root))
        data_btn.pack(side="left", padx=5)
        
        # 项目管理按钮
        project_btn = ctk.CTkButton(menu_container, text="重置进度", width=100, height=35,
                                command=lambda: reset_analysis(self.help_system))
        project_btn.pack(side="left", padx=5)
        
        # 帮助按钮
        help_btn = ctk.CTkButton(menu_container, text="使用向导", width=100, height=35,
                                command=self.help_system.show_wizard)
        help_btn.pack(side="left", padx=5)
        
    def _create_ui_panels(self):
        """使用UI组件创建各个面板"""
        
        # === 1. 控制面板 ===
        control_callbacks = {
            'on_file_select': self.handle_file_select,
            'on_model_select': self.handle_model_select,
            'on_start_training': self.handle_start_training
        }
        self.ui_panels['control'] = ControlPanel(self.root, self.help_system, control_callbacks)
        self.ui_panels['control'].create_panel(row=2, column=0)
        
        # === 2. 结果面板 ===
        self.ui_panels['result'] = ResultPanel(self.root, self.help_system)
        self.ui_panels['result'].create_panel(row=2, column=1)
        
        # === 3. 预测面板 ===
        prediction_callbacks = {
            'on_predict_file': self.handle_predict_file,
            'on_model_info': self.handle_model_info,
        }
        self.ui_panels['prediction'] = PredictionPanel(self.root, self.help_system, prediction_callbacks)
        self.ui_panels['prediction'].create_panel(row=2, column=2)
        
        # === 4. 可视化面板 ===
        self.ui_panels['visualization'] = VisualizationPanel(self.root, self.help_system)
        self.ui_panels['visualization'].create_panel(row=3, column=0, columnspan=2)
        
        # === 5. 信息面板 ===
        self.ui_panels['info'] = InfoPanel(self.root, self.help_system)
        self.ui_panels['info'].create_panel(row=3, column=2)
    
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
    
    # ========== 业务逻辑处理方法 ==========
    
    def handle_file_select(self):
        """处理文件选择"""
        # 获取控制面板的组件引用
        control_panel = self.ui_panels['control']
        
        # 调用原有的数据处理逻辑
        row, column, df = open_data_file(
            control_panel.components['file_status'],  # 传递状态标签
            control_panel.components['start_button'], # 传递训练按钮
            control_panel.components['progress_bar']  # 传递进度条
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
    
    def handle_start_training(self):
        """处理开始训练"""
        control_panel = self.ui_panels['control']
        result_panel = self.ui_panels['result']
        
        # 重置结果显示
        result_panel.reset_results()
        
        # 使用训练UI进行训练
        self.training_ui.train_with_ui_feedback(
            self.exact_selection,
            control_panel.components['progress_label'],
            control_panel.components['progress_bar'],
            result_panel.components['train_accuracy'],
            result_panel.components['test_accuracy'],
            result_panel.components['model_status'],
            self.root
        )
    
    def handle_predict_file(self):
        """处理文件预测"""
        prediction_panel = self.ui_panels['prediction']
        self.prediction_manager.open_file_dialog(prediction_panel.components['result_label'])
    
    def handle_model_info(self):
        """处理模型信息查看"""
        self.prediction_manager.show_model_info_window(self.root)
    
    
    # ========== 公共接口方法（供其他模块调用）==========
    
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


# ========== 保持原有的便捷函数（向后兼容）==========

def select_folder_for_classification():
    """选择文件夹并扫描txt文件"""
    folder_path = filedialog.askdirectory(title="选择类别文件夹")
    if folder_path:
        txt_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith('.txt'):
                txt_files.append(os.path.join(folder_path, file))
        return folder_path, txt_files
    return None, []

def open_folder_classification_window(root, is_intelligent_mode=False):
    """打开文件夹分类窗口"""
    # 创建新窗口
    classification_window = ctk.CTkToplevel(root)
    classification_window.title("数据文件分类设置")
    
    # 计算居中位置
    window_width = 700
    window_height = 750
    screen_width = classification_window.winfo_screenwidth()
    screen_height = classification_window.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)  
    
    # 设置窗口位置和大小
    classification_window.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
    classification_window.resizable(True, True)
    
    # 窗口置顶和焦点设置
    classification_window.attributes('-topmost', True)
    classification_window.focus_force()
    classification_window.lift()
    classification_window.grab_set()  # 模态窗口
    classification_window.after(1000, lambda: classification_window.attributes('-topmost', False))
    
    # 存储分类信息的变量
    class_0_folder = ctk.StringVar(value="")
    class_1_folder = ctk.StringVar(value="")
    class_0_name = ctk.StringVar(value="class 0")
    class_1_name = ctk.StringVar(value="class 1")
    class_0_files = []
    class_1_files = []
    
    # === 标题 ===
    title_label = ctk.CTkLabel(classification_window, 
                              text="数据文件分类设置", 
                              font=ctk.CTkFont(size=16, weight="bold"))
    title_label.pack(pady=10)
    
    # === 类别名称设置区域 ===
    name_frame = ctk.CTkFrame(classification_window)
    name_frame.pack(fill='x', padx=20, pady=10)
    
    ctk.CTkLabel(name_frame, text="类别名称设置（可手动更改命名）:", 
                font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=5)
    
    name_input_frame = ctk.CTkFrame(name_frame, fg_color="transparent")
    name_input_frame.pack(fill='x', padx=10, pady=5)
    
    # 类别0名称
    ctk.CTkLabel(name_input_frame, text="类别0:").pack(side='left', padx=5)
    class_0_entry = ctk.CTkEntry(name_input_frame, textvariable=class_0_name, width=120)
    class_0_entry.pack(side='left', padx=5)
    
    ctk.CTkLabel(name_input_frame, text="类别1:").pack(side='left', padx=(20, 5))
    class_1_entry = ctk.CTkEntry(name_input_frame, textvariable=class_1_name, width=120)
    class_1_entry.pack(side='left', padx=5)
    
    # === 文件夹选择区域 ===
    folder_frame = ctk.CTkFrame(classification_window)
    folder_frame.pack(fill='x', padx=20, pady=10)
    
    ctk.CTkLabel(folder_frame, text="文件夹选择:", 
                font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=5)
    
    # 类别0文件夹选择
    class_0_folder_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
    class_0_folder_frame.pack(fill='x', padx=10, pady=5)
    
    ctk.CTkLabel(class_0_folder_frame, text="📁 类别0文件夹:").pack(anchor='w')
    
    class_0_path_frame = ctk.CTkFrame(class_0_folder_frame, fg_color="transparent")
    class_0_path_frame.pack(fill='x', pady=2)
    
    class_0_path_label = ctk.CTkLabel(class_0_path_frame, text="未选择", 
                                     font=ctk.CTkFont(size=10), text_color="gray")
    class_0_path_label.pack(side='left')
    
    class_0_count_label = ctk.CTkLabel(class_0_path_frame, text="", 
                                      font=ctk.CTkFont(size=10), text_color="blue")
    class_0_count_label.pack(side='right')
    
    def select_class_0_folder():
        nonlocal class_0_files
        folder_path, txt_files = select_folder_for_classification()
        if folder_path:
            class_0_folder.set(folder_path)
            class_0_files = txt_files
            class_0_path_label.configure(text=f"路径: {folder_path}")
            class_0_count_label.configure(text=f"找到: {len(txt_files)} 个 .txt 文件")
            update_preview()
    
    ctk.CTkButton(class_0_folder_frame, text="选择文件夹...", 
                 command=select_class_0_folder, width=120).pack(anchor='w', pady=2)
    
    # 类别1文件夹选择
    class_1_folder_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
    class_1_folder_frame.pack(fill='x', padx=10, pady=5)
    
    ctk.CTkLabel(class_1_folder_frame, text="📁 类别1文件夹:").pack(anchor='w')
    
    class_1_path_frame = ctk.CTkFrame(class_1_folder_frame, fg_color="transparent")
    class_1_path_frame.pack(fill='x', pady=2)
    
    class_1_path_label = ctk.CTkLabel(class_1_path_frame, text="未选择", 
                                     font=ctk.CTkFont(size=10), text_color="gray")
    class_1_path_label.pack(side='left')
    
    class_1_count_label = ctk.CTkLabel(class_1_path_frame, text="", 
                                      font=ctk.CTkFont(size=10), text_color="blue")
    class_1_count_label.pack(side='right')
    
    def select_class_1_folder():
        nonlocal class_1_files
        folder_path, txt_files = select_folder_for_classification()
        if folder_path:
            class_1_folder.set(folder_path)
            class_1_files = txt_files
            class_1_path_label.configure(text=f"路径: {folder_path}")
            class_1_count_label.configure(text=f"找到: {len(txt_files)} 个 .txt 文件")
            update_preview()
    
    ctk.CTkButton(class_1_folder_frame, text="选择文件夹...", 
                 command=select_class_1_folder, width=120).pack(anchor='w', pady=2)
    
    # === 预览区域 ===
    preview_frame = ctk.CTkFrame(classification_window)
    preview_frame.pack(fill='both', expand=True, padx=20, pady=10)
    
    ctk.CTkLabel(preview_frame, text="预览:", 
                font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=5)
    
    preview_text = ctk.CTkTextbox(preview_frame, height=120)
    preview_text.pack(fill='both', expand=True, padx=10, pady=5)
    
    def update_preview():
        """更新预览信息"""
        preview_text.delete("1.0", "end")
        
        if class_0_files:
            file_names = [os.path.basename(f) for f in class_0_files[:5]]
            preview_text.insert("end", f"{class_0_name.get()} ({len(class_0_files)}个文件):\n")
            preview_text.insert("end", f"  {', '.join(file_names)}")
            if len(class_0_files) > 5:
                preview_text.insert("end", f"... 还有{len(class_0_files)-5}个文件")
            preview_text.insert("end", "\n\n")
        
        if class_1_files:
            file_names = [os.path.basename(f) for f in class_1_files[:5]]
            preview_text.insert("end", f"{class_1_name.get()} ({len(class_1_files)}个文件):\n")
            preview_text.insert("end", f"  {', '.join(file_names)}")
            if len(class_1_files) > 5:
                preview_text.insert("end", f"... 还有{len(class_1_files)-5}个文件")
            preview_text.insert("end", "\n\n")
        
        if not class_0_files and not class_1_files:
            preview_text.insert("end", "请选择文件夹以预览分类结果")
    
    # 绑定名称变化事件
    class_0_name.trace('w', lambda *args: update_preview())
    class_1_name.trace('w', lambda *args: update_preview())
    
    # === 底部按钮 ===
    button_frame = ctk.CTkFrame(classification_window, fg_color="transparent")
    button_frame.pack(fill='x', padx=20, pady=10)
    
    def cancel_classification():
        """取消分类"""
        classification_window.grab_release()
        classification_window.destroy()
    
    def confirm_classification():
        """确认分类并开始处理"""
        if not class_0_files and not class_1_files:
            messagebox.showwarning("警告", "请至少选择一个文件夹")
            return
        
        if not class_0_files:
            response = messagebox.askyesno("确认", "类别0没有文件，是否继续？")
            if not response:
                return
        
        if not class_1_files:
            response = messagebox.askyesno("确认", "类别1没有文件，是否继续？")
            if not response:
                return
        
        # 保存分类信息到data_store
        classification_data = {
            'class_0_name': class_0_name.get(),
            'class_1_name': class_1_name.get(),
            'class_0_files': class_0_files,
            'class_1_files': class_1_files
        }
        
        data_store.set_file_classification(classification_data)
        
        log_message(f"文件分类完成: {class_0_name.get()}({len(class_0_files)}个), {class_1_name.get()}({len(class_1_files)}个)")
        
        # 关闭分类窗口
        classification_window.grab_release()
        classification_window.destroy()

        select_and_process_files_intelligent(root)
    
    ctk.CTkButton(button_frame, text="取消", command=cancel_classification, width=100).pack(side='left')
    ctk.CTkButton(button_frame, text="开始处理", command=confirm_classification, width=120).pack(side='right')
    
    # 初始化预览
    update_preview()
    
    # 窗口关闭处理
    def on_closing():
        classification_window.grab_release()
        classification_window.destroy()
    
    classification_window.protocol("WM_DELETE_WINDOW", on_closing)


def create_gui():
    """创建GUI - 使用模块化UI组件"""
    root = ctk.CTk()
    gui_manager = MainGUIManager(root)
    gui_manager.create_gui_components()
    return root


if __name__ == "__main__":
    root = create_gui()
    root.mainloop()