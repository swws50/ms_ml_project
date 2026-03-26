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
            'include_dataset_info': ctk.BooleanVar(value=True),
            'include_training_info': ctk.BooleanVar(value=True),
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

        # 智能检测：根据 data_store 实际数据状态决定默认勾选
        _ss = data_store.get_system_status()
        self.print_options['include_dataset_info'].set(
            _ss.get('file_classification', {}).get('has_data', False))
        self.print_options['include_training_info'].set(
            data_store.get_training_data_info().get('has_data', False))
        self.print_options['include_prediction_info'].set(
            hasattr(data_store, 'get_latest_prediction') and
            data_store.get_latest_prediction() is not None)
        self.print_options['include_model_info'].set(
            data_store.get_latest_model_info().get('has_model', False))

        options = [
            ("include_dataset_info", "数据集信息"),
            ("include_training_info", "训练信息"),
            ("include_prediction_info", "预测结果"),
            ("include_model_info", "模型信息")
        ]

        for key, text in options:
            checkbox = ctk.CTkCheckBox(
                content_frame,
                text=text,
                variable=self.print_options[key]
            )
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
        """生成临时 PDF 并用系统默认阅读器打开预览"""
        import tempfile
        try:
            self.print_manager._current_patient_info = self.patient_info
            self.print_manager._current_options = self.print_options
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            self.print_manager._export_to_pdf(tmp.name)
            os.startfile(tmp.name)
        except Exception as e:
            messagebox.showerror("预览失败", str(e))
    
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
        system_status = data_store.get_system_status()
        has_data = any([
            system_status.get('file_classification', {}).get('has_data', False),
            data_store.get_training_data_info().get('has_data', False),
            data_store.get_latest_model_info().get('has_model', False),
            hasattr(data_store, 'get_latest_prediction') and data_store.get_latest_prediction() is not None,
        ])
        if not has_data:
            return False

        self._current_patient_info = patient_info
        self._current_options = options
        self._export_to_file()
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

            stem = os.path.splitext(os.path.basename(metrics_path))[0]
            charts_dir = metrics_path.replace('\\metrics\\', '\\charts\\') \
                                     .replace('/metrics/', '/charts/') \
                                     .replace('.json', '')
            chart_roc_path = os.path.join(charts_dir, 'ROC_Curve.png')
            chart_cm_path  = os.path.join(charts_dir, 'ConfusionMatrix.png')

            return {
                'auc':  (auc_mean,  auc_std,  auc_lo,  auc_hi),
                'sens': (sens_mean, sens_std, sens_lo, sens_hi),
                'spec': (spec_mean, spec_std, spec_lo, spec_hi),
                'f1':   (f1_mean,   f1_std),
                'n_iter': len(auc_arr),
                'cv': meta.get('cv', ''),
                'threshold_strategy': meta.get('threshold_strategy', ''),
                'class_names': meta.get('class_names', []),
                'chart_roc': chart_roc_path if os.path.exists(chart_roc_path) else None,
                'chart_cm':  chart_cm_path  if os.path.exists(chart_cm_path)  else None,
            }
        except Exception:
            return None

    def _export_to_file(self):
        """弹出保存框并导出 PDF"""
        filename = filedialog.asksaveasfilename(
            title="保存诊断报告",
            defaultextension=".pdf",
            initialfile=f"肝癌早筛预警检测报告_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            filetypes=[("PDF文件", "*.pdf")]
        )
        if filename:
            try:
                self._export_to_pdf(filename)
                log_message(f"报告已保存到: {filename}", "SUCCESS")
            except Exception as e:
                log_message(f"保存报告失败: {str(e)}", "ERROR")
                raise

    def _export_to_pdf(self, filename):
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
            'SectionHeader', fontName=font_name, fontSize=14,
            leading=22, spaceBefore=6, spaceAfter=2, textColor=colors.HexColor('#1a3a5c')
        )
        style_body = ParagraphStyle(
            'BodyText', fontName=font_name, fontSize=12, leading=18
        )
        style_indent = ParagraphStyle(
            'Indent', fontName=font_name, fontSize=12, leading=18, leftIndent=20
        )
        style_indent2 = ParagraphStyle(
            'Indent2', fontName=font_name, fontSize=12, leading=18, leftIndent=40
        )
        # 病人信息段专用缩小版样式（整体缩小两个字号）
        style_body_sm = ParagraphStyle(
            'BodyTextSm', fontName=font_name, fontSize=10, leading=16
        )

        HEADER_BG   = colors.HexColor('#1a3a5c')
        HEADER_FG   = colors.white
        BORDER      = colors.HexColor('#cccccc')

        def title_rule():
            """标题下方粗横线"""
            return HRFlowable(width='100%', thickness=2,
                              color=colors.HexColor('#1a3a5c'), spaceAfter=6)

# ── 读取数据 ──────────────────────────────────────────────
        from config import get_output_paths, ICON_CONFIG
        OUTPUT_FILES = get_output_paths()

        model_info       = data_store.get_latest_model_info()
        system_status    = data_store.get_system_status()
        training_data    = data_store.get_training_data_info()
        latest_pred      = data_store.get_latest_prediction() if hasattr(data_store, 'get_latest_prediction') else None
        metrics          = self._load_metrics_summary(model_info.get('model_path', ''))

        # ── 病人信息判断 ──────────────────────────────────────────
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

        # ── 图表路径（优先用与模型绑定的 metrics 副本，回退到 charts/）──
        chart_roc = (metrics.get('chart_roc') if metrics else None) \
                    or str(OUTPUT_FILES.get('chart_roc', ''))
        chart_cm  = (metrics.get('chart_cm')  if metrics else None) \
                    or str(OUTPUT_FILES.get('chart_confusion', ''))

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
        title_style = ParagraphStyle(
            'Title', fontName=font_name, fontSize=20,
            leading=22, alignment=1,
            textColor=colors.HexColor('#1a3a5c')
        )
        icon_path = str(ICON_CONFIG.get('app_icon_png', ''))
        if os.path.exists(icon_path):
            icon_img = Image(icon_path)
            icon_img._restrictSize(40, 40)
            title_row = Table(
                [[icon_img, Paragraph("肝癌早筛预警检测报告", title_style)]],
                colWidths=[46, 210]  # 紧凑宽度，整体居中
            )
            title_row.setStyle(TableStyle([
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING',    (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('LEFTPADDING',   (1, 0), (1, 0),   4),
                ('RIGHTPADDING',  (1, 0), (1, 0),   0),
            ]))
            title_row.hAlign = 'CENTER'
            story.append(title_row)
        else:
            story.append(Paragraph("肝癌早筛预警检测报告", title_style))
        story.append(Spacer(1, 12))
        story.append(title_rule())

        # ════════════════════════════════════════════════════════
        # 病人基础信息 + 预测结果 + 模型基本信息（有病人信息时）
        # ════════════════════════════════════════════════════════
        if has_patient:
            # 病人基础信息（两行三列表格）
            col_w = page_width / 3
            row1 = [
                Paragraph(f"姓名：{p_name}", style_body_sm),
                Paragraph(f"性别：{p_gender}", style_body_sm),
                Paragraph(f"年龄：{p_age} 岁", style_body_sm),
            ]
            row2 = [
                Paragraph(f"编号：{p_id}", style_body_sm),
                Paragraph(f"预测结果：{latest_pred.get('predicted_class', 'N/A')}", style_body_sm),
                Paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style_body_sm),
            ]
            patient_table = Table([row1, row2], colWidths=[col_w, col_w, col_w])
            patient_table.setStyle(TableStyle([
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN',         (2, 1), (2, 1),   'RIGHT'),
                ('TOPPADDING',    (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(patient_table)
            story.append(HRFlowable(width='100%', thickness=0.5,
                                    color=colors.HexColor('#aaaaaa'), spaceBefore=4, spaceAfter=6))
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
                total_s = sum(training_data['class_distribution'].values())
                cls_names_td = system_status.get('file_classification', {}).get('class_names', ['类别0', '类别1'])
                parts = []
                for cls, count in training_data['class_distribution'].items():
                    pct = count / total_s * 100 if total_s > 0 else 0
                    idx = int(cls)
                    cname = cls_names_td[idx] if idx < len(cls_names_td) else f"类别{cls}"
                    parts.append(f'"{cname}" {count}个（{pct:.1f}%）')
                story.append(Paragraph(f"类别分布：{'  '.join(parts)}", style_indent))
                if len(training_data['class_distribution']) == 2:
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

        story.append(Spacer(1, 4))
        story.append(title_rule())
        
        # 免责声明
        story.append(Paragraph(
            "本报告由人工智能辅助分析生成，仅供科研使用，不得作为诊断依据。任何医疗决策请咨询执业医师。",
            ParagraphStyle('Disclaimer', fontName=font_name, fontSize=9,
                           leading=13, textColor=colors.HexColor('#888888'), alignment=1)
        ))

        doc.build(story)