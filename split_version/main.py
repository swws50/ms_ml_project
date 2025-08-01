# main.py - 主程序入口和GUI界面 (使用data_store版本)

# 基础数据处理
import os

import customtkinter as ctk
from tkinter import filedialog, messagebox

# 导入其他模块
from config import MODEL_CONFIGS, DEFAULT_MODEL, DEFAULT_MZ_VALUES
from utils import log_message, clear_log, set_global_widgets
from data_processing import select_and_process_files, open_data_file, select_and_process_files_intelligent
from model_training import predict_by_wrapper, open_file_dialog, show_model_info
from help_system import HelpSystem
from visualization import reset_analysis
import data_store  # 导入数据存储模块

# 全局变量
notebook = None
info_text = None
help_system = None
exact_selection = DEFAULT_MODEL

def on_selected_ctk(choice):
    """CustomTkinter下拉菜单的回调函数"""
    global exact_selection, help_system
    exact_selection = choice
    log_message(f"已选择模型: {exact_selection}")
    
    if help_system:
        help_system.advance_step("train_model")


def open_data_file_wrapper(normalization_label, start_button, progress_bar):
    """包装函数，处理文件加载并推进步骤"""
    global help_system
    
    # 调用数据处理函数
    row, column, df = open_data_file(normalization_label, start_button, progress_bar)
    
    if row is not None and column is not None:
        # 将数据存储到data_store模块
        data_store.set_training_data(row, column, df)
        log_message("训练数据已加载到数据存储模块", "SUCCESS")
        
        # 推进步骤到"选择模型"
        if help_system:
            help_system.advance_step("select_model")
    else:
        log_message("数据加载失败", "ERROR")

def create_gui():
    """ 
    创建并配置应用程序的主图形用户界面
    """
    global info_text, help_system, exact_selection
    
    # 设置 Customctk 主题
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title('诊断分析')
    
    # 创建帮助系统
    help_system = HelpSystem(root)
    
    # 设置窗口大小和状态
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.geometry(f"{width}x{height}+0+0")
    try:
        root.state('zoomed')  # Windows
    except:
        root.attributes('-zoomed', True)  # Linux
   
   # === 创建现代化顶部菜单栏 ===
    menu_frame = ctk.CTkFrame(root, height=60, corner_radius=0)
    menu_frame.grid(row=0, column=0, columnspan=3, sticky='ew', padx=0, pady=0)
    
    # 菜单按钮容器
    menu_container = ctk.CTkFrame(menu_frame, fg_color="transparent")
    menu_container.pack(side="left", padx=20, pady=15)
    
    def select_processing_method(root):
        """选择处理方法的包装函数"""
        if processing_method_var.get():
            # 使用智能峰发现方法
            log_message("=== 启动智能峰发现模式 ===", "INFO")
            log_message("• 将使用pyOpenMS进行专业峰检测", "INFO")
            log_message("• 自动发现并选择最有区分性的特征峰", "INFO")
            log_message("• 不依赖预设的m/z值列表", "INFO")
            
            # 调用智能处理函数
            open_folder_classification_window(root, is_intelligent_mode=True) 
        else:
            # 使用传统方法
            log_message("=== 使用传统处理方式 ===", "INFO")
            log_message(f"• 基于预设的{len(DEFAULT_MZ_VALUES)}个m/z特征值", "INFO")
            log_message("• 使用固定阈值提取峰强度", "INFO")
            
            # 调用传统处理函数
            open_folder_classification_window(root, is_intelligent_mode=False)
            
    # 数据预处理按钮
    data_btn = ctk.CTkButton(menu_container, text="数据预处理", width=120, height=35,
                            command=lambda: select_processing_method(root))
    data_btn.pack(side="left", padx=5)
    
    # 添加处理方式选择开关
    processing_method_var = ctk.BooleanVar(value=False)  # 默认使用传统方法
    processing_switch = ctk.CTkSwitch(menu_container, 
                                    text="提峰模式", 
                                    variable=processing_method_var,
                                    width=120)
    processing_switch.pack(side="left", padx=5)
    help_system.add_hover_tip(processing_switch, 
                            "开启：使用pyOpenMS自动发现最佳特征峰\n"
                            "关闭：使用预设的47个m/z特征值")
            
    # 显示当前处理方法
    method_indicator = ctk.CTkLabel(menu_container, 
                                text="(传统方式)",
                                font=ctk.CTkFont(size=10), 
                                text_color="blue")
    method_indicator.pack(side="left", padx=2)

    # 更新开关回调，改变指示器文本
    def on_method_switch():
        if processing_method_var.get():
            method_indicator.configure(text="(智能峰发现)", text_color="green")
            log_message("切换到智能峰发现模式", "INFO")
        else:
            method_indicator.configure(text="(传统方式)", text_color="blue")
            log_message("切换处理方式", "INFO")
    processing_switch.configure(command=on_method_switch)

    # 模型选择下拉菜单
    model_label = ctk.CTkLabel(menu_container, text="模型选择:", 
                              font=ctk.CTkFont(size=12, weight="bold"))
    model_label.pack(side="left", padx=(15, 5))
    
    
    model_menu = ctk.CTkOptionMenu(menu_container, values=list(MODEL_CONFIGS.keys()),
                                  command=lambda choice: on_selected_ctk(choice))
    model_menu.set(exact_selection)
    model_menu.pack(side="left", padx=5)
    
    # 项目管理按钮
    project_btn = ctk.CTkButton(menu_container, text="重置进度", width=100, height=35,
                               command=lambda: reset_analysis(help_system))
    project_btn.pack(side="left", padx=5)
    
    # 帮助按钮
    help_btn = ctk.CTkButton(menu_container, text="使用向导", width=100, height=35,
                            command=help_system.show_wizard)
    help_btn.pack(side="left", padx=5)

     # 创建步骤进度指示器
    help_system.create_progress_indicator(root, row=1, column=0, columnspan=3)

    # 配置根窗口的网格权重
    root.grid_rowconfigure(3, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_columnconfigure(2, weight=1)

   # Frame1: 操作控制面板（左）
    control_frame = ctk.CTkFrame(root, corner_radius=10)
    control_frame.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)
    
    control_title = ctk.CTkLabel(control_frame, text="操作控制", 
                                font=ctk.CTkFont(size=14, weight="bold"))
    control_title.grid(row=0, column=0, columnspan=2, pady=10)

   # 文件选择
    open_button = ctk.CTkButton(control_frame, text="选择归一化.csv文件", width=180, height=35,
        command=lambda: open_data_file_wrapper(normalization_label, start_button, progress_bar))
    open_button.grid(row=1, column=0, padx=10, pady=5, sticky='ew')
    help_system.add_hover_tip(open_button, "select_excel")

    normalization_label = ctk.CTkLabel(control_frame, text="文件未选择")
    normalization_label.grid(row=1, column=1, padx=10, pady=5, sticky='w')

    # 训练控制
    start_button = ctk.CTkButton(control_frame, text='开始分析', width=180, height=35,
        command=lambda: predict_by_wrapper(progress_label, progress_bar, balanced_accuracy_train_label, 
                                   balanced_accuracy_test_label, model_save_status_label, 
                                   exact_selection, help_system, root))
    start_button.grid(row=2, column=0, padx=10, pady=5, sticky='ew')
    start_button.configure(state='disabled')
    help_system.add_hover_tip(start_button, "start_analysis")

    display_label = ctk.CTkLabel(control_frame, text='默认使用'+exact_selection)
    display_label.grid(row=2, column=1, padx=10, pady=5, sticky='w')
    help_system.add_hover_tip(display_label, "model_selection")

    # 进度显示
    progress_label = ctk.CTkLabel(control_frame, text='分析进度: 0%')
    progress_label.grid(row=3, column=0, padx=10, pady=5, sticky='w')
    
    progress_bar = ctk.CTkProgressBar(control_frame, width=200)
    progress_bar.grid(row=3, column=1, padx=10, pady=5, sticky='ew')
    progress_bar.set(0)
    help_system.add_hover_tip(progress_bar, "progress")

    control_frame.grid_columnconfigure(1, weight=1)

    # Frame2: 训练结果面板（中）
    result_frame = ctk.CTkFrame(root, corner_radius=10)
    result_frame.grid(row=2, column=1, sticky='nsew', padx=5, pady=5)
    
    result_title = ctk.CTkLabel(result_frame, text="训练结果", 
                               font=ctk.CTkFont(size=14, weight="bold"))
    result_title.grid(row=0, column=0, pady=10)

    balanced_accuracy_train_label = ctk.CTkLabel(result_frame, text='平均训练集平衡精度: --')
    balanced_accuracy_train_label.grid(row=1, column=0, padx=10, pady=5, sticky='w')
    help_system.add_hover_tip(balanced_accuracy_train_label, "results")

    balanced_accuracy_test_label = ctk.CTkLabel(result_frame, text='平均测试集平衡精度: --')
    balanced_accuracy_test_label.grid(row=2, column=0, padx=10, pady=5, sticky='w')
    help_system.add_hover_tip(balanced_accuracy_test_label, "results")

    model_save_status_label = ctk.CTkLabel(result_frame, text='模型保存状态: 未保存')
    model_save_status_label.grid(row=3, column=0, padx=10, pady=5, sticky='w')

    # Frame3: 样本预测面板（右）
    predict_frame = ctk.CTkFrame(root, corner_radius=10)
    predict_frame.grid(row=2, column=2, sticky='nsew', padx=5, pady=5)
    
    predict_title = ctk.CTkLabel(predict_frame, text="样本预测", 
                                font=ctk.CTkFont(size=14, weight="bold"))
    predict_title.grid(row=0, column=0, pady=10)

    file_button = ctk.CTkButton(predict_frame, text="选择要检测的txt文件", width=180, height=35,
        command=lambda: open_file_dialog(prediction_result_label, help_system))
    file_button.grid(row=1, column=0, padx=10, pady=5, sticky='ew')
    help_system.add_hover_tip(file_button, "select_predict_file")

    prediction_result_label = ctk.CTkLabel(predict_frame, text='状态：等待选择文件')
    prediction_result_label.grid(row=2, column=0, padx=10, pady=5, sticky='w')

    model_info_button = ctk.CTkButton(predict_frame, text="查看模型详情", width=180, height=35,
        command=lambda: show_model_info())
    model_info_button.grid(row=3, column=0, padx=10, pady=5, sticky='ew')
    help_system.add_hover_tip(model_info_button, "model_info")

    # Frame4: 可视化显示面板（左，占大部分空间）
    visualization_frame = ctk.CTkFrame(root, corner_radius=10)
    visualization_frame.grid(row=3, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
    
   # 配置可视化框架的网格权重
    visualization_frame.grid_rowconfigure(1, weight=1)
    visualization_frame.grid_columnconfigure(0, weight=1)
    
    # 可视化标题
    viz_title = ctk.CTkLabel(visualization_frame, text="模型评估结果", 
                            font=ctk.CTkFont(size=14, weight="bold"))
    viz_title.grid(row=0, column=0, pady=10)
    
    # 可视化占位区域
    visualization_placeholder = ctk.CTkFrame(visualization_frame)
    visualization_placeholder.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
    
    placeholder_label = ctk.CTkLabel(visualization_placeholder, 
                                    text="训练完成后，模型评估图表将在此显示", 
                                    font=ctk.CTkFont(size=12))
    placeholder_label.pack(expand=True)
    
    # Frame5: 运行信息面板（右）
    info_frame = ctk.CTkFrame(root, corner_radius=10)
    info_frame.grid(row=3, column=2, sticky='nsew', padx=5, pady=5)
    
    # 配置信息框架的网格权重
    info_frame.grid_rowconfigure(1, weight=1)
    info_frame.grid_columnconfigure(0, weight=1)
    
    # 信息显示标题
    info_title = ctk.CTkLabel(info_frame, text="运行信息", 
                             font=ctk.CTkFont(size=14, weight="bold"))
    info_title.grid(row=0, column=0, pady=10)

    # 日志文本框
    info_text = ctk.CTkTextbox(info_frame, width=300, height=250)
    info_text.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
    help_system.add_hover_tip(info_text, "log_info")

    # 保存容器引用供visualize_performance使用
    root.visualization_container = visualization_frame
    root.visualization_placeholder = visualization_placeholder

    # 设置全局组件引用
    set_global_widgets(info_text, root)

    # 初始化日志
    log_message("系统已启动，等待用户操作...")
    log_message("数据存储模块已初始化", "INFO")

    # 如果是首次运行，显示向导
    if help_system.show_wizard_on_startup:
        root.after(500, help_system.show_wizard)

    return root


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
    classification_window.geometry("700x750")
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
        
        import data_store
        data_store.set_file_classification(classification_data)
        
        log_message(f"文件分类完成: {class_0_name.get()}({len(class_0_files)}个), {class_1_name.get()}({len(class_1_files)}个)")
        
        # 关闭分类窗口
        classification_window.grab_release()
        classification_window.destroy()
        
        # 开始数据处理
        if is_intelligent_mode:
            # 智能峰发现模式
            log_message("开始智能峰发现处理...", "INFO")
            select_and_process_files_intelligent(root)
        else:
            # 传统方法
            log_message("开始传统方法处理...", "INFO")
            select_and_process_files(root)
    
    ctk.CTkButton(button_frame, text="取消", command=cancel_classification, width=100).pack(side='left')
    ctk.CTkButton(button_frame, text="开始处理", command=confirm_classification, width=120).pack(side='right')
    
    # 初始化预览
    update_preview()
    
    # 窗口关闭处理
    def on_closing():
        classification_window.grab_release()
        classification_window.destroy()
    
    classification_window.protocol("WM_DELETE_WINDOW", on_closing)

if __name__ == "__main__":
    root = create_gui()
    root.mainloop()
