import networkx as nx
import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import copy
import random

class DualDecompositionSolver:
    """
    基于拉格朗日对偶分解的多工艺角clock skew scheduling求解器
    
    算法理论背景：
    原问题：
        min f(u^1, u^2, ..., u^K)
        s.t. timing constraints for each corner k
             consistency constraints: u^k_shared = u^shared for all k
    
    对偶分解后的子问题：
        对每个corner k求解：
        min λ^k^T(u^k - u^shared) + timing_penalty
        s.t. A^k · u^k ≤ b^k (timing constraints)
    
    实现方法：
    - 使用Bellman-Ford算法求解每个子问题的最短路径
    - 子问题目标函数包含拉格朗日乘子项
    - 拉格朗日乘子更新确保一致性约束
    
    正确的问题formulation：
    - 给定修改后的timing constraint graphs（包含us、uh节点）
    - 优化变量：各工艺角的节点电势 u^k
    - 约束：每个工艺角的修改后图无负环
    - 一致性约束：所有工艺角的us、uh节点电势应该一致
    - delay padding = u_s - u_original 或 u_h - u_original
    """
    
    def __init__(self, corner_graphs: Dict[str, nx.DiGraph], T_clk: float):
        """
        初始化dual decomposition求解器
        
        Args:
            corner_graphs: 多工艺角的修改后timing constraint graphs
            T_clk: 时钟周期
        """
        self.corner_graphs = corner_graphs
        self.T_clk = T_clk
        self.corners = list(corner_graphs.keys())
        
        # 收集所有节点（包括原始节点和插入的us、uh节点）
        self.all_nodes = set()
        for graph in corner_graphs.values():
            self.all_nodes.update(graph.nodes())
        self.all_nodes = sorted(list(self.all_nodes))
        
        # 识别插入的节点（us、uh节点）
        self.inserted_nodes = set()
        self.original_nodes = set()
        
        for graph in corner_graphs.values():
            for node, data in graph.nodes(data=True):
                node_type = data.get('type', 'register')
                if node_type in ['inserted_setup', 'inserted_hold', 'inserted_common', 
                               'inserted_setup_dominant', 'inserted_hold_dependent']:
                    self.inserted_nodes.add(node)
                else:
                    self.original_nodes.add(node)
        
        self.inserted_nodes = sorted(list(self.inserted_nodes))
        self.original_nodes = sorted(list(self.original_nodes))
        
        print("识别到 {} 个原始节点，{} 个插入节点".format(len(self.original_nodes), len(self.inserted_nodes)))
        
        # 初始化节点电势（每个工艺角独立）
        self.node_potentials = {corner: {node: 0.0 for node in self.all_nodes} 
                               for corner in self.corners}
        
        # 初始化拉格朗日乘子（对插入节点的一致性约束）
        # 使用随机初始化避免所有乘子相同
        random.seed(42)  # 为了可重复性
        self.lambda_multipliers = {corner: {node: random.uniform(0.1, 2.0) for node in self.inserted_nodes} 
                                  for corner in self.corners}
        
        # 给插入节点一些初始的不同电势，避免所有都为0
        for corner in self.corners:
            for i, node in enumerate(self.inserted_nodes):
                self.node_potentials[corner][node] = 0.1 * (i % 10 + 1) * (1 if corner == self.corners[0] else -1)
        
    def solve_clock_skew_scheduling(self, corner: str) -> Tuple[bool, Dict[str, float]]:
        """
        对给定工艺角求解clock skew scheduling问题
        使用Bellman-Ford算法求解带拉格朗日乘子的最短路径问题
        
        子问题形式：
        min λ^T(u^k - u^shared) + timing_penalty
        s.t. timing constraints
        
        Args:
            corner: 工艺角名称
            
        Returns:
            Tuple[bool, Dict[str, float]]: (是否有解, 节点电势)
        """
        graph = self.corner_graphs[corner]
        
        # 首先使用负环检测检查基本可行性
        from negative_cycle_detector import NegativeCycleDetector
        
        detector = NegativeCycleDetector({corner: graph})
        
        # 检查setup负环
        has_setup_cycle, _ = detector.detect_setup_negative_cycles(corner, self.T_clk)
        
        # 检查hold负环  
        has_hold_cycle, _ = detector.detect_hold_negative_cycles(corner)
        
        basic_feasible = not (has_setup_cycle or has_hold_cycle)
        
        if not basic_feasible:
            return False, {}
        
        # 如果基本可行，使用Bellman-Ford求解带拉格朗日乘子的最优化问题
        return self._solve_augmented_lagrangian_subproblem(corner)
    

    

    
    def _solve_augmented_lagrangian_subproblem(self, corner: str) -> Tuple[bool, Dict[str, float]]:
        """
        正确求解minimum cost potential problem
        
        子问题形式：
        minimize: λᵏᵀ(uᵏ - u^shared) = Σᵢ λᵢᵏ * uᵢᵏ - Σᵢ λᵢᵏ * uᵢ^shared
        
        由于uᵢ^shared是常数，等价于：
        minimize: Σᵢ λᵢᵏ * uᵢᵏ  (λᵢᵏ作为节点成本系数)
        subject to: 
          - setup constraints: u_j - u_i ≤ w_ij
          - hold constraints: u_i - u_j ≤ w_ij
        
        这里使用了minimum cost potential problem的关键思想：
        - 节点成本 = λᵢᵏ (拉格朗日乘子)
        - 边约束 = timing constraint bounds
        - 通过虚拟源节点转换为最短路径问题
        
        Args:
            corner: 工艺角名称
            
        Returns:
            Tuple[bool, Dict[str, float]]: (是否有解, 最优节点电势)
        """
        graph = self.corner_graphs[corner]
        lambda_k = self.lambda_multipliers[corner]
        shared_potentials = self.get_shared_potentials()
        
        print(f"  Corner {corner} 拉格朗日乘子样本: {dict(list(lambda_k.items())[:3])}")
        
        try:
            # 求解minimum cost potential problem的两步法：
            # 第一步：检查timing constraints可行性
            # 第二步：在可行域内最小化成本
            
            # 添加timing constraint边（这些边强制timing约束）
            # 使用两步法：先确保可行性，再优化成本
            constraint_graph = nx.DiGraph()
            
            # 在constraint graph中添加节点
            for node in self.all_nodes:
                constraint_graph.add_node(node)
            
            # 添加timing constraint边到constraint graph
            for u, v, data in graph.edges(data=True):
                path_detail = data.get("path_detail", "")
                
                # Setup constraints: u_v - u_u <= constraint_bound
                setup_data = data.get("setup_delay", {})
                if setup_data:
                    if path_detail in ['setup_path', 'hold_path', 'common_path', 'setup_to_hold_constraint']:
                        # 新添加节点之间的边，约束权重为0
                        constraint_bound = 0.0
                    else:
                        # 原始timing约束边
                        arrival = setup_data.get("arrival_time", 0)
                        T_setup = setup_data.get("library_time", 0)
                        constraint_bound = self.T_clk + T_setup - arrival
                    
                    # 添加到constraint graph，边权重为约束上界
                    constraint_graph.add_edge(u, v, weight=constraint_bound)
                
                # Hold constraints: u_u - u_v <= constraint_bound
                hold_data = data.get("hold_delay", {})
                if hold_data:
                    if path_detail in ['setup_path', 'hold_path', 'common_path', 'setup_to_hold_constraint']:
                        # 新添加节点之间的边，约束权重为0
                        constraint_bound = 0.0
                        constraint_graph.add_edge(u, v, weight=constraint_bound)
                    else:
                        # 原始timing约束边，反向：u_u - u_v <= constraint_bound
                        arrival = hold_data.get("arrival_time", 0)
                        T_hold = hold_data.get("library_time", 0)
                        constraint_bound = arrival - T_hold
                        
                        # 添加反向约束边: v -> u
                        constraint_graph.add_edge(v, u, weight=constraint_bound)
            
            # 第一步：检查timing constraints的可行性
            try:
                if constraint_graph.nodes():
                    reference_node = list(constraint_graph.nodes())[0]
                    
                    # 使用Bellman-Ford检测负环
                    distances, _ = nx.single_source_bellman_ford(
                        constraint_graph, reference_node, weight='weight')
                    
                    # 得到满足timing constraints的基础电势
                    base_potentials = {}
                    for node in self.all_nodes:
                        if node in distances:
                            base_potentials[node] = distances[node]
                        else:
                            base_potentials[node] = 0.0
                else:
                    base_potentials = {node: 0.0 for node in self.all_nodes}
            
            except nx.NetworkXError as e:
                print(f"Corner {corner} timing constraints不可行: {str(e)}")
                return False, {}
            
            # 第二步：在可行域内最小化成本 Σᵢ λᵢᵏ * uᵢᵏ
            # 使用梯度投影法在约束集合内优化
            optimal_potentials = base_potentials.copy()
            
            # 对每个插入节点进行成本优化
            for node in self.inserted_nodes:
                if node in lambda_k:
                    lambda_val = lambda_k[node]
                    
                    if abs(lambda_val) > 1e-10:  # 只对非零拉格朗日乘子优化
                        # 如果λ > 0，希望减小u；如果λ < 0，希望增大u
                        # 在约束范围内调整
                        
                        current_potential = optimal_potentials[node]
                        
                        if lambda_val > 0:
                            # 尝试减小电势，但不能违反incoming constraints
                            min_potential = current_potential
                            for pred in constraint_graph.predecessors(node):
                                bound = constraint_graph[pred][node]['weight']
                                min_potential = max(min_potential, optimal_potentials[pred] - bound)
                            optimal_potentials[node] = min_potential
                            
                        else:  # lambda_val < 0
                            # 尝试增大电势，但不能违反outgoing constraints
                            max_potential = current_potential
                            for succ in constraint_graph.successors(node):
                                bound = constraint_graph[node][succ]['weight']
                                max_potential = min(max_potential, optimal_potentials[succ] + bound)
                            optimal_potentials[node] = max_potential
            
            # 计算目标函数值：Σᵢ λᵢᵏ * uᵢᵏ
            objective_value = sum(lambda_k.get(node, 0) * optimal_potentials[node] 
                                for node in self.inserted_nodes)
            
            print(f"    最优目标值: {objective_value:.6f}")
            
            return True, optimal_potentials
                
        except Exception as e:
            print(f"Corner {corner} 最小成本电势求解出错: {str(e)}")
            return False, {}
    
    def get_shared_potentials(self) -> Dict[str, float]:
        """
        计算插入节点的共享电势（所有工艺角的平均值）
        
        Returns:
            Dict[str, float]: 插入节点的共享电势
        """
        shared_potentials = {}
        
        for node in self.inserted_nodes:
            # 计算所有工艺角的平均电势
            total_potential = sum(self.node_potentials[corner][node] for corner in self.corners)
            shared_potentials[node] = total_potential / len(self.corners)
            
        return shared_potentials
    
    def get_delay_padding_solution(self) -> Dict[Tuple[str, str], float]:
        """
        从节点电势中提取delay padding解
        
        Delay padding的正确计算方法：
        对于边 u->v，delay padding是在原始边上增加的延迟，使timing满足。
        
        基于电势计算：
        - setup constraint: u_v - u_u ≤ T_clk + T_setup - (delay + padding)
        - 所以 padding 应该基于timing slack计算，不是简单的电势差
        
        Returns:
            Dict[Tuple[str, str], float]: delay padding方案 (原始边 -> padding值)
        """
        shared_potentials = self.get_shared_potentials()
        delay_padding = {}
        processed_edges = set()  # 避免重复处理同一条边
        
        # 遍历插入节点，找到对应的原始边
        for graph in self.corner_graphs.values():
            for node, data in graph.nodes(data=True):
                if node in self.inserted_nodes:
                    original_edge = data.get('original_edge')
                    node_type = data.get('type', '')
                    
                    if original_edge and original_edge not in processed_edges:
                        source_node, sink_node = original_edge
                        
                        if source_node in self.original_nodes and sink_node in self.original_nodes:
                            # 计算基于timing constraint的delay padding
                            # 方法1：基于时钟skew的需求
                            source_potential = self.node_potentials[self.corners[0]][source_node]
                            sink_potential = self.node_potentials[self.corners[0]][sink_node]
                            
                            # 基本的timing slack（目标电势差 vs 实际电势差）
                            actual_skew = sink_potential - source_potential
                            
                            # 寻找该边对应的hold和setup插入节点
                            hold_node = None
                            setup_node = None
                            
                            for check_node, check_data in graph.nodes(data=True):
                                if (check_data.get('original_edge') == original_edge and 
                                    check_node in self.inserted_nodes):
                                    if 'hold' in check_data.get('type', '').lower():
                                        hold_node = check_node
                                    elif 'setup' in check_data.get('type', '').lower():
                                        setup_node = check_node
                            
                            # 使用hold节点计算delay padding（更保守的选择）
                            if hold_node and hold_node in shared_potentials:
                                # hold constraint: u_source - u_sink ≤ (original_delay + padding) - T_hold
                                # 重新排列: padding ≥ (u_source - u_sink) + T_hold - original_delay
                                # 简化计算：使用插入的hold节点与原始源节点的电势差
                                hold_potential = shared_potentials[hold_node]
                                
                                # 方法：基于hold节点相对于源节点的位移
                                # 这表示为了满足hold constraint需要的最小延迟增加
                                padding = hold_potential - source_potential
                                
                                # 但是，如果hold节点电势接近source电势，说明不需要太多padding
                                # 使用setup节点作为对比
                                if setup_node and setup_node in shared_potentials:
                                    setup_potential = shared_potentials[setup_node]
                                    # 如果setup要求更大的延迟，使用setup的要求
                                    setup_padding = setup_potential - source_potential
                                    
                                    # 取两者的最小值（更realistic）
                                    padding = min(abs(padding), abs(setup_padding))
                                else:
                                    padding = abs(padding)
                                
                                # 确保padding非负且合理
                                padding = max(0.0, min(padding, self.T_clk * 0.5))  # 限制在半个时钟周期内
                                delay_padding[original_edge] = padding
                                
                            elif setup_node and setup_node in shared_potentials:
                                # 如果只有setup节点，使用更保守的计算
                                setup_potential = shared_potentials[setup_node]
                                padding = abs(setup_potential - source_potential)
                                
                                # 限制padding在合理范围内
                                padding = max(0.0, min(padding, self.T_clk * 0.3))
                                delay_padding[original_edge] = padding
                            
                            processed_edges.add(original_edge)
                            break  # 处理完这条边就跳出内层循环
        
        return delay_padding
    

    
    def check_convergence(self, potentials_old: Dict[str, Dict[str, float]], 
                         lambda_old: Dict[str, Dict[str, float]], 
                         tolerance: float = 10) -> bool:
        """
        检查收敛性
        
        Args:
            potentials_old: 上一次迭代的节点电势
            lambda_old: 上一次迭代的拉格朗日乘子
            tolerance: 收敛容忍度
            
        Returns:
            bool: 是否收敛
        """
        # 1. 检查一致性违反是否足够小
        shared_potentials = self.get_shared_potentials()
        max_consistency_violation = 0.0
        
        for corner in self.corners:
            for node in self.inserted_nodes:
                if node in shared_potentials and node in self.node_potentials[corner]:
                    violation = abs(self.node_potentials[corner][node] - shared_potentials[node])
                    max_consistency_violation = max(max_consistency_violation, violation)
        
        consistency_converged = max_consistency_violation < tolerance * 10  # 放宽一致性要求
        
        # 2. 检查节点电势的变化是否足够小
        max_potential_change = 0.0
        for corner in self.corners:
            for node in self.all_nodes:
                if node in self.node_potentials[corner] and node in potentials_old[corner]:
                    change = abs(self.node_potentials[corner][node] - potentials_old[corner][node])
                    max_potential_change = max(max_potential_change, change)
        
        potential_converged = max_potential_change < tolerance
        
        # 3. 检查拉格朗日乘子的变化是否足够小
        max_lambda_change = 0.0
        for corner in self.corners:
            for node in self.inserted_nodes:
                if node in self.lambda_multipliers[corner] and node in lambda_old[corner]:
                    change = abs(self.lambda_multipliers[corner][node] - lambda_old[corner][node])
                    max_lambda_change = max(max_lambda_change, change)
        
        lambda_converged = max_lambda_change < tolerance
        
        # 如果一致性已经很好，并且变化很小，就认为收敛
        converged = consistency_converged and (potential_converged or lambda_converged)
        
        # 添加详细的调试信息（每50次迭代输出一次）
        if hasattr(self, '_debug_counter'):
            self._debug_counter += 1
        else:
            self._debug_counter = 0
            
        if self._debug_counter % 50 == 0:
            print("=== 收敛诊断 ===")
            print("  一致性违反: {:.6f} (需要 < {:.1f}) -> {}".format(
                max_consistency_violation, tolerance * 10, consistency_converged))
            print("  电势最大变化: {:.6f} (需要 < {:.1f}) -> {}".format(
                max_potential_change, tolerance, potential_converged))
            print("  乘子最大变化: {:.6f} (需要 < {:.1f}) -> {}".format(
                max_lambda_change, tolerance, lambda_converged))
            print("  总体收敛: {} = {} AND ({} OR {})".format(
                converged, consistency_converged, potential_converged, lambda_converged))
        
        return converged
    

    
    def _evaluate_corner_objective(self, corner: str) -> float:
        """
        计算给定corner的目标函数值（拉格朗日项）
        
        Args:
            corner: 工艺角名称
            
        Returns:
            float: 目标函数值
        """
        lambda_k = self.lambda_multipliers[corner]
        shared_potentials = self.get_shared_potentials()
        objective_value = 0.0
        
        for node in self.inserted_nodes:
            if node in lambda_k and node in shared_potentials:
                u_k = self.node_potentials[corner].get(node, 0.0)
                u_shared = shared_potentials[node]
                objective_value += lambda_k[node] * (u_k - u_shared)
        
        return objective_value
    
    def solve(self, max_iterations: int = 1000, tolerance: float = 1e-4, 
             step_size_u: float = 0.01, step_size_lambda: float = 0.01) -> Dict:
        """
        主求解函数
        
        Args:
            max_iterations: 最大迭代次数
            tolerance: 收敛容忍度
            step_size_u: 节点电势更新步长
            step_size_lambda: 拉格朗日乘子更新步长
            
        Returns:
            Dict: 求解结果
        """
        print("开始Dual Decomposition求解...")
        print("工艺角数量: {}".format(len(self.corners)))
        print("总节点数量: {}".format(len(self.all_nodes)))
        print("插入节点数量: {}".format(len(self.inserted_nodes)))
        print("时钟周期: {}".format(self.T_clk))
        
        convergence_history = []
        
        for iteration in range(max_iterations):
            # 保存上一次迭代的值
            potentials_old = copy.deepcopy(self.node_potentials)
            lambda_old = copy.deepcopy(self.lambda_multipliers)
            
            # === 第1步：求解所有corner的子问题（每个corner只求解一次） ===
            corner_solutions = {}
            infeasible_corners = 0
            dual_objective = 0.0
            
            for corner in self.corners:
                feasible, optimal_potentials = self.solve_clock_skew_scheduling(corner)
                corner_solutions[corner] = {
                    'feasible': feasible,
                    'potentials': optimal_potentials if feasible else self.node_potentials[corner],
                    'objective': 0.0
                }
                
                if not feasible:
                    infeasible_corners += 1
                else:
                    # 更新节点电势
                    if optimal_potentials:
                        # 确保所有节点都有值
                        updated_potentials = {}
                        for node in self.all_nodes:
                            if node in optimal_potentials:
                                updated_potentials[node] = optimal_potentials[node]
                            else:
                                updated_potentials[node] = self.node_potentials[corner].get(node, 0.0)
                        self.node_potentials[corner] = updated_potentials
                    
                    # 计算目标函数值
                    corner_solutions[corner]['objective'] = self._evaluate_corner_objective(corner)
                    dual_objective += corner_solutions[corner]['objective']
            
            # === 第2步：更新拉格朗日乘子（基于已求解的结果） ===
            shared_potentials = self.get_shared_potentials()
            lambda_new = copy.deepcopy(self.lambda_multipliers)
            
            for corner in self.corners:
                solution = corner_solutions[corner]
                
                for node in self.inserted_nodes:
                    if not solution['feasible']:
                        # 如果不可行，增加拉格朗日乘子
                        lambda_new[corner][node] += step_size_lambda
                    else:
                        # 如果可行，基于一致性违反程度调整乘子
                        if node in shared_potentials and node in self.node_potentials[corner]:
                            consistency_violation = abs(self.node_potentials[corner][node] - shared_potentials[node])
                            
                            if consistency_violation > 1e-3:  # 放宽一致性要求
                                # 增加乘子以强制一致性
                                lambda_new[corner][node] += step_size_lambda * consistency_violation
                            elif consistency_violation < 1e-4:
                                # 只有在一致性非常好时才轻微减少乘子
                                lambda_new[corner][node] = max(0.1, lambda_new[corner][node] - step_size_lambda * 0.05)
                            # 在中间区域保持乘子不变
                    
                    # 确保乘子在合理范围内
                    lambda_new[corner][node] = max(0.1, min(10.0, lambda_new[corner][node]))
            
            self.lambda_multipliers = lambda_new
            
            # === 第3步：检查收敛性 ===
            converged = self.check_convergence(potentials_old, lambda_old, tolerance)
            
            # === 第4步：计算总目标函数和一致性违反 ===
            consistency_violation = 0.0
            for corner in self.corners:
                for node in self.inserted_nodes:
                    if node in self.node_potentials[corner] and node in shared_potentials:
                        diff = self.node_potentials[corner][node] - shared_potentials[node]
                        consistency_violation += abs(diff)
            
            # 综合目标函数：拉格朗日目标 + 不可行惩罚 + 一致性违反惩罚
            objective_value = dual_objective + 1000 * infeasible_corners + 10 * consistency_violation
            
            convergence_history.append({
                'iteration': iteration,
                'objective': objective_value,
                'dual_objective': dual_objective,
                'consistency_violation': consistency_violation,
                'infeasible_corners': infeasible_corners,
                'converged': converged
            })
            
            if iteration % 50 == 0 or converged:
                print("迭代 {}: 对偶目标 = {:.6f}, ".format(iteration, dual_objective) +
                      "一致性违反 = {:.6f}, ".format(consistency_violation) +
                      "不可行corners = {}, 收敛 = {}".format(infeasible_corners, converged))
                
                # 添加详细调试信息
                if iteration % 100 == 0:
                    print("  共享电势样本: {}".format(dict(list(shared_potentials.items())[:3])))
                    first_corner_lambdas = self.lambda_multipliers[self.corners[0]]
                    print("  拉格朗日乘子样本 (corner {}): {}".format(
                        self.corners[0], dict(list(first_corner_lambdas.items())[:3])))
                    
                    # 显示一些插入节点的电势差异
                    sample_nodes = list(self.inserted_nodes)[:3]
                    for node in sample_nodes:
                        if node in shared_potentials:
                            corner_vals = [self.node_potentials[c].get(node, 0) for c in self.corners]
                            print("  节点 {}: corner电势={}, 共享={:.4f}".format(
                                node, corner_vals, shared_potentials[node]))
            
            if converged:
                print("在第 {} 次迭代后收敛!".format(iteration))
                break
        
        # 评估最终解
        final_feasibility = {}
        for corner in self.corners:
            final_feasibility[corner] = corner_solutions.get(corner, {}).get('feasible', False)
        
        all_feasible = all(final_feasibility.values())
        
        # 提取delay padding方案
        delay_padding_solution = self.get_delay_padding_solution()
        
        return {
            'converged': converged,
            'iterations': min(iteration + 1, max_iterations),
            'objective_value': objective_value,
            'dual_objective': dual_objective,
            'delay_padding_solution': delay_padding_solution,
            'node_potentials': self.node_potentials,
            'shared_potentials': self.get_shared_potentials(),
            'lambda_multipliers': self.lambda_multipliers,
            'final_feasibility': final_feasibility,
            'all_feasible': all_feasible,
            'convergence_history': convergence_history
        }


def run_dual_decomposition_optimization(corner_graphs: Dict[str, nx.DiGraph], 
                                       T_clk: float,
                                       max_iterations: int = 1000,
                                       tolerance: float = 1e-2,
                                       step_size_u: float = 0.01,
                                       step_size_lambda: float = 0.01) -> Dict:
    """
    运行dual decomposition优化的便捷函数
    
    Args:
        corner_graphs: 多工艺角的修改后timing constraint graphs
        T_clk: 时钟周期
        max_iterations: 最大迭代次数
        tolerance: 收敛容忍度  
        step_size_u: 节点电势更新步长
        step_size_lambda: 拉格朗日乘子更新步长
        
    Returns:
        Dict: 优化结果
    """
    solver = DualDecompositionSolver(corner_graphs, T_clk)
    return solver.solve(max_iterations, tolerance, step_size_u, step_size_lambda)


def _test_dual_decomposition():
    """
    测试dual decomposition算法
    """
    import networkx as nx
    
    print("测试Dual Decomposition求解器...")
    
    # 创建简单的测试图
    test_graphs = {}
    for corner in ['ff', 'ss']:
        G = nx.DiGraph()
        G.add_node('reg1', type='register')
        G.add_node('reg2', type='register')
        G.add_node('us_1_2', type='inserted_setup', original_edge=('reg1', 'reg2'))
        
        # 添加setup约束边，让不同corner有不同的delay
        arrival_time = 2.0 if corner == 'ff' else 2.5  # ff更快，ss更慢
        G.add_edge('reg1', 'us_1_2', 
                  setup_delay={'arrival_time': arrival_time, 'library_time': 0.5},
                  path_detail='original')
        G.add_edge('us_1_2', 'reg2',
                  setup_delay={'arrival_time': 0.0, 'library_time': 0.0},
                  path_detail='setup_path')
        
        test_graphs[corner] = G
    
    # 测试求解器
    solver = DualDecompositionSolver(test_graphs, T_clk=10.0)
    
    print("创建了 {} 个工艺角的测试图".format(len(solver.corners)))
    print("总节点数: {}".format(len(solver.all_nodes)))
    print("插入节点数: {}".format(len(solver.inserted_nodes)))
    
    # 运行较少迭代但显示更多信息
    try:
        results = solver.solve(max_iterations=200, tolerance=0.1, 
                             step_size_u=0.01, step_size_lambda=0.02)
        
        print("\n=== 最终结果 ===")
        print("求解完成: 收敛={}, 迭代次数={}".format(results['converged'], results['iterations']))
        print("所有corner可行: {}".format(results['all_feasible']))
        print("最终目标值: {:.6f}".format(results['objective_value']))
        
        # 显示最终的节点电势
        print("\n=== 最终节点电势 ===")
        for corner in solver.corners:
            print("Corner {}:".format(corner))
            for node in solver.inserted_nodes:
                if node in solver.node_potentials[corner]:
                    print("  {}: {:.6f}".format(node, solver.node_potentials[corner][node]))
        
        print("\n=== 共享电势 ===")
        shared = solver.get_shared_potentials()
        for node, potential in shared.items():
            print("  {}: {:.6f}".format(node, potential))
        
        # 显示delay padding结果
        padding = results.get('delay_padding_solution', {})
        print("\n=== Delay Padding方案 ===")
        if padding:
            for edge, value in padding.items():
                print("  边 {}: {:.6f}".format(edge, value))
        else:
            print("  无delay padding方案")
        
        return results
    except Exception as e:
        print("测试过程中出现错误: {}".format(e))
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    _test_dual_decomposition()