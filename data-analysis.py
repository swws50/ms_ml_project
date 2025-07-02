# 基础数据处理
import os
import datetime
import numpy as np
import pandas as pd
import tqdm

# GUI组件
import tkinter
from tkinter import ttk, messagebox, filedialog, scrolledtext
from PIL import Image, ImageTk

# 机器学习核心库
import sklearn
from sklearn import metrics, svm
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (confusion_matrix, recall_score, classification_report, 
                            accuracy_score, balanced_accuracy_score, roc_curve, auc)

# 机器学习模型
from sklearn.linear_model import LogisticRegressionCV
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.cross_decomposition import PLSRegression

# 模型存取
from joblib import dump, load

# 可视化
import matplotlib.pyplot as plt
import seaborn as sns


from tkinter import ttk
import json

class HelpSystem:
    """统一的帮助系统类 - 完整功能实现"""
    
    def __init__(self, root, config_file="help_config.json"):
        self.root = root
        self.config_file = config_file
        self.active_tooltips = {}  # 跟踪活动的提示窗口
        
        # 当前步骤跟踪
        self.current_step = "select_file"
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
            """
            事件适配 — tkinter的事件绑定会传递一个event参数
            调用实际隐藏函数 转发给hide_tip()方法
            为什么需要这个包装：因为widget.bind("<Leave>", hide_tip_event)需要一个接受event参数的函数
            """
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
        ttk.Label(step1, text="诊断分析工具", font=(
            'Helvetica', 14, 'bold')).pack(pady=10)
        ttk.Label(step1, text="本工具用于分析质谱数据并构建机器学习模型，以区分HC与LC样本。",
                  wraplength=550).pack(pady=5)
        ttk.Label(step1, text="使用流程包括：数据预处理、模型训练与评估、新样本预测。",
                  wraplength=550).pack(pady=5)

        # 第2步：数据预处理
        step2 = ttk.Frame(wizard_tabs)
        wizard_tabs.add(step2, text="2. 数据预处理")
        ttk.Label(step2, text="数据预处理步骤", font=(
            'Helvetica', 12, 'bold')).pack(pady=10)
        ttk.Label(step2, text="1. 点击菜单 '数据预处理' -> '选择处理文件'",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)
        ttk.Label(step2, text="2. 选择原始的txt格式质谱数据文件",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)
        ttk.Label(step2, text="3. 等待处理完成，生成LC_MAX.xlsx文件",
                  wraplength=550).pack(anchor='w', padx=20, pady=2)

        # 第3步：模型训练
        step3 = ttk.Frame(wizard_tabs)
        wizard_tabs.add(step3, text="3. 模型训练")
        ttk.Label(step3, text="模型训练与评估", font=(
            'Helvetica', 12, 'bold')).pack(pady=10)
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
        ttk.Label(step4, text="新样本预测", font=(
            'Helvetica', 12, 'bold')).pack(pady=10)
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

        ttk.Label(about_window, text="诊断分析工具", font=(
            'Helvetica', 14, 'bold')).pack(pady=10)
        ttk.Label(about_window, text="版本: 1.0",
                  font=('Helvetica', 10)).pack(pady=5)
        ttk.Label(about_window, text="本工具用于质谱数据分析和疾病诊断模型构建。",
                  wraplength=350).pack(pady=10)
        ttk.Label(about_window, text="支持多种机器学习模型，包括逻辑回归、随机森林、神经网络、PLS回归等。",
                  wraplength=350).pack(pady=5)

        ttk.Button(about_window, text="确定",
                   command=about_window.destroy).pack(pady=20)
    
    def create_workflow_diagram(self, parent):
        """创建简单的工作流程图"""
        canvas = tkinter.Canvas(parent, width=700, height=80, bg='white')
        canvas.pack(padx=10, pady=5)

        # 绘制三个步骤框
        canvas.create_rectangle(50, 20, 200, 60, fill='lightblue', outline='blue')
        canvas.create_rectangle(250, 20, 400, 60, fill='lightgreen', outline='green')
        canvas.create_rectangle(450, 20, 600, 60, fill='lightyellow', outline='orange')

        # 添加文字
        canvas.create_text(125, 40, text="1. 数据预处理",
                           font=('Helvetica', 10, 'bold'))
        canvas.create_text(325, 40, text="2. 模型训练与评估",
                           font=('Helvetica', 10, 'bold'))
        canvas.create_text(525, 40, text="3. 样本预测", font=('Helvetica', 10, 'bold'))

        # 绘制箭头
        canvas.create_line(200, 40, 250, 40, arrow=tkinter.LAST,
                           width=2, fill='blue')
        canvas.create_line(400, 40, 450, 40, arrow=tkinter.LAST,
                           width=2, fill='green')
    
    def update_progress(self, step_key):
        """更新当前步骤"""
        self.current_step = step_key
        # 可以在这里添加进度指示器的更新逻辑
        pass
    
    def setup_all_tooltips(self):
        """为主程序的所有控件设置悬停提示的便捷方法"""
        # 这个方法可以在create_gui中调用，统一设置所有提示
        # 由于控件是在create_gui中创建的，这里只提供接口
        pass

# 全局日志函数
def log_message(message, level="INFO"):
    """增强的日志函数，支持不同级别"""
    global info_text, root
    if info_text is not None:
        # 使用简单符号
        if level == "ERROR":
            formatted_message = f"x 错误: {message}"
        elif level == "WARNING": 
            formatted_message = f"! 警告: {message}"
        elif level == "SUCCESS":
            formatted_message = f"√ 成功: {message}"
        elif level == "INFO":
            formatted_message = f"• 信息: {message}"
        else:
            formatted_message = message
            
        info_text.insert(tkinter.END, formatted_message + "\n")
        info_text.see(tkinter.END)
        if root is not None:
            root.update()
    else:
        print(message)


def clear_log():
    """清空日志信息"""
    global info_text
    if info_text is not None:
        info_text.delete(1.0, tkinter.END)


# 函数：处理原始数据
def process_file(file_name, X):
    """
    处理原始光谱数据文件，提取指定m/z值附近的最大信号强度。
    
    对每个指定的m/z值，在其±0.2的范围内查找最大信号强度，并进行归一化处理。
    这个函数适用于质谱数据的预处理，用于提取特定质谱峰的特征。
    
    参数:
        file_name (str): 原始数据文件路径，文件应为以空白分隔的CSV格式
        X (list): 待提取的m/z值列表
        
    返回:
        pd.DataFrame: 包含两列的DataFrame:
            - 'm/z': 指定的m/z值
            - 'Max_Value': 对应m/z值范围内的最大归一化信号强度
            
    注意:
        - 输入文件应为两列格式：第一列为m/z值，第二列为信号强度
        - 信号强度会除以871.7725进行归一化
        - 如果指定范围内没有数据点，则对应的Max_Value为None
    """
    raw_data = pd.read_csv(file_name, sep=r'\s+', header=None)
    results = []
    for x in X:
        lower_bound = x - 0.2
        upper_bound = x + 0.2

        filtered_df = raw_data[(raw_data[0] >= lower_bound)
                               & (raw_data[0] <= upper_bound)]

        max_value = filtered_df[1].div(
            871.7725).max() if not filtered_df.empty else None

        results.append([x, max_value])
    return pd.DataFrame(results, columns=['m/z', 'Max_Value'])



# 函数：选择并归一化原始数据
def select_and_process_files():
    """
    通过图形界面选择并处理多个原始光谱数据文件，生成用于机器学习的特征矩阵。
    
    此函数打开文件选择对话框，允许用户选择多个txt格式的原始数据文件。
    对每个文件，提取预定义的47个m/z值处的峰值强度，并将结果合并为一个特征矩阵。
    结果保存为Excel文件，其中行为特征(m/z值)，列为样本，包含样本类别标签。
    
    参数:
        无
        
    返回:
        无: 结果直接保存为'LC_MAX.xlsx'文件
        
    全局变量依赖:
        root: tkinter根窗口对象
        
    副作用:
        - 在GUI中创建和更新进度条和标签
        - 生成并保存Excel文件
        - 显示处理完成的消息框
        
    注意:
        - 默认提取48个特征(包括'class'和47个m/z值)
        - 样本类别从文件名的前两个字符获取(LC或HC)
    """
    file_paths = filedialog.askopenfilenames(
        title="选择要分析的文件", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))

    if file_paths:
        log_message("开始处理原始数据文件...")
        # 定义X列表
        X = ['class', 563.43, 887.77, 804.50, 811.54, 619.52, 647.56, 805.51, 591.47, 806.53, 579.38, 771.60, 797.60, 769.59, 655.39, 695.57, 731.54, 565.36, 929.75,
             759.48, 697.59, 807.55, 671.56, 673.57, 879.76, 931.77, 953.77, 641.50, 881.77, 901.73, 927.68, 799.59, 763.52, 903.77, 883.70, 979.80, 955.71,
             675.59, 669.52, 905.77, 643.53, 825.70, 639.41, 971.65, 981.84, 869.71, 925.73, 907.77, 507.27]

        X_series = pd.Series(data=X, index=X)
        all_results = pd.DataFrame(X_series, columns=['m/z'])

        # 创建进度条
        progress_label = tkinter.Label(root, text="进度: 0%")
        progress_label.grid(row=8, column=0, columnspan=2, sticky='ew')
        progress_bar = ttk.Progressbar(root, length=200, mode='determinate')
        progress_bar.grid(row=9, column=0, columnspan=2, sticky='ew')

        progress_label.config(text="正在处理文件...")
        progress_bar['maximum'] = len(file_paths)

        # 处理每个文件，并将结果添加到all_results中
        for index, file_path in enumerate(file_paths, 1):
            file_result = process_file(
                file_path, [x for x in X if x != 'class'])
            file_result.set_index('m/z', inplace=True) 
            file_result.columns = [os.path.splitext(
                os.path.basename(file_path))[0]]  # 使用文件名作为列名
            file_result.loc['class'] = [os.path.splitext(
                os.path.basename(file_path))[0][:2]]
            all_results = pd.concat([all_results, file_result], axis=1)
            log_message(f"已处理文件 {index}/{len(file_paths)}: {os.path.basename(file_path)}")

            # 更新进度条
            progress_bar['value'] = index
            progress_label.config(text=f"正在处理: {index}/{len(file_paths)}")
            root.update()

        #增加数据持久化的异常处理
        try:
            # 检查LC_MAX.xlsx是否已存在
            original_file_path = 'LC_MAX.xlsx'
            if os.path.exists(original_file_path):
                log_message("发现已存在的文件，正在创建备份...", "INFO")
                
                # 获取当前日期
                current_date = datetime.datetime.now().strftime("%Y%m%d")
                # 构建新的文件名
                backup_file_path = f'LC_MAX-{current_date}.xlsx'

                # 如果备份文件也存在，为避免覆盖，添加编号
                counter = 1
                while os.path.exists(backup_file_path):
                    backup_file_path = f'LC_MAX-{current_date}_{counter}.xlsx'
                    counter += 1

                try:
                    # 重命名旧文件
                    os.rename(original_file_path, backup_file_path)
                    log_message(f"备份完成: {backup_file_path}", "SUCCESS")
                except Exception as e:
                    log_message(f"无法重命名已有文件: {str(e)}，将尝试直接保存新文件", "WARNING")

            # 保存新文件
            log_message("正在保存处理结果...", "INFO")
            all_results.to_excel(original_file_path,
                                 index=True, columns=all_results.columns[1:])
            log_message(f"数据处理完成！结果已保存为 {original_file_path}", "SUCCESS")

            progress_bar.grid_remove()
            progress_label.grid_remove()

        except PermissionError:
            log_message("无法保存文件，可能是文件已被打开或没有写入权限", "ERROR")

            # 为用户提供选择其他位置的选项
            response = messagebox.askyesno("权限错误", "无法保存文件到当前位置。\n是否选择其他位置保存文件？")
            if response:
                log_message("用户选择保存到其他位置", "INFO")
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx")],
                    initialfile="LC_MAX.xlsx"
                )

                if save_path:
                    try:
                        all_results.to_excel(
                            save_path, index=True, columns=all_results.columns[1:])
                        log_message(f"数据处理完成！结果已保存为 {save_path}", "SUCCESS")
                        messagebox.showinfo("保存成功", f"文件已成功保存到:\n{save_path}")
                    except Exception as e:
                        log_message(f"保存到新位置时出错: {str(e)}", "ERROR")
                        messagebox.showerror("保存失败", f"保存文件时出错:\n{str(e)}")

                    progress_bar.grid_remove()
                    progress_label.grid_remove()
                else:
                    log_message("用户取消了文件保存操作", "WARNING")
            else:
                log_message("用户选择不保存到其他位置", "WARNING")
                
        except Exception as e:
            log_message(f"保存文件时出错: {str(e)}", "ERROR")
            messagebox.showerror("未知错误", f"保存文件时发生未知错误:\n{str(e)}")
            progress_bar.grid_remove()
            progress_label.grid_remove()

    else:
        log_message("未选择任何文件", "WARNING")



# 函数：选择归一化好的文件
def open_excel_file(normalization_label, start_button, progress_bar):
    """
    打开并加载已处理的特征矩阵Excel文件，准备机器学习模型训练。

    此函数打开文件选择对话框，允许用户选择一个Excel文件(通常是由select_and_process_files函数生成的)。
    加载数据后，提取特征矩阵和类别标签，并进行必要的预处理使其满足模型训练要求。

    参数:
        normalization_label (tkinter.Label): 用于显示文件选择状态的标签
        start_button (tkinter.Button): 训练开始按钮，文件加载成功后启用
        progress_bar (ttk.Progressbar): 进度条组件，文件加载后重置

    返回:
        无: 结果存储在全局变量中

    全局变量修改:
        row: 设置为特征矩阵，形状为(n_samples, n_features)
        column: 设置为类别标签向量，形状为(n_samples,)
        df: 设置为原始加载的DataFrame

    注意:
        - 期望Excel文件格式：第一行为类别标签(HC或LC)，随后各行为特征值
        - 类别标签会被映射为数值：HC=0, LC=1
        - 如果发现未知类别，将显示警告消息
    """
    global row, column, df
    
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xls *.xlsx")])
    
    if not file_path:
        log_message("用户取消了文件选择")
        return
    
    log_message(f"正在加载文件: {os.path.basename(file_path)}")
    
    try:
        df = pd.read_excel(file_path, header=0)
        df = df.iloc[:, 1:]

        if df.empty:
            normalization_label.config(text="文件未选择")
            log_message("错误：所选文件为空，请选择有效的数据文件")
            return

        # 检查文件是否具有预期的格式
        if df.shape[0] < 2:  # 至少需要类别行和一个特征行
            error_msg = "Excel文件格式不正确，至少需要类别行和特征行"
            messagebox.showerror("格式错误", error_msg)
            log_message(f"错误：{error_msg}")
            return

        # 文件加载成功，更新UI状态
        normalization_label.config(text="已选择")
        start_button.config(state='normal')
        progress_bar['value'] = 0
        log_message("数据文件已成功加载")

        # 处理数据
        row = df.iloc[1:, :].values.T
        ylabels = df.iloc[0, :].values
        ylabels = pd.Series(ylabels)

        log_message(f"数据形状: {row.shape}, 样本数: {row.shape[0]}, 特征数: {row.shape[1]}")
        log_message(f"类别标签统计: {dict(ylabels.value_counts())}")

        # 确保有足够的每类样本
        if len(ylabels.value_counts()) < 2:
            warning_msg = "数据中只有一种类别，需要至少两种类别才能训练模型"
            messagebox.showwarning("警告", warning_msg)
            log_message(f"警告：{warning_msg}")

        # 进行标签编码
        class_mapping = {"HC": 0, "LC": 1}
        column = np.array([class_mapping.get(label, -1) for label in ylabels])

        # 检查未知类别
        if -1 in column:
            unknown_classes = set(ylabels[column == -1])
            warning_msg = f"发现未知类别: {unknown_classes}，请检查您的类别映射"
            log_message(f"警告：{warning_msg}")
            messagebox.showwarning("警告", warning_msg)
        else:
            log_message("标签编码完成，数据预处理成功")

    except FileNotFoundError:
        error_msg = f"文件未找到: {file_path}"
        messagebox.showerror("文件错误", error_msg)
        log_message(f"错误：{error_msg}")
    except pd.errors.EmptyDataError:
        error_msg = "Excel文件为空或格式不正确"
        messagebox.showerror("数据错误", error_msg)
        log_message(f"错误：{error_msg}")
    except Exception as e:
        error_msg = f"加载Excel文件时出错: {str(e)}"
        messagebox.showerror("未知错误", error_msg)
        log_message(f"错误：{error_msg}")
        
        

def on_selcted(var_selection, display_label):
    """
     处理模型选择变化的回调函数，更新全局模型选择和显示标签。
    
    当用户从下拉菜单中选择不同的机器学习模型时，此函数将被调用。
    它更新全局变量以存储当前选择的模型类型，并更新UI显示。
    
    参数:
        var_selection (tkinter.StringVar): 包含当前选择的模型名称的变量
        display_label (tkinter.Label): 用于显示当前选择的标签组件
        
    返回:
        无: 修改全局变量和UI
        
    全局变量修改:
        exact_selection: 设置为当前选择的模型名称
    """
    global exact_selection
    exact_selection = var_selection.get()
    display_label.config(text='您选择了: '+exact_selection)



# 使用ROC曲线返回最优分类阈值
def find_optimal_threshold(y_true, y_pred_proba):
    """
    基于ROC曲线分析寻找最优分类阈值。
    
    通过计算ROC曲线上的所有点，找到约登指数(Youden's J statistic)最大的点作为最优阈值。
    约登指数定义为: J = 灵敏度 + 特异度 - 1 = TPR - FPR
    此方法适用于需要将连续预测值(如回归模型输出)转换为二分类结果的情况。
    
    参数:
        y_true (array-like): 真实类别标签，通常为0和1
        y_pred_proba (array-like): 模型的连续预测值或概率估计
        
    返回:
        float: 最优分类阈值，应用此阈值可获得最佳的综合分类性能
        
    注意:
        - 此函数常用于PLS回归等输出连续值的模型
        - 约登指数最大的点平衡了灵敏度和特异度
        - 在不同应用场景中，可能需要其他标准来确定最优阈值
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    # 找到最优点（约登指数最大的点）
    optimal_idx = np.argmax(tpr - fpr)
    return thresholds[optimal_idx]

# 主功能函数：监督训练 + 更新训练部分UI
def predict_by(progress_label, progress_bar, balanced_accuracy_train_label, balanced_accuracy_test_label, model_save_status_label):
    """不再使用info_text参数，直接在函数内部处理日志显示和更新UI组件"""
    """
    执行机器学习模型的训练、评估和保存，并通过GUI界面显示训练进度和结果。
    
    此函数通过重复训练模型500次来获得稳定的性能评估，使用交叉验证（80%训练/20%测试）。
    每次迭代中会跟踪多种评估指标，并最终保存性能最佳的模型。特别适用于
    二分类问题（HC vs LC），支持多种分类器，包括普通分类器和PLS回归模型。
    
    参数:
        progress_label (tkinter.Label): 用于显示训练进度百分比的标签组件
        progress_bar (ttk.Progressbar): 用于可视化训练进度的进度条组件
        balanced_accuracy_train_label (tkinter.Label): 显示训练集平均平衡准确率的标签
        balanced_accuracy_test_label (tkinter.Label): 显示测试集平均平衡准确率的标签
        info_text (tkinter.Text): 用于显示训练日志信息的文本框组件
        model_save_status_label (tkinter.Label): 显示模型保存状态的标签
        
    全局变量依赖:
        row: 特征数据数组，形状为(n_samples, n_features)
        column: 类别标签数组，形状为(n_samples,)
        df: 原始数据DataFrame
        exact_selection: 当前选择的模型类型名称
        class_dict: 包含各种模型参数配置的字典
        best_model: 存储性能最佳的模型实例
        
    返回:
        None: 函数结果通过UI组件和文件保存表现
        
    副作用:
        - 创建并保存多个CSV和NPY文件记录训练结果
        - 保存性能最佳的模型到'best_model.joblib'
        - 更新UI组件显示训练结果
        - 调用visualize_performance函数生成可视化图表
        
    注意:
        - 使用前确保已正确设置全局变量row、column和exact_selection
        - 对于PLSRegression模型，使用ROC曲线寻找最优分类阈值
        - 支持的评估指标包括：平衡准确率、混淆矩阵、精确率、召回率、F1分数和ROC曲线
    """
    global row, column, df, fpr_list, tpr_list, thresholds_list, auc_list, best_model
    
    # 清空日志旧信息
    clear_log()
    log_message("=> 开始模型训练...")
    
    # 数据验证检查
    try:
        # 检查数据是否正确加载
        if 'row' not in globals() or 'column' not in globals() or row is None or column is None:
            log_message("错误: 数据未正确加载")
            messagebox.showerror("数据错误", "未找到有效训练数据，请先选择Excel文件。")
            return

        # 检查样本数量
        n_samples = row.shape[0] if hasattr(row, 'shape') else len(row)
        log_message(f"加载的样本数量: {n_samples}")

        if n_samples < 5:  # 设定一个最小样本数
            error_msg = f"样本数量不足（当前只有{n_samples}个样本），训练机器学习模型需要足够的样本数量。"
            log_message(f"错误: {error_msg}")
            messagebox.showerror("样本数量不足", f"检测到只有{n_samples}个样本，无法进行训练。\n请确保您已正确加载包含多个样本的数据文件。")
            progress_bar['value'] = 0
            return

        # 检查类别分布
        unique_classes = np.unique(column)
        log_message(f"检测到的类别: {unique_classes}")

        if len(unique_classes) < 2:
            error_msg = f"数据中只包含一种类别 ({unique_classes[0]})，分类模型需要至少两种不同的类别。"
            log_message(f"错误: {error_msg}")
            messagebox.showerror("类别不足", "数据中只包含一种类别，无法训练分类模型。\n请确保您的数据包含不同类别的样本（例如HC和LC）。")
            progress_bar['value'] = 0
            return

        # 检查模型选择
        if 'exact_selection' not in globals() or exact_selection is None:
            log_message("错误: 未选择模型类型")
            messagebox.showerror("模型选择错误", "请先选择一个机器学习模型类型。")
            return

        log_message(f"使用模型: {exact_selection}")
        log_message("数据验证通过，开始训练...")

    except Exception as e:
        log_message(f"数据验证出错: {str(e)}")
        messagebox.showerror("验证错误", f"数据验证时出现错误：{str(e)}")
        return

    # 初始化数据结构
    balanced_accuracy_train = []  
    balanced_accuracy_test = []
    trained_models = []
    fpr_list = []
    tpr_list = []
    thresholds_list = [] # 记录训练结果的阈值
    auc_list = []
    Fscores = np.zeros((500, 4))
    thresholds_used = [] # 用于二值化的阈值
    confusion_matrixs = np.zeros((500, 4))
    best_score = -1 # 用于跟踪最佳模型性能

    try:
        # 主训练循环500次
        log_message("开始500轮训练循环...")
        for i in tqdm.tqdm(range(500)):
            percentage = (i + 1) / 500 * 100
            progress_label.config(text='分析进度: {0:.2f}%'.format(percentage))
            progress_bar['value'] = percentage
            root.update()

            # 划分20%为测试集
            train_X, test_X, train_y, test_y = train_test_split(
                row, column, test_size=0.2, stratify=column) 
            
            # 模型初始化和训练
            params = class_dict[exact_selection]
            current_model = globals()[exact_selection](**params) 
            current_model.fit(train_X, train_y)

            # 模型预测处理
            if isinstance(current_model, PLSRegression):
                # 如果模型为PLSRegression，则需要对预测值进行ROC二值化处理    
                train_pred_raw = current_model.predict(train_X).flatten()
                test_pred_raw = current_model.predict(test_X).flatten()
        
                # 使用训练集寻找最优阈值
                optimal_threshold = find_optimal_threshold(train_y, train_pred_raw)
                thresholds_used.append(optimal_threshold)
                # 应用阈值进行二值化
                train_y_pred = (train_pred_raw > optimal_threshold).astype(int)
                text_y_pred = (test_pred_raw > optimal_threshold).astype(int)    
            else: 
                # 其他模型直接预测       
                train_y_pred = current_model.predict(train_X)
                text_y_pred = current_model.predict(test_X)
            
            # 性能评估
            fpr, tpr, thresholds = roc_curve(test_y, text_y_pred)
            fpr_list.append(fpr)
            tpr_list.append(tpr)
            thresholds_list.append(thresholds)
            auc_score = auc(fpr, tpr)
            auc_list.append(auc_score)

            # 使用balanced_accuracy_score保持评估一致性
            balanced_accuracy_train.append(balanced_accuracy_score(train_y, train_y_pred))
            balanced_accuracy_test.append(balanced_accuracy_score(test_y, text_y_pred))

            confusion_matrixs[i] = confusion_matrix(test_y, text_y_pred).flatten()
            Fscore = metrics.classification_report(test_y, text_y_pred, labels=[0, 1], output_dict=True)

            Fscores[i][0] = Fscore["weighted avg"]["precision"]
            Fscores[i][1] = Fscore["weighted avg"]["recall"]
            Fscores[i][2] = Fscore["weighted avg"]["f1-score"]

            trained_models.append(current_model)

            # 覆写保存最佳模型
            if balanced_accuracy_test[i] > best_score:
                best_score = balanced_accuracy_test[i]
                best_model = current_model
                log_message(f"发现更高分数：{best_score:.4f} (迭代{i+1})")

        log_message(f"\n训练完成！最优模型分数：{best_score:.4f}")  
              
        # 循环结束后保存最终的最优模型
        if best_model is not None:
            dump(best_model, 'best_model.joblib')
            log_message(f"最优模型已保存，测试集分数: {best_score:.4f}")
            model_save_status_label.config(text=f'模型保存状态: 已保存 (分数: {best_score:.4f})', fg='green')
        else:
            log_message("警告：未训练出有效模型")
            model_save_status_label.config(text='模型保存状态: 保存失败', fg='red')
      
        # 保存训练数据和指标
        log_message("保存训练结果文件...")
        np.savetxt("Con_matrix_SVM.csv", confusion_matrixs, delimiter=",")
        np.savetxt("Fscore_SVM.csv", Fscores, delimiter=",")
        np.savetxt("2C_auc_SVM.csv", auc_list, delimiter=",")
        np.save("fpr_values.npy", np.array(fpr_list, dtype=object))
        np.save("tpr_values.npy", np.array(tpr_list, dtype=object))
        np.save("thresholds_values.npy", np.array(thresholds_list, dtype=object))
        
        # 如果使用了PLS回归，则额外保存阈值数据
        if len(trained_models) > 0 and isinstance(trained_models[0], PLSRegression) and len(thresholds_used) > 0:
            np.savetxt("PLS_optimal_thresholds.csv", thresholds_used, delimiter=",")
            mean_threshold = np.mean(thresholds_used)
            log_message(f"PLS回归平均最优阈值: {mean_threshold:.4f}")

        # 显示平均性能指标
        mean_balanced_accuracy_train = np.mean(balanced_accuracy_train)
        mean_balanced_accuracy_test = np.mean(balanced_accuracy_test)
        balanced_accuracy_train_label.config(text=f"平均训练集平衡精度: {mean_balanced_accuracy_train:.4f}")
        balanced_accuracy_test_label.config(text=f"平均测试集平衡精度: {mean_balanced_accuracy_test:.4f}")
        
        log_message(f"平均训练集平衡精度: {mean_balanced_accuracy_train:.4f}")
        log_message(f"平均测试集平衡精度: {mean_balanced_accuracy_test:.4f}")
        log_message("开始生成可视化图表...")
        
        # 传参进行可视化
        if len(trained_models) > 0 and isinstance(trained_models[0], PLSRegression) and len(thresholds_used) > 0:
            visualize_performance(balanced_accuracy_train, balanced_accuracy_test, Fscores, confusion_matrixs, fpr_list, tpr_list, auc_list, thresholds_used)
        else:
            visualize_performance(balanced_accuracy_train, balanced_accuracy_test, Fscores, confusion_matrixs, fpr_list=fpr_list, tpr_list=tpr_list, auc_list=auc_list)
            
        log_message("所有任务完成！")

    except Exception as e:
        log_message(f"训练过程中出现错误: {str(e)}")
        messagebox.showerror("训练错误", f"模型训练时出现错误：{str(e)}")
        progress_bar['value'] = 0
        model_save_status_label.config(text='模型保存状态: 训练失败', fg='red')



def visualize_performance(balanced_accuracy_train, balanced_accuracy_test, Fscores, confusion_matrixs, fpr_list, tpr_list, auc_list, thresholds_used=None):
    """
    可视化机器学习模型的多种性能指标并在GUI中显示结果。
    
    参数:
        balanced_accuracy_train: 训练集平衡准确率列表
        balanced_accuracy_test: 测试集平衡准确率列表
        Fscores: 包含加权平均精确率、召回率和F1分数的数组，形状为(n_iterations, 3)
        confusion_matrixs: 混淆矩阵数组，形状为(n_iterations, 4)
        fpr_list: 假阳性率列表，每个元素对应一次迭代的ROC曲线
        tpr_list: 真阳性率列表，每个元素对应一次迭代的ROC曲线
        auc_list: AUC值列表，每个元素对应一次迭代的ROC曲线AUC
        thresholds_used: 可选，PLS回归模型使用的最优阈值列表
        output_dir: 可选，图像保存路径，默认为当前目录
        dpi: 可选，图像DPI，默认为100
        
    返回:
        None: 函数将图像保存到指定目录并在GUI中显示
        
    注意:
        此函数依赖于全局变量root和notebook，需要在tkinter环境中运行
    """
    global root, notebook
    
    log_message("开始生成可视化图表...")
    
    try:
        # 生成准确率图表
        log_message("生成准确率对比图...")
        plt.figure(figsize=(8, 6))  # 使用版本2的较大尺寸
        plt.scatter(range(len(balanced_accuracy_train)), balanced_accuracy_train,
                    label='Training Balanced Accuracy', color='b', s=5)
        plt.scatter(range(len(balanced_accuracy_test)),
                    balanced_accuracy_test, label='Test Balanced Accuracy', color='r', s=5)
        plt.xlabel('Iteration')
        plt.ylabel('Balanced Accuracy')
        plt.legend()
        plt.title('Training and Test Balanced Accuracy over Iterations')
        plt.savefig('Training and Test Balanced Accuracy.png')
        plt.close()

        # 生成F1分数等指标图表
        log_message("生成精确率/召回率/F1分数图...")
        plt.figure(figsize=(8, 6))
        plt.scatter(range(len(Fscores)),
                    Fscores[:, 0], label='Weighted Avg Precision', s=5)
        plt.scatter(range(len(Fscores)),
                    Fscores[:, 1], label='Weighted Avg Recall', s=5)
        plt.scatter(range(len(Fscores)),
                    Fscores[:, 2], label='Weighted Avg F1-score', s=5)
        plt.xlabel('Iteration')
        plt.ylabel('Score')
        plt.legend()
        plt.title('Weighted Average Precision, Recall, and F1-score over Iterations')
        plt.savefig('Weighted Average Precision, Recall, and F1-score.png')
        plt.close()

        # 生成混淆矩阵图表
        log_message("生成混淆矩阵图...")
        reverse_class_mapping = {0: "HC", 1: "LC"}
        plt.figure(figsize=(6, 6))  # 使用版本2的较大尺寸
        mean_conf_matrix = confusion_matrixs.mean(axis=0).reshape((2, 2))
        plt.imshow(mean_conf_matrix, interpolation='nearest', cmap='Blues')
        plt.colorbar(fraction=0.046, pad=0.04)
        plt.xticks([0, 1], [reverse_class_mapping[0], reverse_class_mapping[1]])
        plt.yticks([0, 1], [reverse_class_mapping[0], reverse_class_mapping[1]])
        # 添加数值标签
        for i in range(2):
            for j in range(2):
                plt.text(j, i, f"{mean_conf_matrix[i, j]:.1f}", 
                        ha="center", va="center", color="black")
        plt.xlabel('Predicted Class')
        plt.ylabel('True Class')
        plt.title('Mean Confusion Matrix')
        plt.savefig('Mean Confusion Matrix.png')
        plt.close()

        # 生成ROC曲线
        log_message("生成ROC曲线图...")
        plt.figure(figsize=(8, 6))
        mean_fpr = np.linspace(0, 1, 100)
        mean_tpr = np.mean([np.interp(mean_fpr, fpr, tpr) for fpr, tpr in zip(fpr_list, tpr_list)], axis=0)
        plt.plot(mean_fpr, mean_tpr, color='red', lw=3, label=f'Mean ROC (AUC={np.mean(auc_list):.2f})')
        plt.plot([0, 1], [0, 1], color='gray', linestyle='--')  # 对角线
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Mean ROC Curve')
        plt.legend()
        plt.savefig('Mean ROC Curve.png')
        plt.close()
        
        # 如果有阈值数据，则生成阈值分布图
        threshold_file_exists = False
        if thresholds_used is not None and len(thresholds_used) > 0:
            log_message("生成PLS阈值分布图...")
            mean_threshold = np.mean(thresholds_used)
            std_threshold = np.std(thresholds_used)
            
            plt.figure(figsize=(8, 6), dpi=100)
            hist_data = plt.hist(thresholds_used, bins=20, color='skyblue', 
                             edgecolor='black', alpha=0.7)
        
            if isinstance(hist_data, tuple) and len(hist_data) > 0:
                y_max = max(hist_data[0]) * 1.1
            else:
                y_max = plt.ylim()[1] * 1.1
            # 添加平均阈值和默认阈值的竖线
            plt.axvline(x=mean_threshold, color='r', linestyle='--', 
                   label=f'Mean Threshold: {mean_threshold:.4f}')
            plt.axvline(x=0.5, color='g', linestyle='--', 
                   label='Default Threshold: 0.5')
            
            plt.xlabel('Threshold Value', fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            plt.legend(loc='upper right', fontsize=10)
            plt.title(f'PLS-DA Optimal Threshold Distribution (Mean={mean_threshold:.4f}, Std={std_threshold:.4f})', 
                  fontsize=12)
            plt.ylim(0, y_max)
            plt.tight_layout()
            plt.savefig('PLS_optimal_thresholds.png', dpi=100, bbox_inches='tight')
            plt.close()
            threshold_file_exists = True

        log_message("所有图表生成完成，正在创建显示界面...")

    except Exception as e:
        log_message(f"生成图表时出错: {str(e)}")
        messagebox.showerror("图表生成错误", f"生成可视化图表时出现错误：{str(e)}")
        return

    # 更新主窗口
    root.update()

    # 创建选项卡控件（销毁旧的）
    if 'notebook' in globals() and notebook is not None:
        try:
            notebook.destroy()
        except:
            pass
    
    try:
        notebook = ttk.Notebook(root)
        notebook.grid(row=6, column=0, columnspan=4, sticky='nsew')
        
        # 图表文件列表和对应的标签页名称
        chart_configs = [
            ('Training and Test Balanced Accuracy.png', '准确率'),
            ('Weighted Average Precision, Recall, and F1-score.png', '精确率/召回率/F1'),
            ('Mean Confusion Matrix.png', '混淆矩阵'),
            ('Mean ROC Curve.png', 'ROC曲线')
        ]
        
        # 如果有阈值数据，添加阈值分布图
        if threshold_file_exists:
            chart_configs.append(('PLS_optimal_thresholds.png', '阈值分布'))
        
        # 创建选项卡
        for chart_file, tab_name in chart_configs:
            if os.path.exists(chart_file):
                try:
                    # 创建选项卡框架
                    tab = ttk.Frame(notebook)
                    notebook.add(tab, text=tab_name)
                    
                    # 加载图像
                    image = Image.open(chart_file)
                    photo = ImageTk.PhotoImage(image)
                    
                    # 创建标签并显示图像（版本1的内存管理方式）
                    label = tkinter.Label(tab, image=photo)
                    label.image = photo  # 保持引用，防止被垃圾回收
                    label.pack(fill='both', expand=True)
                    
                    log_message(f"已加载图表: {tab_name}")
                    
                except Exception as e:
                    # 添加版本2的错误处理
                    log_message(f"加载图表 {tab_name} 时出错: {str(e)}")
                    # 创建错误显示的选项卡
                    tab = ttk.Frame(notebook)
                    notebook.add(tab, text=f"{tab_name}(错误)")
                    error_label = tkinter.Label(tab, text=f"无法加载图表: {chart_file}\n错误: {str(e)}", 
                                              fg="red", justify="center")
                    error_label.pack(fill='both', expand=True)
            else:
                # 文件不存在的错误处理
                log_message(f"警告: 图表文件不存在: {chart_file}")
                tab = ttk.Frame(notebook)
                notebook.add(tab, text=f"{tab_name}(缺失)")
                missing_label = tkinter.Label(tab, text=f"图表文件未找到:\n{chart_file}", 
                                            fg="orange", justify="center")
                missing_label.pack(fill='both', expand=True)
        
        log_message("可视化界面创建完成！")
        root.update()
        
    except Exception as e:
        log_message(f"创建可视化界面时出错: {str(e)}")
        messagebox.showerror("界面创建错误", f"创建可视化界面时出现错误：{str(e)}")
        return



def predict_unknown_sample(file_path,prediction_result_label):
    """支持多种类型的sklearn模型，包括:
    - 带predict_proba方法的分类器(如RandomForest, LogisticRegression)
    - 带decision_function方法的分类器(如默认SVM)
    - PLSRegression模型(需配合阈值进行概率转换)
    - 其他不提供概率估计的模型
    
    参数:
        model: 已训练的sklearn模型
        features: 样本特征，形状为 (1, n_features)
        
    返回:
        tuple: (prediction, probabilities)
            - prediction: 预测的类别标签 (0表示HC, 1表示LC)
            - probabilities: 各类别的概率数组 [HC概率, LC概率]
            
    注意:
        对于PLSRegression等回归模型，概率是通过Sigmoid函数转换得到，
        可能需要适当校准以获得更准确的概率估计。"""
    try:
        # 加载保存的模型
        loaded_model = load('best_model.joblib')
        
        if loaded_model is None:
            prediction_result_label.config(text="错误，未找到保存的模型文件", fg='red',font=('Helvetica', 12, 'bold'))
            
        # 定义要处理的特征列表（与训练时相同）
        X = [563.43, 887.77, 804.50, 811.54, 619.52, 647.56, 805.51, 591.47, 806.53, 579.38, 771.60, 797.60, 
             769.59, 655.39, 695.57, 731.54, 565.36, 929.75, 759.48, 697.59, 807.55, 671.56, 673.57, 879.76, 
             931.77, 953.77, 641.50, 881.77, 901.73, 927.68, 799.59, 763.52, 903.77, 883.70, 979.80, 955.71,
             675.59, 669.52, 905.77, 643.53, 825.70, 639.41, 971.65, 981.84, 869.71, 925.73, 907.77, 507.27]
        
        # 处理文件
        sample_data = process_file(file_path, X)
        
        # 准备预测数据 (转换为与训练数据相同的格式)
        sample_features = sample_data['Max_Value'].values.reshape(1, -1)

        

        def get_prediction_probability(model, features):
            """获取给定模型对特征的预测概率
            
            参数:
                model: 训练好的模型
                features: 样本特征
                
            返回:
                预测类别和概率数组 [类别0的概率, 类别1的概率]
            """
            # 针对不同类型的模型处理
            if isinstance(model, PLSRegression):
                # 1. PLS回归模型处理
                # 获取原始预测值
                raw_value = model.predict(features).flatten()[0]
                
                # 获取阈值
                try:
                    threshold = np.mean(np.loadtxt("PLS_optimal_thresholds.csv", delimiter=","))
                except:
                    threshold = 0.5
                    
                # 计算概率和预测类别
                prob1 = 1 / (1 + np.exp(-(raw_value - threshold) * 10))
                probs = np.array([1 - prob1, prob1])
                pred = 1 if raw_value > threshold else 0
                
            elif hasattr(model, 'predict_proba'):
                # 2. 有predict_proba方法的模型(大多数分类器)
                probs = model.predict_proba(features)[0]
                pred = model.predict(features)[0]
                
            elif hasattr(model, 'decision_function'):
                # 3. 有decision_function的模型(如SVM)
                decision_value = model.decision_function(features)
                
                # 确保决策值是标量(针对二分类)
                if isinstance(decision_value, np.ndarray):
                    decision_value = decision_value.flatten()[0]
                    
                # 转换为概率
                prob1 = 1 / (1 + np.exp(-decision_value))
                probs = np.array([1 - prob1, prob1])
                pred = model.predict(features)[0]
                
            else:
                # 4. 其他模型(无法获取概率信息)
                pred = model.predict(features)[0]
                probs = np.array([0, 1]) if pred == 1 else np.array([1, 0])
            
            return pred, probs

        # 利用内嵌函数获取预测类别和类别概率
        prediction, probabilities = get_prediction_probability(loaded_model, sample_features)
        
         # 将预测结果映射回类别标签
        class_mapping = {0: "HC", 1: "LC"}
        predicted_class = class_mapping.get(prediction, "未知")
        
        # 显示预测结果和概率
        confidence_text = f"类别概率: HC={probabilities[0]:.4f}, LC={probabilities[1]:.4f}"
        result_text = f"预测结果: {predicted_class}\n{confidence_text}"

        # 更新UI显示
        result_text += f"\n预测样本: {os.path.basename(file_path)}"
        result_text += f"\n模型信息:{loaded_model.__class__.__name__}"
        
        prediction_result_label.config(text=result_text, fg='red' if predicted_class == "LC" else 'green', font=('Helvetica', 12, 'bold'))
        
        return predicted_class, probabilities
        
    except Exception as e:
        error_message = f"预测过程中发生错误：{str(e)}"
        prediction_result_label.config(text=error_message, fg='red', font=('Helvetica', 12, 'bold'))
        print(error_message)
        return None, None



# 函数：选择文件并连锁预测 + 传递预测部分UI
def open_file_dialog(prediction_result_label):
    """
    打开文件选择对话框，用于选择要预测的样本文件。
    
    此函数提供图形化界面让用户选择一个txt格式的样本文件，并自动
    调用predict_unknown_sample函数进行预测，结果将显示在指定标签中。
    
    参数:
        prediction_result_label (tkinter.Label): 用于显示预测结果的标签控件
        
    返回:
        None: 直接通过GUI界面展示预测结果
        
    注意:
        - 初始目录设置为根目录"/"
        - 默认文件过滤为txt文件，但允许选择任何类型文件
        - 若用户取消选择，将不会执行任何操作
    """
    file_path = filedialog.askopenfilename(initialdir="/",title="选择要预测的文件",filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
    if file_path:
        predict_unknown_sample(file_path,prediction_result_label)

# 添加在predict_unknown_sample函数中显示模型信息的部分
def show_model_info(loaded_model):
    """
    显示加载模型的详细信息窗口。
    
    创建一个新窗口，详细展示模型的类型、参数以及模型特定的重要信息，
    如特征重要性、系数等。对于PLSRegression模型，还会显示组件数、
    权重和载荷等特有信息。
    
    参数:
        loaded_model: 已加载的scikit-learn模型实例
        
    返回:
        None: 在新窗口中显示模型信息
        
    功能特点:
        - 根据不同模型类型自动显示相应特性
        - 对于有feature_importances_属性的模型(如随机森林)，显示特征重要性
        - 对于有coef_属性的模型(如线性模型)，显示系数值
        - 对于PLSRegression模型，特别展示其组件数、权重和载荷信息
        
    注意:
        - 新窗口尺寸固定为600x400像素
        - 使用ScrolledText组件允许滚动查看大量信息
    """
    info_window = tkinter.Toplevel()
    info_window.title(f"模型信息: {type(loaded_model).__name__}")
    info_window.geometry("600x400")
    
    # 使用文本框显示模型信息
    info_text = scrolledtext.ScrolledText(info_window, width=70, height=20)
    info_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    # 获取模型信息
    info_text.insert(tkinter.END, f"模型类型: {type(loaded_model).__name__}\n\n")
    
    # 获取模型参数
    info_text.insert(tkinter.END, "模型参数:\n")
    for param_name, param_value in loaded_model.get_params().items():
        info_text.insert(tkinter.END, f"- {param_name}: {param_value}\n")
    
    # 特殊模型信息
    if hasattr(loaded_model, 'feature_importances_'):
        info_text.insert(tkinter.END, "\n特征重要性:\n")
        importances = loaded_model.feature_importances_
        for i, imp in enumerate(importances):
            info_text.insert(tkinter.END, f"- 特征 {i+1}: {imp:.4f}\n")
    
    elif hasattr(loaded_model, 'coef_'):
        info_text.insert(tkinter.END, "\n特征系数:\n")
        coefs = loaded_model.coef_
        if coefs.ndim == 1:
            for i, coef in enumerate(coefs):
                info_text.insert(tkinter.END, f"- 特征 {i+1}: {coef:.4f}\n")
        
        elif isinstance(loaded_model, PLSRegression):
            info_text.insert(tkinter.END, "\nPLS回归特有信息:\n")
            info_text.insert(tkinter.END, f"- 组件数: {loaded_model.n_components}\n")
            
            if hasattr(loaded_model, 'x_weights_'):
                info_text.insert(tkinter.END, "\nX权重 (前5个特征的前3个组件):\n")
                weights = loaded_model.x_weights_
                for i in range(min(5, weights.shape[0])):
                    weight_str = ", ".join([f"{w:.4f}" for w in weights[i, :min(3, weights.shape[1])]])
                    info_text.insert(tkinter.END, f"- 特征 {i+1}: {weight_str}\n")
            
            if hasattr(loaded_model, 'x_loadings_'):
                info_text.insert(tkinter.END, "\nX载荷 (前5个特征的前3个组件):\n")
                loadings = loaded_model.x_loadings_
                for i in range(min(5, loadings.shape[0])):
                    loading_str = ", ".join([f"{l:.4f}" for l in loadings[i, :min(3, loadings.shape[1])]])
                    info_text.insert(tkinter.END, f"- 特征 {i+1}: {loading_str}\n")
        else:
            for class_idx, class_coef in enumerate(coefs):
                info_text.insert(tkinter.END, f"\n类别 {class_idx} 的系数:\n")
                for i, coef in enumerate(class_coef):
                    info_text.insert(tkinter.END, f"- 特征 {i+1}: {coef:.4f}\n")

def create_gui():
    """ 
    创建并配置应用程序的主图形用户界面。
    
    构建完整的应用程序GUI，包括菜单栏、文件选择按钮、进度显示、
    模型选择、训练控制、结果展示等所有界面元素。设置窗口尺寸为
    全屏并处理各组件的布局和初始状态。
    
    参数:
        None
        
    返回:
        None: 启动主GUI循环
        
    全局变量依赖:
        root: tkinter主窗口对象
        class_dict: 包含可用模型类型及其参数配置的字典
        exact_selection: 当前选择的模型类型名称
        
    界面组件:
        - 菜单栏: 提供数据预处理和模型选择功能
        - 文件操作区: 用于选择训练数据和预测样本
        - 训练控制区: 包含开始分析按钮和进度显示
        - 结果展示区: 显示训练精度和预测结果
        - 信息面板: 展示运行日志和状态信息
        
    功能入口点:
        - 数据预处理: select_and_process_files
        - 模型训练: predict_by
        - 样本预测: predict_unknown_sample
        - 模型信息查看: show_model_info
        
    注意:
        - 窗口使用zoomed状态实现全屏显示，保留Windows任务栏
        - 使用网格布局(grid)管理界面组件位置
        - 某些按钮初始状态为禁用，需要先完成前置操作才能启用
    """
    global info_text 
    root.title('诊断分析')

    # === 创建帮助系统 ===
    help_system = HelpSystem(root)

    menu_bar = tkinter.Menu(root)
    # 设置窗口大小为屏幕大小
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.geometry(f"{width}x{height}+0+0")
    
    # 让窗口最大化，这在Windows上能保留任务栏
    root.state('zoomed')

    # 菜单栏数据预处理显示
    command_menu = tkinter.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="数据预处理", menu=command_menu)
    command_menu.add_command(label="选择处理文件", command=select_and_process_files)

    # 菜单栏模型选择显示
    option_menu = tkinter.Menu(menu_bar, tearoff=0)
    var_selection = tkinter.StringVar()
    var_selection.set(exact_selection)
    for item in class_dict.keys():
        option_menu.add_radiobutton(label=item, variable=var_selection,
                                    value=item, command=lambda: on_selcted(var_selection, display_label))
    menu_bar.add_cascade(label="模型选择", menu=option_menu)

    # === 添加帮助菜单 ===
    help_menu = tkinter.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="帮助", menu=help_menu)
    help_menu.add_command(label="使用向导", command=help_system.show_wizard)
    help_menu.add_command(label="关于", command=help_system.show_about)

    # 训练部分控件
    open_button = tkinter.Button(
        root, text="选择归一化excel文件", command=lambda: open_excel_file(normalization_label, start_button, progress_bar))
    open_button.grid(row=1, column=0)
    # === 添加悬停提示 ===
    help_system.add_hover_tip(open_button, "select_excel")

    normalization_label_text = "文件未选择"
    normalization_label = tkinter.Label(root, text=normalization_label_text)
    normalization_label.grid(row=1, column=1)

    start_button = tkinter.Button(root, text='开始分析', command=lambda: predict_by(
        progress_label, progress_bar, balanced_accuracy_train_label, balanced_accuracy_test_label,model_save_status_label))
    start_button.grid(row=2, column=0)
    start_button.config(state='disabled')
     # === 添加悬停提示 ===
    help_system.add_hover_tip(start_button, "start_analysis")

    display_label = tkinter.Label(
        root, text='默认使用'+exact_selection)
    display_label.grid(row=2, column=1)
    # === 添加悬停提示 ===
    help_system.add_hover_tip(display_label, "model_selection")

    progress_label = tkinter.Label(root, text='分析进度: 0%')
    progress_label.grid(row=3, column=0)
    progress_bar = ttk.Progressbar(root, length=200, mode='determinate')
    progress_bar.grid(row=3, column=1, sticky='ew')
    # === 添加悬停提示 ===
    help_system.add_hover_tip(progress_bar, "progress")

    balanced_accuracy_train_label = tkinter.Label(root, text='平均训练集平衡精度: ')
    balanced_accuracy_train_label.grid(row=5, column=0)
    # === 添加悬停提示 ===
    help_system.add_hover_tip(balanced_accuracy_train_label, "results")

    balanced_accuracy_test_label = tkinter.Label(root, text='平均测试集平衡精度: ')
    balanced_accuracy_test_label.grid(row=5, column=1)
    # === 添加悬停提示 ===
    help_system.add_hover_tip(balanced_accuracy_test_label, "results")

    model_save_status_label = tkinter.Label(root, text='模型保存状态: 未保存')
    model_save_status_label.grid(row=5, column=2) 

    # 新增：信息显示区域（放在 row 1）
    info_label = tkinter.Label(root, text="运行信息：")
    info_label.grid(row=1, column=2, sticky='w')
    

    # 使用ScrolledText替代普通Text（带滚动条）
    info_text = scrolledtext.ScrolledText(root, width=100, height=4, wrap=tkinter.WORD)
    info_text.grid(row=2, column=2, columnspan=2, padx=10, pady=5, sticky='nsew')
    # === 添加悬停提示 ===
    help_system.add_hover_tip(info_text, "log_info")

    # 初始化日志
    log_message("系统已启动，等待用户操作...")
    

    # row 6 用来显示预测后的图像

    # 预测结果显示区域
    prediction_result_label = tkinter.Label(root,text='状态：等待选择文件')
    prediction_result_label.grid(row=7, column=1) 
    # 选择文件按钮
    file_button = tkinter.Button(
        root, text="选择要检测的txt文件", 
        command=lambda: open_file_dialog(prediction_result_label))
    file_button.grid(row=7, column=0)
    # === 添加悬停提示 ===
    help_system.add_hover_tip(file_button, "select_predict_file")

    
    model_info_button = tkinter.Button(
    root, text="查看模型详情", 
    command=lambda: show_model_info(load('best_model.joblib')) if os.path.exists('best_model.joblib') else messagebox.showerror("错误", "未找到模型文件"))
    model_info_button.grid(row=7, column=3)
    # === 添加悬停提示 ===
    help_system.add_hover_tip(model_info_button, "model_info")

     # === 如果是首次运行，显示向导 ===
    if help_system.show_wizard_on_startup:
        root.after(500, help_system.show_wizard)  # 延迟500ms显示，确保主窗口已完全加载

    root.config(menu=menu_bar)
    root.mainloop()

# 全局变量初始化

notebook = None # tkinter.ttk.Notebook对象，用于在GUI中显示选项卡式图表展示区
info_text = None # 全局信息显示文本框

# 定义支持的模型类型及其参数配置字典
class_dict = {
    "RandomForestClassifier": {"n_estimators": 500},
    "LinearSVC": {"max_iter": 10000},
    "LinearDiscriminantAnalysis": {"solver": 'eigen', "shrinkage": 'auto'},
    "LogisticRegressionCV": {"Cs": 20, "penalty": 'l1', "cv": StratifiedKFold(5, shuffle=True), "max_iter": 10000, "solver": 'liblinear', "scoring": 'balanced_accuracy', "n_jobs": -1},
    "MLPClassifier": {"hidden_layer_sizes": (100, 200, 100), "activation": 'logistic', "max_iter": 2000},
    "PLSRegression": {"n_components": 10},
}
# 默认选择的模型类型（字典中的第4个）
exact_selection = list(class_dict.keys())[3]    # LogisticRegressionCV

# 创建tkinter主窗口
root = tkinter.Tk()

# 程序入口点
if __name__ == "__main__":
    create_gui()    # 启动GUI界面
