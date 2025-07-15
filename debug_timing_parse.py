#!/usr/bin/env python3
"""
调试脚本：检查timing报告解析过程中的None值
用于定位ibex benchmark中的数据问题
"""

import re
import os

def debug_timing_parsing(timing_file, max_samples=10):
    """
    调试timing报告解析，查找None值的来源
    
    Args:
        timing_file: timing报告文件路径
        max_samples: 最大样本数量
    """
    print(f"调试timing文件: {timing_file}")
    print("="*60)
    
    if not os.path.exists(timing_file):
        print(f"❌ 文件不存在: {timing_file}")
        return
    
    with open(timing_file, 'r') as f:
        timing_content = f.read()
    
    # 使用与graph_builder.py相同的正则表达式
    path_sections = re.finditer(
        r'Startpoint:\s+(\S+)\s+\((.*?)\).*?'               # group(1,2): Startpoint
        r'Endpoint:\s+(\S+)\s+\((.*?)\).*?'                 # group(3,4): Endpoint
        r'Path Group:.*?\n'
        r'Path Type:.*?\n'
        r'(.*?)^\s*[-\d\.]+\s+slack.*?$'                    # group(5): Path body until 'slack'
        ,
        timing_content,
        re.DOTALL | re.MULTILINE
    )
    
    path_count = 0
    none_arrival_count = 0
    none_setup_count = 0
    successful_parses = 0
    
    for match in path_sections:
        if path_count >= max_samples:
            break
            
        path_count += 1
        start_reg = match.group(1)
        end_reg = match.group(3)
        path_detail = match.group(5)
        
        # 解析arrival time和setup time
        arrival_time = None
        setup_time = None
        
        arrival_match = re.search(r'\n\s*([\d\.\-]+)\s+data arrival time', path_detail)
        setup_match = re.search(r'\n\s*([\d\.\-]+)\s+[\d\.\-]+\s+library setup time', path_detail)
        
        if arrival_match:
            arrival_time = float(arrival_match.group(1))
        else:
            none_arrival_count += 1
            
        if setup_match:
            setup_time = float(setup_match.group(1))
        else:
            none_setup_count += 1
        
        if arrival_time is not None and setup_time is not None:
            successful_parses += 1
        
        print(f"\n路径 {path_count}: {start_reg} -> {end_reg}")
        print(f"  Arrival Time: {arrival_time} {'✅' if arrival_time is not None else '❌'}")
        print(f"  Setup Time: {setup_time} {'✅' if setup_time is not None else '❌'}")
        
        # 如果有None值，显示原始path_detail的前几行进行调试
        if arrival_time is None or setup_time is None:
            print(f"  问题路径详情的前5行:")
            lines = path_detail.split('\n')[:5]
            for i, line in enumerate(lines):
                print(f"    {i+1}: '{line}'")
    
    print(f"\n{'='*60}")
    print(f"总结:")
    print(f"  总路径数: {path_count}")
    print(f"  成功解析: {successful_parses}")
    print(f"  Arrival Time为None: {none_arrival_count}")
    print(f"  Setup Time为None: {none_setup_count}")
    print(f"  解析成功率: {successful_parses/path_count*100:.1f}%" if path_count > 0 else "0%")
    
    if none_arrival_count > 0 or none_setup_count > 0:
        print(f"\n⚠️  发现数据缺失问题！这很可能是导致dual decomposition错误的原因。")
    else:
        print(f"\n✅ 解析完全正常，问题可能在其他地方。")

def debug_hold_timing_parsing(timing_file, max_samples=5):
    """
    调试hold timing报告解析
    """
    print(f"\n调试Hold timing文件: {timing_file}")
    print("="*60)
    
    if not os.path.exists(timing_file):
        print(f"❌ 文件不存在: {timing_file}")
        return
    
    with open(timing_file, 'r') as f:
        timing_content = f.read()
    
    # 解析hold timing路径
    path_sections = re.finditer(
        r'Startpoint:\s+(\S+)\s+\((.*?)\).*?'               # group(1,2): Startpoint
        r'Endpoint:\s+(\S+)\s+\((.*?)\).*?'                 # group(3,4): Endpoint
        r'Path Group:.*?\n'
        r'Path Type:.*?\n'
        r'(.*?)^\s*[-\d\.]+\s+slack.*?$'                    # group(5): Path body until 'slack'
        ,
        timing_content,
        re.DOTALL | re.MULTILINE
    )
    
    path_count = 0
    none_arrival_count = 0
    none_hold_count = 0
    successful_parses = 0
    
    for match in path_sections:
        if path_count >= max_samples:
            break
            
        path_count += 1
        start_reg = match.group(1)
        end_reg = match.group(3)
        path_detail = match.group(5)
        
        # 解析arrival time和hold time
        arrival_time = None
        hold_time = None
        
        arrival_match = re.search(r'\n\s*([\d\.\-]+)\s+data arrival time', path_detail)
        hold_match = re.search(r'\n\s*([\d\.\-]+)\s+[\d\.\-]+\s+library hold time', path_detail)
        
        if arrival_match:
            arrival_time = float(arrival_match.group(1))
        else:
            none_arrival_count += 1
            
        if hold_match:
            hold_time = float(hold_match.group(1))
        else:
            none_hold_count += 1
        
        if arrival_time is not None and hold_time is not None:
            successful_parses += 1
        
        print(f"\nHold路径 {path_count}: {start_reg} -> {end_reg}")
        print(f"  Arrival Time: {arrival_time} {'✅' if arrival_time is not None else '❌'}")
        print(f"  Hold Time: {hold_time} {'✅' if hold_time is not None else '❌'}")
    
    print(f"\n{'='*40}")
    print(f"Hold timing总结:")
    print(f"  Hold路径数: {path_count}")
    print(f"  成功解析: {successful_parses}")
    print(f"  Arrival Time为None: {none_arrival_count}")
    print(f"  Hold Time为None: {none_hold_count}")

if __name__ == "__main__":
    # 调试ibex的timing文件
    ibex_dir = "/home/wllpro/llwang07/kxzhu/DelayPadding/ibex_dir"
    
    print("🔍 调试ibex benchmark的timing解析问题")
    print("="*60)
    
    # 调试setup timing
    max_timing_file = f"{ibex_dir}/timing_ss_asap7_max.rpt"
    debug_timing_parsing(max_timing_file, max_samples=10)
    
    # 调试hold timing
    min_timing_file = f"{ibex_dir}/timing_ss_asap7_min.rpt"
    debug_hold_timing_parsing(min_timing_file, max_samples=5)
    
    print(f"\n🎯 调试建议:")
    print(f"1. 如果发现大量None值，说明正则表达式需要调整")
    print(f"2. 如果解析正常，问题可能在dual_decomposition.py的其他地方")
    print(f"3. 可以比较gcd和ibex的差异来找出具体原因") 