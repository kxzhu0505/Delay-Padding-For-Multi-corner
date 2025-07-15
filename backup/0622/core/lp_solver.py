import cvxpy as cp
import networkx as nx
from collections import defaultdict

def delay_padding_lp_solver(corner_graphs, T_clk, current_setup_padding=None, current_hold_padding=None, 
                          path_constraints=False, alpha=0.1, beta=0.1):
    """
    使用CVXPY求解Delay Padding的LP问题
    
    参数:
        corner_graphs (dict): 多Corner时序图,格式为 {corner: nx.Graph}.
        T_clk (float): 时钟周期.
        current_setup_padding (dict): 当前的setup padding值，格式为{(u,v): value}.
        current_hold_padding (dict): 当前的hold padding值，格式为{(u,v): value}.
        path_constraints (bool): 是否考虑路径约束.
        alpha (float): 电势平滑项系数.
        beta (float): Buffer插入成本系数.
    
    返回:
        dict: 优化后的全局电势 {node: potential}.
        dict: 优化后的setup padding值 {(u,v): value}.
        dict: 优化后的hold padding值 {(u,v): value}.
    """
    # --------------------- 数据准备 ---------------------
    # 提取所有节点并编号
    all_nodes = set()
    all_edges = set()
    for G in corner_graphs.values():
        all_nodes.update(G.nodes())
        all_edges.update(G.edges())
    nodes = sorted(all_nodes)
    edges = sorted(all_edges)
    node_id = {node: idx for idx, node in enumerate(nodes)}
    edge_id = {edge: idx for idx, edge in enumerate(edges)}
    num_nodes = len(nodes)
    num_edges = len(edges)

    # 初始化当前padding值
    if current_setup_padding is None:
        current_setup_padding = defaultdict(float)
    if current_hold_padding is None:
        current_hold_padding = defaultdict(float)

    # 定义CVXPY变量
    p = cp.Variable(num_nodes, name="p")  # 电势
    setup_padding = cp.Variable(num_edges, name="setup_padding")  # setup padding
    hold_padding = cp.Variable(num_edges, name="hold_padding")  # hold padding

    # --------------------- 构建目标函数 ---------------------
    # 目标函数 = 平滑项（电势变化平方和） + Buffer插入成本（padding值之和）
    smooth_cost = alpha * cp.sum_squares(p)
    buffer_cost = beta * (cp.sum(setup_padding) + cp.sum(hold_padding))
    total_cost = smooth_cost + buffer_cost

    # --------------------- 构建约束 ---------------------
    constraints = []
    
    # 非负约束
    constraints.extend([setup_padding >= 0, hold_padding >= 0])

    # 遍历每个Corner的时序约束
    for corner, G in corner_graphs.items():
        for u, v in G.edges():
            u_idx = node_id[u]
            v_idx = node_id[v]
            edge_idx = edge_id[(u,v)]
            edge_data = G.get_edge_data(u, v)
            path_type = edge_data.get("path_detail", 'b')

            # 根据路径类型添加约束
            if path_constraints:
                if path_type == 'a':
                    # a类型：setup_padding = hold_padding = 0
                    constraints.extend([
                        setup_padding[edge_idx] == 0,
                        hold_padding[edge_idx] == 0
                    ])
                elif path_type == 'c':
                    # c类型：setup_padding = hold_padding
                    constraints.append(setup_padding[edge_idx] == hold_padding[edge_idx])
                elif path_type == 'd':
                    # d类型：setup_padding > hold_padding
                    constraints.append(setup_padding[edge_idx] >= hold_padding[edge_idx] + 1)
            
            # Setup约束
            setup_data = edge_data.get("setup_delay", {})
            if setup_data:
                arrival = setup_data.get("arrival_time", 0)
                T_setup = setup_data.get("library_time", 0)
                constraints.append(
                    p[v_idx] - p[u_idx] + setup_padding[edge_idx] <= T_clk - T_setup - arrival
                )
            
            # Hold约束
            hold_data = edge_data.get("hold_delay", {})
            if hold_data:
                arrival = hold_data.get("arrival_time", 0)
                T_hold = hold_data.get("library_time", 0)
                constraints.append(
                    p[v_idx] - p[u_idx] + hold_padding[edge_idx] >= T_hold - arrival
                )

    # --------------------- 求解LP问题 ---------------------
    problem = cp.Problem(cp.Minimize(total_cost), constraints)
    try:
        problem.solve(solver=cp.ECOS, verbose=False)  # 使用ECOS求解器（开源）
    except Exception as e:
        raise RuntimeError(f"LP求解失败: {str(e)}")

    # --------------------- 处理结果 ---------------------
    if problem.status == "optimal":
        # 转换结果为字典格式
        p_optimal = {node: float(p.value[node_id[node]]) for node in nodes}
        setup_optimal = {edge: float(setup_padding.value[edge_id[edge]]) for edge in edges}
        hold_optimal = {edge: float(hold_padding.value[edge_id[edge]]) for edge in edges}
        
        return p_optimal, setup_optimal, hold_optimal
    else:
        raise RuntimeError(f"不可行或无解. 状态: {problem.status}")
