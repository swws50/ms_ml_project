import pandas as pd
import numpy as np
import tkinter
from tkinter import messagebox, filedialog
from tkinter import ttk
from sklearn import metrics  # 矩阵
from matplotlib import pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix, recall_score, classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedKFold
import os
from sklearn import svm, datasets
from sklearn.model_selection import train_test_split, StratifiedKFold
import tqdm
from sklearn.metrics import roc_curve, auc
from sklearn import metrics
import seaborn as sns
from PIL import Image, ImageTk

from sklearn.linear_model import LogisticRegressionCV
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.cross_decomposition import PLSRegression
from sklearn.metrics import balanced_accuracy_score

# %matplotlib widget


# 函数：处理原始数据
def process_file(file_name, X):
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

        # 保存结果
        all_results.to_excel('LC_MAX.xlsx', index=True,
                             columns=all_results.columns[1:])
        messagebox.showinfo("处理完成", "结果已保存为 LC_MAX.xlsx")
        progress_bar.grid_remove()
        progress_label.grid_remove()
    else:
        messagebox.showwarning("", "未选择任何文件。")

# 函数：选择归一化好的文件


def open_excel_file(normalization_label, start_button, progress_bar):
    global row, column, df
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xls *.xlsx")])
    if file_path:
        df = pd.read_excel(file_path, header=0)
        df = df.iloc[:, 1:]
        if df.empty:
            normalization_label.config(text="文件未选择")
        else:
            normalization_label.config(text="已选择")
            start_button.config(state='normal')
            progress_bar['value'] = 0
        row = df.iloc[1:, :].values.T
        ylabels = df.iloc[0, :].values
        ylabels = pd.Series(ylabels)
        print(ylabels.value_counts())

        encoder = LabelEncoder() 
        column = encoder.fit_transform(ylabels)
        train_X, test_X, train_y, test_y, train_labels, test_labels = train_test_split(
            row, column, df.columns, test_size=0.2, stratify=column)  # 取20%为训练集


def on_selcted(var_selection, display_label):
    global exact_selection
    exact_selection = var_selection.get()
    display_label.config(text='您选择了: '+exact_selection)

def find_optimal_threshold(y_true, y_pred_proba):#使用ROC曲线找到最优分类阈值

    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    # 找到最优点（约登指数最大的点）
    optimal_idx = np.argmax(tpr - fpr)
    return thresholds[optimal_idx]

def predict_by(progress_label, progress_bar, balanced_accuracy_train_label, balanced_accuracy_test_label):
    global row, column, df, thresholds_used
    balanced_accuracy_train = []
    balanced_accuracy_test = []
    lrs = []
    Fscores = np.zeros((500, 4))
    thresholds_used = []

    confusion_matrixs = np.zeros((500, 4))
    auc_lists = np.zeros((500, 1))
    auc_list = []
    for i in tqdm.tqdm(range(500)):
        percentage = (i + 1) / 500 * 100
        progress_label.config(text='分析进度: {0:.2f}%'.format(percentage))
        progress_bar['value'] = percentage
        root.update()

        train_X, test_X, train_y, test_y, train_labels, test_labels = train_test_split(
            row, column, df.columns, test_size=0.2, stratify=column)
        params = class_dict[exact_selection]
        lrcv = globals()[exact_selection](**params)
        # lrcv = eval(exact_selection)  # 可以改成上面注释里的不同方法

        lrcv.fit(train_X, train_y)

        # 如果模型为PLSRegression，则需要对预测值进行ROC二值化处理
        if isinstance(lrcv, PLSRegression):
            train_pred_raw = lrcv.predict(train_X).flatten()  # 确保是一维数组
            test_pred_raw = lrcv.predict(test_X).flatten()    # 确保是一维数组
    
            # 使用训练集寻找最优阈值
            optimal_threshold = find_optimal_threshold(train_y, train_pred_raw)
            thresholds_used.append(optimal_threshold)
            # 使用找到的阈值进行预测
            train_pred = (train_pred_raw > optimal_threshold).astype(int)
            y_pred = (test_pred_raw > optimal_threshold).astype(int)
    
            # 计算AUC值
            try:
                fpr, tpr, _ = roc_curve(test_y, test_pred_raw)
                auc_lists[i] = auc(fpr, tpr)
            except Exception as e:
                print(f"计算AUC时出错: {e}")
                auc_lists[i] = np.nan
        else:
            train_pred = lrcv.predict(train_X)
            y_pred = lrcv.predict(test_X)

        # 之前代码直接用的是 lrcv.score()，现在我们改用 balanced_accuracy_score() 来保持评估的一致性，特别是在处理 PLS 的情况下
        balanced_accuracy_train.append(
            balanced_accuracy_score(train_y, train_pred))
        balanced_accuracy_test.append(balanced_accuracy_score(test_y, y_pred))

        confusion_matrixs[i] = confusion_matrix(test_y, y_pred).flatten()
        Fscore = metrics.classification_report(
            test_y, y_pred, labels=[0, 1], output_dict=True)

        Fscores[i][0] = Fscore["weighted avg"]["precision"]
        Fscores[i][1] = Fscore["weighted avg"]["recall"]
        Fscores[i][2] = Fscore["weighted avg"]["f1-score"]

        lrs.append(lrcv)
    '''
    from sklearn.metrics import RocCurveDisplay
    disp = RocCurveDisplay.from_estimator(lrcv,test_X, test_y)
    auc_lists[i]=metrics.auc(disp.fpr,disp.tpr)'''

    np.savetxt("Con_matrix_SVM.csv", confusion_matrixs, delimiter=",")
    np.savetxt("Fscore_SVM.csv", Fscores, delimiter=",")
    np.savetxt("2C_auc_SVM.csv", auc_lists, delimiter=",")
    
    # 如果使用了PLS回归，则保存阈值数据
    if len(lrs) > 0 and isinstance(lrs[0], PLSRegression) and len(thresholds_used) > 0:
        np.savetxt("PLS_optimal_thresholds.csv", thresholds_used, delimiter=",")
        mean_threshold = np.mean(thresholds_used)
        print(f"PLS回归平均最优阈值: {mean_threshold:.4f}")

    mean_balanced_accuracy_train = np.mean(balanced_accuracy_train)
    mean_balanced_accuracy_test = np.mean(balanced_accuracy_test)

    balanced_accuracy_train_label.config(
        text=f"平均训练集平衡精度: {mean_balanced_accuracy_train:.4f}")
    balanced_accuracy_test_label.config(
        text=f"平均测试集平衡精度: {mean_balanced_accuracy_test:.4f}")
    print(np.mean(balanced_accuracy_train), np.mean(balanced_accuracy_test))

    # 如果是PLS回归，则传递阈值数据进行可视化
    if len(lrs) > 0 and isinstance(lrs[0], PLSRegression) and len(thresholds_used) > 0:
        visualize_performance(balanced_accuracy_train,
                          balanced_accuracy_test, Fscores, confusion_matrixs, thresholds_used)
    else:
        visualize_performance(balanced_accuracy_train,
                          balanced_accuracy_test, Fscores, confusion_matrixs)
# print(np.mean(metrics.auc(disp.fpr,disp.tpr)))


def visualize_performance(balanced_accuracy_train, balanced_accuracy_test, Fscores, confusion_matrixs, thresholds_used=None):
    global photo_accuracy, photo_precision_recall_f1score, photo_Confusion_Matrix, photo_threshold
    global notebook

    # Visualization of balanced accuracy
    plt.figure(figsize=(6, 4))
    plt.scatter(range(len(balanced_accuracy_train)), balanced_accuracy_train,
                label='Training Balanced Accuracy', color='b')
    plt.scatter(range(len(balanced_accuracy_test)),
                balanced_accuracy_test, label='Test Balanced Accuracy', color='r')
    plt.xlabel('Iteration')
    plt.ylabel('Balanced Accuracy')
    plt.legend()
    plt.title('Training and Test Balanced Accuracy over Iterations')
    plt.savefig('Training and Test Balanced Accuracy.png')
    plt.close()

    # Visualization of F1 scores
    plt.figure(figsize=(6, 4))
    plt.scatter(range(len(Fscores)),
                Fscores[:, 0], label='Weighted Avg Precision')
    plt.scatter(range(len(Fscores)),
                Fscores[:, 1], label='Weighted Avg Recall')
    plt.scatter(range(len(Fscores)),
                Fscores[:, 2], label='Weighted Avg F1-score')
    plt.xlabel('Iteration')
    plt.ylabel('Score')
    plt.legend()
    plt.title('Weighted Average Precision, Recall, and F1-score over Iterations')
    plt.savefig('Weighted Average Precision, Recall, and F1-score.png')
    plt.close()

    # Visualization of Confusion Matrix
    plt.figure(figsize=(4, 4))
    mean_conf_matrix = confusion_matrixs.mean(axis=0).reshape((2, 2))
    sns.heatmap(mean_conf_matrix, annot=True,
                fmt='g', cmap='Blues', cbar=False)
    plt.title('Mean Confusion Matrix')
    plt.savefig('Mean Confusion Matrix.png')
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
    notebook.grid(row=6, column=0, columnspan=4, sticky='nsew')
        
     # 第一个选项卡 - 准确率
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="准确率")
    image_accuracy = Image.open('Training and Test Balanced Accuracy.png')
    photo_accuracy = ImageTk.PhotoImage(image_accuracy)
    label1 = tkinter.Label(tab1, image=photo_accuracy)
    label1.pack(fill='both', expand=True)
        
    # 第二个选项卡 - 精确率/召回率/F1
    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text="精确率/召回率/F1")
    image_precision_recall_f1score = Image.open('Weighted Average Precision, Recall, and F1-score.png')
    photo_precision_recall_f1score = ImageTk.PhotoImage(image_precision_recall_f1score)
    label2 = tkinter.Label(tab2, image=photo_precision_recall_f1score)
    label2.pack(fill='both', expand=True)
        
    # 第三个选项卡 - 混淆矩阵
    tab3 = ttk.Frame(notebook)
    notebook.add(tab3, text="混淆矩阵")
    image_Confusion_Matrix = Image.open('Mean Confusion Matrix.png')
    photo_Confusion_Matrix = ImageTk.PhotoImage(image_Confusion_Matrix)
    label3 = tkinter.Label(tab3, image=photo_Confusion_Matrix)
    label3.pack(fill='both', expand=True)
        
    # 如果有阈值数据, 添加第四个选项卡
    if thresholds_used is not None and len(thresholds_used) > 0:
        tab4 = ttk.Frame(notebook)
        notebook.add(tab4, text="阈值分布")
        image_threshold = Image.open('PLS_optimal_thresholds.png')
        photo_threshold = ImageTk.PhotoImage(image_threshold)
        label4 = tkinter.Label(tab4, image=photo_threshold)
        label4.pack(fill='both', expand=True)    
    root.update()


def open_file_dialog(file_name_label):
    file_path = filedialog.askopenfilename(initialdir="/", title="Select File",
                                           filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
    if file_path != '':
        file_name_label.config(text='已选择'+file_path)
    pass
# 没写完


def create_gui():
    root.title('诊断分析')
    menu_bar = tkinter.Menu(root)
     # 设置窗口大小为屏幕大小
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.geometry(f"{width}x{height}+0+0")
    
    # 让窗口最大化，这在Windows上能保留任务栏
    root.state('zoomed')

    command_menu = tkinter.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="数据预处理", menu=command_menu)
    command_menu.add_command(label="选择处理文件", command=select_and_process_files)

    option_menu = tkinter.Menu(menu_bar, tearoff=0)
    var_selection = tkinter.StringVar()
    var_selection.set(exact_selection)

    for item in class_dict.keys():
        option_menu.add_radiobutton(label=item, variable=var_selection,
                                    value=item, command=lambda: on_selcted(var_selection, display_label))
    menu_bar.add_cascade(label="模型选择", menu=option_menu)

    open_button = tkinter.Button(
        root, text="选择归一化excel文件", command=lambda: open_excel_file(normalization_label, start_button, progress_bar))
    open_button.grid(row=1, column=0)

    normalization_label_text = "文件未选择"
    normalization_label = tkinter.Label(root, text=normalization_label_text)
    normalization_label.grid(row=1, column=1)

    start_button = tkinter.Button(root, text='开始分析', command=lambda: predict_by(
        progress_label, progress_bar, balanced_accuracy_train_label, balanced_accuracy_test_label))
    start_button.grid(row=2, column=0)
    start_button.config(state='disabled')

    display_label = tkinter.Label(
        root, text='默认使用'+exact_selection)
    display_label.grid(row=2, column=1)

    progress_label = tkinter.Label(root, text='分析进度: 0%')
    progress_label.grid(row=4, column=0)
    progress_bar = ttk.Progressbar(root, length=200, mode='determinate')
    progress_bar.grid(row=4, column=1, sticky='ew')

    balanced_accuracy_train_label = tkinter.Label(root, text='平均训练集平衡精度: ')
    balanced_accuracy_train_label.grid(row=5, column=0)

    balanced_accuracy_test_label = tkinter.Label(root, text='平均测试集平衡精度: ')
    balanced_accuracy_test_label.grid(row=5, column=1)

    # row 6 用来显示分析后的图标
    file_button = tkinter.Button(
        root, text="选择要检测的txt文件", command=lambda: open_file_dialog(file_name_label))
    file_button.grid(row=7, column=0)

    file_name_label = tkinter.Label(root, text='您尚未进行检测')
    file_name_label.grid(row=7, column=1)

    root.config(menu=menu_bar)
    root.mainloop()


photo_accuracy, photo_precision_recall_f1score, photo_Confusion_Matrix,photo_threshold = None, None, None, None
notebook = None
# selections = ["RandomForestClassifier(500)",
#               "svm.LinearSVC(max_iter=10000)",
#               "LinearDiscriminantAnalysis(solver='eigen', shrinkage='auto')",
#               "LogisticRegressionCV(Cs=20, penalty='l1', cv=StratifiedKFold(5, shuffle=True), max_iter=10000, solver='liblinear', scoring='balanced_accuracy', n_jobs=-1)",
#               "MLPClassifier((100, 200, 100), activation='logistic',max_iter=2000)"
#               ]
# exact_selection = selections[3]

class_dict = {
    "RandomForestClassifier": {"n_estimators": 500},
    "LinearSVC": {"max_iter": 10000},
    "LinearDiscriminantAnalysis": {"solver": 'eigen', "shrinkage": 'auto'},
    "LogisticRegressionCV": {"Cs": 20, "penalty": 'l1', "cv": StratifiedKFold(5, shuffle=True), "max_iter": 10000, "solver": 'liblinear', "scoring": 'balanced_accuracy', "n_jobs": -1},
    "MLPClassifier": {"hidden_layer_sizes": (100, 200, 100), "activation": 'logistic', "max_iter": 2000},
    "PLSRegression": {"n_components": 10},
}
exact_selection = list(class_dict.keys())[3]
root = tkinter.Tk()

if __name__ == "__main__":
    create_gui()
