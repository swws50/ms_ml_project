import pandas as pd
import numpy as np
from sklearn import metrics ##矩阵
from matplotlib import pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import confusion_matrix,recall_score,classification_report,accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedKFold
#%matplotlib widget
d = pd.read_csv('python-Frag_area.csv', header=0)
X = d.iloc[1:,:].values.T
ylabels = d.iloc[0, :].values
ylabels=pd.Series(ylabels)
print(ylabels.value_counts())

encoder = LabelEncoder() 
y = encoder.fit_transform(ylabels)
train_X, test_X, train_y, test_y, train_labels, test_labels = train_test_split(X, y, d.columns,test_size=0.2, stratify=y)#取20%为训练集


from sklearn.linear_model import LogisticRegressionCV
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.neural_network import MLPClassifier
from sklearn import svm, datasets
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
import tqdm
from sklearn.metrics import roc_curve, auc
from sklearn import metrics
import tkinter
from tkinter import filedialog



root=tkinter.Tk()
root.title('诊断分析')
menu_bar = tkinter.Menu(root)
option_menu = tkinter.Menu(menu_bar, tearoff=0)
selections=["RandomForestClassifier(500)",
            "LogisticRegressionCV(Cs=20, penalty='l1', cv=StratifiedKFold(5, shuffle=True), max_iter=10000, solver='liblinear', scoring='balanced_accuracy', multi_class='ovr', n_jobs=-1)",
            "LinearDiscriminantAnalysis(solver='eigen', shrinkage='auto')",
            "svm.LinearSVC(max_iter=10000)",
            "MLPClassifier((100, 200, 100), activation='logistic',max_iter=2000)"
]
var_selection = tkinter.StringVar()
var_selection.set(selections[1])
exact_selection="LogisticRegressionCV(Cs=20, penalty='l1', cv=StratifiedKFold(5, shuffle=True), max_iter=10000, solver='liblinear', scoring='balanced_accuracy', multi_class='ovr', n_jobs=-1)"#defult selection

def on_selcted():
    global exact_selection
    exact_selection=''
    exact_selection=var_selection.get()
    display_label.config(text='您选择了'+exact_selection.split('(')[0])


def predict_by():
    balanced_accuracy_train = []
    balanced_accuracy_test = []
    lrs = []
    Fscores = np.zeros((500,4))

    confusion_matrixs = np.zeros((500,4))
    auc_lists = np.zeros((500,1))
    auc_list = []
    for i in tqdm.tqdm(range(500)):
        percentage = (i + 1) / 500 * 100
        progress_label.config(text='分析进度: {0:.2f}%'.format(percentage))
        root.update_idletasks()

        train_X, test_X, train_y, test_y, train_labels, test_labels = train_test_split(X, y, d.columns,test_size=0.2, stratify=y)
        lrcv =eval(exact_selection)###可以改成上面注释里的不同方法
    
        lrcv.fit(train_X, train_y)
        balanced_accuracy_train.append(lrcv.score(train_X, train_y))
        balanced_accuracy_test.append(lrcv.score(test_X, test_y))

        y_pred = lrcv.predict(test_X)
        confusion_matrixs[i] = confusion_matrix(test_y,y_pred).flatten()
        Fscore=metrics.classification_report(test_y, y_pred, labels=[0,1], output_dict = True)
        Fscores[i][0] = Fscore["weighted avg"]["precision"]
        Fscores[i][1] = Fscore["weighted avg"]["recall"]
        Fscores[i][2] = Fscore["weighted avg"]["f1-score"]
    

        lrs.append(lrcv)
    '''
    from sklearn.metrics import RocCurveDisplay
    disp = RocCurveDisplay.from_estimator(lrcv,test_X, test_y)
    auc_lists[i]=metrics.auc(disp.fpr,disp.tpr)'''

    np.savetxt( "Con_matrix_SVM.csv", confusion_matrixs, delimiter="," )
    np.savetxt( "Fscore_SVM.csv", Fscores, delimiter="," )
    np.savetxt( "2C_auc_SVM.csv", auc_lists, delimiter="," )
    mean_balanced_accuracy_train = np.mean(balanced_accuracy_train)
    mean_balanced_accuracy_test = np.mean(balanced_accuracy_test)
    
    balanced_accuracy_train_label.config(text=f"平均训练集平衡精度: {mean_balanced_accuracy_train:.4f}")
    balanced_accuracy_test_label.config(text=f"平均测试集平衡精度: {mean_balanced_accuracy_test:.4f}")
    print(np.mean(balanced_accuracy_train), np.mean(balanced_accuracy_test))
#print(np.mean(metrics.auc(disp.fpr,disp.tpr)))

def open_file_dialog():
    file_path = filedialog.askopenfilename(initialdir="/", title="Select File",
                                           filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
    if file_path != '':
        file_name_label.config(text='已选择'+file_path)
    pass
####没写完
####没写完
####没写完
####没写完
####没写完

for item in selections:
    option_menu.add_radiobutton(label=item.split('(')[0], variable=var_selection, value=item, command=on_selcted)
menu_bar.add_cascade(label="模型选择", menu=option_menu)
display_label = tkinter.Label(root,text='默认使用LogisticRegressionCV')   
display_label.grid(column=0,row=1)
start_button = tkinter.Button(root,text='开始分析',command=predict_by)
start_button.grid(column=0,row=2) 
progress_label = tkinter.Label(root, text='分析进度: 0%')
progress_label.grid(column=0, row=3)
balanced_accuracy_train_label = tkinter.Label(root, text='平均训练集平衡精度: ')
balanced_accuracy_train_label.grid(column=0, row=4)
balanced_accuracy_test_label = tkinter.Label(root, text='平均测试集平衡精度: ')
balanced_accuracy_test_label.grid(column=1, row=4)
file_button = tkinter.Button(root, text="选择要检测的txt文件", command=open_file_dialog)
file_button.grid(column=0,row=5)
file_name_label = tkinter.Label(root,text='您尚未进行检测')
file_name_label.grid(column=1,row=5)
root.config(menu=menu_bar)
root.mainloop()