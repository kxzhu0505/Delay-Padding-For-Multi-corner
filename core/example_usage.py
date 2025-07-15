#!/usr/bin/env python3
"""
使用示例：多工艺角负环检测和最小可行时钟周期分析

这个脚本展示了如何使用TimingGraphBuilder和NegativeCycleDetector
来分析timing constraint graph中的负环并计算最小可行时钟周期。
"""

import os
import sys
from graph_builder import create_timing_graphs
from negative_cycle_detector import analyze_timing_graphs

def main():
    """主函数 - 展示完整的分析流程"""
    print("="*80)
    print("多工艺角负环检测和最小可行时钟周期分析示例")
    print("="*80)
    
    # 1. 配置文件路径
    project_root = "/home/wllpro/llwang07/kxzhu/DelayPadding"
    netlist_path = "/home/wllpro/llwang07/kxzhu/ssta/distribution/vlsi/gcd/gcd.v"
    
    # 配置多工艺角Liberty文件
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
    
    work_dir = "/home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir"
    
    # 2. 构建原始timing graphs
    print("\n步骤1: 构建原始timing graphs...")
    builder = create_timing_graphs(
        netlist_path=netlist_path,
        corners_config=corners_config,
        work_dir=work_dir
    )
    
    if not builder.graphs:
        print("❌ 构建timing graphs失败")
        return False
    
    print(f"✅ 成功构建了 {len(builder.graphs)} 个工艺角的timing graphs")
    
    # 3. 修改timing constraint graph
    print("\n步骤2: 修改timing constraint graph...")
    modified_graphs = {}
    for corner in corners_config.keys():
        print(f"  修改 {corner} 工艺角的图...")
        modified_graph = builder.modify_timing_constraint_graph(corner)
        if modified_graph is not None:
            modified_graphs[corner] = modified_graph
            print(f"    ✅ 成功修改，节点数: {len(modified_graph.nodes())}, 边数: {len(modified_graph.edges())}")
        else:
            print(f"    ❌ 修改失败")
    
    if not modified_graphs:
        print("❌ 所有工艺角的图修改都失败")
        return False
    
    # 4. 进行负环检测和最小可行时钟周期分析
    print("\n步骤3: 负环检测和最小可行时钟周期分析...")
    
    # 方法1：使用集成的分析函数
    print("\n方法1: 使用TimingGraphBuilder集成的分析功能")
    detector = builder.analyze_negative_cycles_and_min_period(
        T_clk_min=1.0,
        T_clk_max=20.0,
        precision=0.1
    )
    
    # 方法2：直接使用NegativeCycleDetector
    print("\n方法2: 直接使用NegativeCycleDetector")
    detector2 = analyze_timing_graphs(
        corner_graphs=modified_graphs,
        T_clk_min=1.0,
        T_clk_max=20.0,
        precision=0.1,
        output_dir=work_dir
    )
    
    # 5. 检查特定时钟周期下的可行性
    print("\n步骤4: 检查特定时钟周期下的可行性...")
    test_periods = [5.0, 10.0, 15.0]
    
    for T_clk in test_periods:
        print(f"\n检查 T_clk = {T_clk:.1f} 的可行性:")
        results = builder.check_feasibility_at_period(T_clk)
        
        if results:
            for corner, result in results.items():
                status = "✅ 可行" if result['feasible'] else "❌ 不可行"
                print(f"  {corner}: {status}")
                
                if result['setup_negative_cycle']:
                    print(f"    Setup负环: {' -> '.join(result['setup_cycle_path'])}")
                if result['hold_negative_cycle']:
                    print(f"    Hold负环: {' -> '.join(result['hold_cycle_path'])}")
    
    # 6. 总结
    print(f"\n{'='*60}")
    print("分析完成！")
    print(f"{'='*60}")
    print(f"✅ 原始timing graphs构建完成")
    print(f"✅ timing constraint graph修改完成")
    print(f"✅ 负环检测和最小可行时钟周期分析完成")
    print(f"✅ 结果文件已保存到: {work_dir}")
    
    return True

def analyze_existing_graphs(corner_graphs, output_dir=None):
    """
    分析已有的timing constraint graphs
    
    Args:
        corner_graphs: 多工艺角的timing constraint graph字典
        output_dir: 输出目录
    """
    print("\n分析已有的timing constraint graphs...")
    
    detector = analyze_timing_graphs(
        corner_graphs=corner_graphs,
        T_clk_min=0.5,
        T_clk_max=50.0,
        precision=0.01,
        output_dir=output_dir
    )
    
    return detector

def quick_feasibility_check(corner_graphs, T_clk_list):
    """
    快速可行性检查
    
    Args:
        corner_graphs: 多工艺角的timing constraint graph字典
        T_clk_list: 要检查的时钟周期列表
    """
    from negative_cycle_detector import NegativeCycleDetector
    
    detector = NegativeCycleDetector(corner_graphs)
    
    print(f"\n快速可行性检查 (检查 {len(T_clk_list)} 个时钟周期)...")
    
    for T_clk in T_clk_list:
        print(f"\nT_clk = {T_clk:.2f}:")
        results = detector.analyze_negative_cycles_at_period(T_clk)
        
        feasible_corners = [corner for corner, result in results.items() if result['feasible']]
        infeasible_corners = [corner for corner, result in results.items() if not result['feasible']]
        
        print(f"  可行工艺角: {feasible_corners}")
        if infeasible_corners:
            print(f"  不可行工艺角: {infeasible_corners}")

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 示例运行成功！")
        else:
            print("\n❌ 示例运行失败！")
    except Exception as e:
        print(f"\n❌ 运行出错: {str(e)}")
        import traceback
        traceback.print_exc() 