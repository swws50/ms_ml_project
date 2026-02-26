# consensus_peak_diagnostics.py - 共识峰识别诊断工具
"""
诊断框架设计思路：

共识峰识别过少的原因可分为两大类：
1. 数据质量问题：原始数据本身的问题
   - 峰发现阶段产出过少
   - 类别间样本不平衡
   - 信号强度异常（过低/过高噪声）
   
2. 算法逻辑问题：参数设置或筛选逻辑的问题
   - 出现率阈值过高
   - 折叠变化阈值过高
   - m/z分组宽度不合理

诊断报告将在每个阶段收集关键指标，帮助定位问题根源。
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Phase1Diagnostics:
    """阶段1诊断：峰发现质量"""
    total_files: int = 0
    successful_files: int = 0
    failed_files: List[str] = field(default_factory=list)
    
    # 每个文件的峰数量
    peaks_per_file: Dict[str, int] = field(default_factory=dict)
    
    # 强度统计
    intensity_stats: Dict[str, Dict] = field(default_factory=dict)  # file_id -> {min, max, mean, median}
    
    # 按类别统计
    class_0_files: int = 0
    class_1_files: int = 0
    class_0_total_peaks: int = 0
    class_1_total_peaks: int = 0
    
    def add_file_result(self, file_id: str, file_class: str, peaks_df: pd.DataFrame, success: bool):
        """记录单个文件的峰发现结果"""
        self.total_files += 1
        
        if not success or peaks_df.empty:
            self.failed_files.append(file_id)
            self.peaks_per_file[file_id] = 0
            return
        
        self.successful_files += 1
        peak_count = len(peaks_df)
        self.peaks_per_file[file_id] = peak_count
        
        # 强度统计
        intensities = peaks_df['intensity']
        self.intensity_stats[file_id] = {
            'min': intensities.min(),
            'max': intensities.max(),
            'mean': intensities.mean(),
            'median': intensities.median(),
            'std': intensities.std(),
            'dynamic_range': intensities.max() / (intensities.min() + 1e-10)
        }
        
        # 按类别累计
        if 'class_0' in file_class.lower() or file_class == self._get_class_0_name():
            self.class_0_files += 1
            self.class_0_total_peaks += peak_count
        else:
            self.class_1_files += 1
            self.class_1_total_peaks += peak_count
    
    def _get_class_0_name(self):
        """获取类别0名称（需要从外部设置）"""
        return getattr(self, '_class_0_name', 'class_0')
    
    def get_summary(self) -> Dict:
        """生成阶段1诊断摘要"""
        peak_counts = list(self.peaks_per_file.values())
        
        return {
            'file_success_rate': self.successful_files / self.total_files if self.total_files > 0 else 0,
            'failed_files': self.failed_files,
            'peaks_per_file': {
                'min': min(peak_counts) if peak_counts else 0,
                'max': max(peak_counts) if peak_counts else 0,
                'mean': np.mean(peak_counts) if peak_counts else 0,
                'median': np.median(peak_counts) if peak_counts else 0,
                'std': np.std(peak_counts) if peak_counts else 0,
            },
            'class_balance': {
                'class_0_files': self.class_0_files,
                'class_1_files': self.class_1_files,
                'class_0_avg_peaks': self.class_0_total_peaks / self.class_0_files if self.class_0_files > 0 else 0,
                'class_1_avg_peaks': self.class_1_total_peaks / self.class_1_files if self.class_1_files > 0 else 0,
            },
            # 识别异常文件
            'outlier_files': self._identify_outliers(peak_counts),
        }
    
    def _identify_outliers(self, peak_counts: List[int]) -> Dict:
        """识别峰数量异常的文件"""
        if not peak_counts or len(peak_counts) < 3:
            return {'low': [], 'high': []}
        
        q1, q3 = np.percentile(peak_counts, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        low_outliers = [f for f, c in self.peaks_per_file.items() if c < lower_bound]
        high_outliers = [f for f, c in self.peaks_per_file.items() if c > upper_bound]
        
        return {
            'low': low_outliers,
            'high': high_outliers,
            'bounds': (lower_bound, upper_bound)
        }


@dataclass 
class Phase2Diagnostics:
    """阶段2诊断：共识峰筛选"""
    total_mz_groups: int = 0
    
    # 筛选漏斗统计
    filter_funnel: Dict[str, int] = field(default_factory=lambda: {
        'initial_groups': 0,
        'passed_occurrence': 0,
        'passed_min_samples': 0,
        'passed_fold_change': 0,
        'final_consensus': 0,
    })
    
    # 被过滤掉的峰的详细原因
    rejection_reasons: Dict[str, List[Dict]] = field(default_factory=lambda: {
        'low_occurrence': [],      # 出现率不足
        'insufficient_samples': [], # 样本数不足
        'low_fold_change': [],     # 折叠变化不足
    })
    
    # 边界案例（差一点就通过的）
    near_miss_cases: List[Dict] = field(default_factory=list)
    
    # 参数敏感性分析
    parameter_impact: Dict = field(default_factory=dict)
    
    def record_group_analysis(self, mz_group: float, 
                               class_0_occurrence: float, class_1_occurrence: float,
                               class_0_samples: int, class_1_samples: int,
                               fold_change: float,
                               min_occurrence_rate: float,
                               min_fold_change: float,
                               passed: bool):
        """记录单个m/z组的分析结果"""
        self.total_mz_groups += 1
        self.filter_funnel['initial_groups'] += 1
        
        # 检查各阶段通过情况
        passed_occurrence = (class_0_occurrence >= min_occurrence_rate or 
                           class_1_occurrence >= min_occurrence_rate)
        passed_samples = (class_0_samples >= 2 or class_1_samples >= 2)
        passed_fc = fold_change >= min_fold_change
        
        group_info = {
            'mz_group': mz_group,
            'class_0_occurrence': class_0_occurrence,
            'class_1_occurrence': class_1_occurrence,
            'class_0_samples': class_0_samples,
            'class_1_samples': class_1_samples,
            'fold_change': fold_change,
        }
        
        if passed_occurrence:
            self.filter_funnel['passed_occurrence'] += 1
        else:
            self.rejection_reasons['low_occurrence'].append(group_info)
            # 检查是否接近阈值（差10%以内）
            max_occ = max(class_0_occurrence, class_1_occurrence)
            if max_occ >= min_occurrence_rate * 0.9:
                self.near_miss_cases.append({
                    **group_info, 
                    'reason': 'occurrence',
                    'gap': min_occurrence_rate - max_occ
                })
            return
        
        if passed_samples:
            self.filter_funnel['passed_min_samples'] += 1
        else:
            self.rejection_reasons['insufficient_samples'].append(group_info)
            return
        
        if passed_fc:
            self.filter_funnel['passed_fold_change'] += 1
            self.filter_funnel['final_consensus'] += 1
        else:
            self.rejection_reasons['low_fold_change'].append(group_info)
            # 检查是否接近阈值
            if fold_change >= min_fold_change * 0.9:
                self.near_miss_cases.append({
                    **group_info,
                    'reason': 'fold_change', 
                    'gap': min_fold_change - fold_change
                })
    
    def analyze_parameter_sensitivity(self, all_groups_data: List[Dict],
                                      current_occurrence: float,
                                      current_fold_change: float):
        """分析参数敏感性 - 如果调整参数会有多少峰通过"""
        
        test_occurrences = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        test_fold_changes = [1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
        
        sensitivity_matrix = {}
        
        for occ in test_occurrences:
            for fc in test_fold_changes:
                count = sum(1 for g in all_groups_data 
                           if (g['class_0_occurrence'] >= occ or g['class_1_occurrence'] >= occ)
                           and (g['class_0_samples'] >= 2 or g['class_1_samples'] >= 2)
                           and g['fold_change'] >= fc)
                sensitivity_matrix[(occ, fc)] = count
        
        self.parameter_impact = {
            'sensitivity_matrix': sensitivity_matrix,
            'current_params': (current_occurrence, current_fold_change),
            'current_result': sensitivity_matrix.get((current_occurrence, current_fold_change), 0),
            'recommendations': self._generate_param_recommendations(sensitivity_matrix, current_occurrence, current_fold_change)
        }
    
    def _generate_param_recommendations(self, matrix: Dict, curr_occ: float, curr_fc: float) -> List[str]:
        """基于敏感性分析生成参数调整建议"""
        recommendations = []
        current_count = matrix.get((curr_occ, curr_fc), 0)
        
        # 检查降低出现率阈值的效果
        if curr_occ > 0.2:
            lower_occ_count = matrix.get((curr_occ - 0.1, curr_fc), 0)
            if lower_occ_count > current_count * 1.2:
                recommendations.append(
                    f"降低出现率阈值到 {curr_occ - 0.1:.1f} 可增加约 "
                    f"{lower_occ_count - current_count} 个共识峰"
                )
        
        # 检查降低折叠变化阈值的效果
        if curr_fc > 1.2:
            lower_fc_count = matrix.get((curr_occ, curr_fc - 0.5), 0) if curr_fc > 1.5 else matrix.get((curr_occ, 1.2), 0)
            if lower_fc_count > current_count * 1.2:
                recommendations.append(
                    f"降低折叠变化阈值可增加约 {lower_fc_count - current_count} 个共识峰"
                )
        
        return recommendations
    
    def get_summary(self) -> Dict:
        """生成阶段2诊断摘要"""
        funnel = self.filter_funnel
        
        return {
            'filter_funnel': funnel,
            'conversion_rates': {
                'occurrence_pass_rate': funnel['passed_occurrence'] / funnel['initial_groups'] if funnel['initial_groups'] > 0 else 0,
                'samples_pass_rate': funnel['passed_min_samples'] / funnel['passed_occurrence'] if funnel['passed_occurrence'] > 0 else 0,
                'fold_change_pass_rate': funnel['passed_fold_change'] / funnel['passed_min_samples'] if funnel['passed_min_samples'] > 0 else 0,
                'overall_pass_rate': funnel['final_consensus'] / funnel['initial_groups'] if funnel['initial_groups'] > 0 else 0,
            },
            'rejection_summary': {
                reason: len(cases) for reason, cases in self.rejection_reasons.items()
            },
            'near_miss_count': len(self.near_miss_cases),
            'near_miss_by_reason': self._count_near_miss_by_reason(),
            'parameter_impact': self.parameter_impact,
            'bottleneck': self._identify_bottleneck(),
        }
    
    def _count_near_miss_by_reason(self) -> Dict[str, int]:
        """按原因统计接近通过的案例"""
        counts = {}
        for case in self.near_miss_cases:
            reason = case.get('reason', 'unknown')
            counts[reason] = counts.get(reason, 0) + 1
        return counts
    
    def _identify_bottleneck(self) -> str:
        """识别主要瓶颈"""
        rejection_counts = {
            reason: len(cases) for reason, cases in self.rejection_reasons.items()
        }
        
        if not rejection_counts:
            return "无明显瓶颈"
        
        max_reason = max(rejection_counts, key=rejection_counts.get)
        
        bottleneck_descriptions = {
            'low_occurrence': "出现率阈值过高 - 大量峰因出现频率不足被过滤",
            'insufficient_samples': "样本数要求过高 - 部分峰在单个类别中样本不足",
            'low_fold_change': "折叠变化阈值过高 - 峰的类别区分度不够",
        }
        
        return bottleneck_descriptions.get(max_reason, f"未知瓶颈: {max_reason}")


@dataclass
class ConsensusPeakDiagnostics:
    """完整诊断报告"""
    phase1: Phase1Diagnostics = field(default_factory=Phase1Diagnostics)
    phase2: Phase2Diagnostics = field(default_factory=Phase2Diagnostics)
    
    # 元数据
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    parameters: Dict = field(default_factory=dict)
    
    def set_parameters(self, min_occurrence_rate: float, min_fold_change: float,
                       mz_tolerance: float, max_features: int):
        """记录当前使用的参数"""
        self.parameters = {
            'min_occurrence_rate': min_occurrence_rate,
            'min_fold_change': min_fold_change,
            'mz_tolerance': mz_tolerance,
            'max_features': max_features,
        }
    
    def generate_report(self) -> str:
        """生成完整的诊断报告"""
        phase1_summary = self.phase1.get_summary()
        phase2_summary = self.phase2.get_summary()
        
        report_lines = [
            "=" * 70,
            "共识峰识别诊断报告",
            f"生成时间: {self.timestamp}",
            "=" * 70,
            "",
            "【当前参数设置】",
            f"  最小出现率阈值: {self.parameters.get('min_occurrence_rate', 'N/A')}",
            f"  最小折叠变化: {self.parameters.get('min_fold_change', 'N/A')}",
            f"  m/z容差: {self.parameters.get('mz_tolerance', 'N/A')}",
            f"  最大特征数: {self.parameters.get('max_features', 'N/A')}",
            "",
            "-" * 70,
            "【阶段1: 峰发现质量诊断】",
            "-" * 70,
            "",
            f"文件处理成功率: {phase1_summary['file_success_rate']:.1%}",
            f"失败文件: {phase1_summary['failed_files'] if phase1_summary['failed_files'] else '无'}",
            "",
            "每文件峰数量统计:",
            f"  最小: {phase1_summary['peaks_per_file']['min']:.0f}",
            f"  最大: {phase1_summary['peaks_per_file']['max']:.0f}",
            f"  平均: {phase1_summary['peaks_per_file']['mean']:.1f}",
            f"  中位数: {phase1_summary['peaks_per_file']['median']:.1f}",
            f"  标准差: {phase1_summary['peaks_per_file']['std']:.1f}",
            "",
            "类别平衡性:",
            f"  类别0: {phase1_summary['class_balance']['class_0_files']} 个文件, "
            f"平均 {phase1_summary['class_balance']['class_0_avg_peaks']:.1f} 峰/文件",
            f"  类别1: {phase1_summary['class_balance']['class_1_files']} 个文件, "
            f"平均 {phase1_summary['class_balance']['class_1_avg_peaks']:.1f} 峰/文件",
            "",
        ]
        
        # 异常文件
        outliers = phase1_summary['outlier_files']
        if outliers['low'] or outliers['high']:
            report_lines.append("⚠️ 异常文件检测:")
            if outliers['low']:
                report_lines.append(f"  峰数量过少: {', '.join(outliers['low'][:5])}")
                if len(outliers['low']) > 5:
                    report_lines.append(f"    ... 还有 {len(outliers['low']) - 5} 个")
            if outliers['high']:
                report_lines.append(f"  峰数量过多: {', '.join(outliers['high'][:5])}")
            report_lines.append("")
        
        # 阶段2诊断
        report_lines.extend([
            "-" * 70,
            "【阶段2: 共识峰筛选诊断】",
            "-" * 70,
            "",
            "筛选漏斗:",
        ])
        
        funnel = phase2_summary['filter_funnel']
        rates = phase2_summary['conversion_rates']
        
        report_lines.extend([
            f"  初始m/z组: {funnel['initial_groups']}",
            f"    ↓ 出现率筛选 → {funnel['passed_occurrence']} "
            f"(通过率: {rates['occurrence_pass_rate']:.1%})",
            f"    ↓ 样本数筛选 → {funnel['passed_min_samples']} "
            f"(通过率: {rates['samples_pass_rate']:.1%})",
            f"    ↓ 折叠变化筛选 → {funnel['passed_fold_change']} "
            f"(通过率: {rates['fold_change_pass_rate']:.1%})",
            f"  最终共识峰: {funnel['final_consensus']} "
            f"(总通过率: {rates['overall_pass_rate']:.1%})",
            "",
        ])
        
        # 拒绝原因分析
        rejection = phase2_summary['rejection_summary']
        report_lines.extend([
            "拒绝原因分布:",
            f"  出现率不足: {rejection.get('low_occurrence', 0)} 个",
            f"  样本数不足: {rejection.get('insufficient_samples', 0)} 个",
            f"  折叠变化不足: {rejection.get('low_fold_change', 0)} 个",
            "",
        ])
        
        # 边界案例
        near_miss = phase2_summary['near_miss_count']
        if near_miss > 0:
            report_lines.extend([
                f"⚠️ 接近通过的边界案例: {near_miss} 个",
                f"  按原因分布: {phase2_summary['near_miss_by_reason']}",
                "",
            ])
        
        # 瓶颈识别
        report_lines.extend([
            "🔍 主要瓶颈:",
            f"  {phase2_summary['bottleneck']}",
            "",
        ])
        
        # 参数建议
        if phase2_summary.get('parameter_impact', {}).get('recommendations'):
            report_lines.extend([
                "💡 参数调整建议:",
            ])
            for rec in phase2_summary['parameter_impact']['recommendations']:
                report_lines.append(f"  • {rec}")
            report_lines.append("")
        
        # 总结诊断
        report_lines.extend([
            "-" * 70,
            "【诊断总结】",
            "-" * 70,
            "",
        ])
        
        diagnosis = self._generate_diagnosis(phase1_summary, phase2_summary)
        report_lines.extend(diagnosis)
        
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)
    
    def _generate_diagnosis(self, phase1: Dict, phase2: Dict) -> List[str]:
        """生成诊断结论"""
        conclusions = []
        
        # 检查是否是数据质量问题
        data_quality_issues = []
        
        if phase1['file_success_rate'] < 0.9:
            data_quality_issues.append("• 文件处理失败率较高，检查数据格式")
        
        if phase1['peaks_per_file']['std'] > phase1['peaks_per_file']['mean'] * 0.5:
            data_quality_issues.append("• 各文件峰数量差异较大，可能存在数据质量不一致")
        
        if phase1['outlier_files']['low']:
            data_quality_issues.append(f"• 发现 {len(phase1['outlier_files']['low'])} 个峰数量异常偏少的文件")
        
        class_balance = phase1['class_balance']
        if class_balance['class_0_files'] > 0 and class_balance['class_1_files'] > 0:
            ratio = max(class_balance['class_0_files'], class_balance['class_1_files']) / \
                    min(class_balance['class_0_files'], class_balance['class_1_files'])
            if ratio > 2:
                data_quality_issues.append(f"• 类别样本不平衡 (比例 {ratio:.1f}:1)")
        
        # 检查是否是算法参数问题
        algorithm_issues = []
        
        rates = phase2['conversion_rates']
        if rates['occurrence_pass_rate'] < 0.3:
            algorithm_issues.append("• 出现率阈值可能设置过高 (建议降低 MIN_OCCURRENCE_RATE)")
        
        if rates['samples_pass_rate'] < 0.5 and rates['occurrence_pass_rate'] > 0.5:
            algorithm_issues.append("• 最小样本数要求导致大量过滤 (当前要求至少一个类别>=2)")
        
        if rates['fold_change_pass_rate'] < 0.3 and rates['samples_pass_rate'] > 0.5:
            algorithm_issues.append("• 折叠变化阈值可能设置过高 (建议降低 MIN_FOLD_CHANGE)")
        
        if phase2['near_miss_count'] > phase2['filter_funnel']['final_consensus'] * 0.5:
            algorithm_issues.append("• 大量峰接近通过阈值，微调参数可能显著改善结果")
        
        # 输出结论
        if data_quality_issues:
            conclusions.append("📊 数据质量问题:")
            conclusions.extend(data_quality_issues)
            conclusions.append("")
        else:
            conclusions.append("✅ 数据质量检查通过")
            conclusions.append("")
        
        if algorithm_issues:
            conclusions.append("⚙️ 算法参数问题:")
            conclusions.extend(algorithm_issues)
            conclusions.append("")
        else:
            conclusions.append("✅ 算法参数设置合理")
            conclusions.append("")
        
        # 总体建议
        if not data_quality_issues and not algorithm_issues:
            conclusions.append("💡 建议: 当前设置正常，如需更多共识峰可适当放宽参数")
        elif data_quality_issues and not algorithm_issues:
            conclusions.append("💡 建议: 优先解决数据质量问题，检查异常文件和数据预处理流程")
        elif algorithm_issues and not data_quality_issues:
            conclusions.append("💡 建议: 数据质量良好，可通过调整算法参数增加共识峰数量")
        else:
            conclusions.append("💡 建议: 同时存在数据和算法问题，建议先解决数据质量问题再调整参数")
        
        return conclusions
    
    def get_quick_stats(self) -> Dict:
        """获取快速统计摘要（用于日志输出）"""
        phase1 = self.phase1.get_summary()
        phase2 = self.phase2.get_summary()
        
        return {
            'total_files': self.phase1.total_files,
            'successful_files': self.phase1.successful_files,
            'total_peaks_discovered': sum(self.phase1.peaks_per_file.values()),
            'total_mz_groups': self.phase2.total_mz_groups,
            'consensus_peaks': phase2['filter_funnel']['final_consensus'],
            'bottleneck': phase2['bottleneck'],
            'overall_pass_rate': phase2['conversion_rates']['overall_pass_rate'],
        }


# 便捷函数
def create_diagnostics() -> ConsensusPeakDiagnostics:
    """创建诊断实例"""
    return ConsensusPeakDiagnostics()
