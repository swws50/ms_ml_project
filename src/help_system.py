# help_system.py - 帮助系统和进度跟踪模块

# 标准库导入
import json
import os

# 第三方库导入
import customtkinter as ctk

# 本地模块导入
from utils import log_message, set_window_icon


class HelpSystem:
    """统一的帮助系统类 - 完整功能实现"""

    def __init__(self, root, config_file="../outputs/help_config.json"):
        self.root = root
        self.config_file = config_file
        self.active_tooltips = {}  # 跟踪活动的提示窗口

        # 步骤进度跟踪
        self.steps = [
            {"id": "preprocess_data", "name": "原始数据预处理", "completed": False},
            {"id": "select_data", "name": "选择已整合数据文件", "completed": False},
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
            "start_preprocessing": "开始数据预处理流程\n包括文件分类和智能峰发现\n处理完成后自动生成归一化CSV文件",
            # 数据预处理相关
            "select_files": "智能提峰：自动识别并提取最优特征峰",

            # 训练相关
            "select_excel": "选择已预处理的Excel数据文件\n第一行应为类别标签标签",
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
            "preprocess_data": "💡 下一步：点击 '开始数据预处理' 处理原始txt文件",
            "select_data": "💡 下一步：选择预处理生成的归一化CSV文件",
            "select_model": "💡 下一步：从 '模型选择' 中选择合适的机器学习算法",
            "train_model": "💡 下一步：点击 '开始训练' 按钮开始训练模型",
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
                    self.show_wizard_on_startup = config.get(
                        'show_wizard_on_startup', True)
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
        self.progress_frame = ctk.CTkFrame(
            parent_frame, corner_radius=8, height=50)
        self.progress_frame.grid(
            row=row, column=column, columnspan=columnspan, sticky='ew', padx=5, pady=5)

        # 标题
        title_label = ctk.CTkLabel(self.progress_frame, text="操作进度:",
                                   font=ctk.CTkFont(size=12, weight="bold"))
        title_label.pack(side='left', padx=10, pady=10)

        # 步骤指示器容器
        steps_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        steps_frame.pack(side='left', padx=10, pady=5)

        # 创建步骤标签
        self.progress_labels = []
        for i, step in enumerate(self.steps):
            # 步骤圆圈
            step_circle = ctk.CTkLabel(steps_frame, text=str(i+1),
                                       width=30, height=30,
                                       font=ctk.CTkFont(
                                           size=10, weight="bold"),
                                       corner_radius=15)
            step_circle.pack(side='left', padx=2)

            # 步骤名称
            step_name = ctk.CTkLabel(steps_frame, text=step['name'],
                                     font=ctk.CTkFont(size=10))
            step_name.pack(side='left', padx=(0, 10))

            # 箭头（除了最后一个步骤）
            if i < len(self.steps) - 1:
                arrow = ctk.CTkLabel(steps_frame, text="→",
                                     font=ctk.CTkFont(size=12))
                arrow.pack(side='left', padx=2)

            self.progress_labels.append((step_circle, step_name))

            # 当前步骤提示
        self.progress_indicator = ctk.CTkLabel(self.progress_frame,
                                               text=self.step_hints.get(
                                                   self.steps[0]['id'], ""),
                                               font=ctk.CTkFont(size=10),
                                               text_color="blue")
        self.progress_indicator.pack(side='right', padx=10, pady=10)

        # 初始化显示
        self.update_progress_display()

    def update_progress_display(self):
        """更新进度显示"""
        if not self.progress_labels:
            return

        for i, (circle, name) in enumerate(self.progress_labels):
            if i < self.current_step_index:
                # 已完成的步骤 - 绿色
                circle.configure(fg_color="#90EE90", text_color="black")
                name.configure(text_color="green", font=ctk.CTkFont(
                    size=10, weight="normal"))
            elif i == self.current_step_index:
                # 当前步骤 - 蓝色高亮
                circle.configure(fg_color="#87CEEB", text_color="black")
                name.configure(text_color="blue",
                               font=ctk.CTkFont(size=10, weight="bold"))
            else:
                # 未完成的步骤 - 灰色
                circle.configure(fg_color="#D3D3D3", text_color="gray")
                name.configure(text_color="gray", font=ctk.CTkFont(
                    size=10, weight="normal"))

            # 更新提示信息
            if self.current_step_index < len(self.steps):
                current_step_id = self.steps[self.current_step_index]['id']
                hint_text = self.step_hints.get(current_step_id, "")
                if self.progress_indicator:
                    self.progress_indicator.configure(text=hint_text)

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

    def get_current_step(self):
        """获取当前步骤信息"""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def add_hover_tip(self, widget, key_or_text, custom_style=None, delay_ms=1000):
        """
        为控件添加悬停提示 - 延迟显示版本

        参数:
            widget: tkinter控件
            key_or_text: 配置键名或直接的提示文本
            custom_style: 自定义样式字典（暂时保留，与CTk兼容）
            delay_ms: 延迟显示时间（毫秒），默认2000ms（2秒）
        """
        # 获取提示文本
        if key_or_text in self.help_texts:
            tip_text = self.help_texts[key_or_text]
        else:
            tip_text = key_or_text

        # 为每个控件创建一个定时器引用
        timer_id = None

        def show_tip_delayed():
            """延迟显示提示"""
            # 先清理所有可能存在的旧提示
            self.hide_all_tips()

            # 检查控件是否还有效
            try:
                x = widget.winfo_rootx() + 20
                y = widget.winfo_rooty() + widget.winfo_height() + 5
            except:
                return  # 控件已被销毁，直接返回

            # 创建提示窗口
            tip_window = ctk.CTkToplevel(widget)
            tip_window.wm_overrideredirect(True)
            tip_window.wm_geometry(f"+{x}+{y}")

            # 设置窗口属性
            tip_window.attributes('-topmost', True)
            tip_window.focus_set = lambda: None  # 禁用焦点获取

            # 创建提示标签
            tip_label = ctk.CTkLabel(tip_window, text=tip_text,
                                     fg_color="#FFFFDD", text_color="black",
                                     font=ctk.CTkFont(size=9), corner_radius=5)
            tip_label.pack(padx=8, pady=5)

            # 保存引用
            self.active_tooltips[widget] = tip_window

            # 添加自动销毁定时器（10秒后自动销毁，防止永久残留）
            tip_window.after(10000, lambda: self.hide_tip(widget))

        def on_enter(event):
            """鼠标进入时启动定时器"""
            nonlocal timer_id
            # 取消之前的定时器（如果存在）
            if timer_id:
                try:
                    widget.after_cancel(timer_id)
                except:
                    pass

            # 设置延迟定时器
            timer_id = widget.after(delay_ms, show_tip_delayed)

        def on_leave(event):
            """鼠标离开时取消定时器并隐藏提示"""
            nonlocal timer_id
            # 取消定时器
            if timer_id:
                try:
                    widget.after_cancel(timer_id)
                except:
                    pass
                timer_id = None

            # 隐藏当前提示
            self.hide_tip(widget)

        def on_click(event):
            """点击时立即取消定时器并隐藏提示"""
            nonlocal timer_id
            # 取消定时器
            if timer_id:
                try:
                    widget.after_cancel(timer_id)
                except:
                    pass
                timer_id = None

            # 隐藏提示
            self.hide_tip(widget)

        def on_focus_out(event):
            """失去焦点时隐藏提示"""
            nonlocal timer_id
            if timer_id:
                try:
                    widget.after_cancel(timer_id)
                except:
                    pass
                timer_id = None
            self.hide_tip(widget)

        # 绑定事件
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        widget.bind("<Button-1>", on_click)      # 左键点击时隐藏
        widget.bind("<FocusOut>", on_focus_out)  # 失去焦点时隐藏

        return self  # 支持链式调用

    def hide_tip(self, widget):
        """隐藏指定控件的提示 - 改进版本"""
        if widget in self.active_tooltips:
            try:
                tip_window = self.active_tooltips[widget]
                if tip_window and tip_window.winfo_exists():
                    tip_window.destroy()
                del self.active_tooltips[widget]
            except Exception:
                # 如果销毁失败，强制从字典中移除
                try:
                    del self.active_tooltips[widget]
                except:
                    pass

                    pass

    def hide_all_tips(self):
        """隐藏所有提示 - 改进版本"""
        # 创建副本以避免在迭代时修改字典
        tips_to_remove = list(self.active_tooltips.keys())
        for widget in tips_to_remove:
            self.hide_tip(widget)

        # 强制清空字典（防止残留）
        self.active_tooltips.clear()

    def show_wizard(self):
        """显示欢迎向导，指导用户使用程序的基本步骤"""
        if self.wizard_window and self.wizard_window.winfo_exists():
            self.wizard_window.lift()
            self.wizard_window.focus_force()
            self.wizard_window.tkraise()
            return

        self.wizard_window = ctk.CTkToplevel(self.root)
        self.wizard_window.title("使用向导")
        self.wizard_window.geometry("650x500")
        self.wizard_window.resizable(False, False)

        set_window_icon(self.wizard_window)

        # 更强力的窗口置顶方案
        # 1. 设置为置顶窗口
        self.wizard_window.attributes('-topmost', True)

        # 2. 获取焦点
        self.wizard_window.focus_force()

        # 3. 抬升窗口
        self.wizard_window.lift()
        self.wizard_window.tkraise()

        # 4. 设置为模态窗口（可选）
        self.wizard_window.grab_set()  # 模态窗口，必须先处理这个窗口

        # 5. 延迟取消置顶（保持用户友好）
        self.wizard_window.after(
            1000, lambda: self.wizard_window.attributes('-topmost', False))

        # 6. 窗口关闭时恢复主窗口焦点
        def on_closing():
            self.wizard_window.grab_release()  # 释放模态
            self.wizard_window.destroy()
            self.wizard_window = None
            self.root.lift()  # 恢复主窗口

        self.wizard_window.protocol("WM_DELETE_WINDOW", on_closing)

       # 创建选项卡视图
        wizard_tabs = ctk.CTkTabview(self.wizard_window, width=580, height=400)
        wizard_tabs.pack(fill='both', expand=True, padx=10, pady=10)

        # 第1步：程序介绍
        step1 = wizard_tabs.add("1. 介绍")
        ctk.CTkLabel(step1, text="诊断分析工具",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        ctk.CTkLabel(step1, text="本工具用于分析质谱数据并构建机器学习模型，以区分健康与患病样本。",
                     wraplength=550).pack(pady=5)
        ctk.CTkLabel(step1, text="使用流程包括：数据预处理、模型训练与评估、新样本预测。",
                     wraplength=550).pack(pady=5)

        # 第2步：数据预处理
        step2 = wizard_tabs.add("2. 数据预处理")
        ctk.CTkLabel(step2, text="数据预处理步骤",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(step2, text="1. 点击'数据预处理'按钮，打开文件分类窗口",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step2, text="2. 在弹出窗口中自定义两个类别的名称",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step2, text="3. 分别选择包含两类样本的文件夹",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step2, text="4. 确认预览信息，开始处理生成CSV文件",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step2, text="5. 等待智能峰发现处理完成，生成CSV文件",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)
        # 第3步：模型训练
        step3 = wizard_tabs.add("3. 模型训练")
        ctk.CTkLabel(step3, text="模型训练与评估",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(step3, text="1. 点击 '选择整理好的.csv文件' 按钮，选择选择生成的normalized_ms_data.csv文件",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step3, text="2. 从菜单 '模型选择' 中选择合适的机器学习模型",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step3, text="3. 点击 '开始训练' 按钮开始训练过程",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step3, text="4. 训练完成后，查看生成的评估图表",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)

        # 第4步：样本预测
        step4 = wizard_tabs.add("4. 样本预测")
        ctk.CTkLabel(step4, text="新样本预测",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(step4, text="1. 模型训练完成后，点击 '选择要检测的txt文件' 按钮",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step4, text="2. 选择要分析的未知样本txt文件",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step4, text="3. 查看预测结果及自定义类别的概率分布",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step4, text="4. 可点击 '查看模型详情' 了解模型参数",
                     wraplength=550).pack(anchor='w', padx=20, pady=2)

        # 底部按钮
        button_frame = ctk.CTkFrame(self.wizard_window, fg_color="transparent")
        button_frame.pack(fill='x', padx=10, pady=10)

        # 创建"不再显示"复选框
        show_again_var = ctk.BooleanVar(value=self.show_wizard_on_startup)
        ctk.CTkCheckBox(button_frame, text="启动时显示此向导",
                        variable=show_again_var).pack(side='left')

        # 创建关闭按钮
        def close_wizard():
            self.show_wizard_on_startup = show_again_var.get()
            self.save_config()
            self.wizard_window.destroy()
            self.wizard_window = None

        ctk.CTkButton(button_frame, text="开始使用",
                      command=close_wizard).pack(side='right')

    def show_about(self):
        """显示关于信息"""
        about_window = ctk.CTkToplevel(self.root)
        about_window.title("关于诊断分析工具")
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        set_window_icon(about_window)

        ctk.CTkLabel(about_window, text="诊断分析工具",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)
        ctk.CTkLabel(about_window, text="版本: 1.0",
                     font=ctk.CTkFont(size=12)).pack(pady=5)
        ctk.CTkLabel(about_window, text="本工具用于质谱数据分析和疾病诊断模型构建。",
                     wraplength=350).pack(pady=10)
        ctk.CTkLabel(about_window, text="支持多种机器学习模型，包括逻辑回归、随机森林、神经网络、PLS回归等。",
                     wraplength=350).pack(pady=5)

        ctk.CTkButton(about_window, text="确定",
                      command=about_window.destroy).pack(pady=20)
