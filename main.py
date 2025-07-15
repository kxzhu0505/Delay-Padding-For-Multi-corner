#!/usr/bin/env python3
import os
import sys
from typing import Dict, List
from core.graph_builder import TimingGraphBuilder
from core.dual_decomposition import run_dual_delay_padding
from core.cp_optimize import find_min_TCLK


if __name__ == "__main__":
    project_root = "/home/wllpro/llwang07/kxzhu/DelayPadding"
        
    # 设置网表和Liberty文件路径
    import argparse
#netlist_path = os.path.join(project_root, "netlist", "/home/wllpro/llwang07/kxzhu/ssta/distribution/vlsi/ethmac/ethmac.v") 
    parser = argparse.ArgumentParser(description="DelayPadding 主程序")
    parser.add_argument('--verilog', type=str, required=True, help='Verilog 网表文件路径')
    args = parser.parse_args()

    netlist_path = args.verilog
    corners_config = {
        'ss_asap7': [
            "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_AO_RVT_SS_nldm_211120.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_INVBUF_RVT_SS_nldm_220122.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_OA_RVT_SS_nldm_211120.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SEQ_RVT_SS_nldm_220123.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SIMPLE_RVT_SS_nldm_211120.lib"
        ],
        'ff_asap7': [
            "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_AO_RVT_FF_nldm_211120.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_INVBUF_RVT_FF_nldm_220122.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_OA_RVT_FF_nldm_211120.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SEQ_RVT_FF_nldm_220123.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SIMPLE_RVT_FF_nldm_211120.lib"
        ]
    }
    # 根据输入的verilog文件名生成工作目录
    verilog_base = os.path.splitext(os.path.basename(netlist_path))[0]
    work_dir = os.path.join(project_root, f"{verilog_base}_dir")
    # 检查必要文件是否存在
    required_files = [netlist_path] 
    for libs in corners_config.values():
        required_files.extend(libs)
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"错误: 找不到必要的文件 {file_path}")
            print("请确保以下文件存在:")
            print(f"1. 网表文件: {netlist_path}")
            print(f"2. 慢角Liberty文件: {corners_config['ss_asap7']}")
            print(f"3. 快角Liberty文件: {corners_config['ff_asap7']}")
    builder = TimingGraphBuilder(netlist_path=netlist_path,
                corners_config=corners_config,
                work_dir=work_dir)
    builder.build_timing_graphs()
    corner_graphs = builder.graphs
    for corner in corners_config.keys():
        builder.print_graph_info(corner)
    print(corner_graphs)

    # run_dual_delay_padding(corner_graphs, T_CLK=600)
    TCLK_min, p_optimal, setup_padding, hold_padding, msg = find_min_TCLK(
        corner_graphs=corner_graphs,
        TCLK_min=0,
        TCLK_max=20000,
        tol=0.1
    )
    
    output_file_path = os.path.join(work_dir, f"{verilog_base}_results.txt")
    if TCLK_min is None:
        with open(output_file_path, "w") as f:
            f.write(f"未找到可行解: {msg}\n")
        print(f"未找到可行解: {msg}")
        print(f"详情请见: {output_file_path}")
        sys.exit(1)
    else:
        with open(output_file_path, "w") as f:
            f.write(f"最小可行时钟周期: {TCLK_min:.3f}ns\n")
            f.write(f"最优电势解: {p_optimal}\n")
            f.write(f"Setup padding解: {setup_padding}\n")
            f.write(f"Hold padding解: {hold_padding}\n")
            f.write(f"信息: {msg}\n")
        print(f"结果已保存到 {output_file_path}")