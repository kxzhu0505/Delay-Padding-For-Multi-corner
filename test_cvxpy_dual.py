#!/usr/bin/env python3
"""
测试新的CVXPY双分解实现
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

import networkx as nx
from dual_decomposition import DualDecompositionSolver

def create_simple_test_graph():
    """创建简单的测试图"""
    # 创建两个工艺角的测试图
    corner_graphs = {}
    
    for corner in ['ff', 'ss']:
        G = nx.DiGraph()
        
        # 添加原始节点
        G.add_node('reg1', type='register')
        G.add_node('reg2', type='register')
        G.add_node('reg3', type='register')
        
        # 添加插入节点
        G.add_node('us_1_2', type='inserted_setup', original_edge=('reg1', 'reg2'))
        G.add_node('uh_1_2', type='inserted_hold', original_edge=('reg1', 'reg2'))
        G.add_node('us_2_3', type='inserted_setup', original_edge=('reg2', 'reg3'))
        G.add_node('uh_2_3', type='inserted_hold', original_edge=('reg2', 'reg3'))
        
        # 根据工艺角设置不同的timing参数
        if corner == 'ff':
            setup_delay_12 = 0.1
            hold_delay_12 = 0.05
            setup_delay_23 = 0.12
            hold_delay_23 = 0.04
        else:  # ss corner
            setup_delay_12 = 0.15
            hold_delay_12 = 0.08
            setup_delay_23 = 0.18
            hold_delay_23 = 0.06
        
        # 添加timing constraint边
        # Setup path: reg1 -> us_1_2 -> reg2
        G.add_edge('reg1', 'us_1_2', 
                  setup_delay={'arrival_time': 1.0, 'library_time': setup_delay_12},
                  path_detail='original_path')
        G.add_edge('us_1_2', 'reg2',
                  setup_delay={'arrival_time': 0, 'library_time': 0},
                  path_detail='setup_path')
        
        # Hold path: reg1 -> uh_1_2 -> reg2 (reversed for hold)
        G.add_edge('reg1', 'uh_1_2',
                  hold_delay={'arrival_time': 1.0, 'library_time': hold_delay_12},
                  path_detail='original_path')
        G.add_edge('uh_1_2', 'reg2',
                  hold_delay={'arrival_time': 0, 'library_time': 0},
                  path_detail='hold_path')
        
        # Setup path: reg2 -> us_2_3 -> reg3
        G.add_edge('reg2', 'us_2_3',
                  setup_delay={'arrival_time': 1.0, 'library_time': setup_delay_23},
                  path_detail='original_path')
        G.add_edge('us_2_3', 'reg3',
                  setup_delay={'arrival_time': 0, 'library_time': 0},
                  path_detail='setup_path')
        
        # Hold path: reg2 -> uh_2_3 -> reg3
        G.add_edge('reg2', 'uh_2_3',
                  hold_delay={'arrival_time': 1.0, 'library_time': hold_delay_23},
                  path_detail='original_path')
        G.add_edge('uh_2_3', 'reg3',
                  hold_delay={'arrival_time': 0, 'library_time': 0},
                  path_detail='hold_path')
        
        corner_graphs[corner] = G
    
    return corner_graphs

def test_networkx_dual_decomposition():
    """测试NetworkX双分解求解器"""
    print("=== 测试NetworkX双分解求解器 ===")
    
    # 创建测试图
    corner_graphs = create_simple_test_graph()
    T_clk = 2.0  # 2ns时钟周期
    
    print(f"创建了 {len(corner_graphs)} 个工艺角的测试图")
    for corner, graph in corner_graphs.items():
        print(f"  {corner}: {graph.number_of_nodes()} 节点, {graph.number_of_edges()} 边")
    
    # 创建求解器
    solver = DualDecompositionSolver(corner_graphs, T_clk)
    
    print(f"\n初始化求解器:")
    print(f"  总节点数: {len(solver.all_nodes)}")
    print(f"  原始节点数: {len(solver.original_nodes)}")
    print(f"  插入节点数: {len(solver.inserted_nodes)}")
    print(f"  工艺角: {solver.corners}")
    
    # 测试单个corner的子问题求解
    print(f"\n=== 测试单个corner子问题求解 ===")
    for corner in solver.corners:
        print(f"\n测试corner: {corner}")
        feasible, potentials = solver.solve_clock_skew_scheduling(corner)
        
        if feasible:
            print(f"  求解成功!")
            print(f"  节点电势样本:")
            for i, (node, potential) in enumerate(potentials.items()):
                if i < 5:  # 只显示前5个
                    print(f"    {node}: {potential:.6f}")
            print(f"  ...")
        else:
            print(f"  求解失败!")
    
    # 运行完整的双分解算法
    print(f"\n=== 运行完整双分解算法 ===")
    result = solver.solve(max_iterations=100, tolerance=1e-3)
    
    print(f"\n求解结果:")
    print(f"  收敛: {result['converged']}")
    print(f"  迭代次数: {result['iterations']}")
    print(f"  对偶目标值: {result['dual_objective']:.6f}")
    print(f"  所有corner可行: {result['all_feasible']}")
    
    if result['delay_padding_solution']:
        print(f"  延迟填充方案:")
        for edge, padding in result['delay_padding_solution'].items():
            print(f"    {edge}: {padding:.6f}")
    else:
        print(f"  无延迟填充方案")
    
    # 显示共享电势
    shared_potentials = result['shared_potentials']
    print(f"\n共享电势:")
    for node, potential in shared_potentials.items():
        print(f"  {node}: {potential:.6f}")

if __name__ == "__main__":
    try:
        test_networkx_dual_decomposition()
    except Exception as e:
        print(f"测试出错: {str(e)}")
        import traceback
        traceback.print_exc() 