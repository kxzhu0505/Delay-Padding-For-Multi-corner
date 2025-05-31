import networkx as nx
from scipy.stats import genextreme
from collections import defaultdict
from core.lp_solver import delay_padding_lp_solver

def run_dual_delay_padding(corner_graphs, TCLK, eta, max_iter=100, tol=1e-3, alpha=0.1, beta=0.1, max_padding=float('inf')):
    """
    多Corner Delay Padding优化函数，适配您的数据结构。
    
    参数:
        corner_graphs (dict): 多Corner时序图，格式为 {corner: nx.Graph}.
        TCLK (float): 时钟周期.
        eta (float): 时序违规容忍度.
        max_iter (int): 最大迭代次数.
        tol (float): 收敛阈值.
        alpha (float): 势能平滑项系数.
        beta (float): Buffer插入惩罚系数.
        max_padding (float): delay padding的最大允许值，默认无限制.
    
    返回:
        dict: 优化后的全局电势 {node: potential}.
        dict: 每条边的setup delay padding值 {(u,v): d_uv}.
        dict: 每条边的hold delay padding值 {(u,v): d_uv}.
        bool: 是否收敛.
        str: 错误信息.
    """
    # --------------------- 初始化 ---------------------
    # 1. 提取所有节点和初始电势（初始化为0）
    all_nodes = set()
    for G in corner_graphs.values():
        all_nodes.update(G.nodes())
    p = defaultdict(float, {node: 0.0 for node in all_nodes})
    
    # 初始化每条边的setup和hold delay padding值
    setup_padding = defaultdict(float)
    hold_padding = defaultdict(float)

    # 2. 初始化对偶变量 lambda（均匀分配）
    corners = list(corner_graphs.keys())
    lambda_m = {corner: 1.0 / len(corners) for corner in corners}

    # 3. 历史代价记录
    prev_total_cost = float('inf')

    def check_timing_violations(G, p, setup_padding, hold_padding):
        """检查是否还存在时序违规"""
        violations = []
        for u, v in G.edges():
            edge_data = G.get_edge_data(u, v)
            edge_key = (u, v)
            
            # 检查setup时序
            setup_data = edge_data.get("setup_delay", {})
            if setup_data:
                arrival_gev_params = setup_data.get("arrival_time", 0)
                T_setup = setup_data.get("library_time", 0)
                if arrival_gev_params:
                    gev_setup = genextreme(*arrival_gev_params)
                    arrival = gev_setup.ppf(eta)
                else:
                    arrival = 0
                
                setup_slack = (TCLK + T_setup - arrival) - (p[v] - p[u]) - setup_padding[edge_key]
                if setup_slack < -tol:  # 使用tol作为数值误差容忍度
                    violations.append(("setup", edge_key, setup_slack))
            
            # 检查hold时序
            hold_data = edge_data.get("hold_delay", {})
            if hold_data:
                arrival_gev_params = hold_data.get("arrival_time", 0)
                T_hold = hold_data.get("library_time", 0)
                if arrival_gev_params:
                    gev_hold = genextreme(*arrival_gev_params)
                    arrival = gev_hold.ppf(eta)
                else:
                    arrival = 0
                hold_slack = (p[v] - p[u]) + hold_padding[edge_key] - (T_hold - arrival)
                if hold_slack < -tol:
                    violations.append(("hold", edge_key, hold_slack))
        
        return violations

    def check_setup_timing(G, p, setup_padding, edge_key=None):
        """检查setup时序违规
        
        Args:
            G: 图
            p: 电势
            setup_padding: setup padding值
            edge_key: 如果提供，只检查特定边
            
        Returns:
            violations: 违规列表，每项包含(边, slack)
        """
        violations = []
        edges = [edge_key] if edge_key else G.edges()
        
        for u, v in edges:
            if edge_key and (u, v) != edge_key:
                continue
                
            edge_data = G.get_edge_data(u, v)
            setup_data = edge_data.get("setup_delay", {})
            if setup_data:
                arrival_gev_params = setup_data.get("arrival_time", 0)
                T_setup = setup_data.get("library_time", 0)
                if arrival_gev_params:
                    gev_setup = genextreme(*arrival_gev_params)
                    arrival = gev_setup.ppf(eta)
                else:
                    arrival = 0
                setup_slack = (TCLK + T_setup - arrival) - (p[v] - p[u]) - setup_padding[edge_key]
                if setup_slack < -tol:  # 使用tol作为数值误差容忍度
                    violations.append(((u,v), setup_slack))
        return violations

    # --------------------- 迭代优化 ---------------------
    for iter in range(max_iter):
        total_cost = 0.0
        corner_costs = {}
        setup_negative_cycles = []  # 记录setup负环
        hold_negative_cycles = []   # 记录hold负环
        unfixable_violations = []

        # --------------------- 子问题求解（按Corner并行） ---------------------
        for corner, G in corner_graphs.items():
            # 1. 构建当前Corner的时序约束图（动态计算边权）
            setup_constraints = []
            hold_constraints = []
            
            # 遍历所有边，分别处理Setup和Hold约束
            for u, v in G.edges():
                edge_data = G.get_edge_data(u, v)
                edge_key = (u, v)
                
                # 获取路径类型
                path_type = edge_data.get("path_detail", 'b')  # 默认为'b'，表示独立
                
                # 根据path_type处理delay padding约束
                if path_type == 'a':
                    # a类型：setup_padding = hold_padding = 0
                    setup_padding[edge_key] = 0
                    hold_padding[edge_key] = 0
                    continue  # 跳过后续处理，因为delay已经固定为0
                
                # 处理Setup约束
                setup_data = edge_data.get("setup_delay", {})
                if setup_data:
                    arrival_gev_params = setup_data.get("arrival_time", 0)
                    T_setup = setup_data.get("library_time", 0)
                    if arrival_gev_params:
                        gev_setup = genextreme(*arrival_gev_params)
                        arrival = gev_setup.ppf(eta)
                    else:
                        arrival = 0
                    setup_constraints.append((u, v, arrival, T_setup, path_type))
                    
                # 处理Hold约束
                hold_data = edge_data.get("hold_delay", {})
                if hold_data:
                    arrival_gev_params = hold_data.get("arrival_time", 0)
                    T_hold = hold_data.get("library_time", 0)
                    if arrival_gev_params:
                        gev_hold = genextreme(*arrival_gev_params)
                        arrival = gev_hold.ppf(eta)
                    else:
                        arrival = 0
                    hold_constraints.append((u, v, arrival, T_hold, path_type))

            # 2. 分别检查setup和hold约束的负环
            # 检查setup负环
            setup_adj = defaultdict(list)
            for u, v, arrival, T_setup, _ in setup_constraints:
                weight = TCLK + T_setup - arrival
                #print(f"u: {u}, v: {v}, arrival: {arrival}, T_setup: {T_setup}, weight: {weight}")
                setup_adj[u].append((v, weight))
            
            has_setup_cycle, setup_cycle = bellman_ford_detect_negative_cycle(setup_adj)
            if has_setup_cycle:
                setup_negative_cycles.append((corner, tuple(setup_cycle)))
                # setup负环无法通过delay padding修复
                unfixable_violations.append((corner, "setup", tuple(setup_cycle), "存在setup负环，无法通过delay padding修复"))
            
            # 检查hold负环
            hold_adj = defaultdict(list)
            for u, v, arrival, T_hold, path_type in hold_constraints:
                weight = arrival - T_hold
                #print(f"u: {u}, v: {v}, arrival: {arrival}, T_hold: {T_hold}, weight: {weight}")
                hold_adj[v].append((u, weight))
            
            has_hold_cycle, hold_cycle = bellman_ford_detect_negative_cycle(hold_adj)
            if has_hold_cycle:
                print(f"hold负环: {hold_cycle}")
                hold_negative_cycles.append((corner, tuple(hold_cycle)))
                # 尝试修复hold负环
                edges_to_check_setup = set()  # 记录需要检查setup的边
                
                for i in range(len(hold_cycle)-1):
                    u, v = hold_cycle[i], hold_cycle[i+1]
                    edge_key = (u, v)
                    # 计算需要的额外delay padding
                    cycle_weight = sum(w for dest, w in hold_adj[v] if dest == u)
                    if cycle_weight < 0:
                        additional_padding = abs(cycle_weight)
                        # 检查是否超过最大允许值
                        if hold_padding[edge_key] + additional_padding > max_padding:
                            unfixable_violations.append((corner, "hold", edge_key, "超过最大允许delay padding值"))
                            continue
                        
                        # 根据路径类型更新padding
                        path_type = G.get_edge_data(u, v).get("path_detail", 'b')
                        if path_type == 'a':
                            unfixable_violations.append((corner, "hold", edge_key, "a类型边不允许delay padding"))
                        elif path_type == 'c':
                            # c类型：setup_padding = hold_padding
                            old_padding = hold_padding[edge_key]
                            hold_padding[edge_key] += additional_padding
                            setup_padding[edge_key] = hold_padding[edge_key]
                            if setup_padding[edge_key] != old_padding:
                                edges_to_check_setup.add(edge_key)
                        elif path_type == 'd':
                            # d类型：setup_padding > hold_padding
                            old_setup = setup_padding[edge_key]
                            hold_padding[edge_key] += additional_padding
                            setup_padding[edge_key] = max(setup_padding[edge_key], hold_padding[edge_key] + 1)
                            if setup_padding[edge_key] != old_setup:
                                edges_to_check_setup.add(edge_key)
                        else:  # path_type == 'b'
                            hold_padding[edge_key] += additional_padding
                
                # 检查修改的边是否导致setup违规
                for edge_key in edges_to_check_setup:
                    setup_violations = check_setup_timing(G, p, setup_padding, edge_key)
                    if setup_violations:
                        for edge, slack in setup_violations:
                            unfixable_violations.append(
                                (corner, "setup", edge, 
                                 f"修复hold负环后导致setup违规 slack={slack:.2f}, "
                                 f"hold_padding={hold_padding[edge]:.2f}, "
                                 f"setup_padding={setup_padding[edge]:.2f}")
                            )
                            
                # 如果有setup违规，回滚这些边的padding值
                if unfixable_violations:
                    for violation in unfixable_violations:
                        if len(violation) == 4 and violation[1] == "setup":
                            edge = violation[2]
                            if isinstance(edge, tuple) and edge in edges_to_check_setup:
                                # 回滚到原始值
                                setup_padding[edge] = 0
                                hold_padding[edge] = 0
            
            # 3. 计算调整代价
            buffer_cost = sum(beta * (setup_padding[edge] + hold_padding[edge]) 
                            for edge in set(setup_padding.keys()) | set(hold_padding.keys()))
            smooth_cost = alpha * sum((p[v] - p[u])**2 for u, v in G.edges())
            corner_cost = smooth_cost + buffer_cost
            
            corner_costs[corner] = corner_cost
            total_cost += lambda_m[corner] * corner_cost

        # 如果存在无法修复的违规，提前返回
        if unfixable_violations:
            error_msg = "存在无法修复的时序违规，只能降低延时或者增大Tcp:\n，"
            for violation in unfixable_violations:
                if len(violation) == 4:  # hold违规
                    corner, vio_type, edge, reason = violation
                    error_msg += f"Corner {corner}, {vio_type}违规, 边 {edge}: {reason}\n"
                else:  # setup负环
                    corner, vio_type, cycle, reason = violation
                    error_msg += f"Corner {corner}, {vio_type}违规, 负环: {cycle}: {reason}\n"
            return p, setup_padding, hold_padding, False, error_msg

        # --------------------- 主问题更新 ---------------------
        # 1. 更新对偶变量 lambda
        avg_cost = sum(corner_costs.values()) / len(corners)
        for corner in corners:
            if corner_costs[corner] > avg_cost:
                lambda_m[corner] *= 1.1
            else:
                lambda_m[corner] *= 0.9
        
        # 归一化lambda
        lambda_sum = sum(lambda_m.values())
        for corner in corners:
            lambda_m[corner] /= lambda_sum

        # 2. 更新全局电势 p和delay padding值
        try:
            p_optimal, setup_optimal, hold_optimal = delay_padding_lp_solver(
                corner_graphs=corner_graphs,
                T_clk=TCLK,
                eta=eta,
                current_setup_padding=setup_padding,
                current_hold_padding=hold_padding,
                path_constraints=True  # 告诉LP求解器需要考虑路径约束
            )
            
            # 更新电势和delay padding
            for node in all_nodes:
                p[node] = p_optimal[node]
            
            # 更新delay padding时考虑路径约束
            for edge in set(setup_optimal.keys()) | set(hold_optimal.keys()):
                u, v = edge
                path_type = corner_graphs[corners[0]].get_edge_data(u, v).get("path_detail", 'b')
                
                if path_type == 'a':
                    setup_padding[edge] = 0
                    hold_padding[edge] = 0
                elif path_type == 'c':
                    # 取两者的最大值确保相等
                    delay = max(setup_optimal.get(edge, 0), hold_optimal.get(edge, 0))
                    setup_padding[edge] = delay
                    hold_padding[edge] = delay
                elif path_type == 'd':
                    # 确保setup > hold
                    setup_delay = max(setup_optimal.get(edge, 0), hold_optimal.get(edge, 0) + 1)
                    hold_delay = min(hold_optimal.get(edge, 0), setup_delay - 1)
                    setup_padding[edge] = setup_delay
                    hold_padding[edge] = max(0, hold_delay)
                else:  # path_type == 'b'
                    setup_padding[edge] = max(0, setup_optimal.get(edge, 0))
                    hold_padding[edge] = max(0, hold_optimal.get(edge, 0))
                    
        except Exception as e:
            return p, setup_padding, hold_padding, False, f"LP求解失败: {e}"

        # --------------------- 收敛判断 ---------------------
        if abs(prev_total_cost - total_cost) < tol:
            # 最终收敛时再次检查所有corner是否有违规
            final_violations = []
            for corner, G in corner_graphs.items():
                violations = check_timing_violations(G, p, setup_padding, hold_padding)
                if violations:
                    for vio_type, edge, slack in violations:
                        final_violations.append((corner, edge, f"{vio_type}违规 slack={slack:.2f}"))
            
            if final_violations:
                error_msg = "算法收敛，但仍存在时序违规:\n"
                for corner, edge, reason in final_violations:
                    error_msg += f"Corner {corner}, 边 {edge}: {reason}\n"
                return p, setup_padding, hold_padding, False, error_msg
            
            status_msg = "收敛成功."
            if hold_negative_cycles:
                status_msg = f"收敛成功，hold负环已通过delay padding成功修复于Corners: {[c for c, _ in hold_negative_cycles]}."
            return p, setup_padding, hold_padding, True, status_msg
            
        prev_total_cost = total_cost

    status_msg = "达到最大迭代次数未收敛."
    if hold_negative_cycles:
        # 检查最终状态是否有违规
        final_violations = []
        for corner, G in corner_graphs.items():
            violations = check_timing_violations(G, p, setup_padding, hold_padding)
            if violations:
                for vio_type, edge, slack in violations:
                    final_violations.append((corner, edge, f"{vio_type}违规 slack={slack:.2f}"))
        
        if final_violations:
            error_msg = "达到最大迭代次数未收敛，且仍存在时序违规:\n"
            for corner, edge, reason in final_violations:
                error_msg += f"Corner {corner}, 边 {edge}: {reason}\n"
            return p, setup_padding, hold_padding, False, error_msg
        else:
            status_msg = f"达到最大迭代次数未收敛，但hold负环已通过delay padding成功修复于Corners: {[c for c, _ in hold_negative_cycles]}."
    
    return p, setup_padding, hold_padding, False, status_msg

def bellman_ford_detect_negative_cycle(adj):
    """Bellman-Ford负环检测
    
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