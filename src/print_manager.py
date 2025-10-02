# print_manager.py - 简化的打印管理模块（医用版本）

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from datetime import datetime
import data_store
from utils import log_message, set_window_icon

class PrintDialog:
    """打印对话框窗口"""
    
    def __init__(self, parent, print_manager):
        self.parent = parent
        self.print_manager = print_manager
        self.dialog = None
        self._icon_ref = None # 保持图标引用，防止被垃圾回收
        self.print_options = {
            'include_dataset_info': ctk.BooleanVar(value=True),
            'include_training_info': ctk.BooleanVar(value=True),
            'include_prediction_info': ctk.BooleanVar(value=True),
            'include_model_info': ctk.BooleanVar(value=True),
            'export_to_file': ctk.BooleanVar(value=True)
        }
        
        self.patient_info = {
            'name': ctk.StringVar(),
            'age': ctk.StringVar(),
            'patient_id': ctk.StringVar(),
            'gender': ctk.StringVar(value="男"),
            'diagnosis_date': ctk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        }

    def show_dialog(self):
        """显示打印设置对话框"""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("打印设置")
        self.dialog.geometry("400x650")

        # 设置图标
        set_window_icon(self.dialog) 

        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self._create_dialog_content()
        self.dialog.wait_window()
    
    def _create_dialog_content(self):
        """创建对话框内容"""
        # 标题
        title_label = ctk.CTkLabel(self.dialog, text="选择打印内容", 
                                 font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=20)
        
        # 内容选择
        content_frame = ctk.CTkFrame(self.dialog)
        content_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(content_frame, text="打印内容选择:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        options = [
            ("include_dataset_info", "数据集信息"),
            ("include_training_info", "训练信息"),
            ("include_prediction_info", "预测结果"),
            ("include_model_info", "模型信息")
        ]
        
        for key, text in options:
            checkbox = ctk.CTkCheckBox(content_frame, text=text, variable=self.print_options[key])
            checkbox.pack(anchor="w", padx=20, pady=5)

        # 病人信息输入
        patient_frame = ctk.CTkFrame(self.dialog)
        patient_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(patient_frame, text="病人基础信息:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        # 姓名输入
        name_frame = ctk.CTkFrame(patient_frame, fg_color="transparent")
        name_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(name_frame, text="姓名:", width=60).pack(side="left")
        ctk.CTkEntry(name_frame, textvariable=self.patient_info['name'], width=120).pack(side="left", padx=5)

        # 年龄和性别
        age_gender_frame = ctk.CTkFrame(patient_frame, fg_color="transparent")
        age_gender_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(age_gender_frame, text="年龄:", width=60).pack(side="left")
        ctk.CTkEntry(age_gender_frame, textvariable=self.patient_info['age'], width=60).pack(side="left", padx=5)
        ctk.CTkLabel(age_gender_frame, text="性别:", width=40).pack(side="left", padx=(20,5))
        gender_menu = ctk.CTkOptionMenu(age_gender_frame, variable=self.patient_info['gender'], 
                                    values=["男", "女"], width=60)
        gender_menu.pack(side="left")

        # 病人编号
        id_frame = ctk.CTkFrame(patient_frame, fg_color="transparent")
        id_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(id_frame, text="编号:", width=60).pack(side="left")
        ctk.CTkEntry(id_frame, textvariable=self.patient_info['patient_id'], width=150).pack(side="left", padx=5)

        # 诊断日期
        date_frame = ctk.CTkFrame(patient_frame, fg_color="transparent")
        date_frame.pack(fill="x", padx=10, pady=(2,10))
        ctk.CTkLabel(date_frame, text="日期:", width=60).pack(side="left")
        ctk.CTkEntry(date_frame, textvariable=self.patient_info['diagnosis_date'], width=120).pack(side="left", padx=5)

        # 导出选项
        export_frame = ctk.CTkFrame(self.dialog)
        export_frame.pack(fill="x", padx=20, pady=10)
        
        export_checkbox = ctk.CTkCheckBox(
            export_frame, 
            text="导出到文本文件", 
            variable=self.print_options['export_to_file']
        )
        export_checkbox.pack(anchor="w", padx=20, pady=10)
        
        # 按钮
        button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        # 预览按钮
        preview_btn = ctk.CTkButton(button_frame, text="预览", 
                                   command=self._on_preview, width=80)
        preview_btn.pack(side="left", padx=5)
        
        print_btn = ctk.CTkButton(button_frame, text="打印", 
                                 command=self._on_print, width=80)
        print_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(button_frame, text="取消", 
                                  command=self.dialog.destroy, width=80)
        cancel_btn.pack(side="right")
    
    def _on_preview(self):
        """预览打印内容"""
        content = self.print_manager._generate_content(self.print_options, self.patient_info)
        if content:
            self._show_preview_window(content)
        else:
            messagebox.showwarning("警告", "没有可预览的内容")
    
    def _show_preview_window(self, content):
        """显示预览窗口"""
        preview_window = ctk.CTkToplevel(self.dialog)
        preview_window.title("打印预览")
        preview_window.geometry("700x500")
        
        # 设置图标
        set_window_icon(preview_window)
        
        # 设置窗口层级
        preview_window.transient(self.dialog)
        preview_window.grab_set()
        preview_window.lift()
        preview_window.focus_set()
        
        # 创建文本框显示预览内容
        textbox = ctk.CTkTextbox(preview_window, font=ctk.CTkFont(family="Courier New"))
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("1.0", content)
        textbox.configure(state="disabled")
        
        # 关闭按钮
        close_btn = ctk.CTkButton(preview_window, text="关闭", 
                                 command=preview_window.destroy, width=100)
        close_btn.pack(pady=10)
    
    def _on_print(self):
        """执行打印操作"""
        try:
            success = self.print_manager.execute_print(self.print_options, self.patient_info)
            if success:
                log_message("报告已生成", "SUCCESS")
                self.dialog.destroy()
            else:
                messagebox.showwarning("警告", "没有可打印的内容")
        except Exception as e:
            log_message(f"打印失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"打印失败: {str(e)}")


class PrintManager:
    """打印管理器"""
    
    def __init__(self):
        pass
    
    def show_print_dialog(self, parent):
        """显示打印对话框"""
        dialog = PrintDialog(parent, self)
        dialog.show_dialog()
    
    def execute_print(self, options, patient_info=None):
        """执行打印操作"""
        content = self._generate_content(options, patient_info)
        if not content:
            return False
        
        # 打印到控制台
        print("\n" + "="*60)
        print("诊断分析报告")
        print("="*60)
        print(content)
        print("="*60)
        
        # 导出到文件
        if options['export_to_file'].get():
            self._export_to_file(content)
        
        return True
    
    def _generate_content(self, options, patient_info=None):
        """生成文本内容"""
        # 获取数据
        system_status = data_store.get_system_status()
        training_data_info = data_store.get_training_data_info()
        model_info = data_store.get_latest_model_info()
        latest_prediction = data_store.get_latest_prediction() if hasattr(data_store, 'get_latest_prediction') else None
        
        # 检查是否有数据
        has_data = any([
            system_status.get('file_classification', {}).get('has_data', False),
            training_data_info.get('has_data', False),
            model_info.get('has_model', False),
            latest_prediction is not None
        ])
        
        if not has_data:
            return None
        
        content_parts = []
        content_parts.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content_parts.append("")
        
        # 数据集信息
        if options['include_dataset_info'].get() and system_status.get('file_classification', {}).get('has_data', False):
            file_class = system_status['file_classification']
            class_names = file_class['class_names']
            file_counts = file_class['file_counts']
            
            content_parts.append("数据集信息:")
            content_parts.append(f"  类别0 \"{class_names[0]}\": {file_counts['class_0']} 个文件")
            content_parts.append(f"  类别1 \"{class_names[1]}\": {file_counts['class_1']} 个文件")
            content_parts.append(f"  总文件数: {file_counts['total']} 个文件")
            
            # 添加数据来源信息
            if file_counts['total'] > 0:
                content_parts.append(f"  数据来源: {'数据预处理' if file_counts['class_0'] > 0 or file_counts['class_1'] > 0 else 'CSV文件导入'}")
            content_parts.append("")

        # 训练信息
        if options['include_training_info'].get() and training_data_info.get('has_data', False):
            content_parts.append("训练数据信息:")
            content_parts.append(f"  样本数量: {training_data_info.get('n_samples', 'N/A')} 个")
            content_parts.append(f"  特征数量: {training_data_info.get('n_features', 'N/A')} 个")
            
            # 更精确的类别分布信息
            if 'class_distribution' in training_data_info and training_data_info['class_distribution']:
                content_parts.append("  类别分布:")
                total_samples = sum(training_data_info['class_distribution'].values())
                
                # 获取实际的类别名称
                class_names = system_status.get('file_classification', {}).get('class_names', ['类别0', '类别1'])
                
                for i, (cls, count) in enumerate(training_data_info['class_distribution'].items()):
                    percentage = (count / total_samples * 100) if total_samples > 0 else 0
                    class_name = class_names[int(cls)] if i < len(class_names) else f"类别{cls}"
                    content_parts.append(f"    \"{class_name}\": {count} 个样本 ({percentage:.1f}%)")
            
            # 添加数据平衡性评估
            if len(training_data_info.get('class_distribution', {})) == 2:
                counts = list(training_data_info['class_distribution'].values())
                balance_ratio = min(counts) / max(counts) if max(counts) > 0 else 0
                balance_status = "平衡" if balance_ratio > 0.8 else "不平衡" if balance_ratio > 0.5 else "严重不平衡"
                content_parts.append(f"  数据平衡性: {balance_status} (比例: {balance_ratio:.2f})")
            
            content_parts.append("")
        
        # 预测信息
        if options['include_prediction_info'].get() and latest_prediction:
            content_parts.append("最新预测结果:")
            content_parts.append(f"  文件名: {latest_prediction.get('filename', 'N/A')}")
            content_parts.append(f"  预测类别: {latest_prediction.get('predicted_class', 'N/A')}")
            content_parts.append(f"  置信度: {latest_prediction.get('confidence', 0):.4f}")
            content_parts.append(f"  预测时间: {latest_prediction.get('timestamp', 'N/A')}")
            content_parts.append("")
        
        # 模型信息
        if options['include_model_info'].get() and model_info.get('has_model', False):
            content_parts.append("模型信息:")
            content_parts.append(f"  模型类型: {model_info.get('model_type', 'N/A')}")
            content_parts.append(f"  训练状态: 已完成")
            content_parts.append("")
        # 病人基础信息
        if patient_info:
            name = patient_info['name'].get().strip()
            age = patient_info['age'].get().strip()
            patient_id = patient_info['patient_id'].get().strip()
            gender = patient_info['gender'].get()
            diagnosis_date = patient_info['diagnosis_date'].get().strip()
            
            if any([name, age, patient_id]):  # 至少有一个信息不为空
                content_parts.append("病人基础信息:")
                if name:
                    content_parts.append(f"  姓名: {name}")
                if age:
                    content_parts.append(f"  年龄: {age}岁")
                if gender:
                    content_parts.append(f"  性别: {gender}")
                if patient_id:
                    content_parts.append(f"  病人编号: {patient_id}")
                if diagnosis_date:
                    content_parts.append(f"  诊断日期: {diagnosis_date}")
                content_parts.append("")
                
        return "\n".join(content_parts)
    
    def _export_to_file(self, content):
        """导出内容到txt文件"""
        filename = filedialog.asksaveasfilename(
            title="保存诊断报告",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("诊断分析报告\n")
                    f.write("=" * 50 + "\n")
                    f.write(content)
                log_message(f"报告已保存到: {filename}", "SUCCESS")
            except Exception as e:
                log_message(f"保存报告失败: {str(e)}", "ERROR")
                raise