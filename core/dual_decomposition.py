import networkx as nx
from collections import defaultdict
from core.lp_solver import delay_padding_lp_solver

def run_dual_delay_padding(corner_graphs,TCLK, max_iter=100, tol=1e-3, alpha=0.1, beta=0.1):
    """
    多Corner Delay Padding优化函数，适配您的数据结构。
    
    参数:
        corner_graphs (dict): 多Corner时序图，格式为 {corner: nx.Graph}.
        max_iter (int): 最大迭代次数.
        tol (float): 收敛阈值.
        alpha (float): 势能平滑项系数.
        beta (float): Buffer插入惩罚系数.
    
    返回:
        dict: 优化后的全局电势 {node: potential}.
        bool: 是否收敛.
        str: 错误信息.
    """
    # --------------------- 初始化 ---------------------
    # 1. 提取所有节点和初始电势（初始化为0）
    all_nodes = set()
    for G in corner_graphs.values():
        all_nodes.update(G.nodes())
    p = defaultdict(float, {node: 0.0 for node in all_nodes})

    # 2. 初始化对偶变量 lambda（均匀分配）
    corners = list(corner_graphs.keys())
    lambda_m = {corner: 1.0 / len(corners) for corner in corners}

    # 3. 历史代价记录
    prev_total_cost = float('inf')

    # --------------------- 迭代优化 ---------------------
    for iter in range(max_iter):
        total_cost = 0.0
        corner_costs = {}
        negative_cycles_detected = []

        # --------------------- 子问题求解（按Corner并行） ---------------------
        for corner, G in corner_graphs.items():
            # 1. 构建当前Corner的时序约束图（动态计算边权）
            adj = defaultdict(list)
            
            # 遍历所有边，提取Setup和Hold约束
            for u, v in G.edges():
                edge_data = G.get_edge_data(u, v)
                
                # 处理Setup约束（假设delay_type="setup"）
                setup_data = edge_data.get("setup_delay", {})
                if setup_data:
                    arrival = setup_data.get("arrival_time", 0)
                    T_setup = setup_data.get("library_time", 0)
                    # Setup约束：p[v] - p[u] <= T_setup - arrival
                    weight = TCLK + T_setup - arrival - (p[v] - p[u])
                    # print(f"Setup约束: {u} -> {v}, weight: {weight}")
                    adj[u].append((v, weight))
                
                # 处理Hold约束（假设delay_type="hold"）
                hold_data = edge_data.get("hold_delay", {})
                if hold_data:
                    arrival = hold_data.get("arrival_time", 0)
                    T_hold = hold_data.get("library_time", 0)
                    # Hold约束：p[v] - p[u] >= arrival - T_hold
                    weight = arrival - T_hold + (p[v] - p[u])
                    # print(f"Hold约束: {v} -> {u}, weight: {weight}")
                    adj[v].append((u, weight))  # 反向边

            # 2. 检测负环
            has_negative_cycle, _ = bellman_ford_detect_negative_cycle(adj)
            if has_negative_cycle:
                negative_cycles_detected.append(corner)
                corner_cost = float('inf')
            else:
                # 3. 计算调整代价（示例：Buffer数量 + 电势平滑）
                buffer_cost = 0
                for u, v in G.edges():
                    delta_p = p[v] - p[u]
                    buffer_cost += beta * max(0, delta_p)  # 假设Buffer数量与delta_p正相关
                smooth_cost = alpha * sum((p[v] - p[u])**2 for u, v in G.edges())
                corner_cost = smooth_cost + buffer_cost
            
            corner_costs[corner] = corner_cost
            total_cost += lambda_m[corner] * corner_cost

        # --------------------- 错误处理 ---------------------
        if negative_cycles_detected:
            return p, False, f"负环存在于Corners: {negative_cycles_detected}. 需减小Dij或增大TC."

        # --------------------- 主问题更新 ---------------------没有检测到负环，delay padding问题成立。
        # 1. 更新对偶变量 lambda（基于与平均值的比较）
        avg_cost = sum(corner_costs.values()) / len(corners)
        for corner in corners:
            if corner_costs[corner] > avg_cost:
                lambda_m[corner] *= 1.1  # 惩罚高代价
            else:
                lambda_m[corner] *= 0.9  # 奖励低代价
        
        # 归一化lambda
        lambda_sum = sum(lambda_m.values())
        for corner in corners:
            lambda_m[corner] /= lambda_sum

        # 2. 更新全局电势 p LP求解
        try:
            p_optimal = delay_padding_lp_solver(corner_graphs = corner_graphs,T_clk = TCLK)
            for node in all_nodes:
                p[node] = p_optimal[node]
        except Exception as e:
            return p, False, f"LP求解失败: {e}"
       

        # --------------------- 收敛判断 ---------------------
        if abs(prev_total_cost - total_cost) < tol:
            return p, True, "收敛成功."
        prev_total_cost = total_cost

    return p, False, "达到最大迭代次数未收敛."

def bellman_ford_detect_negative_cycle(adj):
    """Bellman-Ford负环检测"""
    nodes = list(adj.keys())
    if not nodes:
        return False, []
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
                for _ in range(len(nodes)):
                    current = predecessor.get(current, None)
                    if current is None:
                        break
                    cycle.append(current)
                    if current == v:
                        return True, cycle
                return True, cycle
    return False, []
