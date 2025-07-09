# help_system.py - 帮助系统和进度跟踪模块

import tkinter
from tkinter import ttk
import json
import os

from utils import log_message

class HelpSystem:
    """统一的帮助系统类 - 完整功能实现"""
    
    def __init__(self, root, config_file="help_config.json"):
        self.root = root
        self.config_file = config_file
        self.active_tooltips = {}  # 跟踪活动的提示窗口
        
        # === 步骤进度跟踪 ===
        self.steps = [
            {"id": "select_data", "name": "选择数据文件", "completed": False},
            {"id": "select_model", "name": "选择模型", "completed": False},
            {"id": "train_model", "name": "训练模型", "completed": False},
            {"id": "view_results", "name": "查看结果", "completed": False},
            {"id": "predict_sample", "name": "预测样本", "completed": False}
        ]
        self.current_step_index = 0
        
        # UI组件引用
        self.progress_frame = None
        self.progress_labels = []
        self.progress_indicator = None
        
        self.show_wizard_on_startup = True

        # 为你的程序定制的帮助文本
        self.help_texts = {
            # 数据预处理相关
            "select_files": "选择原始的txt格式质谱数据文件\n系统将自动提取47个m/z值的峰值强度",
            
            # 训练相关
            "select_excel": "选择已预处理的Excel数据文件\n第一行应为HC/LC标签",
            "model_selection": "选择机器学习算法\n• RandomForest: 适合大数据集\n• LogisticRegression: 适合小数据集\n• PLS: 适合高维数据",
            "start_analysis": "开始训练模型\n• 训练时间：约1-3分钟\n• 将进行500轮交叉验证\n• 训练过程中请勿关闭程序",
            
            # 预测相关
            "select_predict_file": "选择要预测的txt格式样本文件\n需要先完成模型训练",
            "model_info": "查看当前训练模型的详细信息\n包括参数、特征重要性等",
            
            # 状态显示
            "progress": "显示当前任务进度\n训练时会实时更新百分比",
            "results": "显示模型训练结果\n包括准确率、混淆矩阵等指标",
            "log_info": "显示系统运行日志\n记录所有操作和错误信息"
        }
        
        # 步骤相关的提示信息
        self.step_hints = {
            "select_data": "💡 下一步：请点击 '选择归一化excel文件' 按钮选择数据文件",
            "select_model": "💡 下一步：从菜单栏 '模型选择' 中选择合适的机器学习算法",
            "train_model": "💡 下一步：点击 '开始分析' 按钮开始训练模型",
            "view_results": "💡 训练完成！您可以查看生成的评估图表",
            "predict_sample": "💡 模型已就绪！可以选择新样本进行预测"
        }

        # 加载用户配置
        self.load_config()
        
        # UI组件引用
        self.wizard_window = None
    
    def load_config(self):
        """加载用户配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.show_wizard_on_startup = config.get('show_wizard_on_startup', True)
        except Exception:
            pass  # 使用默认配置
    
    def save_config(self):
        """保存用户配置"""
        try:
            config = {
                'show_wizard_on_startup': self.show_wizard_on_startup
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def create_progress_indicator(self, parent_frame, row=0, column=0, columnspan=4):
        """
        创建步骤进度指示器
        
        参数:
            parent_frame: 父容器
            row, column, columnspan: grid布局参数
        """
        # 创建进度指示器框架
        self.progress_frame = tkinter.Frame(parent_frame, bg='#f0f0f0', relief='raised', bd=1)
        self.progress_frame.grid(row=row, column=column, columnspan=columnspan, sticky='ew', padx=5, pady=2)
        
        # 标题
        title_label = tkinter.Label(self.progress_frame, text="操作进度:", 
                                   font=('Arial', 9, 'bold'), bg='#f0f0f0')
        title_label.pack(side='left', padx=5)
        
        # 步骤指示器容器
        steps_frame = tkinter.Frame(self.progress_frame, bg='#f0f0f0')
        steps_frame.pack(side='left', padx=10)
        
        # 创建步骤标签
        self.progress_labels = []
        for i, step in enumerate(self.steps):
            # 步骤圆圈
            step_circle = tkinter.Label(steps_frame, text=str(i+1), 
                                       width=3, height=1,
                                       font=('Arial', 8, 'bold'),
                                       relief='solid', bd=1)
            step_circle.pack(side='left', padx=2)
            
            # 步骤名称
            step_name = tkinter.Label(steps_frame, text=step['name'], 
                                     font=('Arial', 8), bg='#f0f0f0')
            step_name.pack(side='left', padx=(0, 10))
            
            # 箭头（除了最后一个步骤）
            if i < len(self.steps) - 1:
                arrow = tkinter.Label(steps_frame, text="→", 
                                     font=('Arial', 8), bg='#f0f0f0')
                arrow.pack(side='left', padx=2)
            
            self.progress_labels.append((step_circle, step_name))
        
        # 当前步骤提示
        self.progress_indicator = tkinter.Label(self.progress_frame, 
                                               text=self.step_hints.get(self.steps[0]['id'], ""),
                                               font=('Arial', 8), bg='#f0f0f0', fg='blue')
        self.progress_indicator.pack(side='right', padx=10)
        
        # 初始化显示
        self.update_progress_display()
    
    def update_progress_display(self):
        """更新进度显示"""
        if not self.progress_labels:
            return
            
        for i, (circle, name) in enumerate(self.progress_labels):
            if i < self.current_step_index:
                # 已完成的步骤 - 绿色
                circle.config(bg='#90EE90', fg='black')
                name.config(fg='green', font=('Arial', 8, 'normal'))
            elif i == self.current_step_index:
                # 当前步骤 - 蓝色高亮
                circle.config(bg='#87CEEB', fg='black')
                name.config(fg='blue', font=('Arial', 8, 'bold'))
            else:
                # 未完成的步骤 - 灰色
                circle.config(bg='#D3D3D3', fg='gray')
                name.config(fg='gray', font=('Arial', 8, 'normal'))
        
        # 更新提示信息
        if self.current_step_index < len(self.steps):
            current_step_id = self.steps[self.current_step_index]['id']
            hint_text = self.step_hints.get(current_step_id, "")
            if self.progress_indicator:
                self.progress_indicator.config(text=hint_text)
    
    def advance_step(self, step_id):
        """
        推进到指定步骤
        
        参数:
            step_id: 步骤ID
        """
        # 找到步骤索引
        step_index = None
        for i, step in enumerate(self.steps):
            if step['id'] == step_id:
                step_index = i
                break
        
        if step_index is not None and step_index >= self.current_step_index:
            # 标记之前的步骤为已完成
            for i in range(step_index):
                self.steps[i]['completed'] = True
            
            # 更新当前步骤
            self.current_step_index = step_index
            self.update_progress_display()
            
            # 记录日志
            step_name = self.steps[step_index]['name']
            log_message(f"步骤进度: {step_name}", "INFO")
    
    def complete_step(self, step_id):
        """
        完成指定步骤并自动推进到下一步
        
        参数:
            step_id: 要完成的步骤ID
        """
        # 找到并完成指定步骤
        for i, step in enumerate(self.steps):
            if step['id'] == step_id:
                step['completed'] = True
                break
        
        # 自动推进到下一步
        next_index = self.current_step_index + 1
        if next_index < len(self.steps):
            self.current_step_index = next_index
            self.update_progress_display()
    
    def reset_progress(self):
        """重置进度"""
        for step in self.steps:
            step['completed'] = False
        self.current_step_index = 0
        self.update_progress_display()
    
    def get_current_step(self):
        """获取当前步骤信息"""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None    
    
    def add_hover_tip(self, widget, key_or_text, custom_style=None):
        """
        为控件添加悬停提示
        
        参数:
            widget: tkinter控件
            key_or_text: 配置键名或直接的提示文本
            custom_style: 自定义样式字典
        """
        # 获取提示文本
        if key_or_text in self.help_texts:
            tip_text = self.help_texts[key_or_text]
        else:
            tip_text = key_or_text
        
        # 默认样式
        default_style = {
            "background": "#FFFFDD",
            "foreground": "black",
            "font": ("Arial", 9),
            "relief": "solid",
            "borderwidth": 1,
            "padx": 8,
            "pady": 5
        }
        
        # 应用自定义样式
        if custom_style:
            default_style.update(custom_style)
        
        def show_tip(event):
            """显示提示"""
            # 清理可能存在的旧提示
            self.hide_tip(widget)
            
            # 计算提示窗口位置
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + widget.winfo_height() + 5
            
            # 创建提示窗口
            tip_window = tkinter.Toplevel(widget)
            tip_window.wm_overrideredirect(True)
            tip_window.wm_geometry(f"+{x}+{y}")
            
            # 创建提示标签
            tip_label = tkinter.Label(tip_window, text=tip_text, **default_style)
            tip_label.pack()
            
            # 保存引用
            self.active_tooltips[widget] = tip_window
        
        def hide_tip_event(event):
            """事件适配器"""
            self.hide_tip(widget)
        
        # 绑定事件
        widget.bind("<Enter>", show_tip)
        widget.bind("<Leave>", hide_tip_event)
        
        return self  # 支持链式调用
    
    def hide_tip(self, widget):
        """隐藏指定控件的提示"""
        if widget in self.active_tooltips:
            try:
                self.active_tooltips[widget].destroy()
                del self.active_tooltips[widget]
            except Exception:
                pass
    
    def hide_all_tips(self):
        """隐藏所有提示"""
        for widget in list(self.active_tooltips.keys()):
            self.hide_tip(widget)
    
    def show_wizard(self):
        """显示欢迎向导，指导用户使用程序的基本步骤"""
        if self.wizard_window and self.wizard_window.winfo_exists():
            self.wizard_window.lift()
            return
            
        self.wizard_window = tkinter.Toplevel(self.root)
        self.wizard_window.title("使用向导")
        self.wizard_window.geometry("600x450")
        self.wizard_window.resizable(False, False)

        # 创建笔记本控件来显示多个步骤
        wizard_tabs = ttk.Notebook(self.wizard_window)
        wizard_tabs.pack(fill='both', expand=True, padx=10, pady=10)

        # 第1步：程序介绍
        step1 = ttk.Frame(wizard_tabs)
        wizard_tabs.add(step1, text="1. 介绍")
        ttk.Label(step1, text="诊断分析工具", font=('Helvetica', 14, 'bold')).pack(pady=10)
        ttk.Label(step1, text="本工具用于分析质谱数据并构建机器学习模型，以区分HC与LC样本。",
                  wraplength=550).pack(pady=5)
        ttk.Label(step1, text="使用流程包括：数据预处理、模型训练与评估、新样本预测。",
                  wraplength=550).pack(pady=5)

        # 第2步：数据预处理
        step2 = ttk.Frame(wizard_tabs)
        wizard_tabs.add(step2, text="2. 数据预处理")
        ttk.Label(step2, text="数据预处理步骤", font=('Helvetica', 12, 'bold')).pack(pady=10)
        ttk.Label(step2, text="1. 点击菜单 '数据预处理' -> '选择处理文件'",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)
        ttk.Label(step2, text="2. 选择原始的txt格式质谱数据文件",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)
        ttk.Label(step2, text="3. 等待处理完成，生成LC_MAX.xlsx文件",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)

        # 第3步：模型训练
        step3 = ttk.Frame(wizard_tabs)
        wizard_tabs.add(step3, text="3. 模型训练")
        ttk.Label(step3, text="模型训练与评估", font=('Helvetica', 12, 'bold')).pack(pady=10)
        ttk.Label(step3, text="1. 点击 '选择归一化excel文件' 按钮，选择LC_MAX.xlsx",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)
        ttk.Label(step3, text="2. 从菜单 '模型选择' 中选择合适的机器学习模型",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)
        ttk.Label(step3, text="3. 点击 '开始分析' 按钮开始训练过程",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)
        ttk.Label(step3, text="4. 训练完成后，查看生成的评估图表",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)

        # 第4步：样本预测
        step4 = ttk.Frame(wizard_tabs)
        wizard_tabs.add(step4, text="4. 样本预测")
        ttk.Label(step4, text="新样本预测", font=('Helvetica', 12, 'bold')).pack(pady=10)
        ttk.Label(step4, text="1. 模型训练完成后，点击 '选择要检测的txt文件' 按钮",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)
        ttk.Label(step4, text="2. 选择要分析的未知样本txt文件",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)
        ttk.Label(step4, text="3. 查看预测结果（HC或LC）及概率",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)
        ttk.Label(step4, text="4. 可点击 '查看模型详情' 了解模型参数",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)

        # 底部按钮
        button_frame = ttk.Frame(self.wizard_window)
        button_frame.pack(fill='x', padx=10, pady=10)

        # 创建"不再显示"复选框
        show_again_var = tkinter.BooleanVar(value=self.show_wizard_on_startup)
        ttk.Checkbutton(button_frame, text="启动时显示此向导",
                        variable=show_again_var).pack(side='left')

        # 创建关闭按钮
        def close_wizard():
            self.show_wizard_on_startup = show_again_var.get()
            self.save_config()
            self.wizard_window.destroy()
            self.wizard_window = None

        ttk.Button(button_frame, text="开始使用",
                   command=close_wizard).pack(side='right')
    
    def show_about(self):
        """显示关于信息"""
        about_window = tkinter.Toplevel(self.root)
        about_window.title("关于诊断分析工具")
        about_window.geometry("400x300")
        about_window.resizable(False, False)

        ttk.Label(about_window, text="诊断分析工具", font=('Helvetica', 14, 'bold')).pack(pady=10)
        ttk.Label(about_window, text="版本: 1.0", font=('Helvetica', 10)).pack(pady=5)
        ttk.Label(about_window, text="本工具用于质谱数据分析和疾病诊断模型构建。",
                  wraplength=350).pack(pady=10)
        ttk.Label(about_window, text="支持多种机器学习模型，包括逻辑回归、随机森林、神经网络、PLS回归等。",
                  wraplength=350).pack(pady=5)

        ttk.Button(about_window, text="确定", command=about_window.destroy).pack(pady=20)
