#!/usr/bin/env python3
import os
import sys
from typing import Dict, List
from core.graph_builder import TimingGraphBuilder
from core.dual_decomposition import run_dual_delay_padding
from core.cp_optimize import find_min_TCLK


if __name__ == "__main__":
    project_root = "/home/wllpro/llwang07/kxzhu/DelayPaddingPVT"
        
    # 设置网表和Liberty文件路径
    netlist_path = os.path.join(project_root, "netlist", "/home/wllpro/llwang07/kxzhu/ssta/distribution/vlsi/gcd/gcd.v")  
    corners_config = {
        'ss_asap7': [
            "/home/wllpro/llwang07/kxzhu/DelayPaddingPVT/platform/asap7sc7p5t_AO_RVT_SS_nldm_211120.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPaddingPVT/platform/asap7sc7p5t_INVBUF_RVT_SS_nldm_220122.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPaddingPVT/platform/asap7sc7p5t_OA_RVT_SS_nldm_211120.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPaddingPVT/platform/asap7sc7p5t_SEQ_RVT_SS_nldm_220123.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPaddingPVT/platform/asap7sc7p5t_SIMPLE_RVT_SS_nldm_211120.lib"
        ],
        'ff_asap7': [
            "/home/wllpro/llwang07/kxzhu/DelayPaddingPVT/platform/asap7sc7p5t_AO_RVT_FF_nldm_211120.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPaddingPVT/platform/asap7sc7p5t_INVBUF_RVT_FF_nldm_220122.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPaddingPVT/platform/asap7sc7p5t_OA_RVT_FF_nldm_211120.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPaddingPVT/platform/asap7sc7p5t_SEQ_RVT_FF_nldm_220123.lib",
            "/home/wllpro/llwang07/kxzhu/DelayPaddingPVT/platform/asap7sc7p5t_SIMPLE_RVT_FF_nldm_211120.lib"
        ]
    }
    work_dir = "/home/wllpro/llwang07/kxzhu/DelayPaddingPVT/gcd_dir"
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
    builder.run_timing_graphs_info()
    # builder.build_timing_graphs()
    corner_graphs = builder.graphs
    print("\n打印图信息...")
    for corner in corners_config.keys():
        builder.print_graph_info(corner)
    eta = 0.95
    TCLK_min, p_optimal, setup_padding, hold_padding, msg = find_min_TCLK(
        corner_graphs=corner_graphs,
        TCLK_min=0,
        TCLK_max=1000,
        eta=eta,
        tol=0.1
    )
    if TCLK_min is None:
        print(f"未找到可行解: {msg}")
        sys.exit(1)
    else:
        print(f"在{eta*100}%的工艺波动下，最小可行时钟周期: {TCLK_min:.3f}ns")
        print(f"最优电势解: {p_optimal}")
        print(f"Setup padding解: {setup_padding}")
        print(f"Hold padding解: {hold_padding}")
        print(f"信息: {msg}")
    
    
    #     print(f"最小可行时钟周期: {TCLK_min:.3f}ns")
    #     print(f"最优电势解: {p_optimal}")
    #     print(f"Setup padding解: {setup_padding}")
    #     print(f"Hold padding解: {hold_padding}")
    #     print(f"信息: {msg}")