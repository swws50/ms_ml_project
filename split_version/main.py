# main.py - 主程序入口和GUI界面（类管理升级版）

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
from model_predictor import PredictionUI
from model_info import ModelInfoDisplay
from help_system import HelpSystem
from visualization import reset_analysis
import data_store  # 直接导入，因为确定不会循环导入


class MainGUIManager:
    """主界面管理器类 - 统一管理所有UI组件"""
    
    def __init__(self, root):
        self.root = root
        self.help_system = None
        self.exact_selection = DEFAULT_MODEL
        
        self.model_info_display = None
        self.training_ui = None
        self.prediction_ui = None

        # 存储所有UI组件引用
        self.components = {
            'menu_frame': None,
            'control_frame': None,
            'result_frame': None, 
            'predict_frame': None,
            'visualization_frame': None,
            'info_frame': None,
            # 具体控件
            'normalization_label': None,
            'start_button': None,
            'progress_bar': None,
            'progress_label': None,
            'model_menu': None,
            'info_text': None,
            'prediction_result_label': None,
            'balanced_accuracy_train_label': None,
            'balanced_accuracy_test_label': None,
            'model_save_status_label': None,
            'visualization_placeholder': None
        }
    
    def on_model_selected(self, choice):
        """模型选择回调函数"""
        self.exact_selection = choice
        log_message(f"已选择模型: {self.exact_selection}")
        
        if self.help_system:
            self.help_system.advance_step("train_model")
    
    def open_data_file_wrapper(self):
        """数据文件加载包装函数"""
        # 调用数据处理函数
        row, column, df = open_data_file(
            self.components['normalization_label'], 
            self.components['start_button'], 
            self.components['progress_bar']
        )
        
        if row is not None and column is not None:
            # 将数据存储到data_store模块
            data_store.set_training_data(row, column, df)
            log_message("训练数据已加载到数据存储模块", "SUCCESS")
            
            # 推进步骤到"选择模型"
            if self.help_system:
                self.help_system.advance_step("select_model")
        else:
            log_message("数据加载失败", "ERROR")
    
    def start_training_wrapper(self):
        """训练开始包装函数"""
        self.training_ui.train_with_ui_feedback(
        self.exact_selection,
        self.components['progress_label'], 
        self.components['progress_bar'], 
        self.components['balanced_accuracy_train_label'], 
        self.components['balanced_accuracy_test_label'], 
        self.components['model_save_status_label'], 
        self.root
    )
    
    def open_file_dialog_wrapper(self):
        """文件对话框包装函数"""
        self.prediction_ui.open_file_dialog(self.components['prediction_result_label'])
    
    def create_gui_components(self):
        """ 
        创建并配置应用程序的主图形用户界面 - 类管理版本
        """
        # 设置 Customctk 主题
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("dark-blue")

        self.root.title('诊断分析')
        
        # 创建帮助系统
        self.help_system = HelpSystem(self.root)

        # 创建训练和预测系统
        self.model_info_display = ModelInfoDisplay()
        self.training_ui = TrainingUI(self.help_system)
        self.prediction_ui = PredictionUI(self.help_system)

        # 设置窗口大小和状态
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{height}+0+0")
        try:
            self.root.state('zoomed')  # Windows
        except:
            self.root.attributes('-zoomed', True)  # Linux
       
        # === 创建现代化顶部菜单栏 ===
        self.components['menu_frame'] = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        self.components['menu_frame'].grid(row=0, column=0, columnspan=3, sticky='ew', padx=0, pady=0)
        
        # 菜单按钮容器
        menu_container = ctk.CTkFrame(self.components['menu_frame'], fg_color="transparent")
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

        # 创建步骤进度指示器
        self.help_system.create_progress_indicator(self.root, row=1, column=0, columnspan=3)

        # 配置根窗口的网格权重
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        # === 创建各个面板 ===
        self._create_control_panel()
        self._create_result_panel()
        self._create_predict_panel()
        self._create_visualization_panel()
        self._create_info_panel()
        
        # 保存容器引用供visualize_performance使用
        self.root.visualization_container = self.components['visualization_frame']
        self.root.visualization_placeholder = self.components['visualization_placeholder']
        
        # 设置全局组件引用
        set_global_widgets(self.components['info_text'], self.root)

        # 初始化日志
        log_message("系统已启动，等待用户操作...")
        log_message("数据存储模块已初始化", "INFO")

        # 如果是首次运行，显示向导
        if self.help_system.show_wizard_on_startup:
            self.root.after(500, self.help_system.show_wizard)
    
    def _create_control_panel(self):
        """创建操作控制面板"""
        self.components['control_frame'] = ctk.CTkFrame(self.root, corner_radius=10)
        self.components['control_frame'].grid(row=2, column=0, sticky='nsew', padx=5, pady=5)
        
        control_title = ctk.CTkLabel(self.components['control_frame'], text="操作控制", 
                                    font=ctk.CTkFont(size=14, weight="bold"))
        control_title.grid(row=0, column=0, columnspan=2, pady=10)

        # 文件选择和模型选择
        open_button = ctk.CTkButton(self.components['control_frame'], text="选择归一化.csv文件", width=180, height=35,
            command=self.open_data_file_wrapper)
        open_button.grid(row=1, column=0, padx=10, pady=5, sticky='ew')
        self.help_system.add_hover_tip(open_button, "select_excel")

        self.components['model_menu'] = ctk.CTkOptionMenu(self.components['control_frame'], 
                                  values=list(MODEL_CONFIGS.keys()),
                                  command=self.on_model_selected, width=160, height=35)
        self.components['model_menu'].set(self.exact_selection)
        self.components['model_menu'].grid(row=2, column=0, padx=10, pady=5, sticky='ew')
        self.help_system.add_hover_tip(self.components['model_menu'], "model_selection")

        self.components['normalization_label'] = ctk.CTkLabel(self.components['control_frame'], text="文件未选择")
        self.components['normalization_label'].grid(row=1, column=1, padx=10, pady=5, sticky='w')

        model_status_label = ctk.CTkLabel(self.components['control_frame'], text=f"已选择: {self.exact_selection}")
        model_status_label.grid(row=2, column=1, padx=10, pady=5, sticky='w')

        # 训练控制
        self.components['start_button'] = ctk.CTkButton(self.components['control_frame'], text='开始分析', width=180, height=35,
            command=self.start_training_wrapper)
        self.components['start_button'].grid(row=3, column=0, padx=10, pady=5, sticky='ew')
        self.components['start_button'].configure(state='disabled')
        self.help_system.add_hover_tip(self.components['start_button'], "start_analysis")

        # 进度显示
        self.components['progress_label'] = ctk.CTkLabel(self.components['control_frame'], text='分析进度: 0%')
        self.components['progress_label'].grid(row=3, column=1, padx=10, pady=5, sticky='w')
        
        self.components['progress_bar'] = ctk.CTkProgressBar(self.components['control_frame'], width=200)
        self.components['progress_bar'].grid(row=3, column=2, padx=10, pady=5, sticky='ew')
        self.components['progress_bar'].set(0)
        self.help_system.add_hover_tip(self.components['progress_bar'], "progress")

        self.components['control_frame'].grid_columnconfigure(1, weight=1)
        self.components['control_frame'].grid_columnconfigure(3, weight=1)
    
    def _create_result_panel(self):
        """创建训练结果面板"""
        self.components['result_frame'] = ctk.CTkFrame(self.root, corner_radius=10)
        self.components['result_frame'].grid(row=2, column=1, sticky='nsew', padx=5, pady=5)
        
        result_title = ctk.CTkLabel(self.components['result_frame'], text="训练结果", 
                                   font=ctk.CTkFont(size=14, weight="bold"))
        result_title.grid(row=0, column=0, pady=10)

        self.components['balanced_accuracy_train_label'] = ctk.CTkLabel(self.components['result_frame'], 
                                                         text='平均训练集平衡精度: --')
        self.components['balanced_accuracy_train_label'].grid(row=1, column=0, padx=10, pady=5, sticky='w')
        self.help_system.add_hover_tip(self.components['balanced_accuracy_train_label'], "results")

        self.components['balanced_accuracy_test_label'] = ctk.CTkLabel(self.components['result_frame'], 
                                                        text='平均测试集平衡精度: --')
        self.components['balanced_accuracy_test_label'].grid(row=2, column=0, padx=10, pady=5, sticky='w')
        self.help_system.add_hover_tip(self.components['balanced_accuracy_test_label'], "results")

        self.components['model_save_status_label'] = ctk.CTkLabel(self.components['result_frame'], 
                                                 text='模型保存状态: 未保存')
        self.components['model_save_status_label'].grid(row=3, column=0, padx=10, pady=5, sticky='w')
    
    def _create_predict_panel(self):
        """创建样本预测面板"""
        self.components['predict_frame'] = ctk.CTkFrame(self.root, corner_radius=10)
        self.components['predict_frame'].grid(row=2, column=2, sticky='nsew', padx=5, pady=5)
        
        # 配置predict_frame的网格权重
        self.components['predict_frame'].grid_rowconfigure(1, weight=1)
        self.components['predict_frame'].grid_columnconfigure(0, weight=0)  # 按钮列不扩展
        self.components['predict_frame'].grid_columnconfigure(1, weight=1)  # 结果列扩展

        predict_title = ctk.CTkLabel(self.components['predict_frame'], text="样本预测", 
                                    font=ctk.CTkFont(size=14, weight="bold"))
        predict_title.grid(row=0, column=0, pady=10)

        # 创建左侧按钮容器
        button_container = ctk.CTkFrame(self.components['predict_frame'], fg_color="transparent")
        button_container.grid(row=1, column=0, sticky='nsew', padx=(10, 5), pady=5)

        # 创建右侧结果显示容器
        result_container = ctk.CTkFrame(self.components['predict_frame'], fg_color="transparent")
        result_container.grid(row=1, column=1, sticky='nsew', padx=(5, 10), pady=5)

        # 左侧按钮区域
        file_button = ctk.CTkButton(button_container, text="选择要检测的txt文件", width=180, height=35,
            command=self.open_file_dialog_wrapper)
        file_button.pack(pady=(0, 10), fill='x')
        self.help_system.add_hover_tip(file_button, "select_predict_file")

        model_info_button = ctk.CTkButton(button_container, text="查看模型详情", width=180, height=35,
        command=lambda: self.model_info_display.show_info_window(self.root))
        model_info_button.pack(pady=(0, 10), fill='x')
        self.help_system.add_hover_tip(model_info_button, "model_info")
        
        # 右侧结果显示区域
        self.components['prediction_result_label'] = ctk.CTkLabel(result_container, text='状态：等待选择文件',
                                            justify='left', anchor='nw')
        self.components['prediction_result_label'].pack(fill='both', expand=True, padx=5, pady=5)
    
    def _create_visualization_panel(self):
        """创建可视化显示面板"""
        self.components['visualization_frame'] = ctk.CTkFrame(self.root, corner_radius=10)
        self.components['visualization_frame'].grid(row=3, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        
        # 配置可视化框架的网格权重
        self.components['visualization_frame'].grid_rowconfigure(1, weight=1)
        self.components['visualization_frame'].grid_columnconfigure(0, weight=1)
        
        # 可视化标题
        viz_title = ctk.CTkLabel(self.components['visualization_frame'], text="模型评估结果", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        viz_title.grid(row=0, column=0, pady=10)
        
        # 可视化占位区域
        self.components['visualization_placeholder'] = ctk.CTkFrame(self.components['visualization_frame'])
        self.components['visualization_placeholder'].grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        
        placeholder_label = ctk.CTkLabel(self.components['visualization_placeholder'], 
                                        text="训练完成后，模型评估图表将在此显示", 
                                        font=ctk.CTkFont(size=12))
        placeholder_label.pack(expand=True)
    
    def _create_info_panel(self):
        """创建运行信息面板"""
        self.components['info_frame'] = ctk.CTkFrame(self.root, corner_radius=10)
        self.components['info_frame'].grid(row=3, column=2, sticky='nsew', padx=5, pady=5)
        
        # 配置信息框架的网格权重
        self.components['info_frame'].grid_rowconfigure(1, weight=1)
        self.components['info_frame'].grid_columnconfigure(0, weight=1)
        
        # 信息显示标题
        info_title = ctk.CTkLabel(self.components['info_frame'], text="运行信息", 
                                 font=ctk.CTkFont(size=14, weight="bold"))
        info_title.grid(row=0, column=0, pady=10)

        # 日志文本框
        self.components['info_text'] = ctk.CTkTextbox(self.components['info_frame'], width=300, height=250)
        self.components['info_text'].grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.help_system.add_hover_tip(self.components['info_text'], "log_info")


# ========== 保持原有的便捷函数（兼容性） ==========

def select_folder_for_classification():
    """选择文件夹并扫描txt文件"""
    folder_path = filedialog.askdirectory(title="选择类别文件夹")
    if folder_path:
        # 扫描文件夹中的所有.txt文件
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
      # === 计算居中位置 ===
    window_width = 700
    window_height = 750
    # 获取屏幕尺寸，计算居中位置
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
    """
    创建GUI - 使用新的类管理方式
    """
    root = ctk.CTk()
    gui_manager = MainGUIManager(root)
    gui_manager.create_gui_components()
    return root


if __name__ == "__main__":
    root = create_gui()
    root.mainloop()