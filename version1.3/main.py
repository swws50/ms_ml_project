# main.py - 主程序入口和GUI界面 (使用data_store版本)

# 基础数据处理
import os

import customtkinter as ctk


# 导入其他模块
from config import MODEL_CONFIGS, DEFAULT_MODEL
from utils import log_message, clear_log, set_global_widgets
from data_processing import select_and_process_files, open_excel_file
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


def open_excel_file_wrapper(normalization_label, start_button, progress_bar):
    """包装函数，处理文件加载并推进步骤"""
    global help_system
    
    # 调用数据处理函数
    row, column, df = open_excel_file(normalization_label, start_button, progress_bar)
    
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
    
    # 数据预处理按钮
    data_btn = ctk.CTkButton(menu_container, text="数据预处理", width=120, height=35,
                            command=lambda: select_and_process_files(root))
    data_btn.pack(side="left", padx=5)
    
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
    open_button = ctk.CTkButton(control_frame, text="选择归一化excel文件", width=180, height=35,
        command=lambda: open_excel_file_wrapper(normalization_label, start_button, progress_bar))
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


if __name__ == "__main__":
    root = create_gui()
    root.mainloop()
