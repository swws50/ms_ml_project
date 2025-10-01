import re
import os
from pathlib import Path

def parse_file(input_file):
    """解析单个文件"""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取m/z数组
    mz_match = re.search(r'cvParam: m/z array.*?binary: \[\d+\]\s+([\d\.\s]+)', content, re.DOTALL)
    mz_values = [float(x) for x in mz_match.group(1).split() if '.' in x]
    
    # 提取intensity数组
    int_match = re.search(r'cvParam: intensity array.*?binary: \[\d+\]\s+([\d\s]+)', content, re.DOTALL)
    int_values = [float(x) for x in int_match.group(1).split() if x.isdigit()]
    
    # 配对输出
    output_file = input_file.replace('.txt', '_paired.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        for mz, intensity in zip(mz_values, int_values):
            f.write(f"{mz}\t{intensity}\n")
    
    print(f"✓ 已处理: {input_file} -> {output_file} ({len(mz_values)} 个数据点)")

# 主程序
print("=" * 50)
print("MALDI质谱数据解析工具")
print("=" * 50)

# 获取当前目录下所有.txt文件
txt_files = list(Path('.').glob('*.txt'))

if not txt_files:
    print("\n未找到.txt文件！")
    print("请将数据文件放在脚本同一目录下")
else:
    print(f"\n找到 {len(txt_files)} 个文件:\n")
    for i, f in enumerate(txt_files, 1):
        print(f"{i}. {f.name}")
    
    print("\n开始处理...\n")
    
    for txt_file in txt_files:
        try:
            parse_file(str(txt_file))
        except Exception as e:
            print(f"✗ 处理失败: {txt_file.name} - {e}")

print("\n" + "=" * 50)
print("处理完成！")
print("=" * 50)
input("\n按回车键退出...")