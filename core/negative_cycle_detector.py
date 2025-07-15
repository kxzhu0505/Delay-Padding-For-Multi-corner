import networkx as nx
from collections import defaultdict
import sys
import os
from typing import Dict, List, Tuple, Optional

class NegativeCycleDetector:
    def __init__(self, corner_graphs):
        """
        初始化负环检测器
        
        Args:
            corner_graphs (dict): 多工艺角的timing constraint graph，格式为 {corner_name: nx.DiGraph}
        """
        self.corner_graphs = corner_graphs
        self.corners = list(corner_graphs.keys())
        
    def bellman_ford_detect_negative_cycle(self, adj):
        """
        Bellman-Ford负环检测算法
        
        Args:
            adj: 邻接表表示的图，格式为 {u: [(v, weight)]}
            
        Returns:
            (bool, list): 是否存在负环及负环路径
        """
        # 收集所有节点（包括源节点和目标节点）
        nodes = set()
        for u in adj:
            nodes.add(u)
            for v, _ in adj[u]:
                nodes.add(v)
                
        if not nodes:
            return False, []
            
        # 初始化所有节点的距离和前驱节点
        dist = {node: 0 for node in nodes}
        predecessor = {node: None for node in nodes}
        
        # Relax所有边 V-1 次
        for _ in range(len(nodes) - 1):
            for u in adj:
                for v, w in adj[u]:
                    if dist[v] > dist[u] + w:
                        dist[v] = dist[u] + w
                        predecessor[v] = u
        
        # 检测负环
        for u in adj:
            for v, w in adj[u]:
                if dist[v] > dist[u] + w:
                    # 回溯环路
                    cycle = []
                    current = v
                    visited = set()
                    
                    while current not in visited:
                        visited.add(current)
                        cycle.append(current)
                        current = predecessor.get(current)
                        if current is None:  # 如果找不到前驱节点
                            break
                        
                    if current is not None:  # 找到了一个环
                        # 找到环的起始位置
                        start_idx = cycle.index(current)
                        cycle = cycle[start_idx:]
                        cycle.append(current)  # 补充完整的环
                        return True, cycle
                        
        return False, []
    
    def detect_setup_negative_cycles(self, corner, T_clk):
        """
        检测setup时序约束的负环
        
        Args:
            corner: 工艺角名称
            T_clk: 时钟周期
            
        Returns:
            (bool, list): 是否存在setup负环及负环路径
        """
        if corner not in self.corner_graphs:
            return False, []
            
        G = self.corner_graphs[corner]
        
        # 构建setup约束图的邻接表
        setup_adj = defaultdict(list)
        
        for u, v, data in G.edges(data=True):
            setup_data = data.get("setup_delay", {})
            if setup_data:
                path_detail = data.get("path_detail", "")
                
                # 检查是否是新添加的节点之间的边（权重应为0）
                if path_detail in ['setup_path', 'hold_path', 'common_path', 'setup_to_hold_constraint']:
                    # 新添加的节点之间的边，权重为0
                    weight = 0.0
                else:
                    # 原始约束边或约束边，使用正常的权重计算
                    arrival = setup_data.get("arrival_time", 0)
                    T_setup = setup_data.get("library_time", 0)

                    if arrival is None:
                        arrival = 0.0
                    if T_setup is None:
                        T_setup = 0.0
                    # setup约束：T_clk + T_setup - arrival >= p[v] - p[u]
                    # 转换为：p[v] - p[u] <= T_clk + T_setup - arrival
                    # 图权重为：T_clk + T_setup - arrival
                    weight = T_clk + T_setup - arrival
                
                setup_adj[u].append((v, weight))
        
        return self.bellman_ford_detect_negative_cycle(setup_adj)
    
    def detect_hold_negative_cycles(self, corner):
        """
        检测hold时序约束的负环
        
        Args:
            corner: 工艺角名称
            
        Returns:
            (bool, list): 是否存在hold负环及负环路径
        """
        if corner not in self.corner_graphs:
            return False, []
            
        G = self.corner_graphs[corner]
        
        # 构建hold约束图的邻接表
        hold_adj = defaultdict(list)
        
        for u, v, data in G.edges(data=True):
            hold_data = data.get("hold_delay", {})
            if hold_data:
                path_detail = data.get("path_detail", "")
                
                # 检查是否是新添加的节点之间的边（权重应为0）
                if path_detail in ['setup_path', 'hold_path', 'common_path', 'setup_to_hold_constraint']:
                    # 新添加的节点之间的边，权重为0
                    # 对于hold约束，保持边的原始方向，但权重为0
                    weight = 0.0
                    hold_adj[u].append((v, weight))
                else:
                    # 原始约束边或约束边，使用正常的权重计算
                    arrival = hold_data.get("arrival_time", 0)
                    T_hold = hold_data.get("library_time", 0)
                    if arrival is None:
                        arrival = 0.0
                    if T_hold is None:
                        T_hold = 0.0
                    # hold约束：p[v] - p[u] >= T_hold - arrival
                    # 转换为：p[u] - p[v] <= arrival - T_hold
                    # 图权重为：arrival - T_hold (注意方向相反)
                    weight = arrival - T_hold
                    hold_adj[v].append((u, weight))
        
        return self.bellman_ford_detect_negative_cycle(hold_adj)
    
    def find_minimum_feasible_clock_period(self, T_clk_min=0.1, T_clk_max=100.0, precision=0.01):
        """
        二分查找最小可行时钟周期
        
        Args:
            T_clk_min: 最小时钟周期搜索范围
            T_clk_max: 最大时钟周期搜索范围
            precision: 精度要求
            
        Returns:
            (float, dict): 最小可行时钟周期和详细分析结果
        """
        print(f"\n开始搜索最小可行时钟周期...")
        print(f"搜索范围: [{T_clk_min:.3f}, {T_clk_max:.3f}], 精度: {precision}")
        
        analysis_results = {}
        
        def is_feasible(T_clk):
            """检查给定时钟周期是否可行"""
            feasible = True
            corner_results = {}
            
            for corner in self.corners:
                # 检查setup负环
                has_setup_cycle, setup_cycle = self.detect_setup_negative_cycles(corner, T_clk)
                
                # 检查hold负环
                has_hold_cycle, hold_cycle = self.detect_hold_negative_cycles(corner)
                
                corner_results[corner] = {
                    'setup_negative_cycle': has_setup_cycle,
                    'setup_cycle_path': setup_cycle if has_setup_cycle else None,
                    'hold_negative_cycle': has_hold_cycle,
                    'hold_cycle_path': hold_cycle if has_hold_cycle else None,
                    'feasible': not (has_setup_cycle or has_hold_cycle)
                }
                
                if has_setup_cycle or has_hold_cycle:
                    feasible = False
            
            return feasible, corner_results
        
        # 二分查找
        left, right = T_clk_min, T_clk_max
        best_feasible_period = None
        
        while right - left > precision:
            mid = (left + right) / 2
            feasible, corner_results = is_feasible(mid)
            
            print(f"测试 T_clk = {mid:.3f}: {'可行' if feasible else '不可行'}")
            
            if feasible:
                best_feasible_period = mid
                analysis_results[mid] = corner_results
                right = mid
            else:
                analysis_results[mid] = corner_results
                left = mid
        
        return best_feasible_period, analysis_results
    
    def analyze_negative_cycles_at_period(self, T_clk):
        """
        分析给定时钟周期下的负环情况
        
        Args:
            T_clk: 时钟周期
            
        Returns:
            dict: 分析结果
        """
        results = {}
        
        for corner in self.corners:
            print(f"\n分析工艺角 {corner} (T_clk = {T_clk:.3f}):")
            
            # 检查setup负环
            has_setup_cycle, setup_cycle = self.detect_setup_negative_cycles(corner, T_clk)
            
            # 检查hold负环
            has_hold_cycle, hold_cycle = self.detect_hold_negative_cycles(corner)
            
            results[corner] = {
                'setup_negative_cycle': has_setup_cycle,
                'setup_cycle_path': setup_cycle,
                'hold_negative_cycle': has_hold_cycle,
                'hold_cycle_path': hold_cycle,
                'feasible': not (has_setup_cycle or has_hold_cycle)
            }
            
            # 打印结果
            if has_setup_cycle:
                print(f"  ❌ 存在setup负环: {' -> '.join(setup_cycle)}")
            else:
                print(f"  ✅ 无setup负环")
                
            if has_hold_cycle:
                print(f"  ❌ 存在hold负环: {' -> '.join(hold_cycle)}")
            else:
                print(f"  ✅ 无hold负环")
                
            if results[corner]['feasible']:
                print(f"  ✅ 工艺角 {corner} 可行")
            else:
                print(f"  ❌ 工艺角 {corner} 不可行")
        
        return results
    
    def analyze_negative_cycles_at_period_silent(self, T_clk):
        """
        静默分析给定时钟周期下的负环情况（不打印详细输出）
        
        Args:
            T_clk: 时钟周期
            
        Returns:
            dict: 分析结果
        """
        results = {}
        
        for corner in self.corners:
            # 检查setup负环
            has_setup_cycle, setup_cycle = self.detect_setup_negative_cycles(corner, T_clk)
            
            # 检查hold负环
            has_hold_cycle, hold_cycle = self.detect_hold_negative_cycles(corner)
            
            results[corner] = {
                'setup_negative_cycle': has_setup_cycle,
                'setup_cycle_path': setup_cycle,
                'hold_negative_cycle': has_hold_cycle,
                'hold_cycle_path': hold_cycle,
                'feasible': not (has_setup_cycle or has_hold_cycle)
            }
        
        return results
    
    def print_analysis_summary(self, min_period, analysis_results):
        """
        打印分析结果摘要
        
        Args:
            min_period: 最小可行时钟周期
            analysis_results: 分析结果
        """
        print(f"\n{'='*60}")
        print(f"多工艺角负环检测和最小可行时钟周期分析结果")
        print(f"{'='*60}")
        
        if min_period is not None:
            print(f"\n✅ 最小可行时钟周期: {min_period:.3f}")
            print(f"✅ 在此时钟周期下，所有工艺角都无负环")
        else:
            print(f"\n❌ 在搜索范围内未找到可行的时钟周期")
            print(f"❌ 建议检查时序约束或扩大搜索范围")
        
        print(f"\n详细分析结果:")
        for T_clk, corner_results in sorted(analysis_results.items()):
            print(f"\n时钟周期 {T_clk:.3f}:")
            
            all_feasible = True
            for corner, result in corner_results.items():
                if not result['feasible']:
                    all_feasible = False
                    
                status = "✅ 可行" if result['feasible'] else "❌ 不可行"
                print(f"  {corner}: {status}")
                
                if result['setup_negative_cycle']:
                    cycle_str = ' -> '.join(result['setup_cycle_path'])
                    print(f"    Setup负环: {cycle_str}")
                    
                if result['hold_negative_cycle']:
                    cycle_str = ' -> '.join(result['hold_cycle_path'])
                    print(f"    Hold负环: {cycle_str}")
            
            overall_status = "✅ 整体可行" if all_feasible else "❌ 整体不可行"
            print(f"  总体状态: {overall_status}")
    
    def save_analysis_to_file(self, min_period, analysis_results, output_file="negative_cycle_analysis.txt"):
        """
        将分析结果保存到文件
        
        Args:
            min_period: 最小可行时钟周期
            analysis_results: 分析结果
            output_file: 输出文件路径
        """
        with open(output_file, 'w') as f:
            f.write("多工艺角负环检测和最小可行时钟周期分析结果\n")
            f.write("="*60 + "\n\n")
            
            if min_period is not None:
                f.write(f"最小可行时钟周期: {min_period:.3f}\n")
                f.write(f"在此时钟周期下，所有工艺角都无负环\n\n")
            else:
                f.write("在搜索范围内未找到可行的时钟周期\n")
                f.write("建议检查时序约束或扩大搜索范围\n\n")
            
            f.write("详细分析结果:\n")
            for T_clk, corner_results in sorted(analysis_results.items()):
                f.write(f"\n时钟周期 {T_clk:.3f}:\n")
                
                all_feasible = True
                for corner, result in corner_results.items():
                    if not result['feasible']:
                        all_feasible = False
                        
                    status = "可行" if result['feasible'] else "不可行"
                    f.write(f"  {corner}: {status}\n")
                    
                    if result['setup_negative_cycle']:
                        cycle_str = ' -> '.join(result['setup_cycle_path'])
                        f.write(f"    Setup负环: {cycle_str}\n")
                        
                    if result['hold_negative_cycle']:
                        cycle_str = ' -> '.join(result['hold_cycle_path'])
                        f.write(f"    Hold负环: {cycle_str}\n")
                
                overall_status = "整体可行" if all_feasible else "整体不可行"
                f.write(f"  总体状态: {overall_status}\n")
        
        print(f"\n分析结果已保存到文件: {output_file}")


def analyze_timing_graphs(corner_graphs, T_clk_min=0.1, T_clk_max=100.0, precision=0.01, output_dir=None):
    """
    分析多工艺角timing graphs的便捷函数
    
    Args:
        corner_graphs: 多工艺角的timing constraint graph
        T_clk_min: 最小时钟周期搜索范围
        T_clk_max: 最大时钟周期搜索范围
        precision: 精度要求
        output_dir: 输出目录
        
    Returns:
        NegativeCycleDetector: 检测器实例
    """
    detector = NegativeCycleDetector(corner_graphs)
    
    # 查找最小可行时钟周期
    min_period, analysis_results = detector.find_minimum_feasible_clock_period(
        T_clk_min, T_clk_max, precision
    )
    
    # 打印分析结果
    detector.print_analysis_summary(min_period, analysis_results)
    
    # 保存分析结果
    if output_dir:
        output_file = os.path.join(output_dir, "negative_cycle_analysis.txt")
    else:
        output_file = "negative_cycle_analysis.txt"
    
    detector.save_analysis_to_file(min_period, analysis_results, output_file)
    
    return detector


# 测试函数
def _test_negative_cycle_detection():
    """测试负环检测功能"""
    print("开始测试负环检测功能...")
    
    # 导入并使用实际的timing graph builder
    import os
    import sys
    
    # 确保能够导入graph_builder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    try:
        from graph_builder import create_timing_graphs
        
        # 使用实际的配置参数
        project_root = "/home/wllpro/llwang07/kxzhu/DelayPadding"
        netlist_path = "/home/wllpro/llwang07/kxzhu/ssta/distribution/vlsi/ethmac/ethmac.v"
        
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
        
        work_dir = "/home/wllpro/llwang07/kxzhu/DelayPadding/ethmac_dir"
        
        # 检查必要文件是否存在
        if not os.path.exists(netlist_path):
            print(f"❌ 找不到网表文件: {netlist_path}")
            return None
            
        print(f"✅ 使用网表文件: {netlist_path}")
        print(f"✅ 输出目录: {work_dir}")
        
        # 1. 构建原始timing graphs
        print("\n步骤1: 构建原始timing graphs...")
        builder = create_timing_graphs(
            netlist_path=netlist_path,
            corners_config=corners_config,
            work_dir=work_dir
        )
        
        if not builder.graphs:
            print("❌ 构建timing graphs失败")
            return None
            
        print(f"✅ 成功构建了 {len(builder.graphs)} 个工艺角的timing graphs")
        
        # 2. 修改timing constraint graph
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
            return None
            
        # 3. 使用修改后的图进行负环检测测试
        print("\n步骤3: 使用修改后的图进行负环检测...")
        detector = analyze_timing_graphs(
            corner_graphs=modified_graphs,
            T_clk_min=1.0,
            T_clk_max=3000.0,
            precision=0.1,
            output_dir=work_dir
        )
        
        # 4. 额外测试：检查几个特定时钟周期
        print("\n步骤4: 测试特定时钟周期的可行性...")
        test_periods = [150.0, 2000.0, 2500.0]
        
        for T_clk in test_periods:
            print(f"\n检查 T_clk = {T_clk:.1f} 的可行性:")
            detector_test = NegativeCycleDetector(modified_graphs)
            results = detector_test.analyze_negative_cycles_at_period(T_clk)
            
            feasible_corners = [corner for corner, result in results.items() if result['feasible']]
            infeasible_corners = [corner for corner, result in results.items() if not result['feasible']]
            
            print(f"  可行工艺角: {feasible_corners}")
            if infeasible_corners:
                print(f"  不可行工艺角: {infeasible_corners}")
                for corner in infeasible_corners:
                    result = results[corner]
                    if result['setup_negative_cycle']:
                        print(f"    {corner} Setup负环: {' -> '.join(result['setup_cycle_path'])}")
                    if result['hold_negative_cycle']:
                        print(f"    {corner} Hold负环: {' -> '.join(result['hold_cycle_path'])}")
        
        # 5. 比较修改前后的可行时钟周期差距
        print("\n步骤5: 比较修改前后的可行时钟周期差距...")
        try:
            comparison_results = compare_before_after_modification(
                builder=builder,
                T_clk_min=1.0,
                T_clk_max=1000.0,
                precision=0.1,
                output_dir=work_dir
            )
            
            if comparison_results:
                print("✅ 修改前后比较分析完成")
            else:
                print("❌ 修改前后比较分析失败")
                
        except Exception as e:
            print(f"❌ 比较分析出错: {e}")
            import traceback
            traceback.print_exc()
        
        return detector
        
    except ImportError as e:
        print(f"❌ 导入graph_builder失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return None




def compare_before_after_modification(builder, T_clk_min=0.1, T_clk_max=500.0, precision=0.1, output_dir=None):
    """
    比较修改前后timing constraint graph的可行时钟周期差距
    
    Args:
        builder: TimingGraphBuilder实例
        T_clk_min: 最小时钟周期搜索范围
        T_clk_max: 最大时钟周期搜索范围
        precision: 精度要求
        output_dir: 输出目录
        
    Returns:
        dict: 比较结果
    """
    print(f"\n{'='*80}")
    print(f"比较修改前后timing constraint graph的可行时钟周期差距")
    print(f"{'='*80}")
    
    comparison_results = {}
    
    # 1. 分析原始图（修改前）
    print(f"\n步骤1: 分析原始timing constraint graph...")
    original_graphs = builder.graphs  # 未修改的原始图
    
    if not original_graphs:
        print("❌ 没有原始timing graphs")
        return None
    
    print(f"✅ 分析 {len(original_graphs)} 个工艺角的原始图")
    
    # 使用原始图进行负环检测（简化输出）
    original_detector = NegativeCycleDetector(original_graphs)
    print("  🔍 搜索原始图的最小可行时钟周期...")
    original_min_period, original_analysis = original_detector.find_minimum_feasible_clock_period(
        T_clk_min, T_clk_max, precision
    )
    
    print(f"\n原始图分析结果:")
    if original_min_period is not None:
        print(f"✅ 原始图最小可行时钟周期: {original_min_period:.3f}")
    else:
        print(f"❌ 原始图在搜索范围内未找到可行时钟周期")
    
    # 2. 分析修改后的图
    print(f"\n步骤2: 分析修改后的timing constraint graph...")
    modified_graphs = {}
    for corner in builder.corners_config.keys():
        modified_graph = builder.modify_timing_constraint_graph(corner)
        if modified_graph is not None:
            modified_graphs[corner] = modified_graph
    
    if not modified_graphs:
        print("❌ 没有成功修改的timing constraint graph")
        return None
        
    print(f"✅ 分析 {len(modified_graphs)} 个工艺角的修改后图")
    
    # 使用修改后的图进行负环检测（简化输出）
    modified_detector = NegativeCycleDetector(modified_graphs)
    print("  🔍 搜索修改后图的最小可行时钟周期...")
    modified_min_period, modified_analysis = modified_detector.find_minimum_feasible_clock_period(
        T_clk_min, T_clk_max, precision
    )
    
    print(f"\n修改后图分析结果:")
    if modified_min_period is not None:
        print(f"✅ 修改后图最小可行时钟周期: {modified_min_period:.3f}")
    else:
        print(f"❌ 修改后图在搜索范围内未找到可行时钟周期")
    
    # 3. 比较分析
    print(f"\n步骤3: 比较分析...")
    
    comparison_results = {
        'original_min_period': original_min_period,
        'modified_min_period': modified_min_period,
        'original_analysis': original_analysis,
        'modified_analysis': modified_analysis,
        'improvement': None,
        'degradation': None,
        'corner_comparison': {}
    }
    
    # 总体比较
    if original_min_period is not None and modified_min_period is not None:
        if modified_min_period < original_min_period:
            improvement = original_min_period - modified_min_period
            improvement_percent = (improvement / original_min_period) * 100
            comparison_results['improvement'] = {
                'absolute': improvement,
                'percentage': improvement_percent
            }
            print(f"🎉 性能提升! 最小可行时钟周期从 {original_min_period:.3f} 降至 {modified_min_period:.3f}")
            print(f"   ✅ 绝对改进: {improvement:.3f} ({improvement_percent:.1f}%)")
        elif modified_min_period > original_min_period:
            degradation = modified_min_period - original_min_period
            degradation_percent = (degradation / original_min_period) * 100
            comparison_results['degradation'] = {
                'absolute': degradation,
                'percentage': degradation_percent
            }
            print(f"⚠️ 性能下降! 最小可行时钟周期从 {original_min_period:.3f} 升至 {modified_min_period:.3f}")
            print(f"   ❌ 绝对退化: {degradation:.3f} ({degradation_percent:.1f}%)")
        else:
            print(f"➡️ 性能保持不变: {original_min_period:.3f}")
    elif original_min_period is None and modified_min_period is not None:
        print(f"🎉 重大改进! 原始图无可行解，修改后图最小可行时钟周期: {modified_min_period:.3f}")
        comparison_results['improvement'] = {'type': 'feasible_from_infeasible'}
    elif original_min_period is not None and modified_min_period is None:
        print(f"❌ 严重退化! 原始图最小可行时钟周期: {original_min_period:.3f}，修改后图无可行解")
        comparison_results['degradation'] = {'type': 'infeasible_from_feasible'}
    else:
        print(f"❌ 原始图和修改后图都无可行解")
    
    # 4. 按工艺角详细比较
    print(f"\n步骤4: 按工艺角详细比较...")
    
    # 选择一些测试时钟周期进行比较
    test_periods = []
    if original_min_period is not None:
        test_periods.append(original_min_period)
    if modified_min_period is not None:
        test_periods.append(modified_min_period)
    if original_min_period is not None and modified_min_period is not None:
        avg_period = (original_min_period + modified_min_period) / 2
        test_periods.append(avg_period)
    
    # 添加一些固定的测试点
    test_periods.extend([100.0, 200.0, 300.0])
    test_periods = sorted(list(set(test_periods)))  # 去重并排序
    
    for T_clk in test_periods[:5]:  # 限制测试点数量
        print(f"\n比较 T_clk = {T_clk:.1f} 的可行性:")
        
        # 原始图可行性（静默模式）
        original_results = original_detector.analyze_negative_cycles_at_period_silent(T_clk)
        original_feasible = [corner for corner, result in original_results.items() if result['feasible']]
        original_infeasible = [corner for corner, result in original_results.items() if not result['feasible']]
        
        # 修改后图可行性（静默模式）
        modified_results = modified_detector.analyze_negative_cycles_at_period_silent(T_clk)
        modified_feasible = [corner for corner, result in modified_results.items() if result['feasible']]
        modified_infeasible = [corner for corner, result in modified_results.items() if not result['feasible']]
        
        print(f"  原始图 - 可行: {len(original_feasible)}/{len(original_results)}, 不可行: {original_infeasible}")
        print(f"  修改图 - 可行: {len(modified_feasible)}/{len(modified_results)}, 不可行: {modified_infeasible}")
        
        # 分析改进/退化的工艺角
        improved_corners = set(modified_feasible) - set(original_feasible)
        degraded_corners = set(original_feasible) - set(modified_feasible)
        
        if improved_corners:
            print(f"  ✅ 改进的工艺角: {list(improved_corners)}")
        if degraded_corners:
            print(f"  ❌ 退化的工艺角: {list(degraded_corners)}")
        if not improved_corners and not degraded_corners:
            print(f"  ➡️ 所有工艺角状态保持不变")
        
        comparison_results['corner_comparison'][T_clk] = {
            'original_feasible': original_feasible,
            'modified_feasible': modified_feasible,
            'improved_corners': list(improved_corners),
            'degraded_corners': list(degraded_corners)
        }
    
    # 5. 保存比较结果
    if output_dir:
        comparison_file = os.path.join(output_dir, "before_after_comparison.txt")
    else:
        comparison_file = "before_after_comparison.txt"
    
    save_comparison_to_file(comparison_results, comparison_file)
    
    print(f"\n📊 比较分析完成! 结果已保存到: {comparison_file}")
    
    return comparison_results

def save_comparison_to_file(comparison_results, output_file):
    """
    将比较结果保存到文件
    
    Args:
        comparison_results: 比较结果字典
        output_file: 输出文件路径
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("修改前后timing constraint graph可行时钟周期比较分析\n")
        f.write("="*80 + "\n\n")
        
        # 总体结果
        f.write("1. 总体比较结果:\n")
        original_period = comparison_results['original_min_period']
        modified_period = comparison_results['modified_min_period']
        
        f.write(f"   原始图最小可行时钟周期: {original_period if original_period else '无可行解'}\n")
        f.write(f"   修改后图最小可行时钟周期: {modified_period if modified_period else '无可行解'}\n")
        
        if comparison_results.get('improvement'):
            if isinstance(comparison_results['improvement'], dict) and 'type' in comparison_results['improvement']:
                f.write(f"   结果: 重大改进 - 从无可行解变为有可行解\n")
            else:
                imp = comparison_results['improvement']
                f.write(f"   结果: 性能提升 {imp['absolute']:.3f} ({imp['percentage']:.1f}%)\n")
        elif comparison_results.get('degradation'):
            if isinstance(comparison_results['degradation'], dict) and 'type' in comparison_results['degradation']:
                f.write(f"   结果: 严重退化 - 从有可行解变为无可行解\n")
            else:
                deg = comparison_results['degradation']
                f.write(f"   结果: 性能下降 {deg['absolute']:.3f} ({deg['percentage']:.1f}%)\n")
        else:
            f.write(f"   结果: 性能保持不变\n")
        
        # 详细比较
        f.write(f"\n2. 详细时钟周期比较:\n")
        for T_clk, corner_comp in comparison_results['corner_comparison'].items():
            f.write(f"\n   时钟周期 {T_clk:.1f}:\n")
            f.write(f"     原始图可行工艺角: {corner_comp['original_feasible']}\n")
            f.write(f"     修改后可行工艺角: {corner_comp['modified_feasible']}\n")
            if corner_comp['improved_corners']:
                f.write(f"     改进的工艺角: {corner_comp['improved_corners']}\n")
            if corner_comp['degraded_corners']:
                f.write(f"     退化的工艺角: {corner_comp['degraded_corners']}\n")
    
    print(f"比较结果已保存到文件: {output_file}")

def quick_before_after_comparison_example():
    """
    快速演示修改前后可行时钟周期比较功能的示例
    """
    print("="*80)
    print("快速演示：修改前后可行时钟周期比较功能")
    print("="*80)
    
    try:
        from graph_builder import create_timing_graphs
        
        # 使用真实配置
        netlist_path = "/home/wllpro/llwang07/kxzhu/ssta/distribution/vlsi/gcd/gcd.v"
        corners_config = {
            'ss_asap7': [
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_AO_RVT_SS_nldm_211120.lib",
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_INVBUF_RVT_SS_nldm_220122.lib",
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_OA_RVT_SS_nldm_211120.lib",
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SEQ_RVT_SS_nldm_220123.lib",
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SIMPLE_RVT_SS_nldm_211120.lib"
            ]
        }
        work_dir = "/home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir"
        
        print("⏳ 构建timing graphs...")
        builder = create_timing_graphs(
            netlist_path=netlist_path,
            corners_config=corners_config,
            work_dir=work_dir
        )
        
        if builder.graphs:
            print("✅ 成功构建timing graphs")
            
            print("⏳ 进行修改前后比较分析...")
            comparison_results = compare_before_after_modification(
                builder=builder,
                T_clk_min=1.0,  # 较小的搜索范围以加快演示
                T_clk_max=1000.0,
                precision=0.1,   # 较大的精度以加快演示
                output_dir=work_dir
            )
            
            if comparison_results:
                print("\n📊 比较分析摘要:")
                original = comparison_results['original_min_period']
                modified = comparison_results['modified_min_period']
                
                print(f"   原始图最小可行时钟周期: {original if original else '无可行解'}")
                print(f"   修改后最小可行时钟周期: {modified if modified else '无可行解'}")
                
                if comparison_results.get('improvement'):
                    if 'absolute' in comparison_results['improvement']:
                        imp = comparison_results['improvement']
                        print(f"   🎉 性能提升: {imp['absolute']:.1f} ({imp['percentage']:.1f}%)")
                    else:
                        print(f"   🎉 从无可行解变为有可行解!")
                elif comparison_results.get('degradation'):
                    if 'absolute' in comparison_results['degradation']:
                        deg = comparison_results['degradation']
                        print(f"   ⚠️ 性能下降: {deg['absolute']:.1f} ({deg['percentage']:.1f}%)")
                    else:
                        print(f"   ❌ 从有可行解变为无可行解!")
                else:
                    print(f"   ➡️ 性能保持不变")
                
                print(f"\n📄 详细结果已保存到: {work_dir}/before_after_comparison.txt")
                return True
            else:
                print("❌ 比较分析失败")
                return False
        else:
            print("❌ 构建timing graphs失败")
            return False
            
    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")
        return False 

def multi_corner_delay_padding_optimization(builder, T_clk=None, output_dir=None):
    """
    完整的多工艺角delay padding优化流程，结合dual decomposition
    
    Args:
        builder: TimingGraphBuilder实例
        T_clk: 时钟周期，如果为None则自动寻找最小可行时钟周期
        output_dir: 输出目录
        
    Returns:
        dict: 优化结果
    """
    from dual_decomposition import run_dual_decomposition_optimization
    
    print("\n" + "="*80)
    print("🚀 多工艺角Delay Padding优化 (基于Dual Decomposition)")
    print("="*80)
    
    try:
        # 1. 构建修改后的timing constraint graphs
        print("\n1. 构建和修改timing constraint graphs...")
        modified_graphs = {}
        
        for corner in builder.corners_config.keys():
            print(f"  处理工艺角: {corner}")
            modified_graph = builder.modify_timing_constraint_graph(corner)
            if modified_graph is None:
                print(f"  ❌ 工艺角 {corner} 图修改失败")
                return None
            modified_graphs[corner] = modified_graph
            print(f"  ✅ 工艺角 {corner} 图修改完成")
        
        # 2. 如果未指定时钟周期，先找到最小可行时钟周期
        if T_clk is None:
            print("\n2. 寻找最小可行时钟周期...")
            detector = NegativeCycleDetector(modified_graphs)
            min_period, _ = detector.find_minimum_feasible_clock_period(
                T_clk_min=1.0, 
                T_clk_max=3000.0, 
                precision=0.1
            )
            
            if min_period is None:
                print("  ❌ 无法找到可行的时钟周期")
                return None
            
            T_clk = min_period * 1  # 给一些余量
            print(f"  ✅ 最小可行时钟周期: {min_period:.3f}")
            print(f"  📝 使用时钟周期: {T_clk:.3f} (含10%余量)")
        else:
            print(f"\n2. 使用指定时钟周期: {T_clk:.3f}")
        
        # 3. 运行dual decomposition优化
        print("\n3. 运行Dual Decomposition优化...")
        print("   目标: 找到跨工艺角一致的delay padding方案")
        
        optimization_results = run_dual_decomposition_optimization(
            corner_graphs=modified_graphs,
            T_clk=T_clk,
            max_iterations=1000,
            tolerance=1e-2,
            step_size_u=0.01,
            step_size_lambda=0.01
        )
        
        # 4. 分析优化结果
        print("\n4. 分析优化结果...")
        if optimization_results['converged']:
            print(f"  ✅ 算法收敛 (迭代次数: {optimization_results['iterations']})")
        else:
            print(f"  ⚠️  算法未完全收敛 (迭代次数: {optimization_results['iterations']})")
        
        #print(f"  📊 约束满足率: {optimization_results['constraint_satisfaction_rate']:.2%}")
        print(f"  🎯 最终一致性违反: {optimization_results['final_consistency_violation']:.6f}")
        
        # 5. 分析delay padding方案
        y_shared = optimization_results['delay_padding_solution']
        node_potentials = optimization_results['node_potentials']
        shared_potentials = optimization_results['shared_potentials']
        
        # 统计delay padding
        total_padding = sum(max(0, padding) for padding in y_shared.values())
        non_zero_padding_edges = sum(1 for padding in y_shared.values() if padding > 1e-6)
        
        print(f"\n5. Delay Padding方案分析:")
        print(f"  🔧 总delay padding: {total_padding:.3f}")
        print(f"  📈 需要padding的边数: {non_zero_padding_edges}/{len(y_shared)}")
        
        # 显示具体的delay padding方案
        if non_zero_padding_edges > 0:
            print(f"  🔍 具体padding方案:")
            for edge, padding in sorted(y_shared.items()):
                if padding > 1e-6:
                    print(f"    {edge[0]} -> {edge[1]}: {padding:.6f}")
        
        # 显示插入节点的共享电势
        print(f"\n  📊 插入节点共享电势:")
        for node, potential in sorted(shared_potentials.items()):
            if abs(potential) > 1e-6:
                print(f"    {node}: {potential:.6f}")
        
        # 6. 验证最终解的可行性
        print("\n6. 验证最终解的可行性...")
        final_feasibility = optimization_results['final_feasibility']
        all_feasible = optimization_results['all_feasible']
        
        if all_feasible:
            print("  ✅ 所有工艺角都满足时序约束，解可行!")
        else:
            print("  ⚠️  部分工艺角仍有约束违反:")
            for corner, feasible in final_feasibility.items():
                status = "✅" if feasible else "❌"
                print(f"    {status} {corner}: {'可行' if feasible else '不可行'}")
        
        # 7. 保存结果
        if output_dir:
            print(f"\n7. 保存结果到 {output_dir}...")
            save_dual_decomposition_results(optimization_results, T_clk, output_dir)
            print("  ✅ 结果已保存")
        
        return {
            'success': True,
            'T_clk': T_clk,
            'optimization_results': optimization_results,
            'delay_padding_solution': y_shared,
            'node_potentials': node_potentials,
            'shared_potentials': shared_potentials,
            'final_feasible': all_feasible,
            'total_padding': total_padding,
            'modified_edges': non_zero_padding_edges
        }
        
    except Exception as e:
        print(f"\n❌ 优化过程中出现错误: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def save_dual_decomposition_results(optimization_results, T_clk, output_dir):
    """
    保存dual decomposition优化结果
    
    Args:
        optimization_results: 优化结果字典
        T_clk: 时钟周期
        output_dir: 输出目录
    """
    # 保存主要结果
    results_file = os.path.join(output_dir, "dual_decomposition_results.txt")
    with open(results_file, 'w') as f:
        f.write("Dual Decomposition优化结果\n")
        f.write("="*50 + "\n\n")
        
        f.write(f"时钟周期: {T_clk:.3f}\n")
        f.write(f"收敛状态: {'是' if optimization_results['converged'] else '否'}\n")
        f.write(f"迭代次数: {optimization_results['iterations']}\n")
        f.write(f"最终一致性违反: {optimization_results['final_consistency_violation']:.6f}\n")
        f.write(f"所有工艺角可行: {'是' if optimization_results['all_feasible'] else '否'}\n\n")
        
        # 保存delay padding方案
        f.write("Delay Padding方案:\n")
        f.write("-"*30 + "\n")
        y_shared = optimization_results['delay_padding_solution']
        total_padding = 0.0
        padding_count = 0
        
        for edge, padding in sorted(y_shared.items()):
            if padding > 1e-6:  # 只显示有意义的padding
                f.write(f"{edge[0]} -> {edge[1]}: {padding:.6f}\n")
                total_padding += padding
                padding_count += 1
        
        if padding_count == 0:
            f.write("无需delay padding\n")
        else:
            f.write(f"\n总计: {padding_count} 条边需要padding，总量 {total_padding:.6f}\n")
        
        # 保存插入节点的共享电势
        f.write("\n插入节点共享电势:\n")
        f.write("-"*30 + "\n")
        shared_potentials = optimization_results['shared_potentials']
        for node, potential in sorted(shared_potentials.items()):
            if abs(potential) > 1e-6:
                f.write(f"{node}: {potential:.6f}\n")
        
        # 保存节点电势方案 (按工艺角)
        f.write("\n节点电势方案 (按工艺角):\n")
        f.write("-"*30 + "\n")
        node_potentials = optimization_results['node_potentials']
        
        for corner in sorted(node_potentials.keys()):
            f.write(f"\n工艺角 {corner}:\n")
            corner_potentials = node_potentials[corner]
            potential_count = 0
            for node, potential in sorted(corner_potentials.items()):
                if abs(potential) > 1e-6:  # 只显示有意义的电势
                    f.write(f"  {node}: {potential:.6f}\n")
                    potential_count += 1
            if potential_count == 0:
                f.write("  所有节点电势为0\n")
        
        # 保存工艺角可行性
        f.write("\n工艺角可行性:\n")
        f.write("-"*30 + "\n")
        final_feasibility = optimization_results['final_feasibility']
        for corner, feasible in sorted(final_feasibility.items()):
            status = "✅ 可行" if feasible else "❌ 不可行"
            f.write(f"{corner}: {status}\n")
    
    # 保存收敛历史
    convergence_file = os.path.join(output_dir, "convergence_history.txt")
    with open(convergence_file, 'w') as f:
        f.write("Iteration,Consistency_Violation,Infeasible_Corners,Step_Size,Converged\n")
        for record in optimization_results['convergence_history']:
            step_size = record.get('step_size', 0.0)
            f.write(f"{record['iteration']},{record['consistency_violation']:.6f},"
                   f"{record['infeasible_corners']},{step_size:.6f},"
                   f"{record['converged']}\n")


def demo_dual_decomposition_optimization():
    """
    演示dual decomposition优化的完整流程
    """
    try:
        print("🔬 Dual Decomposition优化演示")
        print("="*60)
        
        # 导入必要的模块
        from graph_builder import TimingGraphBuilder
        
        # 配置路径和工艺角
        work_dir = '/home/wllpro/llwang07/kxzhu/DelayPadding/ibex_dir'
        netlist_path = "/home/wllpro/llwang07/kxzhu/ssta/distribution/vlsi/ibex/ibex.v"
        
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
        from graph_builder import create_timing_graphs
        # 1. 构建timing graphs
        print("1. 构建timing graphs...")
        # builder = TimingGraphBuilder(netlist_path, corners_config, work_dir=work_dir)
        # graphs = builder.build_timing_graphs()
        print("\n步骤1: 构建原始timing graphs...")
        builder = create_timing_graphs(
            netlist_path=netlist_path,
            corners_config=corners_config,
            work_dir=work_dir
        )
        if not builder.graphs:
            print("❌ 无法构建timing graphs")
            return False
        
        print(f"✅ 成功构建 {len(builder.graphs)} 个工艺角的图")
        
        # 2. 运行dual decomposition优化
        print("\n2. 运行多工艺角优化...")
        results = multi_corner_delay_padding_optimization(
            builder=builder,
            T_clk=None,  # 自动寻找最小可行时钟周期
            output_dir=work_dir
        )
        
        if results and results['success']:
            print("\n🎉 Dual Decomposition优化完成!")
            print(f"📊 时钟周期: {results['T_clk']:.3f}")
            print(f"🔧 总delay padding: {results['total_padding']:.3f}")
            print(f"📈 修改边数: {results['modified_edges']}")
            print(f"✅ 最终可行性: {'是' if results['final_feasible'] else '否'}")
            
            # 显示优化统计信息
            opt_results = results['optimization_results']
            print(f"🔄 迭代次数: {opt_results['iterations']}")
            print(f"📈 收敛状态: {'是' if opt_results['converged'] else '否'}")
            
            # 显示节点统计
            if 'shared_potentials' in results:
                shared_count = len([p for p in results['shared_potentials'].values() if abs(p) > 1e-6])
                print(f"🎯 有效插入节点数: {shared_count}")
            
            return True
        else:
            print("\n❌ Dual Decomposition优化失败")
            if results and 'error' in results:
                print(f"错误信息: {results['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        return False
    

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            # 运行快速演示
            print("运行快速比较演示...")
            success = quick_before_after_comparison_example()
            if success:
                print("\n🎉 快速演示完成!")
            else:
                print("\n❌ 快速演示失败!")
        elif sys.argv[1] == "dual":
            # 运行dual decomposition优化演示
            print("运行Dual Decomposition优化演示...")
            success = demo_dual_decomposition_optimization()
            if success:
                print("\n🎉 Dual Decomposition优化演示完成!")
            else:
                print("\n❌ Dual Decomposition优化演示失败!")
        else:
            print("未知参数。可用选项:")
            print("  demo  - 运行快速比较演示")
            print("  dual  - 运行Dual Decomposition优化演示")
            print("  (无参数) - 运行完整测试")
    else:
        # 运行完整测试
        print("运行完整测试...")
        success = _test_negative_cycle_detection()
        print("\n测试完成!")
        
        print("\n" + "="*60)
        print("💡 提示:")
        print("  - 运行快速演示: python negative_cycle_detector.py demo")
        print("  - 运行Dual Decomposition优化: python negative_cycle_detector.py dual")
        print("  - 运行完整测试: python negative_cycle_detector.py")
        print("="*60)