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

            # 更新进度条
            progress_bar['value'] = index
            progress_label.config(text=f"正在处理: {index}/{len(file_paths)}")
            root.update()
        # 保存结果部分的修改
        try:
            # 检查LC_MAX.xlsx是否已存在
            original_file_path = 'LC_MAX.xlsx'
            if os.path.exists(original_file_path):
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
                    messagebox.showinfo(
                        "提示", f"检测到已有文件，已备份为 {backup_file_path}")
                except Exception as e:
                    messagebox.showwarning(
                        "警告", f"无法重命名已有文件: {str(e)}\n将尝试直接保存新文件。")

            # 保存新文件
            all_results.to_excel(original_file_path,
                                 index=True, columns=all_results.columns[1:])
            messagebox.showinfo("处理完成", f"结果已保存为 {original_file_path}")

            # 更新状态栏
            if 'status_message' in globals():
                status_message.config(text="状态：数据预处理完成，请点击'选择归一化excel文件'")

            progress_bar.grid_remove()
            progress_label.grid_remove()

        except PermissionError:
            messagebox.showerror("错误", "无法保存文件，可能是文件已被打开或没有写入权限")

            # 为用户提供选择其他位置的选项
            response = messagebox.askyesno("提示", "是否选择其他位置保存文件？")
            if response:
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx")],
                    initialfile="LC_MAX.xlsx"
                )

                if save_path:
                    all_results.to_excel(
                        save_path, index=True, columns=all_results.columns[1:])
                    messagebox.showinfo("处理完成", f"结果已保存为 {save_path}")

                    # 更新状态栏
                    if 'status_message' in globals():
                        status_message.config(
                            text=f"状态：数据预处理完成，结果已保存至 {save_path}")

                    progress_bar.grid_remove()
                    progress_label.grid_remove()
        except Exception as e:
            messagebox.showerror("错误", f"保存文件时出错: {str(e)}")
            progress_bar.grid_remove()
            progress_label.grid_remove()
        # 更新状态栏
        if 'status_message' in globals():
            status_message.config(text="状态：数据预处理完成，请点击'选择归一化excel文件'")
    else:
        messagebox.showwarning("", "未选择任何文件。")


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
    global row, column, df, status_message
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xls *.xlsx")])
    if file_path:
        try:
            df = pd.read_excel(file_path, header=0)
            df = df.iloc[:, 1:]

            if df.empty:
                normalization_label.config(text="文件未选择")
                if 'status_message' in globals():
                    status_message.config(text="状态：所选文件为空，请选择有效的数据文件")
                return

            # 检查文件是否具有预期的格式
            if df.shape[0] < 2:  # 至少需要类别行和一个特征行
                messagebox.showerror("格式错误", "Excel文件格式不正确，至少需要类别行和特征行")
                if 'status_message' in globals():
                    status_message.config(text="状态：文件格式错误，请检查Excel文件结构")
                return

            normalization_label.config(text="已选择")
            start_button.config(state='normal')
            progress_bar['value'] = 0
            if 'status_message' in globals():
                status_message.config(text="状态：数据文件已加载，请选择模型并点击'开始分析'")

            # 处理数据
            row = df.iloc[1:, :].values.T
            ylabels = df.iloc[0, :].values
            ylabels = pd.Series(ylabels)

            print(f"加载的数据形状: {row.shape}")
            print(f"类别标签统计: {ylabels.value_counts()}")

            # 确保有足够的每类样本
            if len(ylabels.value_counts()) < 2:
                messagebox.showwarning("警告", "数据中只有一种类别，需要至少两种类别才能训练模型")

            # 进行标签编码
            class_mapping = {"HC": 0, "LC": 1}
            column = np.array([class_mapping.get(label, -1)
                               for label in ylabels])

            # 未知类别报错
            if -1 in column:
                unknown_classes = set(ylabels[column == -1])
                print(f"警告: 发现未知类别: {unknown_classes}")
                messagebox.showwarning(
                    "警告", f"发现未知类别: {unknown_classes}\n请检查您的类别映射")

        except Exception as e:
            messagebox.showerror("错误", f"加载Excel文件时出错: {str(e)}")
            if 'status_message' in globals():
                status_message.config(text=f"状态：加载文件出错 - {str(e)}")


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
    display_label.config(text='当前模型: '+exact_selection)


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


def predict_by(progress_label, progress_bar, balanced_accuracy_train_label, balanced_accuracy_test_label, info_text, model_save_status_label):
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
    global row, column, df, fpr_list, tpr_list, thresholds_list, auc_list, best_model, status_message

    # 初始化数据结构
    balanced_accuracy_train = []
    balanced_accuracy_test = []
    trained_models = []
    fpr_list = []
    tpr_list = []
    thresholds_list = []  # 记录训练结果的阈值
    auc_list = []
    Fscores = np.zeros((500, 4))
    thresholds_used = []  # 用于二值化的阈值
    confusion_matrixs = np.zeros((500, 4))
    best_score = -1  # 用于跟踪最佳模型性能

    # 清空日志旧信息
    info_text.delete(1.0, tkinter.END)
    # 局部函数：用于文本框中的日志记录

    def log_message(message):
        info_text.insert(tkinter.END, message + "\n")
        info_text.see(tkinter.END)  # 自动滚动到底部
        root.update()

    log_message("=> 开始模型训练...")
    # 检查数据是否正确加载
    if row is None or column is None:
        log_message("错误: 数据未正确加载")
        messagebox.showerror("数据错误", "未找到有效训练数据，请先选择Excel文件。")
        if 'status_message' in globals():
            status_message.config(text="状态：数据未正确加载，请选择Excel文件")
        return

    # 检查样本数量
    n_samples = row.shape[0] if hasattr(row, 'shape') else len(row)
    log_message(f"加载的样本数量: {n_samples}")

    if n_samples < 5:  # 设定一个最小样本数
        log_message(f"错误: 样本数量不足（当前只有{n_samples}个样本）")
        log_message("训练机器学习模型需要足够的样本数量。")
        log_message("请确保已正确加载数据文件，并且文件包含多个样本。")

        messagebox.showerror("样本数量不足",
                             f"检测到只有{n_samples}个样本，无法进行训练。\n"
                             "请确保您已正确加载包含多个样本的数据文件。")

        if 'status_message' in globals():
            status_message.config(text="状态：样本数量不足，无法训练模型")

        progress_bar['value'] = 0
        return

    # 检查类别分布
    unique_classes = np.unique(column)
    log_message(f"检测到的类别: {unique_classes}")

    if len(unique_classes) < 2:
        log_message(f"错误: 数据中只包含一种类别 ({unique_classes[0]})")
        log_message("分类模型需要至少两种不同的类别才能进行训练。")

        messagebox.showerror("类别不足",
                             "数据中只包含一种类别，无法训练分类模型。\n"
                             "请确保您的数据包含不同类别的样本（例如HC和LC）。")

        if 'status_message' in globals():
            status_message.config(text="状态：类别不足，无法训练分类模型")

        progress_bar['value'] = 0
        return

    if 'status_message' in globals():
        status_message.config(text="状态：模型训练中，请等待...")

    # 主训练循环500次
    for i in tqdm.tqdm(range(500)):
        percentage = (i + 1) / 500 * 100
        progress_label.config(text='分析进度: {0:.2f}%'.format(percentage))
        progress_bar['value'] = percentage
        root.update()

        # 划分20%为训练集
        train_X, test_X, train_y, test_y = train_test_split(
            row, column, test_size=0.2, stratify=column)

        # 模型初始化和训练 => 模型可以改成params里的不同类型
        params = class_dict[exact_selection]
        current_model = globals()[exact_selection](**params)
        current_model.fit(train_X, train_y)

        # 模型预测处理
        if isinstance(current_model, PLSRegression):
            # 如果模型为PLSRegression，则需要对预测值进行ROC二值化处理
            train_pred_raw = current_model.predict(
                train_X).flatten()  # 确保是一维数组
            test_pred_raw = current_model.predict(
                test_X).flatten()    # 确保是一维数组

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

        # 之前代码用的是 current_model.score()，现在我们改用 balanced_accuracy_score() 来保持评估的一致性，特别是在处理 PLS 的情况下
        balanced_accuracy_train.append(
            balanced_accuracy_score(train_y, train_y_pred))
        balanced_accuracy_test.append(
            balanced_accuracy_score(test_y, text_y_pred))

        confusion_matrixs[i] = confusion_matrix(test_y, text_y_pred).flatten()
        Fscore = metrics.classification_report(
            test_y, text_y_pred, labels=[0, 1], output_dict=True)

        Fscores[i][0] = Fscore["weighted avg"]["precision"]
        Fscores[i][1] = Fscore["weighted avg"]["recall"]
        Fscores[i][2] = Fscore["weighted avg"]["f1-score"]

        trained_models.append(current_model)

        # 覆写保存最佳模型
        if balanced_accuracy_test[i] > best_score:
            best_score = balanced_accuracy_test[i]
            best_model = current_model
            log_message(f"发现更高分数：{best_score:.4f} (迭代{i})")

    log_message(f"\n训练完成！最优模型分数：{best_score:.4f}")
    if 'status_message' in globals():
        status_message.config(text="状态：模型训练完成，可以进行样本预测")

    # 循环结束后保存最终的最优模型（只保存一次）
    if best_model is not None:
        dump(best_model, 'best_model.joblib')
        log_message(f"最优模型已保存，测试集分数: {best_score:.4f}")
        model_save_status_label.config(
            text=f'模型保存状态: 已保存 (分数: {best_score:.4f})', fg='green')
    else:
        log_message("警告：未训练出有效模型")
        model_save_status_label.config(text='模型保存状态: 保存失败', fg='red')

    # 保存训练数据和指标
    np.savetxt("Con_matrix_SVM.csv", confusion_matrixs, delimiter=",")
    np.savetxt("Fscore_SVM.csv", Fscores, delimiter=",")
    np.savetxt("2C_auc_SVM.csv", auc_list, delimiter=",")
    np.save("fpr_values.npy", np.array(fpr_list, dtype=object))
    np.save("tpr_values.npy", np.array(tpr_list, dtype=object))
    np.save("thresholds_values.npy", np.array(thresholds_list, dtype=object))
    # 如果使用了PLS回归，则额外保存阈值数据
    if len(trained_models) > 0 and isinstance(trained_models[0], PLSRegression) and len(thresholds_used) > 0:
        np.savetxt("PLS_optimal_thresholds.csv",
                   thresholds_used, delimiter=",")
        mean_threshold = np.mean(thresholds_used)
        print(f"PLS回归平均最优阈值: {mean_threshold:.4f}")

    # 显示平均性能指标
    mean_balanced_accuracy_train = np.mean(balanced_accuracy_train)
    mean_balanced_accuracy_test = np.mean(balanced_accuracy_test)
    balanced_accuracy_train_label.config(
        text=f"平均训练集平衡精度: {mean_balanced_accuracy_train:.4f}")
    balanced_accuracy_test_label.config(
        text=f"平均测试集平衡精度: {mean_balanced_accuracy_test:.4f}")
    print(np.mean(balanced_accuracy_train), np.mean(balanced_accuracy_test))

    # 传参进行可视化
    if len(trained_models) > 0 and isinstance(trained_models[0], PLSRegression) and len(thresholds_used) > 0:
        visualize_performance(balanced_accuracy_train,
                              balanced_accuracy_test, Fscores, confusion_matrixs, fpr_list, tpr_list, auc_list, thresholds_used)
    else:
        visualize_performance(balanced_accuracy_train,
                              balanced_accuracy_test, Fscores, confusion_matrixs, fpr_list=fpr_list, tpr_list=tpr_list, auc_list=auc_list)


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
    global root
    global notebook

    # Visualization of balanced accuracy
    plt.figure(figsize=(6, 4))
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

    # Visualization of F1 scores
    plt.figure(figsize=(6, 4))
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

    # Visualization of Confusion Matrix
    reverse_class_mapping = {0: "HC", 1: "LC"}
    plt.figure(figsize=(4, 4))
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

    # 计算ROC曲线的均值和标准差
    plt.figure()
    mean_fpr = np.linspace(0, 1, 100)
    mean_tpr = np.mean([np.interp(mean_fpr, fpr, tpr)
                       for fpr, tpr in zip(fpr_list, tpr_list)], axis=0)
    plt.plot(mean_fpr, mean_tpr, color='red', lw=3,
             label=f'Mean ROC (AUC={np.mean(auc_list):.2f})')
    plt.plot([0, 1], [0, 1], color='gray', linestyle='--')  # 对角线
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Mean ROC Curve')
    plt.savefig('Mean ROC Curve.png')
    plt.close()

    # 如果有阈值数据，则添加阈值分布的可视化
    if thresholds_used is not None and len(thresholds_used) > 0:
        mean_threshold = np.mean(thresholds_used)
        std_threshold = np.std(thresholds_used)

        plt.figure(figsize=(6, 4), dpi=100)
        hist_data = plt.hist(thresholds_used, bins=20, color='skyblue',
                             edgecolor='black', alpha=0.7)

        if isinstance(hist_data, tuple) and len(hist_data) > 0:
            y_max = max(hist_data[0]) * 1.1  # 如果hist_data是元组且有值
        else:
            y_max = plt.ylim()[1] * 1.1
        # 添加平均阈值和默认阈值的竖线
        plt.axvline(x=mean_threshold, color='r', linestyle='--',
                    label=f'Mean Threshold: {mean_threshold:.4f}')
        plt.axvline(x=0.5, color='g', linestyle='--',
                    label='Default Threshold: 0.5')

        plt.xlabel('Threshold Value', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
    # 修改图例位置和样式
        plt.legend(loc='upper right', fontsize=10)
        plt.title(f'PLS-DA Optimal Threshold Distribution (Mean={mean_threshold:.4f}, Std={std_threshold:.4f})',
                  fontsize=12)
    # 调整Y轴范围确保显示完整
        plt.ylim(0, y_max)
    # 确保图形边缘有足够的空间显示标签
        plt.tight_layout()
        plt.savefig('PLS_optimal_thresholds.png', dpi=100, bbox_inches='tight')
        plt.close()
    root.update()

    # 创建选项卡控件
    if notebook is not None:
        try:
            notebook.destroy()  # 尝试销毁旧的notebook
        except:
            pass
    notebook = ttk.Notebook(root)
    notebook.grid(row=4, column=0, columnspan=4, sticky='nsew')

    # 第一个选项卡 - 准确率
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="准确率")
    image_accuracy = Image.open('Training and Test Balanced Accuracy.png')
    photo_accuracy = ImageTk.PhotoImage(image_accuracy)
    label1 = tkinter.Label(tab1, image=photo_accuracy)
    label1.image = photo_accuracy  # 保持引用
    label1.pack(fill='both', expand=True)

    # 第二个选项卡 - 精确率/召回率/F1
    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text="精确率/召回率/F1")
    image_precision_recall_f1score = Image.open(
        'Weighted Average Precision, Recall, and F1-score.png')
    photo_precision_recall_f1score = ImageTk.PhotoImage(
        image_precision_recall_f1score)
    label2 = tkinter.Label(tab2, image=photo_precision_recall_f1score)
    label2.image = photo_precision_recall_f1score  # 保持引用
    label2.pack(fill='both', expand=True)

    # 第三个选项卡 - 混淆矩阵
    tab_CM = ttk.Frame(notebook)
    notebook.add(tab_CM, text="混淆矩阵")
    image_Confusion_Matrix = Image.open('Mean Confusion Matrix.png')
    photo_Confusion_Matrix = ImageTk.PhotoImage(image_Confusion_Matrix)
    label3 = tkinter.Label(tab_CM, image=photo_Confusion_Matrix)
    label3.image = photo_Confusion_Matrix  # 保持引用
    label3.pack(fill='both', expand=True)

    # 如果有阈值数据, 添加第四个选项卡
    if thresholds_used is not None and len(thresholds_used) > 0:
        tab4 = ttk.Frame(notebook)
        notebook.add(tab4, text="阈值分布")
        image_threshold = Image.open('PLS_optimal_thresholds.png')
        photo_threshold = ImageTk.PhotoImage(image_threshold)
        label4 = tkinter.Label(tab4, image=photo_threshold)
        label4.image = photo_threshold  # 保持引用
        label4.pack(fill='both', expand=True)

    # 第五个选项卡 - ROC曲线
    tab_roc = ttk.Frame(notebook)
    notebook.add(tab_roc, text="ROC曲线")
    image_roc = Image.open('Mean ROC Curve.png')
    photo_roc = ImageTk.PhotoImage(image_roc)
    label_roc = tkinter.Label(tab_roc, image=photo_roc)
    label_roc.image = photo_roc
    label_roc.pack(fill='both', expand=True)
    root.update()


def show_welcome_wizard():
    """显示欢迎向导，指导用户使用程序的基本步骤"""
    wizard = tkinter.Toplevel(root)
    wizard.title("使用向导")
    wizard.geometry("600x450")
    wizard.resizable(False, False)

    # 创建笔记本控件来显示多个步骤
    wizard_tabs = ttk.Notebook(wizard)
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
    button_frame = ttk.Frame(wizard)
    button_frame.pack(fill='x', padx=10, pady=10)

    # 创建"不再显示"复选框
    show_again_var = tkinter.BooleanVar(value=True)
    ttk.Checkbutton(button_frame, text="启动时显示此向导",
                    variable=show_again_var).pack(side='left')

    # 创建关闭按钮
    ttk.Button(button_frame, text="开始使用",
               command=lambda: close_wizard(wizard, show_again_var)).pack(side='right')


def close_wizard(wizard, show_again_var):
    """关闭向导并保存用户选择"""
    # 这里可以保存用户的选择到配置文件
    wizard.destroy()


def create_tooltip(widget, text):
    """为控件创建悬停提示"""
    def enter(event):
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25

        # 创建提示窗口
        tooltip = tkinter.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(tooltip, text=text, background="#FFFFDD",
                          relief="solid", borderwidth=1, padding=(5, 2))
        label.pack()

        widget._tooltip = tooltip

    def leave(event):
        if hasattr(widget, "_tooltip"):
            widget._tooltip.destroy()

    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)


def show_about():
    """显示关于信息"""
    about_window = tkinter.Toplevel(root)
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


def create_workflow_diagram(parent):
    """创建简单的工作流程图"""
    canvas = tkinter.Canvas(parent, width=700, height=80, bg='white')
    canvas.pack(padx=10, pady=5)

    # 绘制三个步骤框
    canvas.create_rectangle(50, 20, 200, 60, fill='lightblue', outline='blue')
    canvas.create_rectangle(
        250, 20, 400, 60, fill='lightgreen', outline='green')
    canvas.create_rectangle(
        450, 20, 600, 60, fill='lightyellow', outline='orange')

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
    """
    global status_message, exact_selection

    root.title('诊断分析')
    menu_bar = tkinter.Menu(root)
    # 设置窗口大小为屏幕大小
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.geometry(f"{width}x{height}+0+0")

    # 让窗口最大化，这在Windows上能保留任务栏
    root.state('zoomed')

    # 添加标题和流程图
    title_label = tkinter.Label(
        root, text="质谱数据诊断分析工具", font=('Helvetica', 16, 'bold'))
    title_label.grid(row=0, column=0, columnspan=4, pady=10)

    # 添加流程图框架
    flow_frame = ttk.LabelFrame(root, text="操作流程")
    flow_frame.grid(row=1, column=0, columnspan=4,
                    padx=10, pady=5, sticky='ew')
    create_workflow_diagram(flow_frame)

    # 使用Frame对界面进行分区
    preprocessing_frame = ttk.LabelFrame(root, text="第一步：数据预处理")
    preprocessing_frame.grid(
        row=2, column=0, columnspan=4, padx=10, pady=5, sticky='ew')

    # 数据预处理按钮
    preprocess_button = tkinter.Button(preprocessing_frame, text="选择并处理原始文件",
                                       command=select_and_process_files)
    preprocess_button.pack(padx=10, pady=10)
    create_tooltip(preprocess_button, "选择原始txt格式质谱数据文件进行预处理")

    # 第二步：模型训练框架
    training_frame = ttk.LabelFrame(root, text="第二步：模型训练")
    training_frame.grid(row=3, column=0, columnspan=4,
                        padx=10, pady=5, sticky='ew')

    # 训练控件布局
    train_controls = ttk.Frame(training_frame)
    train_controls.pack(padx=10, pady=10, fill='x')

    open_button = tkinter.Button(
        train_controls, text="选择归一化excel文件",
        command=lambda: open_excel_file(normalization_label, start_button, progress_bar))
    open_button.grid(row=0, column=0, padx=5, pady=5)
    create_tooltip(open_button, "选择预处理后生成的LC_MAX.xlsx文件")

    normalization_label_text = "文件未选择"
    normalization_label = tkinter.Label(
        train_controls, text=normalization_label_text)
    normalization_label.grid(row=0, column=1, padx=5, pady=5)

    # 模型选择下拉列表（替代菜单方式）
    model_frame = ttk.Frame(train_controls)
    model_frame.grid(row=0, column=2, padx=5, pady=5)
    ttk.Label(model_frame, text="选择模型:").pack(side='left')
    var_selection = tkinter.StringVar(value=exact_selection)
    model_dropdown = ttk.Combobox(model_frame, textvariable=var_selection,
                                  values=list(class_dict.keys()), state="readonly", width=20)
    model_dropdown.pack(side='left', padx=5)
    model_dropdown.bind("<<ComboboxSelected>>",
                        lambda e: on_selcted(var_selection, display_label))
    create_tooltip(model_dropdown, "选择用于训练的机器学习模型类型")

    display_label = tkinter.Label(
        train_controls, text='当前模型: '+exact_selection)
    display_label.grid(row=0, column=3, padx=5, pady=5)

    start_button = tkinter.Button(train_controls, text='开始分析', command=lambda: predict_by(
        progress_label, progress_bar, balanced_accuracy_train_label, balanced_accuracy_test_label,
        info_text, model_save_status_label))
    start_button.grid(row=1, column=0, padx=5, pady=5)
    start_button.config(state='disabled')
    create_tooltip(start_button, "开始模型训练过程，将执行500次交叉验证")

    # 进度显示
    progress_frame = ttk.Frame(train_controls)
    progress_frame.grid(row=1, column=1, columnspan=3,
                        padx=5, pady=5, sticky='ew')
    progress_label = tkinter.Label(progress_frame, text='分析进度: 0%')
    progress_label.pack(side='top', anchor='w')
    progress_bar = ttk.Progressbar(
        progress_frame, length=300, mode='determinate')
    progress_bar.pack(side='top', fill='x', pady=2)

    # 训练结果显示
    results_frame = ttk.Frame(train_controls)
    results_frame.grid(row=2, column=0, columnspan=4,
                       padx=5, pady=5, sticky='ew')
    balanced_accuracy_train_label = tkinter.Label(
        results_frame, text='平均训练集平衡精度: ')
    balanced_accuracy_train_label.pack(side='left', padx=10)
    balanced_accuracy_test_label = tkinter.Label(
        results_frame, text='平均测试集平衡精度: ')
    balanced_accuracy_test_label.pack(side='left', padx=10)
    model_save_status_label = tkinter.Label(results_frame, text='模型保存状态: 未保存')
    model_save_status_label.pack(side='left', padx=10)

    # 信息显示区域
    info_frame = ttk.LabelFrame(training_frame, text="运行信息")
    info_frame.pack(padx=10, pady=5, fill='x')
    info_text = scrolledtext.ScrolledText(
        info_frame, width=100, height=4, wrap=tkinter.WORD)
    info_text.pack(padx=5, pady=5, fill='both')

    # 图表显示区域（预留位置）
    notebook = ttk.Notebook(root)
    notebook.grid(row=4, column=0, columnspan=4,
                  padx=10, pady=5, sticky='nsew')

    # 第三步：预测框架
    prediction_frame = ttk.LabelFrame(root, text="第三步：样本预测")
    prediction_frame.grid(row=5, column=0, columnspan=4,
                          padx=10, pady=5, sticky='ew')

    predict_controls = ttk.Frame(prediction_frame)
    predict_controls.pack(padx=10, pady=10, fill='x')

    file_button = tkinter.Button(
        predict_controls, text="选择要检测的txt文件",
        command=lambda: open_file_dialog(prediction_result_label))
    file_button.grid(row=0, column=0, padx=5, pady=5)
    create_tooltip(file_button, "选择需要预测的未知样本文件")

    prediction_result_label = tkinter.Label(predict_controls, text='状态：等待选择文件',
                                            font=('Helvetica', 10))
    prediction_result_label.grid(
        row=0, column=1, rowspan=2, padx=5, pady=5, sticky='w')

    model_info_button = tkinter.Button(
        predict_controls, text="查看模型详情",
        command=lambda: show_model_info(load('best_model.joblib')) if os.path.exists('best_model.joblib')
        else messagebox.showerror("错误", "未找到模型文件"))
    model_info_button.grid(row=0, column=2, padx=5, pady=5)
    create_tooltip(model_info_button, "查看当前加载模型的详细参数和特征信息")

    # 状态栏
    status_frame = ttk.Frame(root, relief='sunken', border=1)
    status_frame.grid(row=6, column=0, columnspan=4,
                      sticky='ew', padx=5, pady=5)

    status_message = ttk.Label(status_frame, text="状态：请先从'数据预处理'开始，选择并处理原始文件")
    status_message.pack(side='left', padx=5)

    # 菜单栏设置
    # 文件菜单
    file_menu = tkinter.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="文件", menu=file_menu)
    file_menu.add_command(label="数据预处理", command=select_and_process_files)
    file_menu.add_command(label="打开Excel数据",
                          command=lambda: open_excel_file(normalization_label, start_button, progress_bar))
    file_menu.add_separator()
    file_menu.add_command(label="退出", command=root.quit)

    # 模型菜单
    model_menu = tkinter.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="模型", menu=model_menu)

    # 模型子菜单
    for item in class_dict.keys():
        model_menu.add_radiobutton(label=item, variable=var_selection,
                                   value=item, command=lambda: on_selcted(var_selection, display_label))

    model_menu.add_separator()
    model_menu.add_command(label="训练模型",
                           command=lambda: predict_by(progress_label, progress_bar,
                                                      balanced_accuracy_train_label,
                                                      balanced_accuracy_test_label,
                                                      info_text, model_save_status_label))

    # 帮助菜单
    help_menu = tkinter.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="帮助", menu=help_menu)
    help_menu.add_command(label="使用指南", command=show_welcome_wizard)
    help_menu.add_command(label="关于", command=show_about)

    root.config(menu=menu_bar)

    # 配置行列权重，使组件可以随窗口大小调整
    root.grid_rowconfigure(4, weight=1)  # 让notebook扩展
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_columnconfigure(2, weight=1)
    root.grid_columnconfigure(3, weight=1)

    # 程序启动时显示向导
    root.after(500, show_welcome_wizard)  # 延迟500ms显示，确保主窗口已加载
    root.mainloop()

# 全局变量初始化


notebook = None  # tkinter.ttk.Notebook对象，用于在GUI中显示选项卡式图表展示区

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
