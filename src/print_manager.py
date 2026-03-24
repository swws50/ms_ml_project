# print_manager.py - 简化的打印管理模块（医用版本）

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from datetime import datetime
import data_store
from utils import log_message, set_window_icon, center_window

class PrintDialog:
    """打印对话框窗口"""
    
    def __init__(self, parent, print_manager):
        self.parent = parent
        self.print_manager = print_manager
        self.dialog = None
        self._icon_ref = None # 保持图标引用，防止被垃圾回收
        self.print_options = {
            'include_dataset_info': ctk.BooleanVar(value=False),
            'include_training_info': ctk.BooleanVar(value=False),
            'include_prediction_info': ctk.BooleanVar(value=True),
            'include_model_info': ctk.BooleanVar(value=True),
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
        center_window(self.dialog, 400, 650)

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
            ("include_dataset_info", "数据集信息", False),
            ("include_training_info", "训练信息", False),
            ("include_prediction_info", "预测结果", True),
            ("include_model_info", "模型信息", True)
        ]

        for key, text, default_value in options:
            checkbox = ctk.CTkCheckBox(
                content_frame, 
                text=text, 
                variable=self.print_options[key]
            )
            # 设置默认值
            self.print_options[key].set(default_value)
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
        center_window(preview_window, 700, 500)
        
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

        # 暂存结构化数据供 _export_to_pdf 使用
        self._current_patient_info = patient_info
        self._current_options = options

        self._export_to_file(content)
        return True
    
    def _load_metrics_summary(self, model_path):
        """从与模型同名的 metrics JSON 中计算摘要统计量，返回 dict 或 None"""
        try:
            import json, numpy as np
            from scipy import stats as scipy_stats

            model_path = str(model_path)  # 兼容 WindowsPath 对象

            if not model_path:
                return None

            # 将 models/*.joblib 映射到 metrics/*.json（兼容正反斜杠）
            metrics_path = model_path.replace('\\models\\', '\\metrics\\') \
                                     .replace('/models/', '/metrics/') \
                                     .replace('.joblib', '.json')

            if not os.path.exists(metrics_path):
                return None

            with open(metrics_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            auc_arr = np.array(data.get('auc_list', []), dtype=float)
            cms = data.get('confusion_matrices', [])
            f_scores = data.get('f_scores', [])
            meta = data.get('meta', {})

            if len(auc_arr) == 0 or len(cms) == 0:
                return None

            # 每折 sensitivity / specificity
            sens_arr = np.array([
                cm['tp'] / (cm['tp'] + cm['fn']) if (cm['tp'] + cm['fn']) > 0 else 0.0
                for cm in cms
            ])
            spec_arr = np.array([
                cm['tn'] / (cm['tn'] + cm['fp']) if (cm['tn'] + cm['fp']) > 0 else 0.0
                for cm in cms
            ])
            f1_arr = np.array([fs.get('f1', 0.0) for fs in f_scores], dtype=float)

            def _ci(arr):
                n = len(arr)
                se = scipy_stats.sem(arr)
                lo, hi = scipy_stats.t.interval(0.95, n - 1, loc=arr.mean(), scale=se)
                return arr.mean(), arr.std(), lo, hi

            auc_mean, auc_std, auc_lo, auc_hi = _ci(auc_arr)
            sens_mean, sens_std, sens_lo, sens_hi = _ci(sens_arr)
            spec_mean, spec_std, spec_lo, spec_hi = _ci(spec_arr)
            f1_mean, f1_std, _, _ = _ci(f1_arr)

            return {
                'auc':  (auc_mean,  auc_std,  auc_lo,  auc_hi),
                'sens': (sens_mean, sens_std, sens_lo, sens_hi),
                'spec': (spec_mean, spec_std, spec_lo, spec_hi),
                'f1':   (f1_mean,   f1_std),
                'n_iter': len(auc_arr),
                'cv': meta.get('cv', ''),
                'threshold_strategy': meta.get('threshold_strategy', ''),
                'class_names': meta.get('class_names', []),
            }
        except Exception:
            return None

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

        # 预测信息
        if options['include_prediction_info'].get() and latest_prediction:
            content_parts.append("预测结果:")
            content_parts.append(f"  文件名: {latest_prediction.get('filename', 'N/A')}")
            content_parts.append(f"  预测类别: {latest_prediction.get('predicted_class', 'N/A')}")
            content_parts.append(f"  置信度: {latest_prediction.get('confidence', 0):.4f}")
            content_parts.append(f"  预测时间: {latest_prediction.get('timestamp', 'N/A')}")
            content_parts.append("")

        # 模型信息
        if options['include_model_info'].get() and model_info.get('has_model', False):
            content_parts.append("模型信息:")
            content_parts.append(f"  模型类型: {model_info.get('model_type', 'N/A')}")

            metrics = self._load_metrics_summary(model_info.get('model_path', ''))
            if metrics:
                cv_str = metrics['cv'] if metrics['cv'] else f"{metrics['n_iter']} 次迭代"
                thresh_str = f" ({metrics['threshold_strategy']})" if metrics['threshold_strategy'] else ""
                auc_m,  auc_s,  auc_lo,  auc_hi  = metrics['auc']
                sens_m, sens_s, sens_lo, sens_hi = metrics['sens']
                spec_m, spec_s, spec_lo, spec_hi = metrics['spec']
                f1_m,   f1_s                      = metrics['f1']

                # 类别名称（来自 metrics JSON，比 data_store 更贴近训练时状态）
                cls_names = metrics['class_names']
                sens_label = f"灵敏度 [{cls_names[1]}]" if len(cls_names) > 1 else "灵敏度"
                spec_label = f"特异度 [{cls_names[0]}]" if len(cls_names) > 0 else "特异度"

                content_parts.append(f"  交叉验证: {cv_str}{thresh_str}")
                content_parts.append(f"  AUC-ROC:  {auc_m:.3f} ± {auc_s:.3f}  [95% CI: {auc_lo:.3f} ~ {auc_hi:.3f}]")
                content_parts.append(f"  {sens_label}: {sens_m:.3f} ± {sens_s:.3f}  [95% CI: {sens_lo:.3f} ~ {sens_hi:.3f}]")
                content_parts.append(f"  {spec_label}: {spec_m:.3f} ± {spec_s:.3f}  [95% CI: {spec_lo:.3f} ~ {spec_hi:.3f}]")
                content_parts.append(f"  F1 Score: {f1_m:.3f} ± {f1_s:.3f}")
            else:
                content_parts.append(f"  训练状态: 已完成")
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
            content_parts.append("")

        # 训练信息
        if options['include_training_info'].get() and training_data_info.get('has_data', False):
            content_parts.append("训练数据信息:")
            content_parts.append(f"  样本数量: {training_data_info.get('n_samples', 'N/A')} 个")
            content_parts.append(f"  特征数量: {training_data_info.get('n_features', 'N/A')} 个")

            # 类别分布
            if 'class_distribution' in training_data_info and training_data_info['class_distribution']:
                content_parts.append("  类别分布:")
                total_samples = sum(training_data_info['class_distribution'].values())
                class_names = system_status.get('file_classification', {}).get('class_names', ['类别0', '类别1'])

                for cls, count in training_data_info['class_distribution'].items():
                    percentage = (count / total_samples * 100) if total_samples > 0 else 0
                    cls_idx = int(cls)
                    class_name = class_names[cls_idx] if cls_idx < len(class_names) else f"类别{cls}"
                    content_parts.append(f"    \"{class_name}\": {count} 个样本 ({percentage:.1f}%)")

            # 数据平衡性评估
            if len(training_data_info.get('class_distribution', {})) == 2:
                counts = list(training_data_info['class_distribution'].values())
                balance_ratio = min(counts) / max(counts) if max(counts) > 0 else 0
                balance_status = "平衡" if balance_ratio > 0.8 else "不平衡" if balance_ratio > 0.5 else "严重不平衡"
                content_parts.append(f"  数据平衡性: {balance_status} (比例: {balance_ratio:.2f})")

            content_parts.append("")

        return "\n".join(content_parts)
    
    def _export_to_file(self, content):
        """弹出保存框并导出 PDF"""
        filename = filedialog.asksaveasfilename(
            title="保存诊断报告",
            defaultextension=".pdf",
            initialfile=f"肝癌早筛预警检测报告_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            filetypes=[("PDF文件", "*.pdf")]
        )
        if filename:
            try:
                self._export_to_pdf(filename, content)
                log_message(f"报告已保存到: {filename}", "SUCCESS")
            except Exception as e:
                log_message(f"保存报告失败: {str(e)}", "ERROR")
                raise
    
    def _export_to_pdf(self, filename, content):
        """导出内容到PDF文件（Platypus 布局引擎）"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, Image,
                                        HRFlowable)
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # ── 中文字体 ──────────────────────────────────────────────
        try:
            pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))
            font_name = 'SimSun'
        except Exception:
            try:
                pdfmetrics.registerFont(TTFont('SimHei', 'simhei.ttf'))
                font_name = 'SimHei'
            except Exception:
                font_name = 'Helvetica'

        # ── 样式 ─────────────────────────────────────────────────
        style_header = ParagraphStyle(
            'SectionHeader', fontName=font_name, fontSize=12,
            leading=18, spaceBefore=6, spaceAfter=2, textColor=colors.HexColor('#1a3a5c')
        )
        style_body = ParagraphStyle(
            'BodyText', fontName=font_name, fontSize=10, leading=14
        )
        style_indent = ParagraphStyle(
            'Indent', fontName=font_name, fontSize=10, leading=14, leftIndent=20
        )
        style_indent2 = ParagraphStyle(
            'Indent2', fontName=font_name, fontSize=10, leading=14, leftIndent=40
        )

        HEADER_BG   = colors.HexColor('#1a3a5c')
        HEADER_FG   = colors.white
        BORDER      = colors.HexColor('#cccccc')

        def title_rule():
            """标题下方粗横线"""
            return HRFlowable(width='100%', thickness=2,
                              color=colors.HexColor('#1a3a5c'), spaceAfter=6)

# ── 读取数据 ──────────────────────────────────────────────
        from config import get_output_paths
        OUTPUT_FILES = get_output_paths()

        model_info       = data_store.get_latest_model_info()
        system_status    = data_store.get_system_status()
        training_data    = data_store.get_training_data_info()
        latest_pred      = data_store.get_latest_prediction() if hasattr(data_store, 'get_latest_prediction') else None
        metrics          = self._load_metrics_summary(model_info.get('model_path', ''))

        # ── 病人信息判断 ──────────────────────────────────────────
        # content 参数在此路径不使用，仅保留以兼容调用签名
        # patient_info 通过 execute_print → _export_to_file 的调用链不直接传入，
        # 因此从 _generate_content 生成的 content 字符串中无法简单还原结构化信息。
        # 解决方案：将 patient_info 暂存到实例变量，由 execute_print 负责设置。
        patient_info = getattr(self, '_current_patient_info', None)
        has_patient = False
        p_name = p_age = p_id = p_gender = p_date = ''
        if patient_info:
            p_name   = patient_info['name'].get().strip()
            p_age    = patient_info['age'].get().strip()
            p_id     = patient_info['patient_id'].get().strip()
            p_gender = patient_info['gender'].get().strip()
            p_date   = patient_info['diagnosis_date'].get().strip()
            has_patient = any([p_name, p_age, p_id])

        options = getattr(self, '_current_options', {})
        def opt(key):
            v = options.get(key)
            return v.get() if v is not None else True

        # ── 图表路径 ──────────────────────────────────────────────
        chart_roc = str(OUTPUT_FILES.get('chart_roc', ''))
        chart_cm  = str(OUTPUT_FILES.get('chart_confusion', ''))

        # ── 构建 Flowables ────────────────────────────────────────
        doc = SimpleDocTemplate(
            filename, pagesize=A4,
            leftMargin=50, rightMargin=50,
            topMargin=20, bottomMargin=50,
            title="肝癌早筛预警检测报告"
        )
        page_width = A4[0] - 100  # 可用宽度

        story = []

        # ════════════════════════════════════════════════════════
        # 报告标题（始终显示）
        # ════════════════════════════════════════════════════════
        story.append(Paragraph("肝癌早筛预警检测报告", ParagraphStyle(
            'Title', fontName=font_name, fontSize=18,
            leading=22, spaceAfter=3, alignment=1,
            textColor=colors.HexColor('#1a3a5c')
        )))
        story.append(Spacer(1, 12))
        story.append(title_rule())
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                               ParagraphStyle('TimeRight', fontName=font_name, fontSize=10, leading=14, alignment=2)))

        # ════════════════════════════════════════════════════════
        # 病人基础信息 + 预测结果 + 模型基本信息（有病人信息时）
        # ════════════════════════════════════════════════════════
        if has_patient:
            # 病人基础信息
            story.append(Paragraph("病人基础信息", style_header))
            if p_name:   story.append(Paragraph(f"姓名：{p_name}", style_indent))
            if p_age:    story.append(Paragraph(f"年龄：{p_age} 岁", style_indent))
            if p_gender: story.append(Paragraph(f"性别：{p_gender}", style_indent))
            if p_id:     story.append(Paragraph(f"病人编号：{p_id}", style_indent))
            if p_date:   story.append(Paragraph(f"诊断日期：{p_date}", style_indent))
            story.append(Spacer(1, 4))

            # 预测结果
            if opt('include_prediction_info') and latest_pred:
                story.append(Paragraph("预测结果", style_header))
                story.append(Paragraph(f"文件名：{latest_pred.get('filename', 'N/A')}", style_indent))
                story.append(Paragraph(f"预测类别：{latest_pred.get('predicted_class', 'N/A')}", style_indent))
                story.append(Paragraph(f"置信度：{latest_pred.get('confidence', 0):.4f}", style_indent))
                story.append(Paragraph(f"预测时间：{latest_pred.get('timestamp', 'N/A')}", style_indent))
                story.append(Spacer(1, 4))


        # ════════════════════════════════════════════════════════
        # 模型信息（模型类型 + 交叉验证 + 性能指标，纯文本）
        if opt('include_model_info') and model_info.get('has_model', False):
            story.append(Paragraph("模型信息", style_header))
            story.append(Paragraph(f"模型类型：{model_info.get('model_type', 'N/A')}", style_indent))
            if metrics:
                cv_str = metrics['cv'] if metrics['cv'] else f"{metrics['n_iter']} 次迭代"
                thresh_str = f"（{metrics['threshold_strategy']}）" if metrics['threshold_strategy'] else ""
                cls_names = metrics['class_names']
                sens_label = f"灵敏度 [{cls_names[1]}]" if len(cls_names) > 1 else "灵敏度"
                spec_label = f"特异度 [{cls_names[0]}]" if len(cls_names) > 0 else "特异度"
                auc_m,  auc_s,  auc_lo,  auc_hi  = metrics['auc']
                sens_m, sens_s, sens_lo, sens_hi = metrics['sens']
                spec_m, spec_s, spec_lo, spec_hi = metrics['spec']
                f1_m,   f1_s                     = metrics['f1']
                story.append(Paragraph(f"交叉验证：{cv_str}{thresh_str}", style_indent))
                story.append(Paragraph(f"AUC-ROC：{auc_m:.3f} ± {auc_s:.3f}  [95% CI: {auc_lo:.3f} ~ {auc_hi:.3f}]", style_indent))
                story.append(Paragraph(f"{sens_label}：{sens_m:.3f} ± {sens_s:.3f}  [95% CI: {sens_lo:.3f} ~ {sens_hi:.3f}]", style_indent))
                story.append(Paragraph(f"{spec_label}：{spec_m:.3f} ± {spec_s:.3f}  [95% CI: {spec_lo:.3f} ~ {spec_hi:.3f}]", style_indent))
                story.append(Paragraph(f"F1 Score：{f1_m:.3f} ± {f1_s:.3f}", style_indent))
            else:
                story.append(Paragraph("训练状态：已完成", style_indent))
            story.append(Spacer(1, 4))

        # 训练数据信息（勾选"训练信息"时显示）
        if opt('include_training_info') and training_data.get('has_data', False):
            story.append(Paragraph("训练数据信息", style_header))
            story.append(Paragraph(f"样本数量：{training_data.get('n_samples', 'N/A')} 个", style_indent))
            story.append(Paragraph(f"特征数量：{training_data.get('n_features', 'N/A')} 个", style_indent))
            if 'class_distribution' in training_data and training_data['class_distribution']:
                story.append(Paragraph("类别分布：", style_indent))
                total_s = sum(training_data['class_distribution'].values())
                cls_names_td = system_status.get('file_classification', {}).get('class_names', ['类别0', '类别1'])
                for cls, count in training_data['class_distribution'].items():
                    pct = count / total_s * 100 if total_s > 0 else 0
                    idx = int(cls)
                    cname = cls_names_td[idx] if idx < len(cls_names_td) else f"类别{cls}"
                    story.append(Paragraph(f'"{cname}"：{count} 个样本（{pct:.1f}%）', style_indent2))
            if len(training_data.get('class_distribution', {})) == 2:
                counts = list(training_data['class_distribution'].values())
                ratio = min(counts) / max(counts) if max(counts) > 0 else 0
                bal = "平衡" if ratio > 0.8 else ("不平衡" if ratio > 0.5 else "严重不平衡")
                story.append(Paragraph(f"数据平衡性：{bal}（比例 {ratio:.2f}）", style_indent))
            story.append(Spacer(1, 4))

        # 数据集信息
        if opt('include_dataset_info') and system_status.get('file_classification', {}).get('has_data', False):
            story.append(Paragraph("数据集信息", style_header))
            fc = system_status['file_classification']
            cn = fc['class_names']
            fct = fc['file_counts']
            story.append(Paragraph(f'类别0 "{cn[0]}"：{fct["class_0"]} 个文件', style_body))
            story.append(Paragraph(f'类别1 "{cn[1]}"：{fct["class_1"]} 个文件', style_body))
            story.append(Paragraph(f"总文件数：{fct['total']} 个文件", style_body))
            story.append(Spacer(1, 4))

        # ROC 曲线 + 混淆矩阵 并排
        has_roc = os.path.exists(chart_roc)
        has_cm  = os.path.exists(chart_cm)
        if has_roc or has_cm:
            story.append(Paragraph("模型评估图表", style_header))
            img_w = (page_width - 12) / 2   # 两列各占半宽，留 12 间距
            img_h = 200

            def _make_img_cell(path, caption):
                if not os.path.exists(path):
                    return Paragraph(f"（{caption} 文件不存在）", style_body)
                img = Image(path)
                img._restrictSize(img_w, img_h)
                return img

            cell_roc = _make_img_cell(chart_roc, "ROC 曲线")
            cell_cm  = _make_img_cell(chart_cm,  "混淆矩阵")

            chart_table = Table(
                [[cell_roc, cell_cm],
                 [Paragraph("ROC 曲线", ParagraphStyle('cap', fontName=font_name, fontSize=9, alignment=1)),
                  Paragraph("混淆矩阵", ParagraphStyle('cap2', fontName=font_name, fontSize=9, alignment=1))]],
                colWidths=[img_w + 6, img_w + 6]
            )
            chart_table.setStyle(TableStyle([
                ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING',   (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
            ]))
            story.append(chart_table)

        doc.build(story)