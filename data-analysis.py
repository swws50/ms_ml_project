import pandas as pd
import numpy as np
import tkinter
from tkinter import messagebox, filedialog
from tkinter import ttk
from sklearn import metrics  # 矩阵
from matplotlib import pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import confusion_matrix, recall_score, classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedKFold
import os
from sklearn.linear_model import LogisticRegressionCV
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.neural_network import MLPClassifier
from sklearn import svm, datasets
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
import tqdm
from sklearn.metrics import roc_curve, auc
from sklearn import metrics
import seaborn as sns
from PIL import Image, ImageTk
import io

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
        progress_label.grid(column=0, row=8, columnspan=2, sticky='ew')
        progress_bar.grid(column=0, row=9, columnspan=2, sticky='ew')

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
        all_results.to_excel('LC_MAX.xlsx', index=False,
                             columns=all_results.columns[1:])
        messagebox.showinfo("处理完成", "结果已保存为 LC_MAX.xlsx")
        progress_bar.grid_remove()
        progress_label.grid_remove()
    else:
        messagebox.showwarning("", "未选择任何文件。")

# 函数：选择归一化好的文件


def open_excel_file(normalization_label, start_button):
    global row, column, df
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xls *.xlsx")])
    if file_path:
        df = pd.read_excel(file_path, header=0)
        if df.empty:
            normalization_label.config(text="文件未选择")
        else:
            normalization_label.config(text="已选择")
            start_button.config(state='normal')
            progress_bar['value'] = 0
            progress_bar.grid(column=1, row=4, sticky='ew')
        row = df.iloc[1:, :].values.T
        ylabels = df.iloc[0, :].values
        ylabels = pd.Series(ylabels)
        print(ylabels.value_counts())
        encoder = LabelEncoder()
        column = encoder.fit_transform(ylabels)



def on_selcted(var_selection, display_label):
    global exact_selection
    exact_selection = var_selection.get()
    display_label.config(text='您选择了'+exact_selection.split('(')[0])


def predict_by(progress_label, balanced_accuracy_train_label, balanced_accuracy_test_label):
    global row, column, df
    balanced_accuracy_train = []
    balanced_accuracy_test = []
    lrs = []
    Fscores = np.zeros((500, 4))

    confusion_matrixs = np.zeros((500, 4))
    auc_lists = np.zeros((500, 1))
    auc_list = []
    for i in tqdm.tqdm(range(500)):
        percentage = (i + 1) / 500 * 100
        progress_label.config(text='分析进度: {0:.2f}%'.format(percentage))
        progress_bar['value'] = percentage
        root.update()

        train_X, test_X, train_y, test_y, train_labels, test_labels = train_test_split(
            row, column, df.columns, test_size=0.2, stratify=column)# 取20%为训练集
        lrcv = eval(exact_selection)  # 可以改成上面注释里的不同方法

        lrcv.fit(train_X, train_y)
        balanced_accuracy_train.append(lrcv.score(train_X, train_y))
        balanced_accuracy_test.append(lrcv.score(test_X, test_y))

        y_pred = lrcv.predict(test_X)
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
    mean_balanced_accuracy_train = np.mean(balanced_accuracy_train)
    mean_balanced_accuracy_test = np.mean(balanced_accuracy_test)

    balanced_accuracy_train_label.config(
        text=f"平均训练集平衡精度: {mean_balanced_accuracy_train:.4f}")
    balanced_accuracy_test_label.config(
        text=f"平均测试集平衡精度: {mean_balanced_accuracy_test:.4f}")
    print(np.mean(balanced_accuracy_train), np.mean(balanced_accuracy_test))
    visualize_performance(balanced_accuracy_train,
                          balanced_accuracy_test, Fscores, confusion_matrixs)
# print(np.mean(metrics.auc(disp.fpr,disp.tpr)))


def visualize_performance(balanced_accuracy_train, balanced_accuracy_test, Fscores, confusion_matrixs):
    global photo_accuracy, photo_precision_recall_f1score, photo_Confusion_Matrix
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

    root.update()

    image_accuracy = Image.open('Training and Test Balanced Accuracy.png')
    photo_accuracy = ImageTk.PhotoImage(image_accuracy)
    accuracy_label = tkinter.Label(root, image=photo_accuracy)
    accuracy_label.grid(column=0, row=6)

    image_precision_recall_f1score = Image.open(
        'Weighted Average Precision, Recall, and F1-score.png')
    photo_precision_recall_f1score = ImageTk.PhotoImage(
        image_precision_recall_f1score)
    precision_recall_f1score_label = tkinter.Label(
        root, image=photo_precision_recall_f1score)
    precision_recall_f1score_label.grid(column=1, row=6)

    image_Confusion_Matrix = Image.open('Mean Confusion Matrix.png')
    photo_Confusion_Matrix = ImageTk.PhotoImage(image_Confusion_Matrix)
    Confusion_Matrix_label = tkinter.Label(root, image=photo_Confusion_Matrix)
    Confusion_Matrix_label.grid(column=2, row=6)

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
    command_menu = tkinter.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="数据预处理", menu=command_menu)
    command_menu.add_command(label="选择处理文件", command=select_and_process_files)

    option_menu = tkinter.Menu(menu_bar, tearoff=0)
    selections = ["RandomForestClassifier(500)",
                  "LogisticRegressionCV(Cs=20, penalty='l1', cv=StratifiedKFold(5, shuffle=True), max_iter=10000, solver='liblinear', scoring='balanced_accuracy', multi_class='ovr', n_jobs=-1)",
                  "LinearDiscriminantAnalysis(solver='eigen', shrinkage='auto')",
                  "svm.LinearSVC(max_iter=10000)",
                  "MLPClassifier((100, 200, 100), activation='logistic',max_iter=2000)"
                  ]
    var_selection = tkinter.StringVar()
    var_selection.set(selections[1])

    for item in selections:
        option_menu.add_radiobutton(label=item.split(
            '(')[0], variable=var_selection, value=item, command=lambda: on_selcted(var_selection, display_label))
    menu_bar.add_cascade(label="模型选择", menu=option_menu)

    open_button = tkinter.Button(
        root, text="选择归一化excel文件", command=lambda: open_excel_file(normalization_label, start_button))
    open_button.grid(column=0, row=1)

    normalization_label_text = "文件未选择"
    normalization_label = tkinter.Label(root, text=normalization_label_text)
    normalization_label.grid(column=1, row=1)

    display_label = tkinter.Label(root, text='默认使用LogisticRegressionCV')
    display_label.grid(column=1, row=2)

    start_button = tkinter.Button(root, text='开始分析', command=lambda: predict_by(
        progress_label, balanced_accuracy_train_label, balanced_accuracy_test_label))
    start_button.grid(column=0, row=2)
    start_button.config(state='disabled')

    progress_label = tkinter.Label(root, text='分析进度: 0%')
    progress_label.grid(column=0, row=4)

    balanced_accuracy_train_label = tkinter.Label(root, text='平均训练集平衡精度: ')
    balanced_accuracy_train_label.grid(column=0, row=5)

    balanced_accuracy_test_label = tkinter.Label(root, text='平均测试集平衡精度: ')
    balanced_accuracy_test_label.grid(column=1, row=5)

    file_button = tkinter.Button(
        root, text="选择要检测的txt文件", command=lambda: open_file_dialog(file_name_label))
    file_button.grid(column=0, row=7)

    file_name_label = tkinter.Label(root, text='您尚未进行检测')
    file_name_label.grid(column=1, row=7)

    root.config(menu=menu_bar)
    root.mainloop()


photo_accuracy, photo_precision_recall_f1score, photo_Confusion_Matrix = None, None, None
# defult selection 但是在 on_selcted() 被清空了，所以缺省值是否有意义？
exact_selection = "LogisticRegressionCV(Cs=20, penalty='l1', cv=StratifiedKFold(5, shuffle=True), max_iter=10000, solver='liblinear', scoring='balanced_accuracy', multi_class='ovr', n_jobs=-1)"

root = tkinter.Tk()
progress_bar = ttk.Progressbar(root, length=200, mode='determinate')
if __name__ == "__main__":
    create_gui()
