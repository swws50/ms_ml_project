# parameter_tuning_window_enhanced.py - 增强版参数调优窗口
# 自动显示模型的所有可调参数（包括sklearn默认值）

import customtkinter as ctk
from tkinter import messagebox
import inspect
from config import MODEL_CONFIGS
from utils import log_message, center_window

# 导入所有模型类
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegressionCV
from sklearn.neural_network import MLPClassifier
from sklearn.cross_decomposition import PLSRegression


class ParameterTuningWindow(ctk.CTkToplevel):
    """增强版参数调优窗口 - 显示所有可调参数"""
    
    # 模型类映射
    MODEL_CLASSES = {
        "RandomForestClassifier": RandomForestClassifier,
        "GradientBoostingClassifier": GradientBoostingClassifier,
        "LinearSVC": LinearSVC,
        "LinearDiscriminantAnalysis": LinearDiscriminantAnalysis,
        "LogisticRegressionCV": LogisticRegressionCV,
        "MLPClassifier": MLPClassifier,
        "PLSRegression": PLSRegression,
    }
    
    # 常用参数的分类和说明
    PARAMETER_CATEGORIES = {
        "RandomForestClassifier": {
            "基础参数": ["n_estimators", "max_depth", "min_samples_split", "min_samples_leaf"],
            "高级参数": ["max_features", "bootstrap", "oob_score", "n_jobs", "random_state"],
        },
        "LinearSVC": {
            "基础参数": ["C", "loss", "penalty", "max_iter"],
            "高级参数": ["dual", "tol", "multi_class", "random_state"],
        },
        "MLPClassifier": {
            "基础参数": ["hidden_layer_sizes", "activation", "solver", "max_iter"],
            "高级参数": ["alpha", "learning_rate", "learning_rate_init", "batch_size"],
        },
        "PLSRegression": {
            "基础参数": ["n_components", "scale", "max_iter", "tol"],
        },
    }
    
    def __init__(self, parent, model_name):
        super().__init__(parent)
        
        self.parent = parent
        self.model_name = model_name
        self.parameter_entries = {}
        self.result = None
        
        # 获取模型类和所有参数
        self.model_class = self.MODEL_CLASSES.get(model_name)
        if not self.model_class:
            messagebox.showerror("错误", f"未知的模型: {model_name}")
            self.destroy()
            return
        
        # 获取所有参数及默认值
        self.all_params = self._get_all_parameters()
        self.current_config = MODEL_CONFIGS.get(model_name, {})
        
        # 窗口配置
        self.title(f"参数调优 - {model_name}")
        self.geometry("700x600")
        
        # 设置窗口居中和置顶
        self.transient(parent)
        self.grab_set()
        
        # 初始化UI
        self._setup_ui()
    
    def _get_all_parameters(self):
        """获取模型的所有可调参数及其默认值"""
        try:
            # 获取构造函数签名
            sig = inspect.signature(self.model_class.__init__)
            params = {}
            
            for param_name, param in sig.parameters.items():
                # 跳过 self 参数
                if param_name == 'self':
                    continue
                
                # 获取默认值
                if param.default != inspect.Parameter.empty:
                    params[param_name] = param.default
                else:
                    # 如果没有默认值，标记为 None
                    params[param_name] = None
            
            return params
        except Exception as e:
            log_message(f"获取模型参数失败: {e}", "ERROR")
            return {}
    
    def _setup_ui(self):
        """设置UI"""
        from utils import set_window_icon
        set_window_icon(self) 
        # 配置网格权重
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 标题
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, pady=10, padx=20, sticky='ew')
        
        ctk.CTkLabel(
            title_frame,
            text=f"模型: {self.model_name}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # 显示模式切换
        self.show_mode = ctk.CTkSegmentedButton(
            title_frame,
            values=["仅显示已配置", "显示所有参数"],
            command=self._change_display_mode
        )
        self.show_mode.set("仅显示已配置")
        self.show_mode.pack(side="right")
        
        # 提示信息
        info_label = ctk.CTkLabel(
            self,
            text="💡 提示：蓝色标记的是当前已配置的参数，其他为默认值",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        info_label.grid(row=1, column=0, pady=5, padx=20, sticky='w')
        
        # 参数编辑区（可滚动）
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=2, column=0, sticky='nsew', padx=20, pady=10)
        self.scroll_frame.grid_columnconfigure(1, weight=1)
        
        # 加载参数
        self._load_parameters()
        
        # 底部按钮
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky='ew', padx=20, pady=10)
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkButton(
            button_frame,
            text="保存",
            command=self._save_parameters,
            fg_color="green",
            hover_color="darkgreen",
            height=35
        ).grid(row=0, column=0, padx=5, sticky='ew')
        
        ctk.CTkButton(
            button_frame,
            text="重置",
            command=self._reset_parameters,
            height=35
        ).grid(row=0, column=1, padx=5, sticky='ew')
        
        ctk.CTkButton(
            button_frame,
            text="取消",
            command=self.destroy,
            fg_color="gray",
            hover_color="darkgray",
            height=35
        ).grid(row=0, column=2, padx=5, sticky='ew')
    
    def _change_display_mode(self, value):
        """切换显示模式"""
        self._load_parameters()
    
    def _load_parameters(self):
        """加载参数"""
        # 清空现有显示
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self.parameter_entries.clear()
        
        # 确定要显示的参数
        if self.show_mode.get() == "仅显示已配置":
            params_to_show = self.current_config
        else:
            params_to_show = self.all_params
        
        if not params_to_show:
            ctk.CTkLabel(
                self.scroll_frame,
                text="该模型无可配置参数",
                font=ctk.CTkFont(size=12)
            ).grid(row=0, column=0, columnspan=3, pady=20)
            return
        
        # 显示参数
        row_idx = 0
        for param_name, default_value in params_to_show.items():
            # 获取当前值（优先使用已配置的值）
            current_value = self.current_config.get(param_name, default_value)
            is_configured = param_name in self.current_config
            
            self._create_parameter_row(param_name, current_value, is_configured, row_idx)
            row_idx += 1
    
    def _create_parameter_row(self, param_name, param_value, is_configured, row):
        """创建单个参数行"""
        # 参数名称（已配置的用蓝色标记）
        name_color = "#1f6aa5" if is_configured else "black"
        label = ctk.CTkLabel(
            self.scroll_frame,
            text=f"{param_name}:",
            font=ctk.CTkFont(size=12, weight="bold" if is_configured else "normal"),
            text_color=name_color
        )
        label.grid(row=row, column=0, padx=10, pady=8, sticky='w')
        
        # 参数值输入框
        entry = ctk.CTkEntry(self.scroll_frame, width=250)
        if param_value is not None:
            entry.insert(0, str(param_value))
        else:
            entry.insert(0, "None")
        entry.grid(row=row, column=1, padx=10, pady=8, sticky='ew')
        
        # 状态标签
        if is_configured:
            status = ctk.CTkLabel(
                self.scroll_frame,
                text="✓ 已配置",
                font=ctk.CTkFont(size=10),
                text_color="#1f6aa5"
            )
        else:
            status = ctk.CTkLabel(
                self.scroll_frame,
                text="默认值",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
        status.grid(row=row, column=2, padx=10, pady=8, sticky='w')
        
        # 保存引用
        self.parameter_entries[param_name] = {
            'entry': entry,
            'default': param_value,
            'type': type(param_value) if param_value is not None else str
        }
    
    def _reset_parameters(self):
        """重置所有参数"""
        for param_name, param_info in self.parameter_entries.items():
            param_info['entry'].delete(0, 'end')
            default_val = self.current_config.get(param_name, param_info['default'])
            if default_val is not None:
                param_info['entry'].insert(0, str(default_val))
            else:
                param_info['entry'].insert(0, "None")
        log_message("参数已重置")
    
    def _save_parameters(self):
        """保存修改后的参数"""
        try:
            modified_params = {}
            
            for param_name, param_info in self.parameter_entries.items():
                value_str = param_info['entry'].get().strip()
                
                # 跳过空值
                if not value_str or value_str.lower() == 'none':
                    continue
                
                param_type = param_info['type']
                
                # 类型转换
                try:
                    if param_type == int:
                        modified_params[param_name] = int(value_str)
                    elif param_type == float:
                        modified_params[param_name] = float(value_str)
                    elif param_type == bool:
                        modified_params[param_name] = value_str.lower() in ['true', '1', 'yes']
                    elif param_type == tuple:
                        modified_params[param_name] = eval(value_str)
                    elif param_type == str:
                        modified_params[param_name] = value_str
                    else:
                        # 尝试eval
                        modified_params[param_name] = eval(value_str)
                except Exception as e:
                    messagebox.showerror(
                        "参数错误",
                        f"参数 '{param_name}' 的值 '{value_str}' 格式错误:\n{str(e)}"
                    )
                    return
            
            # 保存结果
            self.result = modified_params
            
            # 更新全局配置
            MODEL_CONFIGS[self.model_name] = modified_params
            
            log_message(f"模型 {self.model_name} 的参数已更新", "SUCCESS")
            messagebox.showinfo("成功", f"已保存 {len(modified_params)} 个参数！")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"保存参数失败:\n{str(e)}")
    
    def get_result(self):
        """获取修改后的参数"""
        return self.result
