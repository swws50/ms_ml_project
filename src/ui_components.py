# ui_components.py - UI组件模块化

# 第三方库导入 
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
# 本地模块导入 
from config import MODEL_CONFIGS
from utils import log_message
import data_store

class ProgressComponent:
    """简化的进度组件，直接集成在UI组件模块中"""
    
    def __init__(self, parent, width=200, show_label=True):
        self.parent = parent
        self.width = width 
        self.show_label = show_label 
        self.progress_bar = None
        self.status_label = None
        self.current_progress = 0.0
        
    def create(self, row, column, sticky='ew', padx=5, pady=2, columnspan=1):
        """创建进度组件"""
        if self.show_label:
            self.status_label = ctk.CTkLabel(self.parent, text="准备中...", font=ctk.CTkFont(size=11))
            self.status_label.grid(row=row, column=column, columnspan=columnspan, sticky='w', padx=padx, pady=(pady, 2))
            
        self.progress_bar = ctk.CTkProgressBar(self.parent, width=self.width)  # 使用 self.width
        self.progress_bar.grid(row=row+1, column=column, columnspan=columnspan, sticky=sticky, padx=padx, pady=(0, pady))
        self.progress_bar.set(0)
        
    def update(self, progress, message=None):
        """更新进度"""
        self.current_progress = max(0.0, min(1.0, progress))
        if self.progress_bar:
            self.progress_bar.set(self.current_progress)
        if message and self.status_label:
            self.status_label.configure(text=message)
            
    def hide(self):
        """隐藏组件"""
        if self.progress_bar:
            self.progress_bar.grid_remove()
        if self.status_label:
            self.status_label.grid_remove()
            
    def show(self):
        """显示组件"""
        if self.progress_bar:
            self.progress_bar.grid()
        if self.status_label:
            self.status_label.grid()
    
class BasePanel:
    """基础面板类 - 提供公共功能"""
    
    def __init__(self, parent, title="", help_system=None):
        self.parent = parent
        self.title = title
        self.help_system = help_system
        self.frame = None
        self.components = {}  # 存储面板内的组件引用
        self.progress_component = None
    
    def create_frame(self, row, column, sticky='nsew', padx=5, pady=5, columnspan=1, rowspan=1, **kwargs):
        """创建基础框架"""
        # 从kwargs中分离grid参数和CTkFrame参数
        grid_params = {
            'row': row,
            'column': column,
            'sticky': sticky,
            'padx': padx,
            'pady': pady
        }
        
        # 如果有columnspan参数，添加到grid_params中
        if columnspan > 1:
            grid_params['columnspan'] = columnspan

         # 如果有rowspan参数，添加到grid_params中  
        if rowspan > 1:
            grid_params['rowspan'] = rowspan
            
        # 创建CTkFrame（不传递grid参数）
        self.frame = ctk.CTkFrame(self.parent, corner_radius=10, **kwargs)
        
        # 使用grid布局（传递grid参数）
        self.frame.grid(**grid_params)
        
        return self.frame
    
    def create_title(self, text=None, row=0, column=0, **kwargs):
        """创建标题标签"""
        title_text = text or self.title
        if title_text:
            title_label = ctk.CTkLabel(self.frame, text=title_text, 
                                     font=ctk.CTkFont(size=14, weight="bold"))
            title_label.grid(row=row, column=column, pady=10, **kwargs)
            return title_label
        return None
    
    def add_hover_tip(self, widget, key_or_text):
        """添加悬停提示"""
        if self.help_system:
            self.help_system.add_hover_tip(widget, key_or_text)     

class PreprocessingPanel(BasePanel):
    """数据预处理面板组件"""
    
    def __init__(self, parent, help_system=None, callbacks=None):
        super().__init__(parent, "数据预处理", help_system)
        self.callbacks = callbacks or {}
    
    def create_panel(self, row, column):
        """创建完整的预处理面板"""
        # 创建基础框架
        self.create_frame(row, column)
        self.create_title()
        
        # 配置网格权重
        self.frame.grid_columnconfigure(0, weight=1)
        
        self._create_panel_content()
        
        return self.frame
    
    def _create_panel_content(self):
        """创建面板内容"""

        self.frame.grid_rowconfigure(1, weight=0)  # 按钮行不扩展
        self.frame.grid_rowconfigure(2, weight=1)  # 空行不扩展  
        self.frame.grid_rowconfigure(3, weight=0)  # 状态行不扩展
        # 主按钮
        self.components['preprocess_button'] = ctk.CTkButton(
            self.frame, text="数据预处理", width=150, height=35,
            command=self._on_start_preprocessing
        )
        self.components['preprocess_button'].grid(row=1, column=0, padx=5, pady=2, sticky='ew')
        self.add_hover_tip(self.components['preprocess_button'], "start_preprocessing")
        
        # 状态显示
        self.components['status_label'] = ctk.CTkLabel(
            self.frame, text="状态：等待开始预处理",
            justify='left', anchor='nw'
        )
        self.components['status_label'].grid(row=2, column=0, padx=5, pady=2, sticky='ew')


    def _on_start_preprocessing(self):
        """预处理按钮回调"""
        if 'on_start_preprocessing' in self.callbacks: 
            self.callbacks['on_start_preprocessing']()
    
    def update_status(self, status_text, color='black'):
        """更新状态显示"""
        self.components['status_label'].configure(text=f"状态：{status_text}", text_color=color)
    
    def set_button_state(self, enabled=True):
        """设置按钮状态"""
        state = 'normal' if enabled else 'disabled'
        self.components['preprocess_button'].configure(state=state)


class ControlPanel(BasePanel):
    """操作控制面板组件"""
    
    def __init__(self, parent, help_system=None, callbacks=None):
        super().__init__(parent, "操作控制", help_system)
        self.callbacks = callbacks or {}
        self.current_model = None
        
    def create_panel(self, row, column):
        """创建完整的控制面板"""
        # 创建基础框架
        self.create_frame(row, column)
        self.create_title()
        
        # 配置网格权重
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(3, weight=1)
        
        # 创建各个控制组件
        self._create_file_controls()
        self._create_model_controls() 
        self._create_training_controls()
        
        return self.frame
    
    def _create_file_controls(self):
        """创建文件选择控件"""
        # 文件选择按钮
        self.components['file_button'] = ctk.CTkButton(
            self.frame, text="选择归一化.csv文件", width=180, height=35,
            command=self._on_file_select
        )
        self.components['file_button'].grid(row=1, column=0, padx=10, pady=5, sticky='ew')
        self.add_hover_tip(self.components['file_button'], "select_excel")
        
        # 文件状态标签
        self.components['file_status'] = ctk.CTkLabel(self.frame, text="文件未选择")
        self.components['file_status'].grid(row=1, column=1, padx=10, pady=5, sticky='w')

         # 添加归一化状态显示
        self.components['norm_status'] = ctk.CTkLabel(
            self.frame, text="归一化: 开", 
            font=ctk.CTkFont(size=10), text_color="green"
        )
        self.components['norm_status'].grid(row=0, column=1, padx=5, pady=5, sticky='w')

    def update_normalization_status(self):
        """更新归一化状态显示"""
        enabled = data_store.is_normalization_enabled()
        text = "归一化: 开" if enabled else "归一化: 关"
        color = "green" if enabled else "orange"
        self.components['norm_status'].configure(text=text, text_color=color)

    def _create_model_controls(self):
        """创建模型选择控件"""
        # 模型选择下拉菜单
        self.components['model_menu'] = ctk.CTkOptionMenu(
            self.frame, values=list(MODEL_CONFIGS.keys()),
            command=self._on_model_select, width=160, height=35
        )
        from config import DEFAULT_MODEL
        self.components['model_menu'].set(DEFAULT_MODEL)
        self.current_model = DEFAULT_MODEL
        self.components['model_menu'].grid(row=2, column=0, padx=10, pady=5, sticky='ew')
        self.add_hover_tip(self.components['model_menu'], "model_selection")
        
        # 模型状态标签
        self.components['model_status'] = ctk.CTkLabel(self.frame, text="已选择: PLSRegression")
        self.components['model_status'].grid(row=2, column=1, padx=10, pady=5, sticky='w')
    
    def _create_training_controls(self):
        """创建训练控制组件"""
        # 开始训练按钮
        self.components['start_button'] = ctk.CTkButton(
            self.frame, text='开始分析', width=180, height=35,
            command=self._on_start_training, state='disabled'
        )
        self.components['start_button'].grid(row=3, column=0, padx=10, pady=5, sticky='ew')
        self.add_hover_tip(self.components['start_button'], "start_analysis")
        
    
    def _on_file_select(self):
        """文件选择回调"""
        if 'on_file_select' in self.callbacks:
            self.callbacks['on_file_select']()
    
    def _on_model_select(self, choice):
        """模型选择回调"""
        self.current_model = choice
        self.components['model_status'].configure(text=f"已选择: {choice}")
        log_message(f"已选择模型: {choice}")
        
        if 'on_model_select' in self.callbacks:
            self.callbacks['on_model_select'](choice)
    
    def _on_start_training(self):
        """开始训练回调"""
        if 'on_start_training' in self.callbacks:
            self.callbacks['on_start_training']()
    
    def update_file_status(self, status_text):
        """更新文件状态"""
        self.components['file_status'].configure(text=status_text)
    
    def enable_training(self, enabled=True):
        """启用/禁用训练按钮"""
        state = 'normal' if enabled else 'disabled'
        self.components['start_button'].configure(state=state)  
    
    def get_selected_model(self):
        """获取选择的模型"""
        return self.current_model or self.components['model_menu'].get()



class ResultPanel(BasePanel):
    """训练结果面板组件"""
    
    def __init__(self, parent, help_system=None):
        super().__init__(parent, "训练结果", help_system)
    
    def create_panel(self, row, column):
        """创建完整的结果面板"""
        # 创建基础框架
        self.create_frame(row, column)
        self.create_title()
        
        # 创建结果显示标签
        self._create_result_labels()
        
        return self.frame
    
    def _create_result_labels(self):
        """创建结果显示标签"""
        # 训练集精度
        self.components['train_accuracy'] = ctk.CTkLabel(
            self.frame, text='平均训练集平衡精度: --'
        )
        self.components['train_accuracy'].grid(row=1, column=0, padx=10, pady=5, sticky='w')
        self.add_hover_tip(self.components['train_accuracy'], "results")
        
        # 测试集精度
        self.components['test_accuracy'] = ctk.CTkLabel(
            self.frame, text='平均测试集平衡精度: --'
        )
        self.components['test_accuracy'].grid(row=2, column=0, padx=10, pady=5, sticky='w')
        self.add_hover_tip(self.components['test_accuracy'], "results")
        
        # 模型保存状态
        self.components['model_status'] = ctk.CTkLabel(
            self.frame, text='模型保存状态: 未保存'
        )
        self.components['model_status'].grid(row=3, column=0, padx=10, pady=5, sticky='w')
    
    def update_train_accuracy(self, accuracy):
        """更新训练集精度"""
        self.components['train_accuracy'].configure(text=f'平均训练集平衡精度: {accuracy:.4f}')
    
    def update_test_accuracy(self, accuracy):
        """更新测试集精度"""
        self.components['test_accuracy'].configure(text=f'平均测试集平衡精度: {accuracy:.4f}')
    
    def update_model_status(self, status, score=None, color='green'):
        """更新模型状态"""
        if score is not None:
            status_text = f'模型保存状态: {status} (分数: {score:.4f})'
        else:
            status_text = f'模型保存状态: {status}'
        
        self.components['model_status'].configure(text=status_text, text_color=color)
    
    def reset_results(self):
        """重置所有结果显示"""
        self.components['train_accuracy'].configure(text='平均训练集平衡精度: --')
        self.components['test_accuracy'].configure(text='平均测试集平衡精度: --')
        self.components['model_status'].configure(text='模型保存状态: 未保存', text_color='gray')


class PredictionPanel(BasePanel):
    """样本预测面板组件"""
    
    def __init__(self, parent, help_system=None, callbacks=None):
        super().__init__(parent, "样本预测", help_system)
        self.callbacks = callbacks or {}
        self.current_model_selection = None

    def create_panel(self, row, column, rowspan=1):
        """创建完整的预测面板"""
        # 创建基础框架
        self.create_frame(row, column, rowspan=rowspan)
        
        # 配置主网格
        self.frame.grid_rowconfigure(1, weight=0)  # 模型设置区域 - 固定高度
        self.frame.grid_rowconfigure(2, weight=0)  # 操作按钮区域 - 固定高度  
        self.frame.grid_rowconfigure(3, weight=1)  # 结果显示区域 - 可扩展
        self.frame.grid_columnconfigure(0, weight=1)

        self.create_title()
        self._create_panel_layout()
        
        return self.frame

    def _create_panel_layout(self):
        """创建面板布局 - 三栏结构"""
        # 配置主网格
        self.frame.grid_rowconfigure(1, weight=0)  # 模型设置区域 - 固定高度
        self.frame.grid_rowconfigure(2, weight=0)  # 操作按钮区域 - 固定高度  
        self.frame.grid_rowconfigure(3, weight=1)  # 结果显示区域 - 可扩展
        self.frame.grid_columnconfigure(0, weight=1)

        # 创建三个区域
        self._create_model_settings_area()
        self._create_action_buttons_area() 
        self._create_result_display_area()
        
    
    def _create_model_settings_area(self):
        """创建模型设置区域"""
        settings_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        settings_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        settings_frame.grid_columnconfigure(1, weight=1)
        settings_frame.grid_columnconfigure(3, weight=1)
        
        
        
        # 模型选择
        ctk.CTkLabel(settings_frame, text="模型选择:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky='w', padx=5, pady=2
        )
        
        self.components['model_select_button'] = ctk.CTkButton(
            settings_frame, text="选择模型文件", width=150, height=28,
            command=self._on_model_file_select
        )
        self.components['model_select_button'].grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        # 兼容性状态指示器（与模型选择对齐）
        self.components['compatibility_status'] = ctk.CTkLabel(
            settings_frame, text="兼容性: 未检测", 
            font=ctk.CTkFont(size=10), text_color="gray"
        )
        self.components['compatibility_status'].grid(row=0, column=2, sticky='w', padx=15, pady=2)
        
        
        # 归一化状态显示（与数据模式选择对齐）
        self.components['norm_status'] = ctk.CTkLabel(
            settings_frame, text="归一化", 
            font=ctk.CTkFont(size=10), text_color="blue"
        )
        self.components['norm_status'].grid(row=0, column=3, sticky='e', padx=5, pady=2)


    def _create_action_buttons_area(self):
        """创建操作按钮区域"""
        button_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=5)
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        # 预测按钮
        self.components['predict_button'] = ctk.CTkButton(
            button_frame, text="选择要检测的txt文件", height=35,
            command=self._on_predict_file
        )
        self.components['predict_button'].grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        self.add_hover_tip(self.components['predict_button'], "select_predict_file")
        
        # 模型信息按钮
        self.components['model_info_button'] = ctk.CTkButton(
            button_frame, text="查看模型详情", height=35,
            command=self._on_model_info
        )
        self.components['model_info_button'].grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.add_hover_tip(self.components['model_info_button'], "model_info")


    def _create_result_display_area(self):
        """创建结果显示区域"""
        result_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        result_frame.grid(row=3, column=0, sticky='nsew', padx=10, pady=5)
        result_frame.grid_rowconfigure(1, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
        # 结果标题和复制按钮
        header_frame = ctk.CTkFrame(result_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 5))
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header_frame, text="预测结果:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky='w'
        )
        
        self.components['copy_button'] = ctk.CTkButton(
            header_frame, text="复制结果", width=80, height=25,
            command=self._copy_result_to_clipboard
        )
        self.components['copy_button'].grid(row=0, column=1, sticky='e')
        
        # 结果文本框 - 改为可选择的文本框
        self.components['result_textbox'] = ctk.CTkTextbox(
            result_frame, height=150, font=ctk.CTkFont(size=11)
        )
        self.components['result_textbox'].grid(row=1, column=0, sticky='nsew')
        self.components['result_textbox'].insert("end", "状态：等待选择文件")

    def update_normalization_status(self):
        """更新归一化状态显示"""
        enabled = data_store.is_normalization_enabled()
        text = "归一化" if enabled else "原始数据"
        color = "blue" if enabled else "orange"
        self.components['norm_status'].configure(text=text, text_color=color)
            
    def _on_predict_file(self):
        """单文件预测回调"""
        if 'on_predict_file' in self.callbacks:
            self.callbacks['on_predict_file']()
    
    def _on_model_info(self):
        """模型信息回调"""
        if 'on_model_info' in self.callbacks:
            self.callbacks['on_model_info']()
    
    
    def update_result(self, result_text, color='black'):
        """更新预测结果显示"""
        self.components['result_textbox'].delete("1.0", "end")
        self.components['result_textbox'].insert("1.0", result_text)
        self.components['result_textbox'].configure(text_color=color)
    

    def _update_compatibility_status(self):
        """更新兼容性状态显示"""
        if self.current_model_selection:
            if self.current_model_selection == "自动检测":
                status = "兼容性: 自动匹配"
                color = "blue"
            else:
                status = "兼容性: 手动选择"
                color = "green"
        else:
            status = "兼容性: 未检测"
            color = "gray"
        
        self.components['compatibility_status'].configure(text=status, text_color=color)

    def _copy_result_to_clipboard(self):
        """复制预测结果到剪贴板"""
        try:
            result_text = self.components['result_textbox'].get("1.0", "end-1c")
            self.components['result_textbox'].clipboard_clear()
            self.components['result_textbox'].clipboard_append(result_text)
            log_message("预测结果已复制到剪贴板", "SUCCESS")
            
            # 临时改变按钮文字提示用户
            original_text = self.components['copy_button'].cget("text")
            self.components['copy_button'].configure(text="已复制!")
            self.components['copy_button'].after(1500, lambda: self.components['copy_button'].configure(text=original_text))
            
        except Exception as e:
            log_message(f"复制到剪贴板失败: {str(e)}", "ERROR")

    def _on_model_file_select(self):
        """打开文件对话框选择模型"""
        from config import OUTPUT_FILES
        
        # 获取模型文件的目录路径
        model_path = OUTPUT_FILES['best_model']
        model_dir = os.path.dirname(model_path)
        
        # 如果模型目录不存在，使用当前目录
        if not os.path.exists(model_dir):
            model_dir = "."
        
        file_path = filedialog.askopenfilename(
            title="选择模型文件",
            filetypes=[("Joblib files", "*.joblib"), ("All files", "*.*")],
            initialdir=model_dir,
            initialfile="best_model.joblib"  # 默认文件名
        )
        
        if file_path:
            model_name = os.path.basename(file_path)
            self.current_model_selection = file_path  # 存储完整路径
            self.components['model_select_button'].configure(text=f"已选择: {model_name}")
            self.components['compatibility_status'].configure(text="模型: 已选择", text_color="green")
            log_message(f"选择模型文件: {model_name}")

class VisualizationPanel(BasePanel):
    """可视化面板组件"""
    
    def __init__(self, parent, help_system=None):
        super().__init__(parent, "模型评估结果", help_system)
    
    def create_panel(self, row, column, rowspan=2, columnspan=2):
        """创建完整的可视化面板"""
        # 修改：将columnspan传递给create_frame
        self.create_frame(row, column, sticky='nsew', rowspan=rowspan, columnspan=columnspan)
        
        # 配置网格权重
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        self.create_title()
        self._create_visualization_area()
        
        return self.frame
    
    def _create_visualization_area(self):
        """创建可视化显示区域"""
        # 可视化占位区域
        self.components['placeholder'] = ctk.CTkFrame(self.frame)
        self.components['placeholder'].grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        
        # 占位提示文本
        self.components['placeholder_label'] = ctk.CTkLabel(
            self.components['placeholder'], 
            text="训练完成后，模型评估图表将在此显示", 
            font=ctk.CTkFont(size=12)
        )
        self.components['placeholder_label'].pack(expand=True)
    
    def get_container(self):
        """获取可视化容器（供其他模块使用）"""
        return self.frame
    
    def get_placeholder(self):
        """获取占位框架（供其他模块使用）"""
        return self.components['placeholder']
    
    def show_loading(self, message="正在生成图表..."):
        """显示加载状态"""
        self.components['placeholder_label'].configure(text=message)
    
    def reset_placeholder(self):
        """重置为默认占位状态"""
        self.components['placeholder_label'].configure(text="训练完成后，模型评估图表将在此显示")


class InfoPanel(BasePanel):
    """运行信息面板组件"""
    
    def __init__(self, parent, help_system=None):
        super().__init__(parent, "运行信息", help_system)
    
    def create_panel(self, row, column, columnspan=2):  # 添加columnspan参数
        """创建完整的信息面板"""
        # 创建基础框架 - 传递columnspan参数
        self.create_frame(row, column, sticky='nsew', columnspan=columnspan)  # 添加columnspan参数
        
        # 配置网格权重
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        self.create_title()
        self._create_info_display()
        
        return self.frame
    
    def _create_info_display(self):
        """创建信息显示区域"""
        # 日志文本框
        self.components['text_box'] = ctk.CTkTextbox(self.frame, width=300, height=250)
        self.components['text_box'].grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.add_hover_tip(self.components['text_box'], "log_info")
    
    def get_textbox(self):
        """获取文本框（供日志系统使用）"""
        return self.components['text_box']
    
    def append_message(self, message):
        """添加消息"""
        self.components['text_box'].insert("end", message + "\n")
        self.components['text_box'].see("end")
    
    def clear_messages(self):
        """清空消息"""
        self.components['text_box'].delete("1.0", "end")

