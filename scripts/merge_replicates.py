"""
质谱技术重复数据合并脚本
将同一样本的两次检测（A和B）取平均

使用方法：
把脚本放到任意位置，然后在命令行运行：
bashpython merge_replicates.py "你的数据文件夹路径"


文件命名规则：
- B1-A_paired.txt, B1-B_paired.txt -> B1_merged.txt
- B2-A_paired.txt, B2-B_paired.txt -> B2_merged.txt
...

数据格式（制表符分隔）：
m/z值    强度值
500.011422155	115.0
500.016497786	120.0
...
"""

import os
import numpy as np
from pathlib import Path
import argparse


def read_spectrum_file(filepath):
    """读取质谱数据文件，返回 m/z 和 intensity 数组"""
    mz_values = []
    intensities = []
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                mz_values.append(float(parts[0]))
                intensities.append(float(parts[1]))
    
    return np.array(mz_values), np.array(intensities)


def write_spectrum_file(filepath, mz_values, intensities):
    """写入合并后的质谱数据"""
    with open(filepath, 'w') as f:
        for mz, intensity in zip(mz_values, intensities):
            f.write(f"{mz}\t{intensity}\n")


def find_sample_pairs(input_dir):
    """
    查找配对的文件
    返回: {sample_id: {'A': filepath_A, 'B': filepath_B}, ...}
    """
    pairs = {}
    
    for filename in os.listdir(input_dir):
        if not filename.endswith('_paired.txt'):
            continue
        
        # 解析文件名: B1-A_paired.txt -> sample_id=B1, replicate=A
        base = filename.replace('_paired.txt', '')
        if '-' in base:
            parts = base.rsplit('-', 1)
            sample_id = parts[0]
            replicate = parts[1]  # A 或 B
            
            if sample_id not in pairs:
                pairs[sample_id] = {}
            pairs[sample_id][replicate] = os.path.join(input_dir, filename)
    
    return pairs


def merge_replicates(mz_a, intensity_a, mz_b, intensity_b, mz_tolerance=0.01):
    """
    合并两次检测的数据
    
    策略：
    1. 如果两次检测的 m/z 点完全一致，直接取平均
    2. 如果有微小差异，在容差范围内匹配后取平均
    """
    # 检查 m/z 是否完全一致
    if len(mz_a) == len(mz_b) and np.allclose(mz_a, mz_b, rtol=1e-9):
        # 完全一致，直接取平均
        merged_mz = mz_a
        merged_intensity = (intensity_a + intensity_b) / 2
        return merged_mz, merged_intensity
    
    # m/z 点不完全一致，需要对齐
    print("  注意: 两次检测的 m/z 点不完全一致，进行对齐合并...")
    
    # 使用 A 的 m/z 作为参考，找 B 中对应的点
    merged_mz = []
    merged_intensity = []
    
    for i, mz in enumerate(mz_a):
        # 在 B 中找最近的点
        idx = np.argmin(np.abs(mz_b - mz))
        if np.abs(mz_b[idx] - mz) <= mz_tolerance:
            # 找到匹配点，取平均
            merged_mz.append((mz + mz_b[idx]) / 2)
            merged_intensity.append((intensity_a[i] + intensity_b[idx]) / 2)
        else:
            # 未找到匹配，只保留 A 的数据
            merged_mz.append(mz)
            merged_intensity.append(intensity_a[i])
    
    return np.array(merged_mz), np.array(merged_intensity)


def calculate_cv(intensity_a, intensity_b):
    """计算两次检测之间的变异系数（CV）"""
    mean_intensity = (intensity_a + intensity_b) / 2
    std_intensity = np.abs(intensity_a - intensity_b) / np.sqrt(2)
    
    # 避免除零，只计算非零位置
    mask = mean_intensity > 0
    if np.sum(mask) == 0:
        return 0
    
    cv_values = std_intensity[mask] / mean_intensity[mask] * 100
    return np.median(cv_values)


def main():
    parser = argparse.ArgumentParser(description='合并质谱技术重复数据')
    parser.add_argument('input_dir', help='输入文件夹路径')
    parser.add_argument('-o', '--output_dir', help='输出文件夹路径（默认在输入文件夹下创建 merged 子文件夹）')
    parser.add_argument('--suffix', default='_merged', help='输出文件后缀（默认: _merged）')
    
    args = parser.parse_args()
    
    input_dir = args.input_dir
    output_dir = args.output_dir or os.path.join(input_dir, 'merged')
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找配对文件
    pairs = find_sample_pairs(input_dir)
    
    if not pairs:
        print("未找到配对的文件！")
        print("请确保文件命名格式为: SampleID-A_paired.txt 和 SampleID-B_paired.txt")
        return
    
    print(f"找到 {len(pairs)} 个样本的配对数据")
    print("-" * 50)
    
    # 处理每对文件
    successful = 0
    for sample_id in sorted(pairs.keys()):
        pair = pairs[sample_id]
        
        if 'A' not in pair or 'B' not in pair:
            print(f"[跳过] {sample_id}: 缺少配对文件")
            continue
        
        print(f"处理: {sample_id}")
        
        # 读取两个文件
        mz_a, intensity_a = read_spectrum_file(pair['A'])
        mz_b, intensity_b = read_spectrum_file(pair['B'])
        
        print(f"  A: {len(mz_a)} 个数据点, 强度范围 [{intensity_a.min():.1f}, {intensity_a.max():.1f}]")
        print(f"  B: {len(mz_b)} 个数据点, 强度范围 [{intensity_b.min():.1f}, {intensity_b.max():.1f}]")
        
        # 计算 CV
        if len(mz_a) == len(mz_b):
            cv = calculate_cv(intensity_a, intensity_b)
            print(f"  技术重复 CV: {cv:.1f}%")
        
        # 合并数据
        merged_mz, merged_intensity = merge_replicates(mz_a, intensity_a, mz_b, intensity_b)
        
        # 写入输出文件
        output_filename = f"{sample_id}{args.suffix}.txt"
        output_path = os.path.join(output_dir, output_filename)
        write_spectrum_file(output_path, merged_mz, merged_intensity)
        
        print(f"  输出: {output_filename} ({len(merged_mz)} 个数据点)")
        successful += 1
    
    print("-" * 50)
    print(f"完成！成功合并 {successful} 个样本")
    print(f"输出目录: {output_dir}")


if __name__ == '__main__':
    main()
